# AWS Lambda in CI/CD Pipeline

## Lambda Role in CI/CD

Lambda functions add automation and intelligence to CI/CD pipelines:

| Use Case | Purpose |
|----------|---------|
| **Test Automation** | Run integration tests |
| **Approval Logic** | Automated decision making |
| **Post-Deployment** | Validation and smoke tests |
| **API Testing** | Invoke endpoints after deploy |
| **Data Validation** | Check database state |
| **Notifications** | Send deployment alerts |
| **Rollback Automation** | Automatic rollback triggers |
| **Infrastructure Checks** | Verify resources created |

## Lambda Functions in Pipeline

### 1. Pre-Build Validation Lambda

```python
import json
import boto3
import subprocess

codebuild = boto3.client('codebuild')
codepipeline = boto3.client('codepipeline')

def lambda_handler(event, context):
    """
    Pre-build validation: Check code quality before building
    """
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Run code quality checks
        result = subprocess.run(['npm', 'run', 'lint'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            raise Exception(f"Linting failed: {result.stderr}")
        
        # Validation passed
        codepipeline.put_job_success_result(jobId=job_id)
        return {
            'statusCode': 200,
            'body': json.dumps('Pre-build validation passed')
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        return {
            'statusCode': 500,
            'body': json.dumps(f'Validation failed: {str(e)}')
        }
```

### 2. Test Automation Lambda

```python
import json
import boto3
import requests
from datetime import datetime

codepipeline = boto3.client('codepipeline')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    Run integration tests after deployment
    """
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Get artifact location from pipeline
        artifacts = event['CodePipeline.job']['data']['inputArtifacts']
        
        # Run tests
        test_results = run_tests()
        
        # Put metric to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='CI/CD',
            MetricData=[
                {
                    'MetricName': 'TestsPassed',
                    'Value': test_results['passed'],
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'TestsFailed',
                    'Value': test_results['failed'],
                    'Unit': 'Count'
                }
            ]
        )
        
        if test_results['failed'] > 0:
            raise Exception(f"{test_results['failed']} tests failed")
        
        codepipeline.put_job_success_result(jobId=job_id)
        return {'statusCode': 200, 'body': 'Tests passed'}
        
    except Exception as e:
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        return {'statusCode': 500, 'body': str(e)}

def run_tests():
    """Run test suite"""
    # This would call your test runner
    return {'passed': 10, 'failed': 0}
```

### 3. Post-Deployment Validation Lambda

```python
import json
import boto3
import requests
import time

codepipeline = boto3.client('codepipeline')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Validate deployment: Check application health
    """
    job_id = event['CodePipeline.job']['id']
    
    try:
        # Get endpoint URL from Parameter Store
        api_url = ssm.get_parameter(
            Name='/app/api-endpoint'
        )['Parameter']['Value']
        
        # Wait for service to warm up
        time.sleep(10)
        
        # Run health checks
        health_status = validate_deployment(api_url)
        
        if not health_status['healthy']:
            raise Exception(f"Health check failed: {health_status['message']}")
        
        codepipeline.put_job_success_result(jobId=job_id)
        return {'statusCode': 200, 'body': 'Deployment validated'}
        
    except Exception as e:
        codepipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={'message': str(e), 'type': 'JobFailed'}
        )
        return {'statusCode': 500, 'body': str(e)}

def validate_deployment(api_url):
    """Check application health"""
    try:
        # Health endpoint
        response = requests.get(f"{api_url}/health", timeout=5)
        
        if response.status_code != 200:
            return {
                'healthy': False,
                'message': f'Health check returned {response.status_code}'
            }
        
        # API functionality check
        response = requests.get(f"{api_url}/api/status", timeout=5)
        
        if response.status_code != 200:
            return {
                'healthy': False,
                'message': f'API check returned {response.status_code}'
            }
        
        return {'healthy': True, 'message': 'All checks passed'}
        
    except Exception as e:
        return {'healthy': False, 'message': str(e)}
```

### 4. API Test Lambda (Canary)

```python
import json
import boto3
import requests
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    Canary test: Verify API functionality post-deployment
    """
    
    try:
        # Get endpoint from environment variable
        api_url = os.environ['API_ENDPOINT']
        
        # Run smoke tests
        tests = [
            test_auth_endpoint(api_url),
            test_data_endpoints(api_url),
            test_error_handling(api_url)
        ]
        
        failed_tests = [t for t in tests if not t['passed']]
        
        if failed_tests:
            raise Exception(f"{len(failed_tests)} tests failed")
        
        # Record success metric
        cloudwatch.put_metric_data(
            Namespace='Canary',
            MetricData=[{
                'MetricName': 'CanaryTest',
                'Value': 1,
                'Unit': 'Count'
            }]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('All canary tests passed!')
        }
        
    except Exception as e:
        # Record failure metric
        cloudwatch.put_metric_data(
            Namespace='Canary',
            MetricData=[{
                'MetricName': 'CanaryTestFailed',
                'Value': 1,
                'Unit': 'Count'
            }]
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Canary test failed: {str(e)}')
        }

def test_auth_endpoint(api_url):
    """Test authentication"""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            json={'email': 'test@example.com', 'password': 'test'},
            timeout=5
        )
        return {'passed': response.status_code == 200, 'test': 'auth'}
    except:
        return {'passed': False, 'test': 'auth'}

def test_data_endpoints(api_url):
    """Test data endpoints"""
    try:
        response = requests.get(f"{api_url}/api/data", timeout=5)
        return {'passed': response.status_code == 200, 'test': 'data'}
    except:
        return {'passed': False, 'test': 'data'}

def test_error_handling(api_url):
    """Test error handling"""
    try:
        response = requests.get(f"{api_url}/api/nonexistent", timeout=5)
        return {'passed': response.status_code == 404, 'test': 'errors'}
    except:
        return {'passed': False, 'test': 'errors'}
```

### 5. Automatic Rollback Lambda

```python
import json
import boto3
from datetime import datetime, timedelta

codedeploy = boto3.client('codedeploy')
cloudwatch = boto3.client('cloudwatch')
codepipeline = boto3.client('codepipeline')

def lambda_handler(event, context):
    """
    Monitor deployment and trigger rollback if needed
    """
    
    try:
        # Get deployment ID from CodeDeploy
        deployment_id = event.get('deployment_id')
        
        # Check error metrics
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='TargetResponseTime',
            Dimensions=[],
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )
        
        avg_response_time = metrics['Datapoints'][0]['Average'] if metrics['Datapoints'] else 0
        
        # Check error rate
        errors = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='HTTPCode_Target_5XX_Count',
            Dimensions=[],
            StartTime=datetime.utcnow() - timedelta(minutes=5),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Sum']
        )
        
        error_count = errors['Datapoints'][0]['Sum'] if errors['Datapoints'] else 0
        
        # Rollback criteria
        if error_count > 10 or avg_response_time > 5000:
            print(f"Rollback triggered: Errors={error_count}, Response Time={avg_response_time}ms")
            
            # Stop deployment
            codedeploy.stop_deployment(
                deploymentId=deployment_id,
                autoRollbackEnabled=True
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps('Rollback initiated')
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps('Deployment metrics are healthy')
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
```

### 6. Notification Lambda

```python
import json
import boto3
from datetime import datetime

sns = boto3.client('sns')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Send deployment notifications
    """
    
    # Get SNS topic from Parameter Store
    topic_arn = ssm.get_parameter(
        Name='/app/notifications/sns-topic'
    )['Parameter']['Value']
    
    # Format message based on event
    if event['source'] == 'aws.codepipeline':
        if event['detail']['state'] == 'SUCCEEDED':
            message = format_success_message(event)
        else:
            message = format_failure_message(event)
    
    # Send notification
    sns.publish(
        TopicArn=topic_arn,
        Subject=f"Deployment {event['detail']['state']}",
        Message=message
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent')
    }

def format_success_message(event):
    """Format success message"""
    return f"""
    Deployment Successful!
    
    Pipeline: {event['detail']['pipeline']}
    Execution ID: {event['detail']['execution-id']}
    Status: SUCCESS
    Time: {datetime.now().isoformat()}
    """

def format_failure_message(event):
    """Format failure message"""
    return f"""
    Deployment Failed!
    
    Pipeline: {event['detail']['pipeline']}
    Execution ID: {event['detail']['execution-id']}
    Status: FAILED
    Time: {datetime.now().isoformat()}
    
    Please review logs and take action.
    """
```

## Lambda Execution Role

### Lambda Execution Policy for CI/CD

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codepipeline:PutJobSuccessResult",
        "codepipeline:PutJobFailureResult"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::my-artifacts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/app/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codedeploy:StopDeployment"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:*"
    }
  ]
}
```

## Lambda Environment Variables

```python
import os

# Get from environment
api_endpoint = os.environ['API_ENDPOINT']
environment = os.environ['ENVIRONMENT']
database_url = os.environ['DATABASE_URL']

# Get from Parameter Store
ssm = boto3.client('ssm')
db_password = ssm.get_parameter(
    Name='/app/db/password',
    WithDecryption=True
)['Parameter']['Value']
```

## Integration with Pipeline

### Add Lambda as Pipeline Action

```json
{
  "name": "ValidateDeployment",
  "actionTypeId": {
    "category": "Invoke",
    "owner": "AWS",
    "provider": "Lambda",
    "version": "1"
  },
  "configuration": {
    "FunctionName": "validate-deployment-lambda",
    "UserParameters": "{\"environment\":\"production\"}"
  },
  "inputArtifacts": [
    {
      "name": "BuildOutput"
    }
  ]
}
```

## Lambda Deployment (ServerlessFramework)

```yaml
service: cicd-automation

provider:
  name: aws
  runtime: python3.9
  region: us-east-1
  iamRoleStatements:
    - Effect: Allow
      Action:
        - codepipeline:*
        - cloudwatch:*
      Resource: "*"

functions:
  validateDeployment:
    handler: handlers/validate.lambda_handler
    timeout: 60
    environment:
      API_ENDPOINT: ${ssm:/app/api-endpoint}
    
  runTests:
    handler: handlers/tests.lambda_handler
    timeout: 300
    memorySize: 512
    
  sendNotification:
    handler: handlers/notify.lambda_handler
    events:
      - eventBridge:
          pattern:
            source:
              - aws.codepipeline
            detail-type:
              - CodePipeline State Change

plugins:
  - serverless-python-requirements
```

## Best Practices

✅ Keep Lambda functions focused (single responsibility)
✅ Use environment variables for configuration
✅ Implement proper error handling
✅ Set appropriate timeouts
✅ Use CloudWatch for logging
✅ Implement retry logic
✅ Monitor function performance
✅ Secure sensitive data with Secrets Manager
✅ Test functions locally
✅ Document expected events

## Next Steps

1. Create Lambda functions for pipeline automation
2. Test functions locally
3. Add to CodePipeline
4. Monitor execution
5. Read [Advanced Topics](../08-Advanced/README.md)

## Summary

- **Lambda in CI/CD** = Automation and validation
- **Pre-Build** = Code quality checks
- **Testing** = Integration and smoke tests
- **Post-Deploy** = Health checks and validation
- **Notifications** = Pipeline status alerts
- **Rollback** = Automated failure response
- **Execution Role** = Fine-grained IAM permissions

---

**Next**: [Advanced Topics](../08-Advanced/README.md)
