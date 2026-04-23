locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  api_name        = "${local.resource_prefix}-${var.api_name_suffix}"
  log_group_name  = "/aws/apigateway/${local.resource_prefix}-${var.api_name_suffix}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Module      = "api-gateway"
    CostCenter  = "engineering"
    DataClass   = "internal"
    Tier        = "api"
  })
}

resource "aws_cloudwatch_log_group" "access_logs" {
  count             = var.access_logging_enabled ? 1 : 0
  name              = local.log_group_name
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "main" {
  name          = local.api_name
  protocol_type = var.protocol_type
  description   = var.api_description

  dynamic "cors_configuration" {
    for_each = var.cors_enabled ? [1] : []
    content {
      allow_origins  = var.cors_allow_origins
      allow_methods  = var.cors_allow_methods
      allow_headers  = var.cors_allow_headers
      expose_headers = var.cors_expose_headers
      max_age        = var.cors_max_age_seconds
    }
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = var.integration_type
  integration_uri        = var.invoke_arn
  payload_format_version = var.payload_format_version
  timeout_milliseconds   = var.integration_timeout_ms
}

resource "aws_apigatewayv2_route" "main" {
  api_id             = aws_apigatewayv2_api.main.id
  route_key          = var.route_key
  authorization_type = var.authorization_type
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.stage_name
  auto_deploy = var.auto_deploy

  default_route_settings {
    throttling_burst_limit   = var.throttling_burst_limit
    throttling_rate_limit    = var.throttling_rate_limit
    detailed_metrics_enabled = var.detailed_metrics_enabled
  }

  dynamic "access_log_settings" {
    for_each = var.access_logging_enabled ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.access_logs[0].arn
      format          = var.access_log_format
    }
  }

  tags = local.common_tags
}
