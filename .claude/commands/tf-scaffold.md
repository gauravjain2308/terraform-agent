# /tf-scaffold  [wave:{n}]
Regenerate or extend the terraform/ directory structure.
Normally runs automatically inside /ServiceModelerConfirm — use this only to re-run manually.

## When to use this manually
- terraform/ was accidentally deleted — rebuild from manifest
- Adding a new wave to an existing project
- Manifest changed (e.g. service renamed) and terraform/ needs updating

## Step 1 — Verify prerequisites

Read `.claude/memory/tf-state.json`.
Verify gate2_build_plan: CONFIRMED. If not: `❌ Run /ServiceModelerConfirm first.`

If `.claude/memory/scaffold-manifest.json` already exists — use it.
Otherwise — write it now from 01-services.json + 02-build-plan.json.

## Step 2 — Determine scope from $ARGUMENTS

- No args or `full`  → run scaffold.py --manifest ... (full scaffold)
- `wave:N`           → run scaffold.py --manifest ... --wave N  (one wave's modules only)
- `force`            → run scaffold.py --manifest ... --force   (overwrite existing files)

## Step 3 — Run scaffold.py automatically

Show: `⚙️  Running scaffold.py...`

Run:
```bash
python3 agent/scripts/scaffold/scaffold.py \
  --manifest .claude/memory/scaffold-manifest.json \
  {--wave N if wave specified} \
  {--force if force specified}
```

Capture stdout. Show result.

## Step 4 — Update memory and confirm

Update scaffold_complete: true in tf-state.json.

Show:
```
✅ terraform/ scaffolded
   {n} files created

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Run /clear
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
