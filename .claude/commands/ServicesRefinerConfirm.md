# /ServicesRefinerConfirm — Lock Service Names
Read agent/review/services-review.md, collect any missing answers interactively, validate, write memory.

## Step 1 — Load state and read file

Read `.claude/memory/tf-state.json`.
Read `agent/review/services-review.md`.

If file missing:
```
❌ agent/review/services-review.md not found.
   Run /ServicesRefiner first to generate it.
```

If STATUS is still PENDING but file looks empty/unedited, warn:
```
⚠️  File appears unedited — Final Name column still has placeholder values.
   Please edit agent/review/services-review.md first.
```

## Step 2 — Validate for hard (structural) errors

Check ONLY structural issues that cannot be fixed interactively:
- All Final Name values: lowercase, hyphens only, no spaces, max 30 chars
- No duplicate Final Names
- All Type values match a known service type

If any hard validation fails, list every problem specifically and stop:
```
❌ Cannot confirm — {n} structural issues found:

  Row 3: Final Name "my_lambda" contains underscore — use "my-lambda"
  Row 5: Type "Lambda" not recognised — use "Lambda Function"

Fix these in agent/review/services-review.md and run /ServicesRefinerConfirm again.
```

## Step 3 — Collect missing answers interactively

Scan the file for missing/unanswered fields. Collect them all before asking.

**Detect missing fields:**
- Unanswered ambiguities: rows where "Your Answer" column still contains `← type your answer here` or is blank
- `project_name` is still a placeholder (contains `{` or is blank)
- `aws_region` is `← fill this in` or blank
- `environments` is `← fill this in` or blank

If there are NO missing fields, skip to Step 4.

If there ARE missing fields, show this header once:
```
📋 Some fields in services-review.md need answers.
   I'll ask them here — just reply and I'll update the file automatically.
```

Then ask each missing field one at a time in chat. Wait for the user's answer before asking the next question.

### Missing project_name
Ask:
```
**Project Name** — what should this project be called?

Rules: lowercase, hyphens only, 4–30 characters, no spaces
Example: my-api-platform
```
Wait for answer. Record it.

### Missing aws_region
Ask:
```
**AWS Region** — which region should this project deploy to?

1️⃣  us-east-1        (N. Virginia)
2️⃣  us-west-2        (Oregon)
3️⃣  eu-west-1        (Ireland)
4️⃣  eu-central-1     (Frankfurt)
5️⃣  ap-southeast-1   (Singapore)

Type the number or the region code.
```
Wait for answer. If user types a number, map it to the region code. Record it.

### Missing environments
Ask:
```
**Environments** — which deployment environments do you need?

1️⃣  dev, prod
2️⃣  dev, staging, prod
3️⃣  dev only
4️⃣  Custom — type your own (comma-separated)

Type the number or your custom list.
```
Wait for answer. If user types a number, map it to the value. Record it.

### Unanswered ambiguities
For EACH unanswered ambiguity row, ask in sequence:
```
**Ambiguity #{n}:** {question from the Question column}

{If the question is about a service type, show relevant options from the list below}
Common options for service-type questions:
  - Redis → ElastiCache Redis
  - Memcached → ElastiCache Memcached
  - Postgres → RDS PostgreSQL
  - MySQL → RDS MySQL

Type your answer:
```
Wait for each answer before asking the next.

### Update the file with collected answers

After all answers are collected, update `agent/review/services-review.md`:
- Replace `project_name: {placeholder}` with `project_name: {answered_value}`
- Replace `aws_region: ← fill this in` with `aws_region: {answered_value}`
- Replace `environments: ← fill this in` with `environments: {answered_value}`
- For each answered ambiguity, replace the `← type your answer here` in that row's "Your Answer" column with the user's answer

Then show:
```
✅ Updated agent/review/services-review.md with your answers.
```

## Step 4 — Final validation pass

Re-read the now-updated file and confirm ALL fields are filled:
- All Final Names valid
- All Types valid
- All Ambiguities answered
- project_name, aws_region, environments all filled

If anything is still missing (edge case), list it and stop:
```
❌ Still missing after update:
   {list remaining issues}
   Edit agent/review/services-review.md and run /ServicesRefinerConfirm again.
```

## Step 5 — Compute wave estimates and show compact summary

Before showing the summary, compute a preliminary wave estimate for each service using the connections recorded in the file:

**Wave estimate algorithm (1 service per wave):**
1. Build a dependency graph from the Connections table.
2. Detect circular dependencies (A→B and B→A, or longer cycles) — these services share one wave estimate.
3. Topological-sort all services (treating circular-dep clusters as single units).
4. Each position in the sort = one wave. Assign wave numbers 1, 2, 3, …
5. For services with no dependencies that are independent of each other, assign them sequential waves using this order: Networking/VPC → IAM/KMS → Databases → Cache/Queues → Storage → Compute → Edge/Gateway.

These are **estimates only** — the user can reorder in `/ServiceModeler`.

```
Ready to lock in Services:

  Services ({n}):
    {name}  →  {type}  (est. Wave {n})
    ...

  Note: wave estimates are based on detected dependencies.
        Final wave order is confirmed in /ServiceModeler.

  Project:  {project_name}
  Region:   {region}
  Envs:     {environments}
  Connections: {n}

Confirm? Type "yes" to lock these in permanently.
(Names cannot change after this without running /tf-reset)
```

Wait for "yes". If anything else — stop without writing.

## Step 6 — Update file with confirmed status

Append to agent/review/services-review.md:

```markdown
---

## Confirmed Summary

| # | Final Name | Type | Terraform Resource | Wave (est.) |
|---|-----------|------|--------------------|------------|
| 1 | {name} | {type} | {aws_resource_type} | {wave} |
...

<!-- Wave estimates: 1 service per wave by default. Services share a wave only for circular deps.
     Final wave order is locked in /ServiceModeler. -->

## Project Config Confirmed
| Setting | Value |
|---------|-------|
| project_name | {value} |
| aws_region | {value} |
| environments | {value} |
| terraform_version | {value} |
| aws_provider_version | {value} |

## Status
**CONFIRMED** — {timestamp}
```

Also update STATUS line: `STATUS: CONFIRMED`

## Step 7 — Write memory files

Write `.claude/memory/01-services.json`:
```json
{
  "confirmed_at": "{timestamp}",
  "project_name": "{value}",
  "region": "{value}",
  "environments": ["{env1}", "{env2}"],
  "services": [
    {"id": "{name}", "type": "{type}", "resource": "{aws_resource}", "wave_estimate": {n}},
    ...
  ],
  "connections": [
    {"from": "{name}", "to": "{name}", "type": "{connection_type}"},
    ...
  ]
}
```

Update `.claude/memory/tf-state.json`:
- `gates.gate1_services` → `"CONFIRMED"`
- `current_phase` → `"SERVICES_REFINED"`
- `last_command` → `"/ServicesRefinerConfirm"`
- `last_updated` → current ISO timestamp

Write `.claude/memory/handoff.json` with `"phase": "SERVICES_REFINED"` and `"next_command": "/ServiceModeler"`.

## Step 8 — Confirm

```
✅ Services confirmed
   → agent/review/services-review.md      ✅ updated with confirmed summary
   → .claude/memory/01-services.json      ✅ written ({n} services)
   → .claude/memory/tf-state.json         ✅ updated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done.
    Run:  /clear
    Then: /ServiceModeler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```