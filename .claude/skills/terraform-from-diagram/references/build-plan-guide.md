# Phase 4 — Dependency Graph & Build Plan

## Ordering Rules

**Default: one service per wave.**

Each service occupies its own wave. A wave contains multiple services ONLY when those services have circular/mutual dependencies that make it impossible to deploy them independently. This is the *minimum mandatory cluster* exception.

### Wave Assignment Algorithm

1. Build a directed dependency graph from the confirmed service connections.
2. **Detect circular dependencies** (strongly connected components with >1 node) — these services MUST share a wave.
3. **Topological sort** the remaining services (and any circular-dep clusters as single units) to produce a total build order.
4. Assign wave numbers in sort order: each position = one wave.
5. When multiple services are independent of each other (no direct or indirect dependency between them), order them using this priority:
   - Networking/VPC first
   - IAM/KMS next
   - Databases, queues, cache, storage
   - Compute (Lambda, ECS, EC2)
   - Edge/gateway last (API GW, CloudFront, ALB)

### Key Constraints

- **Fewer services per wave is always better.** Never group independent services into the same wave.
- **Wave N+1 starts only after all Wave N services are `COMPLETE`.** Sequential ordering = clearer blast radius on failure.
- **Exception only for circular deps.** If Service A depends on Service B AND B depends on A, they share a wave — there is no other way to deploy them.

## Output Format

```markdown
## Build Plan — Service Order

Wave 1 (No dependencies):
  - [x] networking/vpc

Wave 2 (No dependencies):
  - [x] iam/base-roles

Wave 3 (Depends on Wave 1):
  - [ ] database/rds-users

Wave 4 (Depends on Wave 1):
  - [ ] storage/s3-assets

Wave 5 (Depends on Wave 2, 3):
  - [ ] compute/lambda-auth

Wave 6 (Depends on Wave 5):
  - [ ] gateway/api-gw

## Module Dependency Map
networking/vpc → database/rds-users (subnet_ids, vpc_id)
iam/base-roles → compute/lambda-auth (execution_role_arn)
...
```
