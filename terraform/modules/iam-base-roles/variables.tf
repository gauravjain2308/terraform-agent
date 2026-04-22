# Module: iam-base-roles
variable "project_name" { description = "Project name."; type = string }
variable "environment"  { description = "Deployment environment (dev/staging/prod)."; type = string
  validation { condition = contains(["dev","staging","prod"],var.environment)
    error_message = "must be dev, staging, or prod." } }
variable "region"       { description = "AWS region."; type = string }
variable "tags"         { description = "Tags to apply to all resources."; type = map(string); default = {} }
variable "iam_path"     { description = "IAM path prefix."; type = string; default = "/" }
variable "permission_boundary_arn" { description = "Permission boundary ARN (leave empty if not required)."; type = string; default = "" }
variable "lambda_vpc_enabled" { description = "Set true if any Lambda runs inside a VPC."; type = bool; default = false }
