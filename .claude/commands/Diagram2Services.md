Parse the attached draw.io diagram and bootstrap the project state.

## IMPORTANT — Write memory file FIRST before anything else

**Step 1 — Create memory directory and write initial state file immediately:**

Create the file `.claude/memory/tf-state.json` with this content:
```json
{
  "project_name": "pending",
  "current_phase": "DIAGRAM_INGESTED",
  "last_command": "/Diagram2Services",
  "last_updated": "<current timestamp>",
  "gates": {
    "gate1_services": "PENDING",
    "gate2_build_plan": "PENDING",
    "gate3_inputs": "PENDING",
    "build": "NOT_STARTED",
    "finalize": "NOT_STARTED"
  },
  "services": [],
  "diagram_file": "<name of attached file>",
  "build_progress": {
    "completed": [],
    "current": null,
    "remaining": []
  }
}
```

After writing, confirm: `✅ .claude/memory/tf-state.json written`

If the file cannot be written, stop and tell the user before continuing.

---

**Step 2 — Check for existing project**

If `.claude/memory/tf-state.json` already existed before this run and had a phase other than DIAGRAM_INGESTED, ask:
```
⚠️ Found existing project "{name}" at phase {phase}.
   Type "resume" to continue it, or "reset" to start fresh.
```
Wait for response before continuing.

---

**Step 3 — Parse the diagram**

Look for the attached `.drawio` or `.xml` file. If no file is attached, look in the workspace for any `.drawio` file and use that.

Parse the XML:
- mxCell with vertex="1" and a non-empty value → service/component
- mxCell with edge="1" → connection between services
- Extract: id, value (label), style (to infer type), tooltip (extra config)

Use the style string to infer service type:
- aws4.lambda → Lambda Function
- aws4.rds → RDS
- aws4.api_gateway → API Gateway
- aws4.s3 → S3 Bucket
- aws4.sqs → SQS Queue
- aws4.sns → SNS Topic
- aws4.elasticache → ElastiCache
- aws4.vpc or swimlane → VPC/Networking
- aws4.iam → IAM

---

**Step 4 — Show extraction results**

Display a structured table:

```
## Extracted Services
| # | Label | Inferred Type | Cloud | Notes |
|---|-------|--------------|-------|-------|
| 1 | ...   | ...          | AWS   | ...   |

## Extracted Connections
| From | To | Type | Notes |
|------|----|------|-------|

## Ambiguities
- ...
```

---

**Step 5 — Update tf-state.json with extracted data**

Rewrite `.claude/memory/tf-state.json` with the project name (use diagram filename as default), services list, and diagram file name.

Also write `.claude/memory/handoff.json`:
```json
{
  "last_command": "/Diagram2Services",
  "phase": "DIAGRAM_INGESTED",
  "next_command": "/ServicesRefiner",
  "next_action": "Review and confirm service names",
  "quick_context": {
    "project": "<project_name>",
    "services_found": <count>,
    "diagram_file": "<filename>"
  },
  "files_written": [
    ".claude/memory/tf-state.json",
    ".claude/memory/handoff.json"
  ]
}
```

---

**Step 6 — Confirm files written and end**

Show:
```
✅ Parsed: {n} services, {n} connections
✅ .claude/memory/tf-state.json  — written
✅ .claude/memory/handoff.json   — written

Verify the files exist in VS Code Explorer under .claude/memory/
before running /clear.
```

End response with:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Memory files written to disk.
    Confirm .claude/memory/ shows tf-state.json
    Run:  /clear
    Then: /ServicesRefiner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```


## Path reference
All terraform code goes into `terraform/` subfolder.
All review files go into `agent/review/`.
All build logs go into `agent/execution.md`.
Only `terraform/` is committed to git (root .gitignore ignores everything else).

## Gitignore files
When initializing, check that these gitignore files are present:

1. Root `.gitignore` — ignores everything except `terraform/`:
```gitignore
/*
!/terraform/
!.gitignore
```

2. `terraform/.gitignore` — terraform-specific ignores (*.tfvars, .terraform/, *.tfstate, plan files, *.zip)
   Reference: `.claude/skills/terraform-from-diagram/references/terraform-gitignore.example`

3. `agent/.gitignore` — safety net ignoring all agent files
4. `.claude/.gitignore` — safety net ignoring all claude files

If any are missing, create them before proceeding.
