# AWS DynamoDB (NoSQL Database)

**Python boto3 code:** [dynamodb_operations.py](./dynamodb_operations.py)

---

## Table of Contents

1. [What is AWS DynamoDB?](#1-what-is-aws-dynamodb)
2. [Data Model & Terminology](#2-data-model--terminology)
3. [Creating Tables](#3-creating-tables)
4. [Provisioned vs On-Demand Billing](#4-provisioned-vs-on-demand-billing)
5. [Read & Write Operations](#5-read--write-operations)
6. [Batch Operations](#6-batch-operations)
7. [Global Secondary Indexes (GSI)](#7-global-secondary-indexes-gsi)
8. [Local Secondary Indexes (LSI)](#8-local-secondary-indexes-lsi)
9. [Query Operations](#9-query-operations)
10. [Scan Operations](#10-scan-operations)
11. [TTL (Time to Live)](#11-ttl-time-to-live)
12. [Streams & Triggers](#12-streams--triggers)
13. [Transactions](#13-transactions)
14. [Back ups & Point-in-Time Recovery](#14-backups--point-in-time-recovery)
15. [Scaling & Capacity](#15-scaling--capacity)
16. [Best Practices](#16-best-practices)
17. [CLI Cheat Sheet](#17-cli-cheat-sheet)
18. [Performance Optimization](#18-performance-optimization)
19. [Cost Optimization](#19-cost-optimization)
20. [Common Use Cases](#20-common-use-cases)

---

## 1. What is AWS DynamoDB?

**AWS DynamoDB** is a fully managed, serverless NoSQL database service that provides fast and predictable performance at any scale.

### Key Characteristics

- **NoSQL** - Flexible schema (unlike relational databases)
- **Serverless** - No servers to manage; auto-scaling
- **Global** - Global tables for multi-region replication
- **Fast** - Single-digit millisecond latency at scale
- **Scalable** - Handles millions of requests per second
- **Secure** - Encryption, VPC endpoints, IAM fine-grained access
- **Managed** - AWS handles replication, backups, patching

### When to Use DynamoDB

| Use Case | Why DynamoDB |
|----------|------------|
| **High-scale reads/writes** | Auto-scaling handles millions of requests |
| **Session storage** | Fast access, TTL for auto-cleanup |
| **Time series data** | Efficient query patterns |
| **Real-time leaderboards** | Sorted data sets, fast updates |
| **Caching layer** | Sub-millisecond latency |
| **IoT data** | Millions of sensors writing data |
| **Mobile backends** | Offline support + CloudSync |

### DynamoDB vs RDS vs MongoDB

| Aspect | DynamoDB | RDS (SQL) | MongoDB |
|--------|----------|----------|---------|
| **Type** | NoSQL | Relational | NoSQL |
| **Schema** | Flexible | Fixed | Flexible |
| **Joins** | Not native | Native | Have to do manually |
| **Scaling** | Horizontal (auto) | Vertical (manual) | Horizontal |
| **Consistency** | Eventual (tunable) | Strong | Eventual |
| **Cost** | Pay-per-request or provisioned | Fixed + variable | Self-managed complexity |

---

## 2. Data Model & Terminology

### Core Concepts

```
┌─ Table
│  └─ Item (Row/Document)
│     ├─ Attribute (Column/Field)
│     │  ├─ String (S)
│     │  ├─ Number (N)
│     │  ├─ Binary (B)
│     │  ├─ Map (M) - nested object
│     │  ├─ List (L) - array
│     │  ├─ String Set (SS)
│     │  ├─ Number Set (NS)
│     │  └─ Boolean (BOOL)
│     └─ Key Attributes
│        ├─ Partition Key (required)
│        └─ Sort Key (optional)
```

### Example Item

```json
{
  "UserID": "user123",                    // Partition Key
  "Timestamp": 1609459200,                // Sort Key
  "Name": "Alice",                        // String
  "Age": 28,                              // Number
  "Active": true,                         // Boolean
  "Tags": ["admin", "user"],              // List
  "Metadata": {                           // Map
    "LastLogin": 1609459200,
    "LoginCount": 42
  }
}
```

### Partition Key vs Sort Key

```
Partition Key (Hash Key):
  ├─ Required
  ├─ Uniquely identifies item (or group)
  ├─ DynamoDB hashes to distribute across partitions
  ├─ Example: UserID, DeviceID, CompanyID

Sort Key (Range Key):
  ├─ Optional
  ├─ Sorts items within partition
  ├─ Enables range queries
  ├─ Example: Timestamp, Name, Status

Together (Partition Key + Sort Key):
  └─ Forms composite primary key
  └─ Must be unique together
```

---

## 3. Creating Tables

### Create Simple Table

```python
import boto3

dynamodb = boto3.client('dynamodb')

response = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {
            'AttributeName': 'UserID',
            'KeyType': 'HASH'  # Partition key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'UserID',
            'AttributeType': 'S'  # String
        }
    ],
    BillingMode='PAY_PER_REQUEST',  # On-demand
    Tags=[
        {'Key': 'Environment', 'Value': 'production'}
    ]
)

print(f"Table created: {response['TableDescription']['TableName']}")
```

### Create Table with Sort Key

```python
response = dynamodb.create_table(
    TableName='UserActivity',
    KeySchema=[
        {'AttributeName': 'UserID', 'KeyType': 'HASH'},
        {'AttributeName': 'ActivityDate', 'KeyType': 'RANGE'}  # Sort key
    ],
    AttributeDefinitions=[
        {'AttributeName': 'UserID', 'AttributeType': 'S'},
        {'AttributeName': 'ActivityDate', 'AttributeType': 'N'}
    ],
    BillingMode='PROVISIONED',
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)
```

### Attribute Types

```
S  - String
N  - Number
B  - Binary
SS - String Set
NS - Number Set
BS - Binary Set
M  - Map (nested object)
L  - List (array)
BOOL - Boolean
NULL - Null value
```

---

## 4. Provisioned vs On-Demand Billing

### On-Demand Pricing (PAY_PER_REQUEST)

```
Cost:
  - Read:  $0.00013 per read unit
  - Write: $0.00065 per write unit
  - No minimum
  - Auto-scales instantly

Best for:
  ✓ Unpredictable traffic
  ✓ New applications
  ✓ Spiky workloads
  ✓ Variable request rates
```

### Provisioned Pricing (PROVISIONED)

```
Cost:
  - Read:  Reserved capacity * $0.00013 per unit-hour
  - Write: Reserved capacity * $0.00065 per unit-hour
  - Minimum charges apply
  - Fixed cost + overage charges

Best for:
  ✓ Predictable traffic
  ✓ Constant request rate
  ✓ Cost optimization (sustained high volume)

Capacity Units:
  - 1 RCU (Read):  1 strong consistent read of 4KB item
  - 1 WCU (Write): 1 write of 1KB item
```

### Switching Modes

```python
# Switch from Provisioned to On-Demand
dynamodb.update_table(
    TableName='Users',
    BillingMode='PAY_PER_REQUEST'
)

# Switch from On-Demand to Provisioned
dynamodb.update_table(
    TableName='Users',
    BillingMode='PROVISIONED',
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 5
    }
)
```

---

## 5. Read & Write Operations

### Put Item (Insert/Update)

```python
response = dynamodb.put_item(
    TableName='Users',
    Item={
        'UserID': {'S': 'user123'},
        'Name': {'S': 'Alice'},
        'Email': {'S': 'alice@example.com'},
        'Age': {'N': '28'},
        'Active': {'BOOL': True}
    }
)
```

### Get Item (Read)

```python
response = dynamodb.get_item(
    TableName='Users',
    Key={'UserID': {'S': 'user123'}}
)

item = response.get('Item')
if item:
    print(f"User: {item['Name']['S']}")
```

### Update Item (Modify)

```python
response = dynamodb.update_item(
    TableName='Users',
    Key={'UserID': {'S': 'user123'}},
    UpdateExpression='SET Email = :email, #age = :age',
    ExpressionAttributeNames={'#age': 'Age'},  # age is reserved word
    ExpressionAttributeValues={
        ':email': {'S': 'newemail@example.com'},
        ':age': {'N': '29'}
    },
    ReturnValues='ALL_NEW'  # Return updated item
)
```

### Delete Item

```python
response = dynamodb.delete_item(
    TableName='Users',
    Key={'UserID': {'S': 'user123'}}
)
```

### Write Capacity Units (WCU)

```
1 WCU = Write 1KB item per second

Examples:
  - 100 items/sec, 1KB each = 100 WCU
  - 10 items/sec, 500B each = 5 WCU (rounded up)
  - 1000 items/sec, 5KB each = 5000 WCU
```

### Read Capacity Units (RCU)

```
1 RCU = 1 strong consistent read of 4KB item per second
Or: 2 RCU = 1 eventually consistent read of 4KB item per second

Examples (strongly consistent):
  - 100 GetItem calls/sec, 2KB item = 100 RCU
  - 1000 queries/sec, 4KB items = 1000 RCU

Examples (eventually consistent):
  - 100 GetItem calls/sec, 2KB item = 50 RCU (half cost)
```

---

## 6. Batch Operations

### Batch Write

```python
# Write up to 25 items maximum
response = dynamodb.batch_write_item(
    RequestItems={
        'Users': [
            {
                'PutRequest': {
                    'Item': {
                        'UserID': {'S': 'user1'},
                        'Name': {'S': 'Alice'}
                    }
                }
            },
            {
                'PutRequest': {
                    'Item': {
                        'UserID': {'S': 'user2'},
                        'Name': {'S': 'Bob'}
                    }
                }
            },
            {
                'DeleteRequest': {
                    'Key': {'UserID': {'S': 'user3'}}
                }
            }
        ]
    }
)

# Check for unprocessed items
if response['UnprocessedItems']:
    print("Some items failed, retry later")
```

### Batch Get

```python
response = dynamodb.batch_get_item(
    RequestItems={
        'Users': {
            'Keys': [
                {'UserID': {'S': 'user1'}},
                {'UserID': {'S': 'user2'}}
            ],
            'ProjectionExpression': 'UserID, Name'  # Only these attributes
        }
    }
)

for item in response['Responses']['Users']:
    print(item)
```

---

## 7. Global Secondary Indexes (GSI)

### Create Table with GSI

```python
response = dynamodb.create_table(
    TableName='Users',
    KeySchema=[
        {'AttributeName': 'UserID', 'KeyType': 'HASH'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'UserID', 'AttributeType': 'S'},
        {'AttributeName': 'Email', 'AttributeType': 'S'},  # GSI key
        {'AttributeName': 'CreatedDate', 'AttributeType': 'N'}  # GSI sort key
    ],
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'EmailIndex',
            'KeySchema': [
                {'AttributeName': 'Email', 'KeyType': 'HASH'}
            ],
            'Projection': {'ProjectionType': 'ALL'},  # Include all attributes
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'IndexName': 'CreatedDateIndex',
            'KeySchema': [
                {'AttributeName': 'CreatedDate', 'KeyType': 'HASH'},
            ],
            'Projection': {'ProjectionType': 'KEYS_ONLY'},  # Only PK/SK
            'BillingMode': 'PROVISIONED',
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 5
            }
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)
```

### Query GSI

```python
response = dynamodb.query(
    TableName='Users',
    IndexName='EmailIndex',
    KeyConditionExpression='Email = :email',
    ExpressionAttributeValues={
        ':email': {'S': 'alice@example.com'}
    }
)

user = response['Items'][0] if response['Items'] else None
```

### GSI Characteristics

```
Global Secondary Index (GSI):
  ├─ Can have different PKs & SKs than base table
  ├─ Sparse (can be missing from some items)
  ├─ Eventually consistent only
  ├─ No size limit per partition key value
  ├─ Can be added/removed after table creation
  ├─ Has own provisioned throughput
  └─ Good for alternative access patterns

Local Secondary Index (LSI):
  ├─ Must have same PK as base table
  ├─ Different SK allowed
  ├─ Can be strongly consistent
  ├─ Limited to 10GB per partition key value
  ├─ Must be created at table creation time
  ├─ Shares throughput with base table
  └─ Less common than GSI
```

---

## 8. Local Secondary Indexes (LSI)

### Create Table with LSI

```python
response = dynamodb.create_table(
    TableName='UserActivity',
    KeySchema=[
        {'AttributeName': 'UserID', 'KeyType': 'HASH'},
        {'AttributeName': 'ActivityID', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'UserID', 'AttributeType': 'S'},
        {'AttributeName': 'ActivityID', 'AttributeType': 'S'},
        {'AttributeName': 'ActivityDate', 'AttributeType': 'N'}  # LSI sort key
    ],
    LocalSecondaryIndexes=[
        {
            'IndexName': 'UserActivityDateIndex',
            'KeySchema': [
                {'AttributeName': 'UserID', 'KeyType': 'HASH'},  # Same as base table
                {'AttributeName': 'ActivityDate', 'KeyType': 'RANGE'}  # Different SK
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)
```

---

## 9. Query Operations

### Query with Condition

```python
response = dynamodb.query(
    TableName='UserActivity',
    KeyConditionExpression='UserID = :uid AND ActivityDate BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':uid': {'S': 'user123'},
        ':start': {'N': '1609459200'},
        ':end': {'N': '1640995200'}
    },
    ScanIndexForward=False,  # Descending order
    Limit=100
)

for item in response['Items']:
    print(item)
```

### Key Condition Operators

```
= (Equality)                UserID = 'user123'
< (Less than)               Date < 1609459200
≤ (Less or equal)           Date <= 1609459200
> (Greater than)            Date > 1609459200
≥ (Greater or equal)        Date >= 1609459200
BETWEEN                     Date BETWEEN 100 AND 200
BEGINS_WITH                 ActivityID BEGINS_WITH "login_"
```

---

## 10. Scan Operations

### Scan Table

```python
response = dynamodb.scan(
    TableName='Users',
    FilterExpression='#age > :age AND Active = :active',
    ExpressionAttributeNames={'#age': 'Age'},
    ExpressionAttributeValues={
        ':age': {'N': '25'},
        ':active': {'BOOL': True}
    },
    Limit=100
)

for item in response['Items']:
    print(item)

# Check for more items
if response.get('LastEvaluatedKey'):
    print(f"More items available, pagination token: {response['LastEvaluatedKey']}")
```

### Scan vs Query

```
QUERY:
  ✓ Uses primary key or index key
  ✓ More efficient (O(log n) or O(1))
  ✓ Predictable cost
  ✗ Must know partition key
  ✗ Can't search across partitions

SCAN:
  ✓ Searches all items (O(n))
  ✗ Expensive and slow
  ✗ Unpredictable cost
  ✓ Can search any attribute

Rule: Use QUERY when possible, SCAN only as last resort
```

---

## 11. TTL (Time to Live)

### Enable TTL

```python
# Create table with TTL attribute
dynamodb.update_time_to_live(
    TableName='Sessions',
    TimeToLiveSpecification={
        'AttributeName': 'ExpirationTime',  # Unix timestamp
        'Enabled': True
    }
)

# Put item with TTL
dynamodb.put_item(
    TableName='Sessions',
    Item={
        'SessionID': {'S': 'sess123'},
        'UserID': {'S': 'user123'},
        'ExpirationTime': {'N': str(int(time.time()) + 3600)}  # 1 hour from now
    }
)
```

### TTL Characteristics

```
✓ Automatic item deletion (no WCU charged for deletion)
✓ Deletion happens within 48 hours (exact time varies)
✓ Saves storage and money
✓ Uses Unix timestamp (seconds since epoch)
✗ Exact deletion time not guaranteed
✗ Can't retrieve deleted items in that window
```

---

## 12. Streams & Triggers

### Enable DynamoDB Streams

```python
response = dynamodb.update_table(
    TableName='Users',
    StreamSpecification={
        'StreamViewType': 'NEW_AND_OLD_IMAGES',  # What to capture
        'StreamEnabled': True
    }
)

# Stream View Types:
# - KEYS_ONLY: Only key attributes
# - NEW_IMAGE: New item image only
# - OLD_IMAGE: Old item image only
# - NEW_AND_OLD_IMAGES: Both old and new
```

### Lambda Trigger on Stream

```python
# Lambda receives stream events
def lambda_handler(Records, context):
    for record in Records:
        if record['eventName'] == 'INSERT':
            new_item = record['dynamodb']['NewImage']
            print(f"Item inserted: {new_item}")
        elif record['eventName'] == 'MODIFY':
            old_item = record['dynamodb']['OldImage']
            new_item = record['dynamodb']['NewImage']
            print(f"Item modified: {new_item}")
        elif record['eventName'] == 'REMOVE':
            old_item = record['dynamodb']['OldImage']
            print(f"Item deleted: {old_item}")
```

---

## 13. Transactions

### Transaction Write

```python
response = dynamodb.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': 'Users',
                'Item': {
                    'UserID': {'S': 'user123'},
                    'Name': {'S': 'Alice'}
                }
            }
        },
        {
            'Update': {
                'TableName': 'UserStats',
                'Key': {'UserID': {'S': 'user123'}},
                'UpdateExpression': 'SET LoginCount = LoginCount + :inc',
                'ExpressionAttributeValues': {':inc': {'N': '1'}}
            }
        },
        {
            'Delete': {
                'TableName': 'InactiveUsers',
                'Key': {'UserID': {'S': 'user123'}}
            }
        }
    ]
)

# All succeed or all fail (ACID)
```

### Transaction Read

```python
response = dynamodb.transact_get_items(
    TransactItems=[
        {
            'Get': {
                'TableName': 'Users',
                'Key': {'UserID': {'S': 'user123'}}
            }
        },
        {
            'Get': {
                'TableName': 'UserStats',
                'Key': {'UserID': {'S': 'user123'}}
            }
        }
    ]
)

user = response['Responses'][0]['Item']
stats = response['Responses'][1]['Item']
```

---

## 14. Backups & Point-in-Time Recovery

### Create Backup

```python
response = dynamodb.create_backup(
    TableName='Users',
    BackupName='users-backup-20240101'
)

backup_arn = response['BackupDetails']['BackupArn']
print(f"Backup created: {backup_arn}")
```

### Point-in-Time Recovery

```python
# Enable PITR
dynamodb.update_continuous_backups(
    TableName='Users',
    PointInTimeRecoverySpecification={
        'PointInTimeRecoveryEnabled': True
    }
)

# Restore to specific point
response = dynamodb.restore_table_to_point_in_time(
    SourceTableName='Users',
    TargetTableName='Users-Restored',
    UseLatestRestorableTime=True
    # Or: RestoreDateTime=datetime(2024, 1, 1)
)
```

---

## 15. Scaling & Capacity

### Auto Scaling (Provisioned Mode)

```python
autoscaling = boto3.client('application-autoscaling')

# Register scalable target
autoscaling.register_scalable_target(
    ServiceNamespace='dynamodb',
    ResourceId='table/Users',
    ScalableDimension='dynamodb:table:WriteCapacityUnits',
    MinCapacity=5,
    MaxCapacity=40000
)

# Create scaling policy
autoscaling.put_scaling_policy(
    PolicyName='UserTableScaling',
    ServiceNamespace='dynamodb',
    ResourceId='table/Users',
    ScalableDimension='dynamodb:table:WriteCapacityUnits',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 70.0,
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'DynamoDBWriteCapacityUtilization'
        },
        'ScaleOutCooldown': 60,
        'ScaleInCooldown': 300
    }
)
```

---

## 16. Best Practices

### Design Patterns

```
✓ Use on-demand for unpredictable workloads
✓ Use provisioned + auto-scaling for predictable traffic
✓ Denormalize data (include related info in items)
✓ Use sparse GSIs (not all items have GSI attributes)
✓ Design table key structure for access patterns
✓ Use compression for large attributes
✓ Archive old data to S3 (comply with TTL)

❌ DON'T scan large tables (expensive)
❌ DON'T use sequential partition keys
❌ DON'T store large binary objects (use S3 + reference)
❌ DON'T have hot partitions (distribute evenly)
❌ DON'T forget TTL cleanup (causes storage bloat)
```

### Query Design

```
✓ Query using primary key when possible
✓ Use GSI for other access patterns
✓ Batch related reads (batch_get_item)
✓ Use ProjectionExpression to reduce data transfer
✓ Limit and pagination for large result sets

❌ DON'T rely on SCAN for important queries
❌ DON'T fetch all attributes if you need few
❌ DON'T ignore pagination limits
```

---

## 17. CLI Cheat Sheet

```bash
# Create table
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=UserID,AttributeType=S \
  --key-schema AttributeName=UserID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Describe table
aws dynamodb describe-table --table-name Users

# Put item
aws dynamodb put-item \
  --table-name Users \
  --item '{"UserID": {"S": "user1"}, "Name": {"S": "Alice"}}'

# Get item
aws dynamodb get-item \
  --table-name Users \
  --key '{"UserID": {"S": "user1"}}'

# Query
aws dynamodb query \
  --table-name Users \
  --key-condition-expression "UserID = :uid" \
  --expression-attribute-values '{":uid": {"S": "user1"}}'

# Scan
aws dynamodb scan --table-name Users

# Delete table
aws dynamodb delete-table --table-name Users
```

---

## 18. Performance Optimization

### Hot Partitions

```
Problem: One partition gets more traffic than others
Cause: Uneven partition key distribution
Solution:
  ├─ Add prefix/suffix to partition key
  ├─ Use time-based partitioning
  ├─ Reconsider access patterns
  └─ Use DynamoDB Adaptive Capacity (auto-scales)

Example - BAD (all users hash to same partition based on UserType):
  UserID: "ADMIN#1", "ADMIN#2" → All ADMIN requests to one partition

Example - GOOD (distribute evenly):
  UserID: "user#1234#PROFILE"
  UserID: "user#1234#SETTINGS"
  UserID: "user#1234#ACTIVITY"
```

### Query Optimization

```
✓ Use begins_with() for prefix searches
✓ Filter after query, not before
✓ Use GSI to avoid table scans
✓ Batch get related items
✓ Use consistent reads only when needed (2x cost)
✓ Pagination for large result sets
```

---

## 19. Cost Optimization

### Reduce Data Transfer

```
✓ Use ProjectionExpression (fetch only needed attributes)
✓ Compress strings before storing
✓ Remove attributes you don't need
✓ Use filtering (server-side filters reduce app processing)

Example:
# Bad: Fetch entire item (1KB)
item = dynamodb.get_item(
    TableName='Users',
    Key={'UserID': {'S': 'user123'}}
)

# Good: Fetch only needed attributes (100B)
item = dynamodb.get_item(
    TableName='Users',
    Key={'UserID': {'S': 'user123'}},
    ProjectionExpression='UserID, Name, Email'
)
```

### Estimated Monthly Cost

```
Example: 1 million users, 100 reads/sec, 10 writes/sec

ON-DEMAND:
  Reads:  100 RCU × 2.6M seconds/month × $0.00013 = $338
  Writes: 10 WCU × 2.6M seconds/month × $0.00065 = $169
  Total: ~$500/month

PROVISIONED + AUTOSCALING:
  Read:  100 RCU × $0.000013/hour = $10/month
  Write: 10 WCU × $0.000065/hour = $5/month
  Total: ~$15/month (much cheaper!)

But if traffic doubles:
  Read: 200 RCU × $0.000013/hour = $20/month
  Write: 20 WCU × $0.000065/hour = $10/month
  Total: ~$30/month
```

---

## 20. Common Use Cases

### User Sessions

```python
# Put session
dynamodb.put_item(
    TableName='Sessions',
    Item={
        'SessionID': {'S': 'sess_abc123'},
        'UserID': {'S': 'user123'},
        'CreatedAt': {'N': str(int(time.time()))},
        'ExpiresAt': {'N': str(int(time.time() + 86400))},
        'Data': {'M': {
            'IP': {'S': '192.168.1.1'},
            'UserAgent': {'S': 'Mozilla/...'}
        }}
    }
)

# TTL automatically deletes expired sessions
```

### Leaderboard

```python
# Players table with GSI on score
dynamodb.create_table(
    TableName='Players',
    KeySchema=[
        {'AttributeName': 'PlayerID', 'KeyType': 'HASH'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'PlayerID', 'AttributeType': 'S'},
        {'AttributeName': 'Score', 'AttributeType': 'N'},
        {'AttributeName': 'GameID', 'AttributeType': 'S'}
    ],
    GlobalSecondaryIndexes=[{
        'IndexName': 'GameScoreIndex',
        'KeySchema': [
            {'AttributeName': 'GameID', 'KeyType': 'HASH'},
            {'AttributeName': 'Score', 'KeyType': 'RANGE'}
        ],
        'Projection': {'ProjectionType': 'ALL'},
        'BillingMode': 'PAY_PER_REQUEST'
    }]
)

# Query top 10 scores
response = dynamodb.query(
    TableName='Players',
    IndexName='GameScoreIndex',
    KeyConditionExpression='GameID = :gid',
    ExpressionAttributeValues={':gid': {'S': 'game123'}},
    ScanIndexForward=False,  # Descending (highest first)
    Limit=10
)
```

### Time Series Data (IoT Sensors)

```python
# Sensor readings with timestamp sort key
dynamodb.put_item(
    TableName='SensorReadings',
    Item={
        'SensorID': {'S': 'sensor-001'},  # Partition key
        'Timestamp': {'N': '1609459200'},  # Sort key
        'Temperature': {'N': '23.5'},
        'Humidity': {'N': '65'},
        'ExpiresAt': {'N': str(int(time.time()) + 2592000))}  # 30 days
    }
)

# Query range of readings
response = dynamodb.query(
    TableName='SensorReadings',
    KeyConditionExpression='SensorID = :sid AND Timestamp BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':sid': {'S': 'sensor-001'},
        ':start': {'N': '1609459200'},
        ':end': {'N': '1609545600'}
    }
)
```
