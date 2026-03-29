# **📊 AWS CloudWatch**

AWS CloudWatch is a comprehensive monitoring and observability service that collects, visualizes, and acts on metrics, logs, and events from your AWS resources and applications.

## **Table of Contents**

1. [CloudWatch Overview](#1-cloudwatch-overview)
2. [Core Concepts](#2-core-concepts)
3. [Metrics](#3-metrics)
4. [Dashboards](#4-dashboards)
5. [Alarms](#5-alarms)
6. [CloudWatch Logs](#6-cloudwatch-logs)
7. [CloudWatch Events & EventBridge](#7-cloudwatch-events--eventbridge)
8. [CloudWatch Agent](#8-cloudwatch-agent)
9. [Log Insights & Analysis](#9-log-insights--analysis)
10. [Anomaly Detection](#10-anomaly-detection)
11. [Cross-Account Monitoring](#11-cross-account-monitoring)
12. [Cost Optimization](#12-cost-optimization)
13. [Integration Patterns](#13-integration-patterns)
14. [CLI Cheat Sheet](#14-cli-cheat-sheet)
15. [Best Practices](#15-best-practices)
16. [Advanced Topics](#16-advanced-topics)

---

## **1. CloudWatch Overview**

**AWS CloudWatch** is the central hub for monitoring, logging, and alarming across your AWS infrastructure.

### **Key Capabilities**

- 📊 **Metrics** - Collect and analyze numeric data from resources
- 📝 **Logs** - Aggregate, search, and analyze application and system logs
- 🚨 **Alarms** - Trigger actions based on metric thresholds or log patterns
- 📈 **Dashboards** - Visualize metrics and logs in real-time
- 📅 **Events** - React to state changes and scheduled events (via EventBridge)
- 🔍 **Insights** - Query logs with a SQL-like query language
- 🎯 **Anomaly Detection** - Automatically detect unusual metric behavior

### **Why CloudWatch Matters for Developers**

| Aspect | Benefit |
|--------|---------|
| **Visibility** | See full operational picture of your applications and infrastructure |
| **Troubleshooting** | Quickly identify and debug issues through logs and metrics |
| **Automation** | Alarms trigger actions (SNS, Lambda, SQS) for auto-remediation |
| **Cost Control** | Monitor resource usage and optimize costs |
| **Compliance** | Long-term storage and auditing of logs and metrics |
| **Performance** | Track latency, errors, throughput to optimize user experience |

---

## **2. Core Concepts**

### **2.1 Metrics**
A **metric** is a time-series data point representing the measurement of something.

- **Namespace**: Logical grouping (e.g., `AWS/EC2`, `AWS/Lambda`, `MyApp/Performance`)
- **Dimension**: Name-value pair to filter metrics (e.g., `InstanceId=i-12345678`)
- **Data Point**: Timestamp + value
- **Period**: Time interval for aggregation (e.g., 60 seconds, 5 minutes)
- **Statistic**: Aggregation method (Average, Sum, Maximum, Minimum, Count, etc.)

### **2.2 Log Groups**
A **log group** is a collection of log streams for a logical grouping (e.g., `/aws/lambda/my-function`).

- Multiple log streams feed into one log group
- Retention policies apply per log group
- Subscriptions filter logs for external processing

### **2.3 Log Streams**
A **log stream** is a sequence of log events from a single source (e.g., one Lambda execution or EC2 instance).

### **2.4 Alarms**
An **alarm** monitors a metric and triggers actions when thresholds are breached.

States:
- **OK** - Metric is within threshold
- **ALARM** - Metric breached threshold
- **INSUFFICIENT_DATA** - Not enough data to evaluate

### **2.5 Dashboard**
A **dashboard** is a custom-built view combining multiple widgets (metrics, logs, alarms).

---

## **3. Metrics**

### **3.1 AWS Service Metrics (Built-in)**

Most AWS services automatically publish metrics to CloudWatch.

#### **EC2 Example Metrics**
```
AWS/EC2 namespace:
- CPUUtilization (%)
- NetworkIn / NetworkOut (bytes)
- DiskReadOps / DiskWriteOps
- StatusCheckFailed
```

#### **Lambda Example Metrics**
```
AWS/Lambda namespace:
- Invocations (count)
- Errors (count)
- Duration (ms)
- Throttles (count)
- ConcurrentExecutions
- UnreservedConcurrentExecutions
```

#### **RDS Example Metrics**
```
AWS/RDS namespace:
- DatabaseConnections
- CPUUtilization
- ReadLatency / WriteLatency
- BinLogDiskUsage
```

**✔ Key Point**: Default EC2 metrics refresh every **5 minutes**. Use CloudWatch Agent for 1-minute granularity.

### **3.2 Custom Metrics**

Push application-specific metrics to CloudWatch.

#### **Python Example - Boto3**

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

# Single metric value
cloudwatch.put_metric_data(
    Namespace='MyApp/Performance',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 245.5,  # milliseconds
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Service', 'Value': 'OrderProcessor'},
                {'Name': 'Environment', 'Value': 'prod'}
            ]
        }
    ]
)

# Multiple metric values (batch)
cloudwatch.put_metric_data(
    Namespace='MyApp/APIMetrics',
    MetricData=[
        {
            'MetricName': 'RequestCount',
            'Value': 1,
            'Unit': 'Count',
            'Dimensions': [{'Name': 'Endpoint', 'Value': '/api/users'}]
        },
        {
            'MetricName': 'ResponseTime',
            'Value': 125,
            'Unit': 'Milliseconds',
            'Dimensions': [{'Name': 'Endpoint', 'Value': '/api/users'}]
        }
    ]
)
```

#### **Lambda Example - Publish Custom Metrics**

```python
import json
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    try:
        # Your business logic
        items_processed = len(event.get('records', []))

        # Publish custom metric
        cloudwatch.put_metric_data(
            Namespace='MyApp/Lambda',
            MetricData=[
                {
                    'MetricName': 'ItemsProcessed',
                    'Value': items_processed,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'ProcessingSuccess',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )

        return {'statusCode': 200, 'body': f'Processed {items_processed} items'}

    except Exception as e:
        # Publish error metric
        cloudwatch.put_metric_data(
            Namespace='MyApp/Lambda',
            MetricData=[
                {
                    'MetricName': 'ProcessingError',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        raise
```

### **3.3 Metric Resolution**

| Resolution | Best For | Cost | Storage Limit |
|------------|----------|------|----------------|
| **1 minute** | Production systems, catch early issues | Higher | 15 days |
| **5 minutes** | Standard AWS service metrics | Standard | 63 days |
| **1 hour** | Long-term trends, historical analysis | Lower | 15 months |

**High-resolution metrics** cost more but provide finer-grained visibility.

### **3.4 Metric Retention**

- **1 min** → Stored for **15 days**
- **5 min** → Stored for **63 days**
- **1 hour** → Stored for **455 days** (~15 months)

After retention expires, metrics are discarded.

---

## **4. Dashboards**

### **4.1 Creating Dashboards**

Dashboards visualize metrics, logs, and alarms in one place.

#### **Via AWS Management Console**

1. **CloudWatch → Dashboards → Create Dashboard**
2. Add widgets:
   - Line chart
   - Stacked area chart
   - Number widget (current metric value)
   - Logs table
   - Alarm state

#### **Via CloudFormation/CDK**

```json
{
  "Type": "AWS::CloudWatch::Dashboard",
  "Properties": {
    "DashboardName": "MyAppDashboard",
    "DashboardBody": {
      "widgets": [
        {
          "type": "metric",
          "properties": {
            "metrics": [
              ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
              [".", "Errors", {"stat": "Sum"}],
              [".", "Duration", {"stat": "Average"}]
            ],
            "period": 300,
            "stat": "Average",
            "region": "us-east-1",
            "title": "Lambda Performance"
          }
        }
      ]
    }
  }
}
```

### **4.2 Dashboard Best Practices**

- **Organize by service**: Separate regions for EC2, Lambda, RDS, etc.
- **Include error rates**: Critical for spotting issues
- **Add SLA targets**: Visually compare against thresholds
- **Use appropriate scales**: Ensure metrics aren't dwarfed by outliers
- **Include linked alarms**: Show alarm status for context

---

## **5. Alarms**

### **5.1 Alarm Types**

#### **Metric Alarms**
Monitor a single metric against a threshold.

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Example: Alarm when EC2 CPU > 80%
cloudwatch.put_metric_alarm(
    AlarmName='ec2-high-cpu',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Period=300,  # 5 minutes
    EvaluationPeriods=2,  # Triggered if threshold breached for 10 min
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',
    Dimensions=[
        {'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}
    ],
    AlarmActions=[
        'arn:aws:sns:us-east-1:123456789012:my-topic'
    ],
    TreatMissingData='notBreaching'
)
```

#### **Composite Alarms**
Combine multiple alarms with AND/OR logic.

```python
cloudwatch.put_composite_alarm(
    AlarmName='composite-app-health',
    AlarmRule=(
        '(ALARM(ec2-high-cpu) OR ALARM(lambda-errors)) '
        'AND ALARM(rds-cpu-high)'
    ),
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:alerts']
)
```

#### **Anomaly Detection Alarms**
Automatically detect unusual metric behavior.

```python
cloudwatch.put_metric_alarm(
    AlarmName='lambda-duration-anomaly',
    Metrics=[
        {
            'Id': 'm1',
            'ReturnData': True,
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/Lambda',
                    'MetricName': 'Duration',
                    'Dimensions': [{'Name': 'FunctionName', 'Value': 'my-function'}]
                },
                'Period': 300,
                'Stat': 'Average'
            }
        }
    ],
    ThresholdMetricId='ad1',
    Thresholds=[
        {
            'Id': 'ad1',
            'Expression': 'ANOMALY_DETECTION_BAND(m1, 2)',  # 2 standard deviations
            'ReturnData': True
        }
    ],
    ComparisonOperator='LessThanLowerOrGreaterThanUpperThreshold',
    EvaluationPeriods=1
)
```

### **5.2 Alarm States and Lifecycle**

```
OK
  ↓
ALARM (threshold breached)
  ↓
INSUFFICIENT_DATA (not enough data)
  ↓
OK (recovered)
```

**Transitions trigger actions**:
- SNS notifications
- Lambda invocations
- Auto Scaling actions
- Systems Manager OpsCenter
- EventBridge events

### **5.3 Missing Data Handling**

```python
# Options: notBreaching, breaching, missing
cloudwatch.put_metric_alarm(
    AlarmName='my-alarm',
    MetricName='CustomMetric',
    Namespace='MyApp',
    Threshold=100,
    ComparisonOperator='GreaterThanThreshold',
    TreatMissingData='notBreaching',  # Don't trigger if no data
    # ... other parameters
)
```

---

## **6. CloudWatch Logs**

### **6.1 Log Groups & Streams**

#### **Log Group Structure**

```
/aws/lambda/my-function
  │
  ├── 2025-01-15T10:30:00.000Z (stream from 1 execution)
  ├── 2025-01-15T10:35:00.000Z (stream from another execution)
  └── ...

/aws/ecs/my-service
  │
  ├── my-task-id-1
  ├── my-task-id-2
  └── ...
```

### **6.2 Log Retention Policies**

Set retention per log group to manage costs.

```python
import boto3

logs = boto3.client('logs')

# Retain logs for 7 days
logs.put_retention_policy(
    logGroupName='/aws/lambda/my-function',
    retentionInDays=7
)

# Never expire logs (keep indefinitely)
logs.delete_retention_policy(
    logGroupName='/aws/lambda/my-function'
)
```

### **6.3 Log Subscription Filters**

Forward logs to external destinations.

#### **Filter to Kinesis Stream**

```python
logs.put_subscription_filter(
    logGroupName='/aws/lambda/my-function',
    filterName='ToKinesis',
    filterPattern='[ERROR]',  # Only ERROR level logs
    destinationArn='arn:aws:kinesis:us-east-1:123456789012:stream/log-stream',
    roleArn='arn:aws:iam::123456789012:role/CloudWatchLogsRole'
)
```

#### **Filter to Lambda for Processing**

```python
logs.put_subscription_filter(
    logGroupName='/aws/api-gateway/my-api',
    filterName='ToLambda',
    filterPattern='{ $.statusCode > 400 }',  # JSON filter: status code > 400
    destinationArn='arn:aws:lambda:us-east-1:123456789012:function/log-processor'
)
```

### **6.4 Structured Logging Best Practices**

Always use JSON for structured logs:

```python
import json
import logging
from datetime import datetime

# Configure JSON logging
logger = logging.getLogger()

def log_event(message, level='INFO', **context):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        'requestId': context.get('request_id'),
        'userId': context.get('user_id'),
        'service': 'my-service',
        'version': '1.0',
        **context  # Include any additional context
    }
    print(json.dumps(log_entry))

# Usage
def lambda_handler(event, context):
    try:
        request_id = context.aws_request_id

        log_event(
            'Processing request',
            level='INFO',
            request_id=request_id,
            user_id=event.get('userId'),
            endpoint=event.get('path')
        )

        # Your business logic

        log_event(
            'Request successful',
            level='INFO',
            request_id=request_id,
            duration_ms=123
        )

    except Exception as e:
        log_event(
            f'Request failed: {str(e)}',
            level='ERROR',
            request_id=request_id,
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        raise
```

### **6.5 Log Groups for Common Services**

| Service | Log Group Pattern |
|---------|-------------------|
| Lambda | `/aws/lambda/{function-name}` |
| API Gateway | `/aws/api-gateway/{api-name}` |
| ECS | `/ecs/{cluster-name}/{service-name}` |
| RDS | `/aws/rds/{instance-id}` |
| VPC Flow Logs | `/aws/vpc/flowlogs/{flow-log-id}` |
| CloudTrail | `{s3-bucket-name}/AWSLogs/{accountId}/CloudTrail/` |

---

## **7. CloudWatch Events & EventBridge**

### **7.1 Relationship: CloudWatch Events → EventBridge**

**CloudWatch Events** is now part of **Amazon EventBridge** (same API, enhanced).

Use EventBridge for all event routing needs.

### **7.2 Common Event Patterns**

#### **EC2 State Change**

```python
import boto3

events = boto3.client('events')

events.put_rule(
    Name='ec2-state-change',
    EventPattern={
        "source": ["aws.ec2"],
        "detail-type": ["EC2 Instance State-change Notification"],
        "detail": {
            "state": ["running", "stopped"]
        }
    },
    State='ENABLED'
)

# Add target (Lambda, SNS, etc.)
events.put_targets(
    Rule='ec2-state-change',
    Targets=[
        {
            'Id': '1',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function/handle-ec2-change',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeRole'
        }
    ]
)
```

#### **Scheduled Events (Cron)**

```python
events.put_rule(
    Name='daily-backup',
    ScheduleExpression='cron(0 2 * * ? *)',  # 2 AM UTC daily
    State='ENABLED'
)

events.put_targets(
    Rule='daily-backup',
    Targets=[
        {
            'Id': '1',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function/backup-job',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeRole'
        }
    ]
)
```

#### **Custom Application Events**

```python
# Publish custom event from your app
events.put_events(
    Entries=[
        {
            'Source': 'myapp.orders',
            'DetailType': 'Order Placed',
            'Detail': json.dumps({
                'orderId': 'order-12345',
                'customerId': 'cust-67890',
                'amount': 299.99,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    ]
)

# Route to Lambda, SNS, SQS, etc.
```

---

## **8. CloudWatch Agent**

### **8.1 What is CloudWatch Agent?**

A lightweight agent installed on EC2/on-premises servers that:
- Collects system metrics (CPU, memory, disk, network)
- Collects custom application metrics
- Collects logs from files
- Sends data to CloudWatch

### **8.2 Installation & Configuration**

#### **Step 1: Create IAM Role**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "ec2messages:AcknowledgeMessage",
        "ec2messages:DeleteMessage",
        "ec2messages:FailMessage",
        "ec2messages:GetEndpoint",
        "ec2messages:GetMessages",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **Step 2: Download & Install Agent**

```bash
# On EC2 Linux
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# On EC2 Windows
Invoke-WebRequest https://s3.amazonaws.com/amazoncloudwatch-agent/windows/amd64/latest/amazon-cloudwatch-agent.msi -OutFile agent.msi
msiexec /i agent.msi
```

#### **Step 3: Create Agent Configuration**

```json
{
  "metrics": {
    "namespace": "MyApp/EC2",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60,
        "totalcpu": true
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/application.log",
            "log_group_name": "/aws/ec2/my-app",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%d %H:%M:%S"
          }
        ]
      }
    }
  }
}
```

#### **Step 4: Start Agent**

```bash
# Linux
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -fetch-config /opt/aws/amazon-cloudwatch-agent/etc/config.json \
  -m ec2 -a fetch-config
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -m ec2 -a start

# Windows
& "C:\Program Files\Amazon\AmazonCloudWatchAgent\amazon-cloudwatch-agent-ctl.ps1" `
  -a fetch-config -m ec2 -s -c file:C:\ProgramData\Amazon\AmazonCloudWatchAgent\config.json
```

---

## **9. Log Insights & Analysis**

### **9.1 CloudWatch Logs Insights Query Syntax**

QueryString to search and analyze logs.

#### **Basic Queries**

```sql
-- Fields to return
fields @timestamp, @message, @duration

-- Filter for errors
fields @timestamp, @message
| filter @message like /ERROR/

-- Filter with JSON
fields @timestamp, userId
| filter @message.statusCode > 400

-- Count events
fields @message
| stats count() as error_count

-- Get top 10 slowest requests
fields @duration
| stats max(@duration) as max_duration
| sort max_duration desc
| limit 10

-- Timeline of errors
fields @timestamp
| filter isProblem = true
| stats count() as error_count by bin(5m)
```

#### **Advanced Analytics**

```sql
-- Percentiles
fields @duration
| stats pct(@duration, 50) as p50, pct(@duration, 95) as p95, pct(@duration, 99) as p99

-- Group by dimension
fields @timestamp, userId, @duration
| stats avg(@duration) as avg_duration by userId

-- Multi-condition filtering
fields @timestamp, @message, requestId
| filter @message like /ERROR/ and userId != "system"
| stats count() as error_count by userId

-- Parse JSON logs
fields @timestamp, @message
| filter ispresent(@message.error)
| stats count() as errors by @message.error.type
```

### **9.2 Insights Query Examples**

#### **Example 1: Lambda Performance Analysis**

```sql
fields @timestamp, @duration, @maxMemoryUsed, @initDuration
| filter ispresent(@initDuration)  -- Only cold starts
| stats count() as cold_starts,
        avg(@duration) as avg_duration,
        max(@duration) as max_duration,
        avg(@maxMemoryUsed) as avg_memory
```

#### **Example 2: API Error Rate by Endpoint**

```sql
fields @timestamp, @message.endpoint, @message.statusCode
| filter @message.statusCode >= 400
| stats count() as errors by @message.endpoint
| sort errors desc
```

#### **Example 3: Top Users by Error Count**

```sql
fields userId, @message
| filter @message like /ERROR/
| stats count() as error_count by userId
| sort error_count desc
| limit 20
```

---

## **10. Anomaly Detection**

### **10.1 Anomaly Detector Creation**

CloudWatch automatically learns metric behavior and detects deviations.

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Enable anomaly detection
cloudwatch.put_metric_alarm(
    AlarmName='lambda-duration-anomaly',
    Metrics=[
        {
            'Id': 'm1',
            'ReturnData': True,
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/Lambda',
                    'MetricName': 'Duration',
                    'Dimensions': [{'Name': 'FunctionName', 'Value': 'api-processor'}]
                },
                'Period': 300,
                'Stat': 'Average'
            }
        }
    ],
    Thresholds=[
        {
            'Id': 'ad1',
            'Expression': 'ANOMALY_DETECTION_BAND(m1, 2)',  # 2-sigma band
            'ReturnData': True
        }
    ],
    ComparisonOperator='LessThanLowerOrGreaterThanUpperThreshold',
    EvaluationPeriods=1,
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:alerts']
)
```

### **10.2 Anomaly Detection Formula Options**

| Sigma Level | Sensitivity | Use Case |
|-------------|-------------|----------|
| **1** | Very high (catches most anomalies) | Development, aggressive alerting |
| **2** | Moderate (standard) | Production monitoring |
| **3** | Low (only major deviations) | Mission-critical stability |

---

## **11. Cross-Account Monitoring**

### **11.1 Central Monitoring Account Setup**

Monitor resources across multiple AWS accounts from one central account.

#### **Step 1: Create IAM Role in Source Account**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::CENTRAL_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### **Step 2: Create Policy in Source Account**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **Step 3: Access from Central Account (Python)**

```python
import boto3

sts = boto3.client('sts')
cloudwatch = boto3.client('cloudwatch')

# Assume role in source account
assumed = sts.assume_role(
    RoleArn='arn:aws:iam::SOURCE_ACCOUNT_ID:role/CrossAccountMonitoringRole',
    RoleSessionName='central-monitoring'
)

# Use temporary credentials
cloudwatch_cross = boto3.client(
    'cloudwatch',
    aws_access_key_id=assumed['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed['Credentials']['SecretAccessKey'],
    aws_session_token=assumed['Credentials']['SessionToken']
)

# Query metrics from source account
metrics = cloudwatch_cross.list_metrics(Namespace='AWS/Lambda')
```

---

## **12. Cost Optimization**

### **12.1 Cost Drivers**

| Component | Cost Driver | Optimization |
|-----------|------------|--------------|
| **Metrics** | Number of metrics + resolution | Use 5-min resolution; delete unused custom metrics |
| **Logs** | Ingestion + storage | Set retention policy; filter at source |
| **Alarms** | Number of alarms evaluated | Consolidate with composite alarms |
| **Dashboards** | API calls to render | Cache dashboard data; reduce refresh frequency |
| **Logs Insights** | Data scanned | Use appropriate time window; filter early |

### **12.2 Cost Reduction Strategies**

#### **1. Set Aggressive Log Retention**

```python
import boto3

logs = boto3.client('logs')

# 7 days instead of indefinite
logs.put_retention_policy(
    logGroupName='/aws/lambda/function',
    retentionInDays=7
)
```

#### **2. Use Log Subscription Filters to Archive**

```python
# Archive old logs to S3 (cheaper storage)
logs.put_subscription_filter(
    logGroupName='/aws/lambda/logs',
    filterName='archive-to-s3',
    filterPattern='',  # All logs
    destinationArn='arn:aws:kinesis:us-east-1:123456789012:stream/archive'
)
```

#### **3. Delete Unused Custom Metrics**

```python
# List and delete unused metrics
cloudwatch = boto3.client('cloudwatch')

# First, find metrics with no data points
metrics = cloudwatch.list_metrics(Namespace='MyApp')

for metric in metrics['Metrics']:
    # Check if metric has recent data
    data = cloudwatch.get_metric_statistics(
        Namespace=metric['Namespace'],
        MetricName=metric['MetricName'],
        StartTime=datetime.utcnow() - timedelta(days=7),
        EndTime=datetime.utcnow(),
        Period=86400
    )

    if not data['Datapoints']:
        print(f"No data for {metric['MetricName']} - consider deleting")
```

#### **4. Use Composite Alarms**

Instead of separate alarms → 1 composite alarm.

```python
# Before: 5 separate alarms
# After: 5 metric alarms + 1 composite = 6 total (vs. 10)
# But better is to use composite for conditions

cloudwatch.put_composite_alarm(
    AlarmName='app-health',
    AlarmRule='(ALARM(cpu) OR ALARM(memory)) AND OK(disk)',
    AlarmActions=['arn:aws:sns:...']
)
```

---

## **13. Integration Patterns**

### **13.1 CloudWatch → SNS → Email**

Alert developers via email.

```python
import boto3

sns = boto3.client('sns')

# Create SNS topic
topic_response = sns.create_topic(Name='cloudwatch-alerts')
topic_arn = topic_response['TopicArn']

# Subscribe to topic
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='email',
    Endpoint='alerts@mycompany.com'
)

# Create alarm with SNS action
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_alarm(
    AlarmName='high-error-rate',
    MetricName='Errors',
    Namespace='AWS/Lambda',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=[topic_arn]
)
```

### **13.2 CloudWatch Logs → Lambda → Custom Action**

Process logs and take action.

```python
import json
import boto3
import base64
import zlib

def lambda_handler(event, context):
    # Decode CloudWatch Logs event
    log_data = json.loads(
        zlib.decompress(
            base64.b64decode(event['awslogs']['data'])
        )
    )

    log_events = log_data['logEvents']

    for log_event in log_events:
        message = log_event['message']

        if 'CRITICAL_ERROR' in message:
            # Create incident ticket in Jira, PagerDuty, etc.
            create_incident(message)

            # Send to Slack
            send_slack_alert(f"Critical error detected: {message}")

def create_incident(message):
    # Your logic to create incident
    pass

def send_slack_alert(message):
    # Your logic to send Slack message
    pass
```

### **13.3 CloudWatch Metrics → Lambda → DynamoDB**

Store metrics long-term in DynamoDB (cheaper than CloudWatch).

---

## **14. CLI Cheat Sheet**

```bash
# List metrics in namespace
aws cloudwatch list-metrics --namespace "AWS/Lambda"

# Get metric data
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=my-function \
  --statistics Average,Maximum \
  --start-time 2025-01-15T00:00:00Z \
  --end-time 2025-01-15T23:59:59Z \
  --period 3600

# Put custom metric
aws cloudwatch put-metric-data \
  --namespace MyApp \
  --metric-name ProcessingTime \
  --value 123 \
  --unit Milliseconds

# Create alarm
aws cloudwatch put-metric-alarm \
  --alarm-name my-alarm \
  --alarm-description "High CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Describe alarms
aws cloudwatch describe-alarms --alarm-names my-alarm

# Disable alarm
aws cloudwatch disable-alarm-actions --alarm-names my-alarm

# Enable alarm
aws cloudwatch enable-alarm-actions --alarm-names my-alarm

# Delete alarm
aws cloudwatch delete-alarms --alarm-names my-alarm

# Put log retention
aws logs put-retention-policy \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 7

# List log groups
aws logs describe-log-groups

# Get log events
aws logs get-log-events \
  --log-group-name /aws/lambda/my-function \
  --log-stream-name stream-name

# Start Logs Insights query
aws logs start-query \
  --log-group-name /aws/lambda/my-function \
  --start-time 1673740800 \
  --end-time 1673827200 \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | stats count() by bin(5m)'

# Get query results
aws logs get-query-results --query-id <query-id>

# Create subscription filter
aws logs put-subscription-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name my-filter \
  --filter-pattern "[ERROR]" \
  --destination-arn arn:aws:kinesis:us-east-1:123456789012:stream/my-stream
```

---

## **15. Best Practices**

### **15.1 Monitoring & Observability**

- ✅ **Instrument from day one** - Don't wait until issues arise
- ✅ **Use structured logging (JSON)** - Makes logs queryable
- ✅ **Include request IDs** - Trace requests across systems
- ✅ **Log at appropriate levels** - Use INFO, WARN, ERROR appropriately
- ✅ **Custom metrics for business logic** - Track application-specific KPIs
- ✅ **Alert on symptoms, not noise** - Reduce false positives with smart thresholds
- ✅ **Set meaningful dashboards** - Support operational decisions

### **15.2 Cost Optimization**

- ✅ **Set log retention policies** - Avoid storing logs indefinitely
- ✅ **Use high-resolution (1-min) only for critical metrics** - Use 5-min for others
- ✅ **Archive important logs to S3** - Cheaper long-term storage
- ✅ **Use Logs Insights purposefully** - Limit time windows
- ✅ **Consolidate alarms** - Use composite alarms for complex logic
- ✅ **Review unused metrics monthly** - Delete metrics no longer needed

### **15.3 Alarming Strategy**

- ✅ **Alert on business metrics** - Errors, latency, throughput
- ✅ **Don't alert on infrastructure minutiae** - Only if it impacts users
- ✅ **Set realistic thresholds** - Based on baseline + margin
- ✅ **Include context in alerts** - SNS messages with useful info
- ✅ **Escalation paths** - Define who gets notified and when
- ✅ **Alert fatigue prevention** - Tune reduce false positives

### **15.4 Log Management**

- ✅ **Centralize logs** - Route all logs to CloudWatch
- ✅ **Use consistent format** - JSON with standard fields
- ✅ **Avoid logging sensitive data** - PII, secrets, credentials
- ✅ **Filter logs at source** - Don't send unnecessary logs
- ✅ **Version log format** - If format changes, document it
- ✅ **Use log groups as boundaries** - Separate by service/environment

---

## **16. Advanced Topics**

### **16.1 CloudWatch Synthetics**

Create synthetic canaries to monitor endpoints.

```python
# Monitor API endpoint continuously
import boto3

synthetics = boto3.client('synthetics')

# Canary script (runs automatically)
canary_script = """
const synthetics = require('Synthetics');
const https = require('https');

const pageLoadBlueprint = async function () {
    let url = "https://api.example.com/health";
    let response = await new Promise((resolve, reject) => {
        https.get(url, (res) => {
            if (res.statusCode !== 200) {
                reject(new Error(`API returned ${res.statusCode}`));
            }
            resolve(res);
        }).on('error', reject);
    });
    return response;
};

exports.handler = async function(event, context) {
    return await pageLoadBlueprint();
};
```

### **16.2 CloudWatch RUM (Real User Monitoring)**

Monitor actual user experience in web applications.

```javascript
// Embed in web application
import CWRum from "aws-rum-web";

CWRum.init({
    sessionSampleRate: 0.1,
    guestRoleArn: "arn:aws:iam::123456789012:role/CloudWatchRUMRole",
    identityPoolId: "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    telemetries: ["performance", "http", "errors"],
    domain: "example.com",
});
```

### **16.3 Metric Filters from Logs**

Extract metrics from log data automatically.

```python
logs = boto3.client('logs')

# Create metric filter: count errors in logs
logs.put_metric_filter(
    logGroupName='/aws/lambda/my-function',
    filterName='ErrorCount',
    filterPattern='[ERROR]',
    metricTransformations=[
        {
            'metricName': 'ErrorCount',
            'metricNamespace': 'MyApp/Lambda',
            'metricValue': '1',
            'defaultValue': 0
        }
    ]
)
```

### **16.4 Container Insights**

Monitor containerized workloads (ECS, EKS).

```yaml
# CloudFormation example
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: my-cluster
      ClusterSettings:
        - Name: containerInsights
          Value: enabled
```

### **16.5 Application Insights**

Automatic monitoring for .NET and Java applications.

---

## **📌 Final Summary**

| Component | Purpose | Key Takeaway |
|-----------|---------|--------------|
| **Metrics** | Numeric time-series data | Understand resource usage; custom metrics for business logic |
| **Logs** | Events and messages | Centralize; use JSON; set retention |
| **Alarms** | Trigger on thresholds | Alert on impact; reduce false positives |
| **Dashboards** | Visualize status | Organize by service; include SLAs |
| **Logs Insights** | Query logs at scale | Analyze patterns; find root causes |
| **EventBridge** | Route events | Automate responses; decouple systems |
| **Agent** | On-premises monitoring | Collect system + application metrics |
| **Anomaly Detection** | Automatic issue detection | Catch unusual patterns early |

---

**Key Developer Takeaways:**

1. **Instrument everything** - Metrics + logs from day one
2. **Use CloudWatch as your source of truth** - Centralize observability
3. **Alert on business impact, not infrastructure** - Reduce noise
4. **Structured JSON logging** - Makes debugging /analysis faster
5. **Set log retention policies** - Control costs
6. **Custom metrics for what matters** - Business KPIs, performance, errors
7. **Use Logs Insights to investigate** - Query patterns quickly
8. **Integrate with incident response** - Alarms trigger automation
