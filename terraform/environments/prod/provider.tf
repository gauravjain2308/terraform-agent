provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Uncomment for multi-region resources (ACM for CloudFront, WAF global):
# provider "aws" {
#   alias   = "us_east_1"
#   region  = "us-east-1"
#   profile = var.aws_profile
#   default_tags {
#     tags = {
#       Project     = var.project_name
#       Environment = var.environment
#       ManagedBy   = "terraform"
#     }
#   }
# }
