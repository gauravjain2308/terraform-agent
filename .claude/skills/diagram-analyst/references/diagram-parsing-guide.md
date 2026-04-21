# Draw.io Diagram Parsing Guide

Draw.io exports are XML files. This guide explains how to extract infrastructure components.

---

## XML Structure

```xml
<mxGraphModel>
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <!-- All real cells below -->
    <mxCell id="2" value="api-gateway" style="shape=mxgraph.aws4.resourceIcon;..." vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="78" height="78" as="geometry" />
    </mxCell>
    <mxCell id="3" value="lambda-auth" style="shape=mxgraph.aws4.resourceIcon;..." vertex="1" parent="1">
      <mxGeometry x="300" y="100" width="78" height="78" as="geometry" />
    </mxCell>
    <!-- Edge connecting them -->
    <mxCell id="4" value="" edge="1" source="2" target="3" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```

---

## Extraction Rules

### Identifying Services (Nodes)
A cell is a **service/component** if it has `vertex="1"` and a non-empty `value` attribute.

```python
# Pseudocode
for cell in root.findall('.//mxCell'):
    if cell.get('vertex') == '1' and cell.get('value'):
        label = cell.get('value')
        style = cell.get('style', '')
        service_id = cell.get('id')
        tooltip = cell.get('tooltip', '')
        # identify type from style string (see below)
```

### Identifying Connections (Edges)
A cell is a **connection** if it has `edge="1"`.

```python
for cell in root.findall('.//mxCell'):
    if cell.get('edge') == '1':
        source_id = cell.get('source')
        target_id = cell.get('target')
        label = cell.get('value', '')  # e.g. "HTTPS", "SQL", "triggers"
```

---

## Inferring Service Type from Style String

The `style` attribute contains shape identifiers. Match against these patterns:

| Style contains | Inferred Type | Terraform resource prefix |
|----------------|---------------|--------------------------|
| `aws4.api_gateway` | API Gateway (REST) | `aws_api_gateway_rest_api` |
| `aws4.apigateway2` | API Gateway (HTTP/v2) | `aws_apigatewayv2_api` |
| `aws4.lambda` | Lambda Function | `aws_lambda_function` |
| `aws4.rds` | RDS Instance | `aws_db_instance` |
| `aws4.aurora` | Aurora Cluster | `aws_rds_cluster` |
| `aws4.dynamodb` | DynamoDB Table | `aws_dynamodb_table` |
| `aws4.s3` | S3 Bucket | `aws_s3_bucket` |
| `aws4.sns` | SNS Topic | `aws_sns_topic` |
| `aws4.sqs` | SQS Queue | `aws_sqs_queue` |
| `aws4.elasticache` | ElastiCache | `aws_elasticache_cluster` |
| `aws4.vpc` | VPC | `aws_vpc` |
| `aws4.subnet` | Subnet | `aws_subnet` |
| `aws4.security_group` | Security Group | `aws_security_group` |
| `aws4.iam_role` | IAM Role | `aws_iam_role` |
| `aws4.cloudfront` | CloudFront | `aws_cloudfront_distribution` |
| `aws4.route53` | Route53 | `aws_route53_record` |
| `aws4.eks` | EKS Cluster | `aws_eks_cluster` |
| `aws4.ecs` | ECS Service | `aws_ecs_service` |
| `aws4.ecr` | ECR Repository | `aws_ecr_repository` |
| `aws4.secretsmanager` | Secrets Manager | `aws_secretsmanager_secret` |
| `aws4.kms` | KMS Key | `aws_kms_key` |
| `aws4.cloudwatch` | CloudWatch | `aws_cloudwatch_log_group` |
| `mxgraph.azure` | Azure resource | (see azure.md) |
| `mxgraph.gcp` | GCP resource | (see gcp.md) |
| Generic box/rect | Unknown | Flag for user clarification |

### Fallback when style is unclear:
- Check the `value` (label) text for keywords: "db", "database", "cache", "queue", "bucket", "gateway", "lambda", "function"
- Add to the **Ambiguities** section in Phase 2 output

---

## Extracting Config from Tooltips

Draw.io tooltips often contain extra config. Parse them for hints:

| Tooltip contains | Extract as |
|-----------------|------------|
| `port=3306` | database port |
| `engine=postgres` | db engine type |
| `runtime=python3.11` | lambda runtime |
| `memory=512` | lambda memory MB |
| `multi-az` | RDS multi-AZ flag |
| `encrypted` | enable encryption |
| `public` | public-facing resource |
| `private` | internal-only resource |

---

## Handling Groups / Containers

Draw.io often uses container cells (with `children`) to show VPCs, subnets, or availability zones.

```xml
<mxCell id="10" value="VPC" style="swimlane;..." vertex="1">
  <!-- children cells inside represent subnets or resources IN the VPC -->
</mxCell>
```

- A container with label "VPC" → create `aws_vpc` + implied `aws_subnet` children
- A container with label "Public Subnet" / "Private Subnet" → create `aws_subnet`
- Cells inside a container → those services belong to that network segment

---

## Common Diagram Patterns

### Three-tier web app
```
[Route53] → [CloudFront] → [ALB] → [ECS/Lambda] → [RDS]
                                 ↓
                            [ElastiCache]
```

### Serverless API
```
[API Gateway] → [Lambda] → [DynamoDB]
                    ↓
               [S3 bucket]
               [SNS/SQS]
```

### Microservices
```
[API Gateway] → [Lambda A] → [SQS] → [Lambda B] → [RDS]
              → [Lambda C] → [DynamoDB]
```

---

## When Diagram is Ambiguous

Always log ambiguities clearly. Do not silently assume — surface them in Phase 2:

```markdown
## Ambiguities Found in Diagram

1. Cell id="42" has label "DB" with no style identifier
   → Assuming RDS PostgreSQL. Please confirm or specify (MySQL / Aurora / DynamoDB / other)

2. Two unlabeled arrow connections found between Lambda-A and Lambda-B
   → Unclear if synchronous invoke or async via SQS. Please clarify.

3. No VPC container found in diagram
   → Assuming all compute resources in a single VPC. Please confirm.
```
