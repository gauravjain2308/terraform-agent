#!/usr/bin/env python3
"""
Terraform QA System: Manages Q&A for terraform-from-diagram workflow.
Integrates with memory system and review gates.
Minimizes LLM token usage by batch-reviewing only.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

TERRAFORM_QA_DIR = ".claude/skills/terraform-from-diagram/qa"
TERRAFORM_QA_FILE = f"{TERRAFORM_QA_DIR}/terraform_qa_database.json"
MEMORY_DIR = ".claude/memory"

def ensure_directories():
    """Create required directories."""
    Path(TERRAFORM_QA_DIR).mkdir(parents=True, exist_ok=True)
    Path(MEMORY_DIR).mkdir(parents=True, exist_ok=True)

def load_qa_database():
    """Load existing QA database."""
    if not Path(TERRAFORM_QA_FILE).exists():
        return {}
    with open(TERRAFORM_QA_FILE, "r") as f:
        return json.load(f)

def save_qa_database(qa_dict):
    """Save QA database."""
    ensure_directories()
    with open(TERRAFORM_QA_FILE, "w") as f:
        json.dump(qa_dict, f, indent=2)
    print(f"✅ Saved: {TERRAFORM_QA_FILE}")

def load_phase_template(phase_name):
    """Load Q&A template for a phase."""
    template_file = Path(TERRAFORM_QA_DIR) / f"{phase_name}_questions.json"
    if template_file.exists():
        with open(template_file, "r") as f:
            return json.load(f)
    return {}

def get_phase_qa(phase_name):
    """Get all Q&A for a phase."""
    qa_db = load_qa_database()
    return {k: v for k, v in qa_db.items() if v.get("phase") == phase_name}

def add_qa_from_template(phase_name):
    """Add questions from template to database."""
    template = load_phase_template(phase_name)
    qa_db = load_qa_database()

    questions = template.get("questions", [])
    added = 0

    for q in questions:
        question_text = q if isinstance(q, str) else q.get("question", "")
        if question_text and question_text not in qa_db:
            qa_db[question_text] = {
                "phase": phase_name,
                "answer": "[TO BE FILLED]",
                "category": q.get("category", "") if isinstance(q, dict) else "",
                "required": q.get("required", False) if isinstance(q, dict) else False
            }
            added += 1

    save_qa_database(qa_db)
    return added, len(questions)

def get_missing_required(phase_name=None):
    """Get required questions that haven't been answered."""
    qa_db = load_qa_database()
    missing = []

    for question, data in qa_db.items():
        if isinstance(data, dict):
            is_required = data.get("required", False)
            is_filled = data.get("answer", "") not in ["", "[TO BE FILLED]"]

            if phase_name and data.get("phase") != phase_name:
                continue

            if is_required and not is_filled:
                missing.append({
                    "question": question,
                    "phase": data.get("phase", ""),
                    "category": data.get("category", "")
                })

    return missing

def validate_phase(phase_name):
    """Check if all required answers for a phase are filled."""
    missing = get_missing_required(phase_name)

    if missing:
        print(f"\n⚠️  Phase '{phase_name}' — {len(missing)} required answers missing:\n")
        for item in missing:
            print(f"   [{item['category']}] {item['question']}")
        return False

    print(f"✅ Phase '{phase_name}' — all required answers filled!")
    return True

def export_phase_to_md(phase_name, output_file=None):
    """Export phase Q&A to Markdown."""
    qa_db = load_qa_database()
    phase_qa = {k: v for k, v in qa_db.items() if isinstance(v, dict) and v.get("phase") == phase_name}

    if not phase_qa:
        print(f"⚠️  No Q&A found for phase: {phase_name}")
        return

    md = f"# {phase_name} — Q&A\n\n"
    md += f"Generated: {datetime.now().isoformat()}\n\n"

    for i, (question, data) in enumerate(phase_qa.items(), 1):
        if isinstance(data, dict):
            answer = data.get("answer", "[EMPTY]")
            category = data.get("category", "")
            required = "🔴 REQUIRED" if data.get("required") else "⚪ Optional"

            md += f"## Q{i}: {question}\n\n"
            md += f"**Category:** {category} | **Status:** {required}\n\n"
            md += f"**Answer:**\n{answer}\n\n"

    if not output_file:
        output_file = f"{TERRAFORM_QA_DIR}/{phase_name}_answers.md"

    Path(output_file).write_text(md)
    print(f"✅ Exported: {output_file}")

def init_phase(phase_name):
    """Initialize Q&A for a new phase."""
    print(f"🔧 Initializing phase: {phase_name}")
    added, total = add_qa_from_template(phase_name)
    print(f"   Added {added}/{total} questions")

    if validate_phase(phase_name):
        return True
    return False

def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python qa_system.py [command] [args]")
        print("\nCommands:")
        print("  init <phase>        Initialize Q&A for a phase")
        print("  validate <phase>    Check if phase Q&A is complete")
        print("  export <phase>      Export phase Q&A to Markdown")
        print("  status              Show all Q&A status")
        print("  missing             Show all missing required answers")
        return

    cmd = sys.argv[1]

    if cmd == "init" and len(sys.argv) > 2:
        init_phase(sys.argv[2])
    elif cmd == "validate" and len(sys.argv) > 2:
        validate_phase(sys.argv[2])
    elif cmd == "export" and len(sys.argv) > 2:
        phase = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else None
        export_phase_to_md(phase, output)
    elif cmd == "status":
        qa_db = load_qa_database()
        print(f"\n📊 Total Q&A entries: {len(qa_db)}\n")
        phases = {}
        for q, data in qa_db.items():
            if isinstance(data, dict):
                phase = data.get("phase", "unknown")
                phases[phase] = phases.get(phase, 0) + 1

        for phase, count in sorted(phases.items()):
            missing = len(get_missing_required(phase))
            status = "✅" if missing == 0 else "⏳"
            print(f"  {status} {phase}: {count} Q&A ({missing} missing)")
    elif cmd == "missing":
        missing = get_missing_required()
        if not missing:
            print("✅ All required answers filled!")
        else:
            print(f"\n⚠️  {len(missing)} required answers missing:\n")
            for item in missing:
                print(f"   [{item['phase']}] {item['question']}")
    else:
        print(f"❌ Unknown command: {cmd}")

if __name__ == "__main__":
    main()