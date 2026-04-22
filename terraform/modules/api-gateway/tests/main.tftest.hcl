mock_provider "aws" {
  mock_resource "aws_cloudwatch_log_group" {
    defaults = {
      arn  = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/test-s3-presigned-url-upload-dev-api"
      name = "/aws/apigateway/test-s3-presigned-url-upload-dev-api"
    }
  }
  mock_resource "aws_apigatewayv2_api" {
    defaults = {
      id            = "mock-api-id"
      arn           = "arn:aws:apigateway:us-east-1::/apis/mock-api-id"
      api_endpoint  = "https://mock-api-id.execute-api.us-east-1.amazonaws.com"
      execution_arn = "arn:aws:execute-api:us-east-1:123456789012:mock-api-id"
    }
  }
  mock_resource "aws_apigatewayv2_integration" {
    defaults = { id = "mock-integration-id" }
  }
  mock_resource "aws_apigatewayv2_route" {
    defaults = { id = "mock-route-id" }
  }
  mock_resource "aws_apigatewayv2_stage" {
    defaults = {
      id         = "dev"
      arn        = "arn:aws:apigateway:us-east-1::/apis/mock-api-id/stages/dev"
      invoke_url = "https://mock-api-id.execute-api.us-east-1.amazonaws.com/dev"
    }
  }
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_data "aws_region" {
    defaults = { name = "us-east-1" }
  }
}

variables {
  project_name = "test-s3-presigned-url-upload"
  environment  = "dev"
  region       = "us-east-1"
  invoke_arn   = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:test-fn/invocations"
  function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-fn"
  stage_name   = "dev"
}

run "plan_succeeds" {
  command = plan

  assert {
    condition     = aws_apigatewayv2_api.main.protocol_type == "HTTP"
    error_message = "API must use HTTP protocol"
  }

  assert {
    condition     = aws_apigatewayv2_api.main.name == "test-s3-presigned-url-upload-dev-api"
    error_message = "API name must follow resource_prefix-api_name_suffix convention"
  }
}

run "cors_enabled_by_default" {
  command = plan

  assert {
    condition     = length(aws_apigatewayv2_api.main.cors_configuration) > 0
    error_message = "CORS configuration must be present when cors_enabled is true"
  }
}

run "no_access_logs_in_dev" {
  command = plan

  assert {
    condition     = length(aws_cloudwatch_log_group.access_logs) == 0
    error_message = "Access log group should not be created when access_logging_enabled is false"
  }
}

run "integration_uses_lambda_proxy" {
  command = plan

  assert {
    condition     = aws_apigatewayv2_integration.lambda.integration_type == "AWS_PROXY"
    error_message = "Integration type must be AWS_PROXY"
  }

  assert {
    condition     = aws_apigatewayv2_integration.lambda.payload_format_version == "2.0"
    error_message = "Payload format version must be 2.0"
  }
}

run "stage_auto_deploy_enabled" {
  command = plan

  assert {
    condition     = aws_apigatewayv2_stage.main.auto_deploy == true
    error_message = "Stage must have auto_deploy enabled"
  }
}
