# Phase 2 — Extraction Output Format

Build a structured inventory from parsed inputs and show it to the user before Review Gate 1.

```markdown
## Extracted Services

| # | Raw Label (from diagram) | Inferred Type | Cloud Provider | Notes |
|---|--------------------------|---------------|----------------|-------|
| 1 | "api-gw"                 | API Gateway   | AWS            | REST  |
| 2 | "lambda-auth"            | Lambda        | AWS            | Auth handler |
| 3 | "users-db"               | RDS           | AWS            | PostgreSQL |
...

## Extracted Connections

| From        | To          | Type        | Notes              |
|-------------|-------------|-------------|--------------------|
| api-gw      | lambda-auth | invokes     |                    |
| lambda-auth | users-db    | reads/writes| needs sg rule      |
...

## Ambiguities / Assumptions
- "cache" label — assuming ElastiCache Redis (confirm if different)
- No VPC shown — assuming all services in single VPC (confirm)
```
