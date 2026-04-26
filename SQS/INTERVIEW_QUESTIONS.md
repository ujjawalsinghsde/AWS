# SQS & SNS Interview Questions

## 1. Fundamental Questions

### SQS (Simple Queue Service)

1. **What is SQS and its core use cases?**
   - Fully managed message queue service
   - Decouples producers from consumers
   - Reliable message delivery with retry mechanism
   - Use case: Asynchronous task processing, buffering spikes, workload distribution

2. **Explain SQS queue types.**
   - **Standard Queue**: At-least-once delivery, best-effort ordering
   - **FIFO Queue**: Exactly-once, strict ordering, slower throughput (3,000 msg/sec)
   - Choose: FIFO for order-dependent (orders, payments), Standard for general

3. **What is visibility timeout?**
   - Time period during which message is hidden after being received
   - Default: 30 seconds
   - If not deleted within timeout, message becomes visible again
   - Set based on expected processing time
   - ChangeMessageVisibility: Extend timeout during processing

4. **Explain Dead Letter Queue (DLQ).**
   - Queue for messages that failed processing after max retries
   - Helps identify problematic messages
   - Set "maxReceiveCount" (e.g., 3 retries)
   - Monitor DLQ for failures and debug

5. **SQS pricing and optimization.**
   - Charged per 1 million requests
   - Batch operations: SendMessageBatch, ReceiveMessage batch (up to 10)
   - With batching: 1/10 cost for same throughput
   - Long polling: Reduce empty responses

---

### SNS (Simple Notification Service)

6. **What is SNS and its differences from SQS?**
   - Pub/Sub messaging service
   - Publishers send to topics
   - Subscribers receive automatically (email, SMS, HTTP, SQS, Lambda)
   - Push-based (SNS initiates delivery to subscribers)
   - SQS is pull-based (consumer polls)

7. **Explain SNS topic and subscriptions.**
   - Topic: Communication channel
   - Subscription: Endpoint receiving messages
   - Multiple subscribers can receive same message
   - Message filtering: Only receive matching messages
   - Protocol: Email, SMS, HTTP/S, SQS, Lambda, SES

8. **SNS message filtering and attributes.**
   - Send attributes with message
   - Subscribe with filter: Only receive matching
   - Example: {"type": "order"} → only receive "order" messages
   - Saves on processing unwanted messages

---

## 2. Intermediate Scenarios

### Queue Design & Patterns

9. **Scenario: You need guaranteed message processing with no loss. Design system.**
   - Answer:
     - SQS Standard/FIFO (reliable delivery, auto-retry)
     - Set visibility timeout: Processing time + buffer
     - Dead Letter Queue: For failed messages
     - Idempotent processing: Handle duplicate messages
     - ACK/delete message only after successful processing
     - CloudWatch alarms on DLQ depth

10. **Scenario: Application receives traffic spike (10x normal). Absorb spike.**
    - SQS:
      1. Producers push to queue
      2. Consumers process at their own pace
      3. Queue acts as buffer, absorbs spike
      4. Scale consumers up after spike
    - Benefit: Producers don't get throttled, consumers handle at capacity

11. **Fan-out pattern: Send message to multiple services.**
    - SNS topic → Multiple SQS queues subscribed
    - Service 1: SQS queue 1 → Lambda 1
    - Service 2: SQS queue 2 → Lambda 2
    - Service 3: SQS queue 3 → Email
    - Single message reaches all services
    - Each can process independently

12. **Scenario: Process long-running tasks (1 hour) in SQS.**
    - Set visibility timeout: > 1 hour (e.g., 3600 seconds)
    - During processing: Extend timeout if needed (ChangeMessageVisibility)
    - DLQ: Catch failures after timeout
    - Heartbeat: Extend timeout periodically during processing

---

## 3. Advanced Scenarios

### Error Handling & Resilience

13. **Design resilient message processing with retries and backoff.**
    - SQS automatic retries: Not available (visibility timeout)
    - Application retry strategy:
      - Exponential backoff: 1s, 2s, 4s, 8s, etc
      - Max attempts: 3-5
      - DLQ after max attempts
      - Monitor DLQ for patterns
    - Code:
    ```python
    import time
    for attempt in range(max_attempts):
        try:
            process_message(message)
            sqs.delete_message(...)  # Success
            break
        except Exception as e:
            if attempt == max_attempts - 1:
                # Send to DLQ
                move_to_dlq(message)
            else:
                # Visible again after timeout
                wait_time = 2 ** attempt  # Exponential
                time.sleep(wait_time)
    ```

14. **Scenario: SNS delivery to HTTP endpoint fails. Handle gracefully.**
    - SNS retry policy: Configurable (1-3x, exp backoff)
    - Dead Letter Queue is not standard for SNS
    - Solution: HTTP endpoint should be idempotent
    - Better: Send to SQS → HTTP Lambda (more control)
    - Monitor: CloudWatch metrics for failed deliveries

### Ordering & Deduplication

15. **Ensure exactly-once processing with SQS FIFO.**
    - FIFO ensures:
      - Ordering: Messages processed in order
      - Exactly-once: Each message processed once
    - Deduplication ID: Prevents duplicate messages
    - Message Group ID: Logical grouping, separate queues
    - Example: User 1 → Message Group "user-1"
    - Cost: More expensive than Standard

16. **Scenario: Process messages in order per customer, parallel across customers.**
    - FIFO + Message Group IDs:
      - Each customer has unique Group ID
      - Messages with same GID processed in order
      - Different GIDs parallel
    - Example:
      ```python
      sqs.send_message(
          QueueUrl=queue_url,
          MessageBody=json.dumps(order),
          MessageGroupId=f"customer-{customer_id}",
          MessageDeduplicationId=str(uuid.uuid4())
      )
      ```

---

## 4. Real-World Scenarios

17. **Monitor SQS queue depth for scaling decisions.**
    - CloudWatch metrics:
      - ApproximateNumberOfMessagesVisible: Backlog
      - ApproximateAgeOfOldestMessage: How long waiting
      - NumberOfMessagesSent/Received: Throughput
    - Auto-scaling: Scale Lambda/EC2 based on queue depth
    - Ideal: Process faster than messages arrive (queue empty)
    - Alert: If queue grows unbounded or age exceeds threshold

18. **Scenario: SQS queue has poison messages (always fail). Fix.**
    - Monitor DLQ for repeated messages
    - Analyze: Why message fails?
      - Invalid format → Filter before queue
      - External service down → Retry later
      - Bugs in consumer → Fix and redeploy
    - Manual processing: Move from DLQ to queue after fix
    - Alerting: Too many DLQ messages = production alert

19. **Design notification system: User action → Email + SMS + Alert**
    - SNS topic: "user-events"
    - Subscriptions:
      - Email: SES integration
      - SMS: SNS direct or SNS → Lambda → Twilio
      - Alert: SNS → CloudWatch alarm
    - Message filtering: Different notifications per event type

---

## 5. Best Practices

20. **SQS & SNS best practices:**
    - SQS: Visibility timeout > processing time
    - SQS: Use batch operations (SendBatch, ReceiveBatch)
    - SQS: Delete message only after successful processing
    - DLQ: Monitor and act on failed messages
    - SNS: Use message attributes for filtering
    - SNS: Message deduplication for FIFO
    - FIFO: Use when ordering is critical
    - Monitoring: CloudWatch metrics and alarms
    - Logging: CloudTrail for API calls, application logs for processing

---

## 6. Hands-On Examples

21. **SQS consumer with visibility timeout update:**
    ```python
    import boto3

    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.region.amazonaws.com/account/queue'

    def consume_messages():
        while True:
            # Receive up to 10 messages
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20  # Long polling
            )

            if 'Messages' not in response:
                continue

            for message in response['Messages']:
                try:
                    # Process message
                    process_message(message['Body'])

                    # Delete after success
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                except ProcessingException as e:
                    # Extend visibility timeout for retry
                    sqs.change_message_visibility(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle'],
                        VisibilityTimeout=300  # 5 more minutes
                    )
    ```

22. **SNS publish with message attributes:**
    ```python
    import json
    import boto3

    sns = boto3.client('sns')

    def publish_event(event_type, data):
        message = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        response = sns.publish(
            TopicArn='arn:aws:sns:region:account:topic',
            Message=json.dumps(message),
            MessageAttributes={
                'event_type': {
                    'StringValue': event_type,
                    'DataType': 'String'
                },
                'priority': {
                    'StringValue': 'high',
                    'DataType': 'String'
                }
            }
        )
        return response['MessageId']
    ```

23. **Receive messages with filtering:**
    ```python
    # Subscribe with filter
    sns.subscribe(
        TopicArn=topic_arn,
        Protocol='sqs',
        Endpoint=queue_arn,
        Attributes={
            'FilterPolicy': json.dumps({
                'event_type': ['order', 'payment'],
                'priority': ['high']
            })
        }
    )
    ```

---

## Tips for Interview Success

- **Queue vs Pub/Sub**: SQS for 1-to-1, SNS for 1-to-many
- **Visibility timeout**: Core to understanding SQS behavior
- **Idempotency**: Must handle duplicate messages
- **DLQ handling**: Critical for production reliability
- **Ordering**: FIFO has trade-offs (cost, throughput)
- **Decoupling**: Main architectural benefit
- **Resilience**: Retry, backoff, and monitoring strategies
- **Cost optimization**: Batch operations, appropriate queue type

