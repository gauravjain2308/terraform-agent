# Module: api-gateway
# IAM — API Gateway HTTP API uses resource-based Lambda permissions, not IAM execution roles.
# The aws_lambda_permission granting API Gateway access to invoke the Lambda is created
# in the root environment module to avoid a circular module dependency.

