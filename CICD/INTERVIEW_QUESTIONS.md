# CICD Services Interview Questions (CodeCommit, CodeBuild, CodeDeploy, CodePipeline)

## 1. Fundamental Questions

### Basic Concepts

1. **What are AWS CICD services and the pipeline flow?**
   - CodeCommit: Source control (Git repositories)
   - CodeBuild: Build service (compile, test)
   - CodeDeploy: Deployment automation (EC2, on-premises)
   - CodePipeline: Orchestration (coordinates stages)
   - Flow: Commit → Build → Test → Deploy

2. **Explain CodeCommit.**
   - Managed Git repositories
   - Fully AWS-hosted, no self-managed servers
   - SSH and HTTPS access
   - IAM-based access control
   - Pull requests, branch protection
   - Integration with CodeBuild/CodePipeline

3. **What is CodeBuild and buildspec.yml?**
   - Build service (compile code, run tests, create artifacts)
   - Runs on Docker containers
   - buildspec.yml: Build instructions
   - Phases: pre_build, build, post_build
   - Artifacts: Output files (JAR, Docker image, etc)
   - Cache: Speed up builds with dependency cache

4. **Explain CodeDeploy.**
   - Automates code deployment to EC2, on-premises, Lambda
   - AppSpec file: Deployment instructions
   - Deployment groups: Target servers
   - Deployment strategies: All-at-once, rolling, canary, blue-green
   - Automatic rollback on failure

5. **What is CodePipeline?**
   - Orchestrates CICD workflow
   - Stages: Source → Build → Deploy → Approval
   - Triggers: CodeCommit push, recurring schedule
   - Manual approvals for quality gates
   - Integration with 3rd-party tools

---

## 2. Intermediate Scenarios

### Build & Deployment Strategies

6. **Scenario: Set up CICD for Node.js microservice.**
   - CodeCommit: Git repo for source
   - CodeBuild:
     - Install dependencies: `npm install`
     - Run tests: `npm test`
     - Build: `npm run build`
     - Create artifact: Zip code + node_modules
   - CodeDeploy:
     - Deploy to EC2 instances (Auto Scaling Group)
     - Post-deploy: Restart service
     - Health checks: Validate service health
   - CodePipeline:
     - Trigger: CodeCommit push
     - Stages: Build → Deploy staging → Manual Approval → Deploy prod

7. **Implement blue-green deployment strategy.**
   - Blue: Current production
   - Green: New version (offline)
   - Deployment: Update green to new version
   - Testing: Verify green works
   - Cutover: Switch traffic Blue → Green
   - Rollback: Simple (switch back to Blue)
   - Implementation:
     - Two Auto Scaling Groups
     - Load Balancer switches between them
     - CodeDeploy targets green first

8. **Implement canary deployment (progressive rollout).**
   - Phase 1: 5% traffic to new version
   - Monitoring: Error rate, latency
   - Phase 2: 25% traffic
   - Phase 3: 50%, then 100%
   - Rollback: If error rate > threshold
   - CodeDeploy canary configuration:
     - Interval: 5 minutes
     - Percentage: 5%, 25%, 50%, 100%

### Testing & Quality

9. **Scenario: Ensure code quality before production.**
   - Build phase:
     - Unit tests: `npm test`
     - Code quality: SonarQube integration
     - Dependency scan: npm audit
   - Approval stage:
     - QA manual testing (2 hours)
     - Approval gate: Manual approval required
   - Deploy phase:
     - Staging deployment
     - Integration testing
     - Production deployment

---

## 3. Advanced Scenarios

### Cross-Account & Multi-Region

10. **Design CICD for multi-region deployment.**
    - Source: CodeCommit in primary region
    - Build: CodeBuild in primary region
    - Artifact Storage: S3 bucket (replicated to other regions)
    - Deployment:
      - Pipeline stage 1: Deploy to region A
      - Pipeline stage 2: Deploy to region B
      - Pipeline stage 3: Deploy to region C
    - Parallel or sequential depending on requirements

11. **Implement secrets management in CI/CD.**
    - Problem: Don't hardcode API keys
    - Solution:
      - Secrets in Secrets Manager
      - buildspec.yml references secrets:
      ```
      phases:
        build:
          commands:
            - export API_KEY=$(aws secretsmanager get-secret-value --secret-id prod/api-key --query SecretString)
      ```
      - IAM role: Allows CodeBuild to access secrets
      - Docker build: Don't log secrets in build logs

### Artifacts & Caching

12. **Optimize build time with caching**
    - BuildCache mode: S3-based (persistent)
    - buildspec.yml:
    ```
    cache:
      paths:
        - /root/.npm/**/*
        - /root/.m2/**/*
    artifacts:
      files:
        - 'target/app.jar'
    ```
    - First build: Downloads dependencies (slow)
    - Subsequent builds: Uses cached dependencies (fast)

---

## 4. Real-World Scenarios

13. **Scenario: Deployment fails regularly. Troubleshoot.**
    - Check CodeBuild logs:
      - Compilation errors
      - Test failures
      - Missing dependencies
    - Check CodeDeploy:
      - Instance health checks failing
      - AppSpec syntax errors
      - Insufficient permissions
    - Solutions:
      - Local testing before commit
      - Pre-commit hooks for validation
      - Test in staging first

14. **Implement deployment safeguards.**
    - CodePipeline approval stages:
      - After staging deployment
      - Manual approval before production
    - Health checks:
      - CloudWatch metrics validation
      - If error rate spikes, halt pipeline
    - Timeout: If deployment takes too long, rollback
    - Slack notification: Alert on deployment status

15. **Design CICD for compliance (PCI-DSS, HIPAA).**
    - Audit trail:
      - CodeCommit: Who committed what
      - CodeBuild: What was built, artifacts
      - CodeDeploy: When deployed, to where
      - CloudTrail: All API calls
    - Approval gates:
      - Security review
      - Compliance check
      - Manual approval
    - Artifacts:
      - Signed artifacts
      - Immutable versions
      - Retention per compliance

---

## 5. Best Practices

16. **CICD best practices:**
    - Commit frequently (daily minimum)
    - Branch protection: Requires PR reviews
    - Automated testing: Fast feedback
    - Build cache: Reduce build time
    - Monitoring: Pipeline health dashboard
    - Rollback strategy: Easy recovery plan
    - Secrets: Use Secrets Manager, not environment variables
    - Versioning: Semantic versioning for releases

---

## 6. Hands-On Examples

17. **Write buildspec.yml for Node.js application:**
    ```yaml
    version: 0.2

    phases:
      install:
        runtime-versions:
          nodejs: 18
      pre_build:
        commands:
          - npm install
          - npm run lint
      build:
        commands:
          - npm test
          - npm run build
      post_build:
        commands:
          - zip -r app.zip . -x node_modules/\*
          - echo "Build completed on `date`"

    artifacts:
      files:
        - app.zip
      name: app-artifact

    cache:
      paths:
        - /root/.npm/**/*
    ```

18. **Write appspec.yml for CodeDeploy:**
    ```yaml
    version: 0.0
    Resources:
      - TargetService:
          Type: AWS::ECS::Service
          Properties:
            TaskDefinition: !Ref TaskDefinition
            LoadBalancerInfo:
              ContainerName: my-app
              ContainerPort: 3000
    Hooks:
      BeforeInstall:
        - Location: scripts/before-install.sh
          Timeout: 300
      AfterInstall:
        - Location: scripts/after-install.sh
          Timeout: 600
      ApplicationStart:
        - Location: scripts/start.sh
          Timeout: 300
      ApplicationStop:
        - Location: scripts/stop.sh
          Timeout: 300
    ```

19. **Lambda for CodePipeline approval notification:**
    ```python
    import boto3
    import json

    def lambda_handler(event, context):
        codepipeline = boto3.client('codepipeline')
        sns = boto3.client('sns')

        job_id = event['CodePipeline.job']['id']
        approval_token = event['CodePipeline.job']['data']['actionConfiguration']['configuration']['CustomData']

        # Send appr message
        message = {
            'job_id': job_id,
            'approval_url': f"https://console.aws.amazon.com/codesuite/..."
        }

        sns.publish(
            TopicArn='arn:aws:sns:region:account:approvals',
            Subject='Deployment Approval Required',
            Message=json.dumps(message)
        )

        codepipeline.put_job_success_result(jobId=job_id)
    ```

---

## Tips for Interview Success

- **Understand pipeline flow**: Source → Build → Deploy
- **Deployment strategies**: Blue-green vs canary vs rolling
- **AppSpec and buildspec**: Structure and phases
- **Automation**: Minimize manual steps
- **Testing integration**: Fast feedback loop
- **Rollback capability**: Always have recovery plan
- **Monitoring**: Track pipeline health
- **Secrets management**: Never hardcode credentials
- **Multi-region**: Design for global deployments

