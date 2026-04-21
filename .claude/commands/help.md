# /help — Project Guide & Current Status

Show where you are in the project and exactly what to do next.

## Step 1 — Read memory

Read `.claude/memory/tf-state.json` and `.claude/memory/handoff.json` if they exist.

## Step 2 — Show full help output

Always show the complete help block below, then personalise the "Where you are now" and "Your next step" sections based on memory state.

---

Show this output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Terraform from Diagram — Help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 WHERE YOU ARE NOW
{personalised section — see below}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗺️  THE FULL JOURNEY

  Phase 1   /Diagram2Services          Parse your diagram (attach .drawio)
  Phase 2   /ServicesRefiner           Review service names  (edit file)
            /ServicesRefinerConfirm    Lock services
  Phase 3   /ServiceModeler            Review build order    (edit file)
            /ServiceModelerConfirm     Lock + scaffold + gen IAM + validate
  Phase 4   Review agent/review/iam-model-review.md  ← open in VS Code
            /IAMModelerConfirm         Lock IAM roles
  Phase 5   /BuildPlan wave:N          Review config values per wave  (edit file)
            /BuildPlanConfirm wave:N   Lock wave config
  Phase 6a  /ServiceCodeWriter         Write terraform code   (no terraform CLI)
  Phase 6b  /TerraformValidator        Run init/validate/fmt + plan + test
            /ServiceBuilder            Legacy: writer + validator in one run
  Phase 7   /tf-review                 Expert code review    (after building)
  Phase 8   /tf-diagram-diff           Diagram vs code drift (optional)
  Phase 9   /tf-cost                   Estimate costs        (before applying)
            make plan                  Run terraform plan
            make apply                 Apply to dev
  Phase 10  /DeployOrchestrator        Generate CI/CD files + finalize
            Push to GitHub             CI/CD takes over

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ALL COMMANDS

  Skill commands (type in Claude Code):
  ┌──────────────────────────┬────────────────────────────────────────────┐
  │ /Diagram2Services        │ Parse diagram — attach .drawio file        │
  │ /ServicesRefiner         │ Generate service review file               │
  │ /ServicesRefinerConfirm  │ Lock services from edited file             │
  │ /ServiceModeler          │ Generate build plan review file            │
  │ /ServiceModelerConfirm   │ Lock + scaffold + gen IAM + validate (all) │
  │ /IAMModeler              │ Re-lint IAM files (read-only)              │
  │ /IAMModeler refresh      │ Refresh build_status in IAM files          │
  │ /IAMModeler regen        │ Regenerate IAM files from scratch          │
  │ /IAMModelerConfirm       │ Lock IAM roles (only way to lock IAM)      │
  │ /BuildPlan               │ Review config for next unconfirmed wave    │
  │ /BuildPlan wave:N        │ Review config for specific wave N          │
  │ /BuildPlanConfirm        │ Lock wave config from edited file          │
  │ /BuildPlanConfirm wave:N │ Lock specific wave config                  │
  │ /ServiceCodeWriter       │ Write code for next service (no validate)  │
  │ /ServiceCodeWriter wave:N│ Write next unwritten service in wave N     │
  │ /ServiceCodeWriter {name}│ Write code for one specific service        │
  │ /TerraformValidator      │ Validate next CODE_WRITTEN service         │
  │ /TerraformValidator service:X │ Validate one specific service         │
  │ /TerraformValidator wave:N    │ Validate every CODE_WRITTEN svc in wave│
  │ /ServiceBuilder          │ Legacy: write + validate in one run        │
  │ /ServiceBuilder wave:N   │ Legacy: build all services in wave N       │
  │ /ServiceBuilder wave:N service:X │ Legacy: build one service in a wave│
  │ /ServiceBuilder {name}   │ Legacy: build one specific named service   │
  │ /tf-cost                 │ Estimate costs before applying             │
  │ /DeployOrchestrator      │ Full finalization (all waves must complete) │
  │ /DeployOrchestrator wave:N│ Finalize one wave (test + validate + review)│
  │ /DeployOrchestrator ci   │ Generate CI/CD files only                  │
  │ /DeployOrchestrator docs │ Generate README only                       │
  │ /DeployOrchestrator validate│ Run fmt + validate + tflint + checkov  │
  │ /tf-scaffold             │ Re-scaffold manually (normally auto-runs)  │
  │ /tf-status               │ Compact status (phase + next command)      │
  │ /help                    │ This screen                                │
  │ /tf-resume               │ Continue from where you left off           │
  │ /tf-reset                │ Start over (keeps generated files)         │
  └──────────────────────────┴────────────────────────────────────────────┘

  Terminal commands (type in VS Code terminal):
  ┌─────────────────────┬────────────────────────────────────────────┐
  │ make help           │ Show all make targets                      │
  │ make plan           │ terraform plan (dev)                       │
  │ make plan-save      │ Save plan to tf.plan                       │
  │ make apply          │ Apply saved plan                           │
  │ make test           │ Test all modules (no AWS needed)           │
  │ make lint           │ tflint + checkov security scan             │
  │ make cost           │ Run infracost estimate                     │
  │ make setup          │ First-time init                            │
  └─────────────────────┴────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 KEY FILES

  .claude/memory/tf-state.json               Current phase and gate statuses
  .claude/memory/handoff.json                Quick bootstrap for next command
  agent/review/services-review.md            Service names (gitignored)
  agent/review/build-plan-review.md          Build plan (gitignored)
  agent/review/build-plan-inputs-wave-{n}.md Wave inputs (gitignored)
  agent/review/iam-model-review.md           IAM roles tabular review (gitignored)
  agent/review/iam-model-review.json         IAM roles machine-readable (gitignored)
  agent/execution.md                         Full build log (gitignored)
  terraform/                                 ALL terraform code (committed ✅)
  terraform/environments/dev/terraform.tfvars  Your values (gitignored)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ QUICK RULES

  Only terraform/ is committed to git — everything else is gitignored
  Always /clear after every skill command
  After /Diagram2Services — verify .claude/memory/tf-state.json exists before /clear
  Gates: type "confirm" in chat when summary looks right
  /ServiceBuilder builds one service per run — check execution.md after each
  /tf-cost before make apply — always know the cost first
  terraform.tfvars — gitignored, never commit
  terraform.lock.hcl — always commit
  Secrets — AWS Secrets Manager only, never in .tf files

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 3 — Personalise "WHERE YOU ARE NOW"

Replace the `{personalised section}` based on memory state:

**No memory found:**
```
  No project started yet.

  ➤ YOUR NEXT STEP:
    Run /Diagram2Services and attach your .drawio diagram file.
```

**Phase: DIAGRAM_INGESTED (after /Diagram2Services, services not refined yet):**
```
  ✅ Diagram parsed — {n} services detected
  ⏳ Services not refined yet

  ➤ YOUR NEXT STEP:
    Run /ServicesRefiner
    Edit agent/review/services-review.md, then run /ServicesRefinerConfirm.
```

**Phase: SERVICES_REFINED:**
```
  ✅ Services refined — {n} services confirmed
  ⏳ Service model not started

  ➤ YOUR NEXT STEP:
    Run /ServiceModeler
    Edit agent/review/build-plan-review.md, then run /ServiceModelerConfirm.
```

**Phase: MODEL_CONFIRMED:**
```
  ✅ Services refined — {n} services confirmed
  ✅ Service model confirmed ({n} waves)
  ⏳ IAM not locked

  ➤ YOUR NEXT STEP:
    Open agent/review/iam-model-review.md in VS Code, review it,
    then run /IAMModelerConfirm.
```

**Phase: IAM_MODELED:**
```
  ✅ Services refined — {n} services confirmed
  ✅ Service model confirmed ({n} waves)
  ✅ IAM locked
  ⏳ Build plan config not confirmed

  ➤ YOUR NEXT STEP:
    Run /BuildPlan
    Edit agent/review/build-plan-inputs-wave-1.md, then run /BuildPlanConfirm wave:1.
```

**Phase: BUILDPLAN_CONFIRMED, build not started:**
```
  ✅ Services  ✅ Service Model  ✅ IAM  ✅ Build Plan — all confirmed
  ⏳ Build not started

  ➤ YOUR NEXT STEP:
    Run /ServiceCodeWriter
    Writes code for the first service: {first-service-name}
    Then /TerraformValidator to run terraform init/validate/fmt.
    (Or /ServiceBuilder to do both in one run — legacy.)
```

**Phase: DEPLOYING:**
```
  ✅ Services  ✅ Service Model  ✅ IAM  ✅ Build Plan — all confirmed

  Build progress:
    ✅ {service}
    ✅ {service}
    ⏳ {service}  ← next
    ○  {service}
    ○  {service}

  ➤ YOUR NEXT STEP:
    Run /ServiceBuilder
    Will build: {next-service}
    After building all services, run /tf-cost then make plan.
```

**Phase: DEPLOY_COMPLETE:**
```
  ✅ All {n} services built

  ➤ YOUR NEXT STEP:
    Run /tf-cost to see estimated monthly AWS costs
    Then: make plan  →  make apply  →  /DeployOrchestrator
```

**Phase: COMPLETE:**
```
  ✅ Project complete — {n} services

  ➤ YOUR NEXT STEP:
    make plan      — see what will change in AWS
    make apply     — apply to dev environment
    Push to GitHub — CI/CD handles the rest
    
    For prod: GitHub → Actions → Terraform Apply → select prod → type "apply"
```

## Note on /clear

Do NOT tell the user to /clear after /help. This is a read-only informational command.
