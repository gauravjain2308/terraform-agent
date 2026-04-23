module "iam_base_roles" {
  source = "../../modules/iam-base-roles"

  project_name             = var.project_name
  environment              = var.environment
  region                   = var.region
  tags                     = local.common_tags
  iam_path                 = "/"
  permission_boundary_arn  = ""
  lambda_vpc_enabled       = false
}
