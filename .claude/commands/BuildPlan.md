# /BuildPlan  [wave:{n}]
Generate agent/review/build-plan-inputs-wave-{n}.md with ALL options shown as examples.
User fills in the file, then runs /BuildPlanConfirm wave:{n}.

## Step 1 — Load state

Read `.claude/memory/tf-state.json` and `.claude/memory/02-build-plan.json`.
Verify gate2_build_plan is CONFIRMED. If not: `❌ Run /ServiceModelerConfirm first.`

Determine target wave:
- `wave:N` in $ARGUMENTS → use wave N
- Otherwise → lowest wave with inputs STATUS: PENDING

Show banner: `📂 {project_name}  |  Phase 3 — Build Plan Wave {n}`

Get services in this wave from `02-build-plan.json`.

## Step 2 — Generate agent/review/build-plan-inputs-wave-{n}.md

Write the full file. For EVERY field:
- Pre-fill the recommended default (user just has to clear it to change)
- Show all valid options as comments
- Mark required fields with ⚠️ REQUIRED — no default

Read `references/inputs-template-guide.md` for the full field list per service type.

File header:
```markdown
# Build Plan — Wave {n} Config Values
# Edit this file, then run /BuildPlanConfirm wave:{n}
# Run /BuildPlan wave:{n} again to regenerate.
#
# Project: {project_name}
# Wave: {n}  |  Services: {service_list}
# Generated: {timestamp}
```

Then for EACH service in this wave, generate its full config section using the
per-service templates from `references/inputs-template-guide.md`.

Key rules:
- Pre-fill every field with a sensible default
- Show all options as comments above each field
- Mark required fields with `⚠️ REQUIRED — no default`
- DO NOT put real passwords here — use Secrets Paths section

## IAM Roles Section (for this wave only)

```markdown
## IAM Roles — Wave {n}

### Permission Boundary
permission_boundary_arn: none

### IAM Path
iam_path: /

### Lambda VPC Enabled (Wave {n})
lambda_vpc_enabled: {true if any Lambda in this wave connects to VPC resources}

### Extra Permissions (if any)
extra_permissions:
# Format: {consumer-service}: {action} on {resource-description}
# Leave blank if none
```

## Secrets Paths Section (always included)

```markdown
## Secrets — Paths Only (DO NOT put actual values here)

{for each service with a password/secret in this wave}
{service}_password_path:     /{project_name}/{env}/{service}/password
{service}_auth_token_path:   /{project_name}/{env}/{service}/auth-token
```

## STATUS line (at bottom of file)

```
---
## Review Status
STATUS: PENDING
```

Show in chat:
```
📝 agent/review/build-plan-inputs-wave-{n}.md created

Wave {n} services: {list}
Fields with defaults: {n}
⚠️ Required fields (no default): {n}

Next:
  1. Open agent/review/build-plan-inputs-wave-{n}.md in VS Code
  2. Fill in all ⚠️ REQUIRED fields
  3. Review defaults — change any that don't fit your setup
  4. Do NOT put real passwords in the secrets section — paths only
  5. Run /BuildPlanConfirm wave:{n} when done
```

Do NOT ask questions in chat. The file has all options shown.
