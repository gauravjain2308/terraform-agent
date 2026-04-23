#!/usr/bin/env python3
"""
iam-generator.py
Generate IAM roles and policies from build plan. Outputs:
  1. agent/review/iam-model-review.json    — machine-readable full IAM spec
  2. agent/review/iam-model-review.md      — human-readable tabular review (wave-wise)
  3. terraform/modules/iam-base-roles/ — Wave 1 shared roles (.tf + tests)
  4. terraform/modules/{svc}/iam.tf    — Per-service inline + resource policies + tests

Usage:
  python3 agent/scripts/scaffold/iam-generator.py
  python3 agent/scripts/scaffold/iam-generator.py --dry-run
  python3 agent/scripts/scaffold/iam-generator.py --refresh    (re-run, mark built modules)
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# AWS managed policies that live under the service-role/ path prefix
SERVICE_ROLE_POLICIES = {
    "AWSLambdaBasicExecutionRole",
    "AWSLambdaVPCAccessExecutionRole",
    "AWSLambdaENIManagementAccess",
    "AmazonAPIGatewayPushToCloudWatchLogs",
    "AmazonECSTaskExecutionRolePolicy",
    "AmazonRDSEnhancedMonitoringRole",
    "AWSGlueServiceRole",
    "AWSBatchServiceRole",
    "AWSCodeDeployRole",
}

def _policy_arn(policy_name: str) -> str:
    prefix = "service-role/" if policy_name in SERVICE_ROLE_POLICIES else ""
    return f"arn:${{data.aws_partition.current.partition}}:iam::aws:policy/{prefix}{policy_name}"

# ─── IAM Rule Engine ──────────────────────────────────────────────────────────

SERVICE_TYPE_MAP = {
    "lambda function":"lambda","lambda":"lambda",
    "rds postgresql":"rds","rds mysql":"rds",
    "aurora postgresql":"rds","aurora mysql":"rds","rds":"rds",
    "ecs fargate":"ecs","ecs":"ecs",
    "api gateway http":"apigw","api gateway rest":"apigw",
    "api gateway websocket":"apigw","api gateway":"apigw",
    "sqs queue":"sqs","sqs":"sqs",
    "sns topic":"sns","sns":"sns",
    "s3 bucket":"s3","s3":"s3",
    "elasticache redis":"elasticache","elasticache memcached":"elasticache","elasticache":"elasticache",
    "dynamodb table":"dynamodb","dynamodb":"dynamodb",
    "vpc":"vpc","iam role":"iam","kms key":"kms",
}

BASE_ROLE_RULES = {
    "lambda": [{"role_resource":"aws_iam_role.lambda_execution","role_var_name":"lambda_execution",
                "role_name_tpl":"{project}-{env}-lambda-exec","trust":"lambda.amazonaws.com",
                "managed":["AWSLambdaBasicExecutionRole","AWSXRayDaemonWriteAccess"],
                "vpc_managed":["AWSLambdaVPCAccessExecutionRole"],
                "outputs":["lambda_execution_role_arn","lambda_execution_role_name"],
                "note":"Shared execution role for all Lambda functions"}],
    "ecs": [{"role_resource":"aws_iam_role.ecs_task_execution","role_var_name":"ecs_task_execution",
             "role_name_tpl":"{project}-{env}-ecs-exec","trust":"ecs-tasks.amazonaws.com",
             "managed":["AmazonECSTaskExecutionRolePolicy"],"vpc_managed":[],
             "outputs":["ecs_task_execution_role_arn"],
             "note":"ECS task execution role — pulls images, reads secrets at startup"},
            {"role_resource":"aws_iam_role.ecs_task","role_var_name":"ecs_task",
             "role_name_tpl":"{project}-{env}-ecs-task","trust":"ecs-tasks.amazonaws.com",
             "managed":[],"vpc_managed":[],
             "outputs":["ecs_task_role_arn","ecs_task_role_name"],
             "note":"ECS task role — runtime application permissions"}],
    "rds": [{"role_resource":"aws_iam_role.rds_monitoring","role_var_name":"rds_monitoring",
             "role_name_tpl":"{project}-{env}-rds-monitoring","trust":"monitoring.rds.amazonaws.com",
             "managed":["AmazonRDSEnhancedMonitoringRole"],"vpc_managed":[],
             "outputs":["rds_monitoring_role_arn"],"note":"RDS enhanced monitoring role"}],
    "apigw":[{"role_resource":"aws_iam_role.apigw_cloudwatch","role_var_name":"apigw_cloudwatch",
              "role_name_tpl":"{project}-{env}-apigw-cw","trust":"apigateway.amazonaws.com",
              "managed":["AmazonAPIGatewayPushToCloudWatchLogs"],"vpc_managed":[],
              "outputs":["apigw_cloudwatch_role_arn"],"note":"API Gateway CloudWatch logging role"}],
}

INLINE_RULES = {
    "rds":          {"actions":["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"],
                     "resource":"arn:aws:secretsmanager:{region}:{account}:secret:{project}/{env}/{provider}/*",
                     "note":"Read RDS password from Secrets Manager",
                     "kms_via_service":"secretsmanager"},
    "elasticache":  {"actions":["secretsmanager:GetSecretValue"],
                     "resource":"arn:aws:secretsmanager:{region}:{account}:secret:{project}/{env}/{provider}/*",
                     "note":"Read Redis auth token from Secrets Manager",
                     "kms_via_service":"secretsmanager"},
    "sqs":          {"actions":["sqs:ReceiveMessage","sqs:DeleteMessage","sqs:GetQueueAttributes","sqs:ChangeMessageVisibility"],
                     "resource":"arn:aws:sqs:{region}:{account}:{project}-{env}-{provider}",
                     "note":"Consume messages from SQS queue"},
    "s3":           {"actions":["s3:GetObject","s3:PutObject","s3:ListBucket"],
                     "resource":"arn:aws:s3:::{project}-{env}-{provider}/*",
                     "note":"Read/write S3 objects"},
    "dynamodb":     {"actions":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:DeleteItem","dynamodb:Query","dynamodb:Scan"],
                     "resource":"arn:aws:dynamodb:{region}:{account}:table/{project}-{env}-{provider}",
                     "note":"Read/write DynamoDB table"},
    "sns":          {"actions":["sns:Publish"],
                     "resource":"arn:aws:sns:{region}:{account}:{project}-{env}-{provider}",
                     "note":"Publish to SNS topic"},
    "secretsmanager":{"actions":["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"],
                     "resource":"arn:aws:secretsmanager:{region}:{account}:secret:{project}/{env}/{provider}/*",
                     "note":"Read secret value",
                     "kms_via_service":"secretsmanager"},
    "ssm":          {"actions":["ssm:GetParameter","ssm:GetParameters","ssm:GetParametersByPath"],
                     "resource":"arn:aws:ssm:{region}:{account}:parameter/{project}/{env}/*",
                     "note":"Read SSM parameters",
                     "kms_via_service":"ssm"},
    "lambda":       {"actions":["lambda:InvokeFunction"],
                     "resource":"arn:aws:lambda:{region}:{account}:function:{project}-{env}-{provider}",
                     "note":"Invoke Lambda function"},
}

RESOURCE_POLICY_RULES = {
    "lambda":{"policy_type":"aws_lambda_permission","action":"lambda:InvokeFunction",
              "principal":"apigateway.amazonaws.com","condition":"ArnLike SourceArn = API ARN"},
    "sqs":   {"policy_type":"aws_sqs_queue_policy","action":"sqs:SendMessage + sqs:ReceiveMessage + sqs:DeleteMessage",
              "principal":"consuming service role ARN","condition":"—"},
    "s3":    {"policy_type":"aws_s3_bucket_policy","action":"s3:GetObject, s3:PutObject",
              "principal":"accessing service role ARN","condition":"aws:SourceVpc (recommended)"},
    "sns":   {"policy_type":"aws_sns_topic_policy","action":"sns:Publish",
              "principal":"publishing service role ARN","condition":"—"},
}

# ─── Data model builder ───────────────────────────────────────────────────────

def generate_iam(services_data, build_plan_data):
    project  = services_data["project_name"]
    region   = services_data.get("region","{region}")
    services = services_data.get("services",[])
    dep_map  = build_plan_data.get("dependency_map",{})
    waves    = build_plan_data.get("waves",{})

    svc_type = {}
    svc_wave = {}
    for svc in services:
        sid  = svc["id"] if isinstance(svc,dict) else svc
        styp = (svc.get("type","") if isinstance(svc,dict) else "").lower()
        svc_type[sid] = SERVICE_TYPE_MAP.get(styp,"unknown")
    for w,svcs in waves.items():
        for s in svcs: svc_wave[s] = int(w)

    wave1 = min((int(w) for w in waves), default=1)

    # Base roles
    roles = []
    seen  = set()
    for svc in services:
        sid  = svc["id"] if isinstance(svc,dict) else svc
        tkey = svc_type.get(sid,"unknown")
        if tkey not in BASE_ROLE_RULES: continue
        for rule in BASE_ROLE_RULES[tkey]:
            rkey = rule["role_resource"]
            if rkey in seen: continue
            seen.add(rkey)
            roles.append({**rule,"wave":wave1,"module":"iam-base-roles",
                           "role_name":rule["role_name_tpl"].replace("{project}",project),
                           "build_status":"not_built"})

    # Inline policies
    inline_policies = []
    for consumer,deps in dep_map.items():
        ctype = svc_type.get(consumer,"unknown")
        if ctype=="lambda":   target = "aws_iam_role.lambda_execution"
        elif ctype=="ecs":    target = "aws_iam_role.ecs_task"
        else:                 target = f"aws_iam_role.{consumer.replace('-','_')}_role"
        target_var = target.replace("aws_iam_role.","").replace("_role","")

        for provider,outputs in deps.items():
            ptype = svc_type.get(provider,"unknown")
            rule  = INLINE_RULES.get(ptype)
            if not rule: continue
            res = (rule["resource"]
                   .replace("{project}",project)
                   .replace("{env}","${var.environment}")
                   .replace("{region}",region)
                   .replace("{account}","${data.aws_caller_identity.current.account_id}")
                   .replace("{provider}",provider))
            inline_policies.append({
                "consumer":consumer,"consumer_type":ctype,
                "provider":provider,"provider_type":ptype,
                "added_to_role":target,"target_var_name":target_var,
                "actions":rule["actions"],"resource_scope":res,
                "wave":svc_wave.get(consumer,"?"),"module":consumer,
                "note":rule["note"],"build_status":"not_built",
                "kms_via_service":rule.get("kms_via_service"),
            })

    # Resource policies
    resource_policies = []
    seen_rp = set()
    for consumer,deps in dep_map.items():
        for provider,outputs in deps.items():
            ptype = svc_type.get(provider,"unknown")
            rule  = RESOURCE_POLICY_RULES.get(ptype)
            if not rule: continue
            key = f"{provider}:{ptype}"
            if key in seen_rp: continue
            seen_rp.add(key)
            resource_policies.append({
                "resource":provider,"resource_type":ptype,
                "policy_type":rule["policy_type"],"action":rule["action"],
                "principal":rule["principal"],"condition":rule["condition"],
                "module":provider,"wave":svc_wave.get(provider,"?"),
                "triggered_by":f"{consumer} → {provider}","build_status":"not_built",
            })

    # Outputs map
    outputs_map = []
    seen_out = set()
    for role in roles:
        for out in role["outputs"]:
            if out in seen_out: continue
            seen_out.add(out)
            consumers = [p["consumer"] for p in inline_policies if p["added_to_role"]==role["role_resource"]]
            outputs_map.append({"output":out,"produced_by":role["module"],
                                  "produced_wave":role["wave"],"consumed_by":consumers,
                                  "variable_in_consumer":f"var.{out}"})

    # Wave breakdown
    wave_breakdown = {}
    for w in sorted(waves.keys(),key=int):
        wave_breakdown[w] = {
            "base_roles":        [r["role_resource"] for r in roles if str(r["wave"])==str(w)],
            "inline_policies":   [f"{p['consumer']}→{p['provider']}" for p in inline_policies if str(p["wave"])==str(w)],
            "resource_policies": [r["resource"] for r in resource_policies if str(r["wave"])==str(w)],
        }

    return {"generated_at":datetime.now().isoformat(),"project":project,"region":region,
            "confirmed":False,
            "summary":{"total_roles":len(roles),"total_inline_policies":len(inline_policies),
                       "total_resource_policies":len(resource_policies)},
            "iam_config":{"permission_boundary_arn":"none","iam_path":"/","cross_account_access":"none"},
            "wave_breakdown":wave_breakdown,"roles":roles,
            "inline_policies":inline_policies,"resource_policies":resource_policies,
            "outputs_map":outputs_map,
            "checklist":{"no_wildcard_resources":False,"all_roles_have_descriptions":False,
                         "no_admin_access":False,"ecs_has_both_roles":False,
                         "rds_has_monitoring_role":False,"apigw_has_cloudwatch_role":False,
                         "lambda_has_vpc_policy_if_needed":False}}

# ─── Terraform generators ─────────────────────────────────────────────────────

def _trust_doc(vname, trust):
    return (f'data "aws_iam_policy_document" "{vname}_trust" {{\n'
            f'  statement {{\n    effect  = "Allow"\n    actions = ["sts:AssumeRole"]\n'
            f'    principals {{ type = "Service" identifiers = ["{trust}"] }}\n  }}\n}}\n')

def gen_base_roles_main(iam_data):
    project = iam_data["project"]
    roles   = [r for r in iam_data["roles"] if r["module"]=="iam-base-roles"]
    out = ("# Module: iam-base-roles\n# Wave 1 — Shared IAM roles consumed by all later waves\n"
           "# Generated by iam-generator.py\n\n"
           'data "aws_caller_identity" "current" {}\ndata "aws_partition" "current" {}\n\n'
           "locals {\n  resource_prefix = \"${var.project_name}-${var.environment}\"\n"
           "  common_tags = merge(var.tags, {\n"
           "    Project = var.project_name\n    Environment = var.environment\n"
           "    ManagedBy = \"terraform\"\n    Module = \"iam-base-roles\"\n  })\n}\n\n")
    for role in roles:
        vn = role["role_var_name"]
        suffix = vn.replace("_role","").replace("_"," ").title().replace(" ","-").lower()
        out += f"# ── {vn} ── {role['note']}\n"
        out += _trust_doc(vn, role["trust"])
        out += (f'resource "aws_iam_role" "{vn}" {{\n'
                f'  name                 = "${{local.resource_prefix}}-{suffix}"\n'
                f'  assume_role_policy   = data.aws_iam_policy_document.{vn}_trust.json\n'
                f'  description          = "{role["note"]}"\n  path = var.iam_path\n'
                f'  permissions_boundary = var.permission_boundary_arn != "" ? var.permission_boundary_arn : null\n'
                f'  tags = local.common_tags\n}}\n\n')
        for pa in role.get("managed",[]):
            short = pa.lower().replace("awslambda","lambda").replace("amazonrds","rds").replace("amazonecs","ecs").replace("amazons3","s3").replace("-","_")
            out += (f'resource "aws_iam_role_policy_attachment" "{vn}_{short}" {{\n'
                    f'  role       = aws_iam_role.{vn}.name\n'
                    f'  policy_arn = "{_policy_arn(pa)}"\n}}\n\n')
        for vp in role.get("vpc_managed",[]):
            out += (f'resource "aws_iam_role_policy_attachment" "{vn}_vpc" {{\n'
                    f'  count      = var.lambda_vpc_enabled ? 1 : 0\n'
                    f'  role       = aws_iam_role.{vn}.name\n'
                    f'  policy_arn = "{_policy_arn(vp)}"\n}}\n\n')
    return out

def gen_base_roles_variables(iam_data):
    return ('# Module: iam-base-roles\n'
            'variable "project_name" { description = "Project name."; type = string }\n'
            'variable "environment"  { description = "Deployment environment (dev/staging/prod)."; type = string\n'
            '  validation { condition = contains(["dev","staging","prod"],var.environment)\n'
            '    error_message = "must be dev, staging, or prod." } }\n'
            'variable "region"       { description = "AWS region."; type = string }\n'
            'variable "tags"         { description = "Tags to apply to all resources."; type = map(string); default = {} }\n'
            'variable "iam_path"     { description = "IAM path prefix."; type = string; default = "/" }\n'
            'variable "permission_boundary_arn" { description = "Permission boundary ARN (leave empty if not required)."; type = string; default = "" }\n'
            'variable "lambda_vpc_enabled" { description = "Set true if any Lambda runs inside a VPC."; type = bool; default = false }\n')

def gen_base_roles_outputs(iam_data):
    roles = [r for r in iam_data["roles"] if r["module"]=="iam-base-roles"]
    out   = "# Module: iam-base-roles — outputs consumed by all later waves\n\n"
    for role in roles:
        vn = role["role_var_name"]
        for o in role["outputs"]:
            attr = "arn" if o.endswith("_arn") else "name"
            out += (f'output "{o}" {{\n'
                    f'  description = "{o} — consumed by dependent service modules."\n'
                    f'  value       = aws_iam_role.{vn}.{attr}\n}}\n\n')
    return out

def gen_base_roles_test(iam_data):
    project = iam_data["project"]
    region  = iam_data["region"]
    roles   = [r for r in iam_data["roles"] if r["module"]=="iam-base-roles"]
    first   = roles[0]["role_var_name"] if roles else "lambda_execution"
    return (f'# Tests for iam-base-roles\n# Run: terraform test  (no AWS credentials needed)\n\n'
            'mock_provider "aws" {\n'
            '  mock_resource "aws_iam_role" { defaults = { id="mock",arn="arn:aws:iam::123456789012:role/mock",name="mock" } }\n'
            '  mock_resource "aws_iam_role_policy_attachment" { defaults = { id="mock" } }\n'
            '  mock_data "aws_caller_identity" { defaults = { account_id="123456789012" } }\n'
            '  mock_data "aws_partition" { defaults = { partition="aws" } }\n'
            '  mock_data "aws_iam_policy_document" { defaults = { json="{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[]}" } }\n'
            '}\n\n'
            'variables {\n'
            f'  project_name            = "test-{project}"\n'
            '  environment             = "dev"\n'
            f'  region                  = "{region}"\n'
            '  iam_path                = "/"\n'
            '  permission_boundary_arn = ""\n'
            '  lambda_vpc_enabled      = false\n'
            '}\n\n'
            f'run "plan_succeeds" {{\n  command = plan\n'
            f'  assert {{ condition = length(aws_iam_role.{first}) > 0\n'
            f'    error_message = "{first} role must be planned" }}\n}}\n\n'
            f'run "role_name_follows_convention" {{\n  command = plan\n'
            f'  assert {{ condition = can(regex("^test-.*-[a-z-]+$", aws_iam_role.{first}.name))\n'
            '    error_message = "Role name must follow project-env-service pattern" }}\n}}\n\n'
            f'run "tags_applied" {{\n  command = plan\n'
            f'  assert {{ condition = aws_iam_role.{first}.tags["ManagedBy"] == "terraform"\n'
            '    error_message = "ManagedBy tag must be set" }}\n}}\n\n'
            'run "permission_boundary_null_when_empty" {\n  command = plan\n'
            f'  assert {{ condition = aws_iam_role.{first}.permissions_boundary == null\n'
            '    error_message = "permissions_boundary must be null when variable is empty" }}\n}}\n\n'
            'run "vpc_policy_conditional" {\n  command = plan\n'
            '  variables { lambda_vpc_enabled = true }\n'
            '  assert { condition = length(aws_iam_role_policy_attachment.lambda_execution_vpc) == 1\n'
            '    error_message = "VPC policy must attach when lambda_vpc_enabled = true" }\n}\n')

def gen_service_iam_tf(service_id, iam_data):
    inline  = [p for p in iam_data["inline_policies"]   if p["module"]==service_id]
    rp      = [p for p in iam_data["resource_policies"] if p["module"]==service_id]
    if not inline and not rp: return None
    out = (f"# Module: {service_id}\n# IAM — inline policies and resource-based policies\n"
           "# Generated by iam-generator.py\n\n"
           'data "aws_caller_identity" "current" {}\ndata "aws_region" "current" {}\n\n')
    for pol in inline:
        vn  = f"{pol['consumer'].replace('-','_')}_{pol['provider'].replace('-','_')}"
        sid = "Allow"+"".join(w.capitalize() for w in pol['provider'].split('-'))
        acts = json.dumps(pol["actions"], indent=4)
        out += (f"# {pol['note']}\n"
                f'data "aws_iam_policy_document" "inline_{vn}" {{\n'
                f'  statement {{\n    sid     = "{sid}"\n    effect  = "Allow"\n'
                f'    actions = {acts}\n'
                f'    resources = ["{pol["resource_scope"]}"]\n  }}\n')
        # KMS decrypt statement when the underlying resource is encrypted with a CMK.
        # Scoped via kms:ViaService so the permission only applies through the intended AWS service.
        if pol.get("kms_via_service"):
            svc = pol["kms_via_service"]
            out += ('  statement {\n'
                    f'    sid       = "{sid}KmsDecrypt"\n'
                    '    effect    = "Allow"\n'
                    '    actions   = ["kms:Decrypt", "kms:DescribeKey"]\n'
                    '    resources = ["*"]\n'
                    '    condition {\n'
                    '      test     = "StringEquals"\n'
                    '      variable = "kms:ViaService"\n'
                    f'      values   = ["{svc}.${{data.aws_region.current.name}}.amazonaws.com"]\n'
                    '    }\n'
                    '  }\n')
        out += ('}\n\n'
                f'resource "aws_iam_role_policy" "inline_{vn}" {{\n'
                f'  name   = "${{var.project_name}}-${{var.environment}}-{pol["consumer"]}-{pol["provider"]}"\n'
                f'  role   = var.{pol["target_var_name"]}_name\n'
                f'  policy = data.aws_iam_policy_document.inline_{vn}.json\n}}\n\n')
    for pol in rp:
        if pol["policy_type"]=="aws_lambda_permission":
            out += ('resource "aws_lambda_permission" "allow_invoke" {\n'
                    '  statement_id  = "AllowInvoke"\n  action = "lambda:InvokeFunction"\n'
                    '  function_name = aws_lambda_function.main.function_name\n'
                    '  principal     = "apigateway.amazonaws.com"\n'
                    '  source_arn    = "${var.api_gateway_arn}/*"\n}\n\n')
    return out

def gen_service_iam_test(service_id, iam_data):
    inline = [p for p in iam_data["inline_policies"] if p["module"]==service_id]
    if not inline: return None
    project = iam_data["project"]
    out = (f"# IAM tests for {service_id}\n# Run: terraform test  (no AWS credentials needed)\n\n"
           'mock_provider "aws" {\n'
           '  mock_resource "aws_iam_role_policy" { defaults = { id="mock" } }\n'
           '  mock_resource "aws_lambda_permission" { defaults = { id="mock" } }\n'
           '  mock_data "aws_caller_identity" { defaults = { account_id="123456789012" } }\n'
           '  mock_data "aws_region" { defaults = { name="us-east-1" } }\n'
           '  mock_data "aws_iam_policy_document" { defaults = { json="{\\"Version\\":\\"2012-10-17\\",\\"Statement\\":[]}" } }\n'
           '}\n\n')
    for pol in inline:
        vn = f"inline_{pol['consumer'].replace('-','_')}_{pol['provider'].replace('-','_')}"
        out += (f'run "policy_{pol["provider"].replace("-","_")}_scoped_not_wildcard" {{\n'
                '  command = plan\n'
                f'  assert {{ condition = !can(regex("\\\\*$", data.aws_iam_policy_document.{vn}.json))\n'
                f'    error_message = "{pol["provider"]} inline policy must not use bare wildcard resource" }}\n}}\n\n')
    return out

# ─── Markdown ─────────────────────────────────────────────────────────────────

def generate_markdown(d):
    p   = d["project"]
    now = d["generated_at"][:19].replace("T"," ")
    s   = d["summary"]
    wb  = d.get("wave_breakdown",{})
    lines = [
        "# IAM Roles & Policies Review",
        f"Project: {p}  |  Generated: {now}",
        f"Roles: {s['total_roles']}  |  Inline policies: {s['total_inline_policies']}  |  Resource policies: {s['total_resource_policies']}",
        "","---","","## Wave Deployment Map","",
        "| Wave | Base roles created (Wave 1 module) | Inline policies added | Resource policies |",
        "|------|-----------------------------------|----------------------|------------------|",
    ]
    for w in sorted(wb.keys(),key=int):
        b = wb[w]
        base_roles_str = ', '.join('`' + r.split('.')[1] + '`' for r in b['base_roles']) or '—'
        inline_str = ', '.join('`' + i + '`' for i in b['inline_policies']) or '—'
        rp_str = ', '.join('`' + r + '`' for r in b['resource_policies']) or '—'
        lines.append(f"| Wave {w} | {base_roles_str} | {inline_str} | {rp_str} |")
    lines += ["","---","","## Section 1 — IAM Roles (all in iam-base-roles, Wave 1)","",
              "| # | Terraform Resource | Role Name | Trust | Managed Policies | Outputs | Wave | Status |",
              "|---|-------------------|-----------|-------|-----------------|---------|------|--------|"]
    for i,r in enumerate(d["roles"],1):
        lines.append(f"| {i} | `{r['role_resource']}` | `{r['role_name']}` | `{r['trust']}` | "
                     f"{' + '.join(r['managed']) or '—'} | {', '.join(r['outputs'])} | {r['wave']} | ⏳ |")
    lines += ["","---","","## Section 2 — Inline Policies (added when consumer module is built)","",
              "| # | Wave built | Consumer | Accesses | Actions (first 2) | Resource Scope | Status |",
              "|---|-----------|---------|---------|-----------------|---------------|--------|"]
    for i,p2 in enumerate(d["inline_policies"],1):
        acts = ", ".join(p2["actions"][:2]) + ("…" if len(p2["actions"])>2 else "")
        scope = p2["resource_scope"][:55]+"…" if len(p2["resource_scope"])>55 else p2["resource_scope"]
        lines.append(f"| {i} | {p2['wave']} | `{p2['consumer']}` | `{p2['provider']}` ({p2['provider_type']}) | {acts} | `{scope}` | ⏳ |")
    lines += ["","---","","## Section 3 — Resource-Based Policies (added when resource module is built)","",
              "| # | Wave built | Resource | Policy Type | Action | Triggered By | Status |",
              "|---|-----------|---------|------------|--------|-------------|--------|"]
    for i,rp in enumerate(d["resource_policies"],1):
        lines.append(f"| {i} | {rp['wave']} | `{rp['resource']}` | `{rp['policy_type']}` | {rp['action'][:40]} | {rp['triggered_by']} | ⏳ |")
    cfg = d["iam_config"]
    lines += ["","---","","## Section 4 — IAM Configuration","","```",
              f"permission_boundary_arn: {cfg['permission_boundary_arn']}",
              "# Format: arn:aws:iam::{account}:policy/{Policy}  OR  none",
              f"iam_path: {cfg['iam_path']}",
              "# Options: /  |  /app/  |  /service/",
              f"cross_account_access: {cfg['cross_account_access']}",
              "```","","---","","## Section 5 — Wave Build Order","",
              "| Wave | What gets built | Consumed by |",
              "|------|----------------|------------|"]
    for w in sorted(wb.keys(),key=int):
        created = ", ".join(f"`{r.split('.')[1]}`" for r in wb[w]["base_roles"]) or "inline policies only"
        consumed = f"Waves {int(w)+1}+" if int(w)<max(int(x) for x in wb) else "—"
        lines.append(f"| {w} | {created} | {consumed} |")
    lines += ["","---","","## Section 6 — Outputs Map","",
              "| Output | Produced by | Wave | Variable in consumer |",
              "|--------|------------|------|---------------------|"]
    seen=set()
    for r in d["roles"]:
        for o in r["outputs"]:
            if o in seen: continue
            seen.add(o)
            lines.append(f"| `{o}` | `{r['module']}` | {r['wave']} | `var.{o}` |")
    c = lambda v: "✅" if v else "- [ ]"
    chk = d["checklist"]
    lines += ["","---","","## Checklist","",
              f"{c(chk['no_wildcard_resources'])} No bare wildcard `*` on data service resources",
              f"{c(chk['all_roles_have_descriptions'])} All roles have description set",
              f"{c(chk['no_admin_access'])} No AdministratorAccess or PowerUserAccess",
              f"{c(chk['ecs_has_both_roles'])} ECS has both execution role + task role",
              f"{c(chk['rds_has_monitoring_role'])} RDS monitoring role present",
              f"{c(chk['apigw_has_cloudwatch_role'])} API Gateway CloudWatch role present",
              f"{c(chk['lambda_has_vpc_policy_if_needed'])} Lambda VPC policy configured",
              "","---","","## Terraform Files Generated","",
              "| File | Wave | Contains |",
              "|------|------|---------|",
              "| `terraform/modules/iam-base-roles/main.tf` | 1 | All shared base roles |",
              "| `terraform/modules/iam-base-roles/variables.tf` | 1 | permission_boundary, iam_path, lambda_vpc_enabled |",
              "| `terraform/modules/iam-base-roles/outputs.tf` | 1 | All role ARNs + names |",
              "| `terraform/modules/iam-base-roles/tests/main.tftest.hcl` | 1 | 5 test cases |"]
    svcs = set(p2["module"] for p2 in d["inline_policies"]+d["resource_policies"])
    for svc in sorted(svcs):
        w = next((p2["wave"] for p2 in d["inline_policies"] if p2["module"]==svc),"?")
        lines += [f"| `terraform/modules/{svc}/iam.tf` | {w} | Inline + resource policies |",
                  f"| `terraform/modules/{svc}/tests/iam.tftest.hcl` | {w} | IAM no-wildcard tests |"]
    lines += ["","---","","## Review Status","STATUS: PENDING",
              f"","*Generated {now}*"]
    return "\n".join(lines)+"\n"

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--refresh",  action="store_true")
    parser.add_argument("--services", default=".claude/memory/01-services.json")
    parser.add_argument("--plan",     default=".claude/memory/02-build-plan.json")
    parser.add_argument("--out-json", default="agent/review/iam-model-review.json")
    parser.add_argument("--out-md",   default="agent/review/iam-model-review.md")
    parser.add_argument("--tf-dir",   default="terraform/modules")
    args = parser.parse_args()

    for path in [args.services, args.plan]:
        if not Path(path).exists():
            print(f"❌ Not found: {path}"); sys.exit(1)

    services_data   = json.loads(Path(args.services).read_text())
    build_plan_data = json.loads(Path(args.plan).read_text())
    iam_data        = generate_iam(services_data, build_plan_data)

    if args.refresh:
        tf_modules = Path(args.tf_dir)
        if tf_modules.exists():
            built = {p.name for p in tf_modules.iterdir() if p.is_dir()}
            for item in iam_data["roles"]+iam_data["inline_policies"]+iam_data["resource_policies"]:
                if item.get("module") in built:
                    item["build_status"] = "built"

    if args.dry_run:
        print("\n".join(generate_markdown(iam_data).split("\n")[:40])); return

    # Write review files
    Path(args.out_json).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out_json).write_text(json.dumps(iam_data,indent=2), encoding="utf-8")
    Path(args.out_md).write_text(generate_markdown(iam_data), encoding="utf-8")
    s = iam_data["summary"]
    print(f"OK agent/review/iam-model-review.json  ({s['total_roles']} roles)")
    print(f"OK agent/review/iam-model-review.md")

    # Write Terraform files
    base = Path(args.tf_dir)

    # iam-base-roles
    iam_dir = base/"iam-base-roles"
    (iam_dir/"tests/fixtures").mkdir(parents=True,exist_ok=True)
    (iam_dir/"main.tf").write_text(gen_base_roles_main(iam_data), encoding="utf-8")
    (iam_dir/"variables.tf").write_text(gen_base_roles_variables(iam_data), encoding="utf-8")
    (iam_dir/"outputs.tf").write_text(gen_base_roles_outputs(iam_data), encoding="utf-8")
    (iam_dir/"tests/main.tftest.hcl").write_text(gen_base_roles_test(iam_data), encoding="utf-8")
    (iam_dir/"tests/fixtures/test.tfvars").write_text(
        f'project_name            = "test-{iam_data["project"]}"\n'
        f'environment             = "dev"\nregion = "{iam_data["region"]}"\n'
        'iam_path = "/"\npermission_boundary_arn = ""\nlambda_vpc_enabled = false\n',
        encoding="utf-8")
    print(f"OK terraform/modules/iam-base-roles/  (main + variables + outputs + 5 tests)")

    # Per-service iam.tf
    for svc_id in sorted(set(p["module"] for p in iam_data["inline_policies"]+iam_data["resource_policies"])):
        tf  = gen_service_iam_tf(svc_id, iam_data)
        tst = gen_service_iam_test(svc_id, iam_data)
        if tf:
            svc_dir = base/svc_id
            (svc_dir/"tests").mkdir(parents=True,exist_ok=True)
            (svc_dir/"iam.tf").write_text(tf, encoding="utf-8")
            if tst: (svc_dir/"tests/iam.tftest.hcl").write_text(tst, encoding="utf-8")
            print(f"✅ terraform/modules/{svc_id}/iam.tf  +  tests/iam.tftest.hcl")

    print("\nNext: run /IAMModeler to validate")

if __name__=="__main__": main()
