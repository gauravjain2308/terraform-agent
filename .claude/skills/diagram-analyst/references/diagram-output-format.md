# Diagram Analyst Report Format

All reports written to `agent/review/diagram_{command}_{timestamp}.md`.

---

## Drift Report Format (tf-diagram-diff)

```markdown
# Diagram vs Code Drift Report
Command:   /tf-diagram-diff {scope}
Generated: {timestamp}
Diagram:   {diagram_filename}
Project:   {project_name}

---

## Summary

| Category | Total | ✅ Match | ⚠️ Drift | 🔴 Missing |
|----------|-------|---------|---------|-----------|
| Services | {n} | {n} | {n} | {n} |
| Connections | {n} | {n} | {n} | {n} |
| Config Values | {n} | {n} | {n} | {n} |

**Drift status: {IN SYNC | MINOR DRIFT | SIGNIFICANT DRIFT}**

---

## Service Drift

### ✅ In Sync
{list services that match diagram → code exactly}

### ⚠️ Config Drift
{services that exist in both but have differences}

#### {service-name}
| Field | Diagram/Spec | Generated Code | Verdict |
|-------|-------------|---------------|---------|
| Type | Lambda Function | aws_lambda_function | ✅ match |
| Runtime | python3.12 | python3.11 | ⚠️ DRIFT |
| Memory | 512MB | 256MB | ⚠️ DRIFT |

**Suggested fix:** Update `terraform/modules/{service}/main.tf`:
```hcl
runtime     = "python3.12"  # was python3.11
memory_size = 512            # was 256
```

### 🔴 In Diagram, Not in Code
{services present in diagram but no module exists}

| Service | Diagram Type | Module Path | Status |
|---------|-------------|-------------|--------|
| payment-service | Lambda Function | terraform/modules/payment-service/ | ❌ not built |

Action: Run `/ServiceBuilder payment-service` to build this module.

### 🔴 In Code, Not in Diagram (Orphans)
{modules that exist in terraform/ but aren't in the diagram}

| Module | Type | Diagram Match |
|--------|------|--------------|
| temp-function | Lambda | ❌ not found in diagram |

Action: Verify this module is still needed. Remove if obsolete.

---

## Connection Drift

### ✅ Wired Correctly

### ⚠️ Missing Wiring
{connections shown in diagram that aren't in code}

#### Diagram: lambda-auth → elasticache-redis
**Expected in code:**
- `lambda-auth/variables.tf` should declare `var.redis_host`
- `environments/dev/main.tf` should pass `module.elasticache_redis.redis_endpoint`

**Found:** variable declared but not wired in root module.

**Fix:** Add to `terraform/environments/dev/main.tf`:
```hcl
module "lambda_auth" {
  # ... existing ...
  redis_host = module.elasticache_redis.redis_endpoint  # ← add this line
}
```

### 🔴 No Connection in Diagram (Undeclared Dependencies)
{wiring in code that has no corresponding diagram arrow}

---

## Sync Actions Required

Prioritised list to bring code in sync with diagram:

1. 🔴 Build missing module: `/ServiceBuilder payment-service`
2. ⚠️ Fix runtime drift in lambda-auth: update main.tf line 23
3. ⚠️ Wire missing connection: elasticache → lambda-auth in environments/dev/main.tf
4. 🔵 Remove orphan module: terraform/modules/temp-function/ (if no longer needed)
```

---

## Architecture Suggestions Format (tf-diagram-suggest)

```markdown
# Architecture Improvement Suggestions
Command:   /tf-diagram-suggest {scope}
Generated: {timestamp}
Diagram:   {diagram_filename}
Project:   {project_name}

---

## Summary

{n} suggestions found:
  🔴 Critical (security/reliability): {n}
  🟡 Recommended (best practice): {n}
  🔵 Optional (cost/performance): {n}

---

## 🔴 Critical Suggestions

### [REL-1] Add Dead Letter Queue to sqs-orders
**Pattern:** Queue without DLQ
**Risk:** Failed messages are silently lost after 3 retries
**Diagram change:** Add SQS DLQ box connected to sqs-orders
**Code change:**
  1. Update Gate 1: add service `sqs-orders-dlq` (SQS Queue)
  2. Update Gate 2: add Wave 2 dependency  
  3. Or run /ServicesRefiner to re-open service list

---

## 🟡 Recommended Suggestions

### [SEC-2] Add WAF to api-gateway
**Pattern:** Public API without WAF
**Risk:** Exposed to bots, SQL injection, DDoS
**Diagram change:** Add WAF box connected to api-gateway
**Code impact:** Add `aws_wafv2_web_acl` + `aws_wafv2_web_acl_association` to api-gateway module

---

## 🔵 Optional Suggestions

### [COST-1] Switch lambda-auth to arm64
**Pattern:** Lambda using x86_64 architecture
**Saving:** ~20% compute cost
**Code change:** In `terraform/modules/lambda-auth/main.tf`:
```hcl
architectures = ["arm64"]  # change from ["x86_64"]
```
No diagram change needed.

---

## Architecture Quality Score

| Category | Score | Notes |
|----------|-------|-------|
| Reliability | 6/10 | Missing DLQ, no Multi-AZ on dev RDS |
| Security | 7/10 | Missing WAF, secrets exposure risk low |
| Cost Efficiency | 8/10 | Good instance sizing, arm64 opportunity |
| Performance | 7/10 | No caching layer between Lambda and RDS |
| Observability | 5/10 | No alarms, no X-Ray configured |
| **Overall** | **6.6/10** | |
```
