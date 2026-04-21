# /tf-review  [{service-name} | wave:{n} | structure | iam | security | plan]
Expert Terraform code review against AWS best practices, security rules, and project specs.

## Step 1 — Prerequisites

Read `.claude/memory/tf-state.json`.
Verify gate2_build_plan: CONFIRMED AND scaffold_complete: true.
If not: `❌ /tf-review requires Gate 2 confirmed and terraform/ scaffolded.`

Read the skill at `.claude/skills/terraform-reviewer/SKILL.md`.
Read `.claude/skills/terraform-reviewer/references/review-checklist.md`.
Read `.claude/skills/terraform-reviewer/references/review-output-format.md`.

## Step 2 — Determine scope from $ARGUMENTS

- No args       → review all built modules + environments/ + iam-github-oidc/
- {service-name}→ review terraform/modules/{service-name}/ only
- wave:{n}      → review all built modules in wave N
- structure     → review terraform/ structure and boilerplate only
- iam           → IAM roles and policies review only
- security      → security checks only
- plan          → review agent/review/ spec files only (no code needed)

Show banner: `📂 {project_name}  |  Terraform Review  |  scope: {scope}`

## Step 3 — Read files to review

Load all relevant .tf files for the scope. Also load:
- agent/review/services-review.md      (spec compliance check)
- agent/review/build-plan-review.md   (wiring compliance check)
- agent/review/03_inputs_wave_*.md       (config value compliance)
- agent/review/iam-model-review.md           (IAM compliance check)
- .claude/memory/02-build-plan.json      (dependency map)

## Step 4 — Run the review

Apply every applicable checklist item from review-checklist.md.
For each finding:
- Record: check_id, severity, file, line (if applicable), finding, suggested fix

## Step 5 — Write report

Create filename: `agent/review/review_{scope}_{YYYYMMDD_HHMM}.md`
Write full report using format from review-output-format.md.
Do NOT print file contents to chat.

## Step 6 — Show compact summary in chat

```
📋 Review complete → agent/review/review_{scope}_{timestamp}.md

  🔴 Critical:  {n}
  🟡 Warnings:  {n}
  🔵 Info:      {n}

  Result: {PASS / PASS WITH WARNINGS / FAIL}
  {top finding if FAIL, or "No blockers found." if PASS}
```

End with:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open agent/review/review_{scope}_{timestamp}.md for full details.
Run:  /clear
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
