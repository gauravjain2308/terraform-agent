locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  function_name   = "${local.resource_prefix}-presigned-url-fn"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Module      = "presigned-url-fn"
    CostCenter  = "engineering"
    DataClass   = "internal"
    Tier        = "compute"
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder_generated.zip"
  source {
    content  = "def handler(event, context): return {'statusCode': 200}"
    filename = "index.py"
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

locals {
  effective_package_path = var.lambda_package_path != "" ? var.lambda_package_path : data.archive_file.placeholder.output_path
}

resource "aws_lambda_function" "main" {
  function_name = local.function_name
  role          = var.lambda_execution_role_arn
  runtime       = var.runtime
  handler       = var.handler
  architectures = [var.architecture]
  memory_size   = var.memory_size
  timeout       = var.timeout
  package_type  = "Zip"

  filename         = local.effective_package_path
  source_code_hash = var.lambda_package_path != "" ? null : data.archive_file.placeholder.output_base64sha256

  reserved_concurrent_executions = var.reserved_concurrency

  ephemeral_storage {
    size = var.ephemeral_storage_mb
  }

  environment {
    variables = {
      BUCKET_NAME                  = var.bucket_id
      BUCKET_ARN                   = var.bucket_arn
      PRESIGNED_URL_EXPIRY_SECONDS = var.presigned_url_expiry_seconds
      MAX_UPLOAD_SIZE_BYTES        = var.max_upload_size_bytes
      PRESIGNED_URL_METHOD         = var.presigned_url_method
      ALLOWED_CONTENT_TYPES        = var.allowed_content_types
      LOG_LEVEL                    = var.log_level
    }
  }

  tracing_config {
    mode = var.xray_tracing_mode
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda.name
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  lifecycle {
    ignore_changes = [filename]
  }

  tags = local.common_tags
}
