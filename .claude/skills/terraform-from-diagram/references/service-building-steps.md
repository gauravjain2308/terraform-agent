# Phase 7 — Service Build Steps (7a–7h)

## Role
Senior Terraform Engineer (AVM-grade)

Steps 7a–7d belong to `/ServiceCodeWriter` (no terraform CLI).
Steps 7e–7h belong to `/TerraformValidator` (terraform runs in terminal).
The legacy `/ServiceBuilder` runs all steps back-to-back.

Authoritative command definitions: `commands/ServiceCodeWriter.md`, `commands/TerraformValidator.md`.

---

## Phase 1 — `/ServiceCodeWriter`

### Step 7a — Announce

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▶ Writing code for: rds-users   [Wave 2 of 4]  (3 of 5 total)
  Type:         aws_db_instance
  Depends on:   networking-vpc (vpc_id, private_subnet_ids)
  Will export:  db_endpoint, db_port, secret_arn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Append this header to `execution.md` immediately.

### Step 7b — Generate module files

Generate all 5 files using values from `03-inputs.json`.
**Write directly to disk. Do NOT print file contents to chat.**
After writing, show only:
```
   Generated: modules/rds-users/  (main.tf, variables.tf, outputs.tf, versions.tf, tests/)
```

Follow all standards in `references/terraform-standards.md`.

### Step 7c — Write per-service wiring file

Write exactly one file per environment: `environments/{dev,prod}/{service-name}.tf`
containing only this service's `module { ... }` block. Never edit the shared
`environments/{dev,prod}/main.tf`. **Do NOT create a `modules/` subdirectory inside
the environment folder — Terraform only auto-loads `.tf` files from the root of the
working directory, not from subdirectories.** If previously-built services depend on
this service's new outputs, update only their `modules/{dep}/variables.tf`.
```
   ↺ Wired: environments/{dev,prod}/rds-users.tf
      Dependent vars updated: lambda-auth/variables.tf
```

### Step 7d — Lightweight sanity checks (no terraform CLI)

In-process text checks: file presence, brace/quote balance, versions.tf contract,
tags, no hardcoded regions/account-IDs, all `var.*` references declared.
Detailed per-check output to `execution.md`. Show only pass/fail in chat.

On failure — stop here. Do NOT update memory status. User re-runs
`/ServiceCodeWriter {name}` to regenerate.

On success — mark service `CODE_WRITTEN` in `04-build-progress.json`, set
`handoff.json.next_command = "/TerraformValidator service:{name}"`, and print:
```
▶  NEXT STEPS — validate the generated code
   Option A:  /TerraformValidator service:rds-users
   Option B:  cd terraform/modules/rds-users
              terraform init -backend=false
              terraform validate
              terraform fmt -check
```

---

## Phase 2 — `/TerraformValidator`

### Step 7e — terraform init/validate/fmt

```bash
cd modules/{service-name}
terraform init -backend=false
terraform validate
terraform fmt -check
```
Write full output to `execution.md`. Show only pass/fail per command in chat.

### Step 7f — `terraform plan` on service and ALL dependents

Write FULL plan output to:
- `execution.md` (append)
- `.claude/memory/last-plan.txt` (overwrite)

Show ONLY the summary line in chat:
```
   Plan: 8 to add, 0 to change, 0 to destroy.
   Dependents: lambda-auth ✅
```

### Step 7g — `terraform test`

```bash
cd modules/{service-name}
terraform test
```

### Step 7h — Update memory, handoff, and end with /clear

On success: flip `CODE_WRITTEN` → `COMPLETE` in `04-build-progress.json`,
append to `tf-state.json.build_progress.completed`, set
`handoff.json.next_command` to `/ServiceCodeWriter` (next service) or
`/DeployOrchestrator` (all done).

On failure: leave status at `CODE_WRITTEN`. Print the failing command and
suggest re-running `/ServiceCodeWriter {name}` to regenerate.

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

## Targeted Build: `/ServiceBuilder {service-name}`

1. Look up service in `01-services.json` — error if not found
2. Check all dependencies are already built. If not:
   ```
   ❌ Cannot build lambda-auth — dependencies not yet built:
      • rds-users (Wave 2) — not built
   ```
3. Build only that service (steps 7a–7h)
4. Run terraform plan on service and its dependents
5. Update execution.md and memory

## Resume Behaviour: `/ServiceBuilder` (no parameter)

```
🔄 Resuming build — 2/5 services already complete
   Completed: networking-vpc, iam-base-roles
   Next: rds-users
```

Builds the **next single service** in wave order and stops. Each run processes exactly one service.

## Gate Enforcement Table

| Check | Rule |
|-------|------|
| All 3 gates confirmed | Required before any build |
| Targeted build | All dependencies must be built first |
| Sequential build | Exactly one service per run |
| After each service | Always runs terraform plan on service + dependents |
| On plan error | Logs to execution.md, generates Gate 1 suggestion, stops build |

---

## Individual Service Testing

Every module includes `tests/main.tftest.hcl` using Terraform's native test framework.
Tests use `mock_provider` blocks — no real AWS credentials needed for unit tests.

```bash
cd modules/{service-name}
terraform test                      # run all tests
terraform test -filter="test_name"  # run a specific test
```
