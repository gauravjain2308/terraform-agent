# Terraform from Diagram

**Convert a draw.io architecture diagram into production-ready Terraform code — one service at a time, with human review at every step.**

This tool uses Claude Code inside VS Code to guide you through building a complete Terraform project. You describe your architecture visually in draw.io, and the skill generates properly structured, secure, IAM-correct Terraform modules — asking you to confirm every decision before writing code.

---

## What It Does

- Reads your draw.io diagram and detects every service and connection
- Creates pre-filled review files in `agent/review/` — every valid option shown as an inline comment, nothing to look up
- You edit those files directly in VS Code and confirm; no answers typed in chat
- Every decision is written to disk immediately (answer by answer) — partial progress survives a crash
- Derives IAM roles, policies, and resource-based permissions automatically from your architecture and dependency map
- Builds modules one service at a time: write code first, then validate with terraform CLI — you control when each step runs
- Detects when your diagram and generated Terraform have drifted apart and suggests improvements
- Estimates costs with infracost before you apply anything
- Generates GitHub Actions CI/CD workflows
- Keeps all agent files separate from Terraform code — only `terraform/` is committed to git
- Runs heavy file generation locally (scaffold.py, iam-generator.py) — not by the AI — keeping token usage minimal

---

## Architecture: Two Separate Folders

```
your-project/
│
├── terraform/          ← THE ONLY FOLDER COMMITTED TO GIT
│   ├── modules/        ← one module per service
│   ├── environments/   ← dev/ and prod/ root modules
│   ├── .github/        ← CI/CD workflows
│   ├── iam-github-oidc/← CI/CD role bootstrap
│   ├── .gitignore      ← protects secrets and state
│   ├── Makefile        ← developer shortcuts
│   └── README.md
│
├── .claude/            ← GITIGNORED — agent tooling
│   ├── commands/       ← slash commands
│   ├── skills/         ← skill instructions and references
│   └── memory/         ← project state (survives /clear)
│
├── agent/              ← GITIGNORED — working files
│   ├── review/         ← gate review files (conversation logs)
│   ├── execution.md    ← build log
│   └── scripts/        ← helper scripts
│
└── .vscode/            ← GITIGNORED — editor settings
```

**The separation is intentional.** Your infrastructure code (`terraform/`) is clean and commitable. The agent's working files (`agent/`, `.claude/`) stay local and never pollute your git history.

---

## Review Files

Every gate produces a detailed review file in `agent/review/`. These capture the full conversation — every question asked, every answer given, every decision made.

| File | Created by | Contents |
|------|-----------|----------|
| `services-review.md` | `/ServicesRefiner` | Service names conversation log, final confirmed service table |
| `build-plan-review.md` | `/ServiceModeler` | Build order conversation, wave structure, state backend config |
| `build-plan-inputs-wave-1.md` | `/BuildPlan` | Config values for Wave 1 services (instance sizes, CIDRs, etc.) |
| `build-plan-inputs-wave-2.md` | `/BuildPlan wave:2` | Config values for Wave 2 services |
| `iam-model-review.md` | `/ServiceModeler` (auto) or `/IAMModeler` | All IAM roles, inline policies, resource policies in 6 sections |

These files are written **progressively** — each answer is appended immediately, not just at the end. If anything goes wrong mid-conversation, the partial log is already on disk.

---

## Installation

### Prerequisites

| Tool | Install | Used for |
|------|---------|---------|
| VS Code | [code.visualstudio.com](https://code.visualstudio.com) | Editor |
| Claude Code extension | VS Code Extensions → search "Claude Code" | Runs skill commands |
| claude.ai account | [claude.ai](https://claude.ai) | Claude sign-in (Pro recommended) |
| Terraform | `brew install terraform` | Infrastructure tool (≥ 1.6.0) |
| AWS CLI | `brew install awscli` | Cloud provider |
| tflint | `brew install tflint` | AWS-specific lint rules |
| checkov | `brew install checkov` | Security scanning |
| infracost | `brew install infracost` | Cost estimation |

### Step 1 — Drop the skill into your project

Copy the `.claude/` folder into your project root:

```bash
cp -r .claude/ /path/to/your-project/
```

Or if starting fresh, use the full workspace zip which includes VS Code settings, scripts, and the pre-wired `terraform/` structure.

### Step 2 — Open in VS Code

```bash
# Open via the workspace file (loads all settings)
code your-project/terraform-from-diagram.code-workspace

# Or open the folder directly
code your-project/
```

### Step 3 — Install recommended extensions

VS Code shows a popup: **"Install All"** — click it.

Key extensions:
- **HashiCorp Terraform** — syntax highlighting, validation, autocomplete
- **Draw.io Integration** — view `.drawio` files inside VS Code
- **GitLens** — git history and blame

### Step 4 — Sign in to Claude Code

Click the Claude icon in the VS Code sidebar → **Sign in with claude.ai**.

### Step 5 — Install CLI tools

```bash
brew install terraform awscli tflint checkov infracost
infracost auth login    # free account for cost estimation
```

### Step 6 — Configure AWS credentials

```bash
aws configure --profile myproject-dev
# Prompts: Access Key ID, Secret Key, region, output format
export AWS_PROFILE=myproject-dev

# Verify it works
aws sts get-caller-identity
```

---

## Usage — Complete Step by Step

### Prepare your diagram

In draw.io ([app.diagrams.net](https://app.diagrams.net)):
1. Draw your architecture using AWS shape libraries
2. Label each service clearly (e.g. "api-gateway", "rds-users", "lambda-auth")
3. Draw arrows between services to show connections
4. Export: **File → Export As → XML** → save as `architecture.drawio`

---

### Step 1 — Start the skill

Open Claude Code in VS Code. Type and **attach your `.drawio` file**:

```
/Diagram2Services
```

Claude parses the XML, identifies every service and connection, and shows you a summary. It immediately creates `.claude/memory/tf-state.json`.

> ⚠️ **Before running `/clear`:** Check that `.claude/memory/tf-state.json` appears in the VS Code Explorer sidebar. If you clear before the file is written, the state is lost.

```
/clear
```

---

### Step 2 — Gate 1: Service Names

```
/ServicesRefiner
```

Claude **creates** `agent/review/services-review.md` pre-filled from your diagram with all options shown as comments.

Open the file in VS Code and:
- Edit the **Final Name** column (becomes your module folder name)
- Fix any wrong service types
- Answer questions in the Ambiguities section
- Fill in project name, region, environments at the bottom

All valid options are shown as comments in the file — no need to look anything up.

```
/clear
```

---

### Step 3 — Gate 2: Build Order

```
/ServiceModeler
```

Claude **creates** `agent/review/build-plan-review.md` with the proposed wave order pre-filled.
Open the file and:

- Move services between waves if needed
- Add missing dependencies
- Fill in the State Backend section (S3 bucket + DynamoDB table)
- Choose a Secrets strategy

After you confirm, Claude automatically generates `agent/review/iam-model-review.md` — a complete IAM roles and policies table derived from your service list and dependencies.

```
/clear
```

---

### Step 4 — Gate 3: Config Values (one wave at a time)

```
/BuildPlan
```

Claude **creates** `agent/review/build-plan-inputs-wave-1.md` with all config fields pre-filled with recommended defaults and all valid options shown as comments.

Open the file and:
- Change any defaults that don't match your setup
- Fill in `⚠️ REQUIRED` fields (no default — you must provide these)
- Leave fields you don't want to change as-is

After confirming each wave, run the next one:

```
/clear
/BuildPlan wave:2     ← Wave 2 services (databases, queues)
/clear
/BuildPlan wave:3     ← Wave 3 (compute)
/clear
...
```

---

### Step 5 — Review IAM Roles (optional refresh)

`agent/review/iam-model-review.md` was auto-generated after Gate 2. To refresh it or add extra permissions:

```
/IAMModeler
```

This shows six sections:
1. All IAM roles in a table (trust principal, managed policies, what they export)
2. Cross-service inline policies (scoped to exact ARNs from your dependency map)
3. Resource-based policies (SQS queue policies, Lambda permissions, S3 bucket policies)
4. Least-privilege checklist
5. Wave-by-wave IAM build order
6. Outputs map (which module exports which role ARN and who consumes it)

---

### Step 6 — Build (split into two commands)

Building is now **two separate commands** — you decide when to invoke terraform:

#### 6a. Write the code

```
/ServiceCodeWriter
```

Writes **one service** at a time. No terraform CLI is invoked. For each service:

1. Generates 5 files in `terraform/modules/{service}/`
2. Includes all IAM roles, inline policies, and resource policies from `iam-model-review.md`
3. Writes a per-service wiring file: `terraform/environments/{dev,prod}/modules/{service}.tf`
   (so a single-service build only touches that service's own files — clean git commits)
4. Runs lightweight in-process sanity checks (file presence, brace/quote balance, tags, no hardcoded regions/account-IDs, var declarations)
5. Marks the service `CODE_WRITTEN` in `.claude/memory/04-build-progress.json`
6. Prints the next-step commands in chat (both the `/TerraformValidator` option and the manual `terraform init/validate/fmt` option)

#### 6b. Validate the code

```
/TerraformValidator service:{name}
```

Runs in the terminal and streams results to chat:

```bash
cd terraform/modules/{name}
terraform init -backend=false
terraform validate
terraform fmt -check
terraform plan -var-file=tests/fixtures/test.tfvars
terraform test
```

Also runs `terraform plan` on every previously-built dependent. On success, the
service flips from `CODE_WRITTEN` → `COMPLETE`. On failure, status stays at
`CODE_WRITTEN` and the command suggests re-running `/ServiceCodeWriter`.

You can also validate yourself — paste the three commands above into the VS Code
terminal. The writer prints them at the end of its run.

#### Typical loop

```
/ServiceCodeWriter              ← writes code for next service
/TerraformValidator             ← validates it
/clear
/ServiceCodeWriter              ← writes next
/TerraformValidator
...
```

#### Batch modes

**Write or validate a whole wave:**
```
/ServiceCodeWriter wave:2
/TerraformValidator wave:2
```

**Target one specific service:**
```
/ServiceCodeWriter rds-users
/TerraformValidator service:rds-users
```

#### Legacy one-shot

`/ServiceBuilder` still exists as a thin orchestrator that runs writer + validator
back-to-back. Prefer the two-step flow above so you can inspect code before
invoking terraform.

---

### Step 7 — Check costs before applying

```
/tf-cost
```

Runs infracost against your Terraform plan. Shows:
- Total estimated monthly cost
- Per-resource breakdown
- Most expensive resources
- Cost optimisation suggestions

```
/clear
```

---

### Step 8 — Apply locally (dev)

```bash
cd terraform

# First time only
cp environments/dev/terraform.tfvars.example environments/dev/terraform.tfvars
# Edit terraform.tfvars — add: aws_profile = "myproject-dev"
cd environments/dev && terraform init

# Every time
make plan            # safe — reads only, changes nothing
make plan-save       # saves plan to tf.plan
make apply           # applies exactly what was reviewed
make test            # test all modules (no AWS needed)
make lint            # tflint + checkov
```

---

### Step 9 — Finalize

```
/DeployOrchestrator
```

Generates:
- `.github/workflows/terraform-plan.yml` — runs on every PR
- `.github/workflows/terraform-apply.yml` — manual trigger only
- `iam-github-oidc/main.tf` — creates CI/CD IAM roles (run once)
- `terraform/README.md` — infrastructure documentation

```
/clear
```

---

### Step 10 — Push to GitHub

```bash
cd terraform
git init
git add .
git commit -m "Initial terraform infrastructure from diagram"
git remote add origin https://github.com/you/your-repo.git
git push -u origin main
```

Only the `terraform/` folder is committed. Everything else stays local.

### Step 11 — Bootstrap CI/CD (once)

```bash
cd terraform/iam-github-oidc
terraform init
terraform apply
```

Copy the 3 role ARNs into GitHub:
```
Settings → Secrets → New secret:
  AWS_PLAN_ROLE_ARN
  AWS_APPLY_ROLE_ARN_DEV
  AWS_APPLY_ROLE_ARN_PROD

Settings → Variables → New variable:
  AWS_REGION = us-east-1

Settings → Environments:
  dev   — no required reviewers
  prod  — add required reviewers (manual approval gate)
```

From now on every PR gets an automatic plan comment. Apply via:
**GitHub → Actions → Terraform Apply → Run workflow → select env → type "apply"**

---

## All Commands

### Skill commands (Claude Code panel)

| Command | When | What it does |
|---------|------|-------------|
| `/Diagram2Services` | First step | Parse diagram, create memory. Attach `.drawio` file. |
| `/ServicesRefiner` | After start | Service names — conversational Q&A, writes `services-review.md` |
| `/ServicesRefinerConfirm` | Fallback | Lock services from manually edited review file |
| `/ServiceModeler` | After Gate 1 | Build order — conversational, writes `build-plan-review.md` + `iam-model-review.md` |
| `/ServiceModelerConfirm` | Fallback | Lock plan from manually edited review file |
| `/BuildPlan` | After Gate 2 | Config values for next wave, writes `build-plan-inputs-wave-N.md` |
| `/BuildPlan wave:2` | Specific wave | Config for Wave 2 only |
| `/BuildPlanConfirm wave:2` | Fallback | Lock wave 2 config from edited file |
| `/IAMModeler` | After Gate 2 | Generate/refresh IAM review, writes `iam-model-review.md` |
| `/ServiceCodeWriter` | After all gates | Write code for next service — no terraform CLI, only sanity checks |
| `/ServiceCodeWriter wave:2` | Target wave | Write next unwritten service in Wave 2 |
| `/ServiceCodeWriter rds-users` | By name | Write one specific service |
| `/TerraformValidator` | After writer | Run `terraform init/validate/fmt/plan/test` for next CODE_WRITTEN svc |
| `/TerraformValidator service:rds-users` | One svc | Validate that one service module |
| `/TerraformValidator wave:2` | Target wave | Validate every CODE_WRITTEN svc in Wave 2 |
| `/ServiceBuilder` | Legacy | Writer + validator in one run (prefer the two-step flow) |
| `/ServiceBuilder wave:2` | Legacy | Build all services in Wave 2 (writer + validator) |
| `/ServiceBuilder rds-users` | Legacy | Build specific named service (writer + validator) |
| `/tf-cost` | Before applying | infracost estimate — monthly cost breakdown |
| `/DeployOrchestrator` | After all built | CI/CD workflows, README, final validation |
| `/help` | Any time | Full guide + where you are + next step |
| `/tf-status` | Any time | Wave-by-wave build table |
| `/tf-resume` | After a break | Continue from current phase |
| `/tf-reset` | Start over | Wipe memory, keep generated files |

### Make commands (terminal, run from project root)

| Command | What it does |
|---------|-------------|
| `make help` | Show all targets |
| `make setup` | First-time init (copies tfvars, runs init) |
| `make plan` | terraform plan in dev |
| `make plan-save` | Save plan to tf.plan |
| `make apply` | Apply saved plan |
| `make plan ENV=prod` | Plan in prod |
| `make cost` | infracost estimate |
| `make test` | Test all modules (no AWS needed) |
| `make lint` | tflint + checkov |
| `make git-setup` | Init git in terraform/ only |
| `make skill-gate3-wave N=2` | Copy `/BuildPlan wave:2` to clipboard |
| `make skill-build-wave N=2` | Copy `/ServiceBuilder wave:2` to clipboard |
| `make logs` | Open agent/execution.md |
| `make memory` | Show Claude memory state |

---

## Review Files Reference

All files in `agent/review/` — gitignored, local only.

### `services-review.md`
Records the full Gate 1 conversation. Every question, every exact user reply, every renaming decision. Ends with a confirmed service table showing final module names, types, and wave assignments.

### `build-plan-review.md`
Records the Gate 2 conversation. Wave ordering, dependency decisions, state backend config, secrets strategy. Ends with the final dependency map table.

### `build-plan-inputs-wave-N.md`
One file per wave. Records every config question per service, the exact reply, and the resolved value (default or user override). Secrets paths recorded — actual secret values never written.

### `iam-model-review.md`
Six sections:
1. All IAM roles table (trust, policies, exports, build status)
2. Cross-service inline policies (exact ARN scopes from dependency map)
3. Resource-based policies (SQS, S3, SNS, Lambda permissions)
4. Least-privilege checklist
5. Wave-by-wave build order for IAM
6. Outputs map (who exports what, who consumes it)

Updated after every `/ServiceCodeWriter` (IAM wiring) and every `/TerraformValidator`
(build status) — built roles marked ✅, pending ones stay ⏳.

---

## Terraform Module Standards

Every generated module follows these rules:

**Files** — exactly 5 per module:
- `main.tf` — resources only, uses `locals` for name construction
- `variables.tf` — every variable has `description` and `type`, validation blocks where applicable
- `outputs.tf` — exports `id`, `arn`, `name` at minimum, `sensitive = true` on secrets
- `versions.tf` — `required_providers` only (no `required_version` in child modules)
- `tests/main.tftest.hcl` — mock-based tests, no AWS credentials needed

**Naming** — `${var.project_name}-${var.environment}-{service}` for all AWS resources

**Tags** — every taggable resource gets `Project`, `Environment`, `ManagedBy = "terraform"`, `Module`

**Security** — S3 public access block always on, no `0.0.0.0/0` ingress without comment, RDS deletion protection in prod, secrets in Secrets Manager only, KMS encryption where supported

**IAM** — `aws_iam_policy_document` data source always (never raw JSON), least-privilege ARN scoping, `prevent_destroy = true` on prod databases

---

## Gitignore Structure

| File | Protects |
|------|---------|
| `.gitignore` (root) | Ignores everything except `terraform/` |
| `terraform/.gitignore` | Ignores `*.tfvars`, `.terraform/`, `*.tfstate`, plan files, `*.zip` |
| `agent/.gitignore` | Safety net — ignores all agent files |
| `.claude/.gitignore` | Safety net — ignores all Claude files |

The root rule is two lines:
```gitignore
/*              ← ignore everything
!/terraform/    ← except this one folder
```

The `terraform.lock.hcl` file inside `terraform/` is **never** gitignored — always commit it. It locks provider checksums and prevents supply-chain attacks.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `/Diagram2Services` shows no matching command | `.claude/commands/Diagram2Services.md` missing — check `.claude/` folder is in project root |
| `tf-state.json not found` after `/Diagram2Services` | Re-run `/Diagram2Services`. Wait for `✅ tf-state.json written` before `/clear` |
| Review file not created | Check `agent/review/` folder exists. The command creates it — look for `📝 agent/review/services-review.md created` confirmation message |
| Gate 1/2 not confirmed error | Run `/tf-status` to see which gates are pending |
| Wave inputs not confirmed | Run `/BuildPlan wave:N` |
| Build stopped halfway | Run `/ServiceCodeWriter` (or `/TerraformValidator` if code was already written) — both resume from `.claude/memory/04-build-progress.json` |
| Service stuck at `CODE_WRITTEN` | Run `/TerraformValidator service:{name}` — it re-runs init/validate/fmt/plan/test |
| Validation failed | Re-run `/ServiceCodeWriter {name}` to regenerate, then `/TerraformValidator service:{name}` |
| `terraform init` fails | S3 bucket and DynamoDB table for state must exist in AWS first |
| AWS credentials error | `aws sts get-caller-identity --profile myproject-dev` |
| Gate 1 suggestion in execution.md | Edit `agent/review/services-review.md`, run `/ServicesRefiner` |
| Unexpected destroys in plan | A name changed — add a `moved {}` block |
| `/BuildPlanConfirm` fails | Run `/BuildPlan wave:N` to collect required values |
| Running out of Claude tokens | Run `/clear` after every command — state is in files, not conversation |

---

## Rules to Remember

```
Only terraform/ goes to git              →  .gitignore enforces this
/clear after every command               →  tokens reset, files persist
Review files written progressively       →  every answer appended immediately
/ServiceCodeWriter  = writes code, no terraform CLI   → status: CODE_WRITTEN
/TerraformValidator = runs terraform in terminal      → status: COMPLETE
one service per run                                   → check agent/execution.md after each
/tf-cost before make apply               →  always know the cost first
terraform.tfvars                         →  gitignored — never commit
terraform.lock.hcl                       →  always commit
Secrets                                  →  AWS Secrets Manager only, never in .tf files
terraform apply                          →  always from saved plan: plan -out → apply
Prod apply                               →  CI only, second human must approve
```
