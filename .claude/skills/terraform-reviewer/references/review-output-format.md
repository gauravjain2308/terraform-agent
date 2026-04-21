# Review Report Output Format

All review reports are written to `agent/review/review_{scope}_{timestamp}.md`.
Chat output is always compact — never print full report to chat.

---

## Report File Format

```markdown
# Terraform Review Report
Scope:     {all | module:{name} | wave:{n} | structure | iam | security | plan}
Generated: {timestamp}
Project:   {project_name}
Reviewer:  terraform-reviewer skill

---

## Summary

| Category | Checked | 🔴 Critical | 🟡 Warning | 🔵 Info | Status |
|----------|---------|------------|-----------|---------|--------|
| Structure & Standards | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| Variables & Outputs | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| Security | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| IAM Least Privilege | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| Dependency Wiring | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| Testing | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| Spec Compliance | {n} | {n} | {n} | {n} | {PASS/FAIL} |
| **TOTAL** | **{n}** | **{n}** | **{n}** | **{n}** | **{PASS/FAIL}** |

**Overall result: {PASS — ready to apply | PASS WITH WARNINGS — review warnings | FAIL — fix criticals first}**

---

## 🔴 Critical Findings — Must Fix Before Applying

{if none: "None found ✅"}

### [{check_id}] {check_description}
**File:** `terraform/modules/{service}/main.tf` line {n}
**Found:**
```hcl
{the problematic code}
```
**Problem:** {clear explanation of why this is a problem}
**Fix:**
```hcl
{the corrected code}
```
**Reference:** {AWS docs link or standard rule reference}

---

### [{check_id}] {next finding}
...

---

## 🟡 Warnings — Should Fix

{if none: "None found ✅"}

### [{check_id}] {description}
**File:** `terraform/modules/{service}/variables.tf`
**Found:** {issue}
**Suggested fix:** {fix}

---

## 🔵 Informational

{if none: "None"}

### [{check_id}] {description}
**File:** {file}
**Note:** {explanation}

---

## Per-Module Results

| Module | 🔴 | 🟡 | 🔵 | Result |
|--------|----|----|----|----|
| networking-vpc | 0 | 1 | 2 | 🟡 WARN |
| iam-base-roles | 0 | 0 | 1 | ✅ PASS |
| rds-users | 1 | 2 | 0 | 🔴 FAIL |
| lambda-auth | 0 | 0 | 0 | ✅ PASS |

---

## Spec Compliance Check

| Review File | Services Checked | Mismatches |
|-------------|----------------|-----------|
| services-review.md | {n} | {n mismatches or "none"} |
| build-plan-review.md | {n} | {n mismatches or "none"} |
| 03_inputs_wave_*.md | {n} | {n mismatches or "none"} |
| iam-model-review.md | {n} | {n mismatches or "none"} |

{if mismatches: list each one with file + line + expected vs actual}

---

## Suggested Fixes

{Prioritised list of all fixes — criticals first, then warnings}

1. 🔴 Fix SEC1 in `terraform/modules/rds-users/main.tf` — security group allows 0.0.0.0/0
2. 🔴 Fix IAM3 in `terraform/modules/lambda-auth/main.tf` — S3 resource is wildcard
3. 🟡 Fix T1 in `terraform/modules/networking-vpc/main.tf` — NAT gateway missing tags
...

---

## What's Good ✅

{List things that were done well — positive reinforcement}

- All modules use aws_iam_policy_document (never raw JSON)
- RDS has deletion_protection = true
- All Lambda functions have tracing configured
- Naming convention consistent across all modules
...
```

---

## Chat Summary Format

Always end chat response with this compact block:

```
📋 Review complete → agent/review/review_{scope}_{timestamp}.md

  🔴 Critical:  {n}  {← must fix before applying}
  🟡 Warnings:  {n}
  🔵 Info:      {n}

  Result: {PASS / PASS WITH WARNINGS / FAIL}

  {if FAIL: "Top priority: {first critical finding in one line}"}
  {if PASS: "No blockers found. Safe to apply."}

Open the report file for full details and suggested fixes.
```
