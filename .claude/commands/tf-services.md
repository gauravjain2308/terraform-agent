# /tf-services
Show every AWS service and resource being created across all Terraform modules, in a tabular format with a reason for each. Read-only — no /clear needed after this.

## Step 1 — Discover the environment

Read `terraform/environments/dev/` to find every `module "..."` block being invoked.
Then, for each module, read its `terraform/modules/<module-name>/main.tf` (and `iam.tf` if present) to find every `resource "..."` block it contains.

Also scan environment-level `.tf` files for any `resource "..."` blocks defined directly (not inside a module directory).

## Step 2 — Build the output

Print the following report. Replace the example rows with ACTUAL data read from the files.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TERRAFORM SERVICE INVENTORY  |  terraform/environments/dev/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY  ({N} modules  |  {R} resources total)

  ┌──────────────────────────┬───────────┬────────────────────────────────────────────────┐
  │ Module (service)         │ Resources │ Purpose                                        │
  ├──────────────────────────┼───────────┼────────────────────────────────────────────────┤
  │ iam-base-roles           │     N     │ Shared IAM execution roles for Lambda & APIGW  │
  │ upload-bucket            │     N     │ S3 bucket for direct mobile file uploads       │
  │ presigned-url-fn         │     N     │ Lambda that generates S3 pre-signed PUT URLs   │
  │ api-gateway              │     N     │ HTTP API Gateway exposing GET /presigned-url   │
  │ (env-level resources)    │     N     │ Glue permissions between modules               │
  └──────────────────────────┴───────────┴────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED RESOURCE LIST  (every AWS resource being provisioned)

  ┌──────────────────────────┬────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
  │ Module                   │ Resource (type.name)                       │ Why it is created                                                │
  ├──────────────────────────┼────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ iam-base-roles           │ aws_iam_role.lambda_execution              │ Execution role assumed by all Lambda functions                   │
  │ iam-base-roles           │ aws_iam_role_policy_attachment.lambda_*    │ Attaches AWSLambdaBasicExecutionRole managed policy              │
  │ iam-base-roles           │ aws_iam_role_policy_attachment.lambda_xray │ Grants Lambda permission to write X-Ray traces                  │
  │ iam-base-roles           │ aws_iam_role.apigw_cloudwatch              │ Allows API Gateway to push access logs to CloudWatch            │
  │ iam-base-roles           │ aws_iam_role_policy_attachment.apigw_*     │ Attaches AmazonAPIGatewayPushToCloudWatchLogs managed policy     │
  ├──────────────────────────┼────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ upload-bucket            │ aws_s3_bucket.main                        │ Stores uploaded files from mobile clients                        │
  │ upload-bucket            │ aws_s3_bucket_public_access_block.main    │ Blocks all public access — private bucket only                   │
  │ upload-bucket            │ aws_s3_bucket_versioning.main             │ Enables versioning so overwritten files can be recovered         │
  │ upload-bucket            │ aws_s3_bucket_server_side_encryption_*    │ Encrypts all objects at rest with AES-256                        │
  │ upload-bucket            │ aws_s3_bucket_cors_configuration.main     │ Allows browser/mobile clients to PUT directly to S3              │
  │ upload-bucket            │ aws_s3_bucket_lifecycle_configuration.main│ Moves old objects to IA/Glacier, expires non-current versions    │
  ├──────────────────────────┼────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ presigned-url-fn         │ aws_cloudwatch_log_group.lambda           │ Stores Lambda logs with a configured retention window            │
  │ presigned-url-fn         │ aws_lambda_function.main                  │ The function that generates pre-signed PUT URLs for the bucket   │
  ├──────────────────────────┼────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ api-gateway              │ aws_apigatewayv2_api.main                 │ HTTP API endpoint exposed to mobile clients                       │
  │ api-gateway              │ aws_apigatewayv2_integration.lambda       │ Wires the API route to the Lambda function (AWS_PROXY)           │
  │ api-gateway              │ aws_apigatewayv2_route.main               │ Defines GET /presigned-url route                                 │
  │ api-gateway              │ aws_apigatewayv2_stage.main               │ Dev stage with auto-deploy and throttling limits                 │
  ├──────────────────────────┼────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ (env-level)              │ aws_lambda_permission.api_gateway_invoke_* │ Grants API Gateway permission to invoke the Lambda function      │
  └──────────────────────────┴────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONDITIONAL RESOURCES  (created only when a variable is set)

  ┌───────────────────────────────────────────────────┬─────────────────────┬────────────────────────────────────┐
  │ Resource                                          │ Condition           │ Current value (dev)                │
  ├───────────────────────────────────────────────────┼─────────────────────┼────────────────────────────────────┤
  │ aws_cloudwatch_log_group.access_logs (apigw)      │ access_logging_enabled = true  │ false → NOT created   │
  │ aws_iam_role_policy_attachment.lambda_execution_vpc│ lambda_vpc_enabled = true     │ false → NOT created   │
  │ aws_s3_bucket_cors_configuration.main             │ cors_enabled = true           │ true  → CREATED       │
  │ aws_s3_bucket_lifecycle_configuration.main        │ lifecycle_enabled = true      │ true  → CREATED       │
  └───────────────────────────────────────────────────┴─────────────────────┴────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IAM RESOURCES  (roles, policies, attachments)

  ┌──────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
  │ IAM Resource                                     │ Why                                                              │
  ├──────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
  │ aws_iam_role  lambda-execution                   │ Trust policy → lambda.amazonaws.com; used by presigned-url-fn    │
  │ aws_iam_role  apigw-cloudwatch                   │ Trust policy → apigateway.amazonaws.com; enables access logging  │
  │ aws_iam_policy  presigned_url_fn_s3_access       │ Inline policy granting s3:PutObject on the upload bucket         │
  │ aws_iam_role_policy_attachment (3 attachments)   │ Attach AWS managed policies to lambda-execution role             │
  └──────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATA FLOW (why each service depends on the next)

  Mobile client
      │  GET /presigned-url
      ▼
  API Gateway  (aws_apigatewayv2_api)
      │  AWS_PROXY integration → invokes
      ▼
  Lambda: presigned-url-fn  (aws_lambda_function)
      │  Calls s3:GeneratePresignedUrl for
      ▼
  S3 Bucket: upload-bucket  (aws_s3_bucket)
      │  Client uploads file directly using the pre-signed URL
      ▲
  IAM: iam-base-roles  (provides execution role to Lambda)
```

## Step 3 — Rules for generating this output

1. **Read actual files** — do not guess resource names; read `terraform/modules/*/main.tf`, `terraform/modules/*/iam.tf`, and all `terraform/environments/dev/*.tf`.
2. **Count correctly** — the Summary table "Resources" column must match the count of `resource "..."` blocks found in the source.
3. **Conditional resources** — detect `count = var.X ? 1 : 0` and `for_each` patterns; look up the actual variable value set in `terraform/environments/dev/*.tf` or the module invocation.
4. **Reason column** — derive the reason from the resource type + its configuration (e.g., `aws_s3_bucket_public_access_block` with all flags true → "Blocks all public access").
5. **IAM section** — list every `aws_iam_role`, `aws_iam_policy`, and `aws_iam_role_policy_attachment` separately.
6. **Data flow** — always show the logical call chain between services so the user understands why each piece exists.
7. Do NOT run `terraform plan` or any shell command — derive everything from static file analysis.

## Note

This command is read-only. The user can ask follow-up questions after seeing the output.
To see build/wave status, run /tf-status.
To see estimated cost, run /tf-cost.
