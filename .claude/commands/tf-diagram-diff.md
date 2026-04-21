# /tf-diagram-diff  [{service-name}]
Compare draw.io diagram against generated Terraform code. Show what has drifted.

## Step 1 — Prerequisites

Read `.claude/memory/tf-state.json`.
Verify gate2_build_plan: CONFIRMED.
If not: `❌ /tf-diagram-diff requires Gate 2 confirmed.`

Read `.claude/skills/diagram-analyst/SKILL.md`.
Read `.claude/skills/diagram-analyst/references/diagram-output-format.md`.

Get diagram file path from tf-state.json → diagram_file.
If not found: look for *.drawio in workspace root.

## Step 2 — Parse diagram

Parse the .drawio XML:
- Extract all services (vertex cells with value attribute)
- Extract all connections (edge cells)
- Extract service types from style attributes

## Step 3 — Determine scope

- No args → diff all services
- {service-name} → diff that service only

## Step 4 — Run drift detection

For each service:
1. Check if terraform/modules/{name}/ exists
2. If exists — check service type matches Terraform resource type
3. If exists — check config values match 03_inputs_wave_*.md

For each connection in diagram:
1. Check if dependency exists in build-plan-review.md
2. Check if wiring exists in environments/dev/main.tf

For each module in terraform/modules/:
1. Check if it still appears in diagram (orphan detection)

## Step 5 — Write drift report

Create: `agent/review/diagram_diff_{YYYYMMDD_HHMM}.md`
Use format from diagram-output-format.md drift report section.

## Step 6 — Show compact summary

```
📊 Diagram diff → agent/review/diagram_diff_{timestamp}.md

  Services:    {n_total} in diagram  |  {n_built} built  |  {n_missing} missing
  Drift:       {n_drift} config differences
  Orphans:     {n_orphan} modules not in diagram
  Connections: {n_missing_wiring} missing wirings

  Status: {IN SYNC | MINOR DRIFT | SIGNIFICANT DRIFT}
```

End with /clear instruction.
