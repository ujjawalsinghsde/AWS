# AWS CodePipeline - Orchestration

## What is AWS CodePipeline?

AWS CodePipeline is a fully-managed CI/CD orchestration service that:
- Automates entire workflow
- Connects all services (CodeCommit, CodeBuild, CodeDeploy)
- Manages approval gates
- Handles failure notifications
- Provides visibility into status
- Cost: $1 per pipeline per month

## Pipeline Architecture

```
Source (CodeCommit)
        ↓
Build (CodeBuild)
        ↓
Test (Lambda/CodeBuild)
        ↓
Approval (Manual Gate)
        ↓
Deploy Dev (CodeDeploy)
        ↓
Deploy Staging (CodeDeploy)
        ↓
Deploy Production (CodeDeploy)
```

## Pipeline Stages

### Stage 1: Source
Triggers on code changes
```yaml
- Provider: CodeCommit
- Repository: my-app
- Branch: main
- Change detection: CloudWatch Events
- Webhook: Automatic
```

### Stage 2: Build
Compiles and tests code
```yaml
- Provider: CodeBuild
- Project: my-app-build
- Input: Source artifacts
- Output: Build artifacts (S3)
```

### Stage 3: Test (Optional)
Runs automated tests
```yaml
- Provider: Lambda
- Function: test-function
- Input: Build artifacts
- Success/Failure response
```

### Stage 4: Approval (Optional)
Manual intervention
```yaml
- Provider: Manual
- Approvers: Team members
- Comments: Optional feedback
```

### Stage 5: Deploy
Deploys to target
```yaml
- Provider: CodeDeploy
- Application: my-app
- Deployment group: production
- Input: Build artifacts
```

## Creating Pipeline

### Using AWS Console

#### Step 1: Create Pipeline
1. Go to CodePipeline
2. Click "Create pipeline"
3. Pipeline name: my-app-pipeline
4. Service role: Create new role

#### Step 2: Add Source Stage
- Provider: AWS CodeCommit
- Repository: my-app
- Branch: main
- Change detection: Amazon CloudWatch Events

#### Step 3: Add Build Stage
- Provider: AWS CodeBuild
- Project: my-app-build
- Input artifacts: SourceOutput
- Output artifacts: BuildOutput

#### Step 4: Add Approval Stage (Optional)
- Action provider: Manual approval
- Comments optional: true

#### Step 5: Add Deploy Stage
- Provider: CodeDeploy
- Application: my-app
- Deployment group: production
- Input artifacts: BuildOutput

#### Step 6: Review and Create
- Review all settings
- Create pipeline

### Using AWS CLI

```bash
aws codepipeline create-pipeline \
    --cli-input-json file://pipeline.json
```

### pipeline.json Configuration

```json
{
  "pipeline": {
    "name": "my-app-pipeline",
    "roleArn": "arn:aws:iam::123456789:role/CodePipelineRole",
    "artifactStore": {
      "type": "S3",
      "location": "my-pipeline-artifacts"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [
          {
            "name": "GetSource",
            "actionTypeId": {
              "category": "Source",
              "owner": "AWS",
              "provider": "CodeCommit",
              "version": "1"
            },
            "settings": {
              "RepositoryName": "my-app",
              "BranchName": "main",
              "PollForSourceChanges": "false"
            },
            "outputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Build",
        "actions": [
          {
            "name": "Build",
            "actionTypeId": {
              "category": "Build",
              "owner": "AWS",
              "provider": "CodeBuild",
              "version": "1"
            },
            "inputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ],
            "outputArtifacts": [
              {
                "name": "BuildOutput"
              }
            ],
            "configuration": {
              "ProjectName": "my-app-build"
            }
          }
        ]
      },
      {
        "name": "Approval",
        "actions": [
          {
            "name": "ApprovalForProd",
            "actionTypeId": {
              "category": "Approval",
              "owner": "AWS",
              "provider": "Manual",
              "version": "1"
            },
            "configuration": {
              "CustomData": "Please review and approve deployment to production",
              "NotificationArn": "arn:aws:sns:us-east-1:123456789:approvals"
            }
          }
        ]
      },
      {
        "name": "Deploy",
        "actions": [
          {
            "name": "DeployToProd",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "CodeDeploy",
              "version": "1"
            },
            "inputArtifacts": [
              {
                "name": "BuildOutput"
              }
            ],
            "configuration": {
              "ApplicationName": "my-app",
              "DeploymentGroupName": "production"
            }
          }
        ]
      }
    ]
  }
}
```

## Service Role for CodePipeline

### CodePipelineRole Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-pipeline-artifacts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GetBranch",
        "codecommit:GetCommit",
        "codecommit:UploadArchive"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codebuild:BatchGetBuilds",
        "codebuild:BatchGetReports",
        "codebuild:StartBuild"
      ],
      "Resource": "arn:aws:codebuild:*:*:project/my-app-build"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codedeploy:CreateDeployment",
        "codedeploy:GetApplication",
        "codedeploy:GetApplicationRevision",
        "codedeploy:GetDeployment",
        "codedeploy:GetDeploymentConfig",
        "codedeploy:RegisterApplicationRevision"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*"
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

## Artifacts Management

### Artifact Store (S3)

```bash
# Create S3 bucket for artifacts
aws s3 mb s3://my-pipeline-artifacts --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket my-pipeline-artifacts \
    --versioning-configuration Status=Enabled

# Set lifecycle policy (90-day retention)
aws s3api put-bucket-lifecycle-configuration \
    --bucket my-pipeline-artifacts \
    --lifecycle-configuration '{
      "Rules": [
        {
          "Id": "DeleteOldArtifacts",
          "Status": "Enabled",
          "ExpirationInDays": 90
        }
      ]
    }'
```

### Artifact Passing Between Stages

```
Source Stage Output
        ↓ (SourceOutput artifact)
Build Stage Input
        ↓
Build Stage Output
        ↓ (BuildOutput artifact)
Test Stage Input
        ↓
Test Stage Output
        ↓ (TestOutput artifact)
Deploy Stage Input
```

Each stage passes outputs to next stage via S3.

## Approval Gates

### Manual Approval

#### Create Approval Action
```json
{
  "name": "ProductionApproval",
  "actionTypeId": {
    "category": "Approval",
    "owner": "AWS",
    "provider": "Manual",
    "version": "1"
  },
  "configuration": {
    "CustomData": "Review deployment details",
    "NotificationArn": "arn:aws:sns:us-east-1:123456789:approvals"
  }
}
```

#### SNS Notification Setup

```bash
# Create SNS topic
aws sns create-topic --name pipeline-approvals

# Subscribe to topic
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789:pipeline-approvals \
    --protocol email \
    --notification-endpoint your-email@example.com
```

#### Lambda-Based Approval

```javascript
exports.handler = async (event) => {
  const codepipeline = new AWS.CodePipeline();
  
  // Your approval logic
  const shouldApprove = true;
  
  if (shouldApprove) {
    await codepipeline.putJobSuccessResult({
      jobId: event['CodePipeline.job'].id
    }).promise();
  } else {
    await codepipeline.putJobFailureResult({
      jobId: event['CodePipeline.job'].id,
      failureDetails: {
        message: 'Approval logic failed',
        type: 'JobFailed'
      }
    }).promise();
  }
};
```

## Environment-Based Pipelines

### Development Pipeline
```
Code committed → Build → Deploy to Dev
```
(Automatic, frequent)

### Staging Pipeline
```
Code tagged → Build → Deploy to Staging → Run Integration Tests → Deploy to Staging (if tests pass)
```
(Manual trigger or scheduled)

### Production Pipeline
```
Code tagged → Build → Run Integration Tests → Manual Approval → Deploy to Production (Blue-Green)
```
(Approval required)

## Multi-Account Deployments

### Cross-Account Deployment

```json
{
  "name": "DeployToAnotherAccount",
  "actionTypeId": {
    "category": "Deploy",
    "owner": "AWS",
    "provider": "CodeDeploy",
    "version": "1"
  },
  "roleArn": "arn:aws:iam::OTHER-ACCOUNT:role/CrossAccountRole",
  "configuration": {
    "ApplicationName": "my-app",
    "DeploymentGroupName": "production"
  }
}
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
      "Action": "sts:AssumeRole",
      "Condition": {}
    }
  ]
}
```

## Pipeline Execution and Monitoring

### Trigger Pipeline Manually

```bash
aws codepipeline start-pipeline-execution \
    --name my-app-pipeline
```

### Monitor Pipeline Status

```bash
# Get pipeline status
aws codepipeline get-pipeline-state \
    --name my-app-pipeline

# Get pipeline execution history
aws codepipeline list-pipeline-executions \
    --pipeline-name my-app-pipeline \
    --max-results 10
```

### Get Execution Details

```bash
aws codepipeline get-pipeline-execution \
    --pipeline-name my-app-pipeline \
    --pipeline-execution-id execution-id
```

## Failure Handling

### Retry Failed Stage

```bash
aws codepipeline retry-stage-execution \
    --pipeline-name my-app-pipeline \
    --stage-name Build \
    --pipeline-execution-id execution-id \
    --retry-mode FAILED_ACTIONS
```

### Fail Forward with Approval

```json
{
  "actionTypeId": {
    "category": "Approval",
    "owner": "AWS",
    "provider": "Manual",
    "version": "1"
  },
  "configuration": {
    "CustomData": "Build failed. Review logs before proceeding?",
    "NotificationArn": "arn:aws:sns:..."
  },
  "onFailure": "CONTINUE"
}
```

## CloudWatch Events Trigger

### Create CloudWatch Rule for CodeCommit

```bash
aws events put-rule \
    --name codecommit-push-rule \
    --event-pattern '{
      "source": ["aws.codecommit"],
      "detail-type": ["CodeCommit Repository State Change"],
      "detail": {
        "referenceType": ["branch"],
        "referenceName": ["main"],
        "repositoryName": ["my-app"],
        "event": ["referenceCreated", "referenceUpdated"]
      }
    }' \
    --state ENABLED
```

### Add Pipeline as Target

```bash
aws events put-targets \
    --rule codecommit-push-rule \
    --targets Id=1,Arn=arn:aws:codepipeline:us-east-1:123456789:my-app-pipeline,RoleArn=arn:aws:iam::123456789:role/EventsRole
```

## Notifications

### SNS Topic for Pipeline Events

```bash
# Create topic
aws sns create-topic --name pipeline-notifications

# Create pipeline with SNS notifications
aws codepipeline update-pipeline \
    --cli-input-json file://pipeline-with-notifications.json
```

### EventBridge for Advanced Notifications

```json
{
  "Name": "PipelineNotifications",
  "EventPattern": {
    "source": ["aws.codepipeline"],
    "detail-type": ["CodePipeline Pipeline Execution State Change"],
    "detail": {
      "state": ["FAILED", "SUCCEEDED"]
    }
  },
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:lambda:...",
      "RoleArn": "arn:aws:iam::123456789:role/EventsRole"
    }
  ]
}
```

## Advanced Patterns

### Multi-Stage Deployment

```
Source → Build → Test → Approval → Deploy Dev → Test Dev → Deploy Staging → Test Staging → Manual Approval → Deploy Prod
```

### Parallel Deployments

```
Source → Build → Deploy Dev
               → Deploy Staging (parallel)
               → Deploy to Regions (parallel)
```

### Conditional Deployments

```
Source → Build → Test → Check Metrics → Deploy if metrics good
                                     → Skip if issues detected
```

## Pipeline Best Practices

✅ Use artifact versioning
✅ Implement approval gates for production
✅ Monitor pipeline execution
✅ Set up notifications
✅ Use CodePipeline events for automation
✅ Implement rollback procedures
✅ Test pipeline thoroughly
✅ Document deployment process
✅ Implement failure handling
✅ Monitor artifact storage costs

## Next Steps

1. Create CodePipeline
2. Add all stages (Source, Build, Test, Deploy)
3. Configure approval gates
4. Setup notifications
5. Test pipeline end-to-end
6. Read [Lambda Guide](../07-Lambda/README.md)

## Summary

- **CodePipeline** = Orchestration service
- **Stages** = Source → Build → Test → Deploy
- **Artifacts** = Passed between stages via S3
- **Approval Gates** = Manual intervention points
- **Service Roles** = Define permissions
- **Notifications** = SNS/EventBridge for alerts
- **Monitoring** = CloudWatch for metrics

---

**Next**: [Lambda Functions Guide](../07-Lambda/README.md)
