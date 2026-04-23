terraform {
  backend "s3" {
    bucket         = "test-project-terraform-state-use1"
    key            = "test-project-terraform-state-use1/dev/terraform.tfstate"
    region         = "us-east-1"
    use_lockfile   = true
    encrypt        = true
  }
}
