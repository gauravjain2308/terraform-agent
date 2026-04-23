variable "project_name" {
  description = "Project name for resource naming and tagging."
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

# --- IAM (from iam-base-roles) ---

variable "lambda_execution_role_arn" {
  description = "ARN of the shared Lambda execution IAM role (from iam-base-roles)."
  type        = string
}

variable "lambda_execution_name" {
  description = "Name of the shared Lambda execution IAM role (from iam-base-roles), used for inline policy attachment."
  type        = string
}

# --- Dependency: upload-bucket ---

variable "bucket_id" {
  description = "S3 bucket name (ID) from the upload-bucket module."
  type        = string
}

variable "bucket_arn" {
  description = "S3 bucket ARN from the upload-bucket module."
  type        = string
}

# --- API Gateway back-reference (needed by iam.tf lambda permission) ---

variable "api_gateway_arn" {
  description = "ARN of the API Gateway that is allowed to invoke this Lambda. Set to empty string until api-gateway is deployed."
  type        = string
  default     = ""
}

# --- Lambda configuration ---

variable "runtime" {
  description = "Lambda runtime identifier."
  type        = string
  default     = "python3.12"
}

variable "handler" {
  description = "Lambda handler in the form file.function."
  type        = string
  default     = "index.handler"
}

variable "architecture" {
  description = "Instruction set architecture for the Lambda function (x86_64 or arm64)."
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.architecture)
    error_message = "architecture must be x86_64 or arm64."
  }
}

variable "memory_size" {
  description = "Amount of memory (MB) allocated to the Lambda function."
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Maximum execution time in seconds."
  type        = number
  default     = 30
}

variable "ephemeral_storage_mb" {
  description = "Size of the /tmp directory in MB (512–10240)."
  type        = number
  default     = 512
}

variable "reserved_concurrency" {
  description = "Reserved concurrent executions. -1 means unreserved."
  type        = number
  default     = -1
}

variable "lambda_package_path" {
  description = "Local path to the Lambda deployment ZIP. Leave empty to use the auto-generated placeholder (first deploy only)."
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days."
  type        = number
  default     = 7
}

variable "log_level" {
  description = "Application log level passed as an environment variable."
  type        = string
  default     = "INFO"
}

variable "xray_tracing_mode" {
  description = "X-Ray tracing mode: PassThrough or Active."
  type        = string
  default     = "PassThrough"

  validation {
    condition     = contains(["PassThrough", "Active"], var.xray_tracing_mode)
    error_message = "xray_tracing_mode must be PassThrough or Active."
  }
}

# --- Presigned URL settings ---

variable "presigned_url_expiry_seconds" {
  description = "Lifetime of generated presigned URLs in seconds."
  type        = number
  default     = 3600
}

variable "max_upload_size_bytes" {
  description = "Maximum allowed upload size in bytes enforced by the Lambda."
  type        = number
  default     = 104857600
}

variable "presigned_url_method" {
  description = "HTTP method for the presigned URL (PUT or POST)."
  type        = string
  default     = "PUT"

  validation {
    condition     = contains(["PUT", "POST"], var.presigned_url_method)
    error_message = "presigned_url_method must be PUT or POST."
  }
}

variable "allowed_content_types" {
  description = "Comma-separated list of allowed MIME types. Empty string means all types allowed."
  type        = string
  default     = ""
}
