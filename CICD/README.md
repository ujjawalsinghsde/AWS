# AWS CI/CD Deployment - Complete Guide

## Overview

This comprehensive guide covers the entire end-to-end CI/CD deployment pipeline using AWS services. From local development through production deployment, this documentation explains every service, role, configuration, and Lambda function required for a complete deployment workflow.

## Pipeline Architecture

```
Local Code Development
        ↓
   Git Push
        ↓
   CodeCommit (Repository)
        ↓
   CodePipeline (Orchestration)
        ├── Source Stage (CodeCommit)
        ├── Build Stage (CodeBuild)
        ├── Test Stage (Optional Lambda)
        ├── Deploy Stage (CodeDeploy)
        └── Post-Deploy (Lambda Validation)
        ↓
   Artifact Storage (S3)
        ↓
   CodeDeploy to Target
        ↓
   Lambda Functions (API Execution)
        ↓
   API Endpoints Live
```

## Directory Structure

### 1. **01-Basics/** - Foundational Concepts
   - Basic understanding of CI/CD
   - AWS service overview
   - Key terminology

### 2. **02-LocalSetup/** - Local Development Environment
   - Setting up local environment
   - Git configuration
   - AWS credentials setup
   - Local testing

### 3. **03-CodeCommit/** - Source Control
   - Repository creation
   - Branching strategies
   - Access control and IAM

### 4. **04-CodeBuild/** - Build Process
   - Build project creation
   - buildspec.yml configuration
   - Build artifacts
   - Service roles and permissions

### 5. **05-CodeDeploy/** - Deployment Configuration
   - Deployment groups
   - appspec.yml configuration
   - Deployment targets (EC2, On-premises, Lambda)
   - Rollback strategies

### 6. **06-CodePipeline/** - Pipeline Orchestration
   - Pipeline creation
   - Stage configuration
   - Approval gates
   - Manual and automated stages

### 7. **07-Lambda/** - Serverless Functions
   - Custom automation Lambda functions
   - Test automation
   - Post-deployment validation
   - API execution functions

### 8. **08-Advanced/** - Advanced Topics
   - Multi-account deployments
   - Blue-green deployments
   - Canary deployments
   - Monitoring and alerting
   - Cost optimization

### 9. **09-Examples/** - Real-World Examples
   - Complete working examples
   - Sample configurations
   - Terraform/CloudFormation templates

## Service Roles Required

### Key IAM Roles by Service

| Service | Role | Permissions |
|---------|------|-------------|
| **CodePipeline** | CodePipelineRole | Execute stages, cross-account access |
| **CodeBuild** | CodeBuildRole | Access to CodeCommit, S3, CloudWatch, ECR |
| **CodeDeploy** | CodeDeployRole | EC2 access, S3 artifact retrieval, SNS |
| **EC2 Instances** | EC2InstanceRole | Get artifacts, write logs, parameter store access |
| **Lambda** | LambdaExecutionRole | CloudWatch logs, custom policies per function |
| **CodeCommit** | IAMUserRole | Repository access, branch permissions |

## Getting Started

### Step 1: Basic Setup (Start Here)
```bash
# Read fundamentals
cd 01-Basics
# Follow the basic guide
```

### Step 2: Local Development
```bash
# Setup local environment
cd 02-LocalSetup
# Install AWS CLI, Git, configure credentials
```

### Step 3: Create Repository
```bash
# Create CodeCommit repository
cd 03-CodeCommit
# Follow repository setup guide
```

### Step 4: Configure Build
```bash
# Create CodeBuild project
cd 04-CodeBuild
# Configure buildspec.yml
```

### Step 5: Configure Deployment
```bash
# Create CodeDeploy application
cd 05-CodeDeploy
# Configure appspec.yml
```

### Step 6: Create Pipeline
```bash
# Create full pipeline
cd 06-CodePipeline
# Orchestrate all stages
```

### Step 7: Add Automation
```bash
# Create Lambda functions
cd 07-Lambda
# Add custom automation
```

### Step 8: Advanced Features
```bash
# Implement advanced features
cd 08-Advanced
# Blue-green, canary, monitoring
```

## Quick Reference: Service Permissions

### CodePipeline Service Role Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GetBranch",
        "codecommit:GetCommit",
        "codebuild:*",
        "codedeploy:*",
        "s3:*",
        "lambda:InvokeFunction",
        "sns:Publish"
      ],
      "Resource": "*"
    }
  ]
}
```

### CodeBuild Service Role Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "codecommit:GitPull",
        "s3:PutObject",
        "s3:GetObject",
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
```

## Lambda Functions in CI/CD

Lambda functions play crucial roles in CI/CD pipelines:

1. **Pre-Build Validation**: Validate code before build
2. **Custom Build Steps**: Execute custom logic during build
3. **Testing**: Run automated tests via CodeBuild
4. **Approval Functions**: Conditional deployments
5. **Post-Deploy Validation**: Verify deployment success
6. **API Endpoint Validation**: Test API functionality
7. **Rollback Automation**: Automatic rollback on failures
8. **Notifications**: Send deployment status updates

## Common Deployment Scenarios

### 1. Python API Deployment
```
Local Code → CodeCommit → CodeBuild (pip install, test, package)
  → S3 Artifact → CodeDeploy (EC2) → Flask/Gunicorn → Users
```

### 2. Python Lambda Deployment
```
Local Code → CodeCommit → CodeBuild (pip install, package)
  → S3 Artifact → CodeDeploy (Lambda update) → API Gateway → Users
```

### 3. Container Deployment (Python/Node.js)
```
Local Code → CodeCommit → CodeBuild (Docker build, ECR push)
  → CodeDeploy (ECS/EKS) → Load Balancer → APIs → Users
```

## Deployment Frequency & Duration

| Metric | Basic | Advanced |
|--------|-------|----------|
| Deployment Time | 5-10 minutes | 2-5 minutes |
| Rollback Time | 5-10 minutes | <1 minute |
| Deployment Frequency | Daily | Multiple times per day |
| Success Rate | 95%+ | 99%+ |

## Cost Optimization

- **CodeCommit**: $0 for 5 active users
- **CodeBuild**: $0.005 per build minute
- **CodeDeploy**: $0.02 per instance
- **CodePipeline**: $1 per pipeline per month
- **S3**: $0.023 per GB (artifacts storage)

## Troubleshooting Common Issues

See individual section READMEs for:
- CodeCommit access issues
- Build failures
- Deployment timeouts
- Lambda execution errors
- Permission denied errors

## Best Practices

1. ✅ Use separate environments (dev/staging/prod)
2. ✅ Implement approval gates for production
3. ✅ Keep build artifacts in S3 for 90 days
4. ✅ Enable CloudTrail for compliance
5. ✅ Use parameter stores for secrets
6. ✅ Implement proper rollback strategies
7. ✅ Monitor pipeline execution metrics
8. ✅ Regular backup of repositories

## Next Steps

1. Start with **01-Basics** folder
2. Follow sequential folders in order
3. Use **09-Examples** as reference
4. Implement **08-Advanced** features as needed

## Support & Resources

- AWS CodePipeline Docs: https://docs.aws.amazon.com/codepipeline/
- AWS CodeBuild Docs: https://docs.aws.amazon.com/codebuild/
- AWS CodeDeploy Docs: https://docs.aws.amazon.com/codedeploy/
- AWS IAM Best Practices: https://docs.aws.amazon.com/iam/

---

**Last Updated**: March 2026
**Version**: 1.0
