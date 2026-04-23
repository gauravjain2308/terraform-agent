#!/usr/bin/env python3
"""
token-tracker.py
Track token usage per /tf-* command across your project.

Usage:
  python3 agent/scripts/token-tracker.py log  /ServiceBuilder rds-users  4832  1247
  python3 agent/scripts/token-tracker.py show
  python3 agent/scripts/token-tracker.py show --command /ServiceBuilder
  python3 agent/scripts/token-tracker.py summary

The Claude Code extension doesn't expose token counts directly.
Log them manually after each command by checking the API response,
or use this with the Anthropic API directly (see api-runner.py).
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("agent/token-usage.json")

# Approximate cost per 1M tokens (Claude Sonnet 4 as of 2025)
COST_PER_1M_INPUT  = 3.00   # $3.00 per 1M input tokens
COST_PER_1M_OUTPUT = 15.00  # $15.00 per 1M output tokens


def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return {"entries": [], "totals": {"input": 0, "output": 0, "calls": 0}}


def save_log(data):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(data, indent=2))


def log_command(command, input_tokens, output_tokens, note=""):
    data = load_log()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "total_tokens": int(input_tokens) + int(output_tokens),
        "cost_usd": round(
            (int(input_tokens) / 1_000_000 * COST_PER_1M_INPUT) +
            (int(output_tokens) / 1_000_000 * COST_PER_1M_OUTPUT), 6
        ),
        "note": note
    }
    data["entries"].append(entry)
    data["totals"]["input"]  += int(input_tokens)
    data["totals"]["output"] += int(output_tokens)
    data["totals"]["calls"]  += 1
    save_log(data)

    print(f"✅ Logged: {command}")
    print(f"   Input:  {input_tokens:,} tokens")
    print(f"   Output: {output_tokens:,} tokens")
    print(f"   Total:  {int(input_tokens)+int(output_tokens):,} tokens")
    print(f"   Cost:   ~${entry['cost_usd']:.4f}")


def show_log(filter_command=None):
    data = load_log()
    entries = data["entries"]

    if filter_command:
        entries = [e for e in entries if filter_command in e["command"]]

    if not entries:
        print("No entries found.")
        return

    print(f"\n{'Timestamp':<22} {'Command':<30} {'Input':>8} {'Output':>8} {'Total':>8} {'Cost':>10}")
    print("─" * 95)

    for e in entries[-50:]:   # last 50
        ts = e["timestamp"][:16].replace("T", " ")
        print(f"{ts:<22} {e['command']:<30} {e['input_tokens']:>8,} {e['output_tokens']:>8,} {e['total_tokens']:>8,} ${e['cost_usd']:>9.4f}")

    print("─" * 95)
    total_input  = sum(e["input_tokens"]  for e in entries)
    total_output = sum(e["output_tokens"] for e in entries)
    total_cost   = sum(e["cost_usd"]      for e in entries)
    print(f"{'TOTAL':<52} {total_input:>8,} {total_output:>8,} {total_input+total_output:>8,} ${total_cost:>9.4f}")


def show_summary():
    data = load_log()
    entries = data["entries"]

    if not entries:
        print("No entries yet. Log some commands first.")
        return

    # Group by command
    by_command = {}
    for e in entries:
        cmd = e["command"]
        if cmd not in by_command:
            by_command[cmd] = {"calls": 0, "input": 0, "output": 0, "cost": 0}
        by_command[cmd]["calls"]  += 1
        by_command[cmd]["input"]  += e["input_tokens"]
        by_command[cmd]["output"] += e["output_tokens"]
        by_command[cmd]["cost"]   += e["cost_usd"]

    print(f"\n{'Command':<35} {'Calls':>5} {'Avg Input':>10} {'Avg Output':>11} {'Total Cost':>12}")
    print("─" * 80)

    for cmd, stats in sorted(by_command.items(), key=lambda x: -x[1]["cost"]):
        avg_in  = stats["input"]  // stats["calls"]
        avg_out = stats["output"] // stats["calls"]
        print(f"{cmd:<35} {stats['calls']:>5} {avg_in:>10,} {avg_out:>11,} ${stats['cost']:>11.4f}")

    print("─" * 80)
    total = data["totals"]
    total_cost = sum(e["cost_usd"] for e in entries)
    print(f"{'TOTAL':<35} {total['calls']:>5} {'':>10} {'':>11} ${total_cost:>11.4f}")
    print(f"\nAll-time tokens: {total['input']+total['output']:,}  "
          f"(input: {total['input']:,}  output: {total['output']:,})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "log":
        if len(sys.argv) < 5:
            print("Usage: token-tracker.py log <command> <input_tokens> <output_tokens> [note]")
            return
        command      = sys.argv[2]
        input_tokens = sys.argv[3]
        output_tokens= sys.argv[4]
        note         = sys.argv[5] if len(sys.argv) > 5 else ""
        log_command(command, input_tokens, output_tokens, note)

    elif cmd == "show":
        filter_cmd = None
        if "--command" in sys.argv:
            idx = sys.argv.index("--command")
            filter_cmd = sys.argv[idx + 1]
        show_log(filter_cmd)

    elif cmd == "summary":
        show_summary()

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: log | show | summary")


if __name__ == "__main__":
    main()
