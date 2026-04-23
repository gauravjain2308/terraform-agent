# Terraform-Agent — Command Flow Path

The full command path from "draw.io diagram in hand" to "production Terraform committed". Each command is a **hard gate** — you cannot skip ahead. The agent refuses if prerequisites aren't met.

Every gate uses the same **Plan → Review → Confirm** pattern:
1. `/<Gate>` generates a pre-filled review file into `agent/review/` (written progressively, so partial state survives a crash).
2. You edit the file directly in VS Code — all valid options are shown as inline comments.
3. `/<Gate>Confirm` validates it, locks it, and writes memory under `.claude/memory/`.

Run `/clear` between commands — project state lives in files, not the conversation, so clearing frees tokens without losing progress.

---

## 🗺️ Happy-path flow (top to bottom, 9 phases)

```
┌────────────────────────────────────────────────────────────────────┐
│ 0.  Attach the draw.io diagram to Claude Code                      │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 1.  /Diagram2Services                                              │
│     ───────────────────────────────────────────────────────────    │
│     Parses the diagram, extracts services + connections.           │
│     Writes .claude/memory/tf-state.json (current_phase=DIAGRAM_INGESTED). │
│     Writes .claude/memory/handoff.json.                            │
│                                                                    │
│     ▶ next: /clear, then /ServicesRefiner                          │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 2.  GATE 1 — Service list                                          │
│     ───────────────────────────────────────────────────────────    │
│     /ServicesRefiner   → writes agent/review/services-review.md    │
│                          (PLAN ONLY — nothing locked)              │
│                                                                    │
│     you open services-review.md in VS Code:                        │
│       • rename services (e.g. "myLambda" → "auth-handler")         │
│       • set project_name, aws_region, environments                 │
│       • answer any ambiguities                                     │
│                                                                    │
│     /ServicesRefinerConfirm → validates + locks                    │
│                          writes .claude/memory/01-services.json    │
│                          sets current_phase=SERVICES_REFINED       │
│                                                                    │
│     ▶ next: /clear, then /ServiceModeler                           │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 3.  GATE 2 — Build plan (waves + dependencies + backend)           │
│     ───────────────────────────────────────────────────────────    │
│     /ServiceModeler    → writes agent/review/build-plan-review.md  │
│                          with wave assignments, deps, state        │
│                          backend config, secrets strategy.         │
│                                                                    │
│     you open build-plan-review.md:                                 │
│       • verify wave 1/2/3/4 groupings                              │
│       • confirm dependency arrows                                  │
│       • fill state_s3_bucket, state_dynamodb_table, state_region   │
│       • pick secrets_strategy (secrets-manager or ssm)             │
│                                                                    │
│     /ServiceModelerConfirm → validates, locks plan, and automatically: │
│                           1. writes .claude/memory/02-build-plan   │
│                              .json                                 │
│                           2. runs scaffold.py → terraform/ tree    │
│                           3. runs iam-generator.py → IAM files     │
│                              (reviews + .tf)                       │
│                           4. runs IAM lint (warnings only)         │
│                          sets current_phase=MODEL_CONFIRMED        │
│                                                                    │
│     ⚠️  IAM is GENERATED but NOT LOCKED yet.                       │
│                                                                    │
│     ▶ next: /clear, then /IAMModelerConfirm                        │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 4.  GATE 3 (IAM) — review + lock IAM                               │
│     ───────────────────────────────────────────────────────────    │
│     you open agent/review/iam-model-review.md:                     │
│       • scan every role, every inline policy                       │
│       • verify kms:Decrypt is present for Secrets Manager readers  │
│       • set permission_boundary_arn and iam_path                   │
│       • (optional) /IAMModeler regen if build plan changed         │
│                                                                    │
│     /IAMModelerConfirm → validates, locks IAM                      │
│                          sets current_phase=IAM_MODELED            │
│                                                                    │
│     ▶ next: /clear, then /BuildPlan                                │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 5.  GATE 4 — Per-wave inputs (run once per wave)                   │
│     ───────────────────────────────────────────────────────────    │
│     /BuildPlan         → lowest PENDING wave                       │
│     /BuildPlan wave:N  → specific wave                             │
│                          writes agent/review/build-plan-inputs-wave-{n}.md │
│                                                                    │
│     you fill in concrete values for wave N:                        │
│       • db_name, db_username, lambda_memory_mb, ecs_cpu…           │
│       • secret PATHS only (never raw values — validator rejects)   │
│                                                                    │
│     /BuildPlanConfirm wave:N                                       │
│                       → validates (incl. secret-path regex check)  │
│                          writes 03-inputs-wave-{n}.json            │
│                          generates terraform.tfvars.example        │
│                          sets current_phase=BUILDPLAN_IN_PROGRESS  │
│                                                                    │
│     Repeat for each wave.  When the last wave is confirmed:        │
│                          sets current_phase=BUILDPLAN_CONFIRMED    │
│                                                                    │
│     ▶ next: /clear, then /ServiceBuilder                           │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 6.  BUILD — two commands per service (you control each step)       │
│     ───────────────────────────────────────────────────────────    │
│     STEP A — write code (no terraform CLI invoked):                │
│     /ServiceCodeWriter                    → next unwritten service  │
│     /ServiceCodeWriter wave:2             → next in Wave 2         │
│     /ServiceCodeWriter rds-users          → specific service       │
│       generates main.tf / variables.tf / outputs.tf /             │
│       versions.tf / tests/main.tftest.hcl                         │
│       runs in-process sanity checks (brace balance, tags, etc.)   │
│       marks service CODE_WRITTEN in 04-build-progress.json        │
│                                                                    │
│     STEP B — validate (runs terraform CLI in terminal):            │
│     /TerraformValidator                   → next CODE_WRITTEN svc  │
│     /TerraformValidator service:rds-users → one service            │
│     /TerraformValidator wave:2            → all CODE_WRITTEN in W2 │
│       terraform init -backend=false                                │
│       terraform validate + fmt -check                              │
│       terraform plan -var-file=tests/fixtures/test.tfvars          │
│       terraform test (mocked, no AWS credentials needed)           │
│       on pass → marks COMPLETE in 04-build-progress.json          │
│       on fail → stays CODE_WRITTEN, suggests re-running writer     │
│                                                                    │
│     Typical loop:                                                  │
│       /ServiceCodeWriter → /TerraformValidator → /clear → repeat   │
│                                                                    │
│     /ServiceBuilder still exists as a legacy one-shot (writer +    │
│     validator back-to-back), but the two-step flow is preferred.   │
│                                                                    │
│     current_phase=DEPLOYING → DEPLOY_COMPLETE (last svc)           │
│                                                                    │
│     ▶ next: /tf-cost (optional), then /DeployOrchestrator          │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 7.  COST CHECK — optional but recommended                          │
│     ───────────────────────────────────────────────────────────    │
│     /tf-cost          → runs infracost / terraform plan estimate   │
│                         shows monthly $ before you apply           │
│     (read-only, no state changes)                                  │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 8.  FINALIZE                                                       │
│     ───────────────────────────────────────────────────────────    │
│     /DeployOrchestrator              → full: all waves, CI/CD, README │
│     /DeployOrchestrator wave:N       → just Wave N                 │
│     /DeployOrchestrator ci           → .github/workflows/ only     │
│     /DeployOrchestrator docs         → README.md only              │
│     /DeployOrchestrator validate     → fmt + validate + tflint + checkov │
│                                                                    │
│     sets current_phase=COMPLETE                                    │
│                                                                    │
│     ▶ next: git add terraform/ && git commit                       │
└────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│ 9.  APPLY (in the terraform/ directory, outside Claude Code)       │
│     ───────────────────────────────────────────────────────────    │
│     cd terraform/environments/dev                                  │
│     terraform init                                                 │
│     terraform plan -var-file=terraform.tfvars                      │
│     terraform apply                                                │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔁 Supporting commands (use any time)

| Command | What it does |
|---|---|
| `/tf-status` | One-screen summary — current phase, gate statuses, next command. No side effects. |
| `/tf-resume` | Read `tf-state.json.current_phase`, auto-continue the next step. Idempotent. |
| `/tf-reset` | Wipe `.claude/memory/` (keeps `README.md`). Terraform files are **not** deleted. |
| `/tf-review` | Lint generated Terraform. Scope: `{service}` / `wave:{n}` / `structure` / `iam` / `security` / `plan`. |
| `/tf-scaffold wave:N` | Re-run scaffold for one wave (edge case — `/ServiceModelerConfirm` does this automatically). |
| `/IAMModeler [refresh\|regen]` | Regenerate or re-lint IAM. Never locks — use `/IAMModelerConfirm` for that. |
| `/tf-diagram-diff` | Compare current diagram vs. generated Terraform. Flags drift. |
| `/tf-diagram-suggest` | Architecture improvement suggestions (diagram-analyst skill). |
| `/tf-diagram-sync` | Re-parse the diagram and update `tf-state.json` without re-running gates. |
| `/help` | Project guide + current status. |

---

## 🧭 Phase enum (source of truth for `/tf-resume`)

`.claude/memory/tf-state.json.current_phase` is always one of:

| Phase | Set by | What `/tf-resume` does |
|---|---|---|
| `DIAGRAM_INGESTED` | `/Diagram2Services` | Runs `/ServicesRefiner` |
| `SERVICES_REFINED` | `/ServicesRefinerConfirm` | Runs `/ServiceModeler` |
| `MODEL_CONFIRMED` | `/ServiceModelerConfirm` | Tells you to review + run `/IAMModelerConfirm` |
| `IAM_MODELED` | `/IAMModelerConfirm` | Runs `/BuildPlan wave:1` (lowest PENDING) |
| `BUILDPLAN_IN_PROGRESS` | `/BuildPlanConfirm` (partial) | Runs `/BuildPlan wave:{next}` |
| `BUILDPLAN_CONFIRMED` | `/BuildPlanConfirm` (final) | Runs `/ServiceCodeWriter` |
| `DEPLOYING` | `/ServiceCodeWriter` / `/TerraformValidator` | Runs `/ServiceCodeWriter` (next unwritten) or `/TerraformValidator` (next CODE_WRITTEN) |
| `DEPLOY_COMPLETE` | `/TerraformValidator` (last svc) | Runs `/DeployOrchestrator` |
| `COMPLETE` | `/DeployOrchestrator` | Tells you the project is done |

---

## 📁 Files that persist between commands

```
.claude/memory/                  ← machine state (gitignored)
  ├── tf-state.json              ← master state + current_phase
  ├── handoff.json               ← one-line bootstrap for the next command
  ├── 01-services.json           ← after GATE 1
  ├── 02-build-plan.json         ← after GATE 2
  ├── 03-inputs-wave-{n}.json    ← one per wave (after GATE 3)
  ├── 04-iam-roles.json          ← after IAM_MODELED
  ├── 04-build-progress.json     ← updated by /ServiceBuilder
  └── scaffold-manifest.json     ← input to scaffold.py

agent/                           ← human review trail (gitignored)
  ├── review/                    ← written progressively (every answer appended)
  │   ├── services-review.md
  │   ├── build-plan-review.md
  │   ├── build-plan-inputs-wave-{n}.md
  │   └── iam-model-review.md + iam-model-review.json
  ├── execution.md               ← full build log (check for Gate 1 Suggestions after each /ServiceBuilder)
  ├── workflow.md                ← this file
  └── scripts/
      ├── api-runner.py          ← CLI invocation helper
      ├── token-tracker.py       ← session token usage
      └── scaffold/
          ├── scaffold.py        ← runs after /ServiceModelerConfirm
          ├── iam-generator.py   ← runs after /ServiceModelerConfirm
          └── manifest-example.json

terraform/                       ← the only thing committed to git
  ├── environments/{dev,prod}/
  ├── modules/{service}/
  ├── iam-github-oidc/
  └── .github/workflows/
```

---

## 🛑 What each gate refuses

- `/ServiceModeler` refuses if `gate1_services != "CONFIRMED"`.
- `/ServiceModelerConfirm` refuses on circular dependencies or missing backend config.
- `/IAMModelerConfirm` refuses if `gate2_build_plan != "CONFIRMED"`, or if IAM has bare wildcards / admin-level managed policies.
- `/BuildPlanConfirm` refuses if `iam_review != "CONFIRMED"`, or if a `*_password_path` / `*_secret_*` field looks like a raw secret (regex check) instead of an SSM/Secrets-Manager path.
- `/ServiceCodeWriter` and `/TerraformValidator` refuse if any earlier wave is incomplete, or if the target wave has unconfirmed inputs.
- `/TerraformValidator` on a wave refuses if any service in that wave is still `PENDING` (not yet `CODE_WRITTEN`).
- `/DeployOrchestrator` (full) refuses unless every wave is `COMPLETE` in `04-build-progress.json`.

---

## 🧪 Running end-to-end (quick reference)

```bash
# 1. Attach diagram, then in Claude Code:
/Diagram2Services
/clear

# 2. GATE 1 — service names
/ServicesRefiner
# open agent/review/services-review.md in VS Code, edit, save
/ServicesRefinerConfirm
/clear

# 3. GATE 2 — build plan + auto scaffold + auto IAM generation
/ServiceModeler
# open agent/review/build-plan-review.md in VS Code, edit, save
/ServiceModelerConfirm
/clear

# 4. GATE 3 — lock IAM
# open agent/review/iam-model-review.md in VS Code, review, save
/IAMModelerConfirm
/clear

# 5. GATE 4 — wave inputs (repeat per wave)
/BuildPlan wave:1
# open agent/review/build-plan-inputs-wave-1.md in VS Code, fill values, save
/BuildPlanConfirm wave:1
/clear
# … repeat for each wave

# 6. Build — two steps per service, repeat until all done
/ServiceCodeWriter        ← writes code, no terraform CLI
/TerraformValidator       ← runs terraform init/validate/fmt/plan/test
/clear
# repeat until /tf-status shows all COMPLETE

# 7. (Optional) cost preview before applying
/tf-cost
/clear

# 8. Finalize — CI/CD workflows, README
/DeployOrchestrator
/clear

# 9. Commit + apply (terraform/ only)
git add terraform/ && git commit -m "infra: initial generation"
cd terraform/environments/dev && terraform init && terraform apply
```

If you ever lose track of where you are: `/tf-status`. If you want the agent to just pick up and continue: `/tf-resume`.
