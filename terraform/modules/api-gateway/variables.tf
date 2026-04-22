variable "project_name" {
  description = "Project name for resource naming and tagging."
  type        = string
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
  description = "AWS region."
  type        = string
}

variable "tags" {
  description = "Additional tags to merge with common tags."
  type        = map(string)
  default     = {}
}

# ── Inputs from presigned-url-fn (Wave 2) ────────────────────────────────────

variable "invoke_arn" {
  description = "Invoke ARN of the presigned-url Lambda function."
  type        = string
}

variable "function_arn" {
  description = "ARN of the presigned-url Lambda function."
  type        = string
}

# ── IAM (from iam-base-roles, used by iam.tf) ─────────────────────────────────

variable "api_gateway_name" {
  description = "Name of the IAM role to attach the API Gateway inline policy to."
  type        = string
  default     = ""
}

# ── API Gateway configuration ─────────────────────────────────────────────────

variable "api_name_suffix" {
  description = "Suffix appended to the resource prefix to form the API name."
  type        = string
  default     = "api"
}

variable "api_description" {
  description = "Description of the API Gateway."
  type        = string
  default     = "Presigned URL API for mobile direct S3 uploads"
}

variable "protocol_type" {
  description = "API Gateway protocol type. Must be HTTP or WEBSOCKET."
  type        = string
  default     = "HTTP"

  validation {
    condition     = contains(["HTTP", "WEBSOCKET"], var.protocol_type)
    error_message = "protocol_type must be HTTP or WEBSOCKET."
  }
}

# ── Route & integration ───────────────────────────────────────────────────────

variable "route_key" {
  description = "Route key for the API route, e.g. GET /presigned-url."
  type        = string
  default     = "GET /presigned-url"
}

variable "authorization_type" {
  description = "Authorization type for the route (NONE, JWT, AWS_IAM, CUSTOM)."
  type        = string
  default     = "NONE"
}

variable "integration_type" {
  description = "Integration type (AWS_PROXY, HTTP_PROXY, MOCK)."
  type        = string
  default     = "AWS_PROXY"
}

variable "payload_format_version" {
  description = "Lambda payload format version (1.0 or 2.0)."
  type        = string
  default     = "2.0"
}

variable "integration_timeout_ms" {
  description = "Integration timeout in milliseconds (50–29000)."
  type        = number
  default     = 10000
}

# ── Stage ─────────────────────────────────────────────────────────────────────

variable "stage_name" {
  description = "Name of the deployment stage."
  type        = string
}

variable "auto_deploy" {
  description = "Whether to automatically deploy changes to this stage."
  type        = bool
  default     = true
}

variable "throttling_burst_limit" {
  description = "Default route throttling burst limit for the stage."
  type        = number
  default     = 100
}

variable "throttling_rate_limit" {
  description = "Default route throttling rate limit (requests per second) for the stage."
  type        = number
  default     = 50
}

variable "detailed_metrics_enabled" {
  description = "Whether detailed CloudWatch metrics are enabled for the stage."
  type        = bool
  default     = false
}

# ── CORS ──────────────────────────────────────────────────────────────────────

variable "cors_enabled" {
  description = "Whether to configure CORS on the API."
  type        = bool
  default     = true
}

variable "cors_allow_origins" {
  description = "List of allowed origins for CORS."
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_methods" {
  description = "List of allowed HTTP methods for CORS."
  type        = list(string)
  default     = ["GET", "OPTIONS"]
}

variable "cors_allow_headers" {
  description = "List of allowed headers for CORS."
  type        = list(string)
  default     = ["Content-Type", "Authorization", "X-Requested-With"]
}

variable "cors_expose_headers" {
  description = "List of headers to expose in CORS responses."
  type        = list(string)
  default     = ["X-Request-Id"]
}

variable "cors_max_age_seconds" {
  description = "How long (seconds) browsers can cache CORS preflight results."
  type        = number
  default     = 3600
}

# ── Access logging ────────────────────────────────────────────────────────────

variable "access_logging_enabled" {
  description = "Whether to enable access logging for the stage."
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log group retention in days."
  type        = number
  default     = 7
}

variable "access_log_format" {
  description = "JSON format string for access log records."
  type        = string
  default     = "{\"requestId\":\"$context.requestId\",\"ip\":\"$context.identity.sourceIp\",\"requestTime\":\"$context.requestTime\",\"httpMethod\":\"$context.httpMethod\",\"routeKey\":\"$context.routeKey\",\"status\":\"$context.status\",\"protocol\":\"$context.protocol\",\"responseLength\":\"$context.responseLength\",\"integrationLatency\":\"$context.integrationLatency\",\"responseLatency\":\"$context.responseLatency\"}"
}
