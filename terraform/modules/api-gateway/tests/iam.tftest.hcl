# IAM tests for api-gateway
# Run: terraform test  (no AWS credentials needed)

mock_provider "aws" {
  mock_resource "aws_iam_role_policy" { defaults = { id="mock" } }
  mock_resource "aws_lambda_permission" { defaults = { id="mock" } }
  mock_data "aws_caller_identity" { defaults = { account_id="123456789012" } }
  mock_data "aws_region" { defaults = { name="us-east-1" } }
  mock_data "aws_iam_policy_document" { defaults = { json="{\"Version\":\"2012-10-17\",\"Statement\":[]}" } }
}

run "policy_presigned_url_fn_scoped_not_wildcard" {
  command = plan
  assert { condition = !can(regex("\\*$", data.aws_iam_policy_document.inline_api_gateway_presigned_url_fn.json))
    error_message = "presigned-url-fn inline policy must not use bare wildcard resource" }
}

