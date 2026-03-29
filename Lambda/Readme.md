# AWS Lambda (Serverless Compute)

**Python boto3 code:** [lambda_operations.py](./lambda_operations.py)

---

## Table of Contents

1. [What is AWS Lambda?](#1-what-is-aws-lambda)
2. [Core Concepts](#2-core-concepts)
3. [Lambda Execution Model](#3-lambda-execution-model)
4. [Lambda Function Anatomy](#4-lambda-function-anatomy)
5. [Event Sources & Integrations](#5-event-sources--integrations)
6. [IAM & Security](#6-iam--security)
7. [Packaging & Deployment Models](#7-packaging--deployment-models)
8. [Environment Variables & Configuration](#8-environment-variables--configuration)
9. [Versions, Aliases, and Traffic Shifting](#9-versions-aliases-and-traffic-shifting)
10. [Concurrency, Scaling, and Throttling](#10-concurrency-scaling-and-throttling)
11. [Timeout, Memory, CPU, and Ephemeral Storage](#11-timeout-memory-cpu-and-ephemeral-storage)
12. [Observability & Debugging](#12-observability--debugging)
13. [VPC Networking with Lambda](#13-vpc-networking-with-lambda)
14. [Error Handling, Retries, and DLQs](#14-error-handling-retries-and-dlqs)
15. [Event-Driven Architectures](#15-event-driven-architectures)
16. [Performance Optimization](#16-performance-optimization)
17. [Lambda Pricing Model](#17-lambda-pricing-model)
18. [CLI Cheat Sheet](#18-cli-cheat-sheet)
19. [Best Practices](#19-best-practices)
20. [Advanced Topics](#20-advanced-topics)

---

## 1. What is AWS Lambda?

**AWS Lambda** is a serverless compute service that runs your code in response to events and automatically manages the underlying infrastructure.

### Key Characteristics

- **Serverless** - No servers to provision or manage.
- **Event-driven** - Runs when triggered by events (S3, API Gateway, EventBridge, etc.).
- **Auto-scaling** - Scales from zero to many concurrent executions automatically.
- **Pay-per-use** - You pay for requests and execution duration, not idle capacity.
- **Multi-language** - Supports Python, Node.js, Java, .NET, Go, Ruby, and custom runtimes.

### When to Use Lambda

| Use Case | Why Lambda Fits |
|----------|-----------------|
| API backends | Integrates with API Gateway, scales automatically |
| File processing | Trigger from S3 object upload events |
| Data pipelines | Works with SQS, Kinesis, DynamoDB streams |
| Automation | EventBridge schedules and rule-based actions |
| Glue logic | Lightweight orchestration across AWS services |

### Lambda vs EC2 (Quick View)

| Aspect | Lambda | EC2 |
|--------|--------|-----|
| Infra management | Fully managed | You manage instances |
| Scaling | Automatic | Auto Scaling Groups/manual |
| Billing | Per request + duration | Per running instance |
| Max execution | 15 minutes | No hard 15-min function limit |
| Best for | Event-driven workloads | Long-running/stateful workloads |

---

## 2. Core Concepts

### 2.1 Function
A **function** is your code plus runtime configuration (memory, timeout, IAM role, etc.).

### 2.2 Event
An **event** is the input payload passed to your function.

### 2.3 Trigger
A **trigger** is the service/configuration that invokes your function.

### 2.4 Execution Environment
Lambda runs your code inside an isolated runtime environment managed by AWS.

### 2.5 Handler
The **handler** is the entry point Lambda calls, such as:

```text
Python: module_name.function_name
Example: app.lambda_handler
```

---

## 3. Lambda Execution Model

### 3.1 Invocation Lifecycle

```text
Event arrives
   -> Lambda service selects/creates execution environment
   -> Runtime initializes code (cold start if new environment)
   -> Handler executes
   -> Response returned (sync) or acknowledged (async/stream)
```

### 3.2 Cold Start vs Warm Start

- **Cold start**: New environment initialization (code load + runtime init).
- **Warm start**: Reuse of existing environment; lower latency.

Cold start impact depends on runtime, package size, VPC config, and initialization code.

### 3.3 Stateless by Design

- Each invocation should be treated as independent.
- In-memory state can persist only within the same warm environment, not guaranteed.
- Persist state in external services: DynamoDB, S3, ElastiCache, RDS, etc.

---

## 4. Lambda Function Anatomy

### 4.1 Python Function Example

```python
import json
import os

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Hello from Lambda",
            "function": context.function_name,
            "request_id": context.aws_request_id,
            "env": os.environ.get("APP_ENV", "dev")
        })
    }
```

### 4.2 Context Object (Python)

| Field | Description |
|-------|-------------|
| `function_name` | Name of the Lambda function |
| `function_version` | Version being executed |
| `memory_limit_in_mb` | Configured memory |
| `invoked_function_arn` | Invoked ARN |
| `aws_request_id` | Unique request ID |
| `get_remaining_time_in_millis()` | Remaining execution time |

---

## 5. Event Sources & Integrations

### 5.1 Synchronous Invocation
Caller waits for response.

Examples:
- API Gateway
- ALB
- Lambda Function URLs
- AWS SDK invoke (`RequestResponse`)

### 5.2 Asynchronous Invocation
Lambda queues event and processes later.

Examples:
- S3 event notifications
- SNS
- EventBridge
- AWS SDK invoke (`Event`)

### 5.3 Poll-based Event Source Mappings
Lambda polls source and invokes function with batches.

Examples:
- SQS
- Kinesis Data Streams
- DynamoDB Streams
- Amazon MQ / MSK

### 5.4 Common Integration Patterns

| Source | Pattern | Notes |
|--------|---------|-------|
| API Gateway | Request/response | Build serverless REST APIs |
| S3 | Object-created triggers | Thumbnails, ETL, validation |
| SQS | Queue consumer | Retry + DLQ support |
| EventBridge | Event bus routing | Decoupled event-driven systems |
| Step Functions | Workflow tasks | Reliable orchestration |

---

## 6. IAM & Security

### 6.1 Execution Role
Each function runs with an IAM role granting permissions to other AWS services.

Minimum approach:
- Start with least privilege
- Add only required actions/resources

Example policy for reading one S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::my-input-bucket/*"
    }
  ]
}
```

### 6.2 Resource-Based Policies
Allow other principals/services to invoke your function.

Typical use:
- Grant API Gateway or EventBridge permission to invoke Lambda.

### 6.3 Encryption
- Environment variables encrypted at rest (AWS managed KMS by default).
- Optionally provide a customer managed KMS key.

### 6.4 Secrets
Do not hardcode secrets in code or environment variables when avoidable.
Prefer:
- AWS Secrets Manager
- AWS Systems Manager Parameter Store

---

## 7. Packaging & Deployment Models

### 7.1 ZIP Package (Most Common)
- Code + dependencies zipped and uploaded directly or via S3.
- Max upload package size limits apply.

### 7.2 Container Image
- Package as Docker image and store in ECR.
- Useful for larger dependencies, custom tooling, and consistent build environments.

### 7.3 Layers
- Reusable package of libraries/shared code.
- Attach layer versions to multiple functions.

### 7.4 Infrastructure as Code
Preferred deployment methods:
- AWS SAM
- AWS CDK
- CloudFormation
- Terraform

---

## 8. Environment Variables & Configuration

Common configuration in Lambda:
- Environment (`dev`, `stage`, `prod`)
- Resource names (table, bucket, topic)
- Feature flags

Guidelines:
- Keep config external to code.
- Encrypt sensitive values.
- Validate required variables during init.

---

## 9. Versions, Aliases, and Traffic Shifting

### 9.1 Versions
- `$LATEST`: mutable draft.
- Published versions are immutable snapshots.

### 9.2 Aliases
- Stable pointers to versions (`dev`, `qa`, `prod`).
- Allows controlled promotions.

### 9.3 Weighted Routing
Use aliases for canary/linear releases.

```text
Alias prod:
  90% -> version 10
  10% -> version 11
```

Great for safe deployments and rollback.

---

## 10. Concurrency, Scaling, and Throttling

### 10.1 Account Concurrency
Total concurrent executions available per account-region.

### 10.2 Reserved Concurrency
- Guarantees concurrency for one function.
- Also limits max concurrency for that function.

### 10.3 Provisioned Concurrency
Pre-initializes environments to reduce cold-start latency for critical workloads.

### 10.4 Scaling Notes
- Asynchronous and poll-based sources have source-specific scaling behavior.
- SQS batch and visibility timeout tuning matter for throughput/reliability.

---

## 11. Timeout, Memory, CPU, and Ephemeral Storage

### 11.1 Timeout
- 1 to 900 seconds (15 min max).
- Set slightly above expected execution time.

### 11.2 Memory and CPU
- CPU is proportional to memory.
- Increasing memory may reduce runtime and overall cost.

### 11.3 Ephemeral Storage
- `/tmp` storage configurable (up to 10 GB).
- Useful for temporary files, decompression, and media processing.

---

## 12. Observability & Debugging

### 12.1 CloudWatch Logs
Use structured logging (JSON preferred) and include request IDs.

### 12.2 CloudWatch Metrics
Important metrics:
- `Invocations`
- `Errors`
- `Duration`
- `Throttles`
- `ConcurrentExecutions`
- `IteratorAge` (streams)
- `ApproximateAgeOfOldestMessage` (SQS)

### 12.3 AWS X-Ray
Trace downstream calls and latency breakdown.

### 12.4 Alarms
Set alarms on:
- Error rate
- Duration p95/p99
- Throttles
- DLQ message count

---

## 13. VPC Networking with Lambda

Use VPC only when function needs private resources:
- RDS in private subnet
- ElastiCache
- Private services/endpoints

Considerations:
- Attach function to private subnets + security groups.
- Ensure outbound access if needed via NAT or VPC endpoints.
- Additional network setup can affect startup latency.

---

## 14. Error Handling, Retries, and DLQs

### 14.1 Async Invocations
- Lambda retries asynchronous failures.
- You can configure maximum retry attempts and event age.

### 14.2 Destinations and DLQ
- On failure: send event record to SQS/SNS/EventBridge destination.
- For stream/queue processing, handle partial failures when supported.

### 14.3 Idempotency
Implement idempotency keys to prevent duplicate side effects.

---

## 15. Event-Driven Architectures

### 15.1 Fan-out
SNS or EventBridge distributes one event to multiple subscribers.

### 15.2 Decoupling
SQS buffers bursts and isolates producer from consumer speed.

### 15.3 Orchestration
Use Step Functions for multi-step workflows, retries, and compensation logic.

### 15.4 Choreography
EventBridge-based domain events for loosely coupled services.

---

## 16. Performance Optimization

- Minimize package size and imports.
- Move expensive initialization outside handler (reused in warm starts).
- Reuse SDK/database connections.
- Right-size memory with performance tests.
- Use provisioned concurrency for latency-sensitive endpoints.
- Prefer ARM/Graviton where compatible for better price/performance.

---

## 17. Lambda Pricing Model

Lambda pricing has 3 main components:

1. **Requests** - charged per million requests.
2. **Duration** - GB-seconds (memory x execution time).
3. **Provisioned Concurrency** - additional charge when enabled.

Additional charges may come from:
- Data transfer
- CloudWatch logs
- Connected services (API Gateway, SQS, DynamoDB, etc.)

Optimization levers:
- Reduce execution time
- Tune memory for best cost/perf
- Batch where possible (SQS/Kinesis)

---

## 18. CLI Cheat Sheet

```bash
# Create function (ZIP package)
aws lambda create-function \
  --function-name my-function \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/lambda-exec-role \
  --handler app.lambda_handler \
  --zip-file fileb://function.zip

# Invoke function synchronously
aws lambda invoke \
  --function-name my-function \
  --payload '{"message":"hello"}' \
  response.json

# Update function code
aws lambda update-function-code \
  --function-name my-function \
  --zip-file fileb://function.zip

# Update configuration
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 30 \
  --memory-size 512

# Publish version
aws lambda publish-version --function-name my-function

# Create alias
aws lambda create-alias \
  --function-name my-function \
  --name prod \
  --function-version 1

# Set reserved concurrency
aws lambda put-function-concurrency \
  --function-name my-function \
  --reserved-concurrent-executions 50
```

---

## 19. Best Practices

- Keep functions single-purpose and small.
- Design for idempotency.
- Use least-privilege IAM roles.
- Use aliases and gradual rollout for production releases.
- Add alarms for errors, throttles, and high duration.
- Prefer asynchronous decoupling (SQS/EventBridge) under bursty loads.
- Externalize state and config.
- Test with realistic event payloads and failure scenarios.

---

## 20. Advanced Topics

### 20.1 Lambda Extensions
Run sidecar-like agents for telemetry, security, or secrets retrieval.

### 20.2 SnapStart (Java)
Reduces Java cold starts by snapshotting initialized runtime.

### 20.3 Response Streaming
Useful for low-latency streaming responses in some integration patterns.

### 20.4 Multi-Account, Multi-Region Serverless
- Use infrastructure pipelines for promotion.
- Centralize observability and governance.
- Apply SCPs and IAM boundaries for control.

### 20.5 Event Replay & Backfill Strategies
- Preserve original events in S3/EventBridge archives.
- Reprocess safely with idempotency and controlled concurrency.

---
