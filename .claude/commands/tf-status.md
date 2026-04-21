# /tf-status
Show complete project status wave by wave. Read-only — no /clear needed after this.

## Step 1 — Load memory

Read `.claude/memory/handoff.json` first (fast).
Read `.claude/memory/tf-state.json` (full state).
Read `.claude/memory/04-build-progress.json` if it exists.

If no memory: `No project found. Run /Diagram2Services to begin.`

## Step 2 — Show full wave-wise status

Format (fill in actual data from memory):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 {project_name}  |  {region}  |  terraform/
   Phase: {current_phase}
   Updated: {last_updated}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GATES
  {✅/⏳} Services Review    {CONFIRMED: "{n} services" / PENDING: "not done"}
  {✅/⏳} Service Model      {CONFIRMED: "{n} waves" / PENDING: "not done"}
  {✅/⏳} Scaffold — terraform/     {COMPLETE: "{n} files created" / PENDING: "auto-runs with ServiceModelerConfirm"}
  {✅/⏳} IAM   — Roles review      {CONFIRMED: "{n} roles, {n} policies" / PENDING: "run /IAMModelerConfirm"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WAVES — INPUTS & BUILD STATUS

  ┌──────────┬───────────────────────────────┬──────────────┬──────────────┐
  │  Wave    │  Services                     │  Inputs      │  Build       │
  ├──────────┼───────────────────────────────┼──────────────┼──────────────┤
  │  Wave 1  │  networking-vpc, iam-base-roles│ ✅ confirmed │ ✅ complete  │
  │  Wave 2  │  rds-users, elasticache-redis  │ ✅ confirmed │ ⏳ 1/2 done  │
  │  Wave 3  │  lambda-auth                  │ ⏳ pending   │ ○ not started│
  │  Wave 4  │  api-gateway                  │ ○ not ready  │ ○ not started│
  └──────────┴───────────────────────────────┴──────────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WAVE DETAILS

  Wave 1 — Foundation  ✅ COMPLETE
  ┌────────────────────┬──────────────┬──────────┬──────────┐
  │ Service            │ Build        │ Validate │ Tests    │
  ├────────────────────┼──────────────┼──────────┼──────────┤
  │ networking-vpc     │ ✅ complete   │ ✅        │ ✅ 3/3   │
  │ iam-base-roles     │ ✅ complete   │ ✅        │ ✅ 3/3   │
  └────────────────────┴──────────────┴──────────┴──────────┘

  Wave 2 — Data Layer  ⏳ IN PROGRESS
  ┌────────────────────┬──────────────┬──────────┬──────────┐
  │ Service            │ Build        │ Validate │ Tests    │
  ├────────────────────┼──────────────┼──────────┼──────────┤
  │ rds-users          │ ✅ complete   │ ✅        │ ✅ 3/3   │
  │ elasticache-redis  │ ⏳ next       │ -         │ -        │
  └────────────────────┴──────────────┴──────────┴──────────┘

  Wave 3 — Compute  ○ PENDING INPUTS
  ┌────────────────────┬──────────────┐
  │ Service            │ Status       │
  ├────────────────────┼──────────────┤
  │ lambda-auth        │ ○ needs /BuildPlan wave:3 first │
  └────────────────────┴──────────────┘

  Wave 4 — Edge  ○ NOT READY (Wave 3 must complete first)
  ┌────────────────────┬──────────────┐
  │ api-gateway        │ ○ blocked     │
  └────────────────────┴──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OVERALL PROGRESS

  Gates:    2/2 ✅
  Inputs:   2/4 waves confirmed
  Build:    3/5 services complete  [████████░░░░░░░░░░░░] 60%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

➤ YOUR NEXT STEP

  {personalised based on current phase — see below}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILES
  terraform/              Terraform code — commit this to git
  agent/review/           Gate audit trail — gitignored
  agent/execution.md      Build log — gitignored
  .claude/memory/         Project state — gitignored
```

## Step 3 — Personalise "YOUR NEXT STEP"

**No memory:**
```
  Run /Diagram2Services (attach your .drawio file)
```

**After /Diagram2Services, services not refined:**
```
  Run /ServicesRefiner
  Edit agent/review/services-review.md, then run /ServicesRefinerConfirm.
```

**Services refined, service model not done:**
```
  Run /ServiceModeler
  Edit agent/review/build-plan-review.md, then run /ServiceModelerConfirm.
```

**Service model done, some wave inputs pending:**
```
  Run /BuildPlan wave:{lowest_pending_wave}
  Fill in agent/review/build-plan-inputs-wave-{n}.md
  Then /BuildPlanConfirm wave:{n} for each wave.
```

**All configs done, build in progress:**
```
  Run /ServiceBuilder
  Next service: {service-name} (Wave {n})
  
  Or build the whole next wave at once:
  /ServiceBuilder wave:{n}
```

**Build complete, finalize not done:**
```
  Run /tf-cost    → see estimated monthly AWS costs
  Then: make plan-save → make apply → /DeployOrchestrator
```

**All done:**
```
  Project complete ✅
  make plan-save → make apply   (or push to GitHub for CI/CD)
```

## Note

Do NOT tell user to /clear after /tf-status. This is read-only.
They can ask follow-up questions after seeing the status.
