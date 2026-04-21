# Human Review Gate Workflow

This file defines how to generate and present review files at each gate.
Always follow this format — it ensures the human can quickly scan, edit, and approve.

---

## Review Gate Principles

1. **Always generate a file** — don't just print to chat. Save to `review/` directory.
2. **Use clear APPROVE / CHANGE markers** — make it trivial to respond
3. **Pre-fill with best-guess values** — human edits, not re-enters from scratch
4. **List specific questions** — don't ask "does this look right?" — ask targeted questions
5. **Show what changes downstream** — help human understand the consequence of edits

---

## Review Gate 1: Service Names & Inventory

**File:** `review/services-review.md`

```markdown
# 🔍 Review Gate 1: Service Inventory & Names
<!-- Edit this file and confirm. Your edits become the canonical service names. -->

## Instructions
- Review each service row below
- Edit the "Final Name" column if you want a different Terraform module name
- Correct "Type" if misidentified
- Mark each row ✅ CONFIRMED or ✏️ CHANGED
- Answer the questions at the bottom
- Tell Claude "approved" or paste back the edited table

---

## Service Inventory

| # | Label in Diagram | Final Name (edit me) | Type | Cloud | Confidence | Your Status |
|---|-----------------|---------------------|------|-------|------------|-------------|
| 1 | api-gw          | api-gateway         | API Gateway REST | AWS | HIGH | ✅ |
| 2 | lambda-auth     | lambda-auth         | Lambda Function  | AWS | HIGH | ✅ |
| 3 | users-db        | rds-users           | RDS PostgreSQL   | AWS | MEDIUM | ✅ |
| 4 | cache           | elasticache-redis   | ElastiCache Redis| AWS | LOW ⚠️ | ✏️ Please confirm |

> **Naming rules:** lowercase, hyphens only, no underscores, max 30 chars
> **These names become your Terraform module directory names** — choose carefully

---

## Connections Detected

| From            | To              | Type     | Edge Label  |
|-----------------|-----------------|----------|-------------|
| api-gateway     | lambda-auth     | invokes  | (none)      |
| lambda-auth     | rds-users       | SQL      | "writes"    |
| lambda-auth     | elasticache-redis | reads  | (none)      |

---

## Ambiguities — Please Answer

1. **"cache" service** — Assumed ElastiCache Redis. Is this correct?
   → [ ] Yes, Redis  [ ] Yes, Memcached  [ ] Different service: _______

2. **VPC** — No VPC shown in diagram. All services will be placed in a single VPC.
   → [ ] Correct  [ ] I want multi-VPC  [ ] Use existing VPC: _______

3. **Region** — Assumed `us-east-1`. Confirm or specify:
   → Region: _______

---

## General Config

| Setting | Default | Your Value |
|---------|---------|-----------|
| Project name (for naming/tagging) | (required) | _________ |
| Environments to generate | dev, prod | _________ |
| Terraform version | >= 1.6.0 | _________ |
| AWS Provider version | ~> 5.0 | _________ |
| State backend | S3 + DynamoDB | _________ |

---

**→ Reply "approved" when complete, or paste back this file with your edits.**
```

---

## Review Gate 2: Build Plan

**File:** `review/build-plan-review.md`

```markdown
# 🔍 Review Gate 2: Build Plan & Dependency Order
<!-- Review the proposed build order. Edits here affect which services are built first. -->

## Instructions
- Confirm the dependency ordering is correct
- Flag any missing dependencies between services
- Confirm naming and structural preferences

---

## Confirmed Services (from Gate 1)

{paste finalized service list here}

---

## Proposed Build Order

<!-- WAVE RULE: one service per wave. Multiple services share a wave ONLY for circular/mutual deps. -->

### Wave 1 — No dependencies (built first)
| Module | What it creates | Key outputs |
|--------|----------------|-------------|
| `networking-vpc` | VPC, subnets, route tables, IGW | `vpc_id`, `private_subnet_ids`, `public_subnet_ids` |

### Wave 2 — No dependencies
| Module | What it creates | Key outputs |
|--------|----------------|-------------|
| `iam-base-roles` | Shared IAM roles/policies | `lambda_execution_role_arn` |

### Wave 3 — Depends on Wave 1
| Module | Depends on | Key outputs |
|--------|-----------|-------------|
| `rds-users` | networking-vpc (subnets) | `db_endpoint`, `secret_arn` |

### Wave 4 — Depends on Wave 1
| Module | Depends on | Key outputs |
|--------|-----------|-------------|
| `elasticache-redis` | networking-vpc (subnets) | `redis_endpoint` |

### Wave 5 — Depends on Waves 2, 3, 4
| Module | Depends on | Key outputs |
|--------|-----------|-------------|
| `lambda-auth` | iam-base-roles, rds-users, elasticache-redis | `function_arn`, `invoke_arn` |

### Wave 6 — Depends on Wave 5 (built last)
| Module | Depends on | Key outputs |
|--------|-----------|-------------|
| `api-gateway` | lambda-auth | (final endpoint) |

---

## Cross-Module Wiring Preview

The root module (`environments/dev/main.tf`) will wire these outputs:

```
module.networking_vpc.vpc_id           → module.rds_users.vpc_id
module.networking_vpc.private_subnets  → module.rds_users.subnet_ids
module.networking_vpc.private_subnets  → module.elasticache_redis.subnet_ids
module.iam_base_roles.lambda_role_arn  → module.lambda_auth.execution_role_arn
module.rds_users.db_endpoint           → module.lambda_auth.db_host
module.rds_users.secret_arn            → module.lambda_auth.db_secret_arn
module.elasticache_redis.endpoint      → module.lambda_auth.redis_host
module.lambda_auth.invoke_arn          → module.api_gateway.lambda_invoke_arn
```

---

## Questions

1. Is this dependency ordering correct?
   → [ ] Yes  [ ] No, {service-A} should come before {service-B}: _______

2. Any missing services not in the diagram?
   → [ ] No  [ ] Yes, add: _______

3. Variable injection strategy for secrets (DB password, etc.)?
   → [ ] AWS Secrets Manager (recommended)
   → [ ] SSM Parameter Store
   → [ ] terraform.tfvars (dev only, not recommended for secrets)
   → [ ] HashiCorp Vault: _______

4. State backend config:
   → S3 Bucket name: _______
   → DynamoDB table name: _______
   → [ ] Skip for now, I'll add backend config later

---

**→ Reply "approved" to begin code generation, or paste back with edits.**
```

---

## Mid-Build Check (Optional — for complex services)

For services with >5 required variables or security implications, show this inline:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Built: rds-users
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Resources:  aws_db_instance, aws_db_subnet_group,
            aws_security_group, aws_secretsmanager_secret

Variables needing real values:
  • db_name       — database name (no default)
  • db_username   — master username (no default)

Security notes:
  • SG allows ingress on 5432 from lambda-auth SG only ✅
  • deletion_protection = false (dev) / true (prod) ✅
  • Password auto-generated and stored in Secrets Manager ✅

Continue to next service? [yes / adjust]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Progress Indicator

Show this in chat as each service completes:

```
📦 Build Progress
──────────────────────────────────────────
[✅] networking-vpc       Wave 1/6
[✅] iam-base-roles       Wave 2/6
[✅] rds-users            Wave 3/6
[🔄] elasticache-redis   Wave 4/6  ← CURRENT
[ ] lambda-auth           Wave 5/6
[ ] api-gateway           Wave 6/6
──────────────────────────────────────────
```

---

## PLAN MODE Message Templates

Use these exact messages when running the Plan command for each gate.

### Gate 1 — `/ServicesRefiner`
```
📋 PLAN MODE — nothing is committed yet.
   Review and edit: review/services-review.md
   Run /ServicesRefiner again to preview changes after editing.
   Run /ServicesRefinerConfirm when ready to lock in service names.
```

### Gate 2 — `/ServiceModeler`
```
📋 PLAN MODE — nothing is committed yet.
   Review and edit: review/build-plan-review.md
   Run /ServiceModeler again to preview after editing.
   Run /ServiceModelerConfirm when ready to lock in the build plan.
```

### Gate 3 — `/BuildPlan`
```
📋 PLAN MODE — nothing is committed yet.
   Fill in: review/03_inputs_collection.md
   ⚠️ {N} REQUIRED fields need values before confirming.
   Run /BuildPlan again to see remaining gaps after editing.
   Run /BuildPlanConfirm when all required fields are filled.
```

---

## Gate Confirm Output Templates

Use these exact chat output blocks after each successful Commit command.

### Gate 1 — `/ServicesRefinerConfirm`
```
✅ Gate 1 confirmed
   → .claude/memory/01-services.json  ({N} services)
   → .claude/memory/tf-state.json     (updated)
   → .claude/memory/handoff.json      (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /ServiceModeler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Gate 2 — `/ServiceModelerConfirm`
```
✅ Gate 2 confirmed
   → .claude/memory/02-build-plan.json  ({N} waves, {M} services)
   → .claude/memory/handoff.json        (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /BuildPlan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Gate 3 — `/BuildPlanConfirm`
```
✅ Gate 3 confirmed
   → environments/dev/terraform.tfvars.example   (open to review)
   → environments/prod/terraform.tfvars.example  (open to review)
   → .claude/memory/03-inputs.json               (all config locked)
   → .claude/memory/handoff.json                 (updated)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Files written. Context can be cleared.
    Run:  /clear
    Then: /ServiceCodeWriter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
