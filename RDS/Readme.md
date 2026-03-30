# AWS RDS (Relational Database Service)

**Python boto3 code:** [rds_operations.py](./rds_operations.py)

---

## Table of Contents

1. [What is AWS RDS?](#1-what-is-aws-rds)
2. [Supported Database Engines](#2-supported-database-engines)
3. [RDS Architecture & Components](#3-rds-architecture--components)
4. [Creating RDS Instances](#4-creating-rds-instances)
5. [Connectivity & Security](#5-connectivity--security)
6. [Backups & Restore](#6-backups--restore)
7. [Multi-AZ & High Availability](#7-multi-az--high-availability)
8. [Read Replicas](#8-read-replicas)
9. [Scaling & Performance](#9-scaling--performance)
10. [Monitoring & Logging](#10-monitoring--logging)
11. [Maintenance & Patching](#11-maintenance--patching)
12. [Encryption at Rest & In Transit](#12-encryption-at-rest--in-transit)
13. [IAM Database Authentication](#13-iam-database-authentication)
14. [RDS Proxy](#14-rds-proxy)
15. [Aurora (Serverless RDS)](#15-aurora-serverless-rds)
16. [Performance Insights](#16-performance-insights)
17. [Cost Optimization](#17-cost-optimization)
18. [CLI Cheat Sheet](#18-cli-cheat-sheet)
19. [Best Practices](#19-best-practices)
20. [Advanced Topics](#20-advanced-topics)

---

## 1. What is AWS RDS?

**AWS RDS** is a managed relational database service that handles tedious administration tasks like backups, patch management, failover, and replication.

### Key Characteristics

- **Managed Service** - AWS handles backups, updates, monitoring, and failover.
- **Multi-Engine Support** - MySQL, MariaDB, PostgreSQL, Oracle, SQL Server, Aurora.
- **High Availability** - Multi-AZ deployments with automatic failover.
- **Scalability** - Read replicas for scaling reads; vertical scaling for compute.
- **Automated Backups** - Point-in-time recovery (35-day retention by default).
- **Encryption** - KMS encryption at rest and SSL/TLS in transit.
- **IAM Integration** - Native IAM authentication for databases.

### When to Use RDS

| Use Case | Why RDS Fits |
|----------|--------------|
| Relational data | Traditional SQL workloads (transactions, joins) |
| High availability | Multi-AZ with automatic failover (99.95% SLA) |
| Read scaling | Read replicas for distributed analytics queries |
| Compliance | Encryption, audit logging, HIPAA/PCI-DSS compliance |
| Managed operations | No patching, no backup management overhead |

---

## 2. Supported Database Engines

### Engine Comparison

| Engine | Best For | Limitations |
|--------|----------|------------|
| **PostgreSQL** | Advanced features, JSONB, Extensions | Slightly higher license cost |
| **MySQL 8.0** | Web apps, LAMP/MEAN stacks | Smaller ecosystem than PostgreSQL |
| **MariaDB** | MySQL alternative with 20% higher performance | Community-driven (less enterprise support) |
| **Oracle** | Enterprise workloads, legacy systems | Most expensive, licensing complex |
| **SQL Server** | .NET apps, enterprise Windows shops | Windows licensing costs |
| **Aurora MySQL** | Ultra-high performance, Global Database | Aurora-specific (not standard MySQL) |
| **Aurora PostgreSQL** | Advanced features + Aurora performance | Aurora-specific compatibility |

### Choosing Database Engine

```
✅ PostgreSQL: Complex queries, JSONB, PostGIS
✅ MySQL: Simple web apps, high compatibility
✅ MariaDB: Drop-in MySQL replacement
✅ Oracle: Mission-critical enterprise apps
✅ SQL Server: .NET ecosystem
✅ Aurora: Need extreme performance
```

---

## 3. RDS Architecture & Components

### RDS Instance Components

```
┌─────────────────────────────────────┐
│     RDS DB Instance                 │
├─────────────────────────────────────┤
│  DB Engine (PostgreSQL, MySQL, etc) │
│  - Storage Volume (EBS)             │
│  - Memory (instance type dependent) │
│  - Network Interface (ENI)          │
│  - Backup Storage                   │
└─────────────────────────────────────┘
```

### Key Terminology

- **DB Instance**: A database environment in the cloud. One instance = one database.
- **DB Instance Class**: Instance size (db.t3.micro, db.r5.large, etc.)
- **Storage Type**: General Purpose (gp2/gp3), Provisioned IOPS (io1/io2)
- **Storage Capacity**: 20 GB to 65 TB (varies by engine)
- **DB Subnet Group**: VPC subnets where RDS instances can be placed
- **Security Group**: Firewall rules controlling network access

### Instance Families

```
📊 db.t3/t4g     - Burstable (dev, test, small apps) - LOW COST
📊 db.m5/m6i    - General Purpose (balanced workloads)
📊 db.r5/r6i    - Memory Optimized (read-heavy, analytics)
📊 db.x1/x2     - Extreme Memory (SAP HANA, data warehouses)
```

---

## 4. Creating RDS Instances

### Minimal RDS Instance (Boto3)

```python
import boto3

rds = boto3.client('rds')

response = rds.create_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    DBInstanceClass='db.t3.micro',
    Engine='postgres',
    EngineVersion='15.3',
    MasterUsername='postgres',
    MasterUserPassword='MySecurePassword123!',
    AllocatedStorage=20,
    StorageType='gp2',
    StorageEncrypted=True,
    BackupRetentionPeriod=7,
    MultiAZ=False,
    PubliclyAccessible=False
)

print(f"DB Instance: {response['DBInstance']['DBInstanceIdentifier']}")
```

### Production-Grade RDS Instance

```python
response = rds.create_db_instance(
    DBInstanceIdentifier='prod-postgres',
    DBInstanceClass='db.r5.large',
    Engine='postgres',
    EngineVersion='15.3',
    MasterUsername='admin',
    MasterUserPassword='ComplexPassword123!@#',
    AllocatedStorage=100,
    StorageType='gp3',
    Iops=3000,
    StorageEncrypted=True,
    KmsKeyId='arn:aws:kms:us-east-1:123456789:key/12345',
    BackupRetentionPeriod=35,
    PreferredBackupWindow='03:00-04:00',
    PreferredMaintenanceWindow='sun:04:00-sun:05:00',
    MultiAZ=True,
    PubliclyAccessible=False,
    VpcSecurityGroupIds=['sg-0123456789abcdef0'],
    DBSubnetGroupName='default',
    EnableIAMDatabaseAuthentication=True,
    EnableCloudwatchLogsExports=['postgresql'],
    EnableEnhancedMonitoring=True,
    MonitoringInterval=60,
    DeletionProtection=True,
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Application', 'Value': 'myapp'}
    ]
)
```

### Parameters Explained

| Parameter | Purpose | When to Change |
|-----------|---------|-----------------|
| **DBInstanceClass** | Compute size | For scaling performance |
| **AllocatedStorage** | Initial disk size | RDS can autoscale if configured |
| **StorageType** | gp2/gp3/io1/io2 | io1/io2 for high IOPS workloads |
| **MultiAZ** | Sync replica in another AZ | Always true for production |
| **BackupRetentionPeriod** | Days to keep backups | Longer = higher cost but better compliance |
| **EnableIAMDBAuth** | Use IAM roles instead of passwords | Recommended for security |

---

## 5. Connectivity & Security

### VPC & Security Group Setup

```python
# Modify Security Group to allow database connections
ec2 = boto3.client('ec2')

ec2.authorize_security_group_ingress(
    GroupId='sg-0123456789abcdef0',
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 5432,
            'ToPort': 5432,
            'IpRanges': [
                {'CidrIp': '10.0.0.0/16', 'Description': 'VPC CIDR'},
                {'CidrIp': '10.1.0.0/16', 'Description': 'On-premises'}
            ]
        }
    ]
)
```

### Port Numbers by Engine

| Engine | Default Port |
|--------|--------------|
| PostgreSQL | 5432 |
| MySQL | 3306 |
| Oracle | 1521 |
| SQL Server | 1433 |

### Connecting to RDS

```python
import psycopg2

# Get endpoint
db_endpoint = 'my-postgres-db.c9akciq32.us-east-1.rds.amazonaws.com'

# Connect (Password Auth)
conn = psycopg2.connect(
    host=db_endpoint,
    port=5432,
    database='mydb',
    user='postgres',
    password='MyPassword123'
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
conn.close()
```

### IAM Database Authentication (Recommended)

```python
import pymysql
from aws_cdk import Duration
import boto3

# Generate auth token (token valid for 15 minutes)
rds = boto3.client('rds')

token = rds.generate_db_auth_token(
    DBHostname='my-mysql-db.c9akciq32.us-east-1.rds.amazonaws.com',
    Port=3306,
    DBUser='iamuser'
)

# Connect using token as password
conn = pymysql.connect(
    host='my-mysql-db.c9akciq32.us-east-1.rds.amazonaws.com',
    port=3306,
    user='iamuser',
    password=token,
    ssl={'ssl': True}
)
```

---

## 6. Backups & Restore

### Automated Backups

```python
# Modify backup settings
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    BackupRetentionPeriod=35,  # Days
    PreferredBackupWindow='03:00-04:00',  # UTC, 1-hour window
    ApplyImmediately=True
)
```

### Manual Snapshots

```python
# Create snapshot
snapshot_response = rds.create_db_snapshot(
    DBSnapshotIdentifier='my-postgres-db-snapshot-20240101',
    DBInstanceIdentifier='my-postgres-db'
)

# List snapshots
snapshots = rds.describe_db_snapshots(
    DBInstanceIdentifier='my-postgres-db'
)

# Restore from snapshot
rds.restore_db_instance_from_db_snapshot(
    DBInstanceIdentifier='my-postgres-db-restored',
    DBSnapshotIdentifier='my-postgres-db-snapshot-20240101'
)
```

### Point-in-Time Recovery (PITR)

```python
from datetime import datetime, timedelta

# Restore to a specific point in time
recovery_time = datetime.utcnow() - timedelta(days=2)

rds.restore_db_instance_to_point_in_time(
    SourceDBInstanceIdentifier='my-postgres-db',
    TargetDBInstanceIdentifier='my-postgres-db-restored-pitr',
    RestoreTime=recovery_time,
    UseLatestRestorableTime=False  # Set to True to use most recent available
)
```

### Backup Window Best Practices

```
⏰ Schedule backups during LOW TRAFFIC HOURS
   - Development: Any time (backup has minimal impact)
   - Production: Off-peak hours (e.g., 02:00-03:00 UTC)

📊 Retention Planning
   - Default: 7 days (usually enough for bugs caught within a week)
   - Compliance: 30-90 days (regulatory requirements)
   - Archive: Move old backups to S3 for cost savings
```

---

## 7. Multi-AZ & High Availability

### Multi-AZ Architecture

```
Primary Instance (us-east-1a)  ────────────────  Standby Instance (us-east-1b)
    Master                              SYNC            Passive
   (Reads/Writes)                    Replication       (Failover only)

    ↓ Failed

Automatic Failover (< 2 minutes) → Standby becomes Primary
```

### Enable Multi-AZ

```python
# For new instance
rds.create_db_instance(
    ...
    MultiAZ=True,
    ...
)

# For existing instance
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    MultiAZ=True,
    ApplyImmediately=False  # Applied during maintenance window
)
```

### Failover Behavior

```python
# Manually trigger failover (for testing)
rds.reboot_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    ForceFailover=True  # If MultiAZ enabled
)

# Connection string remains same - RDS DNS resolves to new primary
```

### SLA & RTO/RPO

```
Multi-AZ SLA:    99.95% availability
RTO (Recovery Time Objective):  ~2 minutes
RPO (Recovery Point Objective): 0 seconds (synchronous replication)
Failover:        Automatic (no intervention needed)
```

---

## 8. Read Replicas

### Creating Read Replicas

```python
# Read replica in same region
rds.create_db_instance_read_replica(
    DBInstanceIdentifier='my-postgres-db-read-replica-1',
    SourceDBInstanceIdentifier='my-postgres-db'
)

# Read replica in different region (cross-region)
rds.create_db_instance_read_replica(
    DBInstanceIdentifier='my-postgres-db-read-replica-cross-region',
    SourceDBInstanceIdentifier='my-postgres-db',
    SourceRegion='us-east-1'  # Different region
)

# High-performance read replica
rds.create_db_instance_read_replica(
    DBInstanceIdentifier='my-postgres-db-analytics',
    SourceDBInstanceIdentifier='my-postgres-db',
    DBInstanceClass='db.r5.xlarge'  # Larger than source
)
```

### Read Replica Use Cases

| Use Case | Why Read Replicas |
|----------|------------------|
| **Analytics Queries** | Separate read traffic from transactional writes |
| **Reporting** | Long-running queries don't slow down production |
| **Multi-region** | Serve users from nearest region (low latency) |
| **HA for reads** | Failover if primary becomes read-only |
| **Testing** | Promote replica to standalone DB for testing |

### Promoting Read Replica to Standalone DB

```python
# Replica becomes independent primary
rds.promote_read_replica(
    DBInstanceIdentifier='my-postgres-db-read-replica-1',
    BackupRetentionPeriod=7  # Now needs its own backups
)
```

### Key Differences: Multi-AZ vs Read Replicas

| Feature | Multi-AZ | Read Replicas |
|---------|----------|---------------|
| **Purpose** | High Availability | Scaling reads |
| **Synchronous** | Yes | No (async - eventual consistency) |
| **Failover** | Automatic | Manual promotion |
| **Visibility** | Hidden from application | Must route reads to replica |
| **Latency** | Same region (low) | May be different region |
| **Cost** | Doubles compute cost | Costs same as primary |

---

## 9. Scaling & Performance

### Vertical Scaling (Instance Type)

```python
# Scale up to larger instance type
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    DBInstanceClass='db.r5.xlarge',  # Larger
    ApplyImmediately=False  # During maintenance window (causes downtime)
)

# Apply immediately (causes brief downtime)
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    DBInstanceClass='db.r5.xlarge',
    ApplyImmediately=True
)
```

### Storage Scaling (Auto Scaling)

```python
# Enable storage autoscaling
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    AllocatedStorage=100,
    StorageType='gp3',
    MaxAllocatedStorage=1000,  # Auto-scale up to 1TB
    ApplyImmediately=True
)
```

### IOPS Scaling (io1/io2 storage)

```python
# Increase IOPS for high-traffic workloads
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    StorageType='io2',
    Iops=5000,  # 50 IOPS per GB, max 64000
    ApplyImmediately=True
)
```

### When to Scale

```
📈 VERTICAL SCALING (instance type)
   - High CPU usage (>70%)
   - Insufficient memory
   - Bursty traffic patterns

📈 HORIZONTAL SCALING (read replicas)
   - Read-heavy workloads
   - Analytics/reporting queries
   - Global distribution needed

💾 STORAGE SCALING
   - Growing dataset
   - Auto-scaling prevents full disk
```

---

## 10. Monitoring & Logging

### CloudWatch Metrics

```python
# Get key metrics
cloudwatch = boto3.client('cloudwatch')

response = cloudwatch.get_metric_statistics(
    Namespace='AWS/RDS',
    MetricName='CPUUtilization',
    Dimensions=[
        {'Name': 'DBInstanceIdentifier', 'Value': 'my-postgres-db'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    Period=300,  # 5-minute intervals
    Statistics=['Average', 'Maximum']
)

for datapoint in response['Datapoints']:
    print(f"{datapoint['Timestamp']}: {datapoint['Average']}%")
```

### Important Metrics to Monitor

| Metric | Normal Range | Alert At |
|--------|--------------|----------|
| **CPUUtilization** | < 50% | > 80% |
| **DatabaseConnections** | Variable | Near max |
| **ReadLatency** | < 5ms | > 10ms |
| **WriteLatency** | < 10ms | > 20ms |
| **DiskQueueDepth** | < 10 | > 100 |
| **FreeableMemory** | > 20% | < 10% |
| **SlowQueryCount** | Low | Increasing trend |

### Enhanced Monitoring

```python
# Enable Enhanced Monitoring (more detailed OS-level metrics)
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EnableEnhancedMonitoring=True,
    MonitoringInterval=60,  # 1 minute (charged per second)
    MonitoringRoleArn='arn:aws:iam::123456789:role/rds-monitoring'
)
```

### Enable Logging

```python
# Enable PostgreSQL logs
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    CloudwatchLogsExportConfiguration={
        'LogTypesToEnable': ['postgresql']  # Also: 'upgrade'
    }
)

# View logs in CloudWatch Logs
logs = boto3.client('logs')
log_events = logs.get_log_events(
    logGroupName='/aws/rds/instance/my-postgres-db/postgresql',
    logStreamName='postgresql.log'
)
```

---

## 11. Maintenance & Patching

### Maintenance Windows

```python
# Set preferred maintenance window
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    PreferredMaintenanceWindow='sun:04:00-sun:05:00',  # UTC
    ApplyImmediately=False
)
```

### Available Maintenance Actions

```
🔧 AWS Patches:  Security updates, OS patches (usually no downtime)
🔧 Engine Patches: Database engine updates (may require downtime)
🔧 OS Updates: Operating system patches (may cause brief downtime)
🔧 Hardware Refresh: Physical host replacement (Multi-AZ provides HA)
```

### View Pending Maintenance

```python
instances = rds.describe_db_instances(
    DBInstanceIdentifier='my-postgres-db'
)

for db in instances['DBInstances']:
    print(f"Pending Maintenance: {db.get('PendingMaintenanceActions', [])}")
```

### Apply Updates

```python
# Apply immediately (causes downtime)
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EngineVersion='15.4',
    ApplyImmediately=True
)

# Schedule for maintenance window
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EngineVersion='15.4',
    ApplyImmediately=False
)
```

---

## 12. Encryption at Rest & In Transit

### At-Rest Encryption (KMS)

```python
# Enable encryption when creating instance
rds.create_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    StorageEncrypted=True,
    KmsKeyId='arn:aws:kms:us-east-1:123456789:key/12345',
    ...
)

# Encrypted snapshots
snapshot = rds.create_db_snapshot(
    DBSnapshotIdentifier='my-snapshot',
    DBInstanceIdentifier='my-postgres-db'
)
# Snapshots inherit encryption from source

# Restore from encrypted snapshot
rds.restore_db_instance_from_db_snapshot(
    DBInstanceIdentifier='restored-db',
    DBSnapshotIdentifier='my-snapshot',
    StorageEncrypted=True  # Inherited
)
```

### In-Transit Encryption (SSL/TLS)

```python
# PostgreSQL - require SSL
import psycopg2

conn = psycopg2.connect(
    host='my-postgres-db.c9akciq32.us-east-1.rds.amazonaws.com',
    sslmode='require',  # Enforce SSL
    sslrootcert='/path/to/rds-ca-2019-root.pem',  # Verify certificate
    ...
)
```

### KMS Permissions

```python
# Lambda needs permission to decrypt
iam = boto3.client('iam')

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt",
                "kms:DescribeKey"
            ],
            "Resource": "arn:aws:kms:us-east-1:123456789:key/12345"
        }
    ]
}
```

---

## 13. IAM Database Authentication

### Setting Up IAM Authentication

```python
# Enable IAM authentication on instance
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EnableIAMDatabaseAuthentication=True,
    ApplyImmediately=True
)

# Create database user mapped to IAM role
# Connect as Master user first, then:
"""
-- PostgreSQL
CREATE USER iam_lambda;
GRANT rds_iam TO iam_lambda;
"""

# IAM Role for Lambda
iam = boto3.client('iam')
iam.attach_role_policy(
    RoleName='my-lambda-role',
    PolicyArn='arn:aws:iam::aws:policy/AmazonRDSFullAccess'
)
```

### Lambda Connecting with IAM Auth

```python
import boto3
import psycopg2

def lambda_handler(event, context):
    rds = boto3.client('rds')

    # Generate auth token (valid 15 minutes)
    token = rds.generate_db_auth_token(
        DBHostname='my-postgres-db.c9akciq32.us-east-1.rds.amazonaws.com',
        Port=5432,
        DBUser='iam_lambda'
    )

    # Connect using token
    conn = psycopg2.connect(
        host='my-postgres-db.c9akciq32.us-east-1.rds.amazonaws.com',
        port=5432,
        database='mydb',
        user='iam_lambda',
        password=token,
        sslmode='require'
    )

    return {'statusCode': 200, 'body': 'Connected!'}
```

### Benefits of IAM Auth

```
✅ No password management - uses temporary credentials
✅ Credentials in CloudTrail - Security auditing
✅ Granular permissions - Different roles for different apps
✅ Short-lived - Token valid only 15 minutes
✅ Centralized access control - Managed through IAM
```

---

## 14. RDS Proxy

### What is RDS Proxy?

```
┌─────────────────────────────────────────────────┐
│  Application Pool                               │
│  - Lambda  - ECS  - EC2  - Microservices        │
└────────────────────────┬────────────────────────┘
                         │ HTTP request
                         ↓
              ┌──────────────────────┐
              │    RDS Proxy         │
              │  Connection Pool     │
              │  - Multiplexing      │
              │  - IAM Auth          │
              │  - Query Caching     │
              └──────────┬───────────┘
                         │
                         ↓
                  ┌──────────────────┐
                  │  RDS Instance    │
                  │  ~500 Connections│
                  └──────────────────┘

RDS Proxy holds persistent connections to DB
Applications connect to Proxy (ephemeral connections)
Proxy reuses DB connections (connection pooling)
```

### Creating RDS Proxy

```python
# Create proxy
rds = boto3.client('rds')

rds.create_db_proxy(
    DBProxyName='my-app-proxy',
    EngineFamily='POSTGRESQL',
    Auth=[
        {
            'AuthScheme': 'SECRETS',
            'SecretArn': 'arn:aws:secretsmanager:us-east-1:123456789:secret:db-password'
        }
    ],
    RoleArn='arn:aws:iam::123456789:role/rds-proxy-role',
    DBProxySecurityGroupIds=['sg-0123456789abcdef0'],
    SubnetIds=['subnet-12345', 'subnet-67890'],
    RequireTLS=True,
    IdleClientTimeout=900,  # Disconnect idle connections after 15 min
    MaxIdleConnectionsPercent=50,
    ConnectionBorrowTimeout=120
)

# Create proxy target group
rds.create_db_proxy_target_group(
    DBProxyName='my-app-proxy',
    TargetGroupName='default',
    DBInstanceIdentifiers=['my-postgres-db']
)
```

### Connecting Through RDS Proxy

```python
# Connection string changes to:
# proxy.endpoint instead of instance directendpoint

import psycopg2

proxy_endpoint = 'my-app-proxy.proxy-c9akciq32.us-east-1.rds.amazonaws.com'

conn = psycopg2.connect(
    host=proxy_endpoint,  # Use proxy endpoint
    port=5432,
    database='mydb',
    user='postgres',
    password='MyPassword123'
)

cursor = conn.cursor()
cursor.execute("SELECT 1")
conn.close()
```

### RDS Proxy Benefits

| Benefit | How |
|---------|-----|
| **Lower Latency** | Connection pooling reduces handshake overhead |
| **Handle Spikes** | 1000 Lambda invocations → 50 proxy connections to DB |
| **Graceful Failover** | Proxy is in front of RDS instance |
| **Query Caching** | Optional - cache SELECT results |
| **IAM Support** | Supports IAM database authentication |

### When to Use RDS Proxy

```
✅ Lambda-heavy workloads (frequent connection churn)
✅ Microservices with many connection creators
✅ Need connection pooling without application code changes
✅ Burst traffic patterns

❌ Long-running connections (keep proxy idle)
❌ Streaming results (proxy buffers in memory)
❌ Application already has pooling (redundant)
```

---

## 15. Aurora (Serverless RDS)

### Aurora vs Standard RDS

| Feature | Aurora | Standard RDS |
|---------|--------|-------------|
| **Architecture** | Shared storage layer | Instance storage |
| **Scaling** | Instant (shared cluster) | Requires instance type change |
| **Replicas** | Built-in (highly available) | Manual multi-AZ |
| **Performance** | 5x MySQL, 3x PostgreSQL | Baseline |
| **Cost** | Higher per hour, lower overall | Lower per hour |
| **Downtime on failover** | < 30 seconds | 2+ minutes |
| **Serverless option** | Yes (Aurora Serverless v2) | No |

### Aurora Serverless v2

```python
# Create Aurora Serverless instance
rds.create_db_cluster(
    DBClusterIdentifier='my-aurora-serverless',
    Engine='aurora-postgresql',
    EngineVersion='15.2',
    EngineMode='provisioned',  # Serverless v2
    DatabaseName='mydb',
    MasterUsername='postgres',
    MasterUserPassword='MyPassword123',
    ServerlessV2ScalingConfiguration={
        'MinCapacity': 0.5,  # 0.5 - 128 ACUs
        'MaxCapacity': 2
    }
)

# Add instances to cluster
rds.create_db_instance(
    DBInstanceIdentifier='my-aurora-instance-1',
    DBInstanceClass='db.serverless',
    Engine='aurora-postgresql',
    DBClusterIdentifier='my-aurora-serverless'
)
```

### When to Use Aurora

```
✅ Need high availability (built-in replicas)
✅ Read-heavy + write-heavy workloads (same performance)
✅ Global scale (Aurora Global Database)
✅ Serverless auto-scaling (unpredictable traffic)

❌ Need specific database features (check Aurora compatibility)
❌ Cost-sensitive with predictable low traffic (Standard RDS cheaper)
❌ Single-region, single-AZ is sufficient
```

---

## 16. Performance Insights

### Enable Performance Insights

```python
# Enable when creating instance
rds.create_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EnablePerformanceInsights=True,
    PerformanceInsightsRetentionPeriod=7,  # Days
    PerformanceInsightsKMSKeyId='arn:aws:kms:us-east-1:123456789:key/12345',
    ...
)

# Or enable on existing instance
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    EnablePerformanceInsights=True,
    ApplyImmediately=False
)
```

### View Performance Data

```python
pi = boto3.client('pi')

# Get performance data
response = pi.get_resource_metrics(
    ServiceType='RDS',
    Identifier='db-ABC123DEFG456HIJ',
    StartTime=datetime.utcnow() - timedelta(hours=1),
    EndTime=datetime.utcnow(),
    PeriodInSeconds=60,
    MetricQueries=[
        {
            'Metric': 'db.load.weighted'
        }
    ]
)

print(response)
```

### Key Performance Insights Metrics

```
📊 db.load.weighted    - Number of active sessions
📊 db.rows.read       - Scan efficiency
📊 db.rows.returned   - Output rows
📊 db.rows.written    - DML statements
📊 db.wait_events     - Lock contentions, I/O waits
```

---

## 17. Cost Optimization

### Rightsizing Instances

```
📊 Understand Your Usage (CloudWatch, Performance Insights)
   1. High CPU but low memory → upgrade CPU not RAM
   2. Low CPU, high memory → memory-optimized instance may be waste
   3. Bursty traffic → t3 (burstable) better than r5 (memory-only)

💡 Calculation:
   Current instance cost × utilization × redundancy
```

### Cost Reduction Strategies

| Strategy | Savings |
|----------|---------|
| **Reserved Instances (1-3 year)** | 50-70% savings |
| **Read Replicas for reporting** | Separates workloads (cheaper than upscaling primary) |
| **Consolidate small DBs** | Fewer instances = lower overhead |
| **Store logs in S3, not RDS** | RDS storage is expensive |
| **Use gp3 instead of gp2** | 20% cheaper, same performance |
| **Turn off backups for dev** | Backups cost storage |
| **Aurora for scale workloads** | More cost-effective at large scale |

### Cost Tracking

```python
# Track RDS costs
ce = boto3.client('ce')

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': '2024-01-01',
        'End': '2024-01-31'
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    Filter={
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['Amazon Relational Database Service']
        }
    }
)
```

---

## 18. CLI Cheat Sheet

```bash
# Create instance
aws rds create-db-instance \
  --db-instance-identifier my-postgres-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password MyPassword123

# Describe instances
aws rds describe-db-instances --db-instance-identifier my-postgres-db

# Modify instance
aws rds modify-db-instance \
  --db-instance-identifier my-postgres-db \
  --db-instance-class db.t3.small \
  --apply-immediately

# Create snapshot
aws rds create-db-snapshot \
  --db-snapshot-identifier my-snapshot \
  --db-instance-identifier my-postgres-db

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier restored-db \
  --db-snapshot-identifier my-snapshot

# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier my-replica \
  --source-db-instance-identifier my-postgres-db

# Delete instance
aws rds delete-db-instance \
  --db-instance-identifier my-postgres-db \
  --skip-final-snapshot
```

---

## 19. Best Practices

### Security

```
🔒 Enable encryption at rest (KMS)
🔒 Enable encryption in transit (SSL/TLS)
🔒 Use IAM authentication instead of database passwords
🔒 Restrict security groups to minimum required access
🔒 Use private subnets (not publicly accessible)
🔒 Audit logs to CloudWatch Logs
🔒 Regular secret rotation (if using passwords)
🔒 Enable deletion protection for production
🔒 MFA delete for automated backups
```

### High Availability

```
🎯 Enable Multi-AZ for production
🎯 Automated backups with 35-day retention
🎯 Test disaster recovery (PITR, snapshots)
🎯 Monitor failover events (should be automatic)
🎯 Use RDS Proxy for connection resilience
🎯 Read replicas for geographically distributed reads
```

### Performance

```
⚡ Use read replicas for read-heavy workloads
⚡ Monitor slow query logs
⚡ Add indexes for common queries
⚡ Use connection pooling (RDS Proxy or app-level)
⚡ Vertical scaling for CPU/memory bound workloads
⚡ Horizontal scaling (read replicas) for read-bound workloads
⚡ Aurora for extreme performance needs
```

### Operations

```
🔧 Schedule maintenance windows during low traffic
🔧 Test update processes in dev first
🔧 Use CloudFormation/IaC for infrastructure
🔧 Monitor key metrics (CPU, connections, latency)
🔧 Implement database parameters backup
🔧 Regular backup verification (restore and test)
🔧 Document connection strings and credentials (AWS Secrets Manager)
```

---

## 20. Advanced Topics

### Database Parameter Groups

```python
# Create custom parameter group
rds.create_db_parameter_group(
    DBParameterGroupName='custom-postgres-params',
    DBParameterGroupFamily='postgres15',
    Description='Custom parameters for production'
)

# Modify parameters
rds.modify_db_parameter_group(
    DBParameterGroupName='custom-postgres-params',
    Parameters=[
        {
            'ParameterName': 'shared_buffers',
            'ParameterValue': '262144',  # 2GB
            'ApplyMethod': 'pending-reboot'
        }
    ]
)

# Apply custom parameter group
rds.modify_db_instance(
    DBInstanceIdentifier='my-postgres-db',
    DBParameterGroupName='custom-postgres-params',
    ApplyImmediately=False
)
```

### Events & Notifications

```python
# Subscribe to RDS events
sns = boto3.client('sns')

rds.create_event_subscription(
    SubscriptionName='my-db-events',
    SnsTopicArn='arn:aws:sns:us-east-1:123456789:my-topic',
    SourceType='db-instance',
    EventCategories=['availability', 'failure', 'maintenance']
)

# Events include: failover, backup completion, maintenance start/end
```

### Custom Endpoints (Aurora)

```python
# Create custom endpoint for analytics (read-only)
rds.create_db_cluster_endpoint(
    DBClusterIdentifier='my-aurora-cluster',
    DBClusterEndpointIdentifier='analytics-endpoint',
    EndpointType='READER',
    StaticMembers=['aurora-instance-1']
)

# Application routes analytics queries to analytics-endpoint
```

### Global Database (Multi-Region)

```python
# Create global database
rds.create_db_global_cluster(
    GlobalClusterIdentifier='my-global-db',
    Engine='aurora-postgresql'
)

# Add region (asynchronous replication with ~1s lag)
rds.create_db_instance(
    DBInstanceIdentifier='my-instance-eu',
    engine='aurora-postgresql',
    GlobalClusterIdentifier='my-global-db'
)
```

---

## Summary: RDS Decision Tree

```
┌─ Do you need a relational database?
│  └─ N: Use DynamoDB, Elasticsearch, etc.
│  └─ Y: Continue...
│
├─ High availability required?
│  └─ N: Single-AZ (dev/test cheaper)
│  └─ Y: Multi-AZ + backups + read replicas
│
├─ Extreme performance needed?
│  └─ N: Standard RDS (PostgreSQL/MySQL)
│  └─ Y: Aurora (5x faster MySQL, 3x faster PostgreSQL)
│
├─ Serverless (auto-scaling) needed?
│  └─ N: Provisioned instance
│  └─ Y: Aurora Serverless v2
│
├─ Read-heavy workload?
│  └─ N: Primary only
│  └─ Y: Add read replicas
│
└─ Global distribution needed?
   └─ N: Single region
   └─ Y: Aurora Global Database
```

---

## Resources

- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [RDS Pricing Calculator](https://calculator.aws/)
- [RDS Best Practices Whitepaper](https://aws.amazon.com/rds/best-practices/)
