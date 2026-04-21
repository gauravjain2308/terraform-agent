# /IAMModeler  [refresh | regen]
Regenerate or lint IAM files after Service Model confirmation. **Never locks IAM** — use `/IAMModelerConfirm` for that.

## When to use
- You edited `agent/review/iam-model-review.md` or `.json` and want to re-lint
- Build plan changed and you need to regenerate IAM from scratch
- Modules were built and you want `build_status` refreshed in the IAM files

## Command variants

```
/IAMModeler           → re-lint the current iam-model-review files (read-only)
/IAMModeler refresh   → run iam-generator.py --refresh to update built/not-built status
/IAMModeler regen     → run iam-generator.py from scratch (use if build plan changed)
```

---

## Step 1 — Load state

Read `.claude/memory/tf-state.json`.
Verify `gates.gate2_build_plan == "CONFIRMED"`. If not: `❌ Run /ServiceModelerConfirm first.`

If `gates.iam_review == "CONFIRMED"` and the user passed `regen`:
```
⚠️  IAM is already CONFIRMED. Regenerating will reset it to PENDING.
    Continue? Type "regen" again to confirm.
```
Wait for explicit `regen` before proceeding. This keeps locked IAM safe from accidental overwrite.

## Step 2 — Handle variant

**`/IAMModeler refresh`:**
```bash
python3 agent/scripts/scaffold/iam-generator.py --refresh \
  --services .claude/memory/01-services.json \
  --plan     .claude/memory/02-build-plan.json
```
Then continue to lint below.

**`/IAMModeler regen`:**
```bash
python3 agent/scripts/scaffold/iam-generator.py \
  --services .claude/memory/01-services.json \
  --plan     .claude/memory/02-build-plan.json
```
Reset `gates.iam_review` to `"PENDING"` in `tf-state.json`. Then continue to lint below.

**`/IAMModeler` (no args):**
Skip straight to lint.

## Step 3 — Check files exist

If `agent/review/iam-model-review.json` missing:
```
❌ IAM files not found. Run /ServiceModelerConfirm or /IAMModeler regen.
```
Stop.

## Step 4 — Lint (warnings only — does not lock)

Read `agent/review/iam-model-review.json`. Run checks:

- **Structure**: all required keys present
- **Least privilege**: no bare wildcard resource scopes
- **Security**: no `AdministratorAccess` / `PowerUserAccess` in `managed`
- **Config**: `iam_path` and `permission_boundary_arn` keys present
- **KMS coverage**: every consumer that reads from Secrets Manager or SSM has a `kms:Decrypt` statement scoped by `kms:ViaService` (inspect `terraform/modules/{svc}/iam.tf`)

Surface findings as warnings. Show checklist summary from JSON.

## Step 5 — Next step

This command **never** writes `confirmed: true` or updates `current_phase`. If lint is clean and you're ready to lock:
```
✅ {n} checks passed.

Next: open agent/review/iam-model-review.md in VS Code, edit if needed,
      then run /IAMModelerConfirm to lock IAM.
```

If lint surfaced warnings, list them and stop — let the user fix and re-run `/IAMModeler`.
