mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      id                          = "s3-presigned-url-upload-dev-uploads"
      arn                         = "arn:aws:s3:::s3-presigned-url-upload-dev-uploads"
      bucket_domain_name          = "s3-presigned-url-upload-dev-uploads.s3.amazonaws.com"
      bucket_regional_domain_name = "s3-presigned-url-upload-dev-uploads.s3.us-east-1.amazonaws.com"
    }
  }
  mock_resource "aws_s3_bucket_public_access_block" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_resource "aws_s3_bucket_versioning" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_resource "aws_s3_bucket_server_side_encryption_configuration" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_resource "aws_s3_bucket_cors_configuration" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_resource "aws_s3_bucket_lifecycle_configuration" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_resource "aws_s3_bucket_policy" {
    defaults = { id = "s3-presigned-url-upload-dev-uploads" }
  }
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_data "aws_region" {
    defaults = { name = "us-east-1" }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{}" }
  }
}

run "plan_succeeds_with_valid_inputs" {
  command = plan

  variables {
    project_name  = "s3-presigned-url-upload"
    environment   = "dev"
    region        = "us-east-1"
    force_destroy = true
    cors_enabled  = true
  }

  assert {
    condition     = aws_s3_bucket.main.bucket == "s3-presigned-url-upload-dev-uploads"
    error_message = "Bucket name must follow naming convention: {project}-{env}-uploads."
  }
}

run "rejects_invalid_environment" {
  command = plan

  variables {
    project_name = "s3-presigned-url-upload"
    environment  = "production"
    region       = "us-east-1"
  }

  expect_failures = [var.environment]
}

run "tags_are_applied" {
  command = plan

  variables {
    project_name = "s3-presigned-url-upload"
    environment  = "dev"
    region       = "us-east-1"
  }

  assert {
    condition     = aws_s3_bucket.main.tags["ManagedBy"] == "terraform"
    error_message = "ManagedBy tag must be 'terraform'."
  }

  assert {
    condition     = aws_s3_bucket.main.tags["Project"] == "s3-presigned-url-upload"
    error_message = "Project tag must match project_name."
  }
}

run "public_access_blocked" {
  command = plan

  variables {
    project_name = "s3-presigned-url-upload"
    environment  = "dev"
    region       = "us-east-1"
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.main.block_public_acls == true
    error_message = "block_public_acls must be true."
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.main.restrict_public_buckets == true
    error_message = "restrict_public_buckets must be true."
  }
}
