"""
AWS DynamoDB - Boto3 Operations
Document: DynamoDB/dynamodb_operations.py

This module provides practical boto3 examples for common DynamoDB operations.
"""

import boto3
import json
import time
from datetime import datetime, timedelta

# Initialize DynamoDB client and resource
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')


# ============================================================================
# 1. TABLE OPERATIONS
# ============================================================================

def create_table_on_demand(table_name):
    """Create a simple table with on-demand billing"""
    try:
        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Environment', 'Value': 'development'}
            ]
        )

        print(f"✓ Table created: {table_name}")
        return response
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return None


def create_table_provisioned(table_name, read_units=5, write_units=5):
    """Create a table with provisioned billing"""
    try:
        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': read_units,
                'WriteCapacityUnits': write_units
            }
        )

        print(f"✓ Table created: {table_name}")
        print(f"  Read Capacity: {read_units} RCU")
        print(f"  Write Capacity: {write_units} WCU")
        return response
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return None


def list_tables():
    """List all DynamoDB tables"""
    try:
        response = dynamodb_client.list_tables()
        print(f"\n📊 DynamoDB Tables ({len(response['TableNames'])} total):")
        print("-" * 80)
        for table in response['TableNames']:
            print(f"  - {table}")
        return response
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        return None


def describe_table(table_name):
    """Get detailed information about a table"""
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        table = response['Table']

        print(f"\n📋 Table: {table_name}")
        print("-" * 80)
        print(f"  Status:              {table['TableStatus']}")
        print(f"  Item Count:          {table['ItemCount']}")
        print(f"  Size (bytes):        {table['TableSizeBytes']}")
        print(f"  Billing Mode:        {table['BillingModeSummary'].get('BillingMode', 'N/A')}")
        print(f"  ARN:                 {table['TableArn']}")

        if table['BillingModeSummary'].get('BillingMode') == 'PROVISIONED':
            print(f"  Read Capacity:       {table['ProvisionedThroughput']['ReadCapacityUnits']}")
            print(f"  Write Capacity:      {table['ProvisionedThroughput']['WriteCapacityUnits']}")

        return table
    except Exception as e:
        print(f"✗ Error describing table: {e}")
        return None


def delete_table(table_name):
    """Delete a table"""
    try:
        response = dynamodb_client.delete_table(TableName=table_name)
        print(f"✓ Table deleted: {table_name}")
        return response
    except Exception as e:
        print(f"✗ Error deleting table: {e}")
        return None


# ============================================================================
# 2. PUT, GET, UPDATE, DELETE ITEMS
# ============================================================================

def put_item(table_name, items_dict):
    """Put an item in table"""
    try:
        response = dynamodb_client.put_item(
            TableName=table_name,
            Item=items_dict
        )
        print(f"✓ Item put successfully")
        return response
    except Exception as e:
        print(f"✗ Error putting item: {e}")
        return None


def get_item(table_name, pk_value, sk_value=None):
    """Get an item from table"""
    try:
        key = {'PK': {'S': pk_value}}
        if sk_value:
            key['SK'] = {'S': sk_value}

        response = dynamodb_client.get_item(
            TableName=table_name,
            Key=key
        )

        if 'Item' in response:
            print(f"✓ Item retrieved")
            print(f"  {response['Item']}")
            return response['Item']
        else:
            print(f"✗ Item not found")
            return None
    except Exception as e:
        print(f"✗ Error getting item: {e}")
        return None


def update_item(table_name, pk_value, update_expression, attr_values, sk_value=None):
    """Update an item in table"""
    try:
        key = {'PK': {'S': pk_value}}
        if sk_value:
            key['SK'] = {'S': sk_value}

        response = dynamodb_client.update_item(
            TableName=table_name,
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=attr_values,
            ReturnValues='ALL_NEW'
        )

        print(f"✓ Item updated")
        return response['Attributes']
    except Exception as e:
        print(f"✗ Error updating item: {e}")
        return None


def delete_item(table_name, pk_value, sk_value=None):
    """Delete an item from table"""
    try:
        key = {'PK': {'S': pk_value}}
        if sk_value:
            key['SK'] = {'S': sk_value}

        response = dynamodb_client.delete_item(
            TableName=table_name,
            Key=key
        )

        print(f"✓ Item deleted")
        return response
    except Exception as e:
        print(f"✗ Error deleting item: {e}")
        return None


# ============================================================================
# 3. BATCH OPERATIONS
# ============================================================================

def batch_write_items(table_name, items_list):
    """Batch write multiple items"""
    try:
        request_items = {
            table_name: [
                {'PutRequest': {'Item': item}} for item in items_list
            ]
        }

        response = dynamodb_client.batch_write_item(
            RequestItems=request_items
        )

        processed = len(items_list) - len(response.get('UnprocessedItems', {}).get(table_name, []))
        print(f"✓ Batch write completed: {processed}/{len(items_list)} items")

        if response.get('UnprocessedItems'):
            print(f"⚠️  Unprocessed items: {len(response['UnprocessedItems'][table_name])}")

        return response
    except Exception as e:
        print(f"✗ Error in batch write: {e}")
        return None


def batch_get_items(table_name, keys_list):
    """Batch get multiple items"""
    try:
        request_items = {
            table_name: {
                'Keys': keys_list
            }
        }

        response = dynamodb_client.batch_get_item(
            RequestItems=request_items
        )

        items = response['Responses'][table_name]
        print(f"✓ Batch get completed: {len(items)} items retrieved")

        return items
    except Exception as e:
        print(f"✗ Error in batch get: {e}")
        return None


# ============================================================================
# 4. QUERY OPERATIONS
# ============================================================================

def query_items(table_name, pk_value, sk_value=None, limit=10):
    """Query items by partition key"""
    try:
        expression = 'PK = :pk'
        attr_values = {':pk': {'S': pk_value}}

        if sk_value:
            expression += ' AND SK = :sk'
            attr_values[':sk'] = {'S': sk_value}

        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression=expression,
            ExpressionAttributeValues=attr_values,
            Limit=limit
        )

        print(f"✓ Query completed: {response['Count']} items found")
        for item in response['Items']:
            print(f"  - {item}")

        return response['Items']
    except Exception as e:
        print(f"✗ Error querying items: {e}")
        return None


def query_range(table_name, pk_value, sk_prefix, limit=10):
    """Query items with sort key range"""
    try:
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': {'S': pk_value},
                ':sk': {'S': sk_prefix}
            },
            Limit=limit
        )

        print(f"✓ Range query completed: {response['Count']} items found")
        return response['Items']
    except Exception as e:
        print(f"✗ Error in range query: {e}")
        return None


# ============================================================================
# 5. SCAN OPERATIONS
# ============================================================================

def scan_table(table_name, limit=10):
    """Scan table (use sparingly - expensive!)"""
    try:
        response = dynamodb_client.scan(
            TableName=table_name,
            Limit=limit
        )

        print(f"✓ Scan completed: {response['Count']} items found (of {response.get('ScannedCount')} scanned)")
        for item in response['Items']:
            print(f"  - {item}")

        return response['Items']
    except Exception as e:
        print(f"✗ Error scanning table: {e}")
        return None


def scan_with_filter(table_name, filter_expression, attr_values, limit=10):
    """Scan with filter expression"""
    try:
        response = dynamodb_client.scan(
            TableName=table_name,
            FilterExpression=filter_expression,
            ExpressionAttributeValues=attr_values,
            Limit=limit
        )

        print(f"✓ Filtered scan completed: {response['Count']} items matched")
        return response['Items']
    except Exception as e:
        print(f"✗ Error in filtered scan: {e}")
        return None


# ============================================================================
# 6. GSI OPERATIONS
# ============================================================================

def add_global_secondary_index(table_name, index_name, pk_attr, billing_mode='PAY_PER_REQUEST'):
    """Add a Global Secondary Index to table"""
    try:
        response = dynamodb_client.update_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': pk_attr, 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexUpdates=[
                {
                    'Create': {
                        'IndexName': index_name,
                        'KeySchema': [
                            {'AttributeName': pk_attr, 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': billing_mode
                    }
                }
            ]
        )

        print(f"✓ GSI '{index_name}' created")
        return response
    except Exception as e:
        print(f"✗ Error adding GSI: {e}")
        return None


def query_gsi(table_name, index_name, pk_attr, pk_value, limit=10):
    """Query a Global Secondary Index"""
    try:
        response = dynamodb_client.query(
            TableName=table_name,
            IndexName=index_name,
            KeyConditionExpression=f'{pk_attr} = :pk',
            ExpressionAttributeValues={':pk': {'S': pk_value}},
            Limit=limit
        )

        print(f"✓ GSI query completed: {response['Count']} items found")
        return response['Items']
    except Exception as e:
        print(f"✗ Error querying GSI: {e}")
        return None


# ============================================================================
# 7. TTL OPERATIONS
# ============================================================================

def enable_ttl(table_name, ttl_attr='ExpiresAt'):
    """Enable Time To Live for a table"""
    try:
        response = dynamodb_client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'AttributeName': ttl_attr,
                'Enabled': True
            }
        )

        print(f"✓ TTL enabled for table: {table_name}")
        print(f"  TTL Attribute: {ttl_attr}")
        return response
    except Exception as e:
        print(f"✗ Error enabling TTL: {e}")
        return None


def put_item_with_ttl(table_name, item, ttl_seconds=86400):
    """Put item with automatic expiration"""
    try:
        expiration_time = int(time.time()) + ttl_seconds
        item['ExpiresAt'] = {'N': str(expiration_time)}

        response = dynamodb_client.put_item(
            TableName=table_name,
            Item=item
        )

        expiration_date = datetime.fromtimestamp(expiration_time)
        print(f"✓ Item put with TTL")
        print(f"  Expires: {expiration_date}")
        return response
    except Exception as e:
        print(f"✗ Error putting item with TTL: {e}")
        return None


# ============================================================================
# 8. TRANSACTION OPERATIONS
# ============================================================================

def transact_write(table_name, operations):
    """Perform transactional writes"""
    try:
        response = dynamodb_client.transact_write_items(
            TransactItems=operations
        )

        print(f"✓ Transaction completed successfully")
        return response
    except Exception as e:
        print(f"✗ Error in transaction: {e}")
        return None


def transact_get(table_name, keys_list):
    """Perform transactional reads"""
    try:
        transact_items = [
            {
                'Get': {
                    'TableName': table_name,
                    'Key': key
                }
            }
            for key in keys_list
        ]

        response = dynamodb_client.transact_get_items(
            TransactItems=transact_items
        )

        items = [resp['Item'] for resp in response['Responses']]
        print(f"✓ Transaction get completed: {len(items)} items retrieved")
        return items
    except Exception as e:
        print(f"✗ Error in transaction get: {e}")
        return None


# ============================================================================
# 9. BACKUP OPERATIONS
# ============================================================================

def create_backup(table_name, backup_name):
    """Create a table backup"""
    try:
        response = dynamodb_client.create_backup(
            TableName=table_name,
            BackupName=backup_name
        )

        backup_arn = response['BackupDetails']['BackupArn']
        print(f"✓ Backup created: {backup_name}")
        print(f"  ARN: {backup_arn}")
        return response
    except Exception as e:
        print(f"✗ Error creating backup: {e}")
        return None


def list_backups(table_name=None):
    """List backups"""
    try:
        response = dynamodb_client.list_backups()
        backups = response['BackupSummaries']

        if table_name:
            backups = [b for b in backups if b['TableName'] == table_name]

        print(f"\n📦 Backups ({len(backups)} total):")
        print("-" * 80)
        for backup in backups:
            print(f"  {backup['BackupName']:30} | Status: {backup['BackupStatus']}")

        return backups
    except Exception as e:
        print(f"✗ Error listing backups: {e}")
        return None


# ============================================================================
# 10. SCALING OPERATIONS
# ============================================================================

def update_provisioned_capacity(table_name, read_units, write_units):
    """Update provisioned throughput"""
    try:
        response = dynamodb_client.update_table(
            TableName=table_name,
            ProvisionedThroughput={
                'ReadCapacityUnits': read_units,
                'WriteCapacityUnits': write_units
            }
        )

        print(f"✓ Capacity updated for: {table_name}")
        print(f"  Read Capacity: {read_units} RCU")
        print(f"  Write Capacity: {write_units} WCU")
        return response
    except Exception as e:
        print(f"✗ Error updating capacity: {e}")
        return None


def switch_to_on_demand(table_name):
    """Switch table from provisioned to on-demand billing"""
    try:
        response = dynamodb_client.update_table(
            TableName=table_name,
            BillingMode='PAY_PER_REQUEST'
        )

        print(f"✓ Billing mode changed to PAY_PER_REQUEST for: {table_name}")
        return response
    except Exception as e:
        print(f"✗ Error switching billing mode: {e}")
        return None


# ============================================================================
# 11. STREAMS OPERATIONS
# ============================================================================

def enable_streams(table_name, stream_type='NEW_AND_OLD_IMAGES'):
    """Enable DynamoDB Streams"""
    try:
        response = dynamodb_client.update_table(
            TableName=table_name,
            StreamSpecification={
                'StreamViewType': stream_type,
                'StreamEnabled': True
            }
        )

        stream_arn = response['TableDescription'].get('LatestStreamArn')
        print(f"✓ Streams enabled for: {table_name}")
        print(f"  Stream View Type: {stream_type}")
        if stream_arn:
            print(f"  Stream ARN: {stream_arn}")
        return response
    except Exception as e:
        print(f"✗ Error enabling streams: {e}")
        return None


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AWS DynamoDB Boto3 Operations Examples")
    print("=" * 80)

    # Example 1: List tables
    print("\n[1] Listing Tables...")
    list_tables()

    # Example 2: Create table
    print("\n[2] Creating Table...")
    # create_table_on_demand('ExampleTable')

    # Example 3: Describe table
    # print("\n[3] Describing Table...")
    # describe_table('ExampleTable')

    print("\n✓ Examples completed!")
