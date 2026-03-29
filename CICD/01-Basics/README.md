# CI/CD Basics - Foundations

## What is CI/CD?

### CI - Continuous Integration
- **Continuous** = Automatic, constant process
- **Integration** = Combining code from multiple developers
- Automatically test and validate code changes
- Catch bugs early in development
- Frequent integration (multiple times per day)

### CD - Continuous Deployment / Continuous Delivery
- **Continuous Deployment** = Automatic deployment to production
- **Continuous Delivery** = Ready for deployment, manual trigger
- Automate the release process
- Reduce manual intervention
- Fast, reliable deployments

## Why CI/CD?

| Benefit | Impact |
|---------|--------|
| **Reduced Risk** | Smaller changes, easier to identify issues |
| **Faster Delivery** | Automate manual processes |
| **Better Quality** | Automated testing catches bugs |
| **Reduced Costs** | Less manual work, fewer production issues |
| **Faster Feedback** | Developers know status immediately |
| **Increased Reliability** | Consistent deployment process |

## Traditional vs CI/CD Deployment

### Traditional Deployment
```
Developer writes code
        ↓
Manual testing (days/weeks)
        ↓
Ops team deploys (manual, error-prone)
        ↓
Issues discovered in production
        ↓
Hot fixes, rollbacks
        ↓
Takes hours or days to resolve
```

### CI/CD Deployment
```
Developer commits code
        ↓
Automated tests run (minutes)
        ↓
Build artifact created (automatic)
        ↓
Automated deployment (minutes)
        ↓
Automated validation (automatic)
        ↓
Issues caught before production
        ↓
Issues resolved in seconds/minutes
```

## AWS Services in CI/CD Pipeline

### **AWS CodeCommit** (Source Control)
- Git-based repository hosting
- Private repositories
- Branch management
- Pull request support

### **AWS CodeBuild** (Build Service)
- Compiles source code
- Runs tests
- Produces deployable artifacts
- Scales automatically

### **AWS CodeDeploy** (Deployment Service)
- Deploys to EC2, On-premises, Lambda
- Blue-green deployments
- Automatic rollback
- Application versioning

### **AWS CodePipeline** (Orchestration)
- Orchestrates entire workflow
- Connects all services
- Defines deployment stages
- Manages approvals

### **AWS S3** (Artifact Storage)
- Stores build artifacts
- Stores deployment packages
- Version control for artifacts
- Lifecycle management

### **AWS Lambda** (Serverless Functions)
- Custom automation in pipeline
- Testing functions
- Approval workflows
- Post-deployment validation
- API endpoints for applications

## Pipeline Flow Explained

### Stage 1: Source
```
Developer commits code
        ↓
CodeCommit receives commit
        ↓
Webhook triggers CodePipeline
        ↓
CodePipeline reads source
```

### Stage 2: Build
```
CodeBuild gets source code
        ↓
buildspec.yml defines build steps
        ↓
Compile, install dependencies
        ↓
Run tests and code analysis
        ↓
Create artifact (JAR, ZIP, Docker image)
        ↓
Upload to S3
```

### Stage 3: Test (Optional)
```
Lambda function triggered
        ↓
Download artifact from S3
        ↓
Run integration tests
        ↓
Return pass/fail status
```

### Stage 4: Approval (Optional)
```
Human approval gate
        ↓
Wait for manual approval
        ↓
Continue or abort
```

### Stage 5: Deploy
```
CodeDeploy triggered
        ↓
Get artifact from S3
        ↓
Stop current application
        ↓
Deploy new code
        ↓
Start application
        ↓
Health checks
```

### Stage 6: Validation (Optional)
```
Lambda function validates
        ↓
Run smoke tests
        ↓
Check API endpoints
        ↓
Verify application health
        ↓
Success or rollback
```

## Key Concepts

### Artifact
- Output of build process
- ZIP, JAR, Docker image, etc.
- Stored in S3
- Used for deployment

### Build Specification (buildspec.yml)
- YAML file defining build steps
- Install dependencies
- Compile code
- Run tests
- Create artifacts

### Deployment Specification (appspec.yml)
- YAML file defining deployment steps
- Stop application
- Copy files
- Install packages
- Start application
- Run validation scripts

### Service Roles
- IAM roles for AWS services
- Define permissions needed
- Principle of least privilege
- Separate role per service

### Rollback
- Ability to revert to previous version
- Automatic on failure
- Manual rollback available
- Minimum downtime

## Basic Workflow Example

### Scenario: Deploying Python Flask API

1. **Developer Commits Code**
   ```bash
   git add .
   git commit -m "Add new API endpoint"
   git push origin main
   ```

2. **CodeCommit Receives Push**
   - Webhook triggers CodePipeline
   - Notifies pipeline of code change

3. **CodeBuild Builds**
   - Runs `pip install -r requirements.txt`
   - Runs `pytest tests/`
   - Runs code quality checks (`flake8`)
   - Creates ZIP artifact with app code
   - Uploads to S3

4. **CodeDeploy Deploys**
   - Gets ZIP from S3
   - Stops Flask/Gunicorn service
   - Extracts files
   - Creates virtual environment
   - Runs `pip install -r requirements.txt` (prod)
   - Starts Flask with Gunicorn
   - Health checks pass

5. **Lambda Validates**
   - Calls API endpoints
   - Verifies responses
   - Checks database
   - Returns success status

6. **Pipeline Completes**
   - New version now live
   - Users access new features
   - Logs stored in CloudWatch

## Environment Levels

### Development Environment
- Multiple deployments per day
- Rapid feedback
- May have failures
- Less strict testing

### Staging Environment
- Near-production replica
- Full testing suite
- Approval gates
- Performance testing

### Production Environment
- Approval required
- Limited deployments
- Automated rollback
- Health monitoring
- Backup systems

## Service Roles Overview

| Role | Service | Purpose |
|------|---------|---------|
| **CodePipeline Role** | CodePipeline | Execute pipeline stages, invoke services |
| **CodeBuild Role** | CodeBuild | Access source, S3, CloudWatch |
| **CodeDeploy Role** | CodeDeploy | EC2 access, lifecycle events |
| **EC2 Instance Role** | EC2 | Get artifacts, send logs |
| **Lambda Execution Role** | Lambda | CloudWatch logs, custom permissions |

## Common Terms

| Term | Definition |
|------|-----------|
| **Commit** | Saving code changes with message |
| **Branch** | Isolated version of code |
| **Pull Request** | Code review before merging |
| **Pipeline** | Automated workflow from code to production |
| **Stage** | Step in pipeline (build, test, deploy) |
| **Artifact** | Output of build process |
| **Deployment** | Moving code to target environment |
| **Rollback** | Reverting to previous version |
| **Health Check** | Verify application is running correctly |
| **Green Environment** | Active production (receiving traffic) |
| **Blue Environment** | Previous production (available for rollback) |

## Next Steps

1. Read [Local Setup Guide](../02-LocalSetup/README.md)
2. Install AWS CLI and Git
3. Configure AWS credentials
4. Create IAM user with appropriate permissions

## Summary

- **CI/CD** = Continuous Integration and Continuous Deployment/Delivery
- **Benefits** = Faster delivery, higher quality, reduced risk
- **AWS Services** = CodeCommit, CodeBuild, CodeDeploy, CodePipeline, Lambda, S3
- **Pipeline** = Source → Build → Test → Approval → Deploy → Validate
- **Artifacts** = Build outputs stored in S3
- **Roles** = Each service needs IAM role with specific permissions
- **Automation** = Lambda functions for custom logic

---

**Next**: [Local Setup Guide](../02-LocalSetup/README.md)
