# QA Processor - Minimal Token Usage Tool

A simple Python tool to manage Q&A databases with efficient LLM usage.

## How It Works

1. **Read Questions** - Load from text or JSON file
2. **Store in JSON** - Simple key-value database
3. **Manual Answers** - Fill in answers directly (no LLM per-question)
4. **Review Once** - Use LLM only at the end to review all answers

## Usage

### Step 1: Prepare Questions

Add your questions to `questions.txt` (one per line):
```
What is question 1?
What is question 2?
```

Or use JSON format (`questions.json`):
```json
{
  "questions": [
    "What is question 1?",
    "What is question 2?"
  ]
}
```

### Step 2: Generate QA Database

```bash
python qa_processor.py
```

This creates `qa_database.json`:
```json
{
  "What is question 1?": "[TO BE FILLED]",
  "What is question 2?": "[TO BE FILLED]"
}
```

### Step 3: Fill in Answers

Edit `qa_database.json` and replace `[TO BE FILLED]` with actual answers:
```json
{
  "What is question 1?": "This is the answer to question 1.",
  "What is question 2?": "This is the answer to question 2."
}
```

### Step 4: Review with LLM (Optional)

```bash
python qa_processor.py --review
```

Claude will:
- Check all answers are filled
- Review for clarity and accuracy
- Suggest improvements
- Output corrected versions

### Step 5: Generate Markdown

Markdown is auto-generated after each run:
```bash
cat answers.md
```

Output:
```markdown
# Question & Answer Database

## Q1: What is question 1?

**Answer:** This is the answer to question 1.

## Q2: What is question 2?

**Answer:** This is the answer to question 2.
```

## Files

- `questions.txt` - Input questions (one per line)
- `qa_database.json` - Main Q&A storage
- `answers.md` - Generated markdown output
- `qa_processor.py` - The main script

## Token Optimization

✅ **No LLM per-question** - Avoids redundant API calls
✅ **Batch review** - Single API call to review all answers
✅ **Simple format** - JSON is easy to edit directly
✅ **Minimal overhead** - Only review when needed

## Advanced: Use JSON Input

For existing Q&A data:

```bash
python qa_processor.py --json
```

Expects `questions.json` with `"questions"` array.

## Example Workflow

```bash
# 1. Create/update database
python qa_processor.py

# 2. Edit qa_database.json with your answers
# (use any text editor)

# 3. Review with Claude (optional)
python qa_processor.py --review

# 4. Output in Markdown
# answers.md is ready!
```

## Notes

- If a question already exists in `qa_database.json`, it won't be overwritten
- `[TO BE FILLED]` answers will block the review step
- Review feedback can be copied directly into the JSON
- Script is simple and extensible
