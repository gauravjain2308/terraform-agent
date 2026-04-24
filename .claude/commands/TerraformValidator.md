# /TerraformValidator  [service:{name}]  OR  [wave:{n}]  OR  (no args)

Validate already-generated Terraform code. **This command does NOT rewrite code**
— it only runs terminal commands and reports results. If validation fails, the
user re-runs `/ServiceCodeWriter {service-name}` to regenerate.

> **Optional step** — `/TerraformValidator` is NOT required to unblock the next wave.
> Services at `CODE_WRITTEN` status are sufficient for `/ServiceCodeWriter` to proceed
> to the next wave. Run this command when you want explicit validation confirmation
> or before running `/DeployOrchestrator`.

Modes:
  /TerraformValidator                        → validate next service at CODE_WRITTEN status (from handoff.json)
  /TerraformValidator service:{name}         → validate one specific service module
  /TerraformValidator wave:{n}               → validate every CODE_WRITTEN service in a wave, in order

All terminal output is captured to `agent/execution.md`.

## Step 1 — Load state and pick target(s)

Read `.claude/memory/handoff.json`, `.claude/memory/tf-state.json`, and
`.claude/memory/04-build-progress.json`.

Show banner: `📂 {project}  |  validating  |  terraform/`

Pick targets per mode:

- **service:{name}** — single service. If its status is not `CODE_WRITTEN` or `COMPLETE`, refuse:
  ```
  ❌ Cannot validate {service} — no code written yet.
     Run: /ServiceCodeWriter {service}
  ```
  (If status is already `COMPLETE`, proceed — re-validation is allowed.)

- **wave:{n}** — all services in that wave with status `CODE_WRITTEN`. If none:
  ```
  ℹ️  No services in Wave {n} are at CODE_WRITTEN status.
      Run /ServiceCodeWriter wave:{n} first.
  ```

- **no args** — pick first service at `CODE_WRITTEN` in wave order.
  ```
  ℹ️  No services pending validation.
      Run /ServiceCodeWriter to write the next service.
  ```

## Step 2 — Announce

For each target, show in chat AND append to `agent/execution.md`:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪  Validating: {service-name}  [Wave {n}]
    Module:  terraform/modules/{service-name}/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 3 — Run validation commands in the terminal

For each target module, run in order (stop the target on first failure, but
continue with remaining targets in wave mode):

```bash
cd terraform/modules/{service-name}
terraform init -backend=false
terraform validate
terraform fmt -check
```

Capture stdout+stderr of each command to `agent/execution.md` under a
`## Validation — {service-name}` section. Show only the one-line result per
command in chat.

## Step 4 — Run plan and tests (after validate passes)

Only if Step 3 succeeded for this target:

```bash
cd terraform/modules/{service-name}
terraform plan -var-file=tests/fixtures/test.tfvars -no-color 2>&1
terraform test
```

Also run `terraform plan` for each previously-built dependent:
```bash
cd terraform/modules/{dependent}
terraform plan -var-file=tests/fixtures/test.tfvars -no-color 2>&1
```

Append full output to `agent/execution.md` and overwrite `.claude/memory/last-plan.txt`
with the target service's plan output.

## Step 5 — Compact chat output

Read `iam_status` for each target from `.claude/memory/04-build-progress.json`.

Per target:
```
🧪 {service-name}
   terraform init        ✅
   terraform validate    ✅
   terraform fmt -check  ✅
   terraform plan        ✅  {n} to add, {n} to change, {n} to destroy
   terraform test        ✅  {n}/{n} passed
   IAM roles:            {one of the lines below}
     ✅ CREATED  ({n} roles applied in Step 4b)
     ⚠️  SKIPPED — roles not created (insufficient permissions — see warning below)
     —  NOT REQUIRED  (no IAM roles for this service type)
     ⚠️  ERROR  — IAM apply failed with non-permission error (see agent/execution.md)
   Dependents:           {dep} ✅  {dep} ✅
```

If `iam_status` is `"SKIPPED"` for any target, append this block after the compact output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  IAM ROLES SKIPPED — manual creation required before deploying {service-name}

   The following roles were not created (Terraform executor lacked iam:CreateRole):

   {for each role from iam-model-review.json where module == service-name}
     Role:    {role_name}
     Trust:   {trust_principal}
     Attach:  {managed_policy_arns}

   The module code is valid and passes validation, but a terraform apply WILL FAIL
   in AWS until these roles exist.

   To resolve — choose one:
     A) Grant iam:CreateRole + iam:AttachRolePolicy to the Terraform executor role,
        then re-run /ServiceCodeWriter {service-name} to retry role creation.
     B) Create the roles manually in AWS, then update in memory:
          .claude/memory/04-build-progress.json → iam_status: "CREATED", iam_warning: false
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

On failure, show the exact failing command, the first ~10 lines of error
output, and:
```
❌ {command} failed.
   Full output: agent/execution.md (## Validation — {service-name})
   To regenerate code and retry:
     /ServiceCodeWriter {service-name}
     /TerraformValidator service:{service-name}
```

Do NOT update memory status on failure — the service stays at `CODE_WRITTEN`.

## Step 6 — Update memory (on success)

For each target that passed all of Steps 3 and 4:

Update `.claude/memory/04-build-progress.json`:
- Flip this service's status from `CODE_WRITTEN` → `COMPLETE`.
- Preserve `iam_status` and `iam_warning` as-is — do NOT clear them on COMPLETE.
  A SKIPPED role does not block COMPLETE (code is valid); the warning persists so
  `/DeployOrchestrator` can surface it before the final terraform apply.
- If ALL services in the wave are now `COMPLETE`, mark the wave `COMPLETE`.
  If any service in the wave has `iam_warning: true`, also set `wave_iam_warning: true`
  on the wave entry so the orchestrator can gate the apply.

Update `.claude/memory/tf-state.json`:
- Append this service to `build_progress.completed`.
- Set `last_command` → `"/TerraformValidator"` and `last_updated` → current ISO timestamp.
- Set `current_phase`:
  - `"DEPLOYING"` if any service remains unbuilt,
  - `"DEPLOY_COMPLETE"` if this was the last service in the last wave.

Write `.claude/memory/handoff.json`:
- If more services remain: `"next_command": "/ServiceCodeWriter"` and `"phase": "DEPLOYING"`.
- If all complete: `"next_command": "/DeployOrchestrator"` and `"phase": "DEPLOY_COMPLETE"`.

## Step 7 — Final summary and end

Single-service mode:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {service-name} VALIDATED → status COMPLETE  [Wave {n} — {x}/{total}]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wave mode — add a roll-up:
```
Wave {n}: {passed}/{total} validated
  ✅ {service}
  ✅ {service}
  ❌ {service}   ← see agent/execution.md
```

If wave is now complete:
```
🎉 Wave {n} complete! All {n} services validated.
```

End with:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Done. Validation finished. Clear context.
    Run:  /clear
    Then: {next_command from handoff.json}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
