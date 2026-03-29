# AWS SES (Simple Email Service)

**Python boto3 code:** [ses_operations.py](./ses_operations.py)

---

## Table of Contents

1. [What is AWS SES?](#1-what-is-aws-ses)
2. [Core Concepts](#2-core-concepts)
3. [Identity Verification](#3-identity-verification)
4. [Sending Emails](#4-sending-emails)
5. [Email Templates](#5-email-templates)
6. [Suppression Lists](#6-suppression-lists)
7. [Configuration Sets](#7-configuration-sets)
8. [Event Publishers](#8-event-publishers)
9. [Bounce & Complaint Handling](#9-bounce--complaint-handling)
10. [Dashboard & Sandbox Mode](#10-dashboard--sandbox-mode)
11. [DKIM & SPF Verification](#11-dkim--spf-verification)
12. [Bulk Sending](#12-bulk-sending)
13. [Cost Optimization](#13-cost-optimization)
14. [Best Practices](#14-best-practices)
15. [Common Architectures](#15-common-architectures)
16. [SES CLI Cheat Sheet](#16-ses-cli-cheat-sheet)

---

## 1. What is AWS SES?

**Amazon SES (Simple Email Service)** is a cost-effective, flexible, and scalable email service for sending transactional emails, marketing messages, and notifications.

### Key Characteristics

- **Fully Managed** — No email infrastructure to maintain
- **High Deliverability** — Built-in reputation management
- **Scalable** — Send from few emails to millions per day
- **Cost-Effective** — ~$0.10 per 1000 emails (with free credits)
- **Multiple Sending Options** — SMTP, boto3 API, or integration with other AWS services
- **Detailed Metrics** — Track bounces, complaints, opens, clicks
- **Real-time Feedback** — Known bounces and complaints via SNS

### When to Use SES

✓ Transactional emails (order confirmations, password resets, receipts)
✓ Marketing campaigns
✓ Notifications
✓ Bulk email sending
✓ High-volume email delivery
✓ Integration with Lambda, SNS, applications

---

## 2. Core Concepts

### 2.1 Identities

An **identity** is an email address or domain from which you send emails.

```
Email Identity:    sender@example.com
Domain Identity:   example.com (can send from any address in domain)

Verification:
- Email identity: Click verification link sent to that email
- Domain identity: Add DKIM/SPF records to DNS
```

### 2.2 Sending Limits

```
Sandbox Mode (default):
- Max 200 emails per 24 hours
- Max 1 email per second
- Only send to verified addresses
- Good for testing

Production Mode:
- Requested via support ticket or trusted AWS account
- No daily sending limit
- Rate limit: 14 emails per second (can request increase)
- Can send to any address
```

### 2.3 Email Structure

```
From: sender@example.com
To: recipient@example.com
Subject: Order Confirmation
Headers: (metadata)
Body: Plain text and/or HTML
Attachments: Optional

Maximum email size: 40 MB (including attachments)
```

---

## 3. Identity Verification

### 3.1 Email Identity Verification

```python
import boto3

client = boto3.client('ses', region_name='us-east-1')

# Verify email address
response = client.verify_email_identity(EmailAddress='sender@example.com')
print("Verification email sent to sender@example.com")

# User receives email with verification link
# Click link to activate identity
```

### 3.2 Domain Identity Verification

```python
# Verify domain
response = client.verify_domain_identity(Domain='example.com')
dkim_tokens = response['VerificationToken']

print(f"Add TXT record to DNS:")
print(f"  Name: _amazonses.example.com")
print(f"  Value: {dkim_tokens}")

# After DNS update, check verification
response = client.verify_domain_dkim(Domain='example.com')
dkim_tokens = response['DkimTokens']  # 3 tokens

print(f"\nAdd CNAME records for DKIM:")
for token in dkim_tokens:
    print(f"  {token}._domainkey.example.com CNAME {token}.dkim.amazonses.com")
```

### 3.3 List Verified Identities

```python
# List all verified identities
response = client.list_identities(IdentityType='EmailAddress')
email_identities = response['Identities']

response = client.list_identities(IdentityType='Domain')
domain_identities = response['Identities']

print(f"Email Identities: {email_identities}")
print(f"Domain Identities: {domain_identities}")
```

### 3.4 Get Identity Verification Status

```python
response = client.get_identity_verification_attributes(
    Identities=['sender@example.com', 'example.com']
)

for identity, attrs in response['VerificationAttributes'].items():
    status = attrs['VerificationStatus']
    print(f"{identity}: {status}")

    if status == 'Success':
        print(f"  DKIM Enabled: {attrs.get('DkimEnabled')}")
        print(f"  SPF Verified: {attrs.get('DkimVerificationStatus')}")
```

---

## 4. Sending Emails

### 4.1 Send Simple Email

```python
# Basic send using API
response = client.send_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['recipient@example.com'],
    },
    Message={
        'Subject': {
            'Data': 'Order Confirmation',
            'Charset': 'UTF-8'
        },
        'Body': {
            'Text': {
                'Data': 'Your order has been received.',
                'Charset': 'UTF-8'
            }
        }
    }
)

message_id = response['MessageId']
print(f"Email sent (ID: {message_id})")
```

### 4.2 Send HTML Email

```python
response = client.send_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['recipient@example.com'],
    },
    Message={
        'Subject': {
            'Data': 'Order Confirmation',
            'Charset': 'UTF-8'
        },
        'Body': {
            'Html': {
                'Data': '''
                <html>
                    <body>
                        <h1>Order Confirmation</h1>
                        <p>Thank you for your order!</p>
                        <p>Order #: 123456</p>
                    </body>
                </html>
                ''',
                'Charset': 'UTF-8'
            },
            'Text': {
                'Data': 'Order Confirmation\nThank you for your order!\nOrder #: 123456',
                'Charset': 'UTF-8'
            }
        }
    }
)
```

### 4.3 Send with CC/BCC

```python
response = client.send_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['user@example.com'],
        'CcAddresses': ['admin@example.com'],
        'BccAddresses': ['archive@example.com']
    },
    Message={
        'Subject': {
            'Data': 'Important Notification'
        },
        'Body': {
            'Text': {
                'Data': 'Email content here'
            }
        }
    }
)
```

### 4.4 Send with Reply-To

```python
response = client.send_email(
    Source='noreply@example.com',
    Destination={
        'ToAddresses': ['recipient@example.com']
    },
    ReplyToAddresses=['support@example.com'],  # Reply goes here
    Message={
        'Subject': {
            'Data': 'Support Response'
        },
        'Body': {
            'Text': {
                'Data': 'How can we help?'
            }
        }
    }
)
```

### 4.5 Send Raw Email

```python
# For advanced email control (MIME format)
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create message
msg = MIMEMultipart()
msg['Subject'] = 'Test Email'
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'

# Add body
body = MIMEText('Email body here')
msg.attach(body)

# Send raw
response = client.send_raw_email(
    Source='sender@example.com',
    RawMessage={
        'Data': msg.as_string()
    }
)
```

---

## 5. Email Templates

### 5.1 Creating Templates

```python
# Create template
template_name = 'OrderConfirmation'

client.create_template(
    Template={
        'TemplateName': template_name,
        'SubjectPart': 'Order Confirmation - {{OrderId}}',
        'TextPart': '''
Dear {{CustomerName}},

Thank you for your order #{{OrderId}}.

Order Total: ${{Amount}}

Best regards,
The Team
        ''',
        'HtmlPart': '''
<html>
<body>
    <h1>Order Confirmation</h1>
    <p>Dear {{CustomerName}},</p>
    <p>Thank you for your order <strong>#{{OrderId}}</strong>.</p>
    <p>Order Total: <strong>${{Amount}}</strong></p>
    <p>Best regards,<br>The Team</p>
</body>
</html>
        '''
    }
)

print(f"Template '{template_name}' created")
```

### 5.2 Sending Templated Email

```python
response = client.send_templated_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['customer@example.com']
    },
    Template='OrderConfirmation',
    TemplateData=json.dumps({
        'OrderId': '12345',
        'CustomerName': 'John Doe',
        'Amount': '99.99'
    })
)

print(f"Templated email sent (ID: {response['MessageId']})")
```

### 5.3 Managing Templates

```python
# List templates
response = client.list_templates()
templates = response.get('TemplatesMetadata', [])

# Get template
response = client.get_template(TemplateName='OrderConfirmation')
template = response['Template']

# Update template
client.update_template(
    Template={
        'TemplateName': 'OrderConfirmation',
        'SubjectPart': 'New subject here'
    }
)

# Delete template
client.delete_template(TemplateName='OrderConfirmation')
```

---

## 6. Suppression Lists

### 6.1 Bounce List

```python
# Get suppressed addresses (bounces)
response = client.list_suppressed_destinations(
    Reason='BOUNCE',
    ListType='MANAGED'  # AWS managed list
)

for item in response['SuppressedDestinationAttributes']:
    email = item['EmailAddress']
    reason = item['Reason']
    print(f"{email} - {reason}")

# Check if address is suppressed
response = client.get_suppressed_destination(
    EmailAddress='bounced@example.com'
)
```

### 6.2 Complaint List

```python
# Get suppressed addresses (complaints)
response = client.list_suppressed_destinations(
    Reason='COMPLAINT',
    ListType='MANAGED'
)

# Users who marked email as spam
for item in response['SuppressedDestinationAttributes']:
    print(f"Complaint: {item['EmailAddress']}")
```

### 6.3 Managed Suppression List

```python
# AWS maintains automatic suppression list
# Hard bounces, permanent failures, spam complaints
# Automatically suppressed

# Check account-level suppression status
response = client.get_account_sending_enabled()
print(f"Sending Enabled: {response['Enabled']}")

# Check if suspended
response = client.get_account_details()
```

---

## 7. Configuration Sets

### 7.1 Creating Configuration Sets

```python
# Create configuration set for event tracking
config_set_name = 'MyAppEvents'

client.create_configuration_set(
    ConfigurationSet={
        'Name': config_set_name
    }
)

print(f"Configuration set '{config_set_name}' created")
```

### 7.2 Adding Event Destinations

```python
import boto3

# Publish events to SNS
sns_topic_arn = 'arn:aws:sns:us-east-1:123456789012:EmailEvents'

# Add bounce event destination
client.create_configuration_set_event_destination(
    ConfigurationSetName='MyAppEvents',
    EventDestination={
        'Name': 'BounceEventDestination',
        'Enabled': True,
        'MatchingEventTypes': ['bounce'],
        'SNSDestination': {
            'TopicARN': sns_topic_arn
        }
    }
)

# Add complaint event destination
client.create_configuration_set_event_destination(
    ConfigurationSetName='MyAppEvents',
    EventDestination={
        'Name': 'ComplaintEventDestination',
        'Enabled': True,
        'MatchingEventTypes': ['complaint'],
        'SNSDestination': {
            'TopicARN': sns_topic_arn
        }
    }
)

# Add delivery event destination
client.create_configuration_set_event_destination(
    ConfigurationSetName='MyAppEvents',
    EventDestination={
        'Name': 'DeliveryEventDestination',
        'Enabled': True,
        'MatchingEventTypes': ['delivery'],
        'SNSDestination': {
            'TopicARN': sns_topic_arn
        }
    }
)

# Add send event destination
client.create_configuration_set_event_destination(
    ConfigurationSetName='MyAppEvents',
    EventDestination={
        'Name': 'SendEventDestination',
        'Enabled': True,
        'MatchingEventTypes': ['send'],
        'SNSDestination': {
            'TopicARN': sns_topic_arn
        }
    }
)
```

### 7.3 Using Configuration Sets

```python
# Send email with configuration set
response = client.send_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['recipient@example.com']
    },
    ConfigurationSetName='MyAppEvents',  # Track this email
    Message={
        'Subject': {
            'Data': 'Test Email'
        },
        'Body': {
            'Text': {
                'Data': 'Tracking enabled'
            }
        }
    }
)
```

### 7.4 Reputation Tracking

```python
# Get sending statistics
response = client.get_account_sending_enabled()

# Get configuration set statistics
response = client.get_configuration_set_statistics(
    ConfigurationSetName='MyAppEvents'
)

stats = response.get('DeliveryOptions', {})
# Track bounces, complaints, etc.
```

---

## 8. Event Publishers

### 8.1 Understanding Events

```
SEND Event:
- Email accepted by SES
- Fired immediately
- Earliest notification

BOUNCE Event:
- Hard bounce: Invalid email (permanent failure)
- Soft bounce: Temporary failure (mailbox full, service down)
- Transient: Retried automatically
- Permanent: Added to suppression list

COMPLAINT Event:
- Recipient marked email as spam
- Always added to suppression list
- Should remove from mailing list

DELIVERY Event:
- Email delivered to recipient inbox
- Network acknowledgment received

OPEN Event:
- Recipient opened email
- Requires tracking pixel in email

CLICK Event:
- Recipient clicked link in email
- Requires tracked links
```

---

## 9. Bounce & Complaint Handling

### 9.1 Processing Bounce Notifications

```python
import json

def handle_bounce_notification(sns_message):
    """Handle SES bounce notification from SNS"""
    message = json.loads(sns_message['Message'])

    bounce = message['bounce']
    bounce_type = bounce['bounceType']  # 'Permanent' or 'Transient'

    if bounce_type == 'Permanent':
        # Hard bounces - remove from mailing list
        for recipient in bounce['bouncedRecipients']:
            email = recipient['emailAddress']
            print(f"Permanent bounce: {email}")
            # Delete from database

    elif bounce_type == 'Transient':
        # Soft bounces - retry later
        for recipient in bounce['bouncedRecipients']:
            email = recipient['emailAddress']
            print(f"Transient bounce: {email} - Will retry")
            # Schedule retry
```

### 9.2 Processing Complaint Notifications

```python
def handle_complaint_notification(sns_message):
    """Handle SES complaint notification from SNS"""
    message = json.loads(sns_message['Message'])

    complaint = message['complaint']

    # Recipient marked as spam
    for recipient in complaint['complainedRecipients']:
        email = recipient['emailAddress']
        print(f"Spam complaint: {email}")
        # Remove from list immediately
        # Don't send to this address again
```

---

## 10. Dashboard & Sandbox Mode

### 10.1 Sandbox Mode

```
Sandbox Mode (Default):
- Limited to 200 emails per 24 hours
- Max 1 email per second
- Only verified recipients
- Good for development/testing

Production Access:
- Apply via AWS Support
- Requires valid email list
- Establishes sending reputation
- Better deliverability

To Request Production Access:
1. Go to SES console
2. Click "Request Production Access"
3. Explain use case
4. Usually approved within 24 hours
```

### 10.2 Viewing Sending Statistics

```python
# Get account statistics
response = client.get_account_sending_enabled()
print(f"Sending Enabled: {response['Enabled']}")

# Get configuration set details
response = client.get_configuration_set(
    ConfigurationSetName='MyAppEvents'
)

# Get event destination details
response = client.get_configuration_set_event_destinations(
    ConfigurationSetName='MyAppEvents'
)
```

---

## 11. DKIM & SPF Verification

### 11.1 DKIM (DomainKeys Identified Mail)

```
DKIM signs emails cryptographically
Receives prove email wasn't modified
Improves deliverability

Setup:
1. SES provides 3 CNAME records
2. Add to domain DNS
3. AWS automatically signs emails
4. Recipients can verify signature

Example CNAME record:
token._domainkey.example.com CNAME token.dkim.amazonses.com
```

### 11.2 SPF (Sender Policy Framework)

```
SPF record tells recipients which IPs can send email

Example SPF record:
v=spf1 include:amazonses.com ~all

Points to SES servers
Prevents spoofing
```

### 11.3 Adding DKIM

```python
# Get DKIM tokens
response = client.verify_domain_dkim(Domain='example.com')
dkim_tokens = response['DkimTokens']

print("Add these CNAME records to your DNS:")
for token in dkim_tokens:
    print(f"{token}._domainkey.example.com CNAME {token}.dkim.amazonses.com")

# Enable DKIM signing
# Done automatically after DNS records added
```

---

## 12. Bulk Sending

### 12.1 Bulk Email with BCC

```python
# Send same email to many recipients (limited)
recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']

response = client.send_email(
    Source='sender@example.com',
    Destination={
        'ToAddresses': ['undisclosed-recipients@example.com'],
        'BccAddresses': recipients  # Use BCC for bulk
    },
    Message={
        'Subject': {'Data': 'Bulk News'},
        'Body': {'Text': {'Data': 'Newsletter content'}}
    }
)
```

### 12.2 Sending Emails in Loop

```python
def send_bulk_emails(recipients, subject, body):
    """Send email to multiple recipients"""
    success_count = 0
    fail_count = 0

    for recipient in recipients:
        try:
            response = client.send_email(
                Source='sender@example.com',
                Destination={'ToAddresses': [recipient]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            success_count += 1
            print(f"✓ Sent to {recipient}")

        except Exception as e:
            fail_count += 1
            print(f"✗ Failed to send to {recipient}: {e}")

    print(f"\nResults: {success_count} success, {fail_count} failed")

# Example
recipients = ['user1@example.com', 'user2@example.com']
send_bulk_emails(recipients, 'Newsletter', 'Monthly news...')
```

### 12.3 Rate Limiting

```python
import time

# SES limit: 1 email per second in sandbox, ~14 in production

def send_bulk_with_rate_limit(recipients, subject, body, rate_per_second=1):
    """Send emails with rate limiting"""
    delay = 1 / rate_per_second

    for i, recipient in enumerate(recipients):
        try:
            client.send_email(
                Source='sender@example.com',
                Destination={'ToAddresses': [recipient]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            print(f"✓ Sent {i+1}/{len(recipients)}")

        except Exception as e:
            print(f"✗ Error: {e}")

        time.sleep(delay)
```

---

## 13. Cost Optimization

### 13.1 Pricing Model

```
Standard Pricing:
- $0.10 per 1,000 emails sent (on-demand)
- Incoming emails: $0.10 per 1,000 emails

Volume Discounts:
- 5M emails/month: $0.09 per 1,000
- 10M emails/month: $0.08 per 1,000
- 25M emails/month: Custom pricing

Free tier (new customers):
- 6,250 emails per day
- 62,500 emails per month
- No charge first 12 months (AWS free tier)
```

### 13.2 Cost Reduction Strategies

```
1. Use templates
   - Store formatted emails
   - Reduce payload size

2. Batch uploads
   - Group similar emails
   - Better efficiency

3. Monitor bounces/complaints
   - Remove problematic addresses
   - Avoid wasted sends

4. Use text emails when possible
   - HTML emails slightly larger
   - Both work fine

5. Improve list quality
   - Verify email addresses upfront
   - Reduce bounces

6. Use configuration sets efficiently
   - Track important emails only
   - Not all emails need tracking
```

---

## 14. Best Practices

### 14.1 Setup Best Practices

✓ **Verify domain, not just email**
- More professional (no "amazon.com" in From)
- Can send from any address in domain
- Set up DKIM and SPF

✓ **Start with templates**
```python
template = {
    'TemplateName': 'OrderConfirmation',
    'SubjectPart': 'Your order {{OrderId}} confirmed',
    'HtmlPart': '<h1>Order {{OrderId}}</h1>...'
}
```

✓ **Set up configuration sets immediately**
- Track bounces, complaints, deliveries
- Respond to real-time feedback

✓ **Monitor your sending**
```python
# Create CloudWatch alarms
cloudwatch.put_metric_alarm(
    AlarmName='SES-HighBounceRate',
    MetricName='Bounce',  # At typical 5% is normal
    Namespace='AWS/SES',
    ...
)
```

### 14.2 Sending Best Practices

✓ **Always include Reply-To header**
```python
response = client.send_email(
    Source='noreply@example.com',
    ReplyToAddresses=['support@example.com'],  # Where replies go
    ...
)
```

✓ **Use sensible From address**
- No-reply addresses for transactional mail
- Recognizable from other services

✓ **Always send both Text and HTML versions**
```python
'Body': {
    'Text': {'Data': 'Plain text version'},
    'Html': {'Data': '<html>...'}
}
```

✓ **Include unsubscribe mechanism**
- Legal requirement in many jurisdictions
- Reduces complaints

✓ **Don't send to invalid addresses**
- Verify emails before sending
- Monitor suppression list
- Clean old addresses

✓ **Test deliverability**
- Use services like Mail Tester
- Aim for 99%+ inbox placement
- Monitor reputation

### 14.3 Compliance Best Practices

✓ **CAN-SPAM compliance**
- Include physical mailing address
- Include unsubscribe link
- Honor unsubscribe requests within 10 days
- Clear subject line

✓ **GDPR compliance**
- Only send to opted-in addresses
- Provide unsubscribe option
- Honor "right to be forgotten"

✓ **Monitor suppressions**
```python
# Handle bounces immediately
# Remove from list permanently

# Handle complaints immediately
# Never send to complaining address again
```

### 14.4 Production Best Practices

✓ **Request production access**
- Remove 200 email/day limit
- Better reputation management

✓ **Warm up sending**
- Start with low volume
- Gradually increase over time
- Builds reputation with ISPs

✓ **Monitor metrics**
- Bounce rate (should be <5%)
- Complaint rate (should be <0.1%)
- Delivery rate (should be >95%)

✓ **Maintain separate bounce list**
```python
def handle_bounce(email):
    """Track permanent bounces"""
    # Store in database
    # Never send to this address again
    # Update user status
```

---

## 15. Common Architectures

### 15.1 Transactional Email with Lambda

```
[Event] (order created)
  ↓
[Lambda] (triggered)
  ↓
[SES] (send email)
  ↓
[SNS] (bounce/complaint events)
  ↓
[Database] (log delivery, handle bounces)
```

### 15.2 Marketing Email Campaign

```
[Upload Recipients] → [Template] → [SES]
          ↓                          ↓
    [Database]               [Configuration Set]
          ↓                          ↓
    [Check suppression]     [Track events via SNS]
          ↓                          ↓
    [Send campaign]        [Update metrics]
          ↓
    [Monitor & adjust]
```

### 15.3 Email with SNS Notifications

```
[SES] → [Configuration Set]
          ├─→ [Bounce Event] → [SNS] → [Lambda] → Remove from list
          ├─→ [Complaint Event] → [SNS] → [Lambda] → Block sender
          ├─→ [Delivery Event] → [SNS] → [Lambda] → Log delivery
          └─→ [Open/Click Events] → [SNS] → [Analytics]
```

---

## 16. SES CLI Cheat Sheet

```bash
# Verify email identity
aws ses verify-email-identity \
  --email-address sender@example.com

# Verify domain identity
aws ses verify-domain-identity \
  --domain example.com

# Get DKIM tokens
aws ses verify-domain-dkim --domain example.com

# List identities
aws ses list-identities --identity-type EmailAddress

# Send email
aws ses send-email \
  --source sender@example.com \
  --destination ToAddresses=recipient@example.com \
  --message 'Subject={Data=Test},Body={Text={Data=Hello}}'

# Create template
aws ses create-template \
  --template TemplateName=MyTemplate,SubjectPart='Test',TextPart='Body'

# Send templated email
aws ses send-templated-email \
  --source sender@example.com \
  --destination ToAddresses=recipient@example.com \
  --template MyTemplate \
  --template-data '{"Name":"John"}'

# Get sending statistics
aws ses get-account-sending-enabled

# Get suppressed addresses
aws ses list-suppressed-destinations --reason BOUNCE
aws ses list-suppressed-destinations --reason COMPLAINT

# Create configuration set
aws ses create-configuration-set --configuration-set Name=MySet

# Get configuration set
aws ses get-configuration-set --configuration-set-name MySet
```

---

## Summary

| Topic | Key Takeaway |
|-------|--------------|
| **Identities** | Verify email or domain before sending |
| **Templates** | Use templates for consistent formatting |
| **Events** | Configure SNS for bounce/complaint notifications |
| **Suppressions** | Handle bounces and complaints automatically |
| **Configuration Sets** | Track email metrics and events |
| **DKIM/SPF** | Improve deliverability with authentication |
| **Cost** | Start in sandbox, monitor metrics, scale carefully |
| **Compliance** | Follow CAN-SPAM and GDPR requirements |

