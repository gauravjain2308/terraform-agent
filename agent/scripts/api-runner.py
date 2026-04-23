#!/usr/bin/env python3
"""
api-runner.py
Run a command via the Anthropic API directly and log tokens automatically.
This is the accurate way to track tokens — the Claude Code UI doesn't expose counts.

Setup:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...

Usage:
  python3 agent/scripts/api-runner.py /tf-status
  python3 agent/scripts/api-runner.py /tf-review rds-users
  python3 agent/scripts/api-runner.py /tf-diagram-suggest

What it does:
  1. Reads the command file from .claude/commands/
  2. Reads relevant memory files for context
  3. Calls Claude API with the command
  4. Prints the response
  5. Logs token usage to agent/token-usage.json automatically
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("❌ anthropic package not installed.")
    print("   Run: pip install anthropic")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

MODEL          = "claude-sonnet-4-20250514"
MAX_TOKENS     = 8192
COMMANDS_DIR   = Path(".claude/commands")
MEMORY_DIR     = Path(".claude/memory")
SKILLS_DIR     = Path(".claude/skills")
TOKEN_LOG      = Path("agent/token-usage.json")

COST_PER_1M_INPUT  = 3.00
COST_PER_1M_OUTPUT = 15.00

# ── Token logging ─────────────────────────────────────────────────────────────

def log_tokens(command, input_tokens, output_tokens):
    TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(TOKEN_LOG.read_text()) if TOKEN_LOG.exists() else {
        "entries": [], "totals": {"input": 0, "output": 0, "calls": 0}
    }
    cost = round(
        (input_tokens  / 1_000_000 * COST_PER_1M_INPUT) +
        (output_tokens / 1_000_000 * COST_PER_1M_OUTPUT), 6
    )
    data["entries"].append({
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": cost
    })
    data["totals"]["input"]  += input_tokens
    data["totals"]["output"] += output_tokens
    data["totals"]["calls"]  += 1
    TOKEN_LOG.write_text(json.dumps(data, indent=2))
    return cost


# ── Context builder ───────────────────────────────────────────────────────────

def build_context(command_name):
    """Build the full context string: memory + relevant skill references."""
    parts = []

    # Load handoff.json first (compact bootstrap)
    handoff = MEMORY_DIR / "handoff.json"
    if handoff.exists():
        parts.append(f"## Project State (handoff.json)\n```json\n{handoff.read_text()}\n```")

    # Load tf-state.json
    state = MEMORY_DIR / "tf-state.json"
    if state.exists():
        parts.append(f"## Full State (tf-state.json)\n```json\n{state.read_text()}\n```")

    # Load relevant memory files based on command
    memory_files = {
        "ServicesRefiner":    [],
        "ServiceModeler":     ["01-services.json"],
        "BuildPlan":          ["01-services.json", "02-build-plan.json"],
        "ServiceBuilder":     ["01-services.json", "02-build-plan.json"],
        "tf-review":          ["01-services.json", "02-build-plan.json"],
        "tf-diagram":         ["01-services.json", "02-build-plan.json"],
        "tf-status":          ["04-build-progress.json"],
        "IAMModeler":         ["01-services.json", "02-build-plan.json"],
    }

    cmd_base = command_name.lstrip("/").split()[0]
    for prefix, files in memory_files.items():
        if cmd_base.startswith(prefix):
            for f in files:
                fpath = MEMORY_DIR / f
                if fpath.exists():
                    parts.append(f"## Memory: {f}\n```json\n{fpath.read_text()}\n```")
            break

    return "\n\n".join(parts)


def load_command_instruction(command_name):
    """Load the command .md file."""
    cmd_base = command_name.lstrip("/").split()[0]
    cmd_file = COMMANDS_DIR / f"{cmd_base}.md"
    if not cmd_file.exists():
        print(f"❌ Command file not found: {cmd_file}")
        print(f"   Available: {[f.stem for f in COMMANDS_DIR.glob('*.md')]}")
        sys.exit(1)
    return cmd_file.read_text()


# ── Main runner ───────────────────────────────────────────────────────────────

def run_command(command_str):
    client = anthropic.Anthropic()

    command_name = command_str.split()[0]    # e.g. /tf-review
    arguments    = " ".join(command_str.split()[1:])  # e.g. rds-users

    print(f"Running: {command_str}")
    print(f"Model:   {MODEL}")
    print("─" * 60)

    # Build system prompt from command file
    instruction = load_command_instruction(command_name)
    context     = build_context(command_name)

    system_prompt = f"""You are a Terraform infrastructure expert assistant.
You are executing the command: {command_str}

## Command Instructions
{instruction}

## Current Project Context
{context}
"""

    user_message = f"""Execute command: {command_str}
Arguments: {arguments if arguments else "(none)"}

Follow the command instructions exactly. Write all output files as specified.
Keep chat output compact (≤ 25 lines).
End with the standard /clear instruction block."""

    # Call the API
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    # Extract response text
    response_text = response.content[0].text

    # Token counts
    input_tokens  = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens  = input_tokens + output_tokens
    cost          = log_tokens(command_str, input_tokens, output_tokens)

    # Print response
    print(response_text)
    print("\n" + "─" * 60)
    print(f"📊 Token usage logged to agent/token-usage.json")
    print(f"   Input:  {input_tokens:,} tokens")
    print(f"   Output: {output_tokens:,} tokens")
    print(f"   Total:  {total_tokens:,} tokens")
    print(f"   Cost:   ~${cost:.4f}")
    print(f"   Model:  {MODEL}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set.")
        print("   Run: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    if not command.startswith("/"):
        command = "/" + command

    run_command(command)


if __name__ == "__main__":
    main()
