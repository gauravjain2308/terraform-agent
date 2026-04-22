# Per-service module wiring
#
# Each service's `module "..."` block is written to its own file here
# (e.g. `rds-users.tf`) by /ServiceCodeWriter. Terraform auto-loads every
# *.tf file in this directory, so no root-level edits are needed.
#
# Environment: dev
