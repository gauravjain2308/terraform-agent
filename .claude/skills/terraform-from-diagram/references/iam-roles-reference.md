# IAM Roles & Policies Reference

This file defines all IAM roles and policies required per service type.
The skill reads this when generating `agent/review/iam-model-review.md` after Gate 2.

---

## IAM Table Format

Each service gets a row in the IAM review table with these columns:

| Column | Description |
|--------|-------------|
| Service | Terraform module name |
| Role Name | Terraform resource name for the role |
| AWS Role ARN Pattern | Naming convention used |
| Trust Policy | Which AWS service can assume this role |
| Managed Policies | AWS-managed policies attached |
| Inline Policies | Custom policy statements needed |
| Outputs | What the module exports for other services to consume |
| Created By | Which module creates this role (some roles are shared) |

---

## Per-Service IAM Requirements

### Lambda Function

**Role:** `aws_iam_role.lambda_execution`

| Attribute | Value |
|-----------|-------|
| Trust policy principal | `lambda.amazonaws.com` |
| Managed — basic execution | `AWSLambdaBasicExecutionRole` |
| Managed — VPC access (if VPC) | `AWSLambdaVPCAccessExecutionRole` |
| Managed — X-Ray | `AWSXRayDaemonWriteAccess` |
| Inline — Secrets Manager read | `secretsmanager:GetSecretValue` on specific secret ARNs |
| Inline — SSM read (if used) | `ssm:GetParameter`, `ssm:GetParametersByPath` |
| Inline — SQS consume (if consumer) | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` |
| Inline — S3 read/write (if needed) | `s3:GetObject`, `s3:PutObject` on specific bucket ARNs |
| Inline — DynamoDB (if needed) | `dynamodb:GetItem`, `dynamodb:PutItem`, etc. on specific table ARNs |
| Inline — invoke other Lambda | `lambda:InvokeFunction` on specific function ARNs |
| Output | `execution_role_arn`, `execution_role_name` |
| Created by | `iam-base-roles` module (shared) OR per-Lambda module |

**Least-privilege rules:**
- Never use `"Resource": "*"` for data service actions
- Always scope to specific ARN: `arn:aws:s3:::${var.bucket_name}/*`
- Never attach `AdministratorAccess` or `PowerUserAccess`

---

### RDS (PostgreSQL / MySQL / Aurora)

**No IAM role required for the database itself.**

However, the application connecting to RDS needs:

| Attribute | Value |
|-----------|-------|
| What needs the policy | Lambda / ECS task role that connects to RDS |
| Inline — Secrets Manager | `secretsmanager:GetSecretValue` on the RDS password secret ARN |
| Inline — RDS IAM auth (optional) | `rds-db:connect` on `arn:aws:rds-db:{region}:{account}:dbuser/{resource-id}/{db-user}` |
| Enhanced monitoring role | `aws_iam_role.rds_monitoring` with trust `monitoring.rds.amazonaws.com` |
| Managed — enhanced monitoring | `AmazonRDSEnhancedMonitoringRole` |
| Output | `monitoring_role_arn`, `db_secret_arn` |
| Created by | `rds-users` module creates the monitoring role |

---

### ECS Fargate

**Two roles required:**

**Task Execution Role** — used by ECS control plane to pull image and read secrets:

| Attribute | Value |
|-----------|-------|
| Trust policy | `ecs-tasks.amazonaws.com` |
| Managed | `AmazonECSTaskExecutionRolePolicy` |
| Inline — Secrets Manager pull | `secretsmanager:GetSecretValue` on task secrets |
| Inline — ECR pull (if private) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
| Output | `task_execution_role_arn` |

**Task Role** — used by the container itself at runtime:

| Attribute | Value |
|-----------|-------|
| Trust policy | `ecs-tasks.amazonaws.com` |
| Inline — application permissions | S3, DynamoDB, SQS, SNS, Secrets Manager per app needs |
| Output | `task_role_arn` |
| Created by | `iam-base-roles` module + per-service inline policy |

---

### API Gateway

**No IAM execution role required** for HTTP/REST API itself.

However:

| Attribute | Value |
|-----------|-------|
| CloudWatch logging role | `aws_iam_role.apigw_cloudwatch` with trust `apigateway.amazonaws.com` |
| Managed — logging | `AmazonAPIGatewayPushToCloudWatchLogs` |
| Account-level setting | `aws_api_gateway_account` must reference this role |
| Output | `cloudwatch_role_arn` |
| Created by | `api-gateway` module |

For **Lambda authorizer** (if used):
| Attribute | Value |
|-----------|-------|
| Inline | `lambda:InvokeFunction` on authorizer Lambda ARN |
| Applied to | API Gateway resource-based policy on Lambda |

---

### SQS Queue

**No IAM role required** for SQS itself (queue uses resource-based policies).

The queue needs:

| Attribute | Value |
|-----------|-------|
| Queue policy — sender | Allow producer Lambda/ECS role: `sqs:SendMessage` |
| Queue policy — consumer | Allow consumer Lambda/ECS role: `sqs:ReceiveMessage`, `sqs:DeleteMessage` |
| DLQ policy | Same consumer role: `sqs:SendMessage` to DLQ |
| KMS key policy (if encrypted) | Allow SQS service to use key |
| Output | `queue_arn`, `queue_url`, `dlq_arn` |
| Created by | `sqs-{name}` module — queue policy inline |

---

### S3 Bucket

**No IAM role required** for S3 itself (uses bucket + IAM policies).

| Attribute | Value |
|-----------|-------|
| Bucket policy (if cross-account) | `aws_s3_bucket_policy` resource |
| Replication role (if enabled) | Trust: `s3.amazonaws.com`, Inline: `s3:ReplicateObject` |
| Access from Lambda/ECS | Inline on their task/execution role |
| Output | `bucket_arn`, `bucket_id` |
| Created by | `s3-{name}` module |

---

### ElastiCache Redis

**No IAM role required.** Uses auth token (password) stored in Secrets Manager.

| Attribute | Value |
|-----------|-------|
| Access control | Redis AUTH token in Secrets Manager |
| Application access | Lambda/ECS role needs `secretsmanager:GetSecretValue` on auth token secret |
| Output | `redis_endpoint`, `redis_port`, `auth_token_secret_arn` |

---

### SNS Topic

**No IAM role required.** Uses resource-based policy.

| Attribute | Value |
|-----------|-------|
| Topic policy — publish | Allow publisher Lambda/ECS role: `sns:Publish` |
| Topic policy — subscribe | Allow subscriber: `sns:Subscribe` |
| Delivery to SQS | Needs SQS queue policy to allow SNS delivery |
| Delivery to Lambda | Lambda permission resource: `aws_lambda_permission` |
| Output | `topic_arn` |

---

### IAM Base Roles Module

This is a special Wave 1 module that creates shared roles consumed by later waves.

**Always include in Wave 1 when Lambda or ECS services are present.**

| Role | Trust | Managed Policies | Outputs |
|------|-------|-----------------|---------|
| `lambda_execution_role` | `lambda.amazonaws.com` | `AWSLambdaBasicExecutionRole` | `lambda_execution_role_arn`, `lambda_execution_role_name` |
| `ecs_task_execution_role` | `ecs-tasks.amazonaws.com` | `AmazonECSTaskExecutionRolePolicy` | `ecs_execution_role_arn` |
| `ecs_task_role` | `ecs-tasks.amazonaws.com` | none (inline per service added later) | `ecs_task_role_arn`, `ecs_task_role_name` |
| `rds_monitoring_role` | `monitoring.rds.amazonaws.com` | `AmazonRDSEnhancedMonitoringRole` | `rds_monitoring_role_arn` |
| `apigw_cloudwatch_role` | `apigateway.amazonaws.com` | `AmazonAPIGatewayPushToCloudWatchLogs` | `apigw_cloudwatch_role_arn` |

---

### GitHub Actions OIDC Roles (iam-github-oidc module)

| Role | Trust Condition | Permissions | Used by |
|------|----------------|-------------|---------|
| `github_actions_plan` | `token.actions.githubusercontent.com:sub` matches repo | Read-only: `sts:AssumeRoleWithWebIdentity` + read perms | terraform-plan.yml |
| `github_actions_apply_dev` | same repo + environment:dev | Full apply perms on dev resources | terraform-apply.yml (dev) |
| `github_actions_apply_prod` | same repo + environment:prod | Full apply perms on prod resources | terraform-apply.yml (prod) |

---

## IAM Least-Privilege Checklist

Apply this to every inline policy generated:

- [ ] Resource ARN is specific — never `*` for data services
- [ ] Actions list is minimal — only what the service actually calls
- [ ] No `iam:*`, `sts:AssumeRole` unless explicitly required
- [ ] No `s3:*` — list only needed actions
- [ ] Condition blocks used where possible (e.g. restrict by VPC, tag, MFA)
- [ ] Permission boundary attached if required by org policy
- [ ] `description` set on every policy and role
- [ ] `path` set consistently (e.g. `/app/`)

---

## IAM Review File Format

The generated `agent/review/iam-model-review.md` covers **all waves in one file** and has five sections:

### Section A — Header
```
# IAM Review — {project_name}
STATUS: PENDING
Waves: {n} | Services: {n} | Roles: {n} | Inline policies: {n}
```

### Section B — Roles Summary (all waves)
```markdown
## Roles Summary — All Waves

| Wave | Module | Role Resource Name | AWS Role Name (Naming Convention) | Trust Principal | Managed Policies | Outputs Exported | Build Status |
|------|--------|--------------------|----------------------------------|-----------------|-----------------|-----------------|--------------|
| 1 | iam-base-roles | `lambda_execution_role` | `{project}-lambda-execution` | lambda.amazonaws.com | AWSLambdaBasicExecutionRole | lambda_execution_role_arn | ⏳ pending |
```

### Section C — Inline Policies (all services)
```markdown
## Inline Policies — All Services

| Wave | Consumer Service | Needs Access To | IAM Actions | Resource Scope | Attached To Role | Notes |
|------|-----------------|----------------|-------------|---------------|-----------------|-------|
| 2 | lambda-auth | rds-users secret | secretsmanager:GetSecretValue | arn:aws:secretsmanager:{region}:{account}:secret:{project}/rds-users/* | lambda_execution_role | ← fill account ID |
```

### Section D — Resource Policies (queues / buckets / topics)
```markdown
## Resource Policies — Queues / Buckets / Topics

| Service | Resource Type | Policy Statement | Principal | Actions | Condition |
|---------|--------------|-----------------|-----------|---------|-----------|
| sqs-orders | SQS Queue | Allow producer | {lambda-arn} | sqs:SendMessage | — |
```
Omit this section if no SQS/SNS/S3 resource policies are needed.

### Section E — Configuration & Checklist
```markdown
## IAM Configuration

| Setting | Value |
|---------|-------|
| IAM path | `/app/` |
| Permission boundary ARN | `none` |

## Pre-lock Checklist
- [ ] No bare * resource scopes on data services
- [ ] No AdministratorAccess / PowerUserAccess
- [ ] Every Secrets Manager / SSM consumer has kms:Decrypt scoped with kms:ViaService
- [ ] All ← placeholders replaced
```

This file is used by `/ServiceCodeWriter` to determine which roles to reference, which inline policies to attach, and which resource policies to create per service module.
