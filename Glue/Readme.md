# AWS Glue

## Table of Contents
1. [AWS Glue Fundamentals](#aws-glue-fundamentals)
2. [Key Concepts](#key-concepts)
3. [Glue Components](#glue-components)
4. [Glue Crawlers](#glue-crawlers)
5. [Glue Jobs](#glue-jobs)
6. [Data Catalog](#data-catalog)
7. [Transforms and ETL](#transforms-and-etl)
8. [Development Setup](#development-setup)
9. [IAM and Security](#iam-and-security)
10. [Scaling and Performance](#scaling-and-performance)
11. [Monitoring and Debugging](#monitoring-and-debugging)
12. [Cost Optimization](#cost-optimization)
13. [Integration Patterns](#integration-patterns)
14. [Real-World Examples](#real-world-examples)
15. [Best Practices](#best-practices)

---

## AWS Glue Fundamentals

### What is AWS Glue?

AWS Glue is a fully managed **Extract, Transform, Load (ETL)** service that makes it simple and cost-effective to categorize, clean, enrich, and move data reliably between different data stores.

**Key Capabilities:**
- Automated schema discovery via crawlers
- Serverless job execution (Spark, Python Shell, Ray)
- Built-in data catalog for metadata management
- Supports 70+ data sources
- Integration with other AWS services (S3, RDS, Redshift, DynamoDB, etc.)
- Pay-per-DPU (Data Processing Unit) pricing for jobs

### When to Use Glue

✅ **Use Glue for:**
- Building data pipelines (ELT/ETL)
- Data integration from multiple sources
- Schema discovery and metadata management
- Data preparation for analytics
- Recurring data transformation tasks
- Data warehouse/lake population
- Data quality and enrichment

❌ **Don't use Glue for:**
- Real-time streaming (use Kinesis Data Streams or Flink)
- Simple data downloads (use S3 direct access)
- Minimal transformations (use Lambda)
- Complex ML workflows (use SageMaker)

### Glue vs Other AWS Services

| Service | Use Case |
|---------|----------|
| **Glue** | Batch ETL, schema discovery, data catalog |
| **Lambda** | Simple transformations, event-driven processing |
| **EMR** | Complex Hadoop/Spark jobs, when you need full control |
| **Data Pipeline** | Legacy scheduling (deprecated) |
| **SageMaker** | ML-focused transformations |
| **Kinesis** | Real-time streaming data |

---

## Key Concepts

### DPU (Data Processing Unit)

DPU is the unit of computation in Glue:
- **1 DPU** = 4vCPU + 16GB RAM
- **Standard worker**: processes heavy compute/memory workloads
- **G.2X worker**: optimized for GPU workloads
- Billed per second (minimum 10 minutes per job run)

### Glue Version

Glue supports different runtime versions:
- **Glue 3.0+**: Latest with Spark 3.x, better performance
- **Glue 2.0**: Spark 2.4
- **Glue 1.0**: Legacy (deprecating)

### Job Bookmarks

Track state between job runs to process only new data:
```python
# Job bookmark automatically tracks:
- Last processed file offset
- Last processed partition
- Last processed record
```

**Types:**
- **Enabled**: Tracks state, processes only new data
- **Disabled**: Processes all data every run
- **Job run cleanup**: Resets bookmark state

---

## Glue Components

### 1. Glue Crawlers

Automatic schema discovery from data stores.

**What Crawlers Do:**
- Connect to data sources (S3, RDS, JDBC, etc.)
- Scan data and infer schema
- Create/update metadata in Glue Data Catalog
- Run on schedule or on-demand

**Crawler Configuration:**

```yaml
Name: my-crawler
Role: AWSGlueServiceRole
Database: my_database
S3Path: s3://my-bucket/data/
DataFormat: Parquet, CSV, JSON
SchemaChangePolicy:
  UpdateBehavior: UPDATE_IN_DATABASE
  DeleteBehavior: LEGACY
Schedule: cron(0 8 * * ? *)  # Daily at 8 AM
```

**Crawler Output:**
- Creates/updates tables in Glue Catalog
- Generates column definitions
- Detects partitions
- Updates table statistics

**Best Practices:**
- Use path excludes to skip logs/backups
- Set appropriate batch size for large datasets
- Handle schema changes with policies
- Schedule crawlers strategically (after data loads)

### 2. Glue Data Catalog

Centralized metadata repository for all data sources.

**What's Stored:**
- Database schemas
- Table definitions
- Column metadata and types
- Partitions and locations
- Connection strings

**Integration Points:**
```
Data Catalog ← Crawlers ← Data Sources
         ↓
    Glue Jobs → Query with Athena/Redshift Spectrum
         ↓
    Lake Formation → Access Control
```

**Database & Table Hierarchy:**
```
Database
├── Table 1
│   ├── Column 1: String
│   ├── Column 2: Integer
│   └── Partition Keys: year/month/day
├── Table 2
└── Table 3
```

### 3. Glue Jobs

Execute ETL code in a managed, serverless environment.

**Job Types:**

| Type | Language | Best For |
|------|----------|----------|
| **Spark** | Python/Scala | Distributed processing, large datasets |
| **Python Shell** | Python | Simple ETL, no Spark needed |
| **Ray** | Python | ML pipelines, parallel processing |
| **Streaming** | Python/Scala | Continuous data processing |

---

## Glue Crawlers

### Creating Crawlers

**Console Approach:**
1. Go to AWS Glue → Crawlers
2. Click "Create crawler"
3. Configure:
   - Data source (S3, RDS, JDBC, etc.)
   - IAM role
   - Target database
   - Output table name
   - Schema change policy
4. Schedule or run on demand

**CloudFormation:**

```yaml
Resources:
  MyGlueCrawler:
    Type: AWS::Glue::Crawler
    Properties:
      Name: my-crawler
      Role: !GetAtt GlueServiceRole.Arn
      DatabaseName: my_database
      SchemaChangePolicy:
        UpdateBehavior: UPDATE_IN_DATABASE
        DeleteBehavior: LOG
      Targets:
        S3Targets:
          - Path: s3://my-bucket/data/
            Exclusions:
              - "*.log"
              - "*/temp/*"
      TablePrefix: crawler_
      SchemaChangePolicy:
        UpdateBehavior: UPDATE_IN_DATABASE
        DeleteBehavior: LOG
      Schedule:
        ScheduleExpression: cron(0 8 * * ? *)
```

### Schema Change Policies

How Glue handles schema changes in crawlers:

**UpdateBehavior:**
- `UPDATE_IN_DATABASE` (default): Update existing tables
- `LOG`: Write changes to CloudWatch logs only

**DeleteBehavior:**
- `LEGACY`: Delete partitions and tables (old behavior)
- `LOG`: Write to CloudWatch logs
- `HIDE_COLUMNS`: Hide missing columns (recommended)
- `DELETE_FROM_DATABASE`: Delete tables/partitions

### Crawler Partitioning

Automatic partition discovery:

```python
# Crawler detects partitions from S3 path structure:
# s3://bucket/data/year=2024/month=03/day=15/

# Creates partition keys:
# year: 2024
# month: 03
# day: 15
```

**Partition Discovery Options:**
- Auto-detect from path
- Manual specification
- Custom grouping pattern

### Running Crawlers

**On-Demand:**
```bash
aws glue start-crawler --name my-crawler
```

**Scheduled:**
- Cron expressions supported
- Can run multiple times daily
- Backfill historical data

**Monitoring:**
```bash
aws glue get-crawler --name my-crawler
# Returns: state (READY, RUNNING, STOPPING)

aws glue get-crawler-metrics --crawler-name my-crawler
# Returns: tables created, updated, deleted
```

---

## Glue Jobs

### Creating Glue Jobs

**Spark Job Example** (Distributed Processing):

```yaml
Name: transform-sales-data
Type: Spark
GlueVersion: 3.0
Workers:
  NumberOfWorkers: 10
  WorkerType: G.2X
Timeout: 2880  # 48 hours
MaxRetries: 1
ExecutionProperty:
  MaxConcurrentRuns: 5
Parameters:
  job-bookmark-option: job-bookmark-enabled
  enable-spark-ui: true
  enable-glue-datacatalog: true
  enable-metrics: true
```

**Python Shell Job Example** (Simple Processing):

```yaml
Name: process-csv-files
Type: PythonShell
PythonVersion: 3.9
WorkerType: G.1X
NumberOfWorkers: 1
Timeout: 300
MaxRetries: 1
```

**Ray Job Example** (Parallel Processing):

```yaml
Name: ml-preprocessing
Type: Ray
GlueVersion: 4.0
WorkerType: Z.2X
NumberOfWorkers: 5
```

### Job Parameters

```python
# Access parameters in jobs:
import sys
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['output_path', 'database'])
output_path = args['output_path']
database = args['database']

# Command line parameters:
aws glue start-job-run \
  --job-name my-job \
  --arguments '{"--output_path":"s3://bucket/output/", "--database":"sales_db"}'
```

### Glue Job Monitoring

**CloudWatch Metrics:**
- ExecutionTime
- glue.driver.aggregate.numStages
- glue.driver.aggregate.numTasks
- glue.executor.*.jvm.heap.usage

**Job Bookmarks:**
```python
# Track processed data
import boto3

glue = boto3.client('glue')
response = glue.get_job_run(JobName='my-job', RunId='run-123')
print(response['JobRun']['JobRunState'])  # RUNNING, SUCCEEDED, FAILED
```

---

## Data Catalog

### Database Management

**Create Database:**

```python
import boto3

glue = boto3.client('glue')

glue.create_database(
    CatalogId='123456789012',
    DatabaseInput={
        'Name': 'sales_database',
        'Description': 'Sales and transaction data',
        'LocationUri': 's3://my-bucket/sales-data/',
        'Parameters': {
            'classification': 'parquet',
            'compressionType': 'snappy'
        }
    }
)
```

**List Databases:**

```python
response = glue.get_databases()
for db in response['DatabaseList']:
    print(f"{db['Name']}: {db['Description']}")
```

### Table Management

**Create Table:**

```python
glue.create_table(
    DatabaseName='sales_database',
    TableInput={
        'Name': 'customers',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'customer_id', 'Type': 'bigint'},
                {'Name': 'name', 'Type': 'string'},
                {'Name': 'email', 'Type': 'string'},
                {'Name': 'signup_date', 'Type': 'date'}
            ],
            'Location': 's3://my-bucket/customers/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTypeOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary':
                    'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                'Parameters': {'field.delim': ','}
            }
        },
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'int'},
            {'Name': 'month', 'Type': 'int'}
        ]
    }
)
```

**Query Tables:**

```python
# In Athena - use Glue Catalog:
SELECT * FROM sales_database.customers
WHERE year=2024 AND month=3

# Or in Glue Job:
glue_context = GlueContext(spark_context)
customers_df = glue_context.create_dynamic_frame.from_catalog(
    database='sales_database',
    table_name='customers'
).toDF()
```

### Partitions

**Add Partition:**

```python
glue.batch_create_partition(
    DatabaseName='sales_database',
    TableName='customers',
    PartitionInputList=[
        {
            'Values': ['2024', '03'],
            'StorageDescriptor': {
                'Columns': [...],
                'Location': 's3://my-bucket/customers/year=2024/month=03/',
                'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTypeOutputFormat',
                'SerdeInfo': {...}
            }
        }
    ]
)
```

**Query Partitions:**

```python
response = glue.get_partitions(
    DatabaseName='sales_database',
    TableName='customers',
    Expression='year=2024 AND month=3'
)
```

---

## Transforms and ETL

### AWS Glue Studio (Visual ETL)

**No-code/Low-code approach:**
1. Drag and drop sources, transforms, and targets
2. Visual mapping between fields
3. Auto-generated PySpark code
4. Real-time recommendations

**Transform Types:**
- **Apply mapping**: Rename, drop, reorder columns
- **Filter**: Keep/drop rows based on conditions
- **Join**: Combine tables
- **Aggregate**: Group by and summarize
- **Pivot**: Transform rows to columns

### Glue DPU-Seconds Billing

Understanding cost:

```
Cost = DPU-Seconds × $0.44 (approximately)
Total DPU-Seconds = (Num Workers × DPU per Worker × Time in Seconds)

Example:
- 10 workers × 1 DPU × 3600 seconds = 36,000 DPU-seconds
- Cost ≈ 36,000 × $0.44 / 3600 = $4.40 per hour
```

### Data Transformation Patterns

**Pattern 1: Extract, Transform, Load**

```python
from awsglue.context import GlueContext
from pyspark.sql import SparkSession
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
import sys

# Initialize
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'output_path'])
spark = SparkSession.builder.appName('ETL').getOrCreate()
glue_context = GlueContext(spark.sparkContext)
job = Job(glue_context)
job.init(args['JOB_NAME'], args)

# Extract - Read from Glue Catalog
customers = glue_context.create_dynamic_frame.from_catalog(
    database='sales_db',
    table_name='customers'
).toDF()

# Transform - Data cleaning
customers_clean = (
    customers
    .filter(customers.email.isNotNull())
    .withColumn('signup_year', f.year(customers.signup_date))
    .drop('internal_id')
)

# Load - Write to S3
customers_clean.repartition(10).write \
    .mode('overwrite') \
    .parquet(args['output_path'])

job.commit()
```

**Pattern 2: Data Validation & Quality Checks**

```python
from pyspark.sql.functions import col, when, count, lit

# Calculate data quality metrics
quality = customers.select([
    count(lit(1)).alias('total_rows'),
    count(when(col('email').isNull(), 1)).alias('null_emails'),
    count(when(~col('email').contains('@'), 1)).alias('invalid_emails'),
    count(when(col('age') < 0, 1)).alias('invalid_ages')
])

quality.collect()[0]
# Row(total_rows=1000, null_emails=5, invalid_emails=2, invalid_ages=0)

# Log metrics
for row in quality.collect():
    print(f"Quality Report: {row}")
```

**Pattern 3: Incremental Processing with Bookmarks**

```python
# Job configuration enables bookmarks:
# --job-bookmark-option: job-bookmark-enabled

# Glue automatically:
# 1. Tracks last processed file/partition
# 2. Skips already processed data on next run
# 3. Only processes new files

# Manual bookmark control:
glue_context.create_dynamic_frame.from_catalog(
    database='sales_db',
    table_name='transactions',
    transformation_ctx='transactions',
    push_down_predicate='year=2024 AND month>2'
).toDF()
```

---

## Development Setup

### Local Development with AWS Glue

**Option 1: Glue Development Endpoint (Deprecated)**
- Old approach, not recommended
- Being phased out

**Option 2: Docker-based Glue Runtime (Recommended)**

```bash
# Install Docker
# Pull Glue image
docker pull amazon/aws-glue-libs:glue_libs_3.0.0_image_01

# Run interactive development
docker run -it \
  -v ~/.aws:/root/.aws:ro \
  -v $(pwd):/workspace \
  amazon/aws-glue-libs:glue_libs_3.0.0_image_01 \
  pyspark

# In PySpark shell:
from awsglue.context import GlueContext
glueContext = GlueContext(spark)

# Test Glue job
df = glueContext.create_dynamic_frame.from_catalog(
    database='test_db',
    table_name='test_table'
).toDF()
```

**Option 3: Local Spark + AWS SDK**

```bash
# Install Spark locally
# Install boto3, awsglue
pip install awsglue boto3

# Develop job locally, test with sample data
# Deploy to Glue when ready
```

**Option 4: AWS Glue Studio + Interactive Sessions**

```python
# Interactive sessions in Glue Studio
# Real-time development without deploying entire job

# Start session:
aws glue create-session \
  --name my-dev-session \
  --role-arn arn:aws:iam::ACCOUNT:role/GlueRole \
  --default-arguments="--glue_version=3.0"

# Develop and test interactively
```

### Writing Glue Jobs

**Basic Job Structure:**

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, when, format_string

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'input_database',
    'input_table',
    'output_path'
])

# Initialize Spark and Glue
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args['JOB_NAME'], args)

# =====================
# ETL Logic Here
# =====================

# Extract
input_dyf = glue_context.create_dynamic_frame.from_catalog(
    database=args['input_database'],
    table_name=args['input_table'],
    transformation_ctx='input'
)

# Convert to DataFrame for complex transformations
df = input_dyf.toDF()

# Transform
transformed_df = (
    df
    .filter(df.is_active == True)
    .withColumn('processed_date',
                format_string('%Y-%m-%d', col('created_date')))
)

# Load
glue_context.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(transformed_df, glue_context, 'output'),
    connection_type='s3',
    connection_options={'path': args['output_path']},
    format='parquet',
    transformation_ctx='output'
)

job.commit()
```

**Handling Delimited Data:**

```python
# Read CSV with schema
import_dyf = glue_context.create_dynamic_frame.from_options(
    connection_type='s3',
    connection_options={
        'paths': ['s3://my-bucket/data/customers.csv'],
        'recurse': True
    },
    format='csv',
    format_options={
        'withHeader': True,
        'separator': ',',
        'quote': '"',
        'escape': '\\'
    },
    transformation_ctx='import'
)

# Apply schema
applymapping_dyf = ApplyMapping.apply(
    frame=import_dyf,
    mappings=[
        ('customer_id', 'string', 'customer_id', 'bigint'),
        ('name', 'string', 'name', 'string'),
        ('purchase_amount', 'string', 'amount', 'double')
    ],
    transformation_ctx='applymapping'
)
```

---

## IAM and Security

### Required IAM Permissions

**Basic Glue Job Execution:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

{
  "Effect": "Allow",
  "Action": [
    "glue:GetDatabase",
    "glue:GetTable",
    "glue:GetPartitions",
    "glue:CreateJob",
    "glue:UpdateJob",
    "glue:StartJobRun",
    "glue:GetJobRun"
  ],
  "Resource": "*"
}

{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject"
  ],
  "Resource": [
    "arn:aws:s3:::my-bucket/*"
  ]
}

{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:*"
}
```

**S3 Access:**

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::my-data-bucket",
    "arn:aws:s3:::my-data-bucket/*"
  ]
}
```

**RDS/JDBC Connection:**

```json
{
  "Effect": "Allow",
  "Action": [
    "rds-db:connect"
  ],
  "Resource": [
    "arn:aws:rds:region:account:db:db-instance-name/*"
  ]
}
```

### Encryption & Data Protection

**Data Encryption in Transit:**
- All Glue connections use TLS/SSL

**Data Encryption at Rest:**
```yaml
# Glue Catalog encryption
CatalogEncryptionMode: SSE-KMS
KmsKeyId: arn:aws:kms:region:account:key/key-id

# S3 encryption (job output)
StorageEncryptionConfiguration:
  SSEEncryption: SSE-S3 or SSE-KMS
```

**Connection Secrets:**
```python
# Store database credentials in AWS Secrets Manager
glue.create_connection(
    Name='prod-db-connection',
    Description='Production database',
    ConnectionType='mysql',
    ConnectionProperties={
        'JDBC_DRIVER_JAR_URI': 's3://bucket/mysql-connector-java.jar',
        'USERNAME': 'admin',
        'PASSWORD': 'secret-name',  # References Secrets Manager
        'ENCRYPTED': 'true',
        'SECRET_ID': 'prod/db/password'
    }
)
```

---

## Scaling and Performance

### Worker Types

| Worker Type | vCPU | Memory | Network | Best For |
|-------------|------|--------|---------|----------|
| G.1X | 4 | 16GB | Up to 10Gbps | Streaming, Python Shell |
| G.2X | 8 | 32GB | Up to 10Gbps | Standard Spark jobs |
| Z.2X | 8 | 32GB | Up to 100Gbps | ML, GPU workloads |

### Scaling Strategies

**1. Automatic Scaling (with Flex/Job Bookmarks):**

```python
# Glue automatically optimizes DPU usage
# with job bookmarks and flex runs

job.init('my-job', args)
# Glue assigns minimum DPU and scales as needed
```

**2. Manual Configuration:**

```yaml
Workers:
  NumberOfWorkers: 100  # Distributed processing
  WorkerType: G.2X
  GlueVersion: 3.0
```

**3. Partition Pruning:**

```python
# Only read needed partitions
df = glue_context.create_dynamic_frame.from_catalog(
    database='sales_db',
    table_name='transactions',
    push_down_predicate='year=2024 AND month>=3'  # Filter at read time
).toDF()
```

**4. Partitioning Output:**

```python
# Write partitioned output for faster future reads
df.write \
  .partitionBy('year', 'month', 'day') \
  .mode('overwrite') \
  .parquet(output_path)
```

### Performance Optimization

**Optimization 1: Reduce Data Across Network**

```python
# ❌ Bad - moves large data
df = big_table.join(small_table, 'id')

# ✅ Good - broadcasts small data
from pyspark.sql.functions import broadcast
df = big_table.join(broadcast(small_table), 'id')
```

**Optimization 2: Column Selection**

```python
# ❌ Bad - reads all columns
df = spark.read.parquet(path)

# ✅ Good - reads only needed columns
df = spark.read.parquet(path).select('id', 'name', 'amount')
```

**Optimization 3: Cache Intermediate Results**

```python
# If reusing transformed data
df_transformed = df.filter(...).cache()
result1 = df_transformed.groupBy(...).count()
result2 = df_transformed.filter(...)  # Uses cached data
```

**Optimization 4: Aggregation Before Write**

```python
# ❌ Bad - writes large detail rows
df_details.write.parquet(...)

# ✅ Good - aggregate first
df_summary = df_details.groupBy('category').agg({
    'amount': 'sum',
    'count': 'count'
})
df_summary.write.parquet(...)
```

---

## Monitoring and Debugging

### CloudWatch Metrics

**Job Executor Metrics:**
```python
# Available metrics:
# - glue.driver.*.jvm.heap.usage
# - glue.executor.*.jvm.heap.usage
# - glue.executor.*.blockManager.disk.diskSpaceUsed
# - glue.driver.aggregate.numStages
# - glue.driver.aggregate.numTasks

# Monitor in CloudWatch:
# Namespace: AWS/Glue
# Dimensions: JobName, RunId, ExecutorId
```

**Accessing Metrics:**

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Get job execution time
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/Glue',
    MetricName='glue.driver.aggregate.numStages',
    Dimensions=[
        {'Name': 'JobName', 'Value': 'my-job'},
        {'Name': 'RunId', 'Value': 'run-12345'}
    ],
    StartTime=datetime.now() - timedelta(hours=1),
    EndTime=datetime.now(),
    Period=60,
    Statistics=['Average', 'Maximum']
)
```

### CloudWatch Logs

**Job Logging:**

```python
# Enable detailed logging
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info(f"Processing {num_records} records")
logger.warning(f"Found {null_count} null values")
logger.error(f"Failed to process: {error}")

# View logs in CloudWatch:
# Log Group: /aws-glue/jobs/my-job-name
# Log Stream: run-12345-attempt-1
```

**Log Insights Queries:**

```
# Find failed jobs
fields @timestamp, jobName, status
| filter status = "FAILED"
| stats count() by jobName

# Find slow jobs
fields @timestamp, jobName, duration
| filter duration > 3600
| sort duration desc
```

### Debugging Failed Jobs

**1. Check Job Logs:**

```bash
aws logs tail /aws-glue/jobs/my-job --follow
```

**2. Inspect Last Run:**

```python
glue = boto3.client('glue')

response = glue.get_job_runs(
    JobName='my-job',
    MaxResults=10
)

for run in response['JobRuns']:
    print(f"RunId: {run['Id']}")
    print(f"State: {run['JobRunState']}")
    print(f"Error: {run.get('ErrorMessage', 'None')}")
    print(f"Duration: {run['ExecutionTime']}s")
```

**3. Common Errors & Solutions:**

| Error | Cause | Solution |
|-------|-------|----------|
| `AccessDenied` | Missing IAM permissions | Check role permissions |
| `EntityNotFoundException` | Database/table not found | Verify catalog items exist |
| `InvalidInputException` | Bad parameters | Check parameter format |
| `InternalServiceException` | Glue service error | Retry or contact support |
| `Timeout` | Job takes too long | Increase timeout or optimize |

### Structured Logging

```python
import json
from datetime import datetime

def log_event(event_type, details):
    """Log structured events for analysis"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'job_name': os.environ.get('JOB_NAME'),
        'run_id': os.environ.get('JOB_RUN_ID'),
        'details': details
    }
    print(json.dumps(log_entry))

# Usage
log_event('data_validation', {
    'source_rows': 10000,
    'valid_rows': 9950,
    'error_rows': 50
})
```

---

## Cost Optimization

### Understanding Glue Pricing

**DPU-Seconds Pricing:**
- ~$0.44 per DPU-hour
- Minimum 10 minutes per job run
- Pay for total DPU-seconds used

**Calculation Example:**
```
Scenario: 5 workers × G.2X (1 DPU each) for 30 minutes

DPU-Seconds = 5 workers × 1 DPU × (30 × 60) seconds = 9,000
Cost = 9,000 DPU-seconds × ($0.44 / 3600) = ~$1.10

Daily (if runs 20 times): $1.10 × 20 = $22/day
Monthly: $22 × 30 = ~$660/month
```

### Cost Optimization Strategies

**1. Right-Size Workers:**

```yaml
# ❌ Expensive - over-provisioned
Workers: 50
WorkerType: G.2X
Duration: 10 minutes

# ✅ Optimized - only use needed resources
Workers: 5
WorkerType: G.2X
Duration: 15 minutes (slightly longer, but much cheaper)
```

**2. Use Job Bookmarks:**

```yaml
# Enables: job-bookmark-option job-bookmark-enabled
# Benefit: Skip already processed data, reduce runtime

# Example savings:
# Without bookmark: 100GB scanned = 20 DPU-minutes
# With bookmark: 10GB new data = 2 DPU-minutes (90% savings)
```

**3. Partition Pruning:**

```python
# ❌ Reads entire table
df = glue_context.create_dynamic_frame.from_catalog(
    database='sales_db',
    table_name='transactions'
).toDF()

# ✅ Reads only March 2024
df = glue_context.create_dynamic_frame.from_catalog(
    database='sales_db',
    table_name='transactions',
    push_down_predicate='year=2024 AND month=3'
).toDF()

# Cost reduction: 80-90% fewer rows = 80-90% lower DPU usage
```

**4. Use Glue Flex Jobs:**

```yaml
# Standard: Pay for full duration
# Flex: Use spare capacity, ~60% cheaper but slower
# Good for: Non-urgent daily batch jobs

Flexible: true  # CloudFormation/API parameter
```

**5. Consolidate Jobs:**

```python
# ❌ 3 separate jobs
job1: extract from S3
job2: transform data
job3: load to redshift

# ✅ Single job combines all
extract()
transform()
load()

# Savings: Reduced number of job runs, better resource utilization
```

### Monitoring Costs

```python
import boto3

ce = boto3.client('ce')

# Get Glue costs
response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': '2024-03-01',
        'End': '2024-03-31'
    },
    Granularity='MONTHLY',
    Filter={
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['AWS Glue']
        }
    },
    Metrics=['AmortizedCost']
)

for result in response['ResultsByTime']:
    print(f"Month: {result['TimePeriod']['Start']}")
    print(f"Cost: ${result['Total']['AmortizedCost']['Amount']}")
```

---

## Integration Patterns

### Pattern 1: S3 → Glue Crawler → Catalog → Athena

```
Data in S3
    ↓
Glue Crawler runs (scheduled/on-demand)
    ↓
Creates/Updates Catalog tables
    ↓
Use Athena to query catalog
    ↓
Results back to S3
```

**Implementation:**

```python
# 1. Configure crawler in CloudFormation/Console
# 2. Crawler discovers schema
# 3. Query with Athena

# In Athena:
SELECT COUNT(*), department FROM products_database.products
GROUP BY department
```

### Pattern 2: RDS → Glue Job → S3 (Dump DB to Data Lake)

```
RDS Database
    ↓
Glue Job (Spark)
    ↓
Extract via JDBC
    ↓
Transform/Clean
    ↓
Write to S3 (Parquet)
    ↓
Catalog tables
```

**Implementation:**

```python
# Glue job
glue_context = GlueContext(spark_context)

# Read from RDS
rds_dyf = glue_context.create_dynamic_frame.from_options(
    connection_type='postgresql',
    connection_options={
        'url': 'jdbc:postgresql://hostname:5432/dbname',
        'user': 'username',
        'password': 'password',
        'dbtable': 'customers'
    },
    format='jdbc',
    transformation_ctx='rds'
)

# Transformation
df = rds_dyf.toDF()
df_clean = df.filter(df.is_active == True)

# Write to S3
glue_context.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(df_clean, glue_context, 'output'),
    connection_type='s3',
    connection_options={'path': 's3://lake/customers/'},
    format='parquet'
)
```

### Pattern 3: Multi-Source Integration

```
Data Sources:
├── S3 (CSV, JSON)
├── RDS (PostgreSQL)
├── DynamoDB
└── API (via Lambda)
    ↓
Glue Job
    ├── Extract from all sources
    ├── Match/merge records
    ├── Enrich data
    └── Validate quality
    ↓
Unified output
    ├── S3 (Parquet)
    ├── Redshift (RI update)
    └── Catalog updated
```

### Pattern 4: Streaming Integration with Kinesis

```
Kinesis Data Stream
    ↓
Glue Streaming Job
    ↓
Micro-batch transforms
    ↓
Output (S3/Redshift)
```

**Implementation:**

```python
from awsglue.context import GlueContext
from pyspark.sql import functions as F

glue_context = GlueContext(spark_context)

# Read from Kinesis
stream_df = glue_context.create_data_frame.from_kinesis(
    stream_name='my-stream',
    initial_position='latest',
    window_size='100 seconds'
)

# Transform
output = stream_df.select(
    F.col('data'),
    F.col('timestamp')
).filter(F.col('data').isNotNull())

# Write to S3
output.write.mode('append').parquet('s3://bucket/output/')
```

### Pattern 5: Data Quality & Monitoring

```
Source Data
    ↓
Glue Job
    ├── Data validation
    ├── Quality checks
    ├── Schema validation
    └── Anomaly detection
    ↓
If quality fails:
    ├── Log error
    ├── Notify team
    └── Quarantine data
    ↓
If passes:
    └── Load to target
```

---

## Real-World Examples

### Example 1: E-Commerce Order Processing Pipeline

**Scenario:** Daily batch processing of orders from multiple sources into data warehouse.

**Architecture:**

```
Order Sources:
├── S3 (Daily CSV exports)
├── Shopify API (via Lambda → S3)
└── On-prem database
    ↓
Glue Crawler (daily 6 AM)
    ├── Updates order schema
    └── Detects new data
    ↓
Glue ETL Job (6:30 AM)
    ├── Extract orders
    ├── Join with products
    ├── Enrich with customer data
    ├── Calculate metrics
    ├── Validate data quality
    └── Load to Redshift
    ↓
Redshift
    └── Ready for BI analysis (QlikSense, Tableau)
```

**Job Code:**

```python
import sys
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import *
from pyspark.context import SparkContext

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'redshift_endpoint'])

sc = SparkContext()
glue_context = GlueContext(sc)
job = Job(glue_context)
job.init(args['JOB_NAME'], args)

# Extract orders
orders = glue_context.create_dynamic_frame.from_catalog(
    database='raw_data',
    table_name='orders',
    transformation_ctx='orders'
).toDF()

# Extract products
products = glue_context.create_dynamic_frame.from_catalog(
    database='raw_data',
    table_name='products',
    transformation_ctx='products'
).toDF()

# Extract customers
customers = glue_context.create_dynamic_frame.from_catalog(
    database='raw_data',
    table_name='customers',
    transformation_ctx='customers'
).toDF()

# Join data
enriched_orders = (
    orders
    .join(products, 'product_id', 'left')
    .join(customers, 'customer_id', 'left')
    .withColumn('processing_date', current_date())
)

# Calculate metrics
order_summary = enriched_orders.groupBy('customer_id', 'order_date').agg(
    count('*').alias('item_count'),
    sum('total_amount').alias('order_total'),
    avg('unit_price').alias('avg_price')
)

# Data quality checks
quality_report = enriched_orders.agg(
    count(when(col('order_id').isNull(), 1)).alias('null_order_ids'),
    count(when(col('total_amount') < 0, 1)).alias('negative_amounts'),
    approx_count_distinct('customer_id').alias('unique_customers')
)

# Log quality metrics
for row in quality_report.collect():
    print(f"Quality: {row}")

# Load to Redshift
enriched_orders.write \
    .format('com.databricks.spark.redshift') \
    .option('url', f'jdbc:redshift://{args["redshift_endpoint"]}/analytics') \
    .option('user', 'etl_user') \
    .option('password', 'secret') \
    .option('dbtable', 'fact_orders') \
    .mode('append') \
    .save()

job.commit()
```

**Glue Configuration:**

```yaml
Name: ecommerce-order-pipeline
GlueVersion: 3.0
Workers: 20
WorkerType: G.2X
Timeout: 120
MaxRetries: 2
JobBookmarkOption: job-bookmark-enabled
Tags:
  Environment: production
  Team: data-engineering
```

### Example 2: Data Lake Consolidation

**Scenario:** Consolidate data from 50+ data sources into unified data lake.

**Architecture:**

```
Multiple Sources (50+)
├── Databases
├── APIs
├── Files
├── Streams
    ↓
Glue Crawlers (20+ crawlers, staggered)
    ├── Each discovers schema
    ├── Creates catalog entries
    └── Runs every 6 hours
    ↓
Data Lake (S3)
    ├── Bronze (raw)
    ├── Silver (cleaned)
    └── Gold (analytics)
    ↓
Glue Transformation Jobs
    ├── Bronze → Silver
    ├── Silver → Gold
    └── Quality enforcement
    ↓
Analytics/ML
    ├── Athena for SQL
    ├── SageMaker for ML
    └── QuickSight for BI
```

**Crawler Configuration (Multiple):**

```python
import boto3

glue = boto3.client('glue')

sources = [
    {'type': 's3', 'path': 's3://data1/'},
    {'type': 's3', 'path': 's3://data2/'},
    {'type': 'rds', 'database': 'prod_db1'},
    # ... 47 more sources
]

for i, source in enumerate(sources):
    glue.create_crawler(
        Name=f'crawler-{i}',
        Role='arn:aws:iam::ACCOUNT:role/GlueRole',
        DatabaseName='raw_data',
        Targets={'S3Targets': [{'Path': source['path']}]}
                if source['type'] == 's3' else {'...'},
        Schedule={'ScheduleExpression': f'cron({i % 60} * * * ? *)'},  # Stagger crawlers
        TablePrefix=f"src_{i}_",
        SchemaChangePolicy={
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'LOG'
        }
    )
```

---

## Best Practices

### 1. Data Organization

```
s3://data-lake/
├── bronze/ (raw data)
│   ├── source1/year=2024/month=03/day=15/
│   ├── source2/year=2024/month=03/day=15/
│   └── ...
├── silver/ (cleaned, validated)
│   ├── customers/
│   ├── orders/
│   └── ...
└── gold/ (aggregated, business-ready)
    ├── customer_analytics/
    ├── sales_metrics/
    └── ...
```

### 2. Catalog Organization

```
Databases:
├── raw_data (bronze layer sources)
├── processed_data (silver layer)
└── analytics_data (gold layer)

Table Naming:
├── stg_customers (staging)
├── dim_customers (dimension)
└── fact_transactions (fact)
```

### 3. Job Design

✅ **Do:**
- Keep jobs focused (single responsibility)
- Use parameters for configuration
- Enable job bookmarks for incremental processing
- Add comprehensive error handling and logging
- Version your code (Git)
- Test locally before deployment

❌ **Don't:**
- Hard-code credentials (use Secrets Manager)
- Create massive monolithic jobs
- Assume input data quality
- Ignore error scenarios
- Oversize worker allocation

### 4. Testing Strategy

```python
# Unit test transformations
def test_clean_customer_data():
    input_data = [
        {'id': 1, 'email': 'test@test.com'},
        {'id': 2, 'email': None},
        {'id': 3, 'email': 'invalid'}
    ]
    df = spark.createDataFrame(input_data, ['id', 'email'])

    cleaned = clean_customer_data(df)
    assert cleaned.count() == 2
    assert cleaned.filter(col('email').isNull()).count() == 0

# Integration test with sample S3 data
def test_glue_job_integration():
    # Run job with small test dataset
    # Verify output matches expected schema and values
    pass
```

### 5. Monitoring & Alerting

```python
# Set up CloudWatch alarms
import boto3

cloudwatch = boto3.client('cloudwatch')

# Alert if job fails
cloudwatch.put_metric_alarm(
    AlarmName='glue-job-failed',
    MetricName='glue.driver.aggregate.numFailedTasks',
    Namespace='AWS/Glue',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:region:account:alert-topic']
)

# Alert if job takes too long
cloudwatch.put_metric_alarm(
    AlarmName='glue-job-slow',
    MetricName='glue.driver.aggregate.numStages',
    Namespace='AWS/Glue',
    Statistic='Maximum',
    Period=300,
    EvaluationPeriods=2,
    Threshold=100,
    ComparisonOperator='GreaterThanThreshold'
)
```

### 6. Documentation

- Document job purpose and data lineage
- Keep README files in job repository
- Document transformation logic with comments
- Maintain data dictionary
- Track schema changes
- Document deployment procedures

### 7. Security Best Practices

```python
# ✅ Good: Use Secrets Manager
from boto3.secretsmanager import client as secretsmanager

secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='prod/db/password')
password = secret['SecretString']

# ✅ Good: Use IAM role-based access
glue.create_connection(
    Name='db-connection',
    ConnectionType='postgresql',
    ConnectionProperties={
        'SECRET_ID': 'prod/db/credentials'
    }
)

# ❌ Bad: Hard-coded credentials
PASSWORD = 'MyPassword123'
```

---

## Quick Reference

### Common Commands

```bash
# Create job from script
aws glue create-job \
  --name my-job \
  --role arn:aws:iam::123456789012:role/GlueRole \
  --command Name=glueetl,ScriptLocation=s3://bucket/job.py \
  --glue-version 3.0

# Start job run
aws glue start-job-run \
  --job-name my-job \
  --arguments '{"--output_path":"s3://bucket/output/"}'

# Get job status
aws glue get-job-run \
  --job-name my-job \
  --run-id jr_xxx

# List tables in catalog
aws glue get-tables \
  --database-name my_database

# Get table schema
aws glue get-table \
  --database-name my_database \
  --name my_table
```

### Useful Glue Job Parameters

```python
# Standard
--JOB_NAME: Job name
--job-bookmark-option: Enable bookmarks (job-bookmark-enabled)

# Performance
--spark-event-logs-path: S3 path for Spark logs
--enable-metrics: CloudWatch metrics
--enable-glue-datacatalog: Use Glue Catalog

# Streaming
--starting-offsets: latest or earliest
--max-batch-size: Records per batch
```

---

## Conclusion

AWS Glue provides a powerful, serverless platform for ETL workloads. Key takeaways:

1. **Start with Crawlers** - Automatic schema discovery saves time
2. **Design for Scaling** - Use partitions and job bookmarks
3. **Monitor Everything** - CloudWatch metrics are your friend
4. **Cost Matters** - Right-size workers, use flex jobs
5. **Security First** - Use Secrets Manager, not hard-coded credentials
6. **Organize Data** - Bronze/Silver/Gold structure works well
7. **Test Before Deploying** - Use local development and sample data
8. **Document** - Future you will thank current you
