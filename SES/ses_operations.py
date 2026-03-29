"""
AWS SES (Simple Email Service) - Comprehensive Operations and Examples
Covers: Verification, Sending emails, Templates, Configuration Sets, Event handling
"""

import json
import boto3
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError


class SESClient:
    """Wrapper for AWS SES operations with common patterns"""

    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize SES client"""
        self.client = boto3.client('ses', region_name=region_name)
        self.sns_client = boto3.client('sns', region_name=region_name)

    # ==================== IDENTITY VERIFICATION ====================

    def verify_email_identity(self, email: str) -> bool:
        """Verify email address identity"""
        try:
            self.client.verify_email_identity(EmailAddress=email)
            print(f"✓ Verification email sent to {email}")
            print(f"  Check inbox for confirmation link")
            return True

        except ClientError as e:
            print(f"✗ Error verifying email: {e}")
            return False

    def verify_domain_identity(self, domain: str) -> Optional[str]:
        """Verify domain identity"""
        try:
            response = self.client.verify_domain_identity(Domain=domain)
            verification_token = response['VerificationToken']

            print(f"✓ Domain verification initiated for {domain}")
            print(f"  Add this TXT record to your DNS:")
            print(f"  Name: _amazonses.{domain}")
            print(f"  Value: {verification_token}")

            return verification_token

        except ClientError as e:
            print(f"✗ Error verifying domain: {e}")
            return None

    def verify_domain_dkim(self, domain: str) -> Optional[List[str]]:
        """Set up DKIM for domain"""
        try:
            response = self.client.verify_domain_dkim(Domain=domain)
            dkim_tokens = response['DkimTokens']

            print(f"✓ DKIM setup for {domain}")
            print(f"  Add these CNAME records:")
            for token in dkim_tokens:
                print(f"  {token}._domainkey.{domain}")
                print(f"    CNAME {token}.dkim.amazonses.com")

            return dkim_tokens

        except ClientError as e:
            print(f"✗ Error setting up DKIM: {e}")
            return None

    def list_verified_identities(self) -> Tuple[List[str], List[str]]:
        """List all verified identities"""
        try:
            email_response = self.client.list_identities(IdentityType='EmailAddress')
            domain_response = self.client.list_identities(IdentityType='Domain')

            email_identities = email_response.get('Identities', [])
            domain_identities = domain_response.get('Identities', [])

            print(f"✓ {len(email_identities)} email identities, {len(domain_identities)} domain identities")
            return email_identities, domain_identities

        except ClientError as e:
            print(f"✗ Error listing identities: {e}")
            return [], []

    def get_identity_verification_status(self, identity: str) -> Optional[Dict]:
        """Get verification status of identity"""
        try:
            response = self.client.get_identity_verification_attributes(
                Identities=[identity]
            )

            attrs = response['VerificationAttributes'].get(identity, {})
            status = attrs.get('VerificationStatus', 'Unknown')

            print(f"  Status: {status}")
            if status == 'Success':
                print(f"  DKIM Enabled: {attrs.get('DkimEnabled')}")

            return attrs

        except ClientError as e:
            print(f"✗ Error getting verification status: {e}")
            return None

    # ==================== SENDING EMAILS ====================

    def send_simple_email(self, source: str, recipients: List[str],
                         subject: str, body: str) -> Optional[str]:
        """Send simple text email"""
        try:
            response = self.client.send_email(
                Source=source,
                Destination={
                    'ToAddresses': recipients,
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            message_id = response['MessageId']
            print(f"✓ Email sent (ID: {message_id[:8]}...)")
            return message_id

        except ClientError as e:
            print(f"✗ Error sending email: {e}")
            return None

    def send_html_email(self, source: str, recipients: List[str],
                       subject: str, html_body: str,
                       text_body: Optional[str] = None) -> Optional[str]:
        """Send HTML email with fallback text"""
        try:
            if not text_body:
                text_body = 'HTML content - please view in an HTML-capable email client'

            response = self.client.send_email(
                Source=source,
                Destination={
                    'ToAddresses': recipients,
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            print(f"✓ HTML email sent (ID: {response['MessageId'][:8]}...)")
            return response['MessageId']

        except ClientError as e:
            print(f"✗ Error sending HTML email: {e}")
            return None

    def send_email_with_reply_to(self, source: str, recipients: List[str],
                                 subject: str, body: str,
                                 reply_to: str) -> Optional[str]:
        """Send email with custom reply-to address"""
        try:
            response = self.client.send_email(
                Source=source,
                Destination={'ToAddresses': recipients},
                ReplyToAddresses=[reply_to],
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )

            print(f"✓ Email sent with reply-to: {reply_to}")
            return response['MessageId']

        except ClientError as e:
            print(f"✗ Error sending email with reply-to: {e}")
            return None

    def send_email_with_cc_bcc(self, source: str, to: List[str],
                              subject: str, body: str,
                              cc: Optional[List[str]] = None,
                              bcc: Optional[List[str]] = None) -> Optional[str]:
        """Send email with CC and BCC recipients"""
        try:
            destination = {'ToAddresses': to}
            if cc:
                destination['CcAddresses'] = cc
            if bcc:
                destination['BccAddresses'] = bcc

            response = self.client.send_email(
                Source=source,
                Destination=destination,
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )

            print(f"✓ Email sent to {len(to)} recipients")
            if cc:
                print(f"  CC: {len(cc)} recipients")
            if bcc:
                print(f"  BCC: {len(bcc)} recipients")

            return response['MessageId']

        except ClientError as e:
            print(f"✗ Error sending email: {e}")
            return None

    def send_email_with_config_set(self, source: str, recipients: List[str],
                                  subject: str, body: str,
                                  config_set_name: str) -> Optional[str]:
        """Send email with configuration set (for tracking)"""
        try:
            response = self.client.send_email(
                Source=source,
                Destination={'ToAddresses': recipients},
                ConfigurationSetName=config_set_name,
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )

            print(f"✓ Email sent with tracking via {config_set_name}")
            return response['MessageId']

        except ClientError as e:
            print(f"✗ Error sending email: {e}")
            return None

    # ==================== EMAIL TEMPLATES ====================

    def create_template(self, template_name: str, subject: str,
                       text_body: str, html_body: str) -> bool:
        """Create email template"""
        try:
            self.client.create_template(
                Template={
                    'TemplateName': template_name,
                    'SubjectPart': subject,
                    'TextPart': text_body,
                    'HtmlPart': html_body
                }
            )

            print(f"✓ Template '{template_name}' created")
            return True

        except ClientError as e:
            print(f"✗ Error creating template: {e}")
            return False

    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get template details"""
        try:
            response = self.client.get_template(TemplateName=template_name)
            template = response['Template']

            print(f"✓ Template: {template['TemplateName']}")
            return template

        except ClientError as e:
            print(f"✗ Error getting template: {e}")
            return None

    def list_templates(self) -> List[Dict]:
        """List all templates"""
        try:
            response = self.client.list_templates()
            templates = response.get('TemplatesMetadata', [])

            print(f"Found {len(templates)} template(s)")
            for template in templates:
                print(f"  - {template['Name']}")

            return templates

        except ClientError as e:
            print(f"✗ Error listing templates: {e}")
            return []

    def update_template(self, template_name: str, subject: Optional[str] = None,
                       text_body: Optional[str] = None,
                       html_body: Optional[str] = None) -> bool:
        """Update existing template"""
        try:
            # Get current template
            response = self.client.get_template(TemplateName=template_name)
            template = response['Template']

            # Update fields
            if subject is None:
                subject = template['SubjectPart']
            if text_body is None:
                text_body = template['TextPart']
            if html_body is None:
                html_body = template['HtmlPart']

            self.client.update_template(
                Template={
                    'TemplateName': template_name,
                    'SubjectPart': subject,
                    'TextPart': text_body,
                    'HtmlPart': html_body
                }
            )

            print(f"✓ Template '{template_name}' updated")
            return True

        except ClientError as e:
            print(f"✗ Error updating template: {e}")
            return False

    def send_templated_email(self, source: str, recipients: List[str],
                            template_name: str,
                            template_data: Dict) -> Optional[str]:
        """Send email using template"""
        try:
            response = self.client.send_templated_email(
                Source=source,
                Destination={
                    'ToAddresses': recipients
                },
                Template=template_name,
                TemplateData=json.dumps(template_data)
            )

            print(f"✓ Templated email sent (ID: {response['MessageId'][:8]}...)")
            return response['MessageId']

        except ClientError as e:
            print(f"✗ Error sending templated email: {e}")
            return None

    def delete_template(self, template_name: str) -> bool:
        """Delete template"""
        try:
            self.client.delete_template(TemplateName=template_name)
            print(f"✓ Template '{template_name}' deleted")
            return True

        except ClientError as e:
            print(f"✗ Error deleting template: {e}")
            return False

    # ==================== CONFIGURATION SETS ====================

    def create_configuration_set(self, config_set_name: str) -> bool:
        """Create configuration set for tracking"""
        try:
            self.client.create_configuration_set(
                ConfigurationSet={
                    'Name': config_set_name
                }
            )

            print(f"✓ Configuration set '{config_set_name}' created")
            return True

        except ClientError as e:
            print(f"✗ Error creating configuration set: {e}")
            return False

    def add_event_destination(self, config_set_name: str,
                             event_name: str, event_types: List[str],
                             sns_topic_arn: str) -> bool:
        """Add event destination (SNS) to configuration set"""
        try:
            self.client.create_configuration_set_event_destination(
                ConfigurationSetName=config_set_name,
                EventDestination={
                    'Name': event_name,
                    'Enabled': True,
                    'MatchingEventTypes': event_types,
                    'SNSDestination': {
                        'TopicARN': sns_topic_arn
                    }
                }
            )

            print(f"✓ Event destination '{event_name}' added")
            print(f"  Events: {', '.join(event_types)}")
            return True

        except ClientError as e:
            print(f"✗ Error adding event destination: {e}")
            return False

    def create_complete_tracking_setup(self, config_set_name: str,
                                      sns_topic_arn: str) -> bool:
        """Create config set with all event tracking"""
        try:
            # Create config set
            self.create_configuration_set(config_set_name)

            # Add bounce events
            self.add_event_destination(
                config_set_name,
                'BounceEvents',
                ['bounce'],
                sns_topic_arn
            )

            # Add complaint events
            self.add_event_destination(
                config_set_name,
                'ComplaintEvents',
                ['complaint'],
                sns_topic_arn
            )

            # Add delivery events
            self.add_event_destination(
                config_set_name,
                'DeliveryEvents',
                ['delivery'],
                sns_topic_arn
            )

            # Add send events
            self.add_event_destination(
                config_set_name,
                'SendEvents',
                ['send'],
                sns_topic_arn
            )

            print(f"✓ Complete tracking setup created")
            return True

        except Exception as e:
            print(f"✗ Error creating tracking setup: {e}")
            return False

    def list_configuration_sets(self) -> List[Dict]:
        """List all configuration sets"""
        try:
            response = self.client.list_configuration_sets()
            config_sets = response.get('ConfigurationSets', [])

            print(f"Found {len(config_sets)} configuration set(s)")
            return config_sets

        except ClientError as e:
            print(f"✗ Error listing configuration sets: {e}")
            return []

    def delete_configuration_set(self, config_set_name: str) -> bool:
        """Delete configuration set"""
        try:
            self.client.delete_configuration_set(
                ConfigurationSetName=config_set_name
            )

            print(f"✓ Configuration set '{config_set_name}' deleted")
            return True

        except ClientError as e:
            print(f"✗ Error deleting configuration set: {e}")
            return False

    # ==================== SUPPRESSION LISTS ====================

    def get_suppressed_addresses(self, reason: str = 'BOUNCE') -> List[Dict]:
        """Get suppressed email addresses"""
        try:
            response = self.client.list_suppressed_destinations(
                Reason=reason,
                ListType='MANAGED'  # AWS managed list
            )

            destinations = response.get('SuppressedDestinationAttributes', [])
            print(f"Found {len(destinations)} suppressed address(es) ({reason})")

            for dest in destinations[:5]:  # Show first 5
                print(f"  - {dest['EmailAddress']}")

            return destinations

        except ClientError as e:
            print(f"✗ Error getting suppressed addresses: {e}")
            return []

    def check_if_suppressed(self, email: str) -> bool:
        """Check if email is in suppression list"""
        try:
            response = self.client.get_suppressed_destination(
                EmailAddress=email
            )

            if 'Attributes' in response:
                print(f"✓ {email} is suppressed")
                return True

            return False

        except self.client.exceptions.NotFoundException:
            print(f"✓ {email} is not suppressed")
            return False

        except ClientError as e:
            print(f"✗ Error checking suppression: {e}")
            return False

    # ==================== ACCOUNT STATUS ====================

    def get_account_sending_enabled(self) -> bool:
        """Check if sending is enabled"""
        try:
            response = self.client.get_account_sending_enabled()
            enabled = response['Enabled']

            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"Sending Status: {status}")

            return enabled

        except ClientError as e:
            print(f"✗ Error checking account status: {e}")
            return False

    def get_account_details(self) -> Optional[Dict]:
        """Get account details (limits, etc.)"""
        try:
            response = self.client.get_account_details()

            details = response.get('AccountDetails', {})
            print("\n📊 Account Details:")

            for key, value in details.items():
                print(f"  {key}: {value}")

            return details

        except ClientError as e:
            print(f"✗ Error getting account details: {e}")
            return None

    # ==================== BULK SENDING ====================

    def send_bulk_email(self, source: str, recipients: List[str],
                       subject: str, body: str,
                       rate_limit: float = 1.0) -> Dict[str, int]:
        """Send email to multiple recipients with rate limiting"""
        """rate_limit: emails per second"""
        delay = 1.0 / rate_limit
        success_count = 0
        fail_count = 0

        print(f"\n📧 Sending to {len(recipients)} recipients...")

        for i, recipient in enumerate(recipients):
            try:
                self.send_simple_email(source, [recipient], subject, body)
                success_count += 1

                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{len(recipients)}")

                time.sleep(delay)

            except Exception as e:
                print(f"  ✗ Failed to send to {recipient}: {e}")
                fail_count += 1

        print(f"\n✓ Results: {success_count} success, {fail_count} failed")
        return {'success': success_count, 'failed': fail_count}

    def send_bulk_templated_email(self, source: str,
                                 recipients_with_data: List[Tuple[str, Dict]],
                                 template_name: str,
                                 rate_limit: float = 1.0) -> Dict[str, int]:
        """Send templated emails to multiple recipients"""
        delay = 1.0 / rate_limit
        success_count = 0
        fail_count = 0

        print(f"\n📧 Sending templated emails to {len(recipients_with_data)} recipients...")

        for i, (recipient, template_data) in enumerate(recipients_with_data):
            try:
                self.send_templated_email(
                    source,
                    [recipient],
                    template_name,
                    template_data
                )
                success_count += 1

                if (i + 1) % 10 == 0:
                    print(f"  Progress: {i + 1}/{len(recipients_with_data)}")

                time.sleep(delay)

            except Exception as e:
                print(f"  ✗ Failed to send to {recipient}: {e}")
                fail_count += 1

        print(f"\n✓ Results: {success_count} success, {fail_count} failed")
        return {'success': success_count, 'failed': fail_count}


# ==================== EVENT HANDLERS ====================

def handle_bounce_event(sns_message: Dict) -> Dict:
    """Process SES bounce notification from SNS"""
    message = json.loads(sns_message['Message'])
    bounce = message.get('bounce', {})

    bounce_type = bounce.get('bounceType')
    bounced_recipients = bounce.get('bouncedRecipients', [])

    result = {
        'type': bounce_type,
        'recipients': []
    }

    for recipient in bounced_recipients:
        email = recipient['emailAddress']
        status = recipient.get('status')
        result['recipients'].append({
            'email': email,
            'status': status
        })

    return result


def handle_complaint_event(sns_message: Dict) -> Dict:
    """Process SES complaint notification from SNS"""
    message = json.loads(sns_message['Message'])
    complaint = message.get('complaint', {})

    complained_recipients = complaint.get('complainedRecipients', [])

    result = {
        'complained': len(complained_recipients),
        'recipients': [r['emailAddress'] for r in complained_recipients]
    }

    return result


def handle_delivery_event(sns_message: Dict) -> Dict:
    """Process SES delivery notification from SNS"""
    message = json.loads(sns_message['Message'])
    delivery = message.get('delivery', {})

    recipients = delivery.get('recipients', [])
    timestamp = delivery.get('timestamp')

    return {
        'recipients': recipients,
        'timestamp': timestamp,
        'count': len(recipients)
    }


def handle_send_event(sns_message: Dict) -> Dict:
    """Process SES send notification from SNS"""
    message = json.loads(sns_message['Message'])
    send_data = message.get('send', {})

    return {
        'timestamp': send_data.get('timestamp'),
        'source': send_data.get('source')
    }


# ==================== USAGE EXAMPLES ====================

def example_verify_email():
    """Verify email identity"""
    print("\n=== VERIFY EMAIL ===")
    ses = SESClient()
    ses.verify_email_identity('sender@example.com')


def example_send_simple():
    """Send simple email"""
    print("\n=== SEND SIMPLE EMAIL ===")
    ses = SESClient()

    ses.send_simple_email(
        source='sender@example.com',
        recipients=['recipient@example.com'],
        subject='Test Email',
        body='This is a test email'
    )


def example_send_html():
    """Send HTML email"""
    print("\n=== SEND HTML EMAIL ===")
    ses = SESClient()

    html = '''
    <html>
        <body>
            <h1>Welcome!</h1>
            <p>Thank you for joining.</p>
        </body>
    </html>
    '''

    ses.send_html_email(
        source='sender@example.com',
        recipients=['recipient@example.com'],
        subject='HTML Email',
        html_body=html
    )


def example_create_template():
    """Create and use email template"""
    print("\n=== EMAIL TEMPLATES ===")
    ses = SESClient()

    # Create template
    ses.create_template(
        template_name='WelcomeEmail',
        subject='Welcome {{Name}}!',
        text_body='Hello {{Name}}, welcome to our service!',
        html_body='<h1>Welcome {{Name}}!</h1><p>Thank you for joining.</p>'
    )

    # Send using template
    ses.send_templated_email(
        source='sender@example.com',
        recipients=['recipient@example.com'],
        template_name='WelcomeEmail',
        template_data={'Name': 'John'}
    )


def example_configuration_set():
    """Create configuration set with tracking"""
    print("\n=== CONFIGURATION SET ===")
    ses = SESClient()
    sns = boto3.client('sns', region_name='us-east-1')

    # Create SNS topic for events
    response = sns.create_topic(Name='SESEventsTopic')
    topic_arn = response['TopicArn']

    # Create config set with tracking
    ses.create_complete_tracking_setup(
        config_set_name='MyEmailTracking',
        sns_topic_arn=topic_arn
    )

    # Send email with tracking
    ses.send_email_with_config_set(
        source='sender@example.com',
        recipients=['recipient@example.com'],
        subject='Tracked Email',
        body='This email is tracked',
        config_set_name='MyEmailTracking'
    )


if __name__ == '__main__':
    # Uncomment to run examples
    # example_verify_email()
    # example_send_simple()
    # example_send_html()
    # example_create_template()
    # example_configuration_set()

    print("\n✓ SES operations module ready")
    print("Import SESClient and use methods for SES operations")
    print("\nExample:")
    print("  from ses_operations import SESClient")
    print("  ses = SESClient()")
    print("  ses.verify_email_identity('sender@example.com')")
    print("  ses.send_simple_email('sender@example.com', ['recipient@example.com'], 'Subject', 'Body')")

