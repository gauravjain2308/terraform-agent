# /IAMModelerConfirm — Lock IAM Review

This is the **only** command that locks IAM. `/ServiceModelerConfirm` generates and lints IAM but does not lock it; `/IAMModeler` regenerates it. This command is the explicit developer sign-off.

## Step 1 — Read file

Read `agent/review/iam-model-review.md` and `agent/review/iam-model-review.json`.
If either missing: `❌ Run /ServiceModelerConfirm (or /IAMModeler) first to generate IAM files.`

Read `.claude/memory/tf-state.json`. Gate 2 must be CONFIRMED:
```
❌ Cannot lock IAM — Service Model not confirmed. Run /ServiceModelerConfirm first.
```

## Step 2 — Validate

Check:
- `permission_boundary_arn` filled (value may be `none` if not required, but key must be present)
- `iam_path` filled
- No "← fill this in" placeholders remaining in the markdown
- All checklist items in `checklist` are boolean (not null)
- No inline policy `resource_scope` ends with a bare `*`
- No role `managed` list contains `AdministratorAccess` or `PowerUserAccess`
- Every consumer that reads from Secrets Manager or SSM has a `kms:Decrypt` statement scoped by `kms:ViaService` (check terraform/modules/*/iam.tf)
- STATUS is PENDING (file not already locked)

On failure, list every problem specifically and stop.

## Step 3 — Confirm

Show summary:
```
Ready to lock IAM:
  Roles:            {n} in iam-base-roles
  Inline policies:  {n}
  Resource policies: {n}
  Permission boundary: {value or "none"}
  IAM path:         {value}

Confirm? Type "yes" to lock.
```
Wait for "yes". Anything else → stop without writing.

## Step 4 — Update file and memory

- Update STATUS: CONFIRMED in `agent/review/iam-model-review.md`
- Set `"confirmed": true` in `agent/review/iam-model-review.json`
- Write `.claude/memory/04-iam-roles.json` (copy of the confirmed json)
- Update `.claude/memory/tf-state.json`:
  - `gates.iam_review` → `"CONFIRMED"`
  - `current_phase` → `"IAM_MODELED"`
  - `last_command` → `"/IAMModelerConfirm"`
  - `last_updated` → current ISO timestamp
- Write `.claude/memory/handoff.json` with `"phase": "IAM_MODELED"` and `"next_command": "/BuildPlan"`

## Step 5 — Show summary

```
✅ IAM review confirmed
   → agent/review/iam-model-review.md      ✅ confirmed ({n} roles, {n} policies)
   → .claude/memory/04-iam-roles.json      ✅ written
   → .claude/memory/tf-state.json          ✅ current_phase = IAM_MODELED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done.
    Run:  /clear
    Then: /BuildPlan  (collect config values per wave)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
