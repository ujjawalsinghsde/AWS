# RDS Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is Amazon RDS and what databases does it support?**
   - Answer: Managed relational database service that automates setup, maintenance, backups, and patching
   - Supported engines: PostgreSQL, MySQL, MariaDB, Oracle, SQL Server, Aurora

2. **Explain RDS pricing model.**
   - On-Demand: Pay per hour, no commitment
   - Reserved Instances: 1-3 year commitment, up to 65% discount
   - Components: Database engine + storage + data transfer + backups

3. **What are the key RDS benefits over self-managed databases?**
   - Automated backups and point-in-time recovery (35 days)
   - Multi-AZ deployment for high availability
   - Read replicas for scaling reads
   - Automated patching and updates
   - Parameter groups for configuration management
   - Option groups for additional features
   - Automated failover with Multi-AZ

4. **Explain RDS Multi-AZ deployment.**
   - Synchronous replication to standby instance in different AZ
   - Automatic failover if primary fails (2-3 minutes)
   - Increased availability but not scalability
   - Higher cost (double compute resources)
   - Failover transparent to application

5. **What is an RDS read replica?**
   - Asynchronous copy of database (can have replication lag)
   - Different from standby (which is for failover)
   - Can be in same region or different region
   - Can promote to independent database
   - Useful for scaling read workloads
   - Reduces primary database load

---

## 2. Intermediate Scenario-Based Questions

### High Availability & Disaster Recovery
6. **Scenario: You need 99.99% uptime for your RDS database. Design the high availability architecture.**
   - Answer:
     - Enable Multi-AZ deployment (synchronous replication)
     - Set up automated backups (35 days retention)
     - Create read replicas in different region
     - Configure CloudWatch alarms for CPU, connections, storage
     - Set instance class to production-level (db.r5.xlarge minimum)
     - Enable Enhanced Monitoring
     - Use RDS Proxy for connection pooling
     - Test failover quarterly

7. **Scenario: Your database fails over from primary to standby. Walk through the process.**
   - RDS detects failure (network, instance, storage)
   - Standby promoted to primary (DNS endpoint updated)
   - Application reconnects automatically (usually within 2-3 minutes)
   - Original primary either repairs or new standby created
   - Best practice: Monitor and alert on failover events

### Scaling & Performance
8. **You have 10,000 read queries/second but only 100 writes/second. How to scale this?**
   - Create read replicas (3-5 replicas)
   - Distribute read traffic across replicas using Route 53 weighted routing
   - Use read replica endpoints in application
   - Cache frequently read data with ElastiCache
   - Implement query result caching
   - Optimize slow queries (identify with Slow Query Log)

9. **Your application reports "too many connections" error. Diagnose and fix.**
   - Root causes:
     1. Connection pool misconfig (too many connections)
     2. Leaking connections (not closing properly)
     3. Genuine spike in traffic
   - Solutions:
     - Use RDS Proxy for connection pooling (overcomes 65k max connections)
     - Implement connection pool settings in application
     - Monitor active connections with Enhanced Monitoring
     - Upgrade instance class for more resources
     - Terminate idle connections

10. **Scenario: Database query takes 30 seconds when it should be under 1 second. Debug.**
    - Use Query Performance Insights (available in RDS enhanced monitoring)
    - Check Slow Query Log for queries exceeding threshold
    - Analyze query execution plan (EXPLAIN)
    - Check for missing indexes
    - Monitor CPU, memory, IOPS utilization
    - Check for table locks or blocking queries
    - Verify network latency to database
    - Solutions: Add index, optimize query, upgrade instance, use cache

---

## 3. Advanced Problem-Solving Questions

### Backup & Disaster Recovery
11. **Design a disaster recovery strategy for RDS database with RPO=1 hour, RTO=15 minutes.**
    - RPO (1 hour): Automated backups every hour + Binary logs
    - RTO (15 minutes):
      - Read replica in different region (can promote quickly)
      - Automated backups for point-in-time recovery
      - Document runbook for restoration
      - Test recovery monthly
    - Architecture:
      - Primary: Multi-AZ in region A
      - Standby read replica: Region B (ready to promote)
      - Backups: Encrypted, retained 35 days
      - Monitoring: CloudWatch alarms for failures

12. **Scenario: You accidentally deleted critical data 2 hours ago. How to recover?**
    - Options:
      1. Point-in-time restore (PITR) to time before deletion
      2. Restore from snapshot if available
      3. Table-level restore (if using mysqldump or similar)
    - RDS supports 35-day backup window
    - New instance created from backup
    - Validate data on new instance before swapping
    - Document incident and prevent future occurrences

### Replication & Migration
13. **How do you migrate RDS database from one region to another with minimal downtime?**
    - Approach 1 (Minimal downtime):
      1. Create cross-region read replica
      2. Stop applications (write-down)
      3. Wait for replica to catch up
      4. Promote read replica to primary
      5. Update connection strings
      6. Verify application functionality
    - Approach 2 (Zero downtime - complex):
      1. Use AWS DMS (Database Migration Service)
      2. Continuous replication during migration
      3. Switch traffic smoothly

14. **Explain RDS replication lag and how to monitor it.**
    - Lag between primary write and replica read
    - Measured in seconds
    - Causes: Heavy write load, network latency, large transactions
    - Monitor: CloudWatch metric "ReplicationLag"
    - Implications:
      - Stale data on replicas (acceptable for read-heavy workloads)
      - Cannot use replica for failover if lag is high
    - Mitigation: Increase instance size, reduce write load, optimize queries

### Database Optimization
15. **Scenario: RDS costs tripled. Identify and reduce costs.**
    - Investigation:
      1. Check storage size increase
      2. Analyze backup size and count
      3. Review number of read replicas
      4. Check data transfer costs
      5. Review instance size utilization
    - Cost reduction:
      - Right-size instance (use Performance Insights)
      - Delete unused read replicas
      - Reduce backup retention (if acceptable)
      - Use Reserved Instances for baseline capacity
      - Move cold data to RDS Archive (if available)
      - Implement data lifecycle policies

16. **How do you optimize RDS for very large databases (100+ GB)?**
    - Storage: Use gp3 (better IOPS per GB vs gp2)
    - Instance size: db.r5.4xlarge or higher (memory for buffer pools)
    - Backup strategy:
      - Automated backups to S3
      - Snapshots copied to different region
      - Implement retention policies
    - Query optimization:
      - Proper indexing strategy
      - Partition large tables
      - Archive old data to Redshift or S3
      - Use materialized views for reporting

---

## 4. Best Practices & Database-Specific Questions

17. **What's the difference between PostgreSQL and MySQL on RDS?**
    - **PostgreSQL**: ACID-compliant, advanced features (JSON, arrays), stricter
    - **MySQL**: Simpler, faster for web applications, widely used, more permissive
    - **RDS Advantage**: Aurora for auto-scaling (better performance)

18. **How do you implement application-level resiliency with RDS?**
    - Connection retry logic with exponential backoff
    - Circuit breaker pattern (fail fast after N retries)
    - Use RDS Proxy for automatic retry and connection pooling
    - Implement query timeout
    - Use read replicas to reduce primary load
    - Cache query results when possible
    - Implement fallback to cached data

19. **Design a parameter group strategy for development, staging, and production.**
    - Development: Loose parameters for debugging
    - Staging: Mirror production config
    - Production: Optimized parameters with Conservative settings
    - Key parameters:
      - max_connections: Production higher
      - log_statement: Production selective (only slow queries)
      - shared_buffers: 25% of available memory
      - effective_cache_size: 50% for PostgreSQL
      - work_mem: 2-5MB per connection

---

## 5. Real-World Scenarios & Tricky Questions

20. **Scenario: RDS instance becomes unresponsive. Customers report errors. Emergency response.**
    - Immediate actions:
      1. Page on-call engineer
      2. Check RDS console for CPU, connections, storage
      3. Failover to standby if Multi-AZ (takes 2-3 min)
      4. Check error logs for OOM, deadlocks
      5. Scale up instance if CPU/memory exhausted
      6. Check for blocking queries
    - Post-incident: Implement auto-scaling, increase instance size, optimize queries

21. **Design a database connection pool strategy for microservices architecture.**
    - Challenge: Each microservice creates connections, total exceeds RDS limit (65k)
    - Solution: RDS Proxy
      - Single proxy manages connections to RDS
      - Microservices connect to proxy
      - Proxy maintains connection pool to RDS
      - Reduces connection count from thousands to hundreds
      - Transparent failover support

22. **Scenario: You need to test production data but can't copy full database. Solution?**
    - Options:
      1. Create snapshot, restore to different instance, subset data
      2. Use AWS Glue to sample data
      3. Create schema-only copy (no data)
      4. Use Aurora Clone feature (instant copy for testing)
    - Best practice: Implement data masking for PII before copying

23. **How do you enforce encryption for RDS?**
    - At-rest encryption: Enable when creating database (KMS key)
    - In-transit encryption: SSL/TLS connections (mandatory_ssl parameter)
    - Cannot enable encryption on unencrypted database (must restore)
    - Backup encryption: Automatic if database encrypted
    - Snapshot encryption: Can encrypt unencrypted snapshot when copying

24. **Scenario: Application uses hardcoded database password. Move to Secrets Manager.**
    - Create secret in Secrets Manager with credentials
    - Grant IAM role access to secret
    - Update application to fetch password from Secrets Manager
    - Enable automatic rotation (30 days)
    - Lambda function handles rotation (update password in RDS)
    - Application handles rotation (connection might briefly fail)

---

## 6. Monitoring & Troubleshooting

25. **What metrics should you monitor for RDS?**
    - Performance: CPUUtilization, DatabaseConnections, ReadLatency, WriteLatency
    - Capacity: FreeableMemory, StorageSpace, NetworkReceiveThroughput
    - Availability: DBInstanceStatus, Failover count, Replica lag
    - Backups: SnapshotStorageUsed, BackupRetentionPeriodStorageUsed
    - Set CloudWatch alarms on critical metrics

26. **How do you troubleshoot slow database queries?**
    - Enable Slow Query Log (configurable threshold)
    - Use Query Performance Insights (shows bottlenecks)
    - Analyze execution plans (EXPLAIN)
    - Check indexes and statistics
    - Monitor lock waits and blocking
    - Review application connection behavior
    - Use Enhanced Monitoring for OS-level visibility

---

## 7. Hands-On Coding Questions

27. **Write a Python function to connect to RDS with connection pooling:**
    ```python
    import psycopg2
    from psycopg2 import pool
    import os

    # Create connection pool
    db_pool = pool.SimpleConnectionPool(
        1,  # Minimum connections
        20,  # Maximum connections
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=5432
    )

    def get_connection():
        return db_pool.getconn()

    def return_connection(conn):
        db_pool.putconn(conn)

    def query_database(sql, params):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            return_connection(conn)

    # Usage
    results = query_database("SELECT * FROM users WHERE id = %s", (1,))
    ```

28. **Write a Lambda to fetch secrets from Secrets Manager and connect to RDS:**
    ```python
    import json
    import boto3
    import psycopg2

    secrets_client = boto3.client('secretsmanager')

    def lambda_handler(event, context):
        try:
            # Get database credentials
            secret_response = secrets_client.get_secret_value(
                SecretId='rds/prod/postgres'
            )
            secret = json.loads(secret_response['SecretString'])

            # Connect to RDS
            conn = psycopg2.connect(
                host=secret['host'],
                database=secret['dbname'],
                user=secret['username'],
                password=secret['password'],
                port=secret['port']
            )

            # Execute query
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            return {
                'statusCode': 200,
                'body': json.dumps({'user_count': result[0]})
            }

        except Exception as e:
            print(f"Error: {str(e)}")
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    ```

29. **Write a script to set up automated RDS backup to S3:**
    ```python
    import boto3

    rds = boto3.client('rds')
    s3 = boto3.client('s3')

    def backup_rds_to_s3(db_instance_id, s3_bucket):
        # Create RDS snapshot
        snapshot_id = f"{db_instance_id}-backup-{int(time.time())}"

        rds.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceIdentifier=db_instance_id
        )

        # Export to S3 (once snapshot is available)
        rds.start_export_task(
            ExportTaskIdentifier=f"export-{snapshot_id}",
            SourceArn=f"arn:aws:rds:region:account:snapshot:{snapshot_id}",
            S3BucketName=s3_bucket,
            S3Prefix="rds-backups/",
            IamRoleArn="arn:aws:iam::account:role/RDSExportRole",
            ExportOnly=[],  # Export all tables
            ExportFormat="PARQUET"  # or CSV
        )
    ```

---

## Tips for Interview Success

- **Know Multi-AZ vs Read Replicas**: Often confused, very important
- **Understand RDS Proxy**: Modern solution for connection issues
- **Master database optimization**: Indexes, query analysis, monitoring
- **Know disaster recovery**: RPO, RTO, backup strategies
- **Understand encryption**: At-rest and in-transit
- **Secrets management**: Never hardcode credentials
- **Cost optimization**: Instance sizing, storage, backup retention
- **Monitoring and alerting**: Key to production readiness

