# /ServiceModeler — Generate Build Plan Review File
Generate agent/review/build-plan-review.md pre-filled from confirmed services.
User edits the file, then runs /ServiceModelerConfirm.

## Step 1 — Load state

Read `.claude/memory/tf-state.json`. Verify gate1_services is CONFIRMED.
If not: `❌ Run /ServicesRefinerConfirm first.`
Read `.claude/memory/01-services.json`.
Show banner: `📂 {project_name}  |  Phase 2 — Service Modeler`

## Step 2 — Derive wave order silently

**Rule: one service per wave. Multiple services share a wave ONLY if they have circular/mutual dependencies.**

Algorithm:
1. Build a directed dependency graph from the `connections` in `01-services.json`.
2. Detect circular dependencies (Service A depends on B AND B depends on A, or longer cycles). Services in a cycle MUST share a wave — they are a mandatory cluster.
3. Topological-sort all services (treating each circular-dep cluster as a single unit).
4. Assign wave numbers in sort order — each position in the sort gets its own wave number.
5. When two or more services are independent of each other (no direct or indirect dependency between them), give each its own sequential wave. Use this tie-breaking order for services at the same dependency depth:
   - Networking/VPC → IAM/KMS → Databases → Cache/Queues → Storage → Compute (Lambda/ECS) → Edge/Gateway

**Example** — 6 services, all independent of each other within each tier:
```
Wave 1: networking-vpc       (no deps)
Wave 2: iam-base-roles       (no deps — separate from Wave 1, not a circular dep)
Wave 3: rds-users            (depends on networking-vpc)
Wave 4: elasticache-redis    (depends on networking-vpc — separate from Wave 3)
Wave 5: lambda-auth          (depends on iam-base-roles, rds-users, elasticache-redis)
Wave 6: api-gateway          (depends on lambda-auth)
```

**Example — circular dep** — if service-a and service-b reference each other, they MUST share a wave:
```
Wave 1: networking-vpc
Wave 2: service-a, service-b   ← mandatory cluster (circular dependency)
Wave 3: downstream-service
```

## Step 3 — Derive suggested backend names from project_name and region

Use these naming patterns for the State Backend suggestions:
```
s3_bucket:      {project_name}-tf-state-{region_short}
                e.g. my-project-tf-state-use1   (us-east-1 → use1)
                e.g. my-project-tf-state-euw1   (eu-west-1 → euw1)

dynamodb_table: {project_name}-tf-lock

Region shorthand map:
  us-east-1      → use1     us-east-2    → use2
  us-west-1      → usw1     us-west-2    → usw2
  eu-west-1      → euw1     eu-west-2    → euw2
  eu-central-1   → euc1     ap-southeast-1 → apse1
  ap-southeast-2 → apse2    ap-northeast-1 → apne1
  ca-central-1   → cac1     sa-east-1    → sae1
```

These names are SUGGESTIONS only — the user can change them.
Terraform will create these resources during the bootstrap step after /BuildPlan confirmation.
Do NOT say "must exist before running terraform init" — we will create them.

## Step 4 — Generate and write agent/review/build-plan-review.md

Write the complete file. Pre-fill every field including the suggested backend names.

```markdown
# Build Plan Review
# Edit this file, then run /ServiceModelerConfirm to lock it in.
# Run /ServiceModeler again to regenerate.
#
# Project: {project_name}  |  Region: {region}
# Generated: {timestamp}
# Services: {n} confirmed from Services Review
# ─────────────────────────────────────────────────────────────────────

---

## Instructions
1. Review the Wave Order table — move services between waves if needed
2. Review the Dependency Map — add any missing connections
3. Confirm or change the State Backend names (pre-filled with suggestions)
4. Choose a Secrets strategy
5. Run /ServiceModelerConfirm when done

---

## Wave Order

<!--
RULES:
  - Default: one service per wave
  - A service can only be in Wave N if ALL its dependencies are in earlier waves
  - Multiple services share a wave ONLY when they have circular/mutual dependencies
    (i.e. they cannot be deployed independently — this is the ONLY exception)
  - More waves = clearer failure isolation — do NOT merge independent services into one wave

TO MOVE A SERVICE: change the Wave number in the Wave column
-->

| Wave | Service | Type | Depends On | Will Export |
|------|---------|------|-----------|------------|
| 1 | networking-vpc | VPC | — | vpc_id, private_subnet_ids, public_subnet_ids |
| 2 | iam-base-roles | IAM Role | — | lambda_execution_role_arn, rds_monitoring_role_arn |
| 3 | rds-users | RDS PostgreSQL | networking-vpc | db_endpoint, db_port, secret_arn |
| 4 | elasticache-redis | ElastiCache Redis | networking-vpc | redis_endpoint, auth_token_secret_arn |
| 5 | lambda-auth | Lambda Function | iam-base-roles, rds-users, elasticache-redis | function_arn, invoke_arn |
| 6 | api-gateway | API Gateway HTTP | lambda-auth | api_endpoint, stage_url |

<!--
ADD A MISSING SERVICE:
| {wave} | {name} | {type} | {depends-on or "—"} | {exports} |
-->

---

## Dependency Map

<!--
These are the cross-module outputs wired in environments/dev/main.tf.
Add rows for any missing connections.
-->

| Consumer Service | Needs From | Output Variable | Variable in Consumer |
|-----------------|-----------|----------------|---------------------|
| rds-users | networking-vpc | vpc_id | var.vpc_id |
| rds-users | networking-vpc | private_subnet_ids | var.subnet_ids |
| elasticache-redis | networking-vpc | vpc_id | var.vpc_id |
| elasticache-redis | networking-vpc | private_subnet_ids | var.subnet_ids |
| lambda-auth | iam-base-roles | lambda_execution_role_arn | var.execution_role_arn |
| lambda-auth | iam-base-roles | lambda_execution_role_name | var.execution_role_name |
| lambda-auth | rds-users | db_endpoint | var.db_host |
| lambda-auth | rds-users | secret_arn | var.db_secret_arn |
| lambda-auth | elasticache-redis | redis_endpoint | var.redis_host |
| api-gateway | lambda-auth | invoke_arn | var.lambda_invoke_arn |

---

## State Backend

<!--
These names have been suggested based on your project name and region.
Terraform will create these resources during the bootstrap step (after /BuildPlan confirmation).
You do NOT need to create them in AWS manually beforehand.

Change the names if they conflict with existing resources in your AWS account,
or if your organisation has a naming convention to follow.
-->

```
state_s3_bucket:      {project_name}-tf-state-{region_short}
# Suggested name — change if needed
# Rules: globally unique, lowercase, hyphens only, 3-63 chars
# Terraform will create this S3 bucket during bootstrap

state_dynamodb_table: {project_name}-tf-lock
# Suggested name — change if needed
# Rules: 3-255 chars, alphanumeric + hyphens + dots + underscores

state_region:         {region}
# Region where state is stored — usually same as project region
```

<!--
BOOTSTRAP NOTE:
After all /BuildPlan waves are confirmed, the skill will generate a bootstrap module
that creates these resources with a single terraform apply before
the main backend is initialised. You will not need to create them manually.
-->

---

## Secrets Strategy

<!--
Choose ONE — delete or comment out the others.
-->

```
secrets_strategy: aws-secrets-manager
# OPTION 1: aws-secrets-manager  (recommended)
#   Pros: auto-rotation, fine-grained IAM access, full audit trail in CloudTrail
#   Cons: ~$0.40/secret/month (~$5/year for 12 secrets)
#   All passwords stored at: /{project_name}/{env}/{service}/password

# OPTION 2: ssm-parameter-store
#   Pros: free for standard parameters (< 4KB), simple to use
#   Cons: no auto-rotation, 4KB size limit, no cross-region replication
#   Use for: non-sensitive config that benefits from centralised management

# OPTION 3: skip
#   Use if you have an existing secrets solution (HashiCorp Vault, CyberArk, etc.)
#   You will manually add secret references to the generated modules
```

---

## Additional Notes

<!-- Optional: architecture context, constraints, team conventions -->


---

## Review Status
STATUS: PENDING
```

Show in chat:
```
📝 agent/review/build-plan-review.md created

Proposed build: {n} waves, {n} services  (1 service per wave — grouped only for circular deps)
  {wave list}

State backend (suggested — Terraform will create these):
  S3:       {suggested_bucket_name}
  DynamoDB: {suggested_table_name}

Next:
  1. Open agent/review/build-plan-review.md in VS Code
  2. Review wave order — move services if needed
  3. Check dependency map — add anything missing
  4. Confirm or rename the state backend names
  5. Choose secrets strategy
  6. Run /ServiceModelerConfirm when done
```

Do NOT ask questions in chat. Everything is in the file.
