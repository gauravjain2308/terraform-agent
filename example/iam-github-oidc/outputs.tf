output "plan_role_arn" {
  description = "Add to GitHub secret: AWS_PLAN_ROLE_ARN"
  value       = aws_iam_role.github_plan.arn
}

output "apply_dev_role_arn" {
  description = "Add to GitHub secret: AWS_APPLY_ROLE_ARN_DEV"
  value       = aws_iam_role.github_apply_dev.arn
}

output "apply_prod_role_arn" {
  description = "Add to GitHub secret: AWS_APPLY_ROLE_ARN_PROD"
  value       = aws_iam_role.github_apply_prod.arn
}
