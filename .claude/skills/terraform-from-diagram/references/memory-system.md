# Memory System Guide

The skill uses a `.claude/memory/` folder to persist state between sessions and commands.
Every gate writes a memory snapshot. Every command reads it first.

This means:
- You can close VS Code, come back tomorrow, run a command and Claude picks up exactly where you left off
- If you skip a gate by accident, Claude will tell you what's missing before proceeding
- Each gate's output is always available for future phases to reference

---

## Memory Folder Structure

```
.claude/
├── skills/
│   └── terraform-from-diagram.skill
└── memory/
    ├── tf-state.json            ← master state file (always read first)
    ├── 01-services.json         ← written after Gate 1 approval
    ├── 02-build-plan.json       ← written after Gate 2 approval
    ├── 03-inputs.json           ← written after Gate 3 approval
    └── 04-build-progress.json   ← updated after each service is built
```

---

## Master State File — `tf-state.json`

Always written/updated after every gate. Claude reads this first on every command.

```json
{
  "project_name": "myproject",
  "current_phase": "GATE_2_APPROVED",
  "last_command": "/tf-plan",
  "last_updated": "2024-01-15T14:32:00Z",
  "gates": {
    "gate1_services": "APPROVED",
    "gate2_build_plan": "APPROVED",
    "gate3_inputs": "PENDING",
    "build": "NOT_STARTED",
    "finalize": "NOT_STARTED"
  },
  "services": ["networking-vpc", "iam-base-roles", "rds-users", "lambda-auth", "api-gateway"],
  "waves": {
    "1": ["networking-vpc", "iam-base-roles"],
    "2": ["rds-users"],
    "3": ["lambda-auth"],
    "4": ["api-gateway"]
  },
  "region": "us-east-1",
  "environments": ["dev", "prod"],
  "diagram_file": "architecture.drawio",
  "build_progress": {
    "completed": ["networking-vpc", "iam-base-roles"],
    "current": "rds-users",
    "remaining": ["lambda-auth", "api-gateway"]
  }
}
```

---

## How Claude Must Use Memory

### On EVERY command — read first:

```
1. Check if .claude/memory/tf-state.json exists
2. If YES  → load state, greet user with current status, then execute command
3. If NO   → this is a fresh start, proceed with /Diagram2Services
```

### State greeting format (show this at the start of every command response):

```
📂 Project: myproject  |  Phase: Gate 2 Approved  |  Next: Fill inputs
```

### Gate prerequisite enforcement:

| Command | Requires in memory |
|---------|-------------------|
| `/Diagram2Services` | Nothing (creates memory) |
| `/ServicesRefinerConfirm` | Gate 1 review file exists |
| `/ServiceModelerConfirm` | Gate 1 approved in memory |
| `/BuildPlanConfirm` | Gate 2 approved in memory |
| `/ServiceBuilder` | All 3 gates approved in memory |
| `/tf-status` | Any memory state |
| `/tf-resume` | Any memory state |

If a prerequisite is missing, Claude must say:
```
❌ Cannot run /ServiceBuilder — Gate 3 inputs not yet approved.
   Run /BuildPlanConfirm first, or /tf-status to see where you are.
```

---

## Memory Files Written Per Gate

### After `/ServicesRefinerConfirm` → write `01-services.json`

```json
{
  "approved_at": "2024-01-15T10:00:00Z",
  "services": [
    {
      "id": "networking-vpc",
      "label": "vpc",
      "type": "aws_vpc",
      "cloud": "aws",
      "wave": 1,
      "module_dir": "modules/networking-vpc"
    },
    {
      "id": "rds-users",
      "label": "users-db",
      "type": "aws_db_instance",
      "cloud": "aws",
      "wave": 2,
      "module_dir": "modules/rds-users"
    }
  ],
  "connections": [
    { "from": "networking-vpc", "to": "rds-users", "outputs": ["vpc_id", "private_subnet_ids"] }
  ],
  "region": "us-east-1",
  "project_name": "myproject"
}
```

### After `/ServiceModelerConfirm` → write `02-build-plan.json`

```json
{
  "approved_at": "2024-01-15T11:00:00Z",
  "waves": {
    "1": ["networking-vpc", "iam-base-roles"],
    "2": ["rds-users"],
    "3": ["lambda-auth"],
    "4": ["api-gateway"]
  },
  "dependency_map": {
    "rds-users": {
      "needs_from": { "networking-vpc": ["vpc_id", "private_subnet_ids"] }
    },
    "lambda-auth": {
      "needs_from": {
        "iam-base-roles": ["lambda_execution_role_arn"],
        "rds-users": ["db_endpoint", "secret_arn"]
      }
    }
  },
  "state_backend": {
    "s3_bucket": "myproject-tf-state",
    "dynamodb_table": "myproject-tf-lock",
    "region": "us-east-1"
  },
  "environments": ["dev", "prod"]
}
```

### After `/BuildPlanConfirm` → write `03-inputs.json`

```json
{
  "approved_at": "2024-01-15T12:00:00Z",
  "global": {
    "project_name": "myproject",
    "region": "us-east-1",
    "terraform_version": ">= 1.6.0",
    "aws_provider_version": "~> 5.0"
  },
  "services": {
    "networking-vpc": {
      "vpc_cidr": "10.0.0.0/16",
      "az_count": 2,
      "enable_nat_gateway": true
    },
    "rds-users": {
      "db_engine": "postgres",
      "db_engine_version": "15.4",
      "db_instance_class": "db.t3.medium",
      "db_allocated_storage_gb": 100,
      "db_multi_az": false,
      "db_backup_retention_days": 7
    },
    "lambda-auth": {
      "lambda_runtime": "python3.12",
      "lambda_memory_mb": 512,
      "lambda_timeout_seconds": 30,
      "lambda_architecture": "arm64"
    }
  }
}
```

### After each service builds → update `04-build-progress.json`

```json
{
  "started_at": "2024-01-15T13:00:00Z",
  "last_updated": "2024-01-15T13:45:00Z",
  "completed": [
    { "service": "networking-vpc", "completed_at": "2024-01-15T13:10:00Z", "validated": true },
    { "service": "iam-base-roles", "completed_at": "2024-01-15T13:20:00Z", "validated": true }
  ],
  "current_service": "rds-users",
  "remaining": ["lambda-auth", "api-gateway"],
  "total": 5,
  "completed_count": 2
}
```

---

## Memory Write Instructions for Claude

After each gate is approved, Claude must:

1. Write the gate-specific JSON file to `.claude/memory/`
2. Update `tf-state.json` with the new phase and timestamp
3. Confirm in chat: `✅ State saved to .claude/memory/tf-state.json`

After each service is built:
1. Update `04-build-progress.json`
2. Update `build_progress` in `tf-state.json`

---

## Memory Reset

If the user wants to start over:
```
/tf-reset
```
Claude deletes all files in `.claude/memory/` and confirms.  
The `.claude/skills/` folder is untouched.

---

## handoff.json — Bootstrap File for Context-Cleared Sessions

Written at the end of EVERY command. Lets the next command bootstrap without
re-reading large memory files or relying on conversation history.

```json
{
  "last_command": "/ServiceBuilder",
  "completed_at": "2024-01-15T14:45:00Z",
  "phase": "DEPLOYING",
  "next_command": "/ServiceBuilder",
  "next_action": "Build lambda-auth (Wave 3) — depends on rds-users ✅",
  "quick_context": {
    "project": "myproject",
    "region": "us-east-1",
    "services_total": 5,
    "completed": ["networking-vpc", "iam-base-roles", "rds-users"],
    "next_service": "lambda-auth",
    "remaining": ["lambda-auth", "api-gateway"],
    "last_plan_summary": "Plan: 8 to add, 0 to change, 0 to destroy."
  },
  "files_written": [
    "modules/rds-users/main.tf",
    "modules/rds-users/variables.tf",
    "modules/rds-users/outputs.tf",
    "modules/rds-users/versions.tf",
    "modules/rds-users/tests/main.tftest.hcl",
    ".claude/memory/04-build-progress.json",
    ".claude/memory/last-plan.txt",
    "execution.md"
  ],
  "clear_after": true
}
```

On next command startup:
1. Read `handoff.json` first — get `quick_context` in < 500 tokens
2. Only read other memory files if the command needs deeper state
3. Show the one-line banner from `quick_context`
