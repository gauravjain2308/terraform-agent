# Local Dev & CI/CD Guide

This file defines what the skill must generate for local development setup and CI/CD pipelines,
and what guidance to include in the project README.

---

## The Core Split — Always Explain This to the User

```
Local machine     →  explore, write, fmt, validate, plan freely, test modules
CI (PR)           →  runs plan automatically, posts output as PR comment
CI (push/manual)  →  runs plan again on main, waits for human to trigger apply
Human             →  reviews plan output, manually triggers apply for dev OR prod
```

**Rule: `terraform apply` is ALWAYS triggered by a human — never automatically.**
CI runs plans and shows you what will change. A human reviews that output and decides to apply.
This applies to both dev and prod — no environment is ever auto-applied.

---

## What the Skill Must Generate

### 1. GitHub Actions workflow files

Always generate these two files as part of Phase 8:

- `.github/workflows/terraform-plan.yml` — runs plan on every PR and every push to main, posts output as comment
- `.github/workflows/terraform-apply.yml` — manually triggered only (`workflow_dispatch`); human selects environment (dev or prod) and confirms before apply runs

### 2. Local dev setup section in README

Always include a "Local Development" section in `README.md` covering:
- Prerequisite tool installation
- AWS credential setup (profile-based)
- First-time init steps
- Daily workflow commands

### 3. `provider.tf` with local profile support

The provider block must handle both local (profile) and CI (role) without code changes,
using an environment variable to switch:

```hcl
# environments/dev/provider.tf

provider "aws" {
  region  = var.region

  # In CI: AWS_PROFILE is unset; credentials come from the OIDC role
  # Locally: set AWS_PROFILE=myproject-dev in your shell
  # This line is a no-op when the env var is not set
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

Add to `variables.tf`:
```hcl
variable "aws_profile" {
  description = "AWS CLI profile for local development. Leave empty in CI (credentials come from role)."
  type        = string
  default     = ""  # empty = use environment/role credentials (correct for CI)
}
```

Local developers set in their `terraform.tfvars` (gitignored):
```hcl
aws_profile = "myproject-dev"
```

CI never sets this variable — it defaults to `""` and uses the OIDC role.

---

## GitHub Actions Workflow Templates

### terraform-plan.yml

```yaml
# .github/workflows/terraform-plan.yml
# Runs on every PR that touches Terraform code.
# Posts the plan output as a PR comment so reviewers can see what will change.

name: Terraform Plan

on:
  pull_request:
    paths:
      - 'environments/**'
      - 'modules/**'
      - '.github/workflows/terraform-*.yml'

permissions:
  id-token: write       # required for OIDC credential exchange
  contents: read
  pull-requests: write  # required to post plan as PR comment

jobs:
  plan-dev:
    name: Plan (dev)
    runs-on: ubuntu-latest
    environment: dev-plan   # read-only environment, no approval needed

    defaults:
      run:
        working-directory: environments/dev

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC — no stored keys)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_PLAN_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ">=1.6.0"

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: .   # run from root

      - name: tflint
        uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest
      - run: tflint --init && tflint --recursive
        working-directory: .

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        id: plan
        run: |
          terraform plan -no-color -out=tf.plan 2>&1 | tee /tmp/plan_output.txt
          echo "exitcode=${PIPESTATUS[0]}" >> $GITHUB_OUTPUT
        continue-on-error: true  # post the comment even if plan fails

      - name: Post Plan to PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const planOutput = fs.readFileSync('/tmp/plan_output.txt', 'utf8');
            const status = '${{ steps.plan.outputs.exitcode }}' === '0' ? '✅' : '❌';
            const body = [
              `## ${status} Terraform Plan — \`environments/dev\``,
              '',
              '<details><summary>Show Plan</summary>',
              '',
              '```terraform',
              planOutput.slice(0, 60000),  // GitHub comment limit
              '```',
              '',
              '</details>',
              '',
              `*Triggered by @${{ github.actor }} on \`${{ github.head_ref }}\`*`
            ].join('\n');

            // Find existing plan comment and update it, or create new
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });
            const existing = comments.find(c =>
              c.user.type === 'Bot' && c.body.includes('Terraform Plan — `environments/dev`')
            );
            if (existing) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existing.id,
                body,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body,
              });
            }

      - name: Fail if plan failed
        if: steps.plan.outputs.exitcode != '0'
        run: exit 1
```

---

### terraform-apply.yml

```yaml
# .github/workflows/terraform-apply.yml
# MANUALLY TRIGGERED ONLY — never runs automatically.
# A human goes to Actions → Terraform Apply → Run workflow,
# selects the environment (dev or prod), and confirms.
# For prod, an additional GitHub Environment approval gate is required.

name: Terraform Apply

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to apply to'
        required: true
        type: choice
        options:
          - dev
          - prod
      confirm:
        description: 'Type "apply" to confirm you have reviewed the plan'
        required: true
        type: string

permissions:
  id-token: write
  contents: read

jobs:
  validate-confirmation:
    name: Validate confirmation input
    runs-on: ubuntu-latest
    steps:
      - name: Check confirmation
        run: |
          if [ "${{ inputs.confirm }}" != "apply" ]; then
            echo "❌ Confirmation failed. You must type 'apply' exactly."
            exit 1
          fi
          echo "✅ Confirmation accepted. Proceeding with apply to ${{ inputs.environment }}."

  apply:
    name: Apply (${{ inputs.environment }})
    runs-on: ubuntu-latest
    needs: validate-confirmation
    # GitHub Environment gate:
    # - 'dev' environment: no required reviewers (human already confirmed via input)
    # - 'prod' environment: set required reviewers in GitHub Settings → Environments
    environment: ${{ inputs.environment }}

    defaults:
      run:
        working-directory: environments/${{ inputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ inputs.environment == 'prod' && secrets.AWS_APPLY_ROLE_ARN_PROD || secrets.AWS_APPLY_ROLE_ARN_DEV }}
          aws-region: ${{ vars.AWS_REGION }}

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ">=1.6.0"

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan (re-run to confirm state is current)
        id: plan
        run: terraform plan -no-color -out=tf.plan 2>&1 | tee /tmp/plan_output.txt

      - name: Show plan summary before applying
        run: |
          echo "========================================="
          echo "ABOUT TO APPLY THE FOLLOWING CHANGES:"
          echo "========================================="
          cat /tmp/plan_output.txt | tail -20
          echo "========================================="
          echo "Triggered by: ${{ github.actor }}"
          echo "Environment: ${{ inputs.environment }}"
          echo "========================================="

      - name: Terraform Apply
        run: terraform apply tf.plan

      - name: Show applied changes
        run: terraform show -no-color

      - name: Post apply summary to Actions summary
        run: |
          echo "## ✅ Apply complete — \`${{ inputs.environment }}\`" >> $GITHUB_STEP_SUMMARY
          echo "- **Applied by:** ${{ github.actor }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Time:** $(date -u)" >> $GITHUB_STEP_SUMMARY
          echo "- **Commit:** ${{ github.sha }}" >> $GITHUB_STEP_SUMMARY
```

---

## OIDC Setup — IAM Role for GitHub Actions

The workflows above use OIDC (no stored access keys). The user needs to create this IAM role
once. Include these instructions in the README.

### Terraform to create the OIDC role (generate this as `iam-github-oidc/main.tf`):

```hcl
# One-time bootstrap: create the GitHub Actions OIDC role
# Run this manually BEFORE the main project pipeline

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # GitHub's OIDC thumbprint (stable — this value is correct)
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      # Restrict to your specific repo — change this:
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:{your-github-org}/{your-repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions_plan" {
  name               = "github-actions-terraform-plan"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
  description        = "Used by GitHub Actions for terraform plan (read-only)"
}

resource "aws_iam_role" "github_actions_apply_dev" {
  name               = "github-actions-terraform-apply-dev"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
  description        = "Used by GitHub Actions for terraform apply to dev"
}

resource "aws_iam_role" "github_actions_apply_prod" {
  name               = "github-actions-terraform-apply-prod"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
  description        = "Used by GitHub Actions for terraform apply to prod (requires manual approval)"
}

output "plan_role_arn" {
  value = aws_iam_role.github_actions_plan.arn
}
output "apply_dev_role_arn" {
  value = aws_iam_role.github_actions_apply_dev.arn
}
output "apply_prod_role_arn" {
  value = aws_iam_role.github_actions_apply_prod.arn
}
```

---

## README Local Development Section Template

Always include this section in the generated `README.md`:

```markdown
## Local Development

### Prerequisites

Install required tools:
```bash
brew install terraform tflint checkov awscli
```

Verify versions:
```bash
terraform version    # must be >= 1.6.0
tflint --version
aws --version
```

### AWS Credentials Setup (Local Only)

Create a dedicated AWS profile for this project — do not use your default profile:

```bash
aws configure --profile {project-name}-dev
# Enter your dev IAM user access key and secret when prompted
```

Then set it in your shell:
```bash
export AWS_PROFILE={project-name}-dev
```

Or add to `environments/dev/terraform.tfvars` (this file is gitignored — safe):
```hcl
aws_profile = "{project-name}-dev"
```

### First-Time Setup

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
# Fill in your values

terraform init
```

### Daily Workflow

```bash
cd environments/dev

# After any change:
terraform fmt -recursive          # fix formatting
tflint --recursive                # catch mistakes
terraform validate                # syntax check
terraform plan                    # see what will change

# When ready to apply to dev:
terraform plan -out=tf.plan
terraform apply tf.plan
terraform show                    # verify result
```

### Testing Individual Modules (No AWS Credentials Needed)

```bash
cd modules/{service-name}
terraform init
terraform test
```

### CI/CD Pipeline

| Event | Action |
|-------|--------|
| Pull Request opened/updated | Plan runs automatically, output posted as PR comment |
| Push to `main` | Plan runs again, output posted to Actions summary |
| Human triggers apply | Go to Actions → Terraform Apply → Run workflow → select env → type "apply" |
| `prod` apply triggered | Requires a second human to approve in GitHub Environments before it runs |

**`terraform apply` is always manually triggered — nothing ever applies automatically.**

### GitHub Actions Setup (One-Time)

1. Run the OIDC bootstrap module to create CI roles (see `iam-github-oidc/`)
2. Add these secrets to your GitHub repo (Settings → Secrets):
   - `AWS_PLAN_ROLE_ARN` — from OIDC bootstrap output
   - `AWS_APPLY_ROLE_ARN_DEV` — from OIDC bootstrap output
   - `AWS_APPLY_ROLE_ARN_PROD` — from OIDC bootstrap output
3. Add this variable (Settings → Variables):
   - `AWS_REGION` — e.g. `us-east-1`
4. Create GitHub Environments (Settings → Environments):
   - `dev` — no required reviewers (human confirmation comes from the workflow input)
   - `prod` — add required reviewers (second human must approve in GitHub UI before apply runs)
```

---

## Summary: What Must Be Generated in Phase 8

The skill must always generate these files as part of finalization:

| File | Purpose |
|------|---------|
| `.github/workflows/terraform-plan.yml` | Auto-plan on PRs and pushes to main |
| `.github/workflows/terraform-apply.yml` | Manual-trigger only; human selects env + types "apply" to confirm |
| `iam-github-oidc/main.tf` | Bootstrap OIDC role (run once manually) |
| `README.md` local dev section | Setup instructions for developers |
| `environments/*/provider.tf` | Profile-aware provider config |
