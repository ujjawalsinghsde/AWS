# DynamoDB Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is Amazon DynamoDB and how is it different from RDS?**
   - DynamoDB: Fully managed NoSQL database, serverless, key-value and document structure
   - RDS: Managed relational database with SQL
   - DynamoDB: Horizontal scaling, eventual consistency by default
   - RDS: Vertical scaling primarily, ACID transactions

2. **Explain DynamoDB data model (tables, items, attributes).**
   - Table: Collection of items
   - Item: Single record with primary key + attributes
   - Primary Key: Partition key (required) + Sort key (optional)
   - Attributes: Key-value pairs (can be different types)
   - Max item size: 400 KB

3. **Explain DynamoDB capacity modes.**
   - **Provisioned Mode**: You specify RCU/WCU, pay per provisioned amount
     - RCU (Read Capacity Unit): 1 RCU = one 4 KB read per second
     - WCU (Write Capacity Unit): 1 WCU = one 1 KB write per second
   - **On-Demand Mode**: Pay-per-request, auto-scales, good for unpredictable traffic
   - Cost trade-off: Provisioned cheaper for predictable, on-demand better for variable

4. **What are global secondary indexes (GSI) and local secondary indexes (LSI)?**
   - **GSI**: Different partition key, optional sort key, 10 GB limit removed, eventual consistency
   - **LSI**: Same partition key, different sort key, 10 GB per partition key value, strong consistency
   - Use case: Query by different attributes than primary key

5. **Explain DynamoDB consistency models.**
   - **Eventual Consistency**: Default, cheaper, data available within milliseconds
   - **Strong Consistency**: Reads latest write, slightly higher latency, higher cost
   - Used in: GetItem, Query, Scan (optional)
   - Important: Transactions always strongly consistent

---

## 2. Intermediate Scenario-Based Questions

### Design & Scaling
6. **Scenario: Design a DynamoDB table for a social media application.**
   - Answer:
     - Primary table: User (PK: UserID)
     - Attributes: Name, Email, Profile, CreatedAt
     - GSI1 (EmailIndex): Email as PK, for login
     - GSI2 (CreatedAtIndex): CreatedAt as PK, for finding recent users
     - Posts table: PK: UserID, SK: PostID
     - Comments table: PK: PostID, SK: CommentID + UserID
     - Followers table: PK: UserID, SK: FollowerUserID
     - TTL: Set on temporary/session items

7. **Scenario: Your table throttles despite provisioning. Why?**
   - Causes:
     1. **Hot partition**: High traffic on specific partition key value
     2. **Skewed data**: One partition key receives majority of traffic
     3. **Range spikes**: Spike exceeds provisioned capacity
   - Solutions:
     1. Use on-demand capacity mode
     2. Increase capacity (short-term)
     3. Add random suffix to partition key (salt) to distribute load
     4. Implement caching with ElastiCache
     5. Review access patterns, consider GSI

8. **Explain DynamoDB batch operations and when to use them.**
   - BatchGetItem: Read up to 100 items
   - BatchWriteItem: Write up to 25 items
   - Benefits: Atomic operations, reduce API calls
   - Limitations: Must know item keys, can be partially successful
   - Example: Fetch user profiles for 50 users in single call

### Query Patterns
9. **Design query patterns for a real-time notification system.**
   - Table structure:
     - PK: UserID
     - SK: Timestamp (reverse = new notifications first)
     - Attributes: Message, Type, ReadFlag, TTL
   - Query: All notifications for user (last hour, unread only)
   - Pattern: Query with SK range + Filter expression for unread
   - Optimization: Create GSI on ReadFlag to count unread only

10. **Scenario: Need to find "top 10 users by follower count". How?**
    - Wrong approach: Scan entire table (expensive)
    - Right approach:
      - LeaderBoard table: PK: "global", SK: FollowerCount (reverse)
      - Update whenever user gains/loses follower
      - Query for top 10 (get first 10 items)
      - Alternative: Use ElastiCache leaderboard with Redis sorted sets

---

## 3. Advanced Problem-Solving Questions

### TTL & Data Management
11. **How do you implement TTL (Time To Live) and automated data expiration?**
    - Set TTL attribute with Unix timestamp
    - DynamoDB automatically deletes items after timestamp
    - No cost for TTL deletions
    - Use case: Sessions, temporary data, logs
    - Note: Deletion may take up to 48 hours (unpredictable)

12. **Scenario: You have user sessions in DynamoDB expiring in 1 hour. Design the cleanup.**
    - Approach 1 (Simple): Use TTL on session table
      - Set TTL to `current_time + 3600`
      - DynamoDB handles deletion
      - No active cleanup Lambda needed
    - Approach 2 (Precise): Custom cleanup Lambda
      - Periodic scan for expired sessions
      - Delete before DynamoDB automatic cleanup
      - More cost but more control

### Transactions & ACID
13. **Explain DynamoDB transactions and when to use them.**
    - Transact GetItems: Atomic reads
    - TransactWriteItems: Up to 25 writes atomic
    - Benefits: All-or-nothing semantics
    - Cost: 2x read/write consumption
    - Use case: Multi-item updates requiring consistency
    - Example: Transfer money (debit account A, credit account B)

14. **Scenario: Transfer amount between two user accounts. Ensure atomicity.**
    ```python
    # Wrong: Two separate updates (not atomic)
    # update_item(user1, {balance: user1.balance - 100})
    # update_item(user2, {balance: user2.balance + 100})

    # Correct: TransactWriteItems
    client.transact_write_items(
        TransactItems=[
            {
                'Update': {
                    'TableName': 'Accounts',
                    'Key': {'UserID': 'user1'},
                    'UpdateExpression': 'SET balance = balance - :amt',
                    'ExpressionAttributeValues': {':amt': 100}
                }
            },
            {
                'Update': {
                    'TableName': 'Accounts',
                    'Key': {'UserID': 'user2'},
                    'UpdateExpression': 'SET balance = balance + :amt',
                    'ExpressionAttributeValues': {':amt': 100}
                }
            }
        ]
    )
    ```

### Performance Optimization
15. **Optimize a DynamoDB query that takes 2 seconds, should be <100ms.**
    - Diagnosis:
      1. Check if using correct index (GSI with partition key = query condition)
      2. Use ConsistentRead=False for eventual consistency (faster)
      3. Limit item size (ProjectionExpression to fetch only needed attributes)
      4. Add caching layer (ElastiCache) for frequently accessed items
      5. Consider parallel queries if needed
    - Example optimization:
      ```python
      # Before: Slow, reads all attributes
      response = table.query(
          KeyConditionExpression='UserID = :id',
          ExpressionAttributeValues={':id': user_id}
      )

      # After: Fast, reads only needed attributes
      response = table.query(
          KeyConditionExpression='UserID = :id',
          ExpressionAttributeValues={':id': user_id},
          ProjectionExpression='UserID, #n, Email',  # Only these attributes
          ExpressionAttributeNames={'#n': 'Name'}  # Escape reserved names
      )
      ```

16. **Design a cost-optimized DynamoDB for analytics (mostly reads, millions of items).**
    - Use on-demand billing (reads cheaper per operation)
    - Implement aggressive caching (ElastiCache)
    - Archive old data to Redshift/S3 after retention period
    - Use Redshift for analytical queries (designed for OLAP)
    - DynamoDB for operational data (OLTP)
    - Implement data TTL for automatic cleanup

---

## 4. Best Practices & Optimization

17. **What are DynamoDB best practices?**
    - Design for your access patterns first (not relational design)
    - Use sparse indexes (attributes don't need to exist in all items)
    - Keep item size < 400 KB
    - Avoid hot partitions (use random suffixes if needed)
    - Use batch operations when possible
    - Implement caching for frequently accessed data
    - Monitor CloudWatch metrics: ConsumedRCU/WCU, UserErrors, SystemErrors
    - Use DynamoDB Streams for triggers/replication
    - Enable point-in-time recovery for backups

18. **How do you migrate from RDS to DynamoDB?**
    - Completely different data models (relational vs key-value)
    - Steps:
      1. Export RDS data to S3 (CSV/Parquet)
      2. Create Lambda to transform and load into DynamoDB
      3. Use RDS to DynamoDB with AWS DMS or custom ETL
      4. Validate data
      5. Update application code for DynamoDB queries
    - Challenge: Redesign queries from SQL to DynamoDB access patterns

---

## 5. Real-World Scenarios & Tricky Questions

19. **Scenario: Your DynamoDB table suddenly starts returning "ProvisionedThroughputExceededException". Root cause?**
    - Causes:
      1. Unplanned traffic spike
      2. Hot partition (specific partition key getting hammered)
      3. Query filtering returns large dataset
      4. Backup or restoration in progress
    - Diagnosis:
      - CloudWatch: ConsumedWriteCapacityUnits spike
      - DynamoDB Contributor Insights: Which partition keys are hot
    - Solutions:
      - Immediate: Increase provisioned capacity or switch to on-demand
      - Short-term: Handle throttling with exponential backoff
      - Long-term: Review access patterns, distribute load, implement caching

20. **Design a shopping cart system with items expiring after 30 minutes.**
    - Table: ShoppingCart
      - PK: SessionID, SK: ItemID
      - Attributes: Quantity, Price, AddedAt
      - TTL: AddedAt + 1800 (30 minutes)
    - Features:
      - Add/Remove items: UpdateItem
      - View cart: Query with SessionID
      - Checkout: Get all items from cart, clear TTL (persist), create order
      - Auto-cleanup: DynamoDB TTL removes expired items

21. **Scenario: DynamoDB contains user profile data. Ensure GDPR "right to be forgotten".**
    - Challenge: DynamoDB doesn't support full-text search
    - Solution:
      - Encryption at rest (KMS key)
      - Encryption in transit (TLS)
      - TTL for automatic deletion after X days
      - Application maintains audit log in different table
      - On deletion request: Delete from main table + related tables/indexes
      - Consider: How to handle Global Secondary Indexes (stay in sync)

22. **Compare DynamoDB vs ElastiCache for caching frequently accessed data.**
    - **DynamoDB**: Persistent, ACID transactions, complex queries, more durable
    - **ElastiCache**: In-memory, extremely fast, volatile, simple key-value
    - **Pattern**: ElastiCache in front of DynamoDB for hot data

23. **Design a notification queue using DynamoDB Streams and Lambda.**
    - Table: Events
    - Lambda subscribed to DynamoDB Streams
    - Trigger: New event inserted
    - Lambda: Process event (send email, SNS notification, etc.)
    - DynamoDB Stream records: OLD_IMAGE, NEW_IMAGE, KEYS_ONLY
    - Parallelization: Lambda processes shards in order (FIFO)

---

## 6. Query Language: DynamoDB Query vs Scan

24. **Explain the difference between Query and Scan operations.**
    - **Query**:
      - Uses primary key (partition + sort key conditions)
      - Efficient, returns items with matching partition key
      - Consumed RCU = items returned (not scanned)
    - **Scan**:
      - Returns all items in table
      - Inefficient for large tables
      - Consumed RCU = items scanned (even if filtered out)
    - Best practice: Always use Query when possible, Scan only when necessary

25. **How do you implement pagination for large result sets?**
    ```python
    def paginate_query(table, partition_key):
        items = []
        last_evaluated_key = None

        while True:
            kwargs = {
                'KeyConditionExpression': 'UserID = :id',
                'ExpressionAttributeValues': {':id': partition_key},
                'Limit': 100  # Items per page
            }

            if last_evaluated_key:
                kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = table.query(**kwargs)
            items.extend(response['Items'])

            if 'LastEvaluatedKey' not in response:
                break

            last_evaluated_key = response['LastEvaluatedKey']

        return items
    ```

---

## 7. Hands-On Coding Questions

26. **Write a Python function to interact with DynamoDB (CRUD operations):**
    ```python
    import boto3

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Users')

    # Create
    def create_user(user_id, name, email):
        response = table.put_item(
            Item={
                'UserID': user_id,
                'Name': name,
                'Email': email,
                'CreatedAt': int(time.time())
            }
        )
        return response

    # Read
    def get_user(user_id):
        response = table.get_item(Key={'UserID': user_id})
        return response.get('Item')

    # Update
    def update_user(user_id, name):
        response = table.update_item(
            Key={'UserID': user_id},
            UpdateExpression='SET #n = :name',
            ExpressionAttributeNames={'#n': 'Name'},
            ExpressionAttributeValues={':name': name},
            ReturnValues='ALL_NEW'
        )
        return response

    # Delete
    def delete_user(user_id):
        response = table.delete_item(Key={'UserID': user_id})
        return response
    ```

27. **Write a Lambda function that processes DynamoDB Streams:**
    ```python
    def lambda_handler(event, context):
        for record in event['Records']:
            event_name = record['eventName']  # INSERT, MODIFY, REMOVE

            if event_name == 'INSERT':
                new_item = record['dynamodb']['NewImage']
                on_user_created(new_item)

            elif event_name == 'MODIFY':
                old_item = record['dynamodb']['OldImage']
                new_item = record['dynamodb']['NewImage']
                on_user_updated(old_item, new_item)

            elif event_name == 'REMOVE':
                old_item = record['dynamodb']['OldImage']
                on_user_deleted(old_item)

        return {'statusCode': 200}

    def on_user_created(item):
        user_id = item['UserID']['S']
        # Send welcome email via SES
        send_email(item['Email']['S'], "Welcome!")

    def on_user_updated(old, new):
        # Log change for audit
        pass

    def on_user_deleted(item):
        # Cleanup related data
        pass
    ```

---

## Tips for Interview Success

- **Access pattern first**: Design tables around how you'll query them
- **Understand partitioning**: Hot partition is common issue
- **Master Query vs Scan**: Query is always preferred when possible
- **Know GSI/LSI trade-offs**: Different use cases
- **Cost optimization**: Choose capacity mode based on traffic patterns
- **Transactions**: Use for multi-item atomicity
- **Caching strategy**: DynamoDB + ElastiCache is common pattern
- **Streams**: For triggering Lambdas on changes
- **Monitoring**: CloudWatch metrics, contributor insights

