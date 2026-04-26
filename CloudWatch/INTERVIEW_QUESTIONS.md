# CloudWatch Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is CloudWatch and its main components?**
   - Monitoring and observability service
   - Components: Metrics, Logs, Alarms, Dashboards, Insights, Anomaly Detection
   - Central place to monitor all AWS resources
   - Custom metrics support

2. **Explain CloudWatch metrics.**
   - Time-series data (value + timestamp)
   - Dimensions: Attributes (InstanceId, DatabaseName)
   - Resolution: 1-minute (standard) or 1-second (high resolution)
   - Retention: 15 days at 1-min, 1 hour at 5-min, then daily for 15 months
   - Custom metrics: Application-specific monitoring

3. **What are CloudWatch alarms?**
   - Monitor metric over time
   - States: OK, ALARM, INSUFFICIENT_DATA
   - Actions: SNS notification, Auto-scaling, EC2 actions
   - Evaluation: Threshold-based or anomaly detection
   - Types: Static threshold or anomaly detection

4. **Explain CloudWatch Logs.**
   - Collect logs from applications, services
   - Log Groups: Collection of logs from same source
   - Log Streams: Ordered logs from single resource
   - Retention: Configurable (never to 400 years)
   - Cost: Per GB ingested + per GB stored

5. **What is CloudWatch Insights?**
   - Query language for logs (CloudWatch Logs Insights)
   - SQL-like syntax for complex queries
   - Real-time analysis
   - Example: Find 404 errors in last 1 hour

---

## 2. Intermediate Scenarios

### Application Monitoring

6. **Scenario: Monitor application health with custom metrics.**
   - Application publishes custom metrics:
     - Request count, latency, error rate
     - Business metrics: Orders processed, revenue
   - CloudWatch receives via PutMetricData API
   - Alarms trigger on thresholds
   - Dashboard displays KPIs
   - Example:
   ```python
   cloudwatch = boto3.client('cloudwatch')
   cloudwatch.put_metric_data(
       Namespace='MyApp',
       MetricData=[
           {
               'MetricName': 'Orders',
               'Value': 100,
               'Unit': 'Count',
               'Timestamp': datetime.now()
           }
       ]
   )
   ```

7. **Implement comprehensive application logging.**
   - Structure: JSON logs for easy parsing
   - Fields: timestamp, level, request_id, user, message
   - Log retention: 30 days for dev, 90 days for prod
   - CloudWatch Insights query:
   ```
   fields @timestamp, @message, @duration
   | stats count() as request_count by bin(300)
   ```

### Troubleshooting & Debugging

8. **Scenario: Application experiencing high latency. Troubleshoot.**
   - CloudWatch metrics:
     - Application latency (p50, p99)
     - ELB response time
     - RDS query latency
     - Lambda duration
   - Identify slowest component
   - Correlate logs: Find slow queries
   - Check infrastructure: CPU, memory, network

---

## 3. Advanced Scenarios

### Anomaly Detection & Predictive

9. **Implement anomaly detection for auto-scaling.**
   - Metric: Request count per minute
   - Anomaly Detector: Learns normal pattern
   - Alarm: Triggers if spike > 2σ
   - Auto-scaling: Scales up automatically
   - Benefit: Responds to unusual traffic

10. **Design dashboard for executive visibility.**
    - KPIs: Revenue, users, uptime
    - Real-time: Last hour data
    - Trend: Daily/weekly comparison
    - Alarms: Current alert status
    - Drill-down: Click to details
    - Auto-refresh: Every 5 minutes

---

## 4. Real-World Scenarios

11. **Scenario: Infrastructure costs increased 40%. Find root cause.**
    - CloudWatch insights:
      - Find high-CPU EC2 instances
      - Identify long-running Lambda functions
      - Check unused resources
    - AWS Cost Explorer:
      - Breakdown by service
      - Identify cost drivers
    - Solutions:
      - Right-size instances
      - Implement cost alarms
      - Use Reserved Instances

12. **Implement cost monitoring with alarms.**
    - Hourly cost estimate from Cost Explorer
    - CloudWatch metric: EstimatedCharges
    - Alarm: If cost > budget for month
    - Action: SNS notification to finance team
    - Investigate high-cost resources

---

## 5. Best Practices

13. **CloudWatch best practices:**
    - Structured logging (JSON format)
    - Appropriate metric granularity
    - Meaningful alarm thresholds
    - Log retention per compliance
    - Dashboard for key metrics
    - Anomaly detection for spikes
    - Regular alarm review
    - Cost optimization: Log filtering

---

## 6. Hands-On Examples

14. **Send custom metric to CloudWatch:**
    ```python
    import boto3

    cloudwatch = boto3.client('cloudwatch')

    def publish_metric(metric_name, value):
        cloudwatch.put_metric_data(
            Namespace='CustomApp',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': 'production'}
                    ]
                }
            ]
        )
    ```

15. **Create CloudWatch alarm with SNS notification:**
    ```python
    cloudwatch = boto3.client('cloudwatch')

    cloudwatch.put_metric_alarm(
        AlarmName='HighErrorRate',
        MetricName='Errors',
        Namespace='MyApp',
        Statistic='Sum',
        Period=300,
        EvaluationPeriods=2,
        Threshold=100,
        ComparisonOperator='GreaterThanThreshold',
        AlarmActions=['arn:aws:sns:region:account:topic']
    )
    ```

---

## Tips for Interview Success

- **Observability**: Think beyond metrics (logs, traces, events)
- **Custom metrics**: Application-specific monitoring
- **Alarms**: Actionable, not false positives
- **Log insights**: Know how to query logs
- **Cost monitoring**: Often important business requirement
- **Dashboard design**: For different audiences
- **Anomaly detection**: Modern approach to alerts

