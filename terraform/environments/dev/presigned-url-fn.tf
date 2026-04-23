module "presigned_url_fn" {
  source = "../../modules/presigned-url-fn"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  tags         = local.common_tags

  # IAM — from iam-base-roles module
  lambda_execution_role_arn = module.iam_base_roles.lambda_execution_role_arn
  lambda_execution_name     = module.iam_base_roles.lambda_execution_role_name

  # Dependency: upload-bucket outputs
  bucket_id  = module.upload_bucket.bucket_id
  bucket_arn = module.upload_bucket.bucket_arn

  # Lambda configuration
  runtime              = "python3.12"
  handler              = "index.handler"
  architecture         = "arm64"
  memory_size          = 256
  timeout              = 30
  ephemeral_storage_mb = 512
  reserved_concurrency = -1
  log_retention_days   = 7
  log_level            = "DEBUG"
  xray_tracing_mode    = "PassThrough"

  # Presigned URL settings
  presigned_url_expiry_seconds = 3600
  max_upload_size_bytes        = 104857600
  presigned_url_method         = "PUT"
  allowed_content_types        = ""
}
