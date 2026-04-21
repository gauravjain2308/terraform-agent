# /ServiceModelerConfirm
Locks the build plan, scaffolds terraform/, generates IAM files, and runs IAM lint.
**Does not lock IAM** — that is a separate, deliberate step via `/IAMModelerConfirm`.

After this command you must:
  1. Open `agent/review/iam-model-review.md` and review it.
  2. Run `/IAMModelerConfirm` to lock IAM.
  3. Then run `/BuildPlan wave:1`.

---

## Step 1 — Read and validate the review file

Read `agent/review/build-plan-review.md`.

Validate:
- No circular dependencies (service in Wave N cannot depend on Wave N or later)
- All services in Dependency Map exist in Services Review service list
- state_s3_bucket is filled in and not a placeholder
- state_dynamodb_table is filled in
- state_region is filled in
- secrets_strategy is set to a valid value
- STATUS is PENDING

On failure, list every problem specifically and stop.

## Step 2 — Show summary and confirm

```
Ready to lock Service Model:

  Waves:        {n}
    Wave 1: {service list}
      Roles: {comma-separated role names required — e.g. lambda_execution_role, or "none required"}
    Wave 2: {service list}
      Roles: {comma-separated role names required — or "none required"}
    ...
  Dependencies: {n} connections
  State:        s3://{bucket}  |  DynamoDB: {table}
  Secrets:      {strategy}

  IAM roles are wave-scoped: each role is applied during /ServiceCodeWriter for its wave.
  If the Terraform executor lacks iam:CreateRole the role is skipped and you are notified.

  After "yes" this will run automatically:
    1. Write memory files
    2. Scaffold terraform/ directory  (scaffold.py)
    3. Generate IAM review files      (iam-generator.py)
    4. Validate IAM and lock it in

Type "yes" to proceed.
```

Wait for "yes". If anything else — stop without writing.

## Step 3 — Write memory

Update STATUS: CONFIRMED in `agent/review/build-plan-review.md`.

Write `.claude/memory/02-build-plan.json`:
```json
{
  "confirmed_at": "{timestamp}",
  "waves": { "1": [...], "2": [...] },
  "dependency_map": { "{consumer}": { "{provider}": ["{outputs}"] } },
  "state_backend": {
    "s3_bucket": "{value}",
    "dynamodb_table": "{value}",
    "region": "{value}"
  },
  "secrets_strategy": "{value}"
}
```

Update `.claude/memory/tf-state.json`:
- `gates.gate2_build_plan` → `"CONFIRMED"`
- `current_phase` → `"MODEL_CONFIRMED"`
- `last_command` → `"/ServiceModelerConfirm"`
- `last_updated` → current ISO timestamp

Show: `✅ Step 1/4 — Build plan locked`

## Step 4 — Write scaffold manifest and run scaffold.py

**Write `.claude/memory/scaffold-manifest.json`** from confirmed build plan data:
```json
{
  "project_name": "{value from 01-services.json}",
  "region": "{value}",
  "environments": ["{env1}", "{env2}"],
  "state_s3_bucket": "{value}",
  "state_dynamodb_table": "{value}",
  "state_region": "{value}",
  "waves": { "1": ["{service-ids}"], "2": [...] },
  "services": {
    "{service-id}": { "type": "{human-readable type}", "wave": {n} }
  },
  "dependency_map": { "{consumer}": { "{provider}": ["{outputs}"] } }
}
```

**Run scaffold.py:**
```bash
python3 agent/scripts/scaffold/scaffold.py \
  --manifest .claude/memory/scaffold-manifest.json
```

Capture and check exit code. If it fails, show the full error output and stop.

Update `.claude/memory/tf-state.json`: scaffold_complete → true

Show: `✅ Step 2/4 — terraform/ scaffolded  ({n} files created)`

## Step 5 — Run iam-generator.py

```bash
python3 agent/scripts/scaffold/iam-generator.py \
  --services .claude/memory/01-services.json \
  --plan     .claude/memory/02-build-plan.json

# This generates BOTH review files AND terraform .tf files:
#   agent/review/iam-model-review.json
#   agent/review/iam-model-review.md
#   terraform/modules/iam-base-roles/main.tf (+ variables, outputs, tests)
#   terraform/modules/{svc}/iam.tf (+ tests/iam.tftest.hcl) for each service
```

Capture and check exit code. If it fails, show the full error output and stop.

Update `.claude/memory/tf-state.json`: iam_generated → true

Show: `✅ Step 3/4 — IAM files generated (review + terraform code + tests)`

## Step 6 — IAM lint (warnings only — does not lock)

Read `agent/review/iam-model-review.json` and run structural + least-privilege checks:

**Structure checks:**
- All required keys present: roles, inline_policies, resource_policies, iam_config, checklist
- Each role has: id, module, role_resource, role_name, trust, outputs, wave
- Each inline policy has: consumer, provider, actions, resource_scope

**Least-privilege checks:**
- No inline policy `resource_scope` ends with `*` alone (bare wildcard)
- No role `managed` list contains `AdministratorAccess` or `PowerUserAccess`
- Every consumer that reads from Secrets Manager or SSM has a `kms:Decrypt` statement scoped by `kms:ViaService`

**Config checks:**
- `iam_path` is set
- `permission_boundary_arn` key exists

Surface *all* findings as warnings, then continue:
```
⚠️  IAM lint: {n} warnings (review these in agent/review/iam-model-review.md):
  • Row {n} inline_policies: resource_scope is bare "*"
  • ...
```

**Do not** set `confirmed: true` and **do not** update `iam_review` status here. The user is expected to open the file, make changes, and run `/IAMModelerConfirm` to lock it. Write `.claude/memory/handoff.json` with `"next_command": "/IAMModelerConfirm"`.

Show: `✅ Step 4/4 — IAM files generated and linted (not yet locked — run /IAMModelerConfirm)`

## Step 7 — Show final summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Service Model confirmed — ready for IAM review

  ✅ Build plan locked
       → agent/review/build-plan-review.md
       → .claude/memory/02-build-plan.json

  ✅ terraform/ scaffolded ({n} files)
       → environments/dev/  environments/prod/
       → modules/ × {n} stubs
       → iam-github-oidc/  .github/workflows/

  ✅ IAM review generated
       → agent/review/iam-model-review.md   ({n} roles, {n} inline, {n} resource)
       → agent/review/iam-model-review.json
       → terraform/modules/iam-base-roles/main.tf  (base roles, ready to build)
       → terraform/modules/{svc}/iam.tf             (per-service, one per consumer)

  ℹ️  Roles are wave-scoped — applied when each service's wave is built:
       {for each wave: "Wave N ({service-name}): {role names, or 'none required'}"}
       Roles skipped if Terraform executor lacks iam:CreateRole → you will be notified.

  ⚠️  IAM linted but **not locked** — {n} warnings surfaced above.

  Review these files in VS Code before continuing:
    📄 agent/review/iam-model-review.md   ← roles and policies for all services
    📁 terraform/                          ← scaffolded structure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Run:  /clear
    Then: /IAMModelerConfirm   (review + lock IAM)
    Then: /BuildPlan            (Wave 1 config values)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
