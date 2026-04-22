output "api_id" {
  description = "The ID of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.main.id
}

output "api_arn" {
  description = "The ARN of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.main.arn
}

output "api_endpoint" {
  description = "The URI of the API (without stage suffix)."
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "execution_arn" {
  description = "The ARN prefix used for Lambda permission source ARN conditions."
  value       = aws_apigatewayv2_api.main.execution_arn
}

output "stage_id" {
  description = "The ID of the deployed stage."
  value       = aws_apigatewayv2_stage.main.id
}

output "stage_arn" {
  description = "The ARN of the deployed stage."
  value       = aws_apigatewayv2_stage.main.arn
}

output "stage_invoke_url" {
  description = "The URL to invoke the API stage (base URL including stage name)."
  value       = aws_apigatewayv2_stage.main.invoke_url
}

output "presigned_url_endpoint" {
  description = "Full URL for the GET /presigned-url route."
  value       = "${aws_apigatewayv2_stage.main.invoke_url}/presigned-url"
}

output "access_log_group_arn" {
  description = "ARN of the access log group (empty string when logging is disabled)."
  value       = var.access_logging_enabled ? aws_cloudwatch_log_group.access_logs[0].arn : ""
}
