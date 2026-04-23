---
name: terraform-from-diagram
description: >
  Generates production-ready, modular Terraform scripts from requirements documents and
  draw.io architecture diagrams. Use this skill whenever a user wants to: convert a draw.io
  diagram (.drawio or .xml) to infrastructure-as-code, generate Terraform from architecture
  docs or requirements, scaffold cloud infrastructure from a diagram, build IaC incrementally
  service-by-service, validate Terraform against an architecture spec, or create independently
  testable Terraform modules per service. Triggers on phrases like "terraform from diagram",
  "IaC from architecture", "generate terraform", "infrastructure from drawio", or any request
  to translate a diagram or requirements doc into cloud infrastructure code.
---

# Terraform from Diagram — Agent Workflow

This skill converts draw.io diagrams and/or requirements files into modular, production-grade
Terraform code. It operates as a **supervised agent** with mandatory human review gates before
code generation begins, and builds infrastructure **one service at a time** with dependency
tracking. Each service is independently testable.

---

## 🗺️ Overall Workflow (Always Follow This Order)

```
PHASE 1 — INGEST         → Parse diagram + requirements       command: /Diagram2Services
PHASE 2 — EXTRACT        → Identify services, connections
PHASE 3 — REVIEW GATE 1  → Preview service list (PLAN ONLY)   command: /ServicesRefiner        ← STOP
           └── Human edits review/services-review.md
           └── Human confirms                                  command: /ServicesRefinerConfirm
PHASE 4 — PLAN           → Build dependency graph
PHASE 5 — REVIEW GATE 2  → Preview build plan (PLAN ONLY)     command: /ServiceModeler        ← STOP
           └── Human edits review/build-plan-review.md
           └── Human confirms                                  command: /ServiceModelerConfirm
PHASE 5b— INPUTS GATE    → Preview inputs template (PLAN ONLY) command: /BuildPlan       ← STOP
           └── Human fills review/03_inputs_collection.md
           └── Human confirms                                  command: /BuildPlanConfirm
PHASE 6 — SCAFFOLD       → Create project structure
PHASE 7 — BUILD          → Two commands per service, run one at a time
           ├── 7a /ServiceCodeWriter   → write terraform code (no terraform CLI)
           │                             ↳ status: CODE_WRITTEN
           │                             ↳ prints terminal commands for Option B
           ├── 7b /TerraformValidator  → terraform init/validate/fmt/plan/test
           │                             ↳ status: COMPLETE
           └── /ServiceBuilder (legacy) → writer + validator in one run
           OR write a specific service:                         command: /ServiceCodeWriter {service-name}
           After each: terraform plan on service + dependents (inside Validator)
           Logs everything to execution.md
           Flags Gate 1 suggestions if plan finds issues
PHASE 8 — FINALIZE       → Wire outputs, docs, CI/CD           command: /DeployOrchestrator
```

**Other commands:**
```
/tf-status               → show current state from memory, what's done, what's next
/tf-resume               → read memory and continue from where you left off
/tf-reset                → wipe .claude/memory/ and start fresh
```


### Gate Command Pairs Explained

Each gate has **two commands**:

| First command | What it does |
|--------------|-------------|
| `/ServicesRefiner` | **PLAN MODE** — generates `review/services-review.md` and shows a preview. Nothing is committed to memory. Human reviews and edits the file. |
| `/ServicesRefinerConfirm` | **COMMIT** — reads the (possibly edited) review file, validates it, writes memory, proceeds. |

Same pattern for `/ServiceModeler` → `/ServiceModelerConfirm` and `/BuildPlan` → `/BuildPlanConfirm`.

This means you can run `/ServicesRefiner` as many times as you want, editing the review file between runs, until you're happy. Then `/ServicesRefinerConfirm` locks it in.

**Never skip or merge review gates.** Present review files and wait for explicit confirmation before proceeding to the next phase.

---

## Memory System & Context Management — Read This Before Every Command

**Read `references/memory-system.md` and `references/context-management.md` before every command.**

### Bootstrap sequence (every command, every time)

```
1. Read .claude/memory/handoff.json  → one-line status banner
2. Read .claude/memory/tf-state.json → current phase + gate statuses
3. Load ONLY the reference file needed for this command (see context-management.md)
4. Execute the command
5. Write ALL output to files — never print full content to chat
6. Update handoff.json + tf-state.json
7. Show compact summary (≤ 25 lines) in chat
8. End EVERY response with the /clear instruction block
```

### The `/clear` rule

**Every single command MUST end with:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: {next_command}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

`/clear` resets the token count to zero. All state lives in `.claude/memory/` and
generated files — nothing is lost. The next command reads files, not conversation history.

### Token rules (enforced on every response)

- **≤ 25 lines in chat** — everything else goes to a file
- **Never print `.tf` content to chat** — create the file, show the path
- **Never print full plan output to chat** — write to `execution.md`, show only the summary line
- **Never repeat** content already written to a file
- **Never load** reference files that aren't needed for the current command

---

**Triggered by:** `/Diagram2Services` (attach diagram and/or requirements doc to the message)

**First:** Check `.claude/memory/tf-state.json`. If it exists and shows an in-progress project, ask the user:
```
⚠️ Found existing project "{name}" at phase {phase}.
   Run /tf-resume to continue it, or /tf-reset to start fresh.
```

**Initialize memory** — create `.claude/memory/tf-state.json` with:
```json
{
  "project_name": "pending",
  "current_phase": "DIAGRAM_INGESTED",
  "last_command": "/Diagram2Services",
  "gates": {
    "gate1_services": "PENDING",
    "gate2_build_plan": "PENDING",
    "gate3_inputs": "PENDING",
    "build": "NOT_STARTED",
    "finalize": "NOT_STARTED"
  }
}
```

### What to accept:
- `.drawio` or `.xml` (draw.io export) — parse as XML
- `.md`, `.txt`, `.pdf` — requirements/spec documents
- Both together (preferred — diagram + requirements complement each other)

### How to parse draw.io XML:
Read `references/drawio-parsing.md` for full parsing instructions.

**Quick reference:**
```
mxCell with style containing shape=   → infrastructure component
mxCell with edge="1"                  → dependency/connection between services
value="" attribute                    → label / service name
tooltip="" attribute                  → extra config hints
```

Extract and log all components and edges into a structured list before proceeding.

### If no diagram is provided:
Proceed with requirements doc only — synthesize a logical architecture. Note assumptions clearly.

---

## PHASE 2 — Extract & Normalize

Build a structured inventory from parsed inputs:

```markdown
## Extracted Services

| # | Raw Label (from diagram) | Inferred Type | Cloud Provider | Notes |
|---|--------------------------|---------------|----------------|-------|
| 1 | "api-gw"                 | API Gateway   | AWS            | REST  |
| 2 | "lambda-auth"            | Lambda        | AWS            | Auth handler |
| 3 | "users-db"               | RDS           | AWS            | PostgreSQL |
...

## Extracted Connections

| From        | To          | Type        | Notes              |
|-------------|-------------|-------------|--------------------|
| api-gw      | lambda-auth | invokes     |                    |
| lambda-auth | users-db    | reads/writes| needs sg rule      |
...

## Ambiguities / Assumptions
- "cache" label — assuming ElastiCache Redis (confirm if different)
- No VPC shown — assuming all services in single VPC (confirm)
```

Show this full extraction to the user before Review Gate 1.

---

## PHASE 3 — 🚦 REVIEW GATE 1: Service Names & Inventory

### `/ServicesRefiner` — PLAN MODE (no memory written)

**Memory check:** Confirm `current_phase` is `DIAGRAM_INGESTED` or `GATE1_PENDING`. If earlier, show error.

**What this command does:**
- Generates `review/services-review.md` (read `references/review-workflow.md` for format)
- Shows a preview of the service list and connections detected
- Does NOT write to memory
- Does NOT lock anything

**Tell user:**
```
📋 PLAN MODE — nothing is committed yet.
   Review and edit: review/services-review.md
   Run /ServicesRefiner again to preview changes after editing.
   Run /ServicesRefinerConfirm when ready to lock in service names.
```

You can run `/ServicesRefiner` as many times as needed while editing the file.

---

### `/ServicesRefinerConfirm` — COMMIT

**What this command does:**
1. Reads the current `review/services-review.md`
2. Validates: all service names are lowercase-hyphen format, no duplicates, all types identified
3. Shows a final compact summary (≤ 10 lines):
```
About to lock in:
  • 5 services: networking-vpc, iam-base-roles, rds-users, lambda-auth, api-gateway
  • Region: us-east-1
Confirm? [yes / no]
```
4. On yes — writes `.claude/memory/01-services.json` and updates `tf-state.json` and `handoff.json`
5. **Chat output (compact):**
```
✅ Gate 1 confirmed
   → .claude/memory/01-services.json  (5 services)
   → .claude/memory/tf-state.json     (updated)
   → .claude/memory/handoff.json      (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /ServiceModeler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PHASE 4 — Dependency Graph & Build Plan

Using the confirmed service list and connections, build a dependency graph.

### Ordering rules:
1. **No dependencies** → build first (networking, VPC, IAM foundations)
2. **Foundational services** → next (databases, queues, storage)
3. **Compute/application services** → reference foundation
4. **Edge/gateway services** → built last (reference compute)

### Output a build plan:
```markdown
## Build Plan — Service Order

Wave 1 (No dependencies):
  - [x] networking/vpc
  - [x] iam/base-roles

Wave 2 (Depends on Wave 1):
  - [ ] storage/s3-assets
  - [ ] database/rds-users

Wave 3 (Depends on Wave 2):
  - [ ] compute/lambda-auth
  - [ ] compute/lambda-api

Wave 4 (Depends on Wave 3):
  - [ ] gateway/api-gw

## Module Dependency Map
networking/vpc → database/rds-users (subnet_ids, vpc_id)
iam/base-roles → compute/lambda-auth (execution_role_arn)
...
```

---

## PHASE 5 — 🚦 REVIEW GATE 2: Build Plan

### `/ServiceModeler` — PLAN MODE (no memory written)

**Memory check:** Confirm `gate1_services: "CONFIRMED"` in memory. If not:
```
❌ Cannot run /ServiceModeler — Gate 1 not yet confirmed.
   Run /ServicesRefinerConfirm first.
```

**What this command does:**
- Builds the dependency graph from confirmed services in memory
- Generates `review/build-plan-review.md` with wave order and dependency map
- Does NOT write to memory
- Does NOT lock anything

**Tell user:**
```
📋 PLAN MODE — nothing is committed yet.
   Review and edit: review/build-plan-review.md
   Run /ServiceModeler again to preview after editing.
   Run /ServiceModelerConfirm when ready to lock in the build plan.
```

---

### `/ServiceModelerConfirm` — COMMIT

**What this command does:**
1. Reads `review/build-plan-review.md`
2. Validates: no circular dependencies, all referenced services exist, state backend values filled in
3. Shows compact confirmation:
```
About to lock:  Wave 1→2→3→4  |  5 services  |  state: s3://myproject-tf-state
Confirm? [yes / no]
```
4. On yes — writes `.claude/memory/02-build-plan.json`, updates `tf-state.json` and `handoff.json`
5. **Chat output (compact):**
```
✅ Gate 2 confirmed
   → .claude/memory/02-build-plan.json  (4 waves, 5 services)
   → .claude/memory/handoff.json        (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /BuildPlan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PHASE 5b — 🚦 INPUTS GATE

### `/BuildPlan` — PLAN MODE (no memory written)

**Memory check:** Confirm `gate2_build_plan: "CONFIRMED"` in memory. If not:
```
❌ Cannot run /BuildPlan — Gate 2 not yet confirmed.
   Run /ServiceModelerConfirm first.
```

**What this command does:**
- Generates `review/03_inputs_collection.md` with a table for every service (read `references/inputs-template-guide.md`)
- Pre-fills any values already known from diagram tooltips or prior gate answers
- Shows a count of how many `⚠️ REQUIRED` fields still need values
- Does NOT write to memory

**Tell user:**
```
📋 PLAN MODE — nothing is committed yet.
   Fill in: review/03_inputs_collection.md
   ⚠️ 12 REQUIRED fields need values before confirming.
   Run /BuildPlan again to see remaining gaps after editing.
   Run /BuildPlanConfirm when all required fields are filled.
```

Running `/BuildPlan` again after editing the file will re-check which `⚠️ REQUIRED` fields are still blank and show an updated count.

---

### `/BuildPlanConfirm` — COMMIT

**What this command does:**
1. Reads `review/03_inputs_collection.md`
2. Validates: zero `⚠️ REQUIRED` fields remain blank
3. If blanks remain — lists them and refuses:
```
❌ 3 required fields still blank:
   • rds-users → db_name
   • rds-users → db_username
   • networking-vpc → availability_zones
```
4. On all filled — writes files **without echoing their content to chat**:
   - `environments/dev/terraform.tfvars.example`
   - `environments/prod/terraform.tfvars.example`
   - `.claude/memory/03-inputs.json`
5. **Chat output (compact):**
```
✅ Gate 3 confirmed
   → environments/dev/terraform.tfvars.example   (open to review)
   → environments/prod/terraform.tfvars.example  (open to review)
   → .claude/memory/03-inputs.json               (all config locked)
   → .claude/memory/handoff.json                 (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /ServiceBuilder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Read `references/inputs-template-guide.md` fully before generating this file.**

### How to generate `review/03_inputs_collection.md`:

1. **Start with the Prerequisites Checklist block** (always — from the guide)
2. **Add the Global Configuration section** (always)
3. **For each confirmed service** (in wave order), add that service's input table
4. **Pre-fill known values** from diagram tooltips, requirements doc, or Review Gate answers:
   - Mark auto-detected values with `← from diagram` or `← from requirements`
   - Mark values with no sensible default with `⚠️ REQUIRED`
5. **Show dev vs prod differences** inline — e.g. `true` (prod) / `false` (dev)
6. **Group secrets separately** — remind user these go to Secrets Manager / SSM, NOT tfvars

### Directory structure update:
```
review/
├── services-review.md         ← Gate 1
├── build-plan-review.md       ← Gate 2
└── 03_inputs_collection.md    ← THIS GATE (pre-flight)
```

---

## PHASE 6 — Scaffold Project Structure

Create the standard directory layout:

```
{project-name}/
├── .github/
│   └── workflows/
│       ├── terraform-plan.yml   ← auto-plan on every PR, posts comment
│       └── terraform-apply.yml  ← auto-apply dev; manual gate for prod
├── iam-github-oidc/
│   └── main.tf                  ← one-time bootstrap: creates CI IAM roles (run manually)
├── .gitignore                   ← ALWAYS generate this (see standards)
├── .tflint.hcl                  ← static analysis config
├── README.md                    ← includes local dev setup + CI/CD instructions
├── .terraform-version           # pin exact Terraform version
├── modules/
│   └── {service-name}/          # one folder per service
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── versions.tf          # required_providers ONLY (no required_version)
│       └── tests/
│           ├── main.tftest.hcl  # native Terraform test
│           └── fixtures/
│               └── test.tfvars
├── environments/
│   ├── dev/
│   │   ├── main.tf              # root module, calls child modules
│   │   ├── provider.tf          # profile-aware: local uses AWS_PROFILE, CI uses OIDC role
│   │   ├── versions.tf          # required_version + required_providers (root only)
│   │   ├── variables.tf
│   │   ├── backend.tf
│   │   ├── terraform.tfvars          ← populated from 03_inputs_collection (gitignored)
│   │   └── terraform.tfvars.example  ← safe to commit; no secrets
│   └── prod/
│       ├── main.tf
│       ├── provider.tf
│       ├── versions.tf
│       ├── variables.tf
│       ├── backend.tf
│       ├── terraform.tfvars          ← populated from 03_inputs_collection (gitignored)
│       └── terraform.tfvars.example  ← safe to commit; no secrets
└── review/                      # human review files (kept for audit trail)
    ├── services-review.md
    ├── build-plan-review.md
    └── 03_inputs_collection.md   ← filled-in pre-flight inputs
```

**Always generate `.gitignore` at the project root during scaffolding** — read the
`.gitignore` template in `references/terraform-standards.md`. Key rules:
- `terraform.lock.hcl` → **ALWAYS commit** (never gitignore)
- `terraform.tfvars` → **NEVER commit** (gitignored; use `.tfvars.example` for templates)
- `.terraform/` and `*.tfstate` → **NEVER commit**

**Never use `terraform workspace` for environment separation** — the directory-per-environment
pattern above is the correct approach. Workspaces share a single backend configuration and
make it easy to accidentally target the wrong environment. Always use separate directories.

Read `references/terraform-standards.md` for full coding standards before generating any `.tf` files.

---

## PHASE 7 — Build Services (Two Commands per Service)

Code generation and validation are **two separate commands**. Run them one after
the other. This keeps generated-code commits clean (only the target service's
files change) and lets you inspect code before invoking terraform.

### Command variants

```bash
# 7a — Write code only (no terraform CLI invoked)
/ServiceCodeWriter                   # writes next unwritten service in wave order
/ServiceCodeWriter {service-name}    # writes one specific named service
/ServiceCodeWriter wave:N            # writes next unwritten service in wave N

# 7b — Validate already-written code (runs terraform in terminal)
/TerraformValidator                  # validates next CODE_WRITTEN service
/TerraformValidator service:{name}   # validates one specific service
/TerraformValidator wave:N           # validates every CODE_WRITTEN service in wave N

# Legacy convenience — runs 7a + 7b back-to-back
/ServiceBuilder                      # equivalent to /ServiceCodeWriter then /TerraformValidator
/ServiceBuilder {service-name}
```

### Status machine (tracked in `.claude/memory/04-build-progress.json`)

```
(absent/PENDING) ── /ServiceCodeWriter ──▶ CODE_WRITTEN ── /TerraformValidator ──▶ COMPLETE
                                                │
                                                │  (on validation failure, status stays
                                                │   at CODE_WRITTEN; re-run writer to fix)
                                                └──────────────────────────────────────────┘
```

A service only counts toward wave completion at status `COMPLETE`. Dependency
checks for later waves verify earlier-wave services are `COMPLETE`, not just
`CODE_WRITTEN`.

**Memory check:** Confirm all three gates confirmed in memory. If any missing:
```
❌ Cannot run /ServiceBuilder — not all gates confirmed.
   Gate 1: {status}  Gate 2: {status}  Gate 3: {status}
   Run /tf-status to see what's outstanding.
```

**Load from memory before building:**
- Service list and wave order from `01-services.json`
- Dependency map from `02-build-plan.json`
- All input values from `03-inputs.json`
- Resume position from `04-build-progress.json` if it exists

---

### Targeted build: `/ServiceBuilder {service-name}`

When a service name is passed:
1. Look up that service in `01-services.json` — error if not found:
   ```
   ❌ Service "my-service" not found. Known services: networking-vpc, rds-users, ...
   ```
2. Check its dependencies are all already built. If not:
   ```
   ❌ Cannot build lambda-auth — dependencies not yet built:
      • rds-users (Wave 2) — not built
      • iam-base-roles (Wave 1) — not built
      Build those first, or run /ServiceBuilder to proceed in order.
   ```
3. If dependencies are satisfied — build only that one service using steps 7a–7g below
4. After build — run terraform plan on that service and its dependents (step 7e)
5. Update execution.md and memory

---

### Resume behaviour: `/ServiceBuilder` (no parameter)

If `04-build-progress.json` shows a partial build, announce:
```
🔄 Resuming build — 2/5 services already complete
   Completed: networking-vpc, iam-base-roles
   Next: rds-users
```

Then build the **next single service** in wave order and stop. The user runs `/ServiceBuilder` again for the next one, or runs `/ServiceBuilder` to keep building — each run processes exactly one service.

> **Why one at a time?** Each service build + plan cycle may reveal issues that should be
> fixed before proceeding. Stopping after each gives the user a chance to review
> `execution.md` and act on any Gate 1 suggestions before the next service starts.

---

### Steps for each service

**Steps 7a–7d belong to `/ServiceCodeWriter`** (no terraform CLI is invoked).
**Steps 7e–7h belong to `/TerraformValidator`** (terraform runs in the terminal).
The legacy `/ServiceBuilder` runs all of these back-to-back in one command.
The authoritative definitions live in
[ServiceCodeWriter.md](../../commands/ServiceCodeWriter.md) and
[TerraformValidator.md](../../commands/TerraformValidator.md)
— this section is a summary.

#### Phase 1 — `/ServiceCodeWriter`

**Step 7a — Announce** *(writer)*
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▶ Writing code for: rds-users   [Wave 2 of 4]  (3 of 5 total)
  Type:         aws_db_instance
  Depends on:   networking-vpc (vpc_id, private_subnet_ids)
  Will export:  db_endpoint, db_port, secret_arn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Append this header to `execution.md` immediately.

**Step 7b — Generate module files** *(writer)*
Generate all 5 files using values from `03-inputs.json`.
**Write directly to disk. Do NOT print file contents to chat.**
After writing, show only:
```
   Generated: modules/rds-users/  (main.tf, variables.tf, outputs.tf, versions.tf, tests/)
```

Follow all standards in `references/terraform-standards.md`.

**Step 7c — Write per-service wiring file** *(writer)*
Write exactly one file per environment: `environments/{dev,prod}/modules/{service-name}.tf`
containing only this service's `module { ... }` block. Never edit the shared
`environments/{dev,prod}/main.tf`. If previously-built services depend on this
service's new outputs, update only their `modules/{dep}/variables.tf`.
```
   ↺ Wired: environments/{dev,prod}/modules/rds-users.tf
      Dependent vars updated: lambda-auth/variables.tf
```

**Step 7d — Lightweight sanity checks** *(writer — no terraform CLI)*
In-process text checks: file presence, brace/quote balance, versions.tf contract,
tags, no hardcoded regions/account-IDs, all `var.*` references declared.
Detailed per-check output to `execution.md`. Show only pass/fail in chat.
On failure, stop here. Do NOT update memory status. User re-runs
`/ServiceCodeWriter {name}` to regenerate.

On success, mark the service `CODE_WRITTEN` in `04-build-progress.json`, set
`handoff.json.next_command = "/TerraformValidator service:{name}"`, and
print the NEXT STEPS block:
```
▶  NEXT STEPS — validate the generated code
   Option A:  /TerraformValidator service:rds-users
   Option B:  cd terraform/modules/rds-users
              terraform init -backend=false
              terraform validate
              terraform fmt -check
```

#### Phase 2 — `/TerraformValidator`

**Step 7e — terraform init/validate/fmt** *(validator — runs in terminal)*
```bash
cd modules/{service-name}
terraform init -backend=false
terraform validate
terraform fmt -check
```
Write full output to `execution.md`. Show only pass/fail per command in chat.

**Step 7f — `terraform plan` on service and ALL dependents** *(validator)*
Write FULL plan output to:
- `execution.md` (append)
- `.claude/memory/last-plan.txt` (overwrite)

Show ONLY the summary line in chat:
```
   Plan: 8 to add, 0 to change, 0 to destroy.
   Dependents: lambda-auth ✅
```

**Step 7g — `terraform test`** *(validator)*
```bash
cd modules/{service-name}
terraform test
```

**Step 7h — Update memory, handoff, and end with /clear** *(validator — success only)*
On success, flip status `CODE_WRITTEN` → `COMPLETE` in `04-build-progress.json`,
append to `tf-state.json.build_progress.completed`, and set
`handoff.json.next_command` to `/ServiceCodeWriter` (next service) or
`/DeployOrchestrator` (all done).

On failure, leave status at `CODE_WRITTEN`. The chat prints the failing command
and suggests re-running `/ServiceCodeWriter {name}` to regenerate.

**Chat output on success (total ≤ 15 lines):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ rds-users VALIDATED → COMPLETE  [3/5 — Wave 2]
   Validate:   ✅ passed
   Plan:       8 to add, 0 to change
   Dependents: lambda-auth ✅
   Tests:      3/3 passed
   Log:        → execution.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /ServiceCodeWriter   (next: lambda-auth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### execution.md Format

The skill creates and maintains `execution.md` in the project root throughout the build.
It is append-only — never overwrite existing entries.

```markdown
# Build Execution Log
Project: {project-name}
Started: {timestamp}

---

## 🔄 Build Started
- Gate 1 confirmed: {timestamp}
- Gate 2 confirmed: {timestamp}
- Gate 3 confirmed: {timestamp}
- Services to build: networking-vpc, iam-base-roles, rds-users, lambda-auth, api-gateway
- Build order: Wave 1 → Wave 2 → Wave 3 → Wave 4

---

## ▶ networking-vpc — Building  [Wave 1]  {timestamp}
### Generated files
- modules/networking-vpc/main.tf
- modules/networking-vpc/variables.tf
- modules/networking-vpc/outputs.tf
- modules/networking-vpc/versions.tf
- modules/networking-vpc/tests/main.tftest.hcl

### Validation
- terraform validate: ✅ passed
- terraform fmt:      ✅ passed

### Terraform Plan — networking-vpc
```hcl
Plan: 12 to add, 0 to change, 0 to destroy.
  + aws_vpc.main
  + aws_subnet.private[0]
  + aws_subnet.private[1]
  ...
```

### Tests
- plan_succeeds_with_valid_inputs: ✅
- rejects_invalid_environment:     ✅
- tags_are_applied:                ✅

### Gate 1 Suggestions
none

## ✅ networking-vpc — COMPLETE  {timestamp}

---

## ▶ rds-users — Building  [Wave 2]  {timestamp}
...

## ⚠️ Gate 1 Suggestion
Service:        lambda-auth
Issue:          Plan error — missing vpc_config, cannot reach RDS in private subnet
Suggestion:     Add connection lambda-auth → networking-vpc in services-review.md
Recommended fix: Edit review/services-review.md connections table, run /ServicesRefiner to preview
Impact:         Adds vpc_subnet_ids, vpc_security_group_ids variables to lambda-auth

---
```

---

## `/ServiceBuilder` Prerequisite and Gate Enforcement

| Check | Rule |
|-------|------|
| All 3 gates confirmed | Required before any build |
| Targeted build (`/ServiceBuilder svc`) | All dependencies of that service must be built first |
| Sequential build (`/ServiceBuilder`) | Builds exactly one service per run — user controls pace |
| After each service | Always runs terraform plan on service + dependents |
| On plan error | Logs to execution.md, generates Gate 1 suggestion if applicable, stops build |

---

## PHASE 8 — Finalize

**Triggered by:** `/DeployOrchestrator`

**Memory check:** Confirm `build_progress.remaining` is empty in `04-build-progress.json`. If services are still unbuilt:
```
❌ Cannot run /DeployOrchestrator — build not complete.
   Built: 3/5 services. Run /ServiceBuilder to complete remaining services.
```

**Read `references/cicd-and-local-dev.md` fully before generating any files in this phase.**

1. **Root module wiring** — Ensure `environments/dev/main.tf` passes all cross-module outputs correctly
2. **Generate `provider.tf`** for each environment — profile-aware (local uses `AWS_PROFILE`, CI uses OIDC role with no profile set). Use the template from `references/cicd-and-local-dev.md`.
3. **Generate GitHub Actions workflows:**
   - `.github/workflows/terraform-plan.yml` — runs plan on every PR, posts output as comment
   - `.github/workflows/terraform-apply.yml` — applies dev on merge to main; applies prod after manual approval
4. **Generate `iam-github-oidc/main.tf`** — one-time bootstrap module to create OIDC roles for CI. User runs this once manually before the pipeline works.
5. **Generate `README.md`** — must include: architecture summary, prerequisites, local dev setup (tool install, AWS profile config, first-time init, daily workflow), CI/CD pipeline explanation, and GitHub Actions one-time setup steps. Use the README template from `references/cicd-and-local-dev.md`.
6. **Generate `environments/dev/terraform.tfvars.example`** — all required variables with placeholder values and comments
7. **Run full validation and static analysis (from project root) — write results to execution.md, show only pass/fail in chat:**
```bash
terraform fmt -recursive
cd environments/dev && terraform init -backend=false && terraform validate
tflint --recursive
checkov -d . --framework terraform
```
8. **Show compact final summary (≤ 20 lines):**
```
✅ Project complete  —  {n} services  |  ~{x} resources

Files:
  modules/          {n} modules
  environments/     dev + prod
  .github/          terraform-plan.yml, terraform-apply.yml
  iam-github-oidc/  main.tf
  execution.md      full build log
  README.md         local dev + CI/CD guide

Validation: fmt ✅  validate ✅  tflint ✅  checkov ✅

Next steps:
  1. make setup                (first-time local init)
  2. make plan                 (see what will change)
  3. cd iam-github-oidc && terraform apply  (CI bootstrap, once)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    (No next skill command — project is complete)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Individual Service Testing

Every module includes a `tests/main.tftest.hcl` using Terraform's native test framework.

Read `references/terraform-standards.md#testing` for test patterns.

To test a single service:
```bash
cd modules/{service-name}
terraform test                     # runs tests/main.tftest.hcl
terraform test -filter="test_name" # runs a specific test
```

Tests use `mock_provider` blocks so no real cloud credentials are needed for unit tests.

---

## Key Constraints (Always Enforce)

- **Never** put secrets or real values in `.tf` files — always use `var.*` references
- **Never** use `count` for services that need individual identity — use `for_each`  
- **Always** pin provider versions with `~>` constraints
- **Always** use remote state for cross-module data sharing (use `terraform_remote_state` or outputs)
- **Always** separate `variables.tf`, `outputs.tf` from `main.tf`
- **Never** hardcode region — always `var.region`
- Tag every taggable resource

---

## Command Handlers

### `/tf-status`
Read `.claude/memory/handoff.json` then `.claude/memory/tf-state.json` and show compact status (≤ 15 lines). No reference files needed.

Read `.claude/memory/tf-state.json` and show a full project status summary:

```
📂 Project: myproject
   Region:  us-east-1
   Updated: 2024-01-15 14:32

Gates:
  ✅ Gate 1 — Services confirmed (5 services)
  ✅ Gate 2 — Build plan confirmed
  ⏳ Gate 3 — Inputs: run /BuildPlan to preview, /BuildPlanConfirm when filled

Build:
  NOT STARTED

Next command: /BuildPlan
```

### `/tf-resume`
Read memory and pick up from the current phase:
- Show the status summary (same as `/tf-status`)
- Then immediately continue the current phase without waiting for another command
- Example: if memory shows `MODEL_CONFIRMED`, generate `review/03_inputs_collection.md` automatically

### `/tf-reset`
```
⚠️ This will delete all memory for project "{name}" and start fresh.
   Your generated Terraform files will NOT be deleted.
   Type "reset" to confirm, or anything else to cancel.
```
On confirmation: delete all files in `.claude/memory/`, confirm deletion.

---

## Reference Files

| File | When to Load | Token cost |
|------|-------------|-----------|
| `references/context-management.md` | **Every command — load first** | low |
| `references/memory-system.md` | Every command | low |
| `references/drawio-parsing.md` | `/Diagram2Services` only | medium |
| `references/review-workflow.md` | Gate commands only | medium |
| `references/inputs-template-guide.md` | `/BuildPlan` only | high |
| `references/terraform-standards.md` | `/ServiceBuilder` only | high |
| `references/cicd-and-local-dev.md` | `/DeployOrchestrator` only | high |
| `references/iam-roles-reference.md` | `/IAMModeler`, `/ServiceBuilder`, `/ServiceModeler` | medium |

**Never load high-cost reference files for commands that don't need them.**
