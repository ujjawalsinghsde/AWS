# Advanced CI/CD Topics

## Multi-Account Deployments

### Architecture

```
Shared Account (Pipeline)
        ↓ AssumeRole
Dev Account (Resources)
        ↓ AssumeRole
Prod Account (Resources)
```

### Cross-Account Role Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SOURCE-ACCOUNT:role/CodePipelineRole"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Pipeline Configuration

```json
{
  "name": "Deploy",
  "actions": [
    {
      "name": "DeployToDev",
      "roleArn": "arn:aws:iam::DEV-ACCOUNT:role/CrossAccountRole",
      "configuration": {
        "ApplicationName": "my-app",
        "DeploymentGroupName": "dev"
      }
    },
    {
      "name": "DeployToProd",
      "roleArn": "arn:aws:iam::PROD-ACCOUNT:role/CrossAccountRole",
      "configuration": {
        "ApplicationName": "my-app",
        "DeploymentGroupName": "prod"
      }
    }
  ]
}
```

## Blue-Green Deployments

### Implementation Strategy

```
Load Balancer
    ↓
┌─────────────┬─────────────┐
Blue Env      Green Env
v1            v2
100% traffic  0% traffic
    ↓
DNS/LB Switch
    ↓
Blue Env      Green Env
v1            v2
0% traffic    100% traffic
    ↓
Rollback available
Blue Env      Green Env
v1            v2
Quick switch  Old version ready
```

### Elastic Load Balancer Setup

```bash
# Create target groups
aws elbv2 create-target-group \
    --name blue-targets \
    --protocol HTTP \
    --port 80

aws elbv2 create-target-group \
    --name green-targets \
    --protocol HTTP \
    --port 80

# Register instances in target groups
aws elbv2 register-targets \
    --target-group-arn arn:aws:elasticloadbalancing:... \
    --targets Id=i-1234567890abcdef0

# Create listener rule
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### CodeDeploy Blue-Green Configuration

```json
{
  "version": "0.0",
  "Resources": [
    {
      "TargetService": {
        "Type": "AWS::EC2::Instance",
        "Properties": {
          "Name": "MyApp",
          "Port": 3000
        }
      }
    }
  ],
  "Hooks": [
    {
      "BeforeBlockTraffic": "scripts/before-block.sh"
    },
    {
      "AfterBlockTraffic": "scripts/after-block.sh"
    },
    {
      "BeforeAllowTraffic": "scripts/before-allow.sh"
    },
    {
      "AfterAllowTraffic": "scripts/after-allow.sh"
    }
  ]
}
```

## Canary Deployments

### Traffic Shift Strategies

#### Linear
```
Time: 0min → 10min → 20min → 30min
Traffic to v2: 0% → 10% → 20% → 30%
```

#### Exponential
```
Time: 0min → 10min → 20min
Traffic to v2: 0% → 10% → 100%
```

#### All-at-once
```
Time: 0min
Traffic to v2: 100%
```

### Lambda Alias for Canary

```python
import boto3

lambda_client = boto3.client('lambda')

# Create version
version = lambda_client.publish_version(
    FunctionName='my-function',
    Description='New version'
)

# Create alias for canary
lambda_client.create_alias(
    FunctionName='my-function',
    Name='live',
    FunctionVersion=version['Version'],
    RoutingConfig={
        'AdditionalVersionWeights': {
            version['Version']: {
                'FunctionWeight': 0.1  # 10% traffic
            }
        }
    }
)

# Monitor metrics
cloudwatch = boto3.client('cloudwatch')
metrics = cloudwatch.get_metric_statistics(
    Namespace='AWS/Lambda',
    MetricName='Errors',
    Dimensions=[
        {
            'Name': 'FunctionName',
            'Value': 'my-function'
        }
    ],
    StartTime=datetime.utcnow() - timedelta(minutes=10),
    EndTime=datetime.utcnow(),
    Period=300,
    Statistics=['Sum']
)

# If metrics look good, shift more traffic
if all(dp['Sum'] == 0 for dp in metrics['Datapoints']):
    lambda_client.update_alias(
        FunctionName='my-function',
        Name='live',
        FunctionVersion=version['Version'],
        RoutingConfig={
            'AdditionalVersionWeights': {
                version['Version']: {
                    'FunctionWeight': 1.0  # 100% traffic
                }
            }
        }
    )
```

## Monitoring and Observability

### CloudWatch Dashboards

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    'widgets': [
        {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['AWS/CodePipeline', 'PipelineExecutionCount', {'stat': 'Sum'}],
                    ['AWS/CodeBuild', 'FailedBuilds', {'stat': 'Sum'}],
                    ['AWS/CodeDeploy', 'Failed', {'stat': 'Sum'}],
                    ['AWS/Lambda', 'Errors', {'stat': 'Sum'}],
                    ['AWS/Lambda', 'Duration', {'stat': 'Average'}]
                ],
                'period': 300,
                'stat': 'Average',
                'region': 'us-east-1',
                'title': 'CI/CD Pipeline Metrics'
            }
        },
        {
            'type': 'log',
            'properties': {
                'query': '''
                    fields @message, @duration
                    | filter ispresent(@duration)
                    | stats avg(@duration), max(@duration), count() by bin(5m)
                ''',
                'region': 'us-east-1',
                'title': 'Build Duration Trends'
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='CI-CD-Pipeline',
    DashboardBody=json.dumps(dashboard_body)
)
```

### CloudWatch Alarms

```python
cloudwatch = boto3.client('cloudwatch')

# Alert on build failures
cloudwatch.put_metric_alarm(
    AlarmName='CI-CD-Build-Failures',
    MetricName='FailedBuilds',
    Namespace='AWS/CodeBuild',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:alerts']
)

# Alert on deployment errors
cloudwatch.put_metric_alarm(
    AlarmName='CI-CD-Deployment-Failures',
    MetricName='Failed',
    Namespace='AWS/CodeDeploy',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=1,
    ComparisonOperator='GreaterThanOrEqualToThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789:alerts']
)
```

### X-Ray Tracing

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

@xray_recorder.capture('deploy_function')
def deploy_application(event, context):
    # X-Ray will automatically trace Lambda calls
    try:
        result = execute_deployment(event)
        xray_recorder.current_subsegment().put_annotation('status', 'success')
        return result
    except Exception as e:
        xray_recorder.current_subsegment().put_annotation('status', 'failed')
        raise
```

## Cost Optimization

### Spot Instances for Non-Critical Builds

```json
{
  "environment": {
    "computeType": "BUILD_GENERAL1_SMALL",
    "image": "aws/codebuild/amazonlinux2-x86_64-standard:5.0",
    "environmentVariables": [
      {
        "name": "USE_SPOT",
        "value": "true"
      }
    ]
  }
}
```

### S3 Artifact Cleanup

```python
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3')

# Delete artifacts older than 90 days
objects = s3.list_objects_v2(Bucket='my-artifacts')

for obj in objects['Contents']:
    age = datetime.now(obj['LastModified'].tzinfo) - obj['LastModified']
    if age > timedelta(days=90):
        s3.delete_object(Bucket='my-artifacts', Key=obj['Key'])
```

### CodeBuild Caching

```yaml
cache:
  paths:
    - '/root/.npm/**/*'
    - '/root/.cache/**/*'
```

## Security Best Practices

### IAM Least Privilege

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GetBranch",
        "codecommit:GetCommit"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app",
      "Condition": {
        "StringEquals": {
          "codecommit:References": "refs/heads/main"
        }
      }
    }
  ]
}
```

### Secrets Management

```python
import boto3
import json

secrets_manager = boto3.client('secretsmanager')

# Store sensitive data
secrets_manager.create_secret(
    Name='app/database/credentials',
    SecretString=json.dumps({
        'username': 'admin',
        'password': 'secure-password'
    })
)

# Retrieve in Lambda
secret = secrets_manager.get_secret_value(
    SecretId='app/database/credentials'
)
credentials = json.loads(secret['SecretString'])
```

### SSL/TLS for Artifacts

```bash
aws s3api put-bucket-policy \
    --bucket my-artifacts \
    --policy '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "DenyUnencryptedObjectUploads",
          "Effect": "Deny",
          "Principal": "*",
          "Action": "s3:PutObject",
          "Resource": "arn:aws:s3:::my-artifacts/*",
          "Condition": {
            "StringNotEquals": {
              "s3:x-amz-server-side-encryption": "AES256"
            }
          }
        }
      ]
    }'
```

## Performance Optimization

### Build Parallelization

```yaml
version: 0.2

phases:
  build:
    commands:
      - npm run build &
      - npm run test &
      - npm run lint &
      - wait
```

### Docker Layer Caching

```dockerfile
FROM node:18-alpine

# Cache busting strategy
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

## Compliance and Auditing

### CloudTrail Setup

```bash
aws cloudtrail create-trail \
    --name ci-cd-audittrail \
    --s3-bucket-name audit-logs

aws cloudtrail start-logging \
    --trail-name ci-cd-audittrail
```

### CodePipeline Audit

```python
cloudtrail = boto3.client('cloudtrail')

events = cloudtrail.lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'ResourceType',
            'AttributeValue': 'AWS::CodePipeline::Pipeline'
        }
    ],
    MaxResults=50
)

for event in events['Events']:
    print(f"Event: {event['EventName']}")
    print(f"Time: {event['EventTime']}")
    print(f"Resources: {event['Resources']}")
```

## Disaster Recovery

### Pipeline Backup

```python
import json
import boto3

codepipeline = boto3.client('codepipeline')

# Get pipeline definition
pipeline = codepipeline.get_pipeline(name='my-pipeline')

# Save to S3
s3 = boto3.client('s3')
s3.put_object(
    Bucket='backups',
    Key=f"pipelines/{pipeline['name']}-backup.json",
    Body=json.dumps(pipeline)
)
```

### Rollback Procedures

1. **Automatic Rollback**
   - CodeDeploy monitors health checks
   - Automatically reverts on failure

2. **Manual Rollback**
   - Deploy previous version
   - Use blue-green for instant switch

3. **Data Rollback**
   - Database backups via snapshots
   - RDS automated backups

## Next Steps

1. Implement monitoring dashboard
2. Setup cost optimization
3. Configure security policies
4. Plan for multi-account
5. Test disaster recovery

## Summary

- **Multi-Account** = Cross-account deployments
- **Blue-Green** = Zero-downtime deployments
- **Canary** = Gradual traffic shift
- **Monitoring** = CloudWatch dashboards and alarms
- **Cost** = Spot instances, S3 cleanup, caching
- **Security** = Least privilege IAM, secrets
- **Performance** = Parallelization, layer caching
- **Compliance** = CloudTrail, audit logs

---

**Previous**: [Lambda Functions Guide](../07-Lambda/README.md)
**Next**: [Examples](../09-Examples/README.md)
