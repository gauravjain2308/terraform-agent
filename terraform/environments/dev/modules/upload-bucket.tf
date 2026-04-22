module "upload_bucket" {
  source = "../../../modules/upload-bucket"

  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  tags         = local.common_tags

  force_destroy              = true
  versioning_status          = "Enabled"
  encryption_algorithm       = "AES256"
  kms_key_arn                = null
  bucket_key_enabled         = true

  cors_enabled         = true
  cors_allowed_origins = ["*"]
  cors_allowed_methods = ["GET", "PUT", "POST"]
  cors_allowed_headers = ["*"]
  cors_expose_headers  = ["ETag", "x-amz-request-id"]
  cors_max_age_seconds = 3000

  lifecycle_enabled                  = true
  lifecycle_prefix                   = ""
  transition_to_ia_days              = 90
  transition_to_glacier_days         = 365
  noncurrent_version_expiration_days = 30
  object_expiration_days             = 0
}
