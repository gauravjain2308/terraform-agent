# Context Management & Token Reduction

This file defines how the skill minimises token usage across every command.
**Read this before every command.** These rules are not optional.

---

## Core Principle

Every command is **stateless by design** — it reads from files, acts, writes to files,
then the conversation context is cleared. The next command starts fresh from files only.

```
Command runs → reads memory files → acts → writes all output to files
→ prints compact summary to chat (≤ 20 lines)
→ tells user to /clear
→ next command starts with clean context, reads files
```

---

## Rule 1 — Always End With a `/clear` Instruction

Every single command response MUST end with this block:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: {next_command}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This tells the user to clear the conversation before running the next command.
Because all state is in `.claude/memory/` and generated files, nothing is lost.

---

## Rule 2 — Write to Files, Never Print to Chat

| Content type | Where it goes |
|-------------|--------------|
| Generated `.tf` files | Written to disk via `create_file`. Never echoed to chat. |
| `terraform plan` output | Written to `execution.md` and `.claude/memory/last-plan.txt`. Never printed in full to chat. |
| Review gate files | Written to `review/*.md`. Never echoed in full to chat. |
| Validation output | Written to `execution.md`. Only pass/fail shown in chat. |
| Reference file contents | Read internally. Never repeated back to chat. |

**In chat:** only show the compact summary (what was done, key decisions, next step).

---

## Rule 3 — Hard Chat Response Limit

Every command response must fit in **≤ 25 lines of chat output**.

If content is longer, write it to a file and reference the path:
```
✅ Generated modules/rds-users/main.tf  (47 lines)
   → open in VS Code to review
```

Never say "Here is the content of main.tf:" and then print it. Just create the file.

---

## Rule 4 — Handoff File

At the end of every command, write `.claude/memory/handoff.json`.
This is what the next command reads FIRST — a compact bootstrap with only what's needed.

```json
{
  "last_command": "/ServicesRefinerConfirm",
  "completed_at": "2024-01-15T14:00:00Z",
  "phase": "SERVICES_REFINED",
  "next_command": "/ServiceModeler",
  "next_action": "Generate build plan from 5 confirmed services",
  "quick_context": {
    "project": "myproject",
    "region": "us-east-1",
    "services": ["networking-vpc", "iam-base-roles", "rds-users", "lambda-auth", "api-gateway"],
    "current_wave": null,
    "last_built": null
  },
  "files_written": [
    "review/services-review.md",
    ".claude/memory/01-services.json"
  ]
}
```

On the next command, Claude reads `handoff.json` FIRST and uses it to bootstrap.
This avoids re-reading large memory files when only the quick context is needed.

---

## Rule 5 — Lazy Reference Loading

Load reference files **only when the current command actually needs them**.

| Command | Load these references | Skip these |
|---------|----------------------|-----------|
| `/Diagram2Services` | drawio-parsing.md | all others |
| `/ServicesRefiner`, `/ServicesRefinerConfirm` | review-workflow.md | all others |
| `/ServiceModeler`, `/ServiceModelerConfirm` | review-workflow.md | all others |
| `/BuildPlan`, `/BuildPlanConfirm` | inputs-template-guide.md, review-workflow.md | others |
| `/ServiceBuilder` | terraform-standards.md | all others |
| `/DeployOrchestrator` | cicd-and-local-dev.md | all others |
| `/tf-status`, `/tf-resume` | none (memory files only) | all |

Never pre-load all reference files "just in case."

---

## Rule 6 — No Repetition

Never repeat information already written to a file.

❌ Bad:
```
I've confirmed these services:
  1. networking-vpc — aws_vpc
  2. rds-users — aws_db_instance
  3. lambda-auth — aws_lambda_function
  ...
(and then writes the same thing to 01-services.json)
```

✅ Good:
```
✅ 5 services confirmed → .claude/memory/01-services.json
```

If the user wants to see the content, they open the file.

---

## Rule 7 — Compact Status Banner

Every command starts with a one-line banner read from `handoff.json`:

```
📂 myproject  |  SERVICES_REFINED  |  next: /ServiceModeler
```

That is all. Do not re-explain what was done in the previous session.

---

## Rule 8 — Plan Output Truncation

`terraform plan` output can be very long. Apply these rules:

1. Write the FULL output to `.claude/memory/last-plan.txt` and append to `execution.md`
2. In chat, show ONLY the summary line:
   ```
   Plan: 8 to add, 0 to change, 0 to destroy.
   ```
3. If there are errors or warnings, show those specifically (max 10 lines)
4. Add: `Full output → execution.md`

---

## Rule 9 — Build Step Verbosity

During `/ServiceBuilder`, after each service:

**In chat (compact):**
```
✅ rds-users  [3/5]
   plan: 8 add  |  tests: 3/3  |  dependents: ✅
   → execution.md updated
   /clear  then  /ServiceBuilder
```

**In execution.md (full detail):**
Everything — full plan output, all validation lines, all test results.

---

## Rule 10 — Reference File Read Confirmation

When loading a reference file, do NOT reprint its contents into chat.
Just confirm silently that it was read, then act on it.

❌ Bad: "I've read terraform-standards.md. Here is its content: ..."
✅ Good: (reads file silently, generates code per its rules, shows compact output)

---

## The `/clear` Workflow Explained

`/clear` in Claude Code clears the conversation history but NOT the filesystem.
That means:

- `.claude/memory/` files → **preserved** ✅
- Generated `.tf` files → **preserved** ✅
- `execution.md` → **preserved** ✅
- Review gate files → **preserved** ✅
- Conversation context / token count → **reset to zero** ✅

This is why the memory-file-first design enables aggressive context clearing — nothing
useful lives in conversation history.

---

## Token Budget Targets Per Command

| Command | Target context size |
|---------|-------------------|
| `/Diagram2Services` | < 8K tokens (diagram + extraction) |
| `/ServicesRefiner` | < 4K tokens (read memory + write review file) |
| `/ServicesRefinerConfirm` | < 3K tokens (validate + write memory) |
| `/ServiceModeler` | < 4K tokens |
| `/ServiceModelerConfirm` | < 3K tokens |
| `/BuildPlan` | < 6K tokens (inputs template is large) |
| `/BuildPlanConfirm` | < 4K tokens |
| `/ServiceBuilder` | < 8K tokens per service (standards ref + generate + plan output) |
| `/DeployOrchestrator` | < 6K tokens |
| `/tf-status` | < 1K tokens (read handoff.json only) |

If a command is exceeding its budget, split it or write more to files.

---

## Checklist for Every Command Response

Before finishing any response, verify:

- [ ] Compact chat output (≤ 25 lines)?
- [ ] All generated code written to files, not printed to chat?
- [ ] Plan output written to execution.md, only summary shown in chat?
- [ ] `handoff.json` updated?
- [ ] `/clear` instruction at the end?
- [ ] No content repeated from previous commands?
- [ ] Only necessary reference files loaded?
