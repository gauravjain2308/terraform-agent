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

## Overall Workflow (Always Follow This Order)

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
PHASE 5b— INPUTS GATE    → Preview inputs template (PLAN ONLY) command: /BuildPlan            ← STOP
           └── Human fills review/03_inputs_collection.md
           └── Human confirms                                  command: /BuildPlanConfirm
PHASE 6 — SCAFFOLD       → Create project structure
PHASE 7 — BUILD          → Two commands per service, run one at a time
           ├── 7a /ServiceCodeWriter   → write terraform code (no terraform CLI)
           ├── 7b /TerraformValidator  → terraform init/validate/fmt/plan/test
           └── /ServiceBuilder (legacy) → writer + validator in one run
PHASE 8 — FINALIZE       → Wire outputs, docs, CI/CD           command: /DeployOrchestrator
```

**Other commands:**
```
/tf-status  → show current state
/tf-resume  → read memory and continue from where you left off
/tf-reset   → wipe .claude/memory/ and start fresh
```

---

## Gate Command Pairs

Each gate has two commands: a **PLAN** command (writes a review file, commits nothing) and a **COMMIT** command (validates the file, writes memory, locks the gate).

| Gate | Plan command | Commit command |
|------|-------------|----------------|
| Gate 1 — Services | `/ServicesRefiner` | `/ServicesRefinerConfirm` |
| Gate 2 — Build plan | `/ServiceModeler` | `/ServiceModelerConfirm` |
| Gate 3 — Inputs | `/BuildPlan` | `/BuildPlanConfirm` |

Re-run the Plan command as many times as needed while editing the review file. The Commit command locks it in.

**Never skip or merge review gates.** Present review files and wait for explicit confirmation before proceeding.

---

## Memory System & Context Management — Read Before Every Command

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

### Token rules

- **≤ 25 lines in chat** — everything else goes to a file
- **Never print `.tf` content to chat** — create the file, show the path
- **Never print full plan output to chat** — write to `execution.md`, show only the summary line
- **Never repeat** content already written to a file
- **Never load** reference files that aren't needed for the current command

---

## Phase Handlers

### PHASE 1 — `/Diagram2Services`

**First:** Check `.claude/memory/tf-state.json`. If it exists and shows an in-progress project, ask:
```
⚠️ Found existing project "{name}" at phase {phase}.
   Run /tf-resume to continue it, or /tf-reset to start fresh.
```

**Initialize memory** — create `.claude/memory/tf-state.json`:
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

Accept: `.drawio`/`.xml`, `.md`/`.txt`/`.pdf`, or both (preferred).
**Diagram lookup order:** attached file first; if none attached, look **only in `docs/`** — do not search anywhere else in the workspace. If no file is found in `docs/`, stop and ask the user to place the file there.
Parse draw.io XML → read `references/drawio-parsing.md` for full instructions.
If no diagram: proceed with requirements only, note assumptions clearly.

---

### PHASE 2 — Extract & Normalize

Build a structured inventory from parsed inputs. See `references/extraction-template.md` for the output format.
Show the full extraction to the user before Review Gate 1.

---

### PHASE 3 — Gate 1: `/ServicesRefiner` + `/ServicesRefinerConfirm`

**Check:** `current_phase` must be `DIAGRAM_INGESTED` or `GATE1_PENDING`.

**`/ServicesRefiner`** — reads `references/review-workflow.md`, generates `review/services-review.md`, shows PLAN MODE message, does NOT write memory.

**`/ServicesRefinerConfirm`** — validates names (lowercase-hyphen, no dupes, all types identified), shows compact confirmation (≤ 10 lines), writes `.claude/memory/01-services.json`.

---

### PHASE 4 — Dependency Graph

Read `references/build-plan-guide.md` for ordering rules and output format.

---

### PHASE 5 — Gate 2: `/ServiceModeler` + `/ServiceModelerConfirm`

**Check:** `gate1_services: "CONFIRMED"` required in memory. If missing, refuse and show error.

**`/ServiceModeler`** — builds dependency graph from confirmed services, generates `review/build-plan-review.md`, PLAN MODE (nothing written to memory).

**`/ServiceModelerConfirm`** — validates (no circular deps, all services exist, state backend filled), writes `.claude/memory/02-build-plan.json`.

---

### PHASE 5b — Inputs Gate: `/BuildPlan` + `/BuildPlanConfirm`

**Check:** `gate2_build_plan: "CONFIRMED"` required. If missing, refuse and show error.

**`/BuildPlan`** — reads `references/inputs-template-guide.md`, generates `review/03_inputs_collection.md`, shows count of `⚠️ REQUIRED` fields remaining. Re-run after editing to see updated count.

**`/BuildPlanConfirm`** — validates zero required fields blank; writes `environments/dev/terraform.tfvars.example`, `environments/prod/terraform.tfvars.example`, `.claude/memory/03-inputs.json`.

---

### PHASE 6 — Scaffold

Create project directory structure. Read `references/project-structure.md` for the full directory tree and `.gitignore` rules.
Read `references/terraform-standards.md` before generating any `.tf` files.
Read `references/bootstrap-guide.md` and generate the `state-bootstrap/` module (3 files: `main.tf`, `variables.tf`, `versions.tf`). This module must be created during scaffold — it is required before `terraform init` can succeed.

---

### PHASE 7 — Build: `/ServiceCodeWriter` + `/TerraformValidator`

**Check:** All 3 gates confirmed. Load `01-services.json`, `02-build-plan.json`, `03-inputs.json`, `04-build-progress.json`.

**Command variants:**
```bash
/ServiceCodeWriter                 # next unwritten service in wave order
/ServiceCodeWriter {service-name}  # specific service
/ServiceCodeWriter wave:N          # next unwritten in wave N
/TerraformValidator                # next CODE_WRITTEN service
/TerraformValidator service:{name}
/TerraformValidator wave:N
/ServiceBuilder                    # legacy: writer + validator back-to-back
```

**Status machine** (tracked in `04-build-progress.json`):
```
PENDING → [/ServiceCodeWriter] → CODE_WRITTEN → [/TerraformValidator] → COMPLETE
```
Wave N builds only start when all Wave N-1 services are `COMPLETE`.

Read `references/service-building-steps.md` for steps 7a–7h.
Read `references/execution-format.md` for the execution.md append format.

---

### PHASE 8 — Finalize: `/DeployOrchestrator`

**Check:** `build_progress.remaining` must be empty in `04-build-progress.json`.
Read `references/finalize-checklist.md` for all 8 steps, CI/CD templates, and the final summary format.
Read `references/cicd-and-local-dev.md` fully before generating any files.

---

## Key Constraints (Always Enforce)

- **Never** put secrets in `.tf` files — always use `var.*` references
- **Never** use `count` for services needing individual identity — use `for_each`
- **Always** pin provider versions with `~>` constraints
- **Always** use remote state for cross-module data sharing
- **Always** separate `variables.tf`, `outputs.tf` from `main.tf`
- **Never** hardcode region — always `var.region`
- Tag every taggable resource

---

## Command Handlers

### `/tf-status`
Read `handoff.json` then `tf-state.json`. Show compact status (≤ 15 lines). No reference files needed.

```
📂 Project: {project_name}
   Region:  {region}
   Updated: {timestamp}

Gates:
  {✅|⏳} Gate 1 — Services {confirmed ({N} services) | pending}
  {✅|⏳} Gate 2 — Build plan {confirmed | pending}
  {✅|⏳} Gate 3 — Inputs {confirmed | run /BuildPlan to preview}

Build:
  {NOT STARTED | {N}/{M} services complete}

Next command: {next_command}
```

### `/tf-resume`
Read memory, show status summary (same as `/tf-status`), then immediately continue the current phase without waiting for another command.

### `/tf-reset`
```
⚠️ This will delete all memory for project "{name}" and start fresh.
   Your generated Terraform files will NOT be deleted.
   Type "reset" to confirm, or anything else to cancel.
```
On confirmation: delete all files in `.claude/memory/`, confirm deletion.

---

## Reference Files

| File | When to load |
|------|-------------|
| `references/context-management.md` | **Every command — load first** |
| `references/memory-system.md` | Every command |
| `references/drawio-parsing.md` | `/Diagram2Services` only |
| `references/extraction-template.md` | `/Diagram2Services` — Phase 2 output format |
| `references/review-workflow.md` | Gate commands only |
| `references/build-plan-guide.md` | `/ServiceModeler` only |
| `references/inputs-template-guide.md` | `/BuildPlan` only |
| `references/project-structure.md` | `/tf-scaffold` only |
| `references/bootstrap-guide.md` | `/tf-scaffold` (Phase 6) and `/DeployOrchestrator` (Phase 8) |
| `references/service-building-steps.md` | `/ServiceCodeWriter`, `/TerraformValidator`, `/ServiceBuilder` |
| `references/execution-format.md` | Build commands (when appending to execution.md) |
| `references/finalize-checklist.md` | `/DeployOrchestrator` only |
| `references/terraform-standards.md` | `/ServiceBuilder`, `/ServiceCodeWriter` |
| `references/cicd-and-local-dev.md` | `/DeployOrchestrator` only |
| `references/iam-roles-reference.md` | `/IAMModeler`, `/ServiceBuilder`, `/ServiceModeler` |

**Never load high-cost reference files for commands that don't need them.**

---

## Module Roles — What Each Reference File Is For

Each file in `references/` is a focused module loaded on-demand. This section explains the
**role** of every module so you know exactly which one to reach for.

---

### `references/context-management.md`
**Role: Token Budget Enforcer**
Defines rules to keep every response within the 25-line chat limit. Controls which reference
files may be loaded per command, prevents re-reading files already in context, and sets the
`/clear` cadence. **Load before every command** — it overrides all other loading decisions.

---

### `references/memory-system.md`
**Role: State Persistence Contract**
Documents the `.claude/memory/` folder schema: which JSON files exist, what each field means,
how gates are written and read, and how `handoff.json` carries a one-line status banner between
sessions. Load on every command to know where to read/write state.

---

### `references/drawio-parsing.md`
**Role: Diagram XML Parser**
Explains how to read a `.drawio` / `.xml` export and extract infrastructure components —
nodes, edges, labels, and service types — from the raw XML structure. Used only during
`/Diagram2Services` (Phase 1).

---

### `references/extraction-template.md`
**Role: Phase 2 Output Formatter**
Defines the exact markdown structure for the service inventory produced in Phase 2 (Extract &
Normalize). The template covers service name, type, connections, environment variables, and
open questions. Used only after diagram parsing, before Gate 1.

---

### `references/review-workflow.md`
**Role: Human Review Gate Presenter**
Specifies the format for every review file written at a gate (`services-review.md`,
`build-plan-review.md`, `03_inputs_collection.md`). Ensures the human can scan, edit, and
approve quickly. Load for any gate PLAN command (`/ServicesRefiner`, `/ServiceModeler`,
`/BuildPlan`).

---

### `references/build-plan-guide.md`
**Role: Dependency Graph Builder**
Defines the wave-ordering rules (which services must build first), the format of
`02-build-plan.json`, and how to detect circular dependencies. Load only for `/ServiceModeler`
(Phase 5) when constructing the build plan.

---

### `references/inputs-template-guide.md`
**Role: Pre-flight Inputs Collector**
Describes how to generate `review/03_inputs_collection.md` — the single file that lists every
Terraform variable, its default, and whether it is `⚠️ REQUIRED` (blank = must be filled before
build). Load only for `/BuildPlan` (Phase 5b).

---

### `references/project-structure.md`
**Role: Directory Scaffolder**
Defines the canonical folder layout for a generated Terraform project: module directories,
environment folders, state backend config, `.gitignore` rules, and placeholder files. Load only
during Phase 6 (`/tf-scaffold`).

---

### `references/terraform-standards.md`
**Role: Code Quality Rulebook**
All coding standards for generated `.tf` files: provider pinning, `for_each` vs `count`, tag
strategy, variable/output file separation, no hardcoded regions or secrets, and naming
conventions. Load before any code generation (`/ServiceCodeWriter`, `/ServiceBuilder`).

---

### `references/service-building-steps.md`
**Role: Per-Service Build Playbook**
Details steps 7a–7h for building one service module. Steps 7a–7d belong to
`/ServiceCodeWriter` (pure file writing, no CLI); steps 7e–7h belong to `/TerraformValidator`
(`terraform init / validate / fmt / plan`). The legacy `/ServiceBuilder` runs all steps
back-to-back.

---

### `references/execution-format.md`
**Role: Build Log Formatter**
Defines the append-only `execution.md` schema. Every service build appends a structured block
with timestamps, commands run, outputs, and pass/fail status. Never overwrite earlier entries.
Load whenever a build command writes to `execution.md`.

---

### `references/finalize-checklist.md`
**Role: Finalization Checklist**
Lists all 8 steps for Phase 8 (`/DeployOrchestrator`): wiring cross-module outputs, writing
the root `main.tf`, generating CI/CD templates, updating the README, and producing the final
summary. Read this fully before generating any finalization files.

---

### `references/cicd-and-local-dev.md`
**Role: CI/CD & Local Dev Spec**
Defines what the skill must generate for local development (Makefile targets, pre-commit hooks)
and CI/CD pipelines (GitHub Actions / GitLab CI templates). Load only during `/DeployOrchestrator`
(Phase 8), after `finalize-checklist.md`.

---

### `references/iam-roles-reference.md`
**Role: IAM Policy Catalog**
Maps every service type to the IAM roles, policies, and least-privilege permissions it needs.
The skill reads this when generating the IAM model review file and when writing IAM resources
inside service modules. Load for `/IAMModeler`, `/ServiceModeler`, and `/ServiceBuilder`.
