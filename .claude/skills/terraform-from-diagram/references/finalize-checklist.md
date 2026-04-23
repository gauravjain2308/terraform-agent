# Phase 8 — Finalize Checklist (`/DeployOrchestrator`)

**Read `references/cicd-and-local-dev.md` fully before generating any files.**

## Steps

1. **Root module wiring** — ensure `environments/dev/main.tf` passes all cross-module outputs correctly
2. **Generate `provider.tf`** for each environment — profile-aware (local uses `AWS_PROFILE`, CI uses OIDC role with no profile set). Use template from `references/cicd-and-local-dev.md`.
3. **Generate GitHub Actions workflows:**
   - `.github/workflows/terraform-plan.yml` — runs plan on every PR, posts output as comment
   - `.github/workflows/terraform-apply.yml` — applies dev on merge to main; applies prod after manual approval
4. **Generate `iam-github-oidc/main.tf`** — one-time bootstrap module to create OIDC roles for CI. User runs once manually.
5. **Generate `README.md`** — must include: architecture summary, prerequisites, local dev setup, CI/CD pipeline explanation, GitHub Actions one-time setup. Use README template from `references/cicd-and-local-dev.md`.
6. **Generate `environments/dev/terraform.tfvars.example`** — all required variables with placeholder values and comments
7. **Run full validation (write results to execution.md, show only pass/fail in chat):**
   ```bash
   terraform fmt -recursive
   cd environments/dev && terraform init -backend=false && terraform validate
   tflint --recursive
   checkov -d . --framework terraform
   ```
8. **Show compact final summary (≤ 20 lines):**
   ```
   ✅ Project complete  —  {n} services  |  ~{x} resources

   Files:
     modules/          {n} modules
     environments/     dev + prod
     .github/          terraform-plan.yml, terraform-apply.yml
     iam-github-oidc/  main.tf
     execution.md      full build log
     README.md         local dev + CI/CD guide

   Validation: fmt ✅  validate ✅  tflint ✅  checkov ✅

   Next steps:
     1. cd state-bootstrap && terraform init && terraform apply  (create S3 state bucket — FIRST)
     2. make setup                (first-time local init — requires state bucket to exist)
     3. make plan                 (see what will change)
     4. cd iam-github-oidc && terraform apply  (CI bootstrap, once)

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅  Done. Files written. Context can be cleared.
       Run:  /clear
       (No next skill command — project is complete)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```
