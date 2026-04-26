# SNS Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is SNS and how is it different from SQS?**
   - SNS: Pub/Sub messaging (one-to-many)
   - SQS: Message queue (one-to-one with polling)
   - SNS: Push-based delivery
   - SQS: Pull-based polling
   - Common pattern: SNS → SQS for decoupling

2. **Explain SNS topics and subscriptions.**
   - Topic: Communication channel
   - Subscription: Endpoint receiving messages
   - Multiple subscriptions per topic
   - Protocols: Email, SMS, HTTP, SQS, Lambda, SES, etc.

3. **SNS message filtering.**
   - Attributes: Associated with each message
   - Filter policy: Subscribe with conditions
   - Only receive matching messages
   - Reduce unnecessary processing

4. **SNS pricing.**
   - Per million requests
   - SMS charges per message
   - Email to SQS/Lambda: Cheaper than SMS
   - Free: First 1000 requests

5. **SNS reliability and retries.**
   - Automatic retries: Exponential backoff
   - Dead Letter Queue: Not native (use SQS)
   - Idempotent subscribers: Must handle duplicates
   - CloudWatch metrics for failures

---

## 2. Real-World Scenarios

6. **Scenario: Fan-out architecture (one event → multiple services).**
   - Order placed → SNS topic
   - Subscriptions:
     - SQS queue → Inventory service
     - SQS queue → Fulfillment service
     - Lambda → Send confirmation email
     - Email → Customer notification
   - Benefit: Services independent, loosely coupled

7. **Implement message filtering for event routing.**
   - Event types: order, payment, shipment
   - Subscribe with filter: Only receive "order" events
   - Reduces downstream processing
   - Example filter: `{"type": ["order"]}`

---

## Tips for Interview Success

- **Pub/Sub pattern**: Understanding is important
- **Fan-out use cases**: Common in microservices
- **Message filtering**: Optimization technique
- **Retry behavior**: Understand automatic retries
- **Integration with other services**: SQS, Lambda, Email

---

# SES & Secrets Manager

## SES (Simple Email Service)

1. **What is SES and its use cases?**
   - Email delivery service (not email server)
   - Transactional emails, marketing emails
   - Bulk sending
   - Integration with SNS for bounce/complaint handling
   - Sandbox mode (limited) then production

2. **SES email headers and sending parameters:**
   - Headers: From, To, Subject, Reply-To
   - Configuration sets: Track bounces, complaints
   - Sending rate: Progressively increase if compliant
   - Spam filtering: Comply with best practices

---

## Secrets Manager

1. **What is AWS Secrets Manager?**
   - Secure secret storage (passwords, API keys)
   - Automatic rotation support
   - Encryption with KMS
   - Audit logging with CloudTrail
   - Application integration via SDK

2. **Explain secret rotation.**
   - Automatic rotation every N days
   - Lambda function handles rotation logic
   - Versions: Multiple versions, gradual rollover
   - Zero-downtime rotation possible
   - Best practice: Rotate every 30 days

3. **Secrets Manager vs Parameter Store:**
   - **Secrets Manager**: Automatic rotation, built-in compliance
   - **Parameter Store**: Simpler, good for config
   - Choose: Secrets Manager for sensitive, Parameter Store for config

4. **Implement secure database credential management:**
   - Store RDS password in Secrets Manager
   - Lambda execution role: Access secret
   - Lambda: Fetch secret, connect to database
   - Rotation: Update password in RDS + Secrets Manager
   - No hardcoded credentials needed

5. **Real-world scenario: Rotate DB credentials without downtime.**
   - Old password: Still works
   - Lambda rotation: Generate new password
   - Update RDS with new password
   - Update Secrets Manager
   - Old password: Revoke after grace period
   - Applications: Fetch from Secrets Manager

6. **Secrets Manager pricing:**
   - Per secret per month
   - Free: First secret
   - Rotation: Lambda and API calls charged separately

---

## Tips for Interview Success

- **Security mindset**: Never hardcode credentials
- **Rotation strategies**: Understand different approaches
- **Integration patterns**: Lambda, SecretsManager, RDS
- **Audit requirements**: CloudTrail logging is important
- **Cost optimization**: Right tool for right job

