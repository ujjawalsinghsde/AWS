# AWS SNS (Simple Notification Service)

**Python boto3 code:** [sns_operations.py](./sns_operations.py)

---

## Table of Contents

1. [What is AWS SNS?](#1-what-is-aws-sns)
2. [Core Concepts](#2-core-concepts)
3. [Topics and Subscriptions](#3-topics-and-subscriptions)
4. [Subscription Types](#4-subscription-types)
5. [Publishing Messages](#5-publishing-messages)
6. [Message Filtering](#6-message-filtering)
7. [Message Attributes](#7-message-attributes)
8. [Fan-Out Pattern (SNS + SQS)](#8-fan-out-pattern-sns--sqs)
9. [Access Control & Security](#9-access-control--security)
10. [Monitoring & Metrics](#10-monitoring--metrics)
11. [FIFO Topics](#11-fifo-topics)
12. [Message Delivery & Retries](#12-message-delivery--retries)
13. [Cost Optimization](#13-cost-optimization)
14. [Common Architectures](#14-common-architectures)
15. [SNS CLI Cheat Sheet](#15-sns-cli-cheat-sheet)
16. [Best Practices](#16-best-practices)

---

## 1. What is AWS SNS?

**Amazon SNS (Simple Notification Service)** is a fully managed pub/sub messaging service that enables sending messages to multiple subscribers through different channels.

### Key Characteristics

- **Fully Managed** — No infrastructure to manage
- **Pub/Sub Model** — Publishers send messages to topics; subscribers receive them
- **Multiple Endpoints** — Send to SQS, Lambda, HTTP, Email, SMS, mobile push, etc.
- **Scalability** — Automatically scales to handle any message volume
- **Durability** — Messages stored redundantly across multiple AZs
- **Low Latency** — High-performance message delivery
- **Multiple Protocols** — SMS, Email, HTTP/HTTPS, SQS, Lambda, mobile push

### When to Use SNS

✓ Broadcasting messages to multiple subscribers
✓ Sending notifications (Email, SMS, push)
✓ Event-driven architectures
✓ Coordinating distributed systems
✓ Decoupling publishers and subscribers
✓ Fan-out patterns with SQS

---

## 2. Core Concepts

### 2.1 Pub/Sub Model

```
      Publishers
         ↓
    [SNS Topic]  ← Central hub
      ↙ ↓ ↘
   SQS  Lambda  HTTP/Email/SMS
  Queue Function  Endpoint


One publisher → One topic → Multiple subscribers
Subscribers don't know about each other
Decoupled architecture
```

### 2.2 Topics

A **topic** is a communication channel where messages are published.

```
Topic ARN:
arn:aws:sns:<region>:<account-id>:TopicName

Example:
arn:aws:sns:us-east-1:123456789012:OrderNotifications
```

**Topic Characteristics:**
- Unique name within AWS account and region
- Publishers send messages to topic
- SNS delivers to all subscribed endpoints
- Messages don't persist (unlike SQS)
- Messages delivered immediately

### 2.3 Subscriptions

A **subscription** connects a topic to an endpoint that receives messages.

```
Topic: OrderNotifications
├── Subscription 1: SQS Queue (OrderQueue)
├── Subscription 2: Email (admin@example.com)
├── Subscription 3: Lambda Function
└── Subscription 4: HTTP endpoint

When message published to topic → All 4 endpoints receive it
```

**Subscription States:**
- **Pending** — Awaiting confirmation (especially Email, HTTP)
- **Confirmed** — Active, receiving messages
- **Deleted** — No longer receiving messages

---

## 3. Topics and Subscriptions

### 3.1 Creating Topics

```python
import boto3

client = boto3.client('sns', region_name='us-east-1')

# Standard topic
response = client.create_topic(Name='OrderNotifications')
topic_arn = response['TopicArn']

# FIFO topic (exactly-once, ordered)
response = client.create_topic(
    Name='OrderNotifications.fifo',
    Attributes={
        'FifoTopic': 'true',
        'ContentBasedDeduplication': 'true'
    }
)

# Topic with attributes
response = client.create_topic(
    Name='OrderNotifications',
    Tags=[
        {'Key': 'Environment', 'Value': 'Production'},
        {'Key': 'Application', 'Value': 'Orders'}
    ]
)
```

### 3.2 Listing and Getting Topics

```python
# List all topics
response = client.list_topics()
topics = response.get('Topics', [])

# Get topic ARN by name
response = client.get_topic_attributes(TopicArn=topic_arn)
attributes = response['Attributes']
```

### 3.3 Creating Subscriptions

```python
# Subscribe SQS queue
response = client.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint='arn:aws:sqs:us-east-1:123456789012:OrderQueue'
)
subscription_arn = response['SubscriptionArn']

# Subscribe Email
response = client.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='admin@example.com'
)
# User must confirm subscription via email link

# Subscribe Lambda
response = client.subscribe(
    TopicArn=topic_arn,
    Protocol='lambda',
    Endpoint='arn:aws:lambda:us-east-1:123456789012:function:ProcessOrder'
)

# Subscribe HTTP endpoint
response = client.subscribe(
    TopicArn=topic_arn,
    Protocol='https',
    Endpoint='https://example.com/webhook'
)
```

### 3.4 Managing Subscriptions

```python
# List subscriptions for topic
response = client.list_subscriptions_by_topic(TopicArn=topic_arn)

# Get subscription attributes
response = client.get_subscription_attributes(SubscriptionArn=subscription_arn)

# Set subscription attributes (filter policy, etc.)
client.set_subscription_attributes(
    SubscriptionArn=subscription_arn,
    AttributeName='FilterPolicy',
    AttributeValue=json.dumps({
        'priority': ['High'],
        'type': ['OrderCreated', 'OrderShipped']
    })
)

# Unsubscribe
client.unsubscribe(SubscriptionArn=subscription_arn)

# Delete topic
client.delete_topic(TopicArn=topic_arn)
```

---

## 4. Subscription Types

### 4.1 SQS Subscriptions

```python
# Subscribe SQS queue
response = client.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=queue_arn
)

# SNS wraps message in JSON:
{
    "Type": "Notification",
    "MessageId": "12345",
    "TopicArn": "arn:aws:sns:...",
    "Subject": "test subject",
    "Message": "actual message content",
    "Timestamp": "2025-03-30T10:00:00Z",
    "SignatureVersion": "1",
    "Signature": "signature",
    "SigningCertUrl": "...",
    "UnsubscribeUrl": "..."
}

# Consumer decodes:
import json
body = json.loads(sqs_message['Body'])
actual_message = json.loads(body['Message'])
```

### 4.2 Lambda Subscriptions

```python
# Lambda receives SNS event directly:
def lambda_handler(event, context):
    records = event.get('Records', [])
    for record in records:
        sns_message = record['Sns']
        message = sns_message['Message']
        subject = sns_message['Subject']

        print(f"Subject: {subject}")
        print(f"Message: {message}")

        # Process...
        return {'statusCode': 200}
```

### 4.3 Email Subscriptions

```python
client.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='user@example.com'
)

# User receives email with confirmation link
# Must click to activate subscription
# Can use email-json for JSON formatted emails
```

### 4.4 HTTP/HTTPS Subscriptions

```python
# Your webhook receives POST request:
POST /webhook HTTP/1.1
Content-Type: application/x-amz-json-1.1
X-Amz-Sns-Message-Type: Notification

{
    "Type": "Notification",
    "Message": "...",
    "TopicArn": "...",
    ...
}

# Your endpoint must:
# 1. Accept POST requests
# 2. Handle SubscriptionConfirmation (click link to confirm)
# 3. Validate signatures
# 4. Return 200 OK
```

### 4.5 SMS Subscriptions

```python
# Send SMS messages
client.subscribe(
    TopicArn=topic_arn,
    Protocol='sms',
    Endpoint='+1234567890'  # Phone number in E.164 format
)

# Costs apply per SMS sent
# 100 free SMS per month, then ~$0.50 per SMS depending on country
```

### 4.6 Mobile Push Subscriptions

```python
# For iOS, Android, Kindle, Windows Phone
client.subscribe(
    TopicArn=topic_arn,
    Protocol='application',  # Mobile app endpoint
    Endpoint='arn:aws:sns:us-east-1:123456789012:app/APNS/MyApp/12345678-...'
)
```

---

## 5. Publishing Messages

### 5.1 Publish Simple Message

```python
# Basic publish
response = client.publish(
    TopicArn=topic_arn,
    Message='Hello from SNS'
)
message_id = response['MessageId']

# With subject (used for email)
response = client.publish(
    TopicArn=topic_arn,
    Subject='Order Notification',
    Message='Your order #123 has been shipped'
)

# With message structure for protocol-specific formatting
response = client.publish(
    TopicArn=topic_arn,
    Message='Default message for unknown protocols',
    MessageStructure='json',
    Subject='Order Update'
)
```

### 5.2 Publish JSON Message

```python
import json

message = {
    'order_id': 123,
    'customer': 'John Doe',
    'amount': 99.99,
    'status': 'shipped'
}

response = client.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message),
    Subject='Order Shipped'
)
```

### 5.3 Publish with Message Attributes

```python
response = client.publish(
    TopicArn=topic_arn,
    Message='Order notification',
    MessageAttributes={
        'priority': {
            'DataType': 'String',
            'StringValue': 'High'
        },
        'order_id': {
            'DataType': 'String',
            'StringValue': '12345'
        },
        'amount': {
            'DataType': 'Number',
            'StringValue': '99.99'
        }
    }
)
```

### 5.4 Publish with Protocol-Specific Messages

```python
# Different message for each subscriber type
message_structure = {
    "default": "Default message for unknown protocols",
    "sqs": json.dumps({
        "action": "ProcessOrder",
        "order_id": 123
    }),
    "email": "Your order has been shipped!",
    "lambda": json.dumps({
        "event_type": "order.shipped",
        "order_id": 123
    }),
    "https": json.dumps({
        "webhook_event": "order_shipped",
        "order_id": 123
    })
}

response = client.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message_structure),
    MessageStructure='json'
)
```

### 5.5 Publish Batch (up to 10)

```python
entries = [
    {
        'Id': '1',
        'Message': 'Order 1 shipped',
        'Subject': 'Shipment Notification'
    },
    {
        'Id': '2',
        'Message': 'Order 2 delivered',
        'Subject': 'Delivery Notification'
    }
]

response = client.publish_batch(
    TopicArn=topic_arn,
    PublishBatchRequestEntries=entries
)

# Check results
successful = len(response.get('Successful', []))
failed = len(response.get('Failed', []))
```

---

## 6. Message Filtering

### 6.1 Filter Policy

```python
import json

# Only receive messages with specific attributes
filter_policy = {
    "priority": ["High"],  # Only "High" priority
    "type": ["OrderShipped", "OrderDelivered"],  # Only these types
    "amount": [{"numeric": [">", 100]}]  # Amount greater than 100
}

client.set_subscription_attributes(
    SubscriptionArn=subscription_arn,
    AttributeName='FilterPolicy',
    AttributeValue=json.dumps(filter_policy)
)

# Publisher sends with matching attributes
response = client.publish(
    TopicArn=topic_arn,
    Message='Order shipped',
    MessageAttributes={
        'priority': {'DataType': 'String', 'StringValue': 'High'},
        'type': {'DataType': 'String', 'StringValue': 'OrderShipped'},
        'amount': {'DataType': 'Number', 'StringValue': '150'}
    }
)
# Subscriber receives because attributes match filter
```

### 6.2 Filter Policy Examples

```python
# Example 1: Match specific values
{
    "store": ["example_corp"]
}

# Example 2: Match multiple values
{
    "event": ["order-placed", "order-cancelled"]
}

# Example 3: Numeric comparisons
{
    "price": [{"numeric": [">=", 100]}]
}

# Example 4: Logical OR for multiple attributes
{
    "event": ["order-placed"],
    "priority": ["High", "Medium"]
}

# Example 5: Logical AND (all must match)
{
    "type": ["order"],
    "region": ["us-east-1", "us-west-2"],
    "priority": ["High"]
}

# Example 6: String patterns
{
    "email": [{"prefix": "admin"}]  # admin@example.com
}

# Example 7: Anything except
{
    "event": [{"anything-but": "order-cancelled"}]
}

# Example 8: Complex nested OR
{
    "price": [{"numeric": [">=", 100]}, {"numeric": ["<", 50]}]
}
```

### 6.3 Remove Filter Policy

```python
# Allow all messages
client.set_subscription_attributes(
    SubscriptionArn=subscription_arn,
    AttributeName='FilterPolicy',
    AttributeValue=json.dumps({})
)
```

---

## 7. Message Attributes

### 7.1 Supported Data Types

```
String — Text values
Number — Numeric values (integers, floats)
String.Array — Array of strings
Number.Array — Array of numbers
Binary — Binary data (base64 encoded)
```

### 7.2 Using Message Attributes

```python
response = client.publish(
    TopicArn=topic_arn,
    Message='Order notification',
    MessageAttributes={
        'OrderId': {
            'DataType': 'String',
            'StringValue': 'ORD-123456'
        },
        'Amount': {
            'DataType': 'Number',
            'StringValue': '99.99'
        },
        'Tags': {
            'DataType': 'String.Array',
            'StringValue': json.dumps(['urgent', 'ecommerce'])
        },
        'Priority': {
            'DataType': 'Number',
            'StringValue': '1'
        }
    }
)
```

### 7.3 Receiving Message Attributes

```python
# In Lambda:
def lambda_handler(event, context):
    record = event['Records'][0]
    sns = record['Sns']

    message_attrs = sns.get('MessageAttributes', {})
    order_id = message_attrs.get('OrderId', {}).get('Value')
    amount = message_attrs.get('Amount', {}).get('Value')

    print(f"Order: {order_id}, Amount: {amount}")
```

---

## 8. Fan-Out Pattern (SNS + SQS)

### 8.1 Fan-Out Architecture

```
One message → SNS Topic → Multiple SQS Queues

Publisher sends one message to topic
Topic distributes to multiple queues
Each queue has own consumers
Decoupled, scalable architecture

Example: Order event → 3 services process independently:
         ├─ Inventory Service (updates stock)
         ├─ Notification Service (sends email)
         └─ Analytics Service (logs event)
```

### 8.2 Setting Up Fan-Out

```python
import json

# Create topic
response = client.create_topic(Name='OrderEvents')
topic_arn = response['TopicArn']

# Create queues
sqs = boto3.client('sqs')
inventory_queue = sqs.create_queue(QueueName='InventoryQueue')['QueueUrl']
notification_queue = sqs.create_queue(QueueName='NotificationQueue')['QueueUrl']
analytics_queue = sqs.create_queue(QueueName='AnalyticsQueue')['QueueUrl']

# Get queue ARNs
def get_queue_arn(queue_url):
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])
    return attrs['Attributes']['QueueArn']

inv_arn = get_queue_arn(inventory_queue)
notif_arn = get_queue_arn(notification_queue)
analytics_arn = get_queue_arn(analytics_queue)

# Subscribe queues to topic
for queue_arn in [inv_arn, notif_arn, analytics_arn]:
    client.subscribe(
        TopicArn=topic_arn,
        Protocol='sqs',
        Endpoint=queue_arn
    )

# Allow SNS to send messages to SQS queues
queue_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn,
        "Condition": {
            "ArnEquals": {"aws:SourceArn": topic_arn}
        }
    }]
}

# Apply policy to each queue
for queue_url, queue_arn in [(inventory_queue, inv_arn),
                              (notification_queue, notif_arn),
                              (analytics_queue, analytics_arn)]:
    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={'Policy': json.dumps(queue_policy)}
    )
```

### 8.3 Publishing to Fan-Out

```python
# Publish order event
response = client.publish(
    TopicArn=topic_arn,
    Message=json.dumps({
        'order_id': 123,
        'customer': 'John',
        'items': [{'sku': 'ABC', 'qty': 2}],
        'amount': 99.99
    }),
    Subject='New Order Created'
)

# Message automatically delivered to all 3 queues
# Each service consumes independently
# Can scale independently
```

### 8.4 Processing Fan-Out Messages

```python
def process_order_event(message):
    body = json.loads(message['Body'])  # SNS wraps in JSON
    sns_message = json.loads(body['Message'])  # Extract actual message

    order_id = sns_message['order_id']
    return order_id

# Inventory service
def inventory_worker():
    while True:
        messages = sqs.receive_message(QueueUrl=inventory_queue, MaxNumberOfMessages=10)
        for message in messages.get('Messages', []):
            order_id = process_order_event(message)
            update_inventory(order_id)
            sqs.delete_message(QueueUrl=inventory_queue, ReceiptHandle=message['ReceiptHandle'])

# Notification service
def notification_worker():
    while True:
        messages = sqs.receive_message(QueueUrl=notification_queue, MaxNumberOfMessages=10)
        for message in messages.get('Messages', []):
            order_id = process_order_event(message)
            send_email(order_id)
            sqs.delete_message(QueueUrl=notification_queue, ReceiptHandle=message['ReceiptHandle'])
```

---

## 9. Access Control & Security

### 9.1 IAM Policy for SNS

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish",
        "sns:Subscribe"
      ],
      "Resource": "arn:aws:sns:us-east-1:123456789012:OrderNotifications"
    },
    {
      "Effect": "Allow",
      "Action": "sns:ListTopics",
      "Resource": "*"
    }
  ]
}
```

### 9.2 Topic Access Policy

```python
import json

policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Action": "sns:Publish",
        "Resource": topic_arn
    }]
}

client.set_topic_attributes(
    TopicArn=topic_arn,
    AttributeName='Policy',
    AttributeValue=json.dumps(policy)
)
```

### 9.3 Encryption

```python
# Enable encryption with AWS managed key
client.set_topic_attributes(
    TopicArn=topic_arn,
    AttributeName='KmsMasterKeyId',
    AttributeValue='alias/aws/sns'  # AWS managed key
)

# Or use customer-managed KMS key
client.set_topic_attributes(
    TopicArn=topic_arn,
    AttributeName='KmsMasterKeyId',
    AttributeValue='arn:aws:kms:us-east-1:123456789012:key/12345678-...'
)
```

### 9.4 Message Signing & Verification

```python
# SNS automatically signs messages
# To verify signature in HTTP endpoint:

import json
from urllib.request import urlopen
from M2Crypto import BIO, RSA
import hashlib
import base64

def verify_signature(message, signature, cert_url):
    """Verify SNS message signature"""
    # Get certificate
    with urlopen(cert_url) as cert_response:
        cert_data = cert_response.read()

    # Parse and verify
    # Reference: AWS SNS message signature verification
    pass
```

---

## 10. Monitoring & Metrics

### 10.1 CloudWatch Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Get topic metrics
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/SNS',
    MetricName='NumberOfMessagesPublished',
    Dimensions=[
        {
            'Name': 'TopicName',
            'Value': 'OrderNotifications'
        }
    ],
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=300,
    Statistics=['Sum']
)
```

### 10.2 Key Metrics

```
NumberOfMessagesPublished
- Total messages published to topic

NumberOfNotificationsFailed
- Messages delivery failed

NumberOfNotificationsDelivered
- Messages successfully delivered

PublishSize
- Average message size in bytes
```

### 10.3 Create Alarm

```python
cloudwatch.put_metric_alarm(
    AlarmName='SNS-HighFailureRate',
    MetricName='NumberOfNotificationsFailed',
    Namespace='AWS/SNS',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=2,
    Threshold=100,
    ComparisonOperator='GreaterThanThreshold',
    Dimensions=[
        {
            'Name': 'TopicName',
            'Value': 'OrderNotifications'
        }
    ]
)
```

---

## 11. FIFO Topics

### 11.1 FIFO Topic Characteristics

```
Standard Topics (default):
- Best-effort ordering (may be out of order)
- At-most-once delivery
- Unlimited throughput

FIFO Topics:
- Guaranteed ordering (strictly FIFO)
- Exactly-once processing
- Grouped delivery (message groups)
- 300 publish requests/sec default
```

### 11.2 Creating FIFO Topics

```python
response = client.create_topic(
    Name='OrderProcessing.fifo',
    Attributes={
        'FifoTopic': 'true',
        'ContentBasedDeduplication': 'false'  # or true for auto-dedup
    }
)

topic_arn = response['TopicArn']
```

### 11.3 Publishing to FIFO Topics

```python
# Must provide MessageGroupId
response = client.publish(
    TopicArn=topic_arn,
    Message='Order created',
    MessageGroupId='order-123',  # Groups messages
    MessageDeduplicationId='unique-id-123'  # Optional
)

# Messages with same MessageGroupId processed in order
# Different groups processed in parallel
```

### 11.4 FIFO SQS Subscriptions

```python
# FIFO topics must subscribe to FIFO SQS queues
sqs_fifo_queue_arn = 'arn:aws:sqs:us-east-1:123456789012:OrderQueue.fifo'

client.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=sqs_fifo_queue_arn
)

# Guarantees:
# - Messages delivered exactly once
# - Messages processed in order (per message group)
```

---

## 12. Message Delivery & Retries

### 12.1 Delivery Retry Policy

```python
# Configure retry policy for HTTP subscriptions
client.set_subscription_attributes(
    SubscriptionArn=subscription_arn,
    AttributeName='DeliveryPolicy',
    AttributeValue=json.dumps({
        "http": {
            "defaultHealthyRetryPolicy": {
                "minDelayTarget": 20,      # Min delay in seconds
                "maxDelayTarget": 20,      # Max delay in seconds
                "numRetries": 3,           # Number of retries
                "numMaxDelayThresholds": 0,
                "numNoDelayThresholds": 0,
                "numMinDelayThresholds": 0,
                "backoffFunction": "linear"
            },
            "disableSubscriptionOverrides": False
        }
    })
)
```

### 12.2 Dead Letter Queue for SNS to SQS

```python
# Already handled by SQS DLQ when subscribed
# Messages that can't be delivered to SQS go to SQS DLQ
# Not an SNS-specific feature
```

---

## 13. Cost Optimization

### 13.1 Pricing Model

```
SNS Publish:
- Free tier: 1 million API requests per month
- After: $0.50 per million requests

Subscriptions (per endpoint):
- Email: $2.00 per 100,000
- SMS: Variable by country (~$0.50 per SMS)
- Push notifications: $0.50 per million
- SQS: Free (counted in SNS pricing)
- Lambda: Free (counted in Lambda pricing)
```

### 13.2 Cost Optimization Strategies

```
1. Use batch publishing
   - Batch publish up to 10 in one API call
   - Reduces API request count

2. Filter at subscription
   - Use FilterPolicy to limit unnecessary deliveries
   - Only pay for delivered messages

3. Combine with SQS (fan-out)
   - One SNS publish → Multiple SQS subscriptions
   - More cost-effective than multiple direct publishes

4. Use appropriate protocols
   - SQS/Lambda: Cheaper than Email/SMS
   - SQS: Subscriber controls message retention

5. Use FIFO only when needed
   - Slightly higher cost
   - Only for ordering requirements
```

---

## 14. Common Architectures

### 14.1 Event Notification to Multiple Services

```
[Event Source] → [SNS Topic]
                 ├─→ [SQS Queue 1] → Service A
                 ├─→ [SQS Queue 2] → Service B
                 ├─→ [Lambda] → Immediate action
                 └─→ [Email] → Notification
```

### 14.2 Cross-Region Replication

```
[Primary Region]        [Secondary Region]
[SNS Topic] → [Lambda] → [SNS Topic]
              (replication)
```

### 14.3 Event-Driven Microservices

```
[API Request]
    ↓
[Process] → [Publish to SNS]
              ├─→ [Order Service]
              ├─→ [Inventory Service]
              ├─→ [Payment Service]
              └─→ [Notification Service]
```

---

## 15. SNS CLI Cheat Sheet

```bash
# Create topic
aws sns create-topic --name MyTopic

# List topics
aws sns list-topics

# Publish message
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:MyTopic \
  --message "Hello SNS" \
  --subject "Test Subject"

# Subscribe to topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:MyTopic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:MyQueue

# List subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:123456789012:MyTopic

# Set subscription filter policy
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:MyTopic:12345678 \
  --attribute-name FilterPolicy \
  --attribute-value '{"priority":["High"]}'

# Unsubscribe
aws sns unsubscribe \
  --subscription-arn arn:aws:sns:us-east-1:123456789012:MyTopic:12345678

# Delete topic
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:123456789012:MyTopic

# Get topic attributes
aws sns get-topic-attributes \
  --topic-arn arn:aws:sns:us-east-1:123456789012:MyTopic
```

---

## 16. Best Practices

### 16.1 Design Best Practices

✓ **Use filtering to reduce costs**
- Set FilterPolicy on subscriptions
- Only deliver relevant messages
- Avoid unnecessary charges

✓ **For fan-out, use SNS + SQS**
- SNS to multiple SQS queues
- Each consumer controls message retention
- Decoupled architecture

✓ **Use message attributes for filtering**
- Include routing information
- Enable selective delivery
- Improves efficiency

✓ **Separate topics by purpose**
- OrderEvents topic
- UserEvents topic
- SystemEvents topic
- Easier to manage and scale

✓ **Use JSON format**
```python
message = json.dumps({
    'event': 'order.created',
    'order_id': 123,
    'timestamp': datetime.now().isoformat()
})
client.publish(TopicArn=topic_arn, Message=message)
```

✓ **Include correlation IDs**
```python
import uuid
correlation_id = str(uuid.uuid4())
client.publish(
    TopicArn=topic_arn,
    Message=message,
    MessageAttributes={
        'CorrelationId': {'DataType': 'String', 'StringValue': correlation_id}
    }
)
```

✓ **Use FIFO only when ordering required**
- Standard topics are cheaper and faster
- FIFO has throughput limits
- Only use when necessary

### 16.2 Security Best Practices

✓ **Enable encryption**
- Use AWS managed or customer-managed KMS keys

✓ **Use IAM policies with principle of least privilege**
```json
{
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:*:*:SpecificTopic"
}
```

✓ **Set topic policies**
- Restrict who can publish/subscribe

✓ **Validate signatures**
- For HTTP endpoints, verify message signatures

✓ **Use VPC endpoints**
- For private access without internet

### 16.3 Operational Best Practices

✓ **Monitor subscription confirmation**
- For Email, users must click confirmation link
- Implement retry mechanism

✓ **Handle protocol-specific requirements**
- HTTP endpoints must respond quickly (200 OK)
- Lambda roles must allow sns:Publish

✓ **Log all events**
- Use CloudTrail for audit
- Monitor delivery failures

✓ **Set appropriate retention**
- SNS doesn't retain messages (unlike SQS)
- Use SQS if retention needed

---

## Summary

| Topic | Key Takeaway |
|-------|--------------|
| **Pub/Sub** | Decouple publishers from subscribers |
| **Protocols** | Support multiple delivery mechanisms |
| **Fan-Out** | SNS + SQS = scalable event distribution |
| **Filtering** | FilterPolicy reduces costs |
| **FIFO** | Use only for ordered delivery |
| **Security** | Enable encryption, IAM policies |
| **Monitoring** | Track publish and delivery metrics |

