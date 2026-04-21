# /ServicesRefiner — Generate Service Review File
Generate agent/review/services-review.md pre-filled from the diagram.
User edits the file directly in VS Code, then runs /ServicesRefinerConfirm.

## Step 1 — Load state

Read `.claude/memory/tf-state.json`. If missing:
```
❌ No project found. Run /Diagram2Services and attach your .drawio file.
```
Show banner: `📂 {project_name}  |  Phase 1 — Services Review`

## Step 2 — Create agent/review/ directory if it does not exist

## Step 3 — Generate and write agent/review/services-review.md

Write the complete file now. Pre-fill every field from the diagram data.
Show all available options as comments so the user knows exactly what to type.

For the **IAM Roles Required per Service** section: derive the required roles for each detected service from its type using standard AWS IAM patterns (Lambda → execution role; ECS Fargate → task execution + task roles; API Gateway → CloudWatch logging role; RDS → monitoring role; S3/SQS/SNS/ElastiCache → no role, policy only). Pre-fill the table with one row per role per service — role name, trust principal, purpose, and wave estimate.

File format:

```markdown
# Services Review
# Edit this file in VS Code, then run /ServicesRefinerConfirm to lock it in.
# Run /ServicesRefiner again at any time to regenerate with latest diagram data.
#
# Project: {project_name}
# Generated: {timestamp}
# Diagram: {filename}
# ─────────────────────────────────────────────────────────────────────

---

## Instructions
1. Review every row in the Services table below
2. Edit the "Final Name" column — this becomes the Terraform module folder name
3. Edit the "Type" column if any service was misidentified
4. Fill in "Project Config" at the bottom
5. Answer every question in the Ambiguities section
6. Run /ServicesRefinerConfirm when done

---

## Services Detected from Diagram

<!-- 
NAMING RULES:
  - lowercase letters, numbers, hyphens only
  - no underscores, no spaces, no uppercase
  - max 30 characters
  - these names become: terraform/modules/{final-name}/
  - they CANNOT be changed after /ServicesRefinerConfirm
-->

| # | Diagram Label | Final Name ← EDIT THIS | Type ← EDIT IF WRONG | Cloud | Confidence | Notes |
|---|--------------|------------------------|---------------------|-------|-----------|-------|
| 1 | {label}      | {suggested-name}        | {detected-type}      | AWS   | HIGH      | {notes} |
| 2 | {label}      | {suggested-name}        | {detected-type}      | AWS   | HIGH      | |
| 3 | {label}      | {suggested-name}        | {detected-type}      | AWS   | MEDIUM ⚠️  | Verify type |
| 4 | {label}      | {suggested-name}        | {detected-type}      | AWS   | LOW ⚠️    | Check this one |

<!--
AVAILABLE SERVICE TYPES (copy exact spelling into Type column):
  Networking:   VPC  |  Subnet  |  Security Group  |  NAT Gateway  |  Route53
  Compute:      Lambda Function  |  ECS Fargate  |  EC2 Instance  |  EKS Cluster
  Database:     RDS PostgreSQL  |  RDS MySQL  |  Aurora PostgreSQL  |  Aurora MySQL  |  DynamoDB Table
  Cache:        ElastiCache Redis  |  ElastiCache Memcached
  Storage:      S3 Bucket  |  EFS  |  EBS Volume
  Messaging:    SQS Queue  |  SNS Topic  |  EventBridge  |  Kinesis Stream
  Gateway:      API Gateway HTTP  |  API Gateway REST  |  API Gateway WebSocket  |  ALB  |  NLB  |  CloudFront
  Auth:         Cognito User Pool  |  Cognito Identity Pool
  IAM:          IAM Role  |  IAM Policy
  Secrets:      Secrets Manager  |  SSM Parameter Store  |  KMS Key
  CI/CD:        CodePipeline  |  CodeBuild  |  ECR Repository
-->

---

## Connections Detected

<!--
Review the connections below. Add or remove rows as needed.
Format: service-name → service-name  |  connection type  |  notes
-->

| From | To | Connection Type | Notes |
|------|----|----------------|-------|
| {service} | {service} | invokes | |
| {service} | {service} | reads/writes | needs security group rule |
| {service} | {service} | publishes to | async |

---

## IAM Roles Required per Service

<!--
These roles will be applied automatically when each service's wave is built via /ServiceCodeWriter.
One role per row — derived from service type. Do NOT edit unless you need to change trust/permissions.

WHAT HAPPENS DURING THE WAVE BUILD:
  1. /ServiceCodeWriter attempts terraform apply for each role in this table
  2. If the Terraform executor lacks iam:CreateRole → role is SKIPPED, service is still built,
     and you are notified which roles to create manually before running terraform apply in AWS.
  3. If roles are created → /TerraformValidator includes them in the plan validation.

Auto-Create = YES  →  skill attempts to apply this role during the wave build.
Auto-Create = NO   →  created by a different module (e.g. iam-base-roles) — listed for visibility only.
-->

| Service | Wave (est.) | Role Name | Trust Principal | Purpose | Auto-Create |
|---------|------------|-----------|----------------|---------|------------|
| {service} | {wave} | {role_name} | {trust_principal} | {purpose} | YES |

---

## Ambiguities — Answer Every Question

<!--
Fill in the Answer column for each ambiguity found in the diagram.
Leave the Question column unchanged.
-->

| # | Question | Your Answer |
|---|---------|------------|
{ambiguity rows — one per detected ambiguity}
| 1 | Label "{label}" — is this Redis or Memcached? | ← type your answer here |
| 2 | No VPC shown — should all services go in a single VPC? | ← yes / no + details |

<!--
If no ambiguities were found, this section will say "None detected".
-->

---

## Add Missing Services

<!-- 
List any services NOT in the diagram but needed in the project.
Delete this section if nothing to add.
Format: one service per row.
-->

| Final Name | Type | Notes |
|-----------|------|-------|
| | | |

---

## Project Configuration

<!-- Fill in every field below. Remove the # from example lines and edit them. -->

```
project_name:    {project_name}
# Example:       my-api-platform
# Rules:         lowercase, hyphens only, 4-30 chars, no spaces

aws_region:      ← fill this in
# Options:       us-east-1  |  us-west-2  |  eu-west-1  |  eu-central-1  |  ap-southeast-1

environments:    ← fill this in
# Options:       dev,prod  |  dev,staging,prod  |  dev only

aws_provider_version:   ~> 5.0
# Change only if you need a specific version

terraform_version:      >= 1.6.0
# Change only if you need a specific version
```

---

## Review Status
<!-- Do not edit this line — /ServicesRefinerConfirm reads it -->
STATUS: PENDING
```

After writing: open the file in VS Code automatically if possible.

Show in chat:
```
📝 agent/review/services-review.md created

I detected {n} services and {n} connections from your diagram.
{n} ambiguities need answering.

Next:
  1. Open agent/review/services-review.md in VS Code
  2. Edit the Final Name and Type columns  ← required in the file
  3. Optionally fill in Ambiguities and Project Config in the file
  4. Run /ServicesRefinerConfirm when done

💡 Any fields you leave blank (aws_region, environments, ambiguities, etc.)
   will be asked interactively by /ServicesRefinerConfirm — you don't have
   to edit them in the file if you prefer to answer in chat.

To regenerate this file (e.g. after re-exporting diagram): /ServicesRefiner
```

Do NOT ask any questions in chat at this stage. The file has everything the user needs.
The interactive Q&A happens in /ServicesRefinerConfirm for any fields left unanswered.
