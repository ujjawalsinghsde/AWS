# SES Interview Questions

## 1. Fundamental Questions

### Basic Concepts

1. **What is Amazon SES (Simple Email Service)?**
   - Email sending service (not email hosting)
   - Transactional and marketing email
   - Compliant sending (bounce/complaint handling)
   - Global email infrastructure
   - Sandbox mode (limited) → Production (scalable)

2. **Explain SES email sending process.**
   - Configure email address/domain (verify ownership)
   - Set up sending quota (request increase if needed)
   - Send email via API (very cheap)
   - Monitor: Bounces, complaints, opens, clicks
   - Reputation management: Keep complaint rate < 0.1%

3. **SES vs SNS vs other email services.**
   - **SES**: Raw email service, max control, volume discounts
   - **SNS**: Simple notifications (email, SMS), limited flexibility
   - **Third-party**: Sendgrid, Mailgun (more features, expensive)
   - Choose: SES for high volume, business emails; SNS for simple notifications

4. **Email verification in SES.**
   - Sandbox mode: Only send to verified email addresses
   - Production: Can send to any email (if reputation good)
   - Domain verification: Add DKIM, SPF records for sender
   - DKIM signatures: Prevent spoofing, improve deliverability
   - SPF record: Authorize SES to send on your domain

5. **SES pricing and quotas.**
   - First 200 emails/day: Free
   - Beyond: $0.10 per 1,000 emails
   - No setup fee, pay per email sent
   - Bounce/complaint rates monitored
   - Quota: Request increase from AWS
   - Cost optimization: Batch emails, optimize list

---

## 2. Intermediate Scenarios

### Email Templates & Configuration

6. **Scenario: Send templated transactional emails (password reset).**
   - SES Template:
     ```
     Subject: Password Reset Request
     Body: Hi {{name}}, click link to reset: {{resetLink}}
     ```
   - Process:
     1. Store template in SES
     2. Call SendTemplatedEmail with substitution values
     3. SES renders and sends
   - Benefits: Centralized templates, version control, A/B testing

7. **Implement email configuration sets for tracking.**
   - Configuration Set: Group related emails
   - Features:
     - Click tracking: Know which links users click
     - Open tracking: Know if email was opened
     - Bounce/complaint notifications: SNS, Kinesis Firehose
   - Use:
     1. Create configuration set
     2. Attach event destinations (SNS)
     3. Send email with ConfigurationSet parameter
     4. Process bounce/complaint events

### Bounce & Complaint Handling

8. **Handle email bounces and complaints.**
   - **Hard Bounce**: Address doesn't exist (permanent)
     - Action: Remove from mailing list immediately
     - Track: List of permanently invalid emails
   - **Soft Bounce**: Temporary issue (server down, full inbox)
     - Action: Retry later
     - After 3 retries: Treat as permanent
   - **Complaint**: User marked as spam
     - Action: Remove immediately, apologize if needed
     - High rate: May get suspended

9. **Process bounce notifications with SNS/SQS.**
   - Config set → SNS topic (bounce events)
   - SNS → SQS (reliable processing)
   - Consumer: Process bounces
     - Hard bounce: Remove contact
     - Soft bounce: Increment retry counter
     - Complaint: Remove contact, log incident
   ```json
   {
     "eventType": "Bounce",
     "bounce": {
       "bounceType": "Permanent",
       "bouncedRecipients": [
         {"emailAddress": "invalid@example.com"}
       ]
     }
   }
   ```

---

## 3. Advanced Scenarios

### Compliance & Deliverability

10. **Ensure high email deliverability.**
    - Reputation: Keep bounce rate < 5%, complaint < 0.1%
    - Authentication:
      - SPF: Authorize servers to send email
      - DKIM: Sign emails to prevent spoofing
      - DMARC: Policy for SPF/DKIM failure handling
    - List management:
      - Permission-based: Only send to opted-in users
      - Remove invalid addresses: Hard bounces
      - Monitor: Bounce and complaint metrics
    - Monitoring:
      - Warm up new IP reputation gradually
      - Start with known good addresses
      - Increase volume over time

11. **Implement compliance (CAN-SPAM, GDPR).**
    - **CAN-SPAM**: US email compliance
      - Identify as commercial email
      - Include physical address
      - Honor unsubscribe requests within 10 days
      - Monitor complaints
    - **GDPR**: European privacy regulation
      - Consent: Double opt-in required
      - Data: Store minimal personal data
      - Right to deletion: Remove contact on request
      - Data processor: Use Data Processing Agreement with SES

12. **Design unsubscribe and preference management.**
    - One-click unsubscribe: Easy for users
    - Preference center: Users choose email types
    - Implementation:
      - Include unsubscribe header
      - Process unsubscribe link immediately
      - Update DynamoDB with preference
      - Don't reengage without consent

---

## 4. Real-World Scenarios

13. **Scenario: Email delivery rate dropped to 70% (from 95%).**
    - Investigation:
      1. Check bounce rate: Increased hard/soft bounces?
      2. Check complaint rate: Users marking as spam?
      3. Review sending activity: Higher volume? New list?
      4. Check DNS: SPF, DKIM, DMARC records valid?
      5. AWS SES dashboard: Any warnings?
    - Solutions:
      - Pause sending, investigate
      - Review email content (avoid spam triggers)
      - Check list quality (remove invalid addresses)
      - Warm up reputation gradually
      - Fix authentication records

14. **Design bulk email campaign (100K emails/day).**
    - Planning:
      - Warm up: Start with 1K/day, increase over 2 weeks
      - Segmentation: Send to engaged users first
      - Quality: Remove bounces, complaints
    - Implementation:
      - SES API: Call SendBulkTemplatedEmail
      - Batch size: 1-50 per API call
      - Rate limiting: SES quota enforcement
      - Cost: ~$10 for 100K emails
    - Monitoring:
      - CloudWatch metrics: Send, bounce, complaint rates
      - Alarms: Alert if complaint rate spikes
      - Dashboard: Track campaign performance

15. **Integrate SES with application for notifications.**
    - Architecture:
      1. Application creates email (signup, password reset)
      2. Push to SQS (decoupled)
      3. Worker Lambda: Reads from SQS
      4. Call SES SendEmail
      5. Handle bounce/complaint events
    - Benefits:
      - Application doesn't wait for email send
      - Reliable delivery (retry via SQS)
      - Monitoring: Track success/failure

---

## 5. Best Practices

16. **SES best practices:**
    - Verify domain: SPF, DKIM, DMARC
    - High reputation: Monitor bounce/complaint rates
    - List management: Remove invalid addresses
    - Templates: Centralize for consistency
    - Configuration sets: Track engagement metrics
    - Unsubscribe: Easy, honored promptly
    - Compliance: CAN-SPAM, GDPR, CCPA
    - Monitoring: CloudWatch metrics and alarms
    - Cost control: Monitor sending volume
    - Rate limiting: Respect SES quotas

---

## 6. Hands-On Examples

17. **Send email using SES API:**
    ```python
    import boto3

    ses = boto3.client('ses', region_name='us-east-1')

    response = ses.send_email(
        Source='noreply@example.com',
        Destination={
            'ToAddresses': ['user@example.com'],
            'CcAddresses': ['manager@example.com']
        },
        Message={
            'Subject': {
                'Data': 'Order Confirmation',
                'Charset': 'UTF-8'
            },
            'Body': {
                'Html': {
                    'Data': '<h1>Your order #{orderId}</h1><p>Thank you!</p>',
                    'Charset': 'UTF-8'
                }
            }
        },
        ConfigurationSetName='campaign-tracking'
    )

    print(f"Message ID: {response['MessageId']}")
    ```

18. **Send templated email:**
    ```python
    response = ses.send_templated_email(
        Source='noreply@example.com',
        Destination={
            'ToAddresses': ['user@example.com']
        },
        Template='PasswordResetEmail',
        TemplateData=json.dumps({
            'name': 'John',
            'resetLink': 'https://example.com/reset?token=xyz'
        })
    )
    ```

19. **Handle bounce events with SNS:**
    ```python
    def lambda_handler(event, context):
        for record in event['Records']:
            message = json.loads(record['Sns']['Message'])

            if message['eventType'] == 'Bounce':
                bounce_type = message['bounce']['bounceType']
                recipients = message['bounce']['bouncedRecipients']

                for recipient in recipients:
                    email = recipient['emailAddress']

                    if bounce_type == 'Permanent':
                        remove_recipient(email)
                    elif bounce_type == 'Transient':
                        retry_later(email)

        return {'statusCode': 200}
    ```

---

## Tips for Interview Success

- **Email fundamentals**: SPF, DKIM, DMARC for authentication
- **Compliance**: CAN-SPAM, GDPR requirements
- **Reputation**: Bounce and complaint rate management
- **Deliverability**: Warm-up strategy for new IPs
- **Architecture**: Decouple email sending (SQS + Lambda)
- **Monitoring**: Track metrics, catch issues early
- **Cost**: Bulk email is very cheap with SES
- **Integration**: SNS for bounce/complaint notifications
- **List management**: Remove invalid addresses to maintain reputation
- **Templates**: Centralize for consistency and version control

