#!/usr/bin/env python3
"""
QA Processor: Read questions, store answers in JSON, review with LLM.
Minimizes token usage by only using LLM for review, not per-question answering.
"""

import json
import sys
from pathlib import Path

# Input file format
INPUT_QUESTIONS_FILE = "questions.txt"  # One question per line, or use questions.json
OUTPUT_JSON_FILE = "qa_database.json"
OUTPUT_MD_FILE = "answers.md"

def load_questions_from_txt(filepath):
    """Load questions from a text file (one per line)."""
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        questions = [line.strip() for line in f if line.strip()]
    return questions

def load_questions_from_json(filepath):
    """Load questions from JSON file."""
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "questions" in data:
        return data["questions"]
    return []

def load_existing_qa(filepath):
    """Load existing QA database."""
    if not Path(filepath).exists():
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_qa_database(qa_dict, filepath):
    """Save QA database to JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(qa_dict, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {filepath}")

def save_markdown(qa_dict, filepath):
    """Convert QA JSON to Markdown."""
    md_content = "# Question & Answer Database\n\n"

    for i, (question, answer) in enumerate(qa_dict.items(), 1):
        md_content += f"## Q{i}: {question}\n\n"
        md_content += f"**Answer:** {answer}\n\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"✅ Saved: {filepath}")

def process_questions(input_file, use_json=False):
    """Main processing function."""
    print(f"📖 Reading questions from: {input_file}")

    # Load questions
    if use_json:
        questions = load_questions_from_json(input_file)
    else:
        questions = load_questions_from_txt(input_file)

    if not questions:
        print("❌ No questions found!")
        return

    print(f"✅ Loaded {len(questions)} questions")

    # Load existing QA or create new
    qa_db = load_existing_qa(OUTPUT_JSON_FILE)

    # Process new questions
    new_count = 0
    for question in questions:
        if question not in qa_db:
            qa_db[question] = "[TO BE FILLED]"
            new_count += 1

    print(f"➕ {new_count} new questions added")
    print(f"📊 Total questions: {len(qa_db)}")

    # Save
    save_qa_database(qa_db, OUTPUT_JSON_FILE)
    save_markdown(qa_db, OUTPUT_MD_FILE)

    # Show status
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("="*50)
    print(f"1. Edit {OUTPUT_JSON_FILE} and fill in answers")
    print(f"2. Run: python qa_processor.py --review")
    print(f"   (This will use LLM to review all answers)")
    print(f"3. Output will be in {OUTPUT_MD_FILE}")

def review_with_llm():
    """Review QA database with Claude LLM."""
    import anthropic

    qa_db = load_existing_qa(OUTPUT_JSON_FILE)

    if not qa_db:
        print("❌ No QA database found!")
        return

    unfilled = {q: a for q, a in qa_db.items() if "[TO BE FILLED]" in a}

    if unfilled:
        print(f"⚠️  {len(unfilled)} answers still need to be filled!")
        for q in unfilled:
            print(f"   - {q}")
        return

    print("🔍 Reviewing answers with Claude...")

    qa_text = "\n".join([f"Q: {q}\nA: {a}\n" for q, a in qa_db.items()])

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Review this Q&A database for clarity, accuracy, and completeness.
Provide feedback on any answers that need improvement.

{qa_text}

Format: List issues found, then provide corrected answers in JSON format."""
        }]
    )

    print("\n" + "="*50)
    print("REVIEW FEEDBACK FROM CLAUDE:")
    print("="*50)
    print(response.content[0].text)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--review":
            review_with_llm()
            return
        elif sys.argv[1] == "--json":
            process_questions(INPUT_QUESTIONS_FILE, use_json=True)
            return

    process_questions(INPUT_QUESTIONS_FILE, use_json=False)

if __name__ == "__main__":
    main()
