variable "project_name" {
  description = "Name of the project. Used in resource naming and tagging."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}[a-z0-9]$", var.project_name))
    error_message = "project_name must be 4-30 chars, lowercase alphanumeric and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "region" {
  description = "AWS region for resource deployment."
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Additional tags to apply to all resources."
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Allow the bucket to be destroyed even if it contains objects. Set true for dev, false for prod."
  type        = bool
  default     = false
}

variable "versioning_status" {
  description = "Versioning state for the S3 bucket (Enabled or Suspended)."
  type        = string
  default     = "Enabled"

  validation {
    condition     = contains(["Enabled", "Suspended"], var.versioning_status)
    error_message = "versioning_status must be Enabled or Suspended."
  }
}

variable "encryption_algorithm" {
  description = "Server-side encryption algorithm (AES256 or aws:kms)."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.encryption_algorithm)
    error_message = "encryption_algorithm must be AES256 or aws:kms."
  }
}

variable "kms_key_arn" {
  description = "ARN of the KMS key for encryption. Required when encryption_algorithm is aws:kms, null for AES256."
  type        = string
  default     = null
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Key to reduce KMS request costs."
  type        = bool
  default     = true
}

variable "cors_enabled" {
  description = "Enable CORS configuration on the bucket."
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "List of allowed CORS origins."
  type        = list(string)
  default     = ["*"]
}

variable "cors_allowed_methods" {
  description = "List of allowed HTTP methods for CORS."
  type        = list(string)
  default     = ["GET", "PUT", "POST"]
}

variable "cors_allowed_headers" {
  description = "List of allowed headers for CORS requests."
  type        = list(string)
  default     = ["*"]
}

variable "cors_expose_headers" {
  description = "List of headers to expose in CORS responses."
  type        = list(string)
  default     = ["ETag", "x-amz-request-id"]
}

variable "cors_max_age_seconds" {
  description = "Time in seconds the browser can cache preflight CORS response."
  type        = number
  default     = 3000
}

variable "lifecycle_enabled" {
  description = "Enable lifecycle configuration rules on the bucket."
  type        = bool
  default     = false
}

variable "lifecycle_prefix" {
  description = "Object key prefix to which the lifecycle rule applies. Empty string applies to all objects."
  type        = string
  default     = ""
}

variable "transition_to_ia_days" {
  description = "Number of days before transitioning objects to STANDARD_IA storage."
  type        = number
  default     = 90
}

variable "transition_to_glacier_days" {
  description = "Number of days before transitioning objects to GLACIER storage."
  type        = number
  default     = 365
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days after which noncurrent object versions are permanently deleted."
  type        = number
  default     = 30
}

variable "object_expiration_days" {
  description = "Number of days before current objects expire and are deleted. Set 0 to disable."
  type        = number
  default     = 0
}
