terraform {
  backend "s3" {
    bucket         = "s3-presigned-url-upload-tf-state-use1"
    key            = "s3-presigned-url-upload/prod/terraform.tfstate"
    region         = "us-east-1"
    use_lockfile   = true
    encrypt        = true
  }
}
