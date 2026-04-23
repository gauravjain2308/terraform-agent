# Bootstrap Guide — State Backend S3 Bucket

Terraform's remote backend requires the S3 bucket to **already exist** before `terraform init`
can connect to it. Terraform cannot create its own state storage — this is the bootstrap
chicken-and-egg problem. The `state-bootstrap/` module solves it.

---

## Why Variables Don't Work in backend.tf

Terraform backend blocks are evaluated before the provider and variable system initialises.
You **cannot** write `bucket = var.state_bucket` — it will error. All backend values must be
literal strings.

---

## Option A — Terraform Bootstrap Module (Recommended)

Generate a `state-bootstrap/` directory at the project root. This is a separate root module
with a **local backend** (its own state is stored locally — no chicken-and-egg). The user runs
it once before anything else.

### Directory layout

```
state-bootstrap/
├── main.tf       ← S3 bucket + versioning + encryption + public access block
├── variables.tf  ← bucket_name, region
└── versions.tf   ← terraform { required_version = ">= 1.10" }
```

### `state-bootstrap/versions.tf`

```hcl
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### `state-bootstrap/variables.tf`

```hcl
variable "bucket_name" {
  description = "Name of the S3 bucket that will store Terraform state. Must be globally unique."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "S3 bucket names must be 3-63 chars, lowercase letters, numbers, and hyphens."
  }
}

variable "region" {
  description = "AWS region where the state bucket will be created."
  type        = string
  default     = "us-east-1"
}
```

### `state-bootstrap/main.tf`

```hcl
provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "state" {
  bucket = var.bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

output "bucket_name" {
  description = "The name of the state bucket to put in backend.tf."
  value       = aws_s3_bucket.state.bucket
}
```

### Run order

```bash
# 1. Bootstrap the state bucket (run once, ever)
cd state-bootstrap
terraform init          # uses local backend — no bucket needed
terraform apply -var="bucket_name={project_name}-tf-state-use1"

# 2. Now init the real environment
cd ../environments/dev
terraform init          # S3 bucket now exists — succeeds

# 3. Normal workflow
terraform plan -out=tf.plan
terraform apply tf.plan
```

---

## Option B — AWS CLI Fallback

Use this when Terraform is not yet installed or for a quick manual bootstrap.
Replace `{bucket_name}` with your actual bucket name.

```bash
# Create bucket (us-east-1 does NOT use --create-bucket-configuration)
aws s3api create-bucket \
  --bucket {bucket_name} \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket {bucket_name} \
  --versioning-configuration Status=Enabled

# Enable SSE-S3 encryption
aws s3api put-bucket-encryption \
  --bucket {bucket_name} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
    }]
  }'

# Block all public access
aws s3api put-public-access-block \
  --bucket {bucket_name} \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

> For regions other than us-east-1, add `--create-bucket-configuration LocationConstraint={region}`
> to the `create-bucket` command.

---

## Prod State Bucket

If you have a `prod` environment with a separate backend, bootstrap its bucket the same way —
either a second `terraform apply` with a different `bucket_name`, or a second AWS CLI run.

A single bucket can serve both environments using different `key` paths:
```
{project_name}/dev/terraform.tfstate
{project_name}/prod/terraform.tfstate
```

Or use two buckets for stricter environment isolation (recommended for regulated workloads).

---

## When to Load This Guide

Load `bootstrap-guide.md` during:
- **Phase 6 (Scaffold)** — when generating the `state-bootstrap/` module files
- **Phase 8 (Finalize)** — when writing the "Next steps" section in the final summary
