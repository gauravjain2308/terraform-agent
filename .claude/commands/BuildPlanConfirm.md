# /BuildPlanConfirm  [wave:{n}]
Read agent/review/build-plan-inputs-wave-{n}.md, validate, write memory.

## Step 1 — Determine wave and load state

From $ARGUMENTS: `wave:N` → use N. Otherwise lowest PENDING wave.

Read `.claude/memory/tf-state.json`. Require:
- `gates.gate2_build_plan == "CONFIRMED"`
- `gates.iam_review == "CONFIRMED"`

If either is missing:
```
❌ Cannot confirm Build Plan — IAM not locked yet.
   Run /IAMModelerConfirm first.
```

Read `agent/review/build-plan-inputs-wave-{n}.md`.

If missing: `❌ Run /BuildPlan wave:{n} first.`

## Step 2 — Validate

Check:
- All ⚠️ REQUIRED fields are filled (no "⚠️ REQUIRED — no default" remaining)
- No placeholder values remaining (e.g. "← fill this in")
- All values are valid format for their type
- STATUS is PENDING

Specific validations:
- `db_name`: alphanumeric + underscores, starts with letter
- `db_username`: not a reserved word (admin, root, postgres)
- `vpc_cidr`: valid CIDR notation
- `lambda_memory_mb`: 128 to 10240, must be multiple of 64
- `ecs_cpu` + `ecs_memory_mb`: valid Fargate combination
- `ecs_container_image`: filled in (not placeholder)

### Secrets-path validation (hard reject)

For every field whose name matches `*_password_path`, `*_secret_path`, `*_token_path`, `*_apikey_path`, or `*_secret_arn`:

1. The value **must** start with `/` (SSM-style) or `arn:aws:secretsmanager:` (ARN) or `arn:aws:ssm:`.
2. The value **must** contain `{project_name}/{environment}/` segments (use values from `01-services.json`).
3. The value **must not** look like a literal secret:
   - length > 12 without `/` or `:` characters → reject
   - contains only alphanumerics + base64 padding and length ≥ 16 → reject
   - matches common password patterns (e.g. `^[A-Za-z0-9!@#$%^&*]{8,}$` with no `/`) → reject

On any match, stop with:
```
❌ Refusing to confirm — field `{field}` looks like a raw secret value, not a path.
   Expected format: /{project_name}/{environment}/{service}/{secret_name}
   Your value:      {value}   ← looks like a real secret

   Put the actual value in AWS Secrets Manager (or pre-create it via terraform apply)
   and leave this field as the path only. Memory files are gitignored but the path
   flows into terraform.tfvars.example which IS committed.
```

Do not write memory. Do not continue.

### Other failures

List every problem specifically and stop (same format as above).

## Step 3 — Show summary and confirm

Show compact summary of all resolved values (redact any field matching the path regex above to `***PATH***` for display).

Ask "yes" to lock in.

## Step 4 — Update file, generate tfvars, write memory

Append confirmed summary to file. Update STATUS: CONFIRMED.

Generate:
- `terraform/environments/dev/terraform.tfvars.example` from confirmed values
- `terraform/environments/prod/terraform.tfvars.example`

Write `.claude/memory/03-inputs-wave-{n}.json`.

Update `.claude/memory/tf-state.json`:
- `gates.gate3_inputs.wave_{n}` → `"CONFIRMED"`
- If **all** waves in `02-build-plan.json.waves` are CONFIRMED:
  - `gates.gate3_inputs` → `"CONFIRMED"`
  - `current_phase` → `"BUILDPLAN_CONFIRMED"`
- Otherwise:
  - `current_phase` → `"BUILDPLAN_IN_PROGRESS"`
- `last_command` → `"/BuildPlanConfirm"`
- `last_updated` → current ISO timestamp

Write `.claude/memory/handoff.json`:
- If more waves pending: `"next_command": "/BuildPlan wave:{next_pending}"`
- If all waves confirmed: `"next_command": "/ServiceBuilder"`

## Step 5 — Confirm

```
✅ Wave {n} inputs confirmed
   → agent/review/build-plan-inputs-wave-{n}.md                  ✅ updated
   → terraform/environments/dev/terraform.tfvars.example          ✅ generated
   → .claude/memory/03-inputs-wave-{n}.json                      ✅ written

Remaining waves:
  {wave status table}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done.
    Run:  /clear
    Then: /BuildPlan wave:{next}  OR  /ServiceBuilder (if all waves confirmed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
