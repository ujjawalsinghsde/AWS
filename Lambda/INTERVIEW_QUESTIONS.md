# Lambda Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is AWS Lambda and how does it work?**
   - Answer: Serverless compute service that runs code in response to events. You pay only for compute time used. Lambda manages server provisioning, scaling, and maintenance.

2. **Explain Lambda pricing.**
   - Charged per 1 GB-second of memory used + request count
   - Free tier: 1M requests/month + 400,000 GB-seconds/month
   - Example: 512 MB function = 0.5 GB; 1 second execution = 0.5 GB-seconds

3. **What are Lambda's supported languages and runtimes?**
   - Python, Node.js, Java, C#, Go, Ruby, custom runtimes
   - Deprecated: Python 2.7, Node.js 4.3, 6.10, Java 8
   - Latest runtimes receive automatic patches

4. **Explain Lambda function anatomy:**
   - Handler: Entry point function (e.g., lambda_function.lambda_handler)
   - Event: Input data triggering the function
   - Context: Runtime info (request ID, remaining time, memory)
   - Environment variables: Secure config storage
   - Timeout: Max execution time (15 minutes)

5. **What is a Lambda layer?**
   - Reusable code/libraries packaged separately from function code
   - Supports up to 5 layers per function
   - Common use: Shared dependencies, common utilities

---

## 2. Intermediate Scenario-Based Questions

### Event Sources & Integration
6. **Scenario: You need to process S3 file uploads within 1 second. Which Lambda event source is best?**
   - Answer: S3 event notifications (ObjectCreated) with Lambda destination
   - Alternative: EventBridge for filtering, fanout
   - Avoid: Polling S3 (polling not recommended for S3)
   - Configuration: S3 bucket → Lambda permission → trigger event types

7. **How do you handle long-running tasks with Lambda (>15 minutes)?**
   - Don't use Lambda directly (max 15 min timeout)
   - Solutions:
     - Break into smaller functions + Step Functions orchestration
     - Use Step Functions for coordination
     - Queue work in SQS → ECS/EC2 for processing
     - Use AWS Batch for heavy computation
     - Implement check-pointing and resumption

8. **Scenario: Your Lambda processes sensitive data. How do you secure it?**
   - Use VPC execution role with KMS key access
   - Store secrets in Secrets Manager/Parameter Store
   - Encrypt function code with KMS
   - Enable X-Ray tracing for audit trail
   - Use least-privilege IAM roles
   - Never hardcode credentials
   - Enable CloudTrail logging
   - Use VPC endpoints for private AWS service access

### Concurrency & Throttling
9. **Explain Lambda concurrency and throttling.**
   - **Concurrency**: Max number of simultaneous executions (default 1000)
   - Reserved concurrency: Guarantees capacity for critical functions
   - Provisioned concurrency: Pre-initialized instances avoiding cold starts
   - Throttling: When limit reached, requests are rejected (error rate)

10. **Scenario: You have 1 Lambda handling 10,000 requests/second. It's getting throttled. What's the solution?**
    - Short-term: Increase concurrency limit (request increase)
    - Medium-term: Reserved concurrency for critical traffic
    - Long-term:
      - Use Provisioned Concurrency (keep instances warm)
      - Distribute load with SQS (async processing)
      - Implement Circuit Breaker pattern
      - Use Step Functions to orchestrate parallel execution

### Error Handling & Resilience
11. **How do you handle Lambda failures and retries?**
    - Synchronous invocation: Caller handles errors
    - Asynchronous invocation: 2 automatic retries + DLQ
    - EventBridge: Configurable retry policy (up to 24 hours)
    - SQS: Visibility timeout + DLQ for failed messages
    - Best practice: Implement idempotent functions

12. **Scenario: Lambda fails processing orders. Design a resilient order processing system.**
    - Flow:
      1. API Gateway → Lambda (validation only)
      2. SQS queue for reliable message delivery
      3. Processing Lambda with batch size 10
      4. Database transaction for atomicity
      5. DLQ for failed orders
      6. SNS notification for failures
      7. Lambda for DLQ monitoring + alerts
    - Key: Idempotency key prevents duplicate processing

---

## 3. Advanced Problem-Solving Questions

### Cold Starts & Performance
13. **What is a "cold start" and how do you minimize it?**
    - Cold start: Latency when Lambda container isn't ready (~1-2 seconds)
    - Causes: Version changes, traffic spike, long inactivity
    - Solutions:
      - Provisioned concurrency (keeps instances warm, costs money)
      - Connections outside handler (connection pooling)
      - Language choice (Node.js/Python faster than Java)
      - Reduce deployment package size
      - Initialize AWS SDK outside handler
      - Use Lambda@Edge for global distribution

14. **Scenario: Your downstream API accepts 100 requests/second max. Design a Lambda that doesn't overwhelm it.**
    - Use SQS with long polling (max wait time)
    - Create processing Lambda with batch size matched to rate
    - Implement exponential backoff on failures
    - Use concurrency limits to match downstream capacity
    - Example: 100 req/sec downstream = 10 workers × 10 req/sec

15. **You're building a real-time data processing pipeline. Compare Lambda vs Kinesis Lambda vs ECS.**
    - **Lambda**: Low latency required, unpredictable traffic, cost-sensitive
    - **Kinesis + Lambda**: Guaranteed ordering, consistent throughput
    - **ECS**: Consistent load, long-running, cost-effective for steady state

### Memory & Optimization
16. **Scenario: Your Lambda processes 100GB file. Memory runs out. Solutions?**
    - Increase function memory (CPU also scales with memory)
    - Stream file processing instead of loading entire file
    - Use S3 Select for filtering before processing
    - Partition file into chunks with Step Functions
    - Use temporary storage: `/tmp` (not persistent, counts against memory)

17. **How does Lambda memory allocation affect cost and performance?**
    - More memory = more CPU (linear scaling)
    - Cost = (memory GB × duration seconds × $0.0000166667)
    - Higher memory = faster execution, potentially lower total cost
    - Example: 512 MB × 60s = 30.72 cost units vs 1472 MB × 10s = 24.53 cost units
    - Optimization: Find sweet spot with X-Ray duration metrics

### State Management & Databases
18. **Scenario: Lambda needs to maintain state across multiple invocations. How?**
    - Don't store in `/tmp/` (not shared across concurrent Lambda instances)
    - Solutions:
      - DynamoDB: Fast, scalable, key-value store
      - RDS: Relational data, complex queries
      - ElastiCache: In-memory caching for session state
      - S3: For large objects, batch processing
      - Parameter Store: For configuration state

19. **How do you connect Lambda to RDS without exposing database to Internet?**
    - Deploy Lambda in VPC with private subnets
    - RDS in private subnet, security group allows Lambda
    - VPC endpoints for AWS services
    - Use RDS Proxy for connection pooling
    - Enable VPC Flow Logs for troubleshooting

---

## 4. Best Practices & Optimization

20. **What are Lambda best practices for production?**
    - Keep functions small and focused (single responsibility)
    - Use environment variables for configuration
    - Implement logging (CloudWatch) and tracing (X-Ray)
    - Monitor metrics: throttles, errors, duration, cold starts
    - Use layers for shared code
    - Implement comprehensive error handling
    - Test with SAM locally before deploying
    - Use Infrastructure as Code (CloudFormation, SAM)
    - Version functions, use aliases for rollback
    - Implement security: least privilege IAM, encryption

21. **How do you debug Lambda issues in production?**
    - CloudWatch Logs: Application and system logs
    - CloudWatch Insights: Complex queries on logs
    - X-Ray: Trace requests through distributed system
    - Lambda Insights: Container-level metrics
    - CloudTrail: API calls for permissions issues
    - VPC Flow Logs: Network connectivity issues
    - Set up alarms on error rates and throttles

22. **Design a logging strategy for Lambda.**
    - Structure logs as JSON for CloudWatch Insights queries
    - Include: request ID, user, timestamp, operation, result status
    - Use log levels: DEBUG, INFO, WARN, ERROR
    - Log to file descriptor 1 (stdout), not files
    - Use context: `context.request_id` for tracing
    - Sample sensitive data (PII masking)

---

## 5. Real-World Scenarios & Tricky Questions

23. **Scenario: Lambda fails intermittently. Diagnosis approach?**
    - Check CloudWatch Logs for patterns
    - Verify timeout duration (increase if needed)
    - Check memory allocation (out of memory?)
    - Review concurrency (throttling?)
    - Check IAM permissions (access denied?)
    - Monitor downstream services (API limits, database locks)
    - Use X-Ray to identify which service is slow
    - Test with synthetic monitoring

24. **Lambda inside VPC processes requests but fails randomly. Root cause?**
    - **Common issue**: ENI attachment overhead (cold start in VPC)
    - **Solution**: Use NAT gateway for outbound, RDS Proxy for database
    - **Better**: Use Lambda outside VPC + VPC endpoint to AWS Services
    - Consider: Provisioned concurrency for consistent performance

25. **How do you achieve exactly-once processing in Lambda?**
    - Guaranteed at-least-once delivery from event sources
    - Idempotency key: Store processed message IDs in DynamoDB
    - Check before processing: If ID exists, skip
    - Include conditional writes in database transactions
    - Example: DynamoDB unique key = message ID

26. **Scenario: Lambda cost doubled without code changes. Investigate.**
    - Increased invocation count: Check CloudWatch metrics
    - Increased duration: Slow downstream services
    - Higher memory allocation: Check recent deployments
    - Concurrency increase: More concurrent executions
    - Data transfer costs: Check for excessive calls to external APIs
    - Solutions: Caching, connection pooling, batch processing

27. **Design a Lambda-based file processing pipeline for 100 files/day with strict SLA.**
    - Architecture:
      1. S3 upload → EventBridge rule (filtering)
      2. SQS queue for reliable processing
      3. Reserved concurrency Lambda (guaranteed capacity)
      4. DynamoDB for status tracking
      5. SNS for notifications on failure
      6. CloudWatch alarms for SLA violations
      7. Dead Letter Queue for failed files
    - Monitoring: Duration, error rate, queue depth

---

## 6. Asynchronous Processing & Event-Driven

28. **Compare different async patterns for Lambda:**
    - **Direct**: Lambda → SNS/SQS (fire and forget)
    - **Queue-based**: API → SQS → Lambda (decoupled)
    - **Event-driven**: Any source → EventBridge → Lambda (centralized routing)
    - **Stream-based**: Kinesis/DynamoDB Streams → Lambda (ordered processing)

29. **Scenario: Need to send notifications to 1 million users. Design the system.**
    - Don't call user service 1M times in Lambda
    - Use SNS for scalable pub/sub
    - Architecture:
      1. Lambda generates user list, publishes to SNS
      2. SNS delivers to SQS (parallel queues)
      3. Notification service Lambda processes from SQS
      4. Exponential backoff for retries
      5. Monitor DLQ for failures

---

## 7. Deployment & Versioning

30. **How do you implement canary deployment for Lambda?**
    - Create versioned functions (v1, v2)
    - Use alias pointing to v1 (100%)
    - Update production alias: v1 10% → v2 90%
    - Monitor error rates, latency
    - Gradually shift traffic to v2
    - Rollback to v1 if issues
    - Tools: CodeDeploy, SAM, CloudFormation

31. **Explain Lambda@Edge and when to use it.**
    - Lambda executes at CloudFront edge locations (closer to users)
    - Use cases:
      - Request/response manipulation (headers, authentication)
      - A/B testing
      - Image optimization
      - Security headers injection
    - Limitations: 1 second timeout, 128 MB memory
    - Not for heavy compute or database operations

---

## 8. Hands-On Coding Questions

32. **Write a Lambda function to process SQS messages with error handling and DLQ.**
    ```python
    import json
    import boto3
    import logging

    sqs = boto3.client('sqs')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    def lambda_handler(event, context):
        for record in event['Records']:
            try:
                message_body = json.loads(record['body'])

                # Process message
                process_order(message_body)

                # Delete from queue on success
                sqs.delete_message(
                    QueueUrl=os.environ['QUEUE_URL'],
                    ReceiptHandle=record['receiptHandle']
                )

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                # SQS automatically moves to DLQ after max retries
                raise  # Re-raise to fail the message

    def process_order(order):
        logger.info(f"Processing order: {order['order_id']}")
        # Business logic here
        return True
    ```

33. **Write a Lambda for API Gateway with validation and response formatting.**
    ```python
    import json
    import boto3
    from datetime import datetime

    def lambda_handler(event, context):
        try:
            # Parse input
            if not event.get('body'):
                return error_response(400, "Request body required")

            body = json.loads(event['body'])

            # Validation
            if not body.get('email'):
                return error_response(400, "Email required")

            # Process
            result = process_request(body)

            return response(200, result)

        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return error_response(500, "Internal server error")

    def response(status_code, body):
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(body)
        }

    def error_response(status_code, message):
        return response(status_code, {'error': message})

    def process_request(data):
        return {'status': 'success', 'timestamp': datetime.now().isoformat()}
    ```

34. **Write a Lambda that processes DynamoDB Stream records:**
    ```python
    import json
    import boto3

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ProcessedRecords')

    def lambda_handler(event, context):
        for record in event['Records']:
            event_name = record['eventName']  # INSERT, MODIFY, REMOVE

            if event_name == 'INSERT':
                new_image = record['dynamodb']['NewImage']
                process_insert(new_image)

            elif event_name == 'MODIFY':
                old_image = record['dynamodb']['OldImage']
                new_image = record['dynamodb']['NewImage']
                process_update(old_image, new_image)

            elif event_name == 'REMOVE':
                old_image = record['dynamodb']['OldImage']
                process_delete(old_image)

        return {'statusCode': 200, 'processed': len(event['Records'])}

    def process_insert(item):
        # Business logic for new record
        pass

    def process_update(old, new):
        # Business logic for updated record
        pass

    def process_delete(item):
        # Business logic for deleted record
        pass
    ```

---

## Tips for Interview Success

- **Understand trade-offs**: Cost vs Performance vs Complexity
- **Know cold start problem**: It's frequently asked
- **Master concurrency**: Reserved vs Provisioned vs unreserved
- **Async patterns**: SQS, SNS, EventBridge, Kinesis
- **Error handling**: Retries, DLQ, idempotency
- **Step Functions integration**: For complex workflows
- **Hands-on practice**: Build a small microservice with API Gateway + Lambda + DynamoDB
- **Cost optimization**: Memory selection, connection pooling
- **Security mindset**: VPC, IAM, encryption, secrets management

