# AWS Redshift (Data Warehouse)

**Python boto3 code:** [redshift_operations.py](./redshift_operations.py)

---

## Table of Contents

1. [What is AWS Redshift?](#1-what-is-aws-redshift)
2. [Redshift vs Other Data Solutions](#2-redshift-vs-other-data-solutions)
3. [Redshift Architecture & Components](#3-redshift-architecture--components)
4. [Cluster Creation & Configuration](#4-cluster-creation--configuration)
5. [Node Types & Scaling](#5-node-types--scaling)
6. [Data Loading (ETL)](#6-data-loading-etl)
7. [Query Execution & Performance](#7-query-execution--performance)
8. [Redshift Spectrum](#8-redshift-spectrum)
9. [Workload Management (WLM)](#9-workload-management-wlm)
10. [Security & Encryption](#10-security--encryption)
11. [Backup & Disaster Recovery](#11-backup--disaster-recovery)
12. [Monitoring & Performance Tuning](#12-monitoring--performance-tuning)
13. [Cost Optimization](#13-cost-optimization)
14. [RA3 Nodes (Advanced)](#14-ra3-nodes-advanced)
15. [Redshift Concurrency Scaling](#15-redshift-concurrency-scaling)
16. [Advanced Querying & Materialized Views](#16-advanced-querying--materialized-views)
17. [Federated Queries (Amazon Redshift Data API)](#17-federated-queries-amazon-redshift-data-api)
18. [Integration with Other AWS Services](#18-integration-with-other-aws-services)
19. [CLI Cheat Sheet](#19-cli-cheat-sheet)
20. [Best Practices](#20-best-practices)

---

## 1. What is AWS Redshift?

**AWS Redshift** is a fully managed, petabyte-scale data warehouse service designed for high-performance analytics. It uses columnar storage, compression, and query optimization to process large datasets efficiently.

### Key Characteristics

- **Fully Managed** - AWS handles patching, backups, replication, and upgrades
- **Petabyte Scale** - Process hundreds of terabytes of data
- **Columnar Storage** - Highly compressed, optimized for analytical queries (not OLTP)
- **SQL-Based** - PostgreSQL-compatible SQL dialect
- **Cost-Effective** - Pay only for compute/storage used; reserved node options for savings
- **High Performance** - Distributed query engine with parallel processing
- **Scalable** - Add/remove nodes without downtime
- **Security** - Encryption, IAM, VPC, SSL/TLS, column-level access control

### When to Use Redshift

| Use Case | Why Redshift Fits |
|----------|-------------------|
| Data Warehousing | Large-scale analytical queries (100GB to 100TB+) |
| Business Intelligence | BI tools (Tableau, Looker, PowerBI) integration |
| Data Lakes | Query petabytes of structured/semi-structured data via Spectrum |
| Historical Analysis | Time-series, trend analysis on large datasets |
| Ad-hoc Analytics | SQL-based exploration with high performance |
| Compliance & Auditing | Historical data analysis for compliance reporting |

### When NOT to Use Redshift

❌ OLTP (Online Transaction Processing) - Use RDS instead
❌ Real-time sub-millisecond queries - High latency (seconds)
❌ Small datasets (<1GB) - Over-engineered; use Athena or RDS
❌ Single-row reads - Not optimized for point lookups

---

## 2. Redshift vs Other Data Solutions

| Aspect | **Redshift** | **Athena** | **RDS** | **DynamoDB** |
|--------|-------------|-----------|---------|--------------|
| **Data Volume** | 100GB - 100TB+ | TB to PB (on S3) | 1GB - 100GB | Limited |
| **Query Type** | Analytics (OLAP) | Serverless analytics | Transactions (OLTP) | NoSQL queries |
| **Query Speed** | Seconds | Varies (cold start) | Milliseconds | Milliseconds |
| **Storage** | Managed cluster | S3 (external) | Local storage | DynamoDB |
| **Cost Model** | Hourly nodes/RI | Per-TB scanned | Per-month or on-demand | Per-request |
| **Scaling** | Manual/Aurora | Automatic (query-based) | Manual/vertical | Automatic |
| **Schema** | Strict relational | Flexible (Parquet, CSV) | Strict relational | Flexible JSON |
| **Best For** | Data warehouse | Ad-hoc S3 queries | Production databases | Real-time apps |

---

## 3. Redshift Architecture & Components

### Cluster Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    REDSHIFT CLUSTER                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Leader Node │  │  Compute Node│  │ Compute Node │       │
│  │              │  │              │  │              │       │
│  │ - Query plan │  │ - Executes   │  │ - Executes   │       │
│  │ - Metadata   │  │ - Local disk │  │ - Local disk │       │
│  │ - Aggregate  │  │ - Processes  │  │ - Processes  │       │
│  │   results    │  │   data slice │  │   data slice │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│        |                 |                  |               │
│        └─────────────────┴──────────────────┘               │
│              Internal Network (10 Gbps)                      │
│                                                               │
└───────────────────────────────────────────────────────────────┘
         ↓
    ┌─────────────────┐
    │  S3 / Redshift  │
    │    Spectrum     │
    └─────────────────┘
```

### Key Components

**Leader Node**
- Receives SQL queries from clients
- Creates query execution plan
- Distributes queries to compute nodes
- Aggregates results
- Does NOT store data

**Compute Nodes**
- Execute portions of the query in parallel
- Store and process data slices (partitions)
- Share results back to leader node

**Shared State**
- PostgreSQL-compatible metadata
- Table schemas and statistics
- Query history

---

## 4. Cluster Creation & Configuration

### Cluster Configuration Hierarchy

```
Cluster Type
├── Single-Node (Dev/Test only)
│   └── 1 Leader node (no compute nodes)
│   └── Limited to dense storage
│
└── Multi-Node (Production)
    ├── 1 Leader + 2-200 Compute Nodes
    ├── Node types: RA3, DC2, RA3-Plus
    └── Distributed processing & High availability
```

### Node Types

```
RA3 (Latest - Recommended for New Deployments)
├── RA3.XPlus (32 vCPU, 128GB RAM, 32TB managed storage)
├── RA3.4XL (128 vCPU, 512GB RAM, 128TB managed storage)
└── RA3.16XL (128 vCPU, 512GB RAM, 128TB managed storage)
└── Features: Separates compute/storage, S3 integration, lower cost

DC2 (Dense Compute - Previous Gen, High-performance)
├── DC2.Large (2 vCPU, 16GB RAM, 160GB SSD)
└── DC2.8XLarge (32 vCPU, 256GB RAM, 2560GB SSD)
└── Features: Local storage, high IO, used for smaller hot data

RA3-Plus (Enhanced RA3)
├── Similar to RA3 but with enhanced capabilities
└── Automatic query acceleration
```

### Creating a Cluster (AWS Console)

```
1. Redshift Dashboard → Create Cluster
2. Configure:
   - Cluster Identifier (e.g., analytics-warehouse)
   - Node Type (RA3.4XL recommended)
   - Number of Nodes (e.g., 2-5 minimum for production)
   - Database Name (defaults to "dev")
   - Master Username (e.g., admin)
   - Master Password (strong password)
3. Network & Security:
   - VPC, Subnets, Security Groups
   - Enhanced VPC Routing (encrypts data in transit)
4. Backup Configuration:
   - Backup Retention Period (1-35 days default)
   - Preferred Maintenance Window
5. Encryption:
   - Enable AWS KMS encryption
6. Monitoring:
   - Enable CloudWatch metrics
   - Enable enhanced monitoring
7. Review & Create
```

### Cluster Creation (CLI)

```bash
aws redshift create-cluster \
  --cluster-identifier analytics-warehouse \
  --node-type ra3.4xl \
  --number-of-nodes 2 \
  --master-username admin \
  --master-account-password 'StrongPassword123!' \
  --db-name analytics \
  --port 5439 \
  --publicly-accessible false \
  --encrypted \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/12345678 \
  --region us-east-1
```

---

## 5. Node Types & Scaling

### Scaling Strategies

**Vertical Scaling** (Change node type)
- Resizes cluster nodes to larger/smaller types
- Results in brief downtime (~1 hour)
- Used when: Need more memory or compute per node

**Horizontal Scaling** (Add/remove nodes)
- Add compute nodes to existing cluster
- No downtime if using Concurrency Scaling
- Used when: Need more parallel processing power

**Elastic Resize** (Quick node addition)
- Add nodes in minutes (new feature)
- Some WLM queues pause briefly
- Best for: Temporary capacity needs

```bash
# Resize cluster (vertical scaling)
aws redshift modify-cluster \
  --cluster-identifier analytics-warehouse \
  --node-type dc2.8xlarge \
  --number-of-nodes 3

# Elastic resize (faster)
aws redshift resize-cluster \
  --cluster-identifier analytics-warehouse \
  --number-of-nodes 4 \
  --classic=false
```

### Capacity Planning

**Formula**
```
Cluster Storage = (Node Type Storage) × (Number of Nodes)
Cluster vCPU = (Node Type vCPU) × (Number of Compute Nodes)
```

**Example: RA3.4XL with 3 nodes**
```
Total Storage: 128TB × 3 = 384TB
Total vCPU: 128 vCPU × 3 = 384 vCPU (leader doesn't count)
```

---

## 6. Data Loading (ETL)

### Data Loading Methods

| Method | Throughput | Latency | Best For |
|--------|-----------|---------|----------|
| **COPY command** | Highest (MB/s) | Minutes | Batch ETL, large files |
| **Redshift Data API** | Medium | Seconds | Streaming apps, Lambda |
| **UNLOAD + external tables** | High | Minutes | Multi-format data |
| **AWS Glue** | Medium | Minutes | Complex transformations |
| **Amazon AppFlow** | Low-Medium | Minutes | SaaS integrations |

### COPY Command (Most Common)

```sql
COPY table_name
FROM 's3://bucket-name/prefix/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
FORMAT AS PARQUET
DELIMITER ','
IGNOREHEADER 1
NULL AS 'N/A'
DATEFORMAT 'YYYY-MM-DD'
;
```

**COPY from S3 with Manifest**
```sql
COPY orders
FROM 's3://my-data-bucket/orders-manifest.json'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
MANIFEST
DELIMITER ','
;
```

**Monitoring COPY Progress**
```sql
SELECT * FROM stl_load_errors
WHERE query LIKE '%orders%'
ORDER BY starttime DESC
LIMIT 10;
```

### UNLOAD Command (Export Data)

```sql
UNLOAD (
    SELECT * FROM sales
    WHERE year = 2024
)
TO 's3://output-bucket/sales/2024/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
PARQUET
ENCRYPTED
;
```

### Redshift Data API (Lambda-Friendly)

```python
import boto3

client = boto3.client('redshift-data', region_name='us-east-1')

response = client.execute_statement(
    ClusterIdentifier='analytics-warehouse',
    Database='analytics',
    SecretArn='arn:aws:secretsmanager:us-east-1:123456789:secret:redshift-creds',
    Sql='SELECT COUNT(*) FROM orders WHERE year = 2024;'
)

statement_id = response['Id']

# Check status
status = client.describe_statement(Id=statement_id)
print(f"Status: {status['Status']}")  # SUBMITTED, PICKED, STARTED, FINISHED, FAILED

# Get results
if status['Status'] == 'FINISHED':
    results = client.get_statement_result(Id=statement_id)
    print(results['Records'])
```

---

## 7. Query Execution & Performance

### Query Optimization

**1. Column Selection** (Avoid SELECT *)
```sql
-- ❌ Bad: Reads all columns
SELECT * FROM sales WHERE year = 2024;

-- ✅ Good: Columnar storage reads only needed columns
SELECT order_id, customer_id, amount FROM sales WHERE year = 2024;
```

**2. Data Types Matter**
```sql
-- Columnar storage compression depends on data type
-- In Redshift, use most efficient types:

-- ❌ Inefficient
CREATE TABLE sales (
    order_id VARCHAR(100),  -- Wastes space
    amount VARCHAR(20),     -- Should be numeric
    order_date VARCHAR(10)  -- Should be DATE
);

-- ✅ Efficient
CREATE TABLE sales (
    order_id INTEGER,
    amount DECIMAL(10,2),
    order_date DATE
);
```

**3. Distribution Keys** (Co-locate related data)
```sql
-- Queries with JOIN on order_id should distribute by this key
CREATE TABLE orders (
    order_id INTEGER,
    customer_id INTEGER,
    amount DECIMAL(10,2)
)
DISTKEY (order_id);

CREATE TABLE order_items (
    order_item_id INTEGER,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)
DISTKEY (order_id);

-- Now JOIN on order_id happens locally (no network shuffle)
SELECT o.order_id, SUM(oi.quantity)
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id;
```

**4. Sort Keys** (Pre-sort for range queries)
```sql
-- If often queried by date ranges:
CREATE TABLE transactions (
    transaction_id INTEGER,
    customer_id INTEGER,
    transaction_date DATE,
    amount DECIMAL(10,2)
)
DISTKEY (customer_id)
SORTKEY (transaction_date);  -- Pre-sorted; range queries are fast

-- Fast: Redshift uses sort order
SELECT * FROM transactions
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-01-31';
```

**5. Query Explain & Analysis**
```sql
-- View query execution plan
EXPLAIN
SELECT customer_id, SUM(amount)
FROM sales
WHERE year = 2024
GROUP BY customer_id;

-- Detailed query metrics
SELECT * FROM stl_query
WHERE query = 123456
LIMIT 1;
```

### Common Performance Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Uneven data distribution | Slow nodes lag | Check DISTKEY; rebalance data |
| Too many small files on S3 | Slow COPY | Combine files; use MANIFEST |
| SELECT * queries | High memory usage | Specify columns needed |
| Missing sort keys | Slow range queries | Add SORTKEY on filter columns |
| No statistics | Bad query plan | ANALYZE table; UPDATE STATISTICS |

---

## 8. Redshift Spectrum

### What is Redshift Spectrum?

Query data in S3 **without loading it** into Redshift cluster. External tables point to S3 data (Parquet, ORC, CSV, JSON).

### Use Cases
- Query append-only logs in S3 (massive datasets)
- Join S3 data with Redshift tables
- Ad-hoc analysis on raw data without ETL
- Cost savings: Pay only for compute; S3 storage is cheaper

### Creating External Schema

```sql
-- Create external schema (catalog/database in S3)
CREATE EXTERNAL SCHEMA spectrum_schema
FROM DATA CATALOG
DATABASE 'spectrum_db'
IAM_ROLE 'arn:aws:iam::123456789:role/SpectrumRole'
;

-- Create external table (points to S3)
CREATE EXTERNAL TABLE spectrum_schema.raw_logs (
    log_id INTEGER,
    timestamp TIMESTAMP,
    event VARCHAR(256),
    user_id INTEGER,
    properties VARCHAR(MAX)
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION 's3://my-logs-bucket/raw/'
;

-- Query S3 data (joins with regular tables)
SELECT
    l.user_id,
    COUNT(*) event_count
FROM spectrum_schema.raw_logs l
WHERE l.year = 2024 AND l.month = 3
GROUP BY l.user_id
;
```

### Partitioning External Tables

```sql
-- Add partitions (faster queries)
ALTER TABLE spectrum_schema.raw_logs
ADD PARTITION (year=2024, month=3, day=15)
LOCATION 's3://my-logs-bucket/raw/2024/03/15/';

-- Query only 1 day's data (not entire S3 folder)
SELECT * FROM spectrum_schema.raw_logs
WHERE year = 2024 AND month = 3 AND day = 15;
```

---

## 9. Workload Management (WLM)

### What is WLM?

Manages query queues, memory allocation, and concurrency. Ensures high-priority queries get resources; delays low-priority queries.

### WLM Configuration

```sql
-- View current WLM configuration
SELECT * FROM stl_wlm_config;

-- Create WLM queue configuration (Console or CLI)
-- Queue 1: High-priority (BI dashboards)
-- Queue 2: Medium-priority (Data scientists)
-- Queue 3: Low-priority (Batch jobs)

-- Example queue settings:
-- Queue 1: 40% memory, 1 concurrent query, timeout 30 min
-- Queue 2: 30% memory, 5 concurrent queries, timeout 60 min
-- Queue 3: 30% memory, 10 concurrent queries, timeout 180 min
```

### Running Query in Specific Queue

```sql
-- Set query group (routes to specific queue)
SET query_group TO 'high_priority';
SELECT * FROM large_table LIMIT 1000;

-- Return to default queue
RESET query_group;
```

### Monitoring Queue Performance

```sql
SELECT queue, run_minutes, query_count, avg_run_minutes
FROM stl_wlm_query
WHERE date > CURRENT_DATE - 1
GROUP BY queue
ORDER BY queue;
```

---

## 10. Security & Encryption

### Network Security

**VPC Configuration**
```
✅ Deploy cluster in private VPC (no public access)
✅ Use security groups to restrict inbound traffic (port 5439)
✅ Enable Enhanced VPC Routing (encrypts inter-node traffic)
```

**SSL/TLS Encryption**
```bash
# Connect with SSL
psql -h <cluster-endpoint>.redshift.amazonaws.com \
  -U admin \
  -d analytics \
  -p 5439 \
  --set=sslmode=require
```

### Encryption at Rest

```bash
# Enable KMS encryption for cluster
aws redshift create-cluster \
  --cluster-identifier secure-warehouse \
  --encrypted \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/12345
```

### IAM Authentication

```sql
-- Create Redshift user linked to IAM
CREATE USER iam_user WITH PASSWORD DISABLE;

-- Grant permissions
GRANT SELECT ON TABLE sales TO iam_user;
GRANT CREATE ON SCHEMA public TO iam_user;
```

**Connect via IAM**
```bash
# Generate temporary credentials (valid 15 minutes)
aws redshift-data get-cluster-credentials \
  --cluster-identifier analytics-warehouse \
  --db-user iam_admin

# Use token in connection string
```

### Column-Level Access Control

```sql
-- Only specific users see sensitive columns
CREATE TABLE customers (
    customer_id INTEGER,
    name VARCHAR(256),
    email VARCHAR(256),
    ssn VARCHAR(11)  -- Sensitive
);

-- Create masked view for regular users
CREATE OR REPLACE VIEW customers_public AS
SELECT customer_id, name, email FROM customers;

-- Grant access only to view (not table)
GRANT SELECT ON customers_public TO analytics_users;
REVOKE SELECT ON customers FROM analytics_users;
```

---

## 11. Backup & Disaster Recovery

### Automated Backups

```bash
# Modify backup retention
aws redshift modify-cluster \
  --cluster-identifier analytics-warehouse \
  --backup-retention-period 35 \
  --preferred-backup-window "03:00-04:00"
```

### Manual Snapshots

```bash
# Create manual snapshot
aws redshift create-cluster-snapshot \
  --cluster-identifier analytics-warehouse \
  --snapshot-identifier prod-snapshot-2024-03-31

# List snapshots
aws redshift describe-cluster-snapshots

# Restore from snapshot
aws redshift restore-from-cluster-snapshot \
  --cluster-identifier restored-warehouse \
  --snapshot-identifier prod-snapshot-2024-03-31
```

### Cross-Region Disaster Recovery

```bash
# Copy snapshot to another region
aws redshift copy-cluster-snapshot \
  --source-cluster-snapshot-identifier prod-snapshot-2024-03-31 \
  --target-cluster-snapshot-identifier prod-snapshot-dr \
  --source-region us-east-1 \
  --target-region us-west-2
```

---

## 12. Monitoring & Performance Tuning

### Key Metrics

**CPU Utilization**
```sql
SELECT * FROM stl_alert_event_log
WHERE event_time > NOW() - INTERVAL '24 hours'
ORDER BY event_time DESC;
```

**Query Performance**
```sql
SELECT
    query,
    userid,
    starttime,
    endtime,
    DATEDIFF(seconds, starttime, endtime) duration_seconds,
    querytxt
FROM stl_query
WHERE query > 0
ORDER BY starttime DESC
LIMIT 20;
```

**Disk Usage**
```sql
SELECT
    schema,
    table_id,
    size_in_megabytes
FROM svv_table_info
ORDER BY size_in_megabytes DESC
LIMIT 10;
```

**Slow Queries**
```sql
SELECT
    query,
    userid,
    DATEDIFF(seconds, starttime, endtime) duration,
    querytxt
FROM stl_query
WHERE DATEDIFF(seconds, starttime, endtime) > 300  -- >5 mins
ORDER BY starttime DESC
LIMIT 20;
```

### CloudWatch Monitoring

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Get CPU utilization
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Redshift',
    MetricName='CPUUtilization',
    Dimensions=[
        {'Name': 'ClusterIdentifier', 'Value': 'analytics-warehouse'}
    ],
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=300,
    Statistics=['Average', 'Maximum']
)

for point in response['Datapoints']:
    print(f"{point['Timestamp']}: {point['Average']}% avg, {point['Maximum']}% max")
```

---

## 13. Cost Optimization

### Reserved Nodes

```bash
# Purchase reserved capacity (1 or 3 years)
# 40-50% savings vs on-demand

aws redshift purchase-reserved-node-offering \
  --reserved-node-offering-id 12345 \
  --node-count 2
```

### Pricing Models

| Model | Cost | Best For |
|-------|------|----------|
| **On-Demand** | ~$1.26/hour per DC2.Large | Testing, variable usage |
| **Reserved (1-year)** | ~$0.68/hour (46% off) | Stable, predictable load |
| **Reserved (3-year)** | ~$0.54/hour (57% off) | Long-term warehouse |

### Cost Reduction Strategies

**1. Table Compression**
```bash
# Analyze compression opportunities
ANALYZE COMPRESSION <table_name>;

# Results show potential space savings
```

**2. Vacuum & Analyze**
```sql
-- Remove deleted rows, re-sort, update statistics
VACUUM sales;
ANALYZE sales;
```

**3. Archive Cold Data**
```sql
-- UNLOAD old data to S3 (cheap storage)
UNLOAD (
    SELECT * FROM sales
    WHERE year < 2023
)
TO 's3://archive-bucket/sales-archive/'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
;

-- DELETE from main table
DELETE FROM sales WHERE year < 2023;
```

**4. Right-Size Your Cluster**
- Monitor actual usage; don't over-provision
- Use RA3 for flexibility (scales storage independently)

---

## 14. RA3 Nodes (Advanced)

### Advantages of RA3

- **Compute/Storage Separation** - Scale independently
- **Lower Cost** - Pay for storage in Redshift Managed Storage (RMS), not node storage
- **Query Acceleration** - Hardware-accelerated query engine
- **S3 Integration** - Seamless spillover to S3

### RA3 Architecture

```
┌──────────────────────┐
│  Query Engine        │
│  (Compute - RA3      │
│   nodes only)        │
└──────────────────────┘
         ↓
┌──────────────────────┐
│ Redshift Managed     │
│ Storage (RMS)        │
│ On-node cache        │
└──────────────────────┘
         ↓
┌──────────────────────┐
│ S3 (Managed Layer)   │
│ (Storage spillover)  │
└──────────────────────┘
```

### RMS (Redshift Managed Storage)

```bash
# Monitor RMS usage
SELECT * FROM stl_rms_stats WHERE query_id = 123;

# Check managed storage percentage
SELECT
    schema,
    COUNT(*) tables,
    SUM(size_in_megabytes) total_mb
FROM svv_table_info
GROUP BY schema;
```

---

## 15. Redshift Concurrency Scaling

### What is Concurrency Scaling?

Automatically adds compute nodes when query queue depth exceeds threshold. Scales down when no longer needed. You only pay per second for additional nodes (1-minute minimum).

### Enabling Concurrency Scaling

```bash
aws redshift modify-cluster \
  --cluster-identifier analytics-warehouse \
  --enable-concurrency-scaling
```

### Configuration

```sql
-- Set concurrency scaling queue
SET wlm_query_slot_count=2;
SELECT * FROM large_table;
```

### Cost

```
Cost = $0.375 per node per hour (DC2.Large)
If you add 2 nodes for 15 minutes: $0.375 × 2 × 0.25 = $0.1875
```

---

## 16. Advanced Querying & Materialized Views

### Materialized Views (Pre-computed Results)

```sql
-- Create materialized view (stores results as table)
CREATE MATERIALIZED VIEW sales_summary AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    product_category,
    COUNT(*) order_count,
    SUM(amount) total_amount,
    AVG(amount) avg_amount
FROM orders
GROUP BY 1, 2;

-- Query materialized view (instant results)
SELECT * FROM sales_summary WHERE month >= '2024-01-01';

-- Refresh when source data changes
REFRESH MATERIALIZED VIEW sales_summary;
```

### Window Functions for Analytics

```sql
-- Running total
SELECT
    order_date,
    amount,
    SUM(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) running_total
FROM sales;

-- Rank products by sales
SELECT
    product_name,
    SUM(amount) total_sales,
    ROW_NUMBER() OVER (ORDER BY SUM(amount) DESC) rank
FROM sales
GROUP BY product_name;
```

### Common Table Expressions (CTEs)

```sql
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(amount) total_sales
    FROM orders
    GROUP BY 1
)
SELECT
    month,
    total_sales,
    AVG(total_sales) OVER () avg_monthly_sales,
    total_sales - AVG(total_sales) OVER () variance
FROM monthly_sales;
```

---

## 17. Federated Queries (Amazon Redshift Data API)

### Query External Databases

```sql
-- Create external connection (RDS, Aurora, etc.)
CREATE EXTERNAL DATABASE external_rds
DBNAME 'production_db'
HOST 'prod-db.c9akciq32.us-east-1.rds.amazonaws.com'
PORT 5432
REGION 'us-east-1'
SECRET_ARN 'arn:aws:secretsmanager:us-east-1:123456789:secret:rds-creds'
IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
;

-- Query external database
SELECT * FROM external_rds.public.customers LIMIT 10;

-- Join Redshift and external data
SELECT
    r.customer_id,
    r.total_orders,
    e.subscription_tier
FROM redshift_customers r
JOIN external_rds.public.customers e
    ON r.customer_id = e.id;
```

---

## 18. Integration with Other AWS Services

### AWS Glue (ETL)

```python
# AWS Glue job for Redshift loading
import sys
from awsglue.transforms import *
from awsglue.job import Job

job = Job(glueContext)

# Load from S3
dyf = glueContext.create_dynamic_frame.from_options(
    format_options={"multiline": False},
    connection_type="s3",
    format="json",
    connection_options={"paths": ["s3://my-bucket/data/"]},
)

# Write to Redshift
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="redshift",
    connection_options={
        "redshiftTmpDir": "s3://redshift-temp-bucket/",
        "useConnectionProperties": "true",
        "dbtable": "public.sales",
        "connectionName": "redshift-connection"
    },
    format="parquet"
)

job.commit()
```

### Amazon Athena + Redshift Spectrum

Query S3 from Redshift when Athena data format matches (Parquet, ORC).

### QuickSight Dashboards

```
1. QuickSight → Create Data Set → Redshift
2. Select cluster, database, table
3. Create visualizations
4. Share dashboards
```

### EventBridge + Lambda → Redshift

```python
import json
import psycopg2

def lambda_handler(event, context):
    # Event triggered by S3 upload
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']

    # Execute Redshift copy
    conn = psycopg2.connect(
        host="analytics-warehouse.redshift.amazonaws.com",
        port=5439,
        user="admin",
        password="password",
        database="analytics"
    )

    cursor = conn.cursor()
    cursor.execute(f"""
        COPY raw_data FROM 's3://{bucket}/{key}'
        IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
        PARQUET;
    """)
    conn.commit()
    cursor.close()

    return {'statusCode': 200, 'body': 'Data loaded'}
```

---

## 19. CLI Cheat Sheet

```bash
# Create cluster
aws redshift create-cluster \
  --cluster-identifier my-warehouse \
  --node-type ra3.4xl \
  --number-of-nodes 2

# List clusters
aws redshift describe-clusters

# Get cluster endpoint
aws redshift describe-clusters \
  --cluster-identifier my-warehouse \
  --query 'Clusters[0].Endpoint'

# Modify cluster
aws redshift modify-cluster \
  --cluster-identifier my-warehouse \
  --number-of-nodes 3

# Create snapshot
aws redshift create-cluster-snapshot \
  --cluster-identifier my-warehouse \
  --snapshot-identifier backup-2024

# Delete cluster
aws redshift delete-cluster \
  --cluster-identifier my-warehouse \
  --skip-final-cluster-snapshot

# Get cluster status
aws redshift describe-clusters \
  --cluster-identifier my-warehouse \
  --query 'Clusters[0].ClusterStatus'

# Authorize Security Group Ingress
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 5439 \
  --cidr 10.0.0.0/8
```

---

## 20. Best Practices

### Design Best Practices

✅ **Do:**
- Use appropriate distribution keys for JOIN performance
- Implement sort keys on frequently filtered columns
- Maintain table statistics (ANALYZE regularly)
- Compress data appropriately
- Archive historical data to S3
- Use columnar formats (Parquet/ORC) for S3 data

❌ **Don't:**
- SELECT * (specify columns needed)
- Use VARCHAR(MAX) for all text fields
- Skip VACUUM and ANALYZE jobs
- Over-provision cluster nodes
- Store logs or transactional data (use RDS instead)

### Query Best Practices

✅ **Do:**
- Use WHERE clauses to filter early
- Join on distribution keys
- Aggregate before JOIN when possible
- Leverage temp tables for complex queries
- Use UNLOAD for large result sets to S3

❌ **Don't:**
- Perform complex calculations on every row
- Use correlated subqueries
- Create many temporary tables in a session
- Run heavy analytical queries during peak hours

### Security Best Practices

✅ **Do:**
- Enable encryption at rest and in transit
- Use IAM authentication
- Deploy in private VPC
- Enable Enhanced VPC Routing
- Monitor query logs for suspicious activity
- Use Secrets Manager for credentials

❌ **Don't:**
- Store passwords in code or config files
- Publicly expose cluster endpoint
- Grant unnecessary permissions
- Disable encryption
- Use default database names/users

### Maintenance Best Practices

✅ **Do:**
- Regularly VACUUM and ANALYZE tables
- Monitor disk usage and CPU
- Create automated daily snapshots
- Test restore procedures quarterly
- Monitor WLM queue performance
- Set up CloudWatch alarms

❌ **Don't:**
- Ignore long-running queries
- Allow bloated tables (unvacuumed)
- Skip backup testing
- Ignore CloudWatch metrics
- Run heavy jobs during peak hours

---

## Summary

Redshift is a powerful data warehouse for analytics at scale. It combines:
- **SQL-based interface** (PostgreSQL compatible)
- **Columnar storage** (highly compressed)
- **Distributed computing** (parallel query execution)
- **Petabyte scalability** (grow as needed)
- **Cost-effectiveness** (RA3 separates compute/storage)

Master **DISTKEY**, **SORTKEY**, query optimization, and WLM to get the most from Redshift.
