# Inputs Template Guide

This guide explains how to generate the **Project Inputs Collection Template** — a single
pre-flight file that collects every value needed to run Terraform, organized by service.

The user fills this file in before any code generation starts. This eliminates mid-build
interruptions asking for sizes, ports, credentials, etc.

---

## When to Generate

After Review Gate 2 (build plan approved), generate `review/03_inputs_collection.md`
before scaffolding any files.

---

## How to Build the Inputs Template

For each confirmed service, look up its **required inputs table** below and emit the
corresponding section. Merge with any values already extracted from the diagram tooltips
or requirements doc (pre-fill those — don't make the user re-enter what you already know).

---

## Global Inputs (Always Include)

These appear at the top of every generated template, regardless of services:

```markdown
## 🌍 Global Configuration

| Input | Description | Allowed Values | Your Value |
|-------|-------------|----------------|------------|
| `project_name` | Used in all resource names & tags | lowercase, hyphens, 4-30 chars | __________ |
| `aws_region` | Primary deployment region | e.g. `us-east-1`, `eu-west-1` | __________ |
| `aws_secondary_region` | DR / replica region (if needed) | e.g. `us-west-2` | N/A or _____ |
| `environments` | Which envs to generate | `dev` / `dev,staging,prod` | __________ |
| `terraform_version` | Minimum Terraform version | e.g. `>= 1.6.0` | __________ |
| `aws_provider_version` | AWS provider pin | e.g. `~> 5.0` | __________ |
| `state_s3_bucket` | S3 bucket for Terraform state | existing bucket name | __________ |
| `state_dynamodb_table` | DynamoDB table for state locking | existing table name | __________ |
| `default_tags` | Tags applied to every resource | key=value pairs | __________ |
```

---

## Per-Service Input Tables

### VPC / Networking

```markdown
### 🌐 {service-name} — VPC & Networking

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `vpc_cidr` | VPC CIDR block | e.g. `10.0.0.0/16` | `10.0.0.0/16` | __________ |
| `public_subnet_cidrs` | Public subnet CIDRs (one per AZ) | e.g. `10.0.1.0/24,10.0.2.0/24` | — | __________ |
| `private_subnet_cidrs` | Private subnet CIDRs (one per AZ) | e.g. `10.0.10.0/24,10.0.11.0/24` | — | __________ |
| `availability_zones` | AZs to deploy into | e.g. `us-east-1a,us-east-1b` | 2 minimum | __________ |
| `enable_nat_gateway` | Enable NAT for private subnet egress | `true` / `false` | `true` | __________ |
| `single_nat_gateway` | Use one NAT (cheaper, less HA) | `true` / `false` | `false` (prod) | __________ |
| `enable_vpn_gateway` | Attach a VPN gateway | `true` / `false` | `false` | __________ |
| `enable_flow_logs` | Enable VPC flow logs | `true` / `false` | `true` | __________ |

**Prerequisites:**
- [ ] AWS account ID confirmed
- [ ] Region selected and has ≥ 2 AZs available
- [ ] CIDR range does not conflict with on-prem or other VPCs
```

---

### RDS (PostgreSQL / MySQL / Aurora)

```markdown
### 🗄️ {service-name} — RDS Database

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `db_engine` | Database engine | `postgres` / `mysql` / `aurora-postgresql` / `aurora-mysql` | `postgres` | __________ |
| `db_engine_version` | Engine version | e.g. `15.4`, `8.0.35` | Latest LTS | __________ |
| `db_instance_class` | Instance size | See instance table below | `db.t3.medium` (dev) | __________ |
| `db_allocated_storage_gb` | Initial storage in GB | `20` – `65536` | `100` | __________ |
| `db_max_allocated_storage_gb` | Max storage for autoscaling | > allocated_storage | `500` | __________ |
| `db_name` | Database/schema name | alphanumeric, underscores | __________ | __________ |
| `db_username` | Master username | alphanumeric | __________ | __________ |
| `db_port` | Listening port | `5432` (PG) / `3306` (MySQL) | engine default | __________ |
| `db_multi_az` | Enable Multi-AZ standby | `true` / `false` | `true` (prod) | __________ |
| `db_backup_retention_days` | Automated backup retention | `1`–`35` | `7` | __________ |
| `db_backup_window` | Daily backup window (UTC) | `hh:mm-hh:mm` | `03:00-04:00` | __________ |
| `db_maintenance_window` | Weekly maintenance window | `ddd:hh:mm-ddd:hh:mm` | `sun:04:00-sun:05:00` | __________ |
| `db_deletion_protection` | Prevent accidental deletion | `true` / `false` | `true` (prod) | __________ |
| `db_skip_final_snapshot` | Skip snapshot on destroy | `true` / `false` | `false` (prod) | __________ |
| `db_storage_encrypted` | Encrypt storage at rest | `true` / `false` | `true` | __________ |
| `db_parameter_group_family` | Parameter group family | e.g. `postgres15` | matches engine | __________ |
| `db_allowed_cidr_blocks` | CIDRs allowed to connect | IP ranges or SG reference | app SG only | __________ |

**RDS Instance Classes Quick Reference:**
| Class | vCPU | RAM | Use case |
|-------|------|-----|---------|
| `db.t3.micro` | 2 | 1 GB | Dev/test only |
| `db.t3.medium` | 2 | 4 GB | Small dev |
| `db.t3.large` | 2 | 8 GB | Dev/staging |
| `db.r6g.large` | 2 | 16 GB | Small prod |
| `db.r6g.xlarge` | 4 | 32 GB | Medium prod |
| `db.r6g.2xlarge` | 8 | 64 GB | Large prod |
| `db.r6g.4xlarge` | 16 | 128 GB | High-traffic prod |

**Prerequisites:**
- [ ] VPC and private subnets created first (Wave 1)
- [ ] KMS key ARN available if using customer-managed encryption
- [ ] Secrets Manager or SSM path chosen for password storage
- [ ] DB password will be **auto-generated** — do not set manually
```

---

### Lambda Function

```markdown
### ⚡ {service-name} — Lambda Function

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `lambda_runtime` | Runtime identifier | `python3.12` / `nodejs20.x` / `java21` / `go1.x` / `dotnet8` | `python3.12` | __________ |
| `lambda_handler` | Entry point (file.function) | e.g. `handler.lambda_handler` | — | __________ |
| `lambda_memory_mb` | Memory allocation | `128`–`10240` MB (in 1 MB steps) | `256` | __________ |
| `lambda_timeout_seconds` | Max execution time | `1`–`900` seconds | `30` | __________ |
| `lambda_reserved_concurrency` | Max concurrent executions | `-1` (no limit) or `0`–`1000` | `-1` | __________ |
| `lambda_architecture` | CPU architecture | `x86_64` / `arm64` | `arm64` (cheaper) | __________ |
| `lambda_log_retention_days` | CloudWatch log retention | `1`,`3`,`7`,`14`,`30`,`60`,`90`,`180`,`365` | `14` | __________ |
| `lambda_ephemeral_storage_mb` | /tmp storage | `512`–`10240` MB | `512` | __________ |
| `lambda_layers` | Lambda layer ARNs | list of ARNs | `[]` | __________ |
| `lambda_env_vars` | Environment variables | map of key=value | __________ | __________ |
| `lambda_vpc_enabled` | Run inside VPC | `true` / `false` | `true` if needs DB | __________ |
| `lambda_subnet_ids` | Subnets for VPC-attached Lambda | private subnet IDs | — | __________ |
| `lambda_security_group_ids` | SGs for VPC-attached Lambda | security group IDs | — | __________ |

**Lambda Memory / Performance Guide:**
| Memory | Relative vCPU | Best for |
|--------|---------------|---------|
| `128 MB` | Minimal | Lightweight triggers, S3 events |
| `256 MB` | Low | Simple APIs, CRUD |
| `512 MB` | 0.5 vCPU | Standard API handlers |
| `1024 MB` | 1 vCPU | Data processing, image resize |
| `2048 MB` | 2 vCPU | ML inference, heavy compute |
| `3008 MB` | 3 vCPU | Max before dedicated vCPU tier |
| `10240 MB` | 6 vCPU | CPU-bound workloads |

**Prerequisites:**
- [ ] IAM execution role created first (Wave 1)
- [ ] VPC + subnets created if `lambda_vpc_enabled = true`
- [ ] Downstream service endpoints known (DB host, Redis host, etc.)
- [ ] Deployment package / container image strategy decided
```

---

### API Gateway (REST / HTTP)

```markdown
### 🚪 {service-name} — API Gateway

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `apigw_type` | Gateway type | `REST` / `HTTP` / `WebSocket` | `HTTP` (v2, cheaper) | __________ |
| `apigw_stage_name` | Deployment stage name | e.g. `v1`, `api`, `$default` | `$default` (HTTP) | __________ |
| `apigw_throttle_rate` | Requests per second (steady) | integer | `1000` | __________ |
| `apigw_throttle_burst` | Requests per second (burst) | integer | `2000` | __________ |
| `apigw_cors_origins` | Allowed CORS origins | `*` or list of origins | specific domains | __________ |
| `apigw_cors_methods` | Allowed HTTP methods | e.g. `GET,POST,PUT,DELETE` | — | __________ |
| `apigw_access_log_retention` | Access log retention (days) | same as Lambda log values | `30` | __________ |
| `apigw_domain_name` | Custom domain name | FQDN or empty | optional | __________ |
| `apigw_certificate_arn` | ACM certificate ARN for custom domain | ARN or empty | required if domain set | __________ |
| `apigw_authorizer_type` | Auth mechanism | `NONE` / `JWT` / `AWS_IAM` / `COGNITO` / `LAMBDA` | `JWT` | __________ |
| `apigw_jwt_issuer` | JWT issuer URL (if JWT auth) | HTTPS URL | Cognito/Auth0 URL | __________ |
| `apigw_jwt_audience` | JWT audience (if JWT auth) | string | client app ID | __________ |

**Prerequisites:**
- [ ] Lambda function(s) built and `invoke_arn` outputs available
- [ ] ACM certificate created in correct region (us-east-1 for CloudFront, same region for API GW)
- [ ] Route53 hosted zone ID known (if using custom domain)
- [ ] Cognito User Pool created if using Cognito authorizer
```

---

### ElastiCache (Redis / Memcached)

```markdown
### ⚡ {service-name} — ElastiCache

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `cache_engine` | Cache engine | `redis` / `memcached` | `redis` | __________ |
| `cache_engine_version` | Engine version | e.g. `7.1`, `1.6.17` | Latest stable | __________ |
| `cache_node_type` | Node instance type | See node table below | `cache.t3.medium` | __________ |
| `cache_num_nodes` | Number of nodes (Memcached) or replicas | `1`–`6` | `2` (prod) | __________ |
| `cache_num_shards` | Number of shards (Redis cluster mode) | `1`–`500` | `1` | __________ |
| `cache_port` | Port | `6379` (Redis) / `11211` (Memcached) | engine default | __________ |
| `cache_at_rest_encryption` | Encrypt data at rest (Redis) | `true` / `false` | `true` | __________ |
| `cache_in_transit_encryption` | TLS in transit (Redis) | `true` / `false` | `true` | __________ |
| `cache_auth_token` | Redis AUTH token | 16–128 chars, stored in SSM | — | __________ |
| `cache_maintenance_window` | Weekly maintenance window | `ddd:hh:mm-ddd:hh:mm` | `sun:05:00-sun:06:00` | __________ |
| `cache_snapshot_retention` | Backup retention (Redis, days) | `0`–`35` | `1` | __________ |
| `cache_automatic_failover` | Auto-failover for Redis | `true` / `false` | `true` (prod) | __________ |

**ElastiCache Node Types:**
| Type | vCPU | RAM | Network | Use case |
|------|------|-----|---------|---------|
| `cache.t3.micro` | 2 | 0.5 GB | Low | Dev only |
| `cache.t3.medium` | 2 | 3.09 GB | Medium | Dev/staging |
| `cache.r6g.large` | 2 | 13.07 GB | Up to 10 Gbps | Prod |
| `cache.r6g.xlarge` | 4 | 26.32 GB | Up to 10 Gbps | High traffic |
| `cache.r6g.2xlarge` | 8 | 52.82 GB | Up to 10 Gbps | Very high traffic |

**Prerequisites:**
- [ ] VPC and private subnets available
- [ ] Security group that allows app layer ingress on cache port
- [ ] AUTH token stored in SSM Parameter Store (do not put in tfvars)
```

---

### S3 Bucket

```markdown
### 🪣 {service-name} — S3 Bucket

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `s3_bucket_purpose` | Bucket purpose (used in name suffix) | e.g. `assets`, `logs`, `data` | — | __________ |
| `s3_versioning_enabled` | Enable object versioning | `true` / `false` | `true` | __________ |
| `s3_force_destroy` | Allow destroy even if not empty | `true` / `false` | `false` (prod) | __________ |
| `s3_lifecycle_noncurrent_days` | Delete old versions after N days | integer | `30` | __________ |
| `s3_lifecycle_expiration_days` | Expire current objects after N days | integer or `0` (disabled) | `0` | __________ |
| `s3_cors_allowed_origins` | CORS origins (if serving to browser) | list of origins | `[]` | __________ |
| `s3_intelligent_tiering` | Enable Intelligent-Tiering storage class | `true` / `false` | `false` | __________ |
| `s3_replication_region` | Cross-region replication target | region or empty | — | __________ |
| `s3_access_logging_bucket` | Bucket to receive access logs | bucket name or empty | — | __________ |
| `s3_kms_key_arn` | KMS key for SSE-KMS (blank = SSE-S3) | ARN or empty | SSE-S3 default | __________ |

**Prerequisites:**
- [ ] Bucket name globally unique (will be `{project}-{env}-{purpose}-{account_id}`)
- [ ] KMS key created if using SSE-KMS
- [ ] Replication role created if cross-region replication enabled
```

---

### SQS Queue

```markdown
### 📬 {service-name} — SQS Queue

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `sqs_queue_type` | Queue type | `standard` / `fifo` | `standard` | __________ |
| `sqs_visibility_timeout_seconds` | Message lock duration | `0`–`43200` | `30` (match Lambda timeout) | __________ |
| `sqs_message_retention_seconds` | Max message age | `60`–`1209600` (14 days) | `86400` (1 day) | __________ |
| `sqs_delay_seconds` | Delivery delay | `0`–`900` | `0` | __________ |
| `sqs_max_message_size_bytes` | Max message size | `1024`–`262144` | `262144` (256 KB) | __________ |
| `sqs_receive_wait_time_seconds` | Long polling duration | `0`–`20` | `20` (long poll) | __________ |
| `sqs_dlq_max_receive_count` | Retries before DLQ | `1`–`1000` | `3` | __________ |
| `sqs_kms_master_key_id` | KMS key for encryption | key ID or alias | `alias/aws/sqs` | __________ |
| `sqs_fifo_content_dedup` | Content-based deduplication (FIFO) | `true` / `false` | `false` | __________ |

**Prerequisites:**
- [ ] DLQ is always auto-created alongside main queue — no separate config needed
- [ ] Consumer Lambda / ECS service defined before enabling event source mapping
```

---

### ECS Service / Fargate

```markdown
### 🐳 {service-name} — ECS Fargate Service

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `ecs_container_image` | Container image URI | ECR URI or public image | — | __________ |
| `ecs_container_port` | Port exposed by container | `1`–`65535` | `8080` | __________ |
| `ecs_cpu` | vCPU units (1 vCPU = 1024) | `256`,`512`,`1024`,`2048`,`4096`,`8192`,`16384` | `512` | __________ |
| `ecs_memory_mb` | Memory in MB | must be valid for CPU (see table) | `1024` | __________ |
| `ecs_desired_count` | Initial task count | integer | `2` | __________ |
| `ecs_min_capacity` | Auto-scaling minimum | integer | `1` | __________ |
| `ecs_max_capacity` | Auto-scaling maximum | integer | `10` | __________ |
| `ecs_cpu_scale_target` | CPU % to trigger scale-out | `0`–`100` | `70` | __________ |
| `ecs_health_check_path` | ALB health check endpoint | URL path | `/health` | __________ |
| `ecs_health_check_interval` | Health check frequency (seconds) | `5`–`300` | `30` | __________ |
| `ecs_log_retention_days` | CloudWatch log retention | same as Lambda values | `14` | __________ |
| `ecs_assign_public_ip` | Assign public IP to tasks | `true` / `false` | `false` | __________ |

**Fargate CPU / Memory Valid Combinations:**
| CPU (units) | Valid Memory (MB) |
|-------------|------------------|
| `256` | 512, 1024, 2048 |
| `512` | 1024–4096 (in 1024 steps) |
| `1024` | 2048–8192 (in 1024 steps) |
| `2048` | 4096–16384 (in 1024 steps) |
| `4096` | 8192–30720 (in 1024 steps) |

**Prerequisites:**
- [ ] ECR repository created and image pushed
- [ ] ALB / target group created in same VPC
- [ ] ECS task execution role created (Wave 1 IAM)
- [ ] Secrets in Secrets Manager for env var injection
```

---

### IAM Base Roles

```markdown
### 🔑 {service-name} — IAM Base Roles

| Input | Description | Allowed Values | Recommended | Your Value |
|-------|-------------|----------------|-------------|------------|
| `iam_permission_boundary_arn` | Permission boundary for all roles | ARN or empty | org policy ARN | __________ |
| `iam_path` | IAM path prefix for roles/policies | e.g. `/app/` | `/` | __________ |
| `iam_enable_lambda_vpc_access` | Add VPC access policy to Lambda role | `true` / `false` | `true` | __________ |
| `iam_enable_xray` | Allow X-Ray tracing | `true` / `false` | `true` | __________ |
| `iam_additional_policies` | Extra policy ARNs to attach | list of ARNs | `[]` | __________ |

**Prerequisites:**
- [ ] AWS Organizations SCP / permission boundary ARN if required by org policy
- [ ] No secrets or account IDs needed — roles are created fresh
```

---

## How to Generate the Template File

When generating `review/03_inputs_collection.md`:

1. Start with the **Global Configuration** section (always)
2. For each confirmed service (in wave order), add its section from above
3. **Pre-fill** any values already known from diagram tooltips or requirements doc
4. **Mark pre-filled values** with `← from diagram` or `← from requirements` so user knows what was auto-detected
5. Mark mandatory fields with ⚠️ if they have no sensible default
6. Group environment-specific differences (dev vs prod) inline using the format:
   ```
   `true` (prod) / `false` (dev)
   ```
7. Add a **Prerequisites Checklist** section at the top summarising all cross-service deps

---

## Prerequisites Summary Block (Always at Top of Template)

```markdown
## ✅ Prerequisites Checklist

Before filling in the values below, confirm these are in place:

### AWS Account & Access
- [ ] AWS account ID: __________________
- [ ] IAM user/role with sufficient permissions to create all resources
- [ ] AWS CLI configured with correct profile: `aws sts get-caller-identity`
- [ ] Terraform installed: `terraform version` (need >= 1.6.0)

### Pre-Existing Infrastructure (if any)
- [ ] S3 bucket for Terraform state exists: __________________
- [ ] DynamoDB table for state lock exists: __________________
- [ ] VPC already exists? (if yes, provide VPC ID): __________________
- [ ] ACM certificate exists? (if yes, provide ARN): __________________
- [ ] Route53 hosted zone ID: __________________

### Secrets — DO NOT put in this file
The following must be stored in AWS Secrets Manager or SSM Parameter Store:
- [ ] Database master password → path: /project/env/db/password
- [ ] Redis AUTH token → path: /project/env/cache/auth-token
- [ ] API keys / third-party credentials → path: /project/env/...

### Container Images (if ECS/Lambda containers)
- [ ] ECR repository created
- [ ] Image built and pushed to ECR
- [ ] Image URI: __________________
```
