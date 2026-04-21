# /DeployOrchestrator  [wave:{n}]
Generate final project files. Supports wave-wise finalization or full project finalization.

## Command variants

```
/DeployOrchestrator           → finalize entire project (all waves complete required)
/DeployOrchestrator wave:1    → finalize Wave 1 only (test + validate Wave 1 modules)
/DeployOrchestrator wave:2    → finalize Wave 2 only
/DeployOrchestrator ci        → generate CI/CD workflows only
/DeployOrchestrator docs      → generate README only
/DeployOrchestrator validate  → run fmt + validate + tflint + checkov only
```

---

## Step 1 — Load state

Read `.claude/memory/tf-state.json` and `.claude/memory/04-build-progress.json`.
Show banner: `📂 {project}  |  Deploy Orchestrator  |  scope: {scope}`

Parse $ARGUMENTS:
- `wave:N`    → wave-specific finalization (Wave N must be COMPLETE)
- `ci`        → CI/CD files only (Gate 2 must be CONFIRMED)
- `docs`      → README only (Gate 2 must be CONFIRMED)
- `validate`  → validation only (terraform/ must exist)
- (none)      → full finalize — all waves must be COMPLETE

---

## Wave-Specific Finalization: `/DeployOrchestrator wave:N`

**Prerequisite:** All services in Wave N must be COMPLETE in 04-build-progress.json.
If not: `❌ Wave {N} not complete. Run /ServiceBuilder wave:{N} first.`

**What it does for a specific wave:**

### 1 — Run terraform test on all Wave N modules

```bash
for service in {wave_N_services}; do
  cd terraform/modules/$service
  terraform test
done
```

Write results to `agent/execution.md` under `## Wave {N} Finalization`.
Show only pass/fail per module in chat.

### 2 — Run terraform plan with Wave N modules active

In `terraform/environments/dev/main.tf`, uncomment the Wave N module blocks. Run plan:

```bash
cd terraform/environments/dev
terraform init -backend=false
terraform plan -no-color 2>&1
```

Write full plan output to `agent/execution.md`.
Show only summary line in chat: `Plan: {n} to add, 0 to change, 0 to destroy`

If plan has errors → show error, stop, do NOT proceed to next steps.

### 3 — Run static analysis on Wave N modules only

```bash
tflint terraform/modules/{wave_N_service}/
checkov -d terraform/modules/{wave_N_service}/ --framework terraform
```

### 4 — Run /tf-review for Wave N

Read `.claude/skills/terraform-reviewer/references/review-checklist.md`.
Apply all checks to Wave N modules.
Write review report to `agent/review/review_wave{N}_{timestamp}.md`.

### 5 — Update memory

Update `.claude/memory/tf-state.json`:
```json
"finalized_waves": ["1", "2"]
```

Update `.claude/memory/04-build-progress.json`:
- Mark Wave N status as `FINALIZED`

### 6 — Show wave finalization result

```
✅ Wave {N} finalized

  Modules tested:    {list}  ✅ {n}/{n} passed
  Terraform plan:    {n} to add, 0 to change, 0 to destroy
  tflint:            ✅ passed
  checkov:           ✅ passed
  Review:            → agent/review/review_wave{N}_{timestamp}.md

Wave {N} is production-ready. Safe to apply this wave independently.

Next:
  /BuildPlan wave:{N+1}         → collect config for Wave {N+1}
  /ServiceBuilder wave:{N+1}    → build Wave {N+1}
  /DeployOrchestrator wave:{N+1} → finalize Wave {N+1}
```

End with /clear instruction.

---

## Sub-command: `/DeployOrchestrator ci`

**Prerequisite:** Gate 2 CONFIRMED (has state backend + project name).

Read `references/cicd-and-local-dev.md` from the terraform-from-diagram skill.

Generate:
- `terraform/.github/workflows/terraform-plan.yml`
- `terraform/.github/workflows/terraform-apply.yml` (workflow_dispatch only)
- `terraform/iam-github-oidc/main.tf` (if not already written)
- `terraform/iam-github-oidc/outputs.tf`

Show:
```
✅ CI/CD files generated
   → terraform/.github/workflows/terraform-plan.yml
   → terraform/.github/workflows/terraform-apply.yml
   → terraform/iam-github-oidc/main.tf

Next: cd terraform/iam-github-oidc && terraform apply  (once)
```

---

## Sub-command: `/DeployOrchestrator docs`

**Prerequisite:** Gate 2 CONFIRMED.

Generate `terraform/README.md` with:
- Architecture summary (from service list + wave order)
- Prerequisites section
- First-time setup instructions
- Daily workflow commands
- CI/CD explanation table
- Module list with description of each

---

## Sub-command: `/DeployOrchestrator validate`

**Prerequisite:** terraform/ directory exists.

Run all static checks and write results to `agent/execution.md`:

```bash
terraform fmt -recursive terraform/
terraform validate (environments/dev)
terraform validate (environments/prod)
tflint --recursive terraform/
checkov -d terraform/ --framework terraform
```

Show compact pass/fail summary in chat.

---

## Full Finalization: `/DeployOrchestrator` (no args)

**Prerequisite:** ALL waves COMPLETE in 04-build-progress.json.

If any wave is incomplete:
```
❌ Cannot finalize — not all waves complete.

  Wave 1: ✅ complete
  Wave 2: ✅ complete
  Wave 3: ⏳ in progress  ← run /ServiceBuilder wave:3 first
  Wave 4: ○  not started

Tip: You can finalize each wave as it completes:
  /DeployOrchestrator wave:1
  /DeployOrchestrator wave:2
  etc.
```

If all waves complete — run in order:
1. Final `terraform fmt -recursive`
2. `terraform validate` for each environment
3. `tflint --recursive`
4. `checkov -d terraform/`
5. Run /tf-review (full review)
6. Generate `terraform/.github/workflows/terraform-plan.yml`
7. Generate `terraform/.github/workflows/terraform-apply.yml`
8. Generate/update `terraform/iam-github-oidc/main.tf`
9. Generate/update `terraform/README.md`
10. Update `tf-state.json`:
    - `gates.finalize` → `"COMPLETE"`
    - `current_phase` → `"COMPLETE"`
    - `last_command` → `"/DeployOrchestrator"`, `last_updated` → current ISO timestamp
    - Write `.claude/memory/handoff.json` with `"phase": "COMPLETE"` and `"next_command": null`

Show final output:
```
✅ Project complete — {n} services across {n} waves

terraform/ (committed to git):
  modules/         {n} modules
  environments/    dev + prod
  .github/         CI/CD workflows
  iam-github-oidc/ OIDC bootstrap
  README.md

Validation: fmt ✅  validate ✅  tflint ✅  checkov ✅
Review:     → agent/review/review_all_{timestamp}.md

Git:
  cd terraform && git init && git add . && git commit -m "Initial"

Next:
  make cost          → check monthly cost
  make plan          → terraform plan
  make apply         → apply to dev
```

End with /clear instruction.
