# /ServiceBuilder  [wave:{n}]  OR  [wave:{n} service:{name}]  OR  [{service-name}]

**Legacy convenience command.** Chains `/ServiceCodeWriter` and `/TerraformValidator`
in one run. Prefer running the two commands separately — that is the primary flow
(see `/help`).

Modes (same arguments as the two underlying commands):
  /ServiceBuilder                            → write + validate next service in next unbuilt wave
  /ServiceBuilder wave:2                     → write + validate next unwritten service in wave 2
  /ServiceBuilder wave:2 service:rds-users   → write + validate one specific service in a wave
  /ServiceBuilder rds-users                  → write + validate one specific service

## Behaviour

Run the following sequence. Pass `$ARGUMENTS` through unchanged to each.

1. Invoke `/ServiceCodeWriter $ARGUMENTS` (all of Steps 1–8 of that command).
   - If `/ServiceCodeWriter` stops due to a gate check, missing inputs, or a
     sanity-check failure — stop here. Do NOT run the validator.
2. Determine the service that was just written (read it from
   `.claude/memory/handoff.json.next_command`).
3. Invoke `/TerraformValidator service:{that-service}` (all of Steps 1–7 of that command).
4. Present a combined summary:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {service-name}  [Wave {n} — {x}/{total_in_wave}]
   Code:       → terraform/modules/{service-name}/
   Wired:      → terraform/environments/{dev,prod}/modules/{service-name}.tf
   Validate:   ✅ passed
   Plan:       {n} to add, {n} to change, {n} to destroy
   Tests:      {n}/{n} passed
   Log:        → agent/execution.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

End with the usual `/clear` instruction block pointing at whatever
`handoff.json.next_command` now holds.

## Note

Running the two commands separately is recommended when:
- You want to review the generated code before invoking Terraform.
- You want to run `terraform init/validate/fmt` yourself in the terminal.
- Validation fails and you want to tweak code before re-validating.

For that flow, use:
```
/ServiceCodeWriter        # writes code only — no terraform CLI
/TerraformValidator       # runs init/validate/fmt/plan/test in the terminal
```
