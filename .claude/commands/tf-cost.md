# /tf-cost — Cost Estimation Before Apply

Run infracost against the current Terraform plan and show estimated monthly AWS costs.
Always run this before `make apply` so you know what you're about to spend.

## Step 1 — Load state

Read `.claude/memory/tf-state.json`.

If no state found or gates not confirmed:
```
❌ No confirmed Terraform project found.
   Complete all three gates first, then run /ServiceBuilder to generate modules.
```

Show banner: `📂 {project_name}  |  {phase}  |  Cost Estimation`

## Step 2 — Check infracost is installed

Run:
```bash
infracost --version
```

If not installed, show installation instructions and stop:
```
❌ infracost is not installed.

Install it first:
  brew install infracost

Then register for a free API key:
  infracost auth login

Then run /tf-cost again.

infracost is free for individual use. It calls the AWS pricing API
to estimate costs without actually creating any resources.
```

## Step 3 — Check environments/dev/terraform.tfvars exists

If missing:
```
❌ environments/dev/terraform.tfvars not found.
Run: make setup
This copies terraform.tfvars.example and runs terraform init.
```

## Step 4 — Run terraform plan to get a plan file

```bash
cd environments/dev
terraform init -backend=false
terraform plan -out=tf-cost.plan -no-color
```

Write any plan errors to chat and stop if plan fails.

Show in chat: `✅ Plan generated — running cost analysis...`

## Step 5 — Run infracost breakdown

```bash
cd environments/dev
infracost breakdown \
  --path tf-cost.plan \
  --format table \
  --no-color \
  2>&1
```

Capture the full output.

## Step 6 — Parse and display results

Show the full infracost table in chat, then add a summary section:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰  Cost Estimate — {project_name} (dev)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{full infracost table output here}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊  Summary

  Estimated monthly cost:   ${total}/month
  Estimated hourly cost:    ${hourly}/hour

  Most expensive resources:
    {resource_name}   ${cost}/month   ({percentage}% of total)
    {resource_name}   ${cost}/month
    {resource_name}   ${cost}/month

  Free tier eligible:
    {list any resources covered by AWS free tier}

  ⚠️  Note: Estimates are based on on-demand pricing.
     Actual costs may vary based on usage, data transfer,
     and any existing reserved instances or savings plans.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cost acceptable?

  To apply:      make plan-save  then  make apply
  To see detail: infracost breakdown --path environments/dev/tf-cost.plan
  To compare envs: /tf-cost will run against prod if you switch

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 7 — Flag cost concerns

After showing the estimate, analyse it and flag anything notable:

**High cost warnings** (show if applicable):
```
⚠️  HIGH COST ITEMS FLAGGED:

  • rds-users (db.r6g.large) — $180/month
    Consider db.t3.medium for dev to save ~$155/month
    Change in: review/03_inputs_collection.md → db_instance_class

  • nat-gateway — $45/month
    1 NAT gateway charged per AZ. Using single_nat_gateway=true in dev saves ~$45/month
    Change in: review/03_inputs_collection.md → single_nat_gateway
```

**Cost optimisation suggestions** (always show):
```
💡  Cost optimisation tips for dev:

  • Use db.t3.medium instead of db.r6g.large in dev   saves ~$155/month
  • Set single_nat_gateway=true in dev                saves ~$45/month
  • Use lambda arm64 architecture (already set ✅)     5-20% cheaper
  • Reserved instances for prod RDS                   saves up to 40%
```

**Unexpected resources** (show if plan includes things the user might not expect):
```
⚠️  UNEXPECTED RESOURCES IN PLAN:

  These resources were not in your original diagram — verify they're intentional:
  • aws_cloudwatch_log_group.lambda_auth_logs
  • aws_secretsmanager_secret.rds_password
  (These are created automatically by the skill for security best practices)
```

## Step 8 — Save cost report

Write the full cost report to `agent/execution.md` under a `## Cost Estimate` section.
Write a summary to `.claude/memory/cost-estimate.json`:
```json
{
  "estimated_at": "<timestamp>",
  "environment": "dev",
  "monthly_total": "$XX.XX",
  "hourly_total": "$X.XX",
  "most_expensive": [
    {"resource": "...", "cost": "$XX.XX"},
    {"resource": "...", "cost": "$XX.XX"}
  ],
  "warnings": []
}
```

## Step 9 — Clean up plan file

```bash
rm -f environments/dev/tf-cost.plan
```

## Note — do NOT end with /clear

Cost estimation is informational. User needs to read the output and decide.
Do not tell them to /clear — they should be able to ask follow-up questions
about specific costs or optimisations.
