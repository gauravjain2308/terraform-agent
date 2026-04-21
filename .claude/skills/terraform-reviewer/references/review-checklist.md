# Terraform Review Checklist

Full checklist applied by the terraform-reviewer skill.
Each item maps to a finding severity: 🔴 CRITICAL | 🟡 WARNING | 🔵 INFO

---

## Structure & Standards

| # | Check | Severity |
|---|-------|---------|
| S1 | `required_version` present only in root module (environments/), NOT in child modules | 🟡 WARNING |
| S2 | `required_providers` present in every module's versions.tf | 🟡 WARNING |
| S3 | Provider version pinned with `~>` (not `>=` or exact) | 🔵 INFO |
| S4 | All resource names use `locals.resource_prefix` or `locals.common_tags` | 🟡 WARNING |
| S5 | No inline string interpolation inside resource blocks (use locals) | 🔵 INFO |
| S6 | Module directories use kebab-case | 🔵 INFO |
| S7 | Resource addresses use snake_case | 🔵 INFO |
| S8 | Primary resource in module named `.main` | 🔵 INFO |
| S9 | `data "aws_caller_identity"` and `data "aws_region"` used (no hardcoded values) | 🟡 WARNING |
| S10 | `lifecycle { prevent_destroy = true }` on prod databases and critical resources | 🔴 CRITICAL |
| S11 | `moved {}` blocks present if any resource addresses changed | 🟡 WARNING |
| S12 | `precondition` / `postcondition` blocks on critical resources | 🔵 INFO |

---

## Tagging

| # | Check | Severity |
|---|-------|---------|
| T1 | Every taggable resource has `tags = local.common_tags` | 🟡 WARNING |
| T2 | `local.common_tags` includes: Project, Environment, ManagedBy="terraform", Module | 🟡 WARNING |
| T3 | Provider-level `default_tags` set in environments/*/provider.tf | 🔵 INFO |

---

## Variables & Outputs

| # | Check | Severity |
|---|-------|---------|
| V1 | Every variable has `description` | 🟡 WARNING |
| V2 | Every variable has `type` | 🟡 WARNING |
| V3 | Sensitive variables have `sensitive = true` | 🔴 CRITICAL |
| V4 | No default set on required config (VPC IDs, DB names, usernames) | 🟡 WARNING |
| V5 | Validation blocks on string variables with known valid values | 🔵 INFO |
| V6 | Outputs export `id`, `arn`, `name` at minimum | 🟡 WARNING |
| V7 | Sensitive outputs (endpoints, connection strings) have `sensitive = true` | 🔴 CRITICAL |
| V8 | No hardcoded account IDs, region strings, or ARN fragments | 🔴 CRITICAL |

---

## Security

| # | Check | Severity |
|---|-------|---------|
| SEC1 | No `0.0.0.0/0` ingress on security groups (without explicit comment) | 🔴 CRITICAL |
| SEC2 | S3 bucket has `aws_s3_bucket_public_access_block` with all `true` | 🔴 CRITICAL |
| SEC3 | S3 bucket has server-side encryption configured | 🟡 WARNING |
| SEC4 | S3 bucket has versioning enabled | 🟡 WARNING |
| SEC5 | RDS `deletion_protection = true` (prod) | 🔴 CRITICAL |
| SEC6 | RDS `skip_final_snapshot = false` (prod) | 🔴 CRITICAL |
| SEC7 | RDS storage encrypted | 🟡 WARNING |
| SEC8 | RDS password stored in Secrets Manager (not in tfvars or code) | 🔴 CRITICAL |
| SEC9 | Lambda `reserved_concurrent_executions` set (-1 or positive value) | 🟡 WARNING |
| SEC10 | Lambda CloudWatch log group with `retention_in_days` | 🟡 WARNING |
| SEC11 | Lambda `tracing_config { mode = "Active" }` | 🔵 INFO |
| SEC12 | ElastiCache `at_rest_encryption_enabled = true` | 🟡 WARNING |
| SEC13 | ElastiCache `transit_encryption_enabled = true` | 🟡 WARNING |
| SEC14 | SQS queue encrypted | 🟡 WARNING |
| SEC15 | SNS topic encrypted | 🟡 WARNING |
| SEC16 | ECS task definition has `readonlyRootFilesystem = true` | 🔵 INFO |
| SEC17 | No real secrets in .tf files (look for patterns: password=, token=, key=) | 🔴 CRITICAL |
| SEC18 | `terraform.lock.hcl` present (provider checksum verification) | 🟡 WARNING |

---

## IAM Least Privilege

| # | Check | Severity |
|---|-------|---------|
| IAM1 | `aws_iam_policy_document` data source used (never `jsonencode()` or raw JSON strings) | 🟡 WARNING |
| IAM2 | No inline policy uses `"Resource": "*"` for S3, DynamoDB, SQS, SNS, Secrets Manager | 🔴 CRITICAL |
| IAM3 | S3 permissions scoped to specific bucket ARN | 🔴 CRITICAL |
| IAM4 | DynamoDB permissions scoped to specific table ARN | 🔴 CRITICAL |
| IAM5 | SQS permissions scoped to specific queue ARN | 🔴 CRITICAL |
| IAM6 | Secrets Manager permissions scoped to specific secret ARN pattern | 🔴 CRITICAL |
| IAM7 | No role has `AdministratorAccess` | 🔴 CRITICAL |
| IAM8 | No role has `PowerUserAccess` | 🟡 WARNING |
| IAM9 | Lambda execution role uses specific managed policies (not `*`) | 🟡 WARNING |
| IAM10 | ECS tasks have separate execution role and task role | 🟡 WARNING |
| IAM11 | Trust policies use exact service principals (not `"*"`) | 🔴 CRITICAL |
| IAM12 | IAM roles have `description` set | 🔵 INFO |
| IAM13 | IAM path consistent across roles | 🔵 INFO |
| IAM14 | Cross-service permissions match iam-model-review.md | 🟡 WARNING |

---

## Dependency Wiring

| # | Check | Severity |
|---|-------|---------|
| D1 | All outputs in dependency map are actually exported in outputs.tf | 🔴 CRITICAL |
| D2 | All cross-module inputs are declared as variables in consuming module | 🔴 CRITICAL |
| D3 | Root module uses `module.{name}.{output}` (never hardcoded values) | 🔴 CRITICAL |
| D4 | `depends_on` used only in root module, not child modules | 🔵 INFO |
| D5 | Module source paths are correct relative paths | 🟡 WARNING |
| D6 | All services in build plan have a module block in environments/*/main.tf | 🟡 WARNING |

---

## Testing

| # | Check | Severity |
|---|-------|---------|
| TST1 | `tests/main.tftest.hcl` exists in every module | 🟡 WARNING |
| TST2 | Tests use `mock_provider "aws"` (not real AWS calls) | 🟡 WARNING |
| TST3 | At least 3 test cases: valid inputs, invalid environment, tags applied | 🔵 INFO |
| TST4 | `tests/fixtures/test.tfvars` present | 🔵 INFO |
| TST5 | Test assertions check naming convention | 🔵 INFO |
| TST6 | Test assertions check tag values | 🔵 INFO |

---

## Spec Compliance

| # | Check | Severity |
|---|-------|---------|
| SP1 | Module names match Final Name column in services-review.md | 🔴 CRITICAL |
| SP2 | Wave dependencies match build-plan-review.md | 🔴 CRITICAL |
| SP3 | Instance classes/sizes match 03_inputs_wave_*.md | 🟡 WARNING |
| SP4 | IAM roles match iam-model-review.md Section 1 | 🟡 WARNING |
| SP5 | Inline policies match iam-model-review.md Section 2 | 🟡 WARNING |
| SP6 | Resource-based policies match iam-model-review.md Section 3 | 🟡 WARNING |
