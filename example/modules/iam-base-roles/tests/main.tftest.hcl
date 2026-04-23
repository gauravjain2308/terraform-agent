# Tests for iam-base-roles
# Run: terraform test  (no AWS credentials needed)

mock_provider "aws" {
  mock_resource "aws_iam_role" { defaults = { id="mock",arn="arn:aws:iam::123456789012:role/mock",name="mock" } }
  mock_resource "aws_iam_role_policy_attachment" { defaults = { id="mock" } }
  mock_data "aws_caller_identity" { defaults = { account_id="123456789012" } }
  mock_data "aws_partition" { defaults = { partition="aws" } }
  mock_data "aws_iam_policy_document" { defaults = { json="{\"Version\":\"2012-10-17\",\"Statement\":[]}" } }
}

variables {
  project_name            = "test-s3-presigned-url-upload"
  environment             = "dev"
  region                  = "us-east-1"
  iam_path                = "/"
  permission_boundary_arn = ""
  lambda_vpc_enabled      = false
}

run "plan_succeeds" {
  command = plan
  assert { condition = length(aws_iam_role.lambda_execution) > 0
    error_message = "lambda_execution role must be planned" }
}

run "role_name_follows_convention" {
  command = plan
  assert { condition = can(regex("^test-.*-[a-z-]+$", aws_iam_role.lambda_execution.name))
    error_message = "Role name must follow project-env-service pattern" }}
}}

run "tags_applied" {
  command = plan
  assert { condition = aws_iam_role.lambda_execution.tags["ManagedBy"] == "terraform"
    error_message = "ManagedBy tag must be set" }}
}}

run "permission_boundary_null_when_empty" {
  command = plan
  assert { condition = aws_iam_role.lambda_execution.permissions_boundary == null
    error_message = "permissions_boundary must be null when variable is empty" }}
}}

run "vpc_policy_conditional" {
  command = plan
  variables { lambda_vpc_enabled = true }
  assert { condition = length(aws_iam_role_policy_attachment.lambda_execution_vpc) == 1
    error_message = "VPC policy must attach when lambda_vpc_enabled = true" }
}
