Resume the project from where it left off. Read memory and continue the current phase automatically.

## Step 1 — Load state

1. Read `.claude/memory/handoff.json` — quick bootstrap (one line summary).
2. Read `.claude/memory/tf-state.json` — full state (source of truth for `current_phase`).
3. Show a status summary (same layout as `/tf-status`).

If `tf-state.json` is missing: `❌ No project in progress. Run /Diagram2Services with a diagram.`

## Step 2 — Branch on `current_phase`

`current_phase` is a single string written by the most-recent confirm command. Valid values:

| Phase                  | Set by                      | Resume action                                                             |
|------------------------|-----------------------------|---------------------------------------------------------------------------|
| `DIAGRAM_INGESTED`     | `/Diagram2Services`         | Run `/ServicesRefiner` logic — regenerate services-review.md              |
| `SERVICES_REFINED`     | `/ServicesRefinerConfirm`   | Run `/ServiceModeler` logic — regenerate build-plan-review.md             |
| `MODEL_CONFIRMED`      | `/ServiceModelerConfirm`    | Tell user: open `iam-model-review.md`, then run `/IAMModelerConfirm`      |
| `IAM_MODELED`          | `/IAMModelerConfirm`        | Run `/BuildPlan wave:1` logic — lowest PENDING wave                       |
| `BUILDPLAN_IN_PROGRESS`| `/BuildPlanConfirm` (partial)| Run `/BuildPlan wave:{next PENDING}` logic                               |
| `BUILDPLAN_CONFIRMED`  | `/BuildPlanConfirm` (final) | Run `/ServiceBuilder` logic — build next unbuilt service                  |
| `DEPLOYING`            | `/ServiceBuilder`           | Run `/ServiceBuilder` logic — continues from `04-build-progress.json`    |
| `DEPLOY_COMPLETE`      | `/ServiceBuilder` (last)    | Run `/DeployOrchestrator` logic                                           |
| `COMPLETE`             | `/DeployOrchestrator`       | Tell user the project is already finalized                                 |

If `current_phase` is anything else (missing, null, or unrecognized), stop with:
```
❌ tf-state.json.current_phase = "{value}" is not a valid phase.
   Expected one of: DIAGRAM_INGESTED, SERVICES_REFINED, MODEL_CONFIRMED,
   IAM_MODELED, BUILDPLAN_IN_PROGRESS, BUILDPLAN_CONFIRMED,
   DEPLOYING, DEPLOY_COMPLETE, COMPLETE.
   Run /tf-status to inspect, or /tf-reset to start over.
```

## Step 3 — Continue without prompting

Do not ask the user what to do — read the memory and continue automatically. The gate commands have their own human-approval steps, so autoresumption is safe.
