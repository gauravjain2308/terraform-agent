# Terraform-from-Diagram Q&A System

**Structured, JSON-based Q&A management for terraform infrastructure generation — minimizes token usage through batch LLM review.**

---

## What Is This?

A system to systematically collect, validate, and review questions about each phase of the Terraform-from-Diagram workflow. Instead of asking Claude per-question (expensive), answers are collected in JSON and reviewed once in batch (efficient).

```
Per-question approach:  /Diagram2Services → Q1 (LLM) → Q2 (LLM) → Q3 (LLM) → ... [20+ API calls]
Q&A system approach:    /Diagram2Services → collect JSON → validate → review once (LLM) [1 API call]
```

**Result: 80%+ fewer tokens, same quality.**

---

## Quick Start

```bash
# 1. When starting a phase, initialize Q&A
python qa_system.py init DIAGRAM_INGESTED

# 2. Edit the JSON file with answers
vim .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json

# 3. Validate before proceeding
python qa_system.py validate DIAGRAM_INGESTED

# 4. Proceed with normal terraform commands
/ServicesRefiner

# 5. Repeat for each phase...
```

See `QUICKSTART.md` for 30-second guide.

---

## How It Works

### 1. **Phase Templates**

Each phase of terraform-from-diagram has a question template in JSON:

```
DIAGRAM_INGESTED_questions.json       ← What info to extract from diagram
GATE1_SERVICES_questions.json         ← Service validation checklist
GATE2_BUILD_PLAN_questions.json       ← Build plan review
GATE3_INPUTS_questions.json           ← Variable collection
BUILD_SERVICE_questions.json          ← Code generation validation
FINALIZE_questions.json               ← Project finalization
```

### 2. **JSON Storage**

All answers are stored in one file: `terraform_qa_database.json`

```json
{
  "What is the project name?": {
    "phase": "DIAGRAM_INGESTED",
    "answer": "my-api-backend",
    "category": "Project",
    "required": true
  },
  "Are all service names lowercase-hyphen?": {
    "phase": "GATE1_SERVICES",
    "answer": "Yes, all names follow: api-gateway, rds-users, lambda-auth",
    "category": "Naming",
    "required": true
  }
}
```

### 3. **Validation**

Before proceeding to the next phase, validate completeness:

```bash
python qa_system.py validate GATE1_SERVICES
# ✅ Phase 'GATE1_SERVICES' — all required answers filled!
# OR
# ⚠️ 2 required answers missing:
#    [Naming] Are all service names lowercase-hyphen?
#    [Validation] Are there any duplicate service names?
```

### 4. **Review Once**

After filling all phases, Claude reviews the entire Q&A in one batch call:

```bash
python qa_system.py missing  # Shows any gaps
# Then, in Claude Code:
# "Review terraform_qa_database.json for quality, consistency, and best practices"
```

---

## File Structure

```
.claude/skills/terraform-from-diagram/qa/
├── qa_system.py                               Main script
├── README.md                                  This file
├── QUICKSTART.md                              30-second start
├── TERRAFORM_QA_INTEGRATION.md                Full documentation
│
├── terraform_qa_database.json                 All Q&A (auto-created)
│
├── DIAGRAM_INGESTED_questions.json            Phase 1 template
├── GATE1_SERVICES_questions.json              Phase 2 template
├── GATE2_BUILD_PLAN_questions.json            Phase 3 template
├── GATE3_INPUTS_questions.json                Phase 4 template
├── BUILD_SERVICE_questions.json               Phase 5 template
├── FINALIZE_questions.json                    Phase 6 template
│
├── DIAGRAM_INGESTED_answers.md                Exported phase 1
├── GATE1_SERVICES_answers.md                  Exported phase 2
└── ... (more exports)
```

---

## Commands

| Command | What It Does |
|---------|-------------|
| `init {PHASE}` | Load phase questions into database |
| `validate {PHASE}` | Check if phase is complete |
| `export {PHASE}` | Export phase Q&A to Markdown |
| `status` | Show all phases and completion % |
| `missing` | List all unanswered required questions |

### Examples

```bash
# Initialize phase
python qa_system.py init DIAGRAM_INGESTED

# Validate before proceeding
python qa_system.py validate GATE1_SERVICES

# Export to share
python qa_system.py export GATE1_SERVICES

# Check progress
python qa_system.py status

# Find what needs answering
python qa_system.py missing
```

---

## Integration with Terraform Workflow

Each terraform-from-diagram phase has a corresponding Q&A phase:

```
Phase 1: /Diagram2Services       → Q&A: DIAGRAM_INGESTED
Phase 2: /ServicesRefiner        → Q&A: GATE1_SERVICES
Phase 3: /ServiceModeler         → Q&A: GATE2_BUILD_PLAN
Phase 4: /BuildPlan              → Q&A: GATE3_INPUTS
Phase 5: /ServiceCodeWriter      → Q&A: BUILD_SERVICE
Phase 6: /DeployOrchestrator     → Q&A: FINALIZE
```

**Workflow for each phase:**

1. Run terraform command (e.g., `/Diagram2Services`)
2. Initialize Q&A: `python qa_system.py init {PHASE}`
3. Edit review file and Q&A JSON
4. Validate: `python qa_system.py validate {PHASE}`
5. If valid, run confirm command (e.g., `/ServicesRefinerConfirm`)
6. Move to next phase

---

## Token Savings

### Example: 20 Questions per Project

| Approach | LLM Calls | Tokens/Call | Total | Cost* |
|----------|-----------|-------------|-------|-------|
| **Q&A System** (batch review) | 1 | 2,000 | 2,000 | ~$0.02 |
| **Per-question** (traditional) | 20+ | 500 ea | 10,000+ | ~$0.10+ |
| **Savings** | 95%+ fewer calls | — | **80%+ tokens** | **80% cost** |

*Approximate, at current Claude API rates*

---

## Why Use JSON?

✅ **Easy to edit** — Any text editor works  
✅ **Easy to validate** — Check programmatically without LLM  
✅ **Persistent** — Q&A carries across sessions  
✅ **Auditable** — Clear record of decisions  
✅ **Exportable** — Convert to Markdown for handoff  
✅ **Structured** — Machine-readable format

---

## Example Workflow

### Phase 1: Diagram Ingestion

```bash
# 1. Run terraform command
/Diagram2Services

# 2. Initialize Q&A
python qa_system.py init DIAGRAM_INGESTED

# 3. Edit and fill
# terraform_qa_database.json now has questions like:
#   - "What is the project name?"
#   - "What is the target AWS region?"
#   - "What are the identified infrastructure services?"

# 4. Validate
python qa_system.py validate DIAGRAM_INGESTED
# ⚠️ 3 required answers missing

# 5. Fill in answers (edit the JSON)
# Answer: "project-name": "my-api-platform"
# Answer: "region": "us-east-1"
# Answer: "services": "Lambda, RDS, API Gateway, S3"

# 6. Validate again
python qa_system.py validate DIAGRAM_INGESTED
# ✅ All required answers filled!

# 7. Proceed with normal terraform workflow
/ServicesRefiner
```

### Phase 2: Service Review

```bash
# 1. Initialize next phase
python qa_system.py init GATE1_SERVICES

# 2. Edit review/services-review.md (as normal)

# 3. Fill Q&A for this phase

# 4. Validate
python qa_system.py validate GATE1_SERVICES

# 5. Proceed
/ServicesRefinerConfirm
```

### Final: Batch Review

```bash
# After all phases filled
python qa_system.py missing
# ✅ All required answers filled!

# Export all to Markdown
for phase in DIAGRAM_INGESTED GATE1_SERVICES GATE2_BUILD_PLAN GATE3_INPUTS BUILD_SERVICE FINALIZE; do
  python qa_system.py export $phase
done

# Claude reviews all exports at once (1 API call)
# "Review all terraform Q&A and provide feedback on quality and completeness"
```

---

## Troubleshooting

### "No questions found for phase X"
Check that `{PHASE}_questions.json` exists in this directory.

### "terraform_qa_database.json not found"
Run `python qa_system.py init {PHASE}` to create it.

### "Phase is not complete"
Run `python qa_system.py missing` to see which required answers are blank.

### "Want to start over?"
Delete `terraform_qa_database.json` and re-run `init` for each phase.

### "How do I edit terraform_qa_database.json?"
Use any text editor:
```bash
vim .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json
code .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json
```

---

## Full Documentation

- `QUICKSTART.md` — 30-second getting started
- `TERRAFORM_QA_INTEGRATION.md` — Complete integration guide with examples
- `qa_system.py` — Python script (source code)

---

## Design Philosophy

1. **Minimize LLM calls** — Questions are predetermined; LLM only reviews at the end
2. **Simple format** — JSON is human and machine readable
3. **Persistent** — Q&A survives across sessions
4. **Composable** — Works alongside existing terraform-from-diagram workflow
5. **Extensible** — Add new questions by editing `*_questions.json` templates

---

## Next Steps

1. Read `QUICKSTART.md` for 30-second start
2. Run `python qa_system.py init DIAGRAM_INGESTED`
3. Edit `terraform_qa_database.json` with answers from your diagram
4. Validate: `python qa_system.py validate DIAGRAM_INGESTED`
5. Export: `python qa_system.py export DIAGRAM_INGESTED`
6. Proceed with normal `/ServicesRefiner` command

Questions? See `TERRAFORM_QA_INTEGRATION.md` for full docs.