# IAM tests for presigned-url-fn
# Run: terraform test  (no AWS credentials needed)

mock_provider "aws" {
  mock_resource "aws_iam_role_policy" { defaults = { id="mock" } }
  mock_resource "aws_lambda_permission" { defaults = { id="mock" } }
  mock_data "aws_caller_identity" { defaults = { account_id="123456789012" } }
  mock_data "aws_region" { defaults = { name="us-east-1" } }
  mock_data "aws_iam_policy_document" { defaults = { json="{\"Version\":\"2012-10-17\",\"Statement\":[]}" } }
}

run "policy_upload_bucket_scoped_not_wildcard" {
  command = plan

  variables {
    project_name              = "test-project"
    environment               = "dev"
    bucket_id                 = "test-project-dev-upload-bucket-abc12345"
    bucket_arn                = "arn:aws:s3:::test-project-dev-upload-bucket-abc12345"
    lambda_execution_role_arn = "arn:aws:iam::123456789012:role/test-project-dev-lambda-exec"
    lambda_execution_name     = "test-project-dev-lambda-exec"
  }

  assert {
    condition     = !can(regex("\\*$", data.aws_iam_policy_document.inline_presigned_url_fn_upload_bucket.json))
    error_message = "upload-bucket inline policy must not use bare wildcard resource"
  }
}

