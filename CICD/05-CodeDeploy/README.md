# AWS CodeDeploy - Application Deployment

## What is AWS CodeDeploy?

AWS CodeDeploy automates application deployments to:
- Amazon EC2 instances
- On-premises servers
- AWS Lambda functions
- Features:
  - Blue-green deployments
  - In-place deployments
  - Automatic rollback
  - Traffic control
  - Health monitoring
  - Supports multiple languages

## Deployment Types

### 1. In-Place Deployment
```
Old Version Running
        ↓
Stop application
        ↓
Deploy new version
        ↓
Start application
        ↓
Brief downtime
```

**Pros**: Simple, cost-effective
**Cons**: Downtime, risky rollback

### 2. Blue-Green Deployment
```
Blue (Current)          Green (New)
Version 1 running       Version 2 waiting
100% traffic            0% traffic
        ↓ Traffic switch ↓
        ← Instant switch
        ↓
Green (Current)         Blue (Standby)
Version 2 running       Version 1 ready
100% traffic            0% traffic
```

**Pros**: Zero downtime, quick rollback
**Cons**: Twice the resources, complexity

### 3. Canary Deployment
```
Version 1: 95% traffic
Version 2: 5% traffic (testing)
        ↓ Monitor metrics ↓
        ↓ If good, shift more traffic ↓
Version 1: 50% traffic
Version 2: 50% traffic
        ↓ If still good ↓
Version 1: 0% traffic
Version 2: 100% traffic
```

**Pros**: Safe rollout, quick rollback
**Cons**: Complex, slow rollout

## appspec.yml - Deployment Specification

### File Location
```
project-root/
├── appspec.yml                # Deployment specification
├── scripts/                   # Deployment lifecycle scripts
│   ├── install-dependencies.sh
│   ├── start-server.sh
│   └── stop-server.sh
├── src/
└── package.json
```

### Basic Structure for EC2

```yaml
version: 0.0
os: linux

Resources:
  - TargetService:
      Type: AWS::Lambda::Function
      Properties:
        Name: !Ref LambdaFunctionName
        Alias: live
        Port: 3000

Files:
  - source: /
    destination: /opt/my-app

Hooks:
  ApplicationStop:
    - Location: scripts/stop-server.sh
      Timeout: 300
      
  BeforeInstall:
    - Location: scripts/install-dependencies.sh
      Timeout: 300
      
  ApplicationStart:
    - Location: scripts/start-server.sh
      Timeout: 300
      
  ValidateService:
    - Location: scripts/validate-service.sh
      Timeout: 300
```

### Basic Structure for Lambda

```yaml
version: 0.0

Resources:
  - MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: !Ref LambdaFunctionName
        Alias: live
        CurrentVersion: !Ref LambdaFunctionVersion
        TargetVersion: !Ref LambdaFunctionVersion

Hooks:
  BeforeAllowTraffic:
    - Location: tests/pre-traffic.js
      
  AfterAllowTraffic:
    - Location: tests/post-traffic.js
```

## Deployment Lifecycle

### Lifecycle Events (EC2/On-Premises)

```
Deployment Start
        ↓
ApplicationStop ← Stop application
        ↓
BeforeInstall ← Install dependencies
        ↓
AfterInstall ← Post-installation setup
        ↓
ApplicationStart ← Start application
        ↓
ValidateService ← Verify deployment
        ↓
Deployment Complete
```

### Lifecycle Events (Lambda)

```
Target Group 1 (Old Version)
        ↓
BeforeAllowTraffic
        ↓ Test new version
        ↓
Target Group 2 (New Version)
        ↓
Traffic shifts
        ↓
AfterAllowTraffic
        ↓ Verify new version
        ↓
Complete
```

## appspec.yml Examples

### Node.js Server Deployment

```yaml
version: 0.0
os: linux

Resources:
  - NodeApp:
      Type: AWS::EC2::Instance
      Properties:
        Name: MyNodeApp
        Port: 3000

Files:
  - source: /
    destination: /opt/node-app

Hooks:
  ApplicationStop:
    - Location: scripts/stop-server.sh
      Timeout: 300
      RunAs: root
      
  BeforeInstall:
    - Location: scripts/install-dependencies.sh
      Timeout: 600
      RunAs: root
      
  AfterInstall:
    - Location: scripts/after-install.sh
      Timeout: 300
      RunAs: ubuntu
      
  ApplicationStart:
    - Location: scripts/start-server.sh
      Timeout: 300
      RunAs: ubuntu
      
  ValidateService:
    - Location: scripts/validate-service.sh
      Timeout: 300
      RunAs: ubuntu

Permissions:
  - object: /opt/node-app
    owner: ubuntu
    group: ubuntu
    mode: 755
    type:
      - directory
  - object: /opt/node-app
    owner: ubuntu
    group: ubuntu
    mode: 644
    type:
      - file

EventTriggers:
  - DeploymentSuccess
  - DeploymentFailure
```

### Python Flask Deployment

```yaml
version: 0.0
os: linux

Resources:
  - FlaskApp:
      Type: AWS::EC2::Instance
      Properties:
        Name: MyFlaskApp
        Port: 5000

Files:
  - source: /
    destination: /opt/flask-app

Hooks:
  ApplicationStop:
    - Location: scripts/stop-app.sh
      Timeout: 300
      
  BeforeInstall:
    - Location: scripts/before-install.sh
      Timeout: 600
      
  ApplicationStart:
    - Location: scripts/start-app.sh
      Timeout: 300
      
  ValidateService:
    - Location: scripts/validate-app.sh
      Timeout: 300

Permissions:
  - object: /opt/flask-app
    owner: ec2-user
    group: ec2-user
    mode: 755
    type:
      - directory
```

### Lambda Deployment with Canary

```yaml
version: 0.0

Resources:
  - MyLambdaFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: my-api-function
        Alias: live
        CurrentVersion: !Ref LambdaVersion1
        TargetVersion: !Ref LambdaVersion2

Hooks:
  BeforeAllowTraffic:
    - Location: hooks/pre-traffic.js
      
  AfterAllowTraffic:
    - Location: hooks/post-traffic.js

TriggerEvents:
  DeploymentSuccess:
    - SNS-Topic-Name: my-success-topic
  DeploymentFailure:
    - SNS-Topic-Name: my-failure-topic
```

## Lifecycle Scripts

### Stop Server Script (stop-server.sh)

```bash
#!/bin/bash
set -e

echo "Stopping Node.js server..."

# Kill existing process
if [ -f /opt/node-app/pid.txt ]; then
    kill $(cat /opt/node-app/pid.txt) 2>/dev/null || true
fi

# Or using PM2
pm2 delete my-app 2>/dev/null || true

# Or using systemd
systemctl stop node-app.service || true

echo "Server stopped successfully"
exit 0
```

### Install Dependencies Script (install-dependencies.sh)

```bash
#!/bin/bash
set -e

echo "Installing dependencies..."

cd /opt/node-app

# Update system packages
apt-get update
apt-get install -y curl build-essential

# Install Node.js (if not already installed)
if ! command -v npm &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    apt-get install -y nodejs
fi

# Install npm dependencies
npm ci  # Use ci instead of install for CI/CD

# Install global tools if needed
npm install -g pm2

echo "Dependencies installed successfully"
exit 0
```

### Start Server Script (start-server.sh)

```bash
#!/bin/bash
set -e

echo "Starting Node.js server..."

cd /opt/node-app

# Export environment variables
export NODE_ENV=production
export PORT=3000

# Start application using PM2
pm2 start npm --name my-app -- start
pm2 save

# Save PID
echo $! > /opt/node-app/pid.txt

echo "Server started successfully"
exit 0
```

### Validate Service Script (validate-service.sh)

```bash
#!/bin/bash
set -e

echo "Validating service..."

# Wait for service to be available
sleep 5

# Check if server is running
if ! curl -f http://localhost:3000/health; then
    echo "Health check failed"
    exit 1
fi

# Check if specific endpoint works
RESPONSE=$(curl -s http://localhost:3000/api/status)

if [[ $RESPONSE == *"ok"* ]]; then
    echo "Service validation successful"
    exit 0
else
    echo "Service validation failed"
    exit 1
fi
```

## Creating CodeDeploy Application

### Using AWS Console

#### Step 1: Create Application
1. Go to CodeDeploy
2. Click "Applications"
3. Click "Create application"
4. Application name: my-app
5. Compute platform: EC2/On-premises or Lambda

#### Step 2: Create Deployment Group
1. Go to application
2. Click "Create deployment group"
3. Enter group name: production
4. Service role: CodeDeployRole
5. Deployment type: Blue/green or In-place
6. Environment: EC2 instances or On-premises servers
7. Deployment configuration: CodeDeployDefault.OneAtATime

#### Step 3: Configure Deployment
- Auto rollback: Enabled
- Trigger: CodePipeline
- On-premises instances: Agent installation

### Using AWS CLI

```bash
# Create application
aws deploy create-app --application-name my-app

# Create deployment group
aws deploy create-deployment-group \
    --application-name my-app \
    --deployment-group-name production \
    --deployment-config-name CodeDeployDefault.OneAtATime \
    --service-role-arn arn:aws:iam::123456789:role/CodeDeployRole \
    --ec2-tag-filters Key=Environment,Value=production,Type=KEY_AND_VALUE
```

## Service Role for CodeDeploy

### CodeDeploy Service Role Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:*",
        "elasticloadbalancing:*",
        "ec2:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### EC2 Instance Role Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-artifacts/*",
        "arn:aws:s3:::my-artifacts"
      ]
    },
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
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/app/*"
    }
  ]
}
```

## Deployment Configuration

### Predefined Configurations

| Configuration | Behavior |
|--------------|----------|
| **OneAtATime** | Deploy to one instance at a time |
| **HalfAtATime** | Deploy to half of instances |
| **AllAtOnce** | Deploy to all instances simultaneously |

### Traffic Control (Canary)

```json
{
  "linear": {
    "linearPercentage": 10,
    "linearDuration": 10
  }
}
```
Shifts 10% traffic every 10 minutes.

```json
{
  "canary": {
    "canaryPercentage": 5,
    "canaryDuration": 30
  }
}
```
Tests 5% for 30 minutes before full shift.

## Automatic Rollback

```bash
# Enable auto-rollback
aws deploy create-deployment-group \
    --auto-rollback-configuration '[
      "DEPLOYMENT_FAILURE",
      "DEPLOYMENT_STOP_ON_ALARM"
    ]' \
    --alarms '[
      {
        "name": "HighErrorRate"
      }
    ]'
```

## Lambda Deployment with Validation

### Pre-Traffic Test (pre-traffic.js)

```javascript
const AWS = require('aws-sdk');
const lambda = new AWS.Lambda();

exports.handler = async (event) => {
  console.log('Running pre-traffic tests...');
  
  const functionName = event.currentFunctionVersion;
  
  try {
    // Invoke new version
    const result = await lambda.invoke({
      FunctionName: functionName,
      Payload: JSON.stringify({
        test: true,
        endpoint: '/health'
      })
    }).promise();
    
    const response = JSON.parse(result.Payload);
    
    if (response.statusCode === 200) {
      console.log('Pre-traffic tests passed');
      return {
        statusCode: 200,
        body: 'Pre-traffic tests passed'
      };
    } else {
      throw new Error('Health check failed');
    }
  } catch (error) {
    console.error('Pre-traffic tests failed:', error);
    throw error;
  }
};
```

### Post-Traffic Test (post-traffic.js)

```javascript
const AWS = require('aws-sdk');
const lambda = new AWS.Lambda();
const cloudwatch = new AWS.CloudWatch();

exports.handler = async (event) => {
  console.log('Running post-traffic tests...');
  
  try {
    // Check CloudWatch metrics
    const metrics = await cloudwatch.getMetricStatistics({
      Namespace: 'AWS/Lambda',
      MetricName: 'Errors',
      Dimensions: [
        { Name: 'FunctionName', Value: event.currentFunctionVersion }
      ],
      StartTime: new Date(Date.now() - 5 * 60000),
      EndTime: new Date(),
      Period: 300,
      Statistics: ['Sum']
    }).promise();
    
    const errorCount = metrics.Datapoints.reduce((sum, dp) => sum + dp.Sum, 0);
    
    if (errorCount === 0) {
      console.log('Post-traffic tests passed');
      return {
        statusCode: 200,
        body: 'Post-traffic tests passed'
      };
    } else {
      throw new Error(`${errorCount} errors detected during deployment`);
    }
  } catch (error) {
    console.error('Post-traffic tests failed:', error);
    throw error;
  }
};
```

## Health Checks

### Application Health Check (Elastic Load Balancer)

```bash
aws elbv2 modify-target-group \
    --target-group-arn arn:aws:elasticloadbalancing:... \
    --health-check-enabled \
    --health-check-protocol HTTP \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --matcher HttpCode=200
```

### CloudWatch Alarms for Auto-Rollback

```bash
aws deploy create-deployment-group \
    --alarm-configuration '[
      {
        "name": "HighErrorRate",
        "enabled": true
      },
      {
        "name": "HighCPU",
        "enabled": true
      }
    ]'
```

## Troubleshooting Deployments

### Common Issues

1. **Agent Not Running**
   ```bash
   # Check CodeDeploy agent status
   sudo systemctl status codedeploy-agent
   
   # Start agent
   sudo systemctl start codedeploy-agent
   
   # View logs
   sudo tail -f /var/log/codedeploy-agent/codedeploy-agent.log
   ```

2. **Insufficient Permissions**
   - Check S3 artifact access
   - Verify IAM role attached to EC2
   - Check CodeDeploy service role

3. **Script Failures**
   - View deployment logs in CodeDeploy console
   - Check script permissions
   - Verify dependencies are installed

4. **Timeout**
   - Increase timeout in appspec.yml
   - Check script execution time
   - Add health check delays

## Best Practices

✅ Test deployment scripts locally first
✅ Use blue-green for critical services
✅ Implement health checks
✅ Enable automatic rollback
✅ Start with canary deployments
✅ Log all deployment steps
✅ Monitor during deployment
✅ Keep appspec.yml in repository

## Next Steps

1. Create appspec.yml
2. Create lifecycle scripts
3. Create CodeDeploy application
4. Create deployment group
5. Test deployment
6. Read [CodePipeline Guide](../06-CodePipeline/README.md)

## Summary

- **CodeDeploy** = Automated deployment service
- **appspec.yml** = Deployment configuration
- **Lifecycle Hooks** = Custom scripts at deployment stages
- **Deployment Types** = In-place, Blue-green, Canary
- **Health Checks** = Verify service is running
- **Rollback** = Automatic on failure

---

**Next**: [CodePipeline Guide](../06-CodePipeline/README.md)
