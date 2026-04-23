mock_provider "aws" {
  mock_resource "aws_lambda_function" {
    defaults = {
      arn           = "arn:aws:lambda:us-east-1:123456789012:function:test-project-dev-presigned-url-fn"
      invoke_arn    = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:test-project-dev-presigned-url-fn/invocations"
      qualified_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-project-dev-presigned-url-fn:$LATEST"
    }
  }

  mock_resource "aws_cloudwatch_log_group" {
    defaults = {
      arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/test-project-dev-presigned-url-fn"
    }
  }

  mock_resource "aws_iam_role_policy" {
    defaults = {
      id = "mock-policy-id"
    }
  }

  mock_resource "aws_lambda_permission" {
    defaults = {
      id = "mock-permission-id"
    }
  }

  mock_data "aws_region" {
    defaults = {
      name = "us-east-1"
    }
  }

  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
    }
  }

  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{}"
    }
  }
}

run "plan_succeeds_with_valid_inputs" {
  command = plan

  variables {
    project_name              = "test-project"
    environment               = "dev"
    region                    = "us-east-1"
    bucket_id                 = "test-project-dev-upload-bucket-abc12345"
    bucket_arn                = "arn:aws:s3:::test-project-dev-upload-bucket-abc12345"
    lambda_execution_role_arn = "arn:aws:iam::123456789012:role/test-project-dev-lambda-exec"
    lambda_execution_name     = "test-project-dev-lambda-exec"
  }

  assert {
    condition     = aws_lambda_function.main.function_name == "test-project-dev-presigned-url-fn"
    error_message = "Function name must follow naming convention."
  }

  assert {
    condition     = aws_lambda_function.main.runtime == "python3.12"
    error_message = "Default runtime must be python3.12."
  }
}

run "rejects_invalid_environment" {
  command = plan

  variables {
    project_name              = "test-project"
    environment               = "production"
    region                    = "us-east-1"
    bucket_id                 = "test-project-dev-upload-bucket-abc12345"
    bucket_arn                = "arn:aws:s3:::test-project-dev-upload-bucket-abc12345"
    lambda_execution_role_arn = "arn:aws:iam::123456789012:role/test-project-dev-lambda-exec"
    lambda_execution_name     = "test-project-dev-lambda-exec"
  }

  expect_failures = [var.environment]
}

run "tags_are_applied" {
  command = plan

  variables {
    project_name              = "test-project"
    environment               = "dev"
    region                    = "us-east-1"
    bucket_id                 = "test-project-dev-upload-bucket-abc12345"
    bucket_arn                = "arn:aws:s3:::test-project-dev-upload-bucket-abc12345"
    lambda_execution_role_arn = "arn:aws:iam::123456789012:role/test-project-dev-lambda-exec"
    lambda_execution_name     = "test-project-dev-lambda-exec"
  }

  assert {
    condition     = aws_lambda_function.main.tags["ManagedBy"] == "terraform"
    error_message = "ManagedBy tag must be 'terraform'."
  }

  assert {
    condition     = aws_lambda_function.main.tags["Module"] == "presigned-url-fn"
    error_message = "Module tag must be 'presigned-url-fn'."
  }
}

run "rejects_invalid_architecture" {
  command = plan

  variables {
    project_name              = "test-project"
    environment               = "dev"
    region                    = "us-east-1"
    bucket_id                 = "test-project-dev-upload-bucket-abc12345"
    bucket_arn                = "arn:aws:s3:::test-project-dev-upload-bucket-abc12345"
    lambda_execution_role_arn = "arn:aws:iam::123456789012:role/test-project-dev-lambda-exec"
    lambda_execution_name     = "test-project-dev-lambda-exec"
    architecture              = "i386"
  }

  expect_failures = [var.architecture]
}
