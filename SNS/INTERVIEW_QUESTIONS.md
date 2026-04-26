# SNS Interview Questions - Comprehensive

## 1. Fundamental Questions

### Basic Concepts

1. **What is SNS and how does it work?**
   - Pub/Sub messaging service (publish-subscribe)
   - Publishers send messages to topics
   - Subscribers receive messages automatically
   - Multiple subscribers can receive same message
   - Push-based delivery model

2. **Explain SNS topics and subscriptions.**
   - **Topic**: Communication channel where publishers send messages
   - **Subscription**: Endpoint that receives messages from topic
   - Multiple subscriptions per topic (1-to-many)
   - Each subscriber can be different protocol
   - Subscription types: Email, SMS, HTTP/HTTPS, SQS, Lambda, SES

3. **SNS message structure and attributes.**
   - Message: Main content (max 256 KB)
   - Subject: Email subject, optional
   - Message Attributes: Key-value pairs for filtering
   - MessageId: Unique identifier
   - Timestamp: When message was published

4. **SNS vs SQS comparison.**
   - **SNS**: Pub/Sub (one-to-many), push-based, immediate delivery
   - **SQS**: Queue (one-to-one), pull-based, consumer polls
   - **Combined**: SNS → SQS for fan-out with buffering
   - Timing: SNS sends immediately, SQS buffers for consumption

5. **SNS pricing and limits.**
   - Charged per million requests
   - SMS: Additional charges per message
   - Free tier: 1000 requests/month for SNS, 100 SMS messages
   - HTTP endpoint: Up to 100 concurrent connections per topic
   - Message size: Max 256 KB

---

## 2. Intermediate Scenarios

### Message Filtering & Routing

6. **Scenario: Topic receives multiple event types, subscribers want filtered messages.**
   - Topic: "ecommerce-events"
   - Event types: order, payment, shipment, return
   - Subscriber 1: Only "order" events
   - Subscriber 2: Only "payment" events
   - Implementation: Message attributes + filter policy
   ```json
   {
     "FilterPolicy": {
       "eventType": ["order", "payment"]
     }
   }
   ```

7. **Design fan-out architecture for notifications.**
   - Order placed event → SNS topic
   - Subscriptions:
     1. **SQS**: Inventory service (async processing)
     2. **SQS**: Fulfillment service (async processing)
     3. **Lambda**: Send email confirmation (immediately)
     4. **HTTP**: Webhook to external system
   - Benefit: Decoupled architecture, each service independent

### Delivery & Reliability

8. **Explain SNS message delivery and retries.**
   - HTTP/HTTPS: Retry with exponential backoff
   - Retry policy: 1 second, 2 seconds, 5 seconds, 10 seconds, 30 seconds
   - After retries exhausted: Message discarded (use DLQ pattern)
   - Dead Letter Queue: Not native, send failures to SQS
   - Max receive count: Configure on SQS side if SQS endpoint

9. **Handle failed message delivery with DLQ pattern.**
   - Challenge: SNS doesn't have native DLQ
   - Solution: Use SQS with DLQ
   - Flow:
     1. SNS → SQS (subscribes to topic)
     2. SQS → Lambda (consumer)
     3. SQS with DLQ (captures failures after 3 retries)
   - Monitoring: CloudWatch alarms on DLQ depth

---

## 3. Advanced Scenarios

### Multi-Region & High Availability

10. **Design SNS for multi-region disaster recovery.**
    - Primary region: SNS topic
    - Secondary region: Replicated topic
    - Replication: Custom Lambda or SNS to SNS subscription
    - Failover: Route 53 or application logic
    - Deployment: Publish to both topics simultaneously

11. **Implement SNS message ordering (FIFO).**
    - SNS doesn't have FIFO (unlike SQS FIFO)
    - Solution: For ordered processing
      - SNS → SQS FIFO (ordered)
      - SQS FIFO → Lambda (processes in order)
    - Benefit: Guaranteed ordering per message group ID
    - Use case: User-specific events in order

### Integration Patterns

12. **Design notification system (multiple channels).**
    - SNS topic: "notifications"
    - Subscriptions:
      - **Email**: SES integration (transactional)
      - **SMS**: SNS direct (urgent alerts)
      - **Push**: Lambda → Mobile push service
      - **Slack**: Lambda → Slack webhook
    - Message attributes: Priority, urgency for routing

13. **Scenario: Decouple application from notification service.**
    - Application: Publishes events to SNS
    - Notification service: Subscribes to SNS
    - Benefit: Application doesn't care about delivery
    - Scalability: Add new subscribers without changing app
    - Flexibility: Change notification strategy easily

---

## 4. Real-World Scenarios

14. **Monitor SNS topic metrics and health.**
    - CloudWatch metrics:
      - NumberOfMessagesPublished: Topic throughput
      - NumberOfNotificationsFailed: Delivery failures
      - NumberOfNotificationsDelivered: Successful delivery
    - Alarms:
      - MessagePublishRate drops → Check publishers
      - FailureRate spikes → Check endpoints
      - LatePub notifications → Investigate endpoint health

15. **Scenario: SNS messages not reaching subscribers.**
    - Troubleshooting:
      1. Check subscription status (confirmed/pending)
      2. Verify filter policy matches message
      3. Check endpoint permissions (SQS, Lambda)
      4. Review message attributes vs filter
      5. Check CloudWatch for failed deliveries
    - Common causes:
      - UDP subscription not confirmed
      - Lambda permission missing
      - SQS resource-based policy denying

16. **Design SNS for broadcast notification system.**
    - Example: Breaking news alert
    - Topic: "breaking-news"
    - Subscribers:
      - Web: Lambda → API Gateway webhook
      - Mobile: Lambda → Firebase Cloud Messaging
      - Email: SES integration
      - Slack: Lambda → Slack channel
    - Message: Single publish, reaches all channels
    - Cost: Per message x subscribers

---

## 5. Best Practices

17. **SNS best practices:**
    - Use message attributes for filtering
    - Implement idempotent subscribers (handle duplicates)
    - Monitor with CloudWatch metrics
    - Set appropriate message retention
    - Use DLQ pattern for failed messages (via SQS)
    - Encryption: Enable SSE-SQS/SSE-KMS
    - Access control: Resource-based policies only
    - Error handling: Subscribers must manage retries

---

## 6. Hands-On Examples

18. **Publish message with attributes to SNS:**
    ```python
    import boto3
    import json

    sns = boto3.client('sns')

    def publish_event(event_type, data):
        response = sns.publish(
            TopicArn='arn:aws:sns:region:account:topic',
            Message=json.dumps({
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }),
            MessageAttributes={
                'eventType': {
                    'StringValue': event_type,
                    'DataType': 'String'
                },
                'priority': {
                    'StringValue': 'high',
                    'DataType': 'String'
                },
                'region': {
                    'StringValue': 'us-east-1',
                    'DataType': 'String'
                }
            },
            Subject='New Event'
        )
        return response['MessageId']
    ```

19. **Subscribe with message filtering:**
    ```python
    sns = boto3.client('sns')

    # SQS subscription with filter
    subscription = sns.subscribe(
        TopicArn='arn:aws:sns:region:account:topic',
        Protocol='sqs',
        Endpoint='arn:aws:sqs:region:account:queue',
        Attributes={
            'FilterPolicy': json.dumps({
                'eventType': ['order', 'payment'],
                'priority': ['high', 'medium']
            }),
            'RawMessageDelivery': 'false'  # Include SNS wrapper
        }
    )
    ```

20. **Lambda subscriber with SNS event:**
    ```python
    import json

    def lambda_handler(sns_event, context):
        for record in sns_event['Records']:
            message = json.loads(record['Sns']['Message'])
            attributes = record['Sns']['MessageAttributes']

            # Process based on event type
            event_type = attributes.get('eventType', {}).get('Value')

            if event_type == 'order':
                process_order(message)
            elif event_type == 'payment':
                process_payment(message)

            print(f"Processed: {message}")

        return {'statusCode': 200}
    ```

---

## Tips for Interview Success

- **Pub/Sub pattern**: Understand when to use vs Queue
- **Message filtering**: How to route without extra processing
- **Fan-out**: Multiple subscribers from single topic
- **Delivery guarantees**: At-least-once, not exactly-once
- **Integration**: Major AWS services integration points
- **Monitoring**: Health checks and metrics
- **Error handling**: Subscriber responsibility
- **Scalability**: Horizontal scaling of subscribers

