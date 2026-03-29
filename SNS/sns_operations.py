"""
AWS SNS (Simple Notification Service) - Comprehensive Operations and Examples
Covers: Topics, Subscriptions, Publishing, Filtering, Fan-Out patterns
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError


class SNSClient:
    """Wrapper for AWS SNS operations with common patterns"""

    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize SNS client"""
        self.client = boto3.client('sns', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)

    # ==================== TOPIC MANAGEMENT ====================

    def create_topic(self, topic_name: str, fifo: bool = False,
                     content_dedup: bool = False) -> str:
        """Create SNS topic"""
        try:
            attrs = {}
            if fifo:
                topic_name = topic_name if topic_name.endswith('.fifo') else f"{topic_name}.fifo"
                attrs['FifoTopic'] = 'true'
                if content_dedup:
                    attrs['ContentBasedDeduplication'] = 'true'

            response = self.client.create_topic(
                Name=topic_name,
                Attributes=attrs if attrs else None
            )
            topic_arn = response['TopicArn']
            print(f"✓ Created {'FIFO' if fifo else 'standard'} topic: {topic_name}")
            return topic_arn

        except ClientError as e:
            print(f"✗ Error creating topic: {e}")
            raise

    def get_topic_arn(self, topic_name: str) -> Optional[str]:
        """Get ARN of existing topic"""
        try:
            response = self.client.list_topics()
            for topic in response.get('Topics', []):
                arn = topic['TopicArn']
                if topic_name in arn:
                    return arn
            print(f"✗ Topic not found: {topic_name}")
            return None
        except ClientError as e:
            print(f"✗ Error getting topic ARN: {e}")
            return None

    def list_topics(self) -> List[str]:
        """List all topics"""
        try:
            all_topics = []
            response = self.client.list_topics()

            for topic in response.get('Topics', []):
                all_topics.append(topic['TopicArn'])

            print(f"Found {len(all_topics)} topic(s)")
            return all_topics

        except ClientError as e:
            print(f"✗ Error listing topics: {e}")
            return []

    def delete_topic(self, topic_arn: str) -> bool:
        """Delete topic"""
        try:
            self.client.delete_topic(TopicArn=topic_arn)
            print(f"✓ Deleted topic")
            return True
        except ClientError as e:
            print(f"✗ Error deleting topic: {e}")
            return False

    # ==================== SUBSCRIPTIONS ====================

    def subscribe_sqs(self, topic_arn: str, queue_arn: str) -> Optional[str]:
        """Subscribe SQS queue to topic"""
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )
            sub_arn = response['SubscriptionArn']
            print(f"✓ SQS queue subscribed to topic")

            # Set queue policy to allow SNS to send messages
            self._set_sqs_queue_policy(queue_arn, topic_arn)

            return sub_arn

        except ClientError as e:
            print(f"✗ Error subscribing SQS queue: {e}")
            return None

    def subscribe_email(self, topic_arn: str, email: str) -> Optional[str]:
        """Subscribe email to topic (requires confirmation)"""
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            print(f"✓ Email subscribed. Check {email} for confirmation link")
            return response['SubscriptionArn']

        except ClientError as e:
            print(f"✗ Error subscribing email: {e}")
            return None

    def subscribe_lambda(self, topic_arn: str, lambda_arn: str) -> Optional[str]:
        """Subscribe Lambda function to topic"""
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn,
                Protocol='lambda',
                Endpoint=lambda_arn
            )
            print(f"✓ Lambda subscribed to topic")
            return response['SubscriptionArn']

        except ClientError as e:
            print(f"✗ Error subscribing Lambda: {e}")
            return None

    def subscribe_https(self, topic_arn: str, https_endpoint: str) -> Optional[str]:
        """Subscribe HTTPS endpoint to topic"""
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn,
                Protocol='https',
                Endpoint=https_endpoint
            )
            print(f"✓ HTTPS endpoint subscribed to topic")
            return response['SubscriptionArn']

        except ClientError as e:
            print(f"✗ Error subscribing HTTPS: {e}")
            return None

    def subscribe_sms(self, topic_arn: str, phone_number: str) -> Optional[str]:
        """Subscribe phone number to topic (SMS)"""
        try:
            response = self.client.subscribe(
                TopicArn=topic_arn,
                Protocol='sms',
                Endpoint=phone_number
            )
            print(f"✓ SMS subscribed to topic")
            return response['SubscriptionArn']

        except ClientError as e:
            print(f"✗ Error subscribing SMS: {e}")
            return None

    def unsubscribe(self, subscription_arn: str) -> bool:
        """Unsubscribe from topic"""
        try:
            self.client.unsubscribe(SubscriptionArn=subscription_arn)
            print(f"✓ Unsubscribed")
            return True
        except ClientError as e:
            print(f"✗ Error unsubscribing: {e}")
            return False

    def list_subscriptions(self, topic_arn: str) -> List[Dict]:
        """List subscriptions for a topic"""
        try:
            response = self.client.list_subscriptions_by_topic(TopicArn=topic_arn)
            subs = response.get('Subscriptions', [])
            print(f"Found {len(subs)} subscription(s)")

            for sub in subs:
                print(f"  - {sub['Protocol']}: {sub['Endpoint']} ({sub['SubscriptionArn'].split(':')[-1]})")

            return subs

        except ClientError as e:
            print(f"✗ Error listing subscriptions: {e}")
            return []

    # ==================== MESSAGE FILTERING ====================

    def set_filter_policy(self, subscription_arn: str, filter_policy: Dict) -> bool:
        """Set filter policy for subscription"""
        try:
            self.client.set_subscription_attributes(
                SubscriptionArn=subscription_arn,
                AttributeName='FilterPolicy',
                AttributeValue=json.dumps(filter_policy)
            )
            print(f"✓ Filter policy set")
            return True

        except ClientError as e:
            print(f"✗ Error setting filter policy: {e}")
            return False

    def remove_filter_policy(self, subscription_arn: str) -> bool:
        """Remove filter policy (allow all messages)"""
        return self.set_filter_policy(subscription_arn, {})

    # ==================== PUBLISHING ====================

    def publish_message(self, topic_arn: str, message: str,
                       subject: str = '',
                       message_attributes: Optional[Dict] = None,
                       message_group_id: Optional[str] = None,
                       message_dedup_id: Optional[str] = None) -> Optional[str]:
        """Publish message to topic"""
        try:
            kwargs = {
                'TopicArn': topic_arn,
                'Message': message,
            }

            if subject:
                kwargs['Subject'] = subject

            if message_attributes:
                kwargs['MessageAttributes'] = message_attributes

            if message_group_id:
                kwargs['MessageGroupId'] = message_group_id

            if message_dedup_id:
                kwargs['MessageDeduplicationId'] = message_dedup_id

            response = self.client.publish(**kwargs)
            message_id = response['MessageId']
            print(f"✓ Message published (ID: {message_id[:8]}...)")
            return message_id

        except ClientError as e:
            print(f"✗ Error publishing message: {e}")
            return None

    def publish_json(self, topic_arn: str, data: Dict, subject: str = '') -> Optional[str]:
        """Publish JSON message"""
        return self.publish_message(
            topic_arn=topic_arn,
            message=json.dumps(data),
            subject=subject
        )

    def publish_with_attributes(self, topic_arn: str, message: str,
                               attributes: Dict[str, str],
                               subject: str = '') -> Optional[str]:
        """Publish message with attributes"""
        message_attrs = {
            k: {
                'DataType': 'String',
                'StringValue': v
            }
            for k, v in attributes.items()
        }

        return self.publish_message(
            topic_arn=topic_arn,
            message=message,
            subject=subject,
            message_attributes=message_attrs
        )

    def publish_for_filtering(self, topic_arn: str, message: str,
                             priority: str, event_type: str,
                             amount: Optional[float] = None) -> Optional[str]:
        """Publish message with attributes for filtering"""
        attrs = {
            'priority': {
                'DataType': 'String',
                'StringValue': priority
            },
            'type': {
                'DataType': 'String',
                'StringValue': event_type
            }
        }

        if amount is not None:
            attrs['amount'] = {
                'DataType': 'Number',
                'StringValue': str(amount)
            }

        return self.publish_message(
            topic_arn=topic_arn,
            message=message,
            message_attributes=attrs
        )

    def publish_batch(self, topic_arn: str, messages: List[Dict]) -> Dict[str, Any]:
        """Publish multiple messages (up to 10) in batch"""
        try:
            entries = []
            for i, msg in enumerate(messages[:10]):
                entry = {
                    'Id': str(i),
                    'Message': msg.get('message', ''),
                }

                if 'subject' in msg:
                    entry['Subject'] = msg['subject']

                if 'group_id' in msg:
                    entry['MessageGroupId'] = msg['group_id']

                if 'dedup_id' in msg:
                    entry['MessageDeduplicationId'] = msg['dedup_id']

                entries.append(entry)

            response = self.client.publish_batch(
                TopicArn=topic_arn,
                PublishBatchRequestEntries=entries
            )

            successful = len(response.get('Successful', []))
            failed = len(response.get('Failed', []))
            print(f"✓ Batch - Success: {successful}, Failed: {failed}")

            return response

        except ClientError as e:
            print(f"✗ Error publishing batch: {e}")
            return {'Successful': [], 'Failed': messages}

    # ==================== FAN-OUT PATTERN ====================

    def create_fanout_setup(self, topic_name: str, queue_names: List[str]) -> Dict[str, str]:
        """Create SNS topic and fan-out to multiple SQS queues"""
        try:
            # Create topic
            topic_arn = self.create_topic(topic_name)

            # Create queues
            queue_arns = {}
            for queue_name in queue_names:
                queue_url = self.sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
                queue_attrs = self.sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['QueueArn']
                )
                queue_arn = queue_attrs['Attributes']['QueueArn']
                queue_arns[queue_name] = {
                    'url': queue_url,
                    'arn': queue_arn
                }

                # Subscribe queue to topic
                self.subscribe_sqs(topic_arn, queue_arn)

            print(f"✓ Fan-out setup complete: 1 topic → {len(queue_names)} queues")

            return {
                'topic_arn': topic_arn,
                'queues': queue_arns
            }

        except Exception as e:
            print(f"✗ Error creating fan-out: {e}")
            raise

    def publish_to_fanout(self, topic_arn: str, message: str) -> Optional[str]:
        """Publish message to all fan-out queues"""
        return self.publish_message(topic_arn, message)

    # ==================== FIFO TOPICS ====================

    def publish_fifo(self, topic_arn: str, message: str,
                     message_group_id: str,
                     message_dedup_id: Optional[str] = None) -> Optional[str]:
        """Publish to FIFO topic"""
        return self.publish_message(
            topic_arn=topic_arn,
            message=message,
            message_group_id=message_group_id,
            message_dedup_id=message_dedup_id
        )

    # ==================== TOPIC ATTRIBUTES ====================

    def get_topic_attributes(self, topic_arn: str) -> Dict[str, Any]:
        """Get topic attributes"""
        try:
            response = self.client.get_topic_attributes(TopicArn=topic_arn)
            attrs = response['Attributes']
            print("\n📊 Topic Attributes:")
            print(f"  URN: {attrs.get('TopicArn')}")
            print(f"  Display Name: {attrs.get('DisplayName', 'N/A')}")
            print(f"  Owner: {attrs.get('Owner')}")
            return attrs

        except ClientError as e:
            print(f"✗ Error getting topic attributes: {e}")
            return {}

    def set_topic_attribute(self, topic_arn: str, attribute_name: str,
                            attribute_value: str) -> bool:
        """Set topic attribute"""
        try:
            self.client.set_topic_attributes(
                TopicArn=topic_arn,
                AttributeName=attribute_name,
                AttributeValue=attribute_value
            )
            print(f"✓ Topic attribute set: {attribute_name}")
            return True

        except ClientError as e:
            print(f"✗ Error setting topic attribute: {e}")
            return False

    def enable_encryption(self, topic_arn: str, kms_key_id: str = 'alias/aws/sns') -> bool:
        """Enable encryption for topic"""
        return self.set_topic_attribute(topic_arn, 'KmsMasterKeyId', kms_key_id)

    def set_display_name(self, topic_arn: str, display_name: str) -> bool:
        """Set display name for topic"""
        return self.set_topic_attribute(topic_arn, 'DisplayName', display_name)

    # ==================== SUBSCRIPTION ATTRIBUTES ====================

    def get_subscription_attributes(self, subscription_arn: str) -> Dict[str, Any]:
        """Get subscription attributes"""
        try:
            response = self.client.get_subscription_attributes(
                SubscriptionArn=subscription_arn
            )
            attrs = response['Attributes']
            print(f"  Protocol: {attrs.get('Protocol')}")
            print(f"  Endpoint: {attrs.get('Endpoint')}")
            print(f"  Status: {attrs.get('SubscriptionArn').split(':')[-1] != 'PendingConfirmation'}")
            return attrs

        except ClientError as e:
            print(f"✗ Error getting subscription attributes: {e}")
            return {}

    # ==================== HELPER METHODS ====================

    def _set_sqs_queue_policy(self, queue_arn: str, topic_arn: str):
        """Set SQS queue policy to allow SNS to send messages"""
        policy = {
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

        try:
            # Get queue URL from ARN
            queue_url = self._get_queue_url_from_arn(queue_arn)
            if queue_url:
                self.sqs_client.set_queue_attributes(
                    QueueUrl=queue_url,
                    Attributes={'Policy': json.dumps(policy)}
                )
        except Exception as e:
            print(f"Warning: Could not set queue policy: {e}")

    def _get_queue_url_from_arn(self, queue_arn: str) -> Optional[str]:
        """Get queue URL from ARN"""
        parts = queue_arn.split(':')
        if len(parts) >= 6:
            queue_name = parts[5]
            response = self.sqs_client.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        return None

    # ==================== MONITORING ====================

    def print_topic_info(self, topic_arn: str):
        """Print comprehensive topic information"""
        print(f"\n📌 Topic Information: {topic_arn}")
        self.get_topic_attributes(topic_arn)
        print()
        self.list_subscriptions(topic_arn)


# ==================== USAGE EXAMPLES ====================

def example_basic_publish():
    """Basic publish to topic"""
    print("\n=== BASIC PUBLISH ===")
    sns = SNSClient()

    # Create topic
    topic_arn = sns.create_topic('OrderNotifications')

    # Publish message
    sns.publish_message(
        topic_arn,
        'Your order #123 has been shipped!',
        subject='Order Shipped'
    )


def example_subscribe_queue():
    """Subscribe SQS queue to SNS topic"""
    print("\n=== SUBSCRIBE QUEUE ===")
    sns = SNSClient()
    sqs = boto3.client('sqs')

    # Create topic
    topic_arn = sns.create_topic('OrderEvents')

    # Create queue
    queue_url = sqs.create_queue(QueueName='OrderProcessingQueue')['QueueUrl']
    queue_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])
    queue_arn = queue_attrs['Attributes']['QueueArn']

    # Subscribe queue
    sns.subscribe_sqs(topic_arn, queue_arn)

    # Publish message
    sns.publish_message(topic_arn, 'Order created', subject='New Order')


def example_filter_policy():
    """Use filter policy for selective delivery"""
    print("\n=== FILTER POLICY ===")
    sns = SNSClient()

    topic_arn = sns.create_topic('Orders')

    # Get a subscription (would normally have one already)
    subs = sns.list_subscriptions(topic_arn)
    if subs:
        sub_arn = subs[0]['SubscriptionArn']

        # Only receive High priority orders > $100
        filter_policy = {
            'priority': ['High'],
            'amount': [{'numeric': ['>', 100]}]
        }
        sns.set_filter_policy(sub_arn, filter_policy)

        # Publish filtered message
        sns.publish_for_filtering(
            topic_arn,
            'High-value order received',
            priority='High',
            event_type='OrderCreated',
            amount=150
        )


def example_fanout():
    """Fan-out pattern: one topic to multiple queues"""
    print("\n=== FAN-OUT PATTERN ===")
    sns = SNSClient()

    # Create topic and 3 queues
    setup = sns.create_fanout_setup(
        'OrderEvents',
        [
            'InventoryQueue',
            'NotificationQueue',
            'AnalyticsQueue'
        ]
    )

    # Publish message to all queues
    sns.publish_to_fanout(
        setup['topic_arn'],
        json.dumps({
            'order_id': 123,
            'customer': 'John Doe',
            'amount': 99.99
        })
    )

    print("\n✓ Message published to all 3 queues via fan-out")


def example_fifo_topic():
    """Publish to FIFO topic with ordering guarantee"""
    print("\n=== FIFO TOPIC ===")
    sns = SNSClient()

    topic_arn = sns.create_topic('OrderProcessing.fifo', fifo=True, content_dedup=True)

    # Publish ordered messages
    for i in range(3):
        sns.publish_fifo(
            topic_arn,
            f'Order step {i+1}',
            message_group_id='order-123'
        )

    print("✓ Messages published in order")


def example_batch_publish():
    """Publish multiple messages in batch"""
    print("\n=== BATCH PUBLISH ===")
    sns = SNSClient()

    topic_arn = sns.create_topic('Events')

    messages = [
        {'message': 'Event 1', 'subject': 'Subject 1'},
        {'message': 'Event 2', 'subject': 'Subject 2'},
        {'message': 'Event 3', 'subject': 'Subject 3'},
    ]

    sns.publish_batch(topic_arn, messages)


if __name__ == '__main__':
    # Uncomment to run examples
    # example_basic_publish()
    # example_subscribe_queue()
    # example_filter_policy()
    # example_fanout()
    # example_fifo_topic()
    # example_batch_publish()

    print("\n✓ SNS operations module ready")
    print("Import SNSClient and use methods for SNS operations")
    print("\nExample:")
    print("  from sns_operations import SNSClient")
    print("  sns = SNSClient()")
    print("  topic_arn = sns.create_topic('MyTopic')")
    print("  sns.publish_message(topic_arn, 'Hello SNS')")

