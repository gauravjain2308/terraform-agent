# /tf-diagram-suggest  [{service-name}]
Analyse architecture diagram and suggest improvements.

## Step 1 — Prerequisites

Read `.claude/memory/tf-state.json`.
Verify gate2_build_plan: CONFIRMED.
If not: `❌ /tf-diagram-suggest requires Gate 2 confirmed.`

Read `.claude/skills/diagram-analyst/SKILL.md`.
Read `.claude/skills/diagram-analyst/references/architecture-patterns.md`.
Read `.claude/skills/diagram-analyst/references/diagram-output-format.md`.

Parse the .drawio diagram XML.

## Step 2 — Analyse architecture topology

Look for patterns that match the suggestion library in architecture-patterns.md:
- Reliability: missing DLQs, single AZ, no retries
- Security: exposed databases, missing WAF, secrets in env vars
- Cost: oversized instances, x86 Lambda, unnecessary multi-AZ in dev
- Performance: missing cache, sync where async possible
- Observability: no alarms, no tracing

## Step 3 — Scope

- No args → analyse entire diagram
- {service-name} → analyse connections and config for that service only

## Step 4 — Write suggestions report

Create: `agent/review/diagram_suggest_{YYYYMMDD_HHMM}.md`
Use format from diagram-output-format.md suggestions section.
Include architecture quality score.

For each suggestion, specify:
- Whether it requires a diagram change (re-run /ServicesRefiner)
- Or just a code change (fix in existing module)
- Or is informational only

## Step 5 — Show compact summary

```
💡 Architecture suggestions → agent/review/diagram_suggest_{timestamp}.md

  🔴 Critical:    {n}  (security/reliability issues)
  🟡 Recommended: {n}  (best practice improvements)
  🔵 Optional:    {n}  (cost/performance opportunities)

  Top suggestion: {most important finding in one line}

  Architecture quality score: {overall}/10
```

End with /clear instruction.
