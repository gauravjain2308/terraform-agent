# GitHub Actions OIDC Roles
# Run once: cd iam-github-oidc && terraform init && terraform apply
# Then add the 3 role ARN outputs to GitHub repo secrets.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

data "aws_iam_policy_document" "github_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # TODO: replace YOUR_ORG/YOUR_REPO with your GitHub org and repo name
      values   = ["repo:YOUR_ORG/YOUR_REPO:*"]
    }
  }
}

resource "aws_iam_role" "github_plan" {
  name               = "s3-presigned-url-upload-github-plan"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  description        = "GitHub Actions: terraform plan (read-only)"
  tags               = { Project = "s3-presigned-url-upload", ManagedBy = "terraform" }
}

resource "aws_iam_role" "github_apply_dev" {
  name               = "s3-presigned-url-upload-github-apply-dev"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  description        = "GitHub Actions: terraform apply to dev"
  tags               = { Project = "s3-presigned-url-upload", ManagedBy = "terraform" }
}

resource "aws_iam_role" "github_apply_prod" {
  name               = "s3-presigned-url-upload-github-apply-prod"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
  description        = "GitHub Actions: terraform apply to prod (manual approval required)"
  tags               = { Project = "s3-presigned-url-upload", ManagedBy = "terraform" }
}
