# /tf-diagram-sync
Generate a prioritised action list to bring code in sync with diagram.
Combines drift detection + spec compliance into one actionable checklist.

## Step 1 — Prerequisites

Verify gate2_build_plan: CONFIRMED.
Parse diagram. Read all agent/review/ files. Read all terraform/ modules.

## Step 2 — Run both diff and spec compliance silently

Run full drift detection (same as /tf-diagram-diff).
Run spec compliance check (same as /tf-review plan + structure).

## Step 3 — Generate sync action list

Write `agent/review/diagram_sync_{timestamp}.md`:

```markdown
# Sync Action List — {project_name}
Generated: {timestamp}

Bring terraform/ code in sync with diagram and specifications.
Work through this list top to bottom.

---

## 🔴 Do First (blockers)

- [ ] Build missing module: /ServiceBuilder {service}
- [ ] Fix spec drift: {service} runtime is python3.11, spec says python3.12
- [ ] Fix broken wiring: lambda-auth missing redis_host in environments/dev/main.tf

## 🟡 Do Before Applying

- [ ] Fix security: rds-users security group allows 0.0.0.0/0
- [ ] Add missing tag to: aws_nat_gateway.main in networking-vpc

## 🔵 Optional Improvements

- [ ] Switch lambda-auth to arm64 (saves ~20% compute)
- [ ] Enable Single NAT gateway for dev (saves $45/month)

---

## Commands to Run

{ordered list of commands to run based on the issues found}

1. /ServiceBuilder {missing_service}     ← build missing modules first
2. /tf-review {service}            ← review fixed module
3. /tf-diagram-diff                ← verify drift resolved
```

Show compact summary in chat with total actions by priority.
