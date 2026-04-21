# execution.md Format

The skill creates and maintains `execution.md` in the project root throughout the build.
It is **append-only** — never overwrite existing entries.

```markdown
# Build Execution Log
Project: {project-name}
Started: {timestamp}

---

## 🔄 Build Started
- Gate 1 confirmed: {timestamp}
- Gate 2 confirmed: {timestamp}
- Gate 3 confirmed: {timestamp}
- Services to build: networking-vpc, iam-base-roles, rds-users, lambda-auth, api-gateway
- Build order: Wave 1 → Wave 2 → Wave 3 → Wave 4

---

## ▶ networking-vpc — Building  [Wave 1]  {timestamp}
### Generated files
- modules/networking-vpc/main.tf
- modules/networking-vpc/variables.tf
- modules/networking-vpc/outputs.tf
- modules/networking-vpc/versions.tf
- modules/networking-vpc/tests/main.tftest.hcl

### Validation
- terraform validate: ✅ passed
- terraform fmt:      ✅ passed

### Terraform Plan — networking-vpc
Plan: 12 to add, 0 to change, 0 to destroy.
  + aws_vpc.main
  + aws_subnet.private[0]
  ...

### Tests
- plan_succeeds_with_valid_inputs: ✅
- rejects_invalid_environment:     ✅
- tags_are_applied:                ✅

### Gate 1 Suggestions
none

## ✅ networking-vpc — COMPLETE  {timestamp}

---

## ⚠️ Gate 1 Suggestion
Service:        lambda-auth
Issue:          Plan error — missing vpc_config, cannot reach RDS in private subnet
Suggestion:     Add connection lambda-auth → networking-vpc in services-review.md
Recommended fix: Edit review/services-review.md connections table, run /ServicesRefiner to preview
Impact:         Adds vpc_subnet_ids, vpc_security_group_ids variables to lambda-auth

---
```
