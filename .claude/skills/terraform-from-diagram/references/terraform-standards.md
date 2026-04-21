# Terraform Coding Standards

All generated Terraform code must follow these standards. Read this file fully before
writing any `.tf` files.

---

## File Structure Per Module

Every module contains exactly these 5 files:

```
modules/{service-name}/
├── main.tf          → resource definitions only
├── variables.tf     → all input variables with descriptions + validation
├── outputs.tf       → all output values
├── versions.tf      → terraform{} and required_providers{} blocks
└── tests/
    ├── main.tftest.hcl
    └── fixtures/
        └── test.tfvars
```

---

## versions.tf — Correct Pattern Per Module Type

**Child modules** (`modules/*/versions.tf`) — declare providers but NOT `required_version`:
```hcl
# Child module: required_providers only. Do NOT add required_version here.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

**Root module** (`environments/*/versions.tf`) — BOTH `required_version` AND providers:
```hcl
# Root module only: set required_version here, not in child modules.
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

**Why:** `required_version` in child modules causes confusing errors — a version that satisfies
the root can fail in a child. Only the root enforces the version constraint.

**`terraform.lock.hcl`** — Always commit this file to VCS. It locks provider checksums across
the team and prevents supply-chain attacks. Never add it to `.gitignore`.

- Pin minor version with `~>` (allows patch updates, blocks major/minor bumps)
- Match provider version to what's in the diagram requirements or default to latest stable

---

## variables.tf — Standards

```hcl
variable "project_name" {
  description = "Name of the project. Used in resource naming and tagging."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}[a-z0-9]$", var.project_name))
    error_message = "project_name must be 4-30 chars, lowercase alphanumeric and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "AWS region for resource deployment."
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Additional tags to apply to all resources."
  type        = map(string)
  default     = {}
}
```

**Rules:**
- Every variable MUST have a `description`
- Every variable MUST have a `type`
- Sensitive variables MUST have `sensitive = true`
- Add `validation` blocks for string variables with known valid values
- Never set defaults for required config (VPC IDs, passwords, etc.) — let Terraform error

---

## main.tf — Standards

```hcl
locals {
  # Compute derived names here, not inline in resources
  resource_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Module      = "{module-name}"
  })
}

resource "aws_example_resource" "main" {
  name = "${local.resource_prefix}-{service-name}"

  # ... resource-specific config ...

  tags = local.common_tags
}
```

**Rules:**
- Use `locals` for name construction — never inline string interpolation in resource blocks
- All taggable resources MUST get `tags = local.common_tags`
- One `resource "..." "main"` for the primary resource per module
- Secondary/supporting resources: `resource "..." "this_<purpose>"`  
- No hardcoded account IDs, region strings, or ARN suffixes — use `data` sources
- Use `data "aws_caller_identity" "current" {}` and `data "aws_region" "current" {}` for dynamic values

---

## outputs.tf — Standards

```hcl
output "id" {
  description = "The ID of the {resource}."
  value       = aws_example_resource.main.id
}

output "arn" {
  description = "The ARN of the {resource}."
  value       = aws_example_resource.main.arn
}

output "name" {
  description = "The name of the {resource}."
  value       = aws_example_resource.main.name
}
```

**Rules:**
- Always export `id`, `arn`, and `name` at minimum
- Export any value another module will need to reference
- Sensitive outputs (connection strings, etc.) must use `sensitive = true`
- Add `depends_on` in the calling module (not the child) when ordering matters

---

## Naming Conventions

| Resource | Pattern |
|---------|---------|
| Variables | `snake_case` |
| Resources | `snake_case` |
| Modules | `kebab-case` for directories, `snake_case` for module blocks |
| Outputs | `snake_case` |
| Locals | `snake_case` |
| Resource names (AWS) | `${var.project_name}-${var.environment}-{service}` |

For globally-unique resource names (S3 buckets, ECR repos) always append a `random_id` suffix
to prevent cross-account or cross-customer collisions:

```hcl
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "main" {
  bucket = "${local.resource_prefix}-assets-${random_id.bucket_suffix.hex}"
  # e.g. myproject-dev-assets-a1b2c3d4
}
```

---

## Provider Configuration (Root Module Only)

Every root environment module must have a provider block. Child modules never configure providers.

```hcl
# environments/dev/provider.tf  (or at top of main.tf)

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Multi-region resources (ACM for CloudFront, WAF global) need an aliased provider
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

Modules consuming the aliased provider declare it:
```hcl
# In the child module that needs a specific region:
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.0"
      configuration_aliases = [aws.us_east_1]
    }
  }
}
```

And it's passed from the root:
```hcl
module "acm_cert" {
  source = "../../modules/acm-certificate"
  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
}
```

---

## Lifecycle Blocks (Always Consider These)

```hcl
resource "aws_db_instance" "main" {
  # ... config ...

  lifecycle {
    # ALWAYS set on production databases, RDS clusters, Redis clusters:
    prevent_destroy = true

    # For resources that must be replaced (e.g. security group rule changes):
    create_before_destroy = true

    # For resources whose attributes are managed externally (e.g. ECS desired_count
    # managed by auto-scaler, AMI ID managed by CI/CD):
    ignore_changes = [
      engine_version,   # allow minor version auto-upgrades
    ]
  }
}
```

| Rule | When to use |
|------|------------|
| `prevent_destroy = true` | All prod databases, Redis clusters, S3 buckets with data |
| `create_before_destroy = true` | Security groups, ACM certs, anything causing a brief outage if deleted first |
| `ignore_changes = [...]` | ECS `desired_count` (managed by auto-scaler), Lambda `filename` (managed by CI/CD), RDS `engine_version` (auto-minor-upgrades) |

---

## Preconditions and Postconditions

Use these to catch misconfiguration early and make debugging faster:

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${local.resource_prefix}-db-subnet-group"
  subnet_ids = var.subnet_ids

  lifecycle {
    precondition {
      condition     = length(var.subnet_ids) >= 2
      error_message = "RDS requires at least 2 subnets in different AZs. Got ${length(var.subnet_ids)}."
    }
  }
}

resource "aws_db_instance" "main" {
  # ... config ...

  lifecycle {
    postcondition {
      condition     = self.endpoint != ""
      error_message = "RDS instance was created but endpoint is empty — check subnet group and VPC config."
    }
  }
}
```

---

## IAM Policy Pattern — Always Use `aws_iam_policy_document`

Never write IAM policies as raw JSON strings. Always use the data source — it's type-safe,
composable, and caught by `terraform validate`.

```hcl
# WRONG — raw JSON string, no validation, easy to break:
resource "aws_iam_role_policy" "bad" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "s3:GetObject"
      Resource = "arn:aws:s3:::my-bucket/*"
    }]
  })
}

# CORRECT — use the data source:
data "aws_iam_policy_document" "lambda_s3_read" {
  statement {
    sid    = "ReadFromAssetsBucket"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      var.assets_bucket_arn,
      "${var.assets_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name   = "${local.resource_prefix}-s3-read"
  role   = aws_iam_role.main.id
  policy = data.aws_iam_policy_document.lambda_s3_read.json
}
```

---

## Dynamic AZ Discovery

Never hardcode availability zone names — use a data source so configs are region-portable:

```hcl
data "aws_availability_zones" "available" {
  state = "available"

  # Exclude Local Zones (opt-in only AZs that often lack full service support):
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  azs             = slice(data.aws_availability_zones.available.names, 0, var.az_count)
  private_subnets = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i)]
  public_subnets  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 100)]
}
```

---

## `moved` Blocks — Safe Refactoring

When renaming a resource or moving it into a module, use `moved` to prevent destroy/recreate:

```hcl
# Renaming a resource:
moved {
  from = aws_s3_bucket.old_name
  to   = aws_s3_bucket.main
}

# Moving a resource into a module:
moved {
  from = aws_lambda_function.auth
  to   = module.lambda_auth.aws_lambda_function.main
}
```

Add moved blocks in the root or module where the change occurs. They can be removed after
the team has run `terraform apply` and state is updated.

---

```hcl
# environments/dev/main.tf

module "vpc" {
  source = "../../modules/networking-vpc"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  cidr_block   = var.vpc_cidr
  tags         = local.common_tags
}

module "rds_users" {
  source = "../../modules/database-rds-users"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  
  # Cross-module wiring — always use module outputs, never hardcode
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  tags = local.common_tags
}
```

---

## Security Rules (Always Enforce)

1. **S3 buckets**: Always add `aws_s3_bucket_public_access_block` with all `true` unless explicitly public
2. **Security groups**: No `0.0.0.0/0` on ingress unless it's a public-facing load balancer/gateway — add a comment if intentional
3. **RDS**: Always set `deletion_protection = true` in prod, `skip_final_snapshot = false` in prod
4. **Lambda**: Always set `reserved_concurrent_executions` (even if -1) and a log group with retention
5. **IAM roles**: Use least-privilege — never `"*"` actions without a comment justifying it
6. **Secrets**: Never store in `.tf` or `.tfvars` — reference `aws_secretsmanager_secret_version` or SSM Parameter Store
7. **KMS**: Encrypt RDS, S3, Lambda env vars, SQS, SNS where supported

---

## Testing Standards {#testing}

Every module's `tests/main.tftest.hcl` must follow this pattern:

```hcl
# tests/main.tftest.hcl

# Mock the provider — no real AWS credentials needed for unit tests
mock_provider "aws" {
  mock_resource "aws_example_resource" {
    defaults = {
      id  = "mock-id-12345"
      arn = "arn:aws:service:us-east-1:123456789012:resource/mock-id-12345"
    }
  }
}

# --- Test 1: Basic plan succeeds ---
run "plan_succeeds_with_valid_inputs" {
  command = plan

  variables {
    project_name = "test-project"
    environment  = "dev"
    region       = "us-east-1"
  }

  assert {
    condition     = aws_example_resource.main.name == "test-project-dev-{service-name}"
    error_message = "Resource name should follow naming convention."
  }
}

# --- Test 2: Validation rejects bad input ---
run "rejects_invalid_environment" {
  command = plan

  variables {
    project_name = "test-project"
    environment  = "production"  # invalid — should be "prod"
    region       = "us-east-1"
  }

  expect_failures = [var.environment]
}

# --- Test 3: Tags are applied ---
run "tags_are_applied" {
  command = plan

  variables {
    project_name = "test-project"
    environment  = "dev"
    region       = "us-east-1"
  }

  assert {
    condition     = aws_example_resource.main.tags["ManagedBy"] == "terraform"
    error_message = "ManagedBy tag must be 'terraform'."
  }

  assert {
    condition     = aws_example_resource.main.tags["Project"] == "test-project"
    error_message = "Project tag must match project_name variable."
  }
}
```

**Test file: `tests/fixtures/test.tfvars`**
```hcl
project_name = "test-project"
environment  = "dev"
region       = "us-east-1"
```

---

## Validation Commands

Run after every module is generated:

```bash
# From module directory:
terraform init -backend=false
terraform validate
terraform fmt -check -diff

# Run tests (no credentials needed with mock_provider):
terraform test

# From root environment:
terraform init -backend=false
terraform validate
terraform fmt -recursive   # run from project ROOT, no path argument
```

### Static Analysis (Always Run — Catches What validate/fmt Miss)

```bash
# tflint — catches AWS-specific mistakes (invalid instance types, deprecated args, etc.)
tflint --init
tflint --recursive

# checkov — security and compliance scanning (open security groups, unencrypted resources, etc.)
checkov -d . --framework terraform

# OR trivy (alternative to checkov):
trivy config .
```

Install:
```bash
brew install tflint          # or: curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
pip install checkov          # or: brew install checkov
```

Add a `.tflint.hcl` at the project root:
```hcl
plugin "aws" {
  enabled = true
  version = "0.32.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" { enabled = true }
rule "terraform_documented_variables" { enabled = true }
rule "terraform_documented_outputs" { enabled = true }
```

### Safe Apply Pattern

Never run `terraform apply` directly. Always plan first and save the plan:

```bash
# Plan and save (the saved plan is what gets applied — no drift between review and apply):
terraform plan -out=tf.plan

# Review the plan carefully, then apply exactly that plan:
terraform apply tf.plan

# After apply — verify state:
terraform show
terraform state list
```

---

## .gitignore (Generate This at Project Root)

```gitignore
# Local .terraform directory (downloaded providers/modules)
**/.terraform/*

# Lock file should be committed — do NOT ignore:
# .terraform.lock.hcl  ← NEVER gitignore this

# Terraform state files — NEVER commit state
*.tfstate
*.tfstate.*
*.tfstate.backup

# Saved plan files
*.plan
tf.plan

# Crash logs
crash.log
crash.*.log

# Sensitive variable files — real values, never commit
*.tfvars
!*.tfvars.example    # .example files ARE safe to commit

# Override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Generated files
.terraform.tfstate.lock.info
*.zip                # Lambda deployment packages
placeholder.zip
```

**Key rules:**
- `terraform.lock.hcl` — ALWAYS commit. It locks provider checksums.
- `terraform.tfvars` — NEVER commit. Use `terraform.tfvars.example` for the template.
- `.terraform/` — NEVER commit. Re-created by `terraform init`.
- `*.tfstate` — NEVER commit. Always use remote state (S3 + DynamoDB).

---

## Common Module Templates

### Lambda Function Module

Key resources to include:
- `aws_lambda_function.main`
- `aws_iam_role.lambda_execution`
- `aws_iam_role_policy_attachment.lambda_basic`
- `aws_cloudwatch_log_group.lambda` (with `retention_in_days`)
- `aws_lambda_permission.invoker` (if invoked by API Gateway / SNS / etc.)

Required outputs: `function_arn`, `function_name`, `invoke_arn`, `role_arn`

### RDS Module

Key resources to include:
- `aws_db_instance.main` (or `aws_rds_cluster` for Aurora)
- `aws_db_subnet_group.main`
- `aws_security_group.rds`
- `aws_security_group_rule.ingress_from_app`
- `random_password.master` (for initial password — stored in Secrets Manager)
- `aws_secretsmanager_secret.db_password`

Required outputs: `endpoint`, `port`, `db_name`, `secret_arn`

### S3 Bucket Module

Key resources to include:
- `aws_s3_bucket.main`
- `aws_s3_bucket_public_access_block.main`
- `aws_s3_bucket_versioning.main`
- `aws_s3_bucket_server_side_encryption_configuration.main`
- `aws_s3_bucket_lifecycle_configuration.main` (optional but recommended)

Required outputs: `bucket_id`, `bucket_arn`, `bucket_domain_name`

### SQS Queue Module

Key resources to include:
- `aws_sqs_queue.main`
- `aws_sqs_queue.dead_letter` (DLQ — always create)
- `aws_sqs_queue_redrive_policy.main`

Required outputs: `queue_url`, `queue_arn`, `dlq_url`, `dlq_arn`
