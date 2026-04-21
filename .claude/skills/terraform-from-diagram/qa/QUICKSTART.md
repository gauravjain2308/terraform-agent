# Terraform QA System — Quick Start

**Minimize tokens by collecting answers in JSON, reviewing once with Claude.**

---

## 30-Second Start

```bash
# 1. Initialize phase
python qa_system.py init DIAGRAM_INGESTED

# 2. Edit and fill
vim .claude/skills/terraform-from-diagram/qa/terraform_qa_database.json

# 3. Validate
python qa_system.py validate DIAGRAM_INGESTED

# 4. Export to Markdown
python qa_system.py export DIAGRAM_INGESTED

# Done! Proceed with /ServicesRefiner
```

---

## Common Tasks

### See what needs to be answered
```bash
python qa_system.py missing
```

### Show progress across all phases
```bash
python qa_system.py status
```

### Check if phase is ready to proceed
```bash
python qa_system.py validate GATE1_SERVICES
```

### Export phase answers to Markdown
```bash
python qa_system.py export BUILD_SERVICE
```

---

## Phase Checklist

```
☐ DIAGRAM_INGESTED     → init, fill JSON, validate → /ServicesRefiner
☐ GATE1_SERVICES       → init, fill JSON, validate → /ServiceModeler
☐ GATE2_BUILD_PLAN     → init, fill JSON, validate → /BuildPlan
☐ GATE3_INPUTS         → init, fill JSON, validate → /ServiceCodeWriter
☐ BUILD_SERVICE        → init, fill JSON, validate (per service)
☐ FINALIZE             → init, fill JSON, validate → /DeployOrchestrator
☐ REVIEW               → python qa_system.py missing → Claude review all
```

---

## File Location

All Q&A files live in:
```
.claude/skills/terraform-from-diagram/qa/
```

Edit this file:
```
.claude/skills/terraform-from-diagram/qa/terraform_qa_database.json
```

---

## Why Use This?

| Feature | Benefit |
|---------|---------|
| **JSON storage** | Easy to edit, validate, and persist |
| **Phase templates** | Consistent questions per phase |
| **Batch validation** | Check completeness before proceeding |
| **One review call** | Ask Claude once for all answers, not per-question |
| **Markdown export** | Handoff documentation ready |
| **80%+ token savings** | 1 review call vs 20+ per-question calls |

---

## Example

### After filling terraform_qa_database.json:

```json
{
  "What is the project name?": {
    "phase": "DIAGRAM_INGESTED",
    "answer": "my-api-platform",
    "category": "Project",
    "required": true
  },
  "Are all service names lowercase-hyphen?": {
    "phase": "GATE1_SERVICES",
    "answer": "Yes, all services follow naming convention: api-gateway, rds-users, lambda-auth",
    "category": "Naming",
    "required": true
  },
  "Are there any circular dependencies?": {
    "phase": "GATE2_BUILD_PLAN",
    "answer": "No circular dependencies found. Wave order verified.",
    "category": "Dependencies",
    "required": true
  }
}
```

### Validate & Export:

```bash
python qa_system.py validate DIAGRAM_INGESTED
# ✅ Phase 'DIAGRAM_INGESTED' — all required answers filled!

python qa_system.py export DIAGRAM_INGESTED
# ✅ Exported: .claude/skills/terraform-from-diagram/qa/DIAGRAM_INGESTED_answers.md
```

---

## Next Steps

1. Run `python qa_system.py init {PHASE}` at the start of each phase
2. Edit the JSON file with answers
3. Run `python qa_system.py validate {PHASE}` before proceeding
4. After filling all phases, run `python qa_system.py missing` 
5. Share exported Markdown files for handoff

See `TERRAFORM_QA_INTEGRATION.md` for full documentation.