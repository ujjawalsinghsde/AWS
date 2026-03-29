"""
AWS SQS (Simple Queue Service) - Comprehensive Operations and Examples
Covers: Sending, Receiving, Processing, DLQ, Batching, Monitoring
"""

import json
import time
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError


class SQSClient:
    """Wrapper for AWS SQS operations with common patterns"""

    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize SQS client"""
        self.client = boto3.client('sqs', region_name=region_name)
        self.resource = boto3.resource('sqs', region_name=region_name)

    # ==================== QUEUE MANAGEMENT ====================

    def create_standard_queue(self, queue_name: str,
                             visibility_timeout: int = 300,
                             message_retention: int = 345600) -> str:
        """Create standard queue with custom timeout and retention"""
        try:
            response = self.client.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeout': str(visibility_timeout),
                    'MessageRetentionPeriod': str(message_retention),
                    'ReceiveMessageWaitTimeSeconds': '20',  # Long polling
                }
            )
            print(f"✓ Created standard queue: {queue_name}")
            return response['QueueUrl']
        except ClientError as e:
            print(f"✗ Error creating queue: {e}")
            raise

    def create_fifo_queue(self, queue_name: str,
                          content_dedup: bool = True) -> str:
        """Create FIFO queue with deduplication"""
        queue_name_fifo = queue_name if queue_name.endswith('.fifo') else f"{queue_name}.fifo"

        try:
            response = self.client.create_queue(
                QueueName=queue_name_fifo,
                Attributes={
                    'FifoQueue': 'true',
                    'ContentBasedDeduplication': 'true' if content_dedup else 'false',
                    'VisibilityTimeout': '300',
                    'ReceiveMessageWaitTimeSeconds': '20',
                }
            )
            print(f"✓ Created FIFO queue: {queue_name_fifo}")
            return response['QueueUrl']
        except ClientError as e:
            print(f"✗ Error creating FIFO queue: {e}")
            raise

    def get_queue_url(self, queue_name: str) -> str:
        """Get URL of existing queue"""
        try:
            response = self.client.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except ClientError as e:
            print(f"✗ Queue not found: {queue_name}")
            raise

    def delete_queue(self, queue_url: str) -> bool:
        """Delete queue"""
        try:
            self.client.delete_queue(QueueUrl=queue_url)
            print(f"✓ Deleted queue")
            return True
        except ClientError as e:
            print(f"✗ Error deleting queue: {e}")
            return False

    def purge_queue(self, queue_url: str) -> bool:
        """Delete all messages from queue"""
        try:
            self.client.purge_queue(QueueUrl=queue_url)
            print(f"✓ Purged queue (messages deleted)")
            return True
        except ClientError as e:
            print(f"✗ Error purging queue: {e}")
            return False

    def list_queues(self) -> List[str]:
        """List all queues"""
        try:
            response = self.client.list_queues()
            queues = response.get('QueueUrls', [])
            print(f"Found {len(queues)} queue(s)")
            return queues
        except ClientError as e:
            print(f"✗ Error listing queues: {e}")
            return []

    # ==================== QUEUE ATTRIBUTES ====================

    def get_queue_attributes(self, queue_url: str) -> Dict[str, Any]:
        """Get all queue attributes"""
        try:
            response = self.client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )
            attrs = response['Attributes']
            print("\n📊 Queue Attributes:")
            print(f"  Visibility Timeout: {attrs.get('VisibilityTimeout')}s")
            print(f"  Message Retention: {attrs.get('MessageRetentionPeriod')}s")
            print(f"  Approximate Visible: {attrs.get('ApproximateNumberOfMessagesVisible')}")
            print(f"  Approximate Not Visible: {attrs.get('ApproximateNumberOfMessagesNotVisible')}")
            print(f"  Approximate Delayed: {attrs.get('ApproximateNumberOfMessagesDelayed')}")
            print(f"  Created: {attrs.get('CreatedTimestamp')}")
            return attrs
        except ClientError as e:
            print(f"✗ Error getting queue attributes: {e}")
            return {}

    def set_queue_attributes(self, queue_url: str, **kwargs) -> bool:
        """Set queue attributes"""
        attributes = {
            'VisibilityTimeout': kwargs.get('visibility_timeout'),
            'MessageRetentionPeriod': kwargs.get('message_retention'),
            'ReceiveMessageWaitTimeSeconds': kwargs.get('wait_time'),
            'MaximumMessageSize': kwargs.get('max_message_size'),
            'DelaySeconds': kwargs.get('delay_seconds'),
        }
        # Remove None values
        attributes = {k: str(v) for k, v in attributes.items() if v is not None}

        try:
            self.client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes=attributes
            )
            print(f"✓ Updated queue attributes")
            return True
        except ClientError as e:
            print(f"✗ Error setting queue attributes: {e}")
            return False

    # ==================== SENDING MESSAGES ====================

    def send_message(self, queue_url: str, message_body: str,
                     delay_seconds: int = 0,
                     message_attributes: Optional[Dict] = None,
                     message_dedup_id: Optional[str] = None,
                     message_group_id: Optional[str] = None) -> Optional[str]:
        """Send single message to queue"""
        try:
            kwargs = {
                'QueueUrl': queue_url,
                'MessageBody': message_body,
            }

            if delay_seconds > 0:
                kwargs['DelaySeconds'] = delay_seconds

            if message_attributes:
                kwargs['MessageAttributes'] = message_attributes

            if message_dedup_id:
                kwargs['MessageDeduplicationId'] = message_dedup_id

            if message_group_id:
                kwargs['MessageGroupId'] = message_group_id

            response = self.client.send_message(**kwargs)
            message_id = response['MessageId']
            print(f"✓ Message sent (ID: {message_id[:8]}...)")
            return message_id

        except ClientError as e:
            print(f"✗ Error sending message: {e}")
            return None

    def send_message_with_attributes(self, queue_url: str, message_body: str,
                                     attributes: Dict[str, str]) -> Optional[str]:
        """Send message with custom attributes"""
        message_attrs = {
            k: {
                'StringValue': v,
                'DataType': 'String'
            }
            for k, v in attributes.items()
        }

        return self.send_message(
            queue_url=queue_url,
            message_body=message_body,
            message_attributes=message_attrs
        )

    def send_json_message(self, queue_url: str, data: Dict) -> Optional[str]:
        """Send JSON message"""
        return self.send_message(
            queue_url=queue_url,
            message_body=json.dumps(data)
        )

    def send_message_batch(self, queue_url: str, messages: List[Dict]) -> Dict[str, Any]:
        """Send multiple messages (up to 10) in single batch"""
        try:
            entries = []
            for i, msg in enumerate(messages[:10]):
                entry = {
                    'Id': str(i),
                    'MessageBody': msg.get('body', ''),
                }

                if 'delay' in msg:
                    entry['DelaySeconds'] = msg['delay']

                if 'attributes' in msg:
                    entry['MessageAttributes'] = {
                        k: {'StringValue': str(v), 'DataType': 'String'}
                        for k, v in msg['attributes'].items()
                    }

                if 'dedup_id' in msg:
                    entry['MessageDeduplicationId'] = msg['dedup_id']

                if 'group_id' in msg:
                    entry['MessageGroupId'] = msg['group_id']

                entries.append(entry)

            response = self.client.send_message_batch(
                QueueUrl=queue_url,
                Entries=entries
            )

            successful = len(response.get('Successful', []))
            failed = len(response.get('Failed', []))
            print(f"✓ Batch sent - Success: {successful}, Failed: {failed}")

            return response

        except ClientError as e:
            print(f"✗ Error sending batch: {e}")
            return {'Successful': [], 'Failed': messages}

    def send_message_batch_simple(self, queue_url: str, messages: List[str]) -> int:
        """Send batch of simple text messages"""
        entries = [
            {'Id': str(i), 'MessageBody': msg}
            for i, msg in enumerate(messages[:10])
        ]

        response = self.client.send_message_batch(
            QueueUrl=queue_url,
            Entries=entries
        )

        return len(response.get('Successful', []))

    # ==================== RECEIVING MESSAGES ====================

    def receive_message(self, queue_url: str, max_messages: int = 1,
                       wait_time: int = 20) -> List[Dict]:
        """Receive messages from queue (with long polling)"""
        try:
            response = self.client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                MessageAttributeNames=['All']
            )

            messages = response.get('Messages', [])
            print(f"✓ Received {len(messages)} message(s)")
            return messages

        except ClientError as e:
            print(f"✗ Error receiving messages: {e}")
            return []

    def receive_message_batch(self, queue_url: str, count: int = 10) -> List[Dict]:
        """Receive multiple messages (convenience wrapper)"""
        return self.receive_message(queue_url, max_messages=count, wait_time=20)

    def receive_and_process(self, queue_url: str, callback, max_messages: int = 10) -> int:
        """Receive messages and process with callback function"""
        messages = self.receive_message(queue_url, max_messages=max_messages)

        processed = 0
        for message in messages:
            try:
                callback(message)
                self.delete_message(queue_url, message['ReceiptHandle'])
                processed += 1
            except Exception as e:
                print(f"✗ Error processing message: {e}")
                # Don't delete - let visibility timeout handle retry

        return processed

    # ==================== MESSAGE DELETION ====================

    def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """Delete message from queue"""
        try:
            self.client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            print(f"✓ Message deleted")
            return True
        except ClientError as e:
            print(f"✗ Error deleting message: {e}")
            return False

    def delete_message_batch(self, queue_url: str, receipt_handles: List[str]) -> Dict:
        """Delete multiple messages (up to 10) in single batch"""
        try:
            entries = [
                {'Id': str(i), 'ReceiptHandle': handle}
                for i, handle in enumerate(receipt_handles[:10])
            ]

            response = self.client.delete_message_batch(
                QueueUrl=queue_url,
                Entries=entries
            )

            successful = len(response.get('Successful', []))
            failed = len(response.get('Failed', []))
            print(f"✓ Batch delete - Success: {successful}, Failed: {failed}")

            return response

        except ClientError as e:
            print(f"✗ Error deleting batch: {e}")
            return {'Successful': [], 'Failed': []}

    # ==================== VISIBILITY TIMEOUT ====================

    def change_message_visibility(self, queue_url: str, receipt_handle: str,
                                 visibility_timeout: int) -> bool:
        """Extend or reduce message visibility timeout"""
        try:
            self.client.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeoutInSeconds=visibility_timeout
            )
            print(f"✓ Visibility timeout changed to {visibility_timeout}s")
            return True

        except ClientError as e:
            print(f"✗ Error changing visibility: {e}")
            return False

    def extend_visibility(self, queue_url: str, receipt_handle: str,
                         additional_seconds: int = 300) -> bool:
        """Extend visibility timeout (for long-running tasks)"""
        return self.change_message_visibility(
            queue_url, receipt_handle,
            additional_seconds
        )

    def change_visibility_batch(self, queue_url: str,
                               visibility_changes: List[Dict]) -> Dict:
        """Change visibility for multiple messages"""
        try:
            entries = [
                {
                    'Id': str(i),
                    'ReceiptHandle': change['receipt_handle'],
                    'VisibilityTimeoutInSeconds': change['timeout']
                }
                for i, change in enumerate(visibility_changes[:10])
            ]

            response = self.client.change_message_visibility_batch(
                QueueUrl=queue_url,
                Entries=entries
            )

            return response

        except ClientError as e:
            print(f"✗ Error changing visibility batch: {e}")
            return {'Successful': [], 'Failed': []}

    # ==================== DEAD LETTER QUEUE ====================

    def create_dlq(self, dlq_name: str) -> str:
        """Create Dead Letter Queue"""
        return self.create_standard_queue(dlq_name)

    def attach_dlq(self, queue_url: str, dlq_url: str, max_receive_count: int = 3) -> bool:
        """Attach DLQ to main queue (redrive policy)"""
        try:
            # Get DLQ ARN
            dlq_attrs = self.client.get_queue_attributes(
                QueueUrl=dlq_url,
                AttributeNames=['QueueArn']
            )
            dlq_arn = dlq_attrs['Attributes']['QueueArn']

            # Set redrive policy
            redrive_policy = {
                'deadLetterTargetArn': dlq_arn,
                'maxReceiveCount': max_receive_count
            }

            self.client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'RedrivePolicy': json.dumps(redrive_policy)
                }
            )

            print(f"✓ DLQ attached (maxReceiveCount={max_receive_count})")
            return True

        except ClientError as e:
            print(f"✗ Error attaching DLQ: {e}")
            return False

    def get_dlq_messages(self, dlq_url: str) -> List[Dict]:
        """Get messages from DLQ"""
        messages = self.receive_message_batch(dlq_url, count=10)
        print(f"📬 DLQ has {len(messages)} message(s)")
        return messages

    def process_dlq(self, dlq_url: str, callback) -> int:
        """Process DLQ messages and log failures"""
        messages = self.receive_message_batch(dlq_url, count=10)
        processed = 0

        for message in messages:
            try:
                # Log the failure
                receive_count = message.get('Attributes', {}).get('ApproximateReceiveCount', 'unknown')
                print(f"Failed message (attempts: {receive_count}): {message['Body'][:100]}")

                # Process with callback
                callback(message)

                # Delete from DLQ
                self.delete_message(dlq_url, message['ReceiptHandle'])
                processed += 1
            except Exception as e:
                print(f"✗ Error processing DLQ message: {e}")

        return processed

    # ==================== MONITORING & STATS ====================

    def get_queue_stats(self, queue_url: str) -> Dict[str, Any]:
        """Get queue statistics"""
        attrs = self.get_queue_attributes(queue_url)
        return {
            'visible_messages': int(attrs.get('ApproximateNumberOfMessagesVisible', 0)),
            'not_visible_messages': int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
            'delayed_messages': int(attrs.get('ApproximateNumberOfMessagesDelayed', 0)),
            'total_messages': int(attrs.get('ApproximateNumberOfMessagesVisible', 0)) +
                            int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
            'created_timestamp': attrs.get('CreatedTimestamp'),
            'last_modified': attrs.get('LastModifiedTimestamp'),
        }

    def print_queue_stats(self, queue_url: str):
        """Print formatted queue statistics"""
        stats = self.get_queue_stats(queue_url)
        print("\n📈 Queue Statistics:")
        print(f"  Visible Messages: {stats['visible_messages']}")
        print(f"  Being Processed: {stats['not_visible_messages']}")
        print(f"  Delayed Messages: {stats['delayed_messages']}")
        print(f"  Total Messages: {stats['total_messages']}")

    def monitor_queue(self, queue_url: str, interval_seconds: int = 5, duration_seconds: int = 60):
        """Monitor queue for specified duration"""
        end_time = time.time() + duration_seconds
        print(f"\n⏱️  Monitoring for {duration_seconds} seconds (interval: {interval_seconds}s)")

        while time.time() < end_time:
            stats = self.get_queue_stats(queue_url)
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"{timestamp} - Visible: {stats['visible_messages']}, Processing: {stats['not_visible_messages']}")
            time.sleep(interval_seconds)

    # ==================== ENCRYPTION & SECURITY ====================

    def enable_encryption(self, queue_url: str, kms_key_id: str = 'alias/aws/sqs') -> bool:
        """Enable server-side encryption"""
        try:
            self.client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'KmsMasterKeyId': kms_key_id,
                    'KmsDataKeyReusePeriodSeconds': '3600'
                }
            )
            print(f"✓ Encryption enabled")
            return True
        except ClientError as e:
            print(f"✗ Error enabling encryption: {e}")
            return False

    def set_queue_policy(self, queue_url: str, policy: Dict) -> bool:
        """Set queue access policy"""
        try:
            self.client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'Policy': json.dumps(policy)
                }
            )
            print(f"✓ Queue policy updated")
            return True
        except ClientError as e:
            print(f"✗ Error setting queue policy: {e}")
            return False


# ==================== USAGE EXAMPLES ====================

def example_basic_send_receive():
    """Basic send and receive example"""
    print("\n=== BASIC SEND & RECEIVE ===")
    sqs = SQSClient(region_name='us-east-1')

    # Create queue
    queue_url = sqs.create_standard_queue('demo-queue')

    # Send message
    sqs.send_message(queue_url, 'Hello from SQS!')

    # Receive message
    messages = sqs.receive_message(queue_url, max_messages=1)

    if messages:
        msg = messages[0]
        print(f"Body: {msg['Body']}")
        sqs.delete_message(queue_url, msg['ReceiptHandle'])


def example_json_messages():
    """Sending and receiving JSON messages"""
    print("\n=== JSON MESSAGES ===")
    sqs = SQSClient()

    queue_url = sqs.create_standard_queue('json-queue')

    # Send JSON
    data = {
        'order_id': 123,
        'customer': 'John Doe',
        'amount': 99.99,
        'items': ['item1', 'item2']
    }
    sqs.send_json_message(queue_url, data)

    # Receive and parse JSON
    messages = sqs.receive_message(queue_url)
    if messages:
        body = json.loads(messages[0]['Body'])
        print(f"Order: {body['order_id']} - {body['customer']} - ${body['amount']}")


def example_batch_operations():
    """Batch send and delete"""
    print("\n=== BATCH OPERATIONS ===")
    sqs = SQSClient()

    queue_url = sqs.create_standard_queue('batch-queue')

    # Send batch
    messages = [
        {'body': 'Message 1'},
        {'body': 'Message 2'},
        {'body': 'Message 3'},
    ]
    sqs.send_message_batch(queue_url, messages)

    # Receive and delete batch
    received = sqs.receive_message_batch(queue_url, count=10)
    handles = [m['ReceiptHandle'] for m in received]
    sqs.delete_message_batch(queue_url, handles)


def example_fifo_queue():
    """FIFO queue with ordering and deduplication"""
    print("\n=== FIFO QUEUE ===")
    sqs = SQSClient()

    queue_url = sqs.create_fifo_queue('order-processing.fifo')

    # Send FIFO messages
    for i in range(3):
        sqs.send_message(
            queue_url,
            f'Order {i}',
            message_group_id='order-group-1',
            message_dedup_id=f'order-{i}'
        )

    # Messages processed in order
    messages = sqs.receive_message_batch(queue_url, count=10)
    print(f"Received {len(messages)} message(s) in order")


def example_dlq():
    """Dead Letter Queue setup"""
    print("\n=== DEAD LETTER QUEUE ===")
    sqs = SQSClient()

    # Create main and DLQ
    main_queue = sqs.create_standard_queue('main-queue')
    dlq = sqs.create_dlq('main-queue-dlq')

    # Attach DLQ
    sqs.attach_dlq(main_queue, dlq, max_receive_count=3)

    # Send message and simulate failures
    sqs.send_message(main_queue, 'Will fail 3 times')

    # After 3 receive attempts without deletion, message goes to DLQ
    for attempt in range(3):
        msgs = sqs.receive_message(main_queue)
        if msgs:
            print(f"Attempt {attempt + 1}: received, not deleting")

    # Check DLQ
    dlq_msgs = sqs.get_dlq_messages(dlq)
    print(f"DLQ has {len(dlq_msgs)} message(s)")


def example_message_attributes():
    """Sending and receiving custom attributes"""
    print("\n=== MESSAGE ATTRIBUTES ===")
    sqs = SQSClient()

    queue_url = sqs.create_standard_queue('attributes-queue')

    # Send with attributes
    sqs.send_message_with_attributes(
        queue_url,
        'Order update',
        {
            'OrderId': '12345',
            'Priority': 'High',
            'Type': 'OrderStatus'
        }
    )

    # Receive with attributes
    messages = sqs.receive_message(queue_url)
    if messages:
        msg = messages[0]
        attrs = msg.get('MessageAttributes', {})
        print(f"Body: {msg['Body']}")
        print(f"Order ID: {attrs.get('OrderId', {}).get('StringValue')}")
        print(f"Priority: {attrs.get('Priority', {}).get('StringValue')}")


def example_visibility_timeout():
    """Managing visibility timeout"""
    print("\n=== VISIBILITY TIMEOUT ===")
    sqs = SQSClient()

    queue_url = sqs.create_standard_queue('timeout-queue')

    # Send message
    sqs.send_message(queue_url, 'Long running task')

    # Receive message
    messages = sqs.receive_message(queue_url)
    if messages:
        msg = messages[0]
        receipt = msg['ReceiptHandle']

        # Task running, extend visibility
        print("Processing message... extending visibility")
        sqs.extend_visibility(queue_url, receipt, additional_seconds=600)

        # Later, if task completes
        sqs.delete_message(queue_url, receipt)


def example_monitoring():
    """Monitoring queue depth"""
    print("\n=== MONITORING ===")
    sqs = SQSClient()

    queue_url = sqs.create_standard_queue('monitor-queue')

    # Send some messages
    for i in range(5):
        sqs.send_message(queue_url, f'Message {i}')

    # Check stats
    sqs.print_queue_stats(queue_url)

    # Monitor for 30 seconds
    # sqs.monitor_queue(queue_url, interval_seconds=2, duration_seconds=30)


if __name__ == '__main__':
    # Uncomment to run examples
    # example_basic_send_receive()
    # example_json_messages()
    # example_batch_operations()
    # example_fifo_queue()
    # example_dlq()
    # example_message_attributes()
    # example_visibility_timeout()
    # example_monitoring()

    print("\n✓ SQS operations module ready")
    print("Import SQSClient and use methods for SQS operations")
    print("\nExample:")
    print("  from sqs_operations import SQSClient")
    print("  sqs = SQSClient()")
    print("  queue_url = sqs.create_standard_queue('my-queue')")
    print("  sqs.send_message(queue_url, 'Hello SQS')")

