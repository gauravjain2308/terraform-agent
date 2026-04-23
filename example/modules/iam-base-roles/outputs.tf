# Module: iam-base-roles — outputs consumed by all later waves

output "lambda_execution_role_arn" {
  description = "lambda_execution_role_arn — consumed by dependent service modules."
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "lambda_execution_role_name — consumed by dependent service modules."
  value       = aws_iam_role.lambda_execution.name
}

output "apigw_cloudwatch_role_arn" {
  description = "apigw_cloudwatch_role_arn — consumed by dependent service modules."
  value       = aws_iam_role.apigw_cloudwatch.arn
}

