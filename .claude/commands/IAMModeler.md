# /IAMModeler  [refresh | regen]

Generate (or re-generate) the IAM review table for the entire project — all waves, all services,
in one file. This is a **PLAN command**: it writes `agent/review/iam-model-review.md` but does
NOT lock IAM. Use `/IAMModelerConfirm` to lock.

## When to use
- After `/ServiceModelerConfirm` to generate the initial IAM table
- After editing the build plan — use `regen` to rebuild the table from scratch
- After editing `iam-model-review.md` manually — use (no args) to re-lint only

## Command variants

```
/IAMModeler           → re-lint the existing iam-model-review.md (read-only, no regeneration)
/IAMModeler refresh   → re-read services + build plan, update build_status column only
/IAMModeler regen     → regenerate the full table from scratch (resets STATUS to PENDING)
```

---

## Step 1 — Load state

Read `.claude/memory/tf-state.json`.
Verify `gates.gate2_build_plan == "CONFIRMED"`. If not:
```
❌ Build plan not confirmed. Run /ServiceModelerConfirm first.
```

If `gates.iam_review == "CONFIRMED"` and user passed `regen`:
```
⚠️  IAM is already CONFIRMED. Regenerating will reset it to PENDING.
    Type "regen" again to confirm.
```
Wait for explicit `regen` before proceeding.

---

## Step 2 — Handle variant

**`/IAMModeler` (no args) — lint only:**
- Check `agent/review/iam-model-review.md` exists. If not: `❌ File not found. Run /IAMModeler regen.`
- Skip to Step 4 (lint).

**`/IAMModeler refresh`:**
- Read the existing `agent/review/iam-model-review.md`.
- Update only the **Build Status** column: set `✅ built` for any service whose directory
  `terraform/modules/{service}/` contains at least one `.tf` file, otherwise keep `⏳ pending`.
- Skip to Step 4 (lint).

**`/IAMModeler regen` or first-time generation (file does not exist):**
- Read `.claude/memory/01-services.json` and `.claude/memory/02-build-plan.json`.
- Read `references/iam-roles-reference.md` for IAM patterns per service type.
- Proceed to Step 3 (generate table).

---

## Step 3 — Generate `agent/review/iam-model-review.md`

Build the file in three sections. Cover **all waves** in a single file.
Reference `references/iam-roles-reference.md` for the exact roles, trust principals,
managed policies, and inline permissions each service type requires.

### Section A — Header

```markdown
# IAM Review — {project_name}

STATUS: PENDING

> One file covering all waves. Review every role and policy below before running /IAMModelerConfirm.
> Fill in any `← required` placeholders before locking.

Generated: {timestamp}
Waves: {n} | Services: {n} | Roles: {n} | Inline policies: {n}
```

### Section B — Roles Summary Table

One row per role per service, ordered by wave then service name.
Include the `iam-base-roles` module as Wave 1 rows (always first).

```markdown
## Roles Summary — All Waves

| Wave | Module | Role Resource Name | AWS Role Name (Naming Convention) | Trust Principal | Managed Policies | Outputs Exported | Build Status |
|------|--------|--------------------|----------------------------------|-----------------|-----------------|-----------------|--------------|
| 1 | iam-base-roles | `lambda_execution_role` | `{project}-lambda-execution` | `lambda.amazonaws.com` | AWSLambdaBasicExecutionRole | `lambda_execution_role_arn` | ⏳ pending |
| 1 | iam-base-roles | `ecs_task_execution_role` | `{project}-ecs-task-execution` | `ecs-tasks.amazonaws.com` | AmazonECSTaskExecutionRolePolicy | `ecs_execution_role_arn` | ⏳ pending |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

Only include roles that are relevant to the actual services in the project. Use the
`Per-Service IAM Requirements` section of `iam-roles-reference.md` to determine which
roles each service type needs. Omit rows for service types not present in the build plan.

**Naming convention:** `{project_name}-{service-slug}-{role-purpose}` in kebab-case.

### Section C — Inline Policies Table

One row per consumer-to-provider relationship that requires an inline policy.
Derive these from the `dependency_map` in `02-build-plan.json` crossed with the
inline policy requirements in `iam-roles-reference.md`.

```markdown
## Inline Policies — All Services

| Wave | Consumer Service | Needs Access To | IAM Actions | Resource Scope | Attached To Role | Notes |
|------|-----------------|----------------|-------------|---------------|-----------------|-------|
| 2 | lambda-auth | rds-users (Secrets Manager) | `secretsmanager:GetSecretValue` | `arn:aws:secretsmanager:{region}:{account}:secret:{project}/rds-users/*` | `lambda_execution_role` | ← fill account ID |
| 2 | lambda-auth | rds-users (RDS IAM auth) | `rds-db:connect` | `arn:aws:rds-db:{region}:{account}:dbuser/{resource-id}/{db-user}` | `lambda_execution_role` | ← fill resource-id |
| ... | ... | ... | ... | ... | ... | ... |
```

For services with no inline policy requirements (SQS, SNS, S3 that are providers only),
add a row: `| N | {service} | — | — | — | — | No inline policy required |`

### Section D — Resource Policies Table

Queue policies, bucket policies, topic policies — for services that use resource-based
policies instead of (or in addition to) IAM roles.

```markdown
## Resource Policies — Queues / Buckets / Topics

| Service | Resource Type | Policy Statement | Principal | Actions | Condition |
|---------|--------------|-----------------|-----------|---------|-----------|
| sqs-orders | SQS Queue | Allow producer | `{lambda-arn}` | `sqs:SendMessage` | — |
| sqs-orders | SQS Queue | Allow consumer | `{lambda-arn}` | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` | — |
| ... | ... | ... | ... | ... | ... |
```

Omit section entirely if no SQS/SNS/S3 resource policies are needed.

### Section E — Configuration & Checklist

```markdown
## IAM Configuration

| Setting | Value |
|---------|-------|
| IAM path | `/app/`  ← update if org requires a different path |
| Permission boundary ARN | `none`  ← fill in if your org mandates a boundary |
| KMS key for Secrets Manager | `← fill in if using CMK` |

## Pre-lock Checklist

- [ ] All role names follow the `{project}-{service}-{purpose}` convention
- [ ] No `AdministratorAccess` or `PowerUserAccess` in any managed policy list
- [ ] No bare `*` resource scopes on data service actions (S3, DynamoDB, Secrets Manager, SQS)
- [ ] Every Secrets Manager / SSM consumer has `kms:Decrypt` scoped with `kms:ViaService`
- [ ] `permission_boundary_arn` filled (or explicitly set to `none`)
- [ ] `iam_path` filled
- [ ] All `← required` placeholders replaced with real values
- [ ] Roles are wave-ordered — Wave N roles do not depend on Wave N+1 outputs
```

---

## Step 4 — Lint (warnings only, does not lock)

After generating or loading the file, run these checks:

- **Structure**: all four table sections present, header STATUS field exists
- **Least privilege**: no inline policy row has a resource scope ending in bare `*`
- **Security**: no managed policy column contains `AdministratorAccess` or `PowerUserAccess`
- **Placeholders**: count any cells still containing `← fill` or `← required`
- **KMS coverage**: every row in Section C that accesses Secrets Manager or SSM has a
  corresponding `kms:Decrypt` row (check for it in the same table)
- **Config**: IAM path and permission boundary rows present in Section E

Surface all findings as warnings. Do NOT set STATUS to CONFIRMED.

---

## Step 5 — Write file and update state

Write the completed `agent/review/iam-model-review.md`.

Update `.claude/memory/tf-state.json`:
- `gates.iam_review` → `"PENDING"`
- `last_command` → `"/IAMModeler"`
- `last_updated` → current ISO timestamp

Write `.claude/memory/handoff.json`:
```json
{
  "last_command": "/IAMModeler",
  "phase": "IAM_MODELED",
  "next_command": "/IAMModelerConfirm",
  "next_action": "Review iam-model-review.md, fill placeholders, then lock IAM",
  "files_written": ["agent/review/iam-model-review.md"]
}
```

---

## Step 6 — Show summary (≤ 20 lines)

```
✅ IAM review table generated
   → agent/review/iam-model-review.md

   Waves covered:     {n}
   Roles:             {n}  (incl. {n} in iam-base-roles)
   Inline policies:   {n}
   Resource policies: {n}
   Placeholders left: {n}  ← fill these before /IAMModelerConfirm

⚠️  {n} lint warnings — details above

Open agent/review/iam-model-review.md in VS Code.
Fill any ← placeholders, review all rows, then lock with /IAMModelerConfirm.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. File written.
    Run:  /clear
    Then: /IAMModelerConfirm  (once you've reviewed + filled placeholders)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Note for /ServiceCodeWriter

When `/ServiceCodeWriter` runs, it reads `agent/review/iam-model-review.md` to determine:
- Which roles to reference via `data "terraform_remote_state"` (roles created by `iam-base-roles`)
- Which inline policies to attach as `aws_iam_role_policy` resources inside the service module
- Which resource policies (SQS/S3/SNS) to create alongside the service

`/ServiceCodeWriter` will refuse to write IAM resources for a service if `gates.iam_review`
is not `"CONFIRMED"` in `tf-state.json` (or will warn and ask the user to confirm).
