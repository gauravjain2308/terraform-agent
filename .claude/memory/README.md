# Claude Memory — auto-managed by skill

Files written here survive /clear and let Claude resume from where it left off.
This folder is GITIGNORED.

  tf-state.json              master state, phase, gate statuses per wave
  handoff.json               compact bootstrap for next command
  01-services.json           locked after /ServicesRefinerConfirm
  02-build-plan.json         locked after /ServiceModelerConfirm
  03-inputs-wave-{n}.json    one per wave, locked after /BuildPlanConfirm wave:{n}
  04-build-progress.json     wave + service build status
  04-iam-roles.json          IAM roles/policy summary
  cost-estimate.json         last infracost result
