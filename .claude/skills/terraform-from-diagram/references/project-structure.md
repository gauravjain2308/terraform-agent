# Phase 6 — Project Directory Structure

Create the following standard layout during scaffolding:

```
{project-name}/
├── .github/
│   └── workflows/
│       ├── terraform-plan.yml   ← auto-plan on every PR, posts comment
│       └── terraform-apply.yml  ← auto-apply dev; manual gate for prod
├── state-bootstrap/
│   ├── main.tf                  ← one-time bootstrap: creates S3 state bucket (run FIRST, manually)
│   ├── variables.tf             ← bucket_name, region
│   └── versions.tf              ← required_version >= 1.10
├── iam-github-oidc/
│   └── main.tf                  ← one-time bootstrap: creates CI IAM roles (run manually, after state bucket)
├── .gitignore                   ← ALWAYS generate this (see standards)
├── .tflint.hcl                  ← static analysis config
├── README.md                    ← includes local dev setup + CI/CD instructions
├── .terraform-version           # pin exact Terraform version
├── modules/
│   └── {service-name}/          # one folder per service
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── versions.tf          # required_providers ONLY (no required_version)
│       └── tests/
│           ├── main.tftest.hcl  # native Terraform test
│           └── fixtures/
│               └── test.tfvars
├── environments/
│   ├── dev/
│   │   ├── main.tf              # root module, calls child modules
│   │   ├── provider.tf          # profile-aware: local uses AWS_PROFILE, CI uses OIDC role
│   │   ├── versions.tf          # required_version + required_providers (root only)
│   │   ├── variables.tf
│   │   ├── backend.tf
│   │   ├── terraform.tfvars          ← populated from 03_inputs_collection (gitignored)
│   │   └── terraform.tfvars.example  ← safe to commit; no secrets
│   └── prod/
│       ├── main.tf
│       ├── provider.tf
│       ├── versions.tf
│       ├── variables.tf
│       ├── backend.tf
│       ├── terraform.tfvars          ← populated from 03_inputs_collection (gitignored)
│       └── terraform.tfvars.example  ← safe to commit; no secrets
└── review/                      # human review files (kept for audit trail)
    ├── services-review.md
    ├── build-plan-review.md
    └── 03_inputs_collection.md   ← filled-in pre-flight inputs
```

## .gitignore Rules (Always Generate)

Read the `.gitignore` template in `references/terraform-standards.md`. Key rules:
- `terraform.lock.hcl` → **ALWAYS commit** (never gitignore)
- `terraform.tfvars` → **NEVER commit** (gitignored; use `.tfvars.example` for templates)
- `.terraform/` and `*.tfstate` → **NEVER commit**

## Run Order for One-Time Bootstrap Modules

```
1. state-bootstrap/   → terraform init && terraform apply   (creates S3 state bucket — run FIRST)
2. environments/dev/  → terraform init && terraform plan && terraform apply
3. iam-github-oidc/   → terraform init && terraform apply   (creates CI IAM roles)
```

Never run `environments/dev/` before `state-bootstrap/` — `terraform init` will fail with
"bucket does not exist". See `references/bootstrap-guide.md` for full instructions.

---

## Anti-Pattern: Never Use `terraform workspace`

The directory-per-environment pattern above is the correct approach. Workspaces share a single
backend configuration and make it easy to accidentally target the wrong environment.
Always use separate directories.
