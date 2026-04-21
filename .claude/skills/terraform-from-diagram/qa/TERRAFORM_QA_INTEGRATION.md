# Terraform QA System Integration Guide

**Minimizes token usage by systematically collecting Q&A per phase, batch-reviewing only at the end.**

---

## Overview

The Q&A system integrates with the terraform-from-diagram workflow to:

1. **Collect structured questions** for each phase (no repeated LLM asks)
2. **Store answers in JSON** (easy to read, edit, and validate)
3. **Validate completeness** before proceeding to the next gate
4. **Review with Claude** (batch review, not per-question) to catch issues early
5. **Export to Markdown** for documentation and handoff

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│ Terraform Workflow Phases                            │
├──────────────────────────────────────────────────────┤
│ DIAGRAM_INGESTED      → GATE1_SERVICES               │
│   (Q&A Phase 1)          (Q&A Phase 2)               │
│                                                      │
│ GATE2_BUILD_PLAN      → GATE3_INPUTS                 │
│   (Q&A Phase 3)          (Q&A Phase 4)               │
│                                                      │
│ BUILD_SERVICE         → FINALIZE                     │
│   (Q&A Phase 5)          (Q&A Phase 6)               │
└──────────────────────────────────────────────────────┘
         ↓
    terraform_qa_database.json
         ↓
    one LLM review call (batch)
         ↓
    answers.md (final output)
```

---

## Usage Workflow

### Phase 1: Diagram Ingestion (`/Diagram2Services`)

**User runs:**
```bash
python qa_system.py init DIAGRAM_INGESTED
```

**What happens:**
- System loads `DIAGRAM_INGESTED_questions.json`
- Questions added to `terraform_qa_database.json` with status `[TO BE FILLED]`
- User edits the JSON file directly and fills in answers from the diagram

**Example:**
```json
{
  "What is the project name?": {
    "phase": "DIAGRAM_INGESTED",
    "answer": "ecommerce-platform",
    "category": "Project",
    "required": true
  },
  "What is the target AWS region?": {
    "phase": "DIAGRAM_INGESTED",
    "answer": "us-east-1",
    "category": "Project",
    "required": true
  }
}
```

**User validates:**
```bash
python qa_system.py validate DIAGRAM_INGESTED
```

If all required fields are filled, proceed to Gate 1.

---

### Phase 2: Gate 1 — Services Review (`/ServicesRefiner`)

**User runs:**
```bash
python qa_system.py init GATE1_SERVICES
```

**User edits review/services-review.md** (as normal terraform workflow)

**User fills Q&A:**
- Are service names lowercase-hyphen format?
- Are service types correct?
- Are dependencies documented?

**Then runs:**
```bash
python qa_system.py validate GATE1_SERVICES
```

If valid, proceed with `/ServicesRefinerConfirm` as normal.

---

### Phase 3: Gate 2 — Build Plan (`/ServiceModeler`)

```bash
python qa_system.py init GATE2_BUILD_PLAN
```

Review the build plan and fill in Q&A:
- Are wave assignments correct?
- Are there circular dependencies?
- Is the state backend configuration correct?

Validate:
```bash
python qa_system.py validate GATE2_BUILD_PLAN
```

---

### Phase 4: Gate 3 — Inputs (`/BuildPlan`)

```bash
python qa_system.py init GATE3_INPUTS
```

Fill in variables review:
- Are all required inputs filled?
- Are sensitive variables marked?
- Are defaults appropriate?

---

### Phase 5: Build Services (`/ServiceCodeWriter` + `/TerraformValidator`)

For each service being built:

```bash
python qa_system.py init BUILD_SERVICE
```

After writing the service module, validate:
```bash
python qa_system.py validate BUILD_SERVICE
```

Check:
- Providers pinned?
- No hardcoded secrets?
- All variables externalized?
- terraform validate passed?

---

### Phase 6: Finalize (`/DeployOrchestrator`)

```bash
python qa_system.py init FINALIZE
```

Review finalization:
- Root main.tf outputs correct?
- State backend configured?
- CI/CD templates generated?
- README updated?

---

## Batch Review with Claude

**After filling all phases:**

```bash
python qa_system.py missing
```

This shows any unanswered required questions. Fix them.

**Then trigger LLM review** (optional, in Claude Code):

```
Review all terraform Q&A from terraform_qa_database.json and:
- Check for inconsistencies
- Suggest improvements
- Verify best practices are followed
```

Claude reviews the entire JSON at once (1 API call) instead of answering questions per-phase.

---

## Commands Reference

| Command | Purpose |
|---------|---------|
| `init {phase}` | Load questions for a phase |
| `validate {phase}` | Check if phase is complete |
| `export {phase}` | Export phase Q&A to Markdown |
| `status` | Show all phases and completion status |
| `missing` | Show all unanswered required questions |

**Examples:**
```bash
# Initialize phase
python qa_system.py init DIAGRAM_INGESTED

# Validate before proceeding
python qa_system.py validate GATE1_SERVICES

# Export to Markdown
python qa_system.py export DIAGRAM_INGESTED

# See overall status
python qa_system.py status

# Find missing answers
python qa_system.py missing
```

---

## File Structure

```
.claude/skills/terraform-from-diagram/
├── qa_system.py                               (main script)
├── qa/
│   ├── terraform_qa_database.json             (all Q&A, auto-created)
│   ├── DIAGRAM_INGESTED_questions.json        (phase 1 template)
│   ├── GATE1_SERVICES_questions.json          (phase 2 template)
│   ├── GATE2_BUILD_PLAN_questions.json        (phase 3 template)
│   ├── GATE3_INPUTS_questions.json            (phase 4 template)
│   ├── BUILD_SERVICE_questions.json           (phase 5 template)
│   ├── FINALIZE_questions.json                (phase 6 template)
│   ├── DIAGRAM_INGESTED_answers.md            (exported phase 1)
│   ├── GATE1_SERVICES_answers.md              (exported phase 2)
│   └── ... (more exports)
```

---

## Token Optimization

✅ **No per-question LLM calls** — answers come from manual editing  
✅ **JSON-based** — easy to validate programmatically  
✅ **Batch review** — single Claude API call reviews all answers  
✅ **Minimal context load** — question templates are small JSON files  

### Compared to asking Claude per-question:

| Approach | LLM Calls | Tokens Per Call | Total Tokens |
|----------|-----------|-----------------|--------------|
| **Q&A System** | 1 (review) | ~2000 | ~2000 |
| **Per-question** | 20+ | ~500 each | ~10,000+ |
| **Savings** | 95%+ calls | — | 80%+ tokens |

---

## Integration with Terraform Workflow

### Before each gate command:

```bash
# 1. Initialize Q&A for the phase
python qa_system.py init {PHASE}

# 2. Run the terraform command
/ServicesRefiner  # or /ServiceModeler, /BuildPlan, etc.

# 3. User edits review/services-review.md (or equivalent)

# 4. User fills in Q&A in terraform_qa_database.json

# 5. Validate before proceeding
python qa_system.py validate {PHASE}

# 6. If valid, run the confirm command
/ServicesRefinerConfirm  # or /ServiceModelerConfirm, etc.
```

---

## Editing terraform_qa_database.json

The JSON structure for each answer:

```json
{
  "Question text here?": {
    "phase": "PHASE_NAME",
    "answer": "Your answer here",
    "category": "Category",
    "required": true/false
  }
}
```

### Filling answers:

- **Required** (`required: true`) — Must be filled before validation passes
- **Optional** (`required: false`) — Nice to have, but doesn't block progress
- **[TO BE FILLED]** — Placeholder for unfilled required answers

### Edit directly in any text editor:

```bash
# VS Code
code .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json

# Or any editor
vim .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json
```

---

## Examples

### Example 1: Quick start

```bash
# Initialize and fill phase 1
python qa_system.py init DIAGRAM_INGESTED

# Edit the JSON file, fill in answers
# Validate
python qa_system.py validate DIAGRAM_INGESTED

# Export to Markdown
python qa_system.py export DIAGRAM_INGESTED

# Proceed with terraform workflow
/ServicesRefiner
```

### Example 2: Check progress

```bash
# See overall status
python qa_system.py status

# See what's missing
python qa_system.py missing

# Export specific phase
python qa_system.py export GATE2_BUILD_PLAN
```

### Example 3: Review all answers

```bash
# Once all phases filled
python qa_system.py missing  # Should show "All required answers filled!"

# Export all to Markdown for review
for phase in DIAGRAM_INGESTED GATE1_SERVICES GATE2_BUILD_PLAN GATE3_INPUTS BUILD_SERVICE FINALIZE; do
  python qa_system.py export $phase
done

# Claude reviews all *.md exports (batch LLM review)
```

---

## Notes

- **Q&A is independent of review files** — review/services-review.md and terraform_qa_database.json are separate. One is the terraform workflow UI, the other is structured Q&A data.
- **Persistent** — terraform_qa_database.json is persistent across sessions. Don't lose it!
- **Extensible** — Add new questions to the phase `_questions.json` files anytime.
- **Lightweight** — No external dependencies, just Python and JSON.

---

## Troubleshooting

### "No questions found for phase X"
→ Check that `{PHASE}_questions.json` exists in `.claude/skills/terraform-from-diagram/qa/`

### "Phase is not complete"
→ Run `python qa_system.py missing` to see which required answers are unfilled

### "terraform_qa_database.json not found"
→ Run `python qa_system.py init {PHASE}` to create it

### Want to reset Q&A?
→ Delete `.claude/skills/terraform-from-diagram/qa/terraform_qa_database.json` and re-run `init` for each phase