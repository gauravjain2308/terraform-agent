output "function_arn" {
  description = "The ARN of the Lambda function."
  value       = aws_lambda_function.main.arn
}

output "function_name" {
  description = "The name of the Lambda function."
  value       = aws_lambda_function.main.function_name
}

output "invoke_arn" {
  description = "The invoke ARN of the Lambda function (used by API Gateway integration)."
  value       = aws_lambda_function.main.invoke_arn
}

output "function_qualified_arn" {
  description = "The qualified ARN of the Lambda function (includes version)."
  value       = aws_lambda_function.main.qualified_arn
}

output "log_group_name" {
  description = "The CloudWatch log group name for this Lambda function."
  value       = aws_cloudwatch_log_group.lambda.name
}

output "log_group_arn" {
  description = "The CloudWatch log group ARN for this Lambda function."
  value       = aws_cloudwatch_log_group.lambda.arn
}
