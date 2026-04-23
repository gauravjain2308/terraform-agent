module "api_gateway" {
  source = "../../../modules/api-gateway"

  project_name = var.project_name
  environment  = "dev"
  region       = var.region
  tags         = var.tags

  invoke_arn   = module.presigned_url_fn.invoke_arn
  function_arn = module.presigned_url_fn.function_arn

  api_name_suffix          = "api"
  api_description          = "Presigned URL API for mobile direct S3 uploads"
  protocol_type            = "HTTP"
  route_key                = "GET /presigned-url"
  authorization_type       = "NONE"
  integration_type         = "AWS_PROXY"
  payload_format_version   = "2.0"
  integration_timeout_ms   = 10000

  stage_name               = "dev"
  auto_deploy              = true
  throttling_burst_limit   = 100
  throttling_rate_limit    = 50
  detailed_metrics_enabled = false

  cors_enabled             = true
  cors_allow_origins       = ["*"]
  cors_allow_methods       = ["GET", "OPTIONS"]
  cors_allow_headers       = ["Content-Type", "Authorization", "X-Requested-With"]
  cors_expose_headers      = ["X-Request-Id"]
  cors_max_age_seconds     = 3600

  access_logging_enabled   = false
  log_retention_days       = 7
}
