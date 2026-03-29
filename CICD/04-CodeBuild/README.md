# AWS CodeBuild - Build Service

## What is AWS CodeBuild?

AWS CodeBuild is a fully-managed build service that:
- Compiles source code
- Runs tests
- Produces deployable artifacts
- Scales automatically
- Integrates with CodePipeline
- Supports multiple languages/runtimes
- Uses custom Docker images
- Pay only for build minutes

## Key Features

| Feature | Benefit |
|---------|---------|
| **Managed Service** | No server management |
| **Compute Scaling** | Auto-scale based on load |
| **Language Support** | Node.js, Python, Java, Go, .NET, Ruby, PHP, Docker |
| **Caching** | Speed up builds with artifact caching |
| **Artifacts** | S3 integration for outputs |
| **Logs** | CloudWatch integration |
| **Cost** | $0.005 per build minute |
| **Docker Support** | Custom images for unique requirements |

## Build Process Flow

```
CodeCommit Push
        ↓
Webhook triggers CodeBuild
        ↓
Download source code
        ↓
Setup build environment (Docker container)
        ↓
Execute buildspec.yml phases:
  - install
  - pre_build
  - build
  - post_build
        ↓
Upload artifacts to S3
        ↓
Log output to CloudWatch
        ↓
Return success/failure
        ↓
Trigger next pipeline stage
```

## buildspec.yml - Build Configuration

### File Location
```
project-root/
├── buildspec.yml          # Build specification file
├── src/
├── tests/
└── package.json
```

### Basic Structure

```yaml
version: 0.2

# Optional: Override default Docker image
images:
  docker:
    - image_identifier:tag

phases:
  install:
    # Dependencies and tools
    commands:
      - echo "Installing dependencies"
      
  pre_build:
    # Build tasks before main build
    commands:
      - echo "Running tests"
      
  build:
    # Main build tasks
    commands:
      - echo "Building application"
      
  post_build:
    # Cleanup and finalization
    commands:
      - echo "Build complete"

artifacts:
  # Output files
  files:
    - output.zip
  
cache:
  # Speed up subsequent builds
  paths:
    - '/root/.npm/**/*'

reports:
  # Test reports
  test-reports:
    files:
      - 'test-results.json'
    file-format: 'JSON'

env:
  variables:
    ENVIRONMENT: production
  parameter-store:
    DB_PASSWORD: /prod/db/password
```

## buildspec.yml Examples

### Python Project

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo Installing Python dependencies...
      - apt-get update
      - apt-get install -y python3-pip
      - pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install pytest pytest-cov flake8
  
  pre_build:
    commands:
      - echo Running code quality checks...
      - flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
      - echo Running unit tests...
      - pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml
  
  build:
    commands:
      - echo Building Python application...
      - mkdir -p dist
      - cp -r src dist/
      - cp -r requirements.txt dist/
      - cd dist && zip -r ../application.zip . -x "*.pyc" "__pycache__/*"
      - cd ..
  
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Artifact ready for deployment

artifacts:
  files:
    - application.zip
  name: PythonArtifact
  discard-paths: no

reports:
  coverage-report:
    files:
      - coverage.xml
    file-format: COBERTURAXML
  
  test-report:
    files:
      - test-results.xml
    file-format: JUNITXML

cache:
  paths:
    - '/root/.cache/pip/**/*'

logs:
  cloudwatch:
    group-name: /aws/codebuild/my-app
    stream-name: python-build
```

### Node.js Project

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo Installing Node.js dependencies...
      - npm ci
  
  pre_build:
    commands:
      - echo Running linter...
      - npm run lint || true
      - echo Running tests...
      - npm test
  
  build:
    commands:
      - echo Building application...
      - npm run build
      - echo Creating deployment package...
      - zip -r application.zip . -x "node_modules/*" "tests/*" ".git/*" ".env*"
  
  post_build:
    commands:
      - echo Build completed on `date`

artifacts:
  files:
    - application.zip
  name: NodeJSArtifact

cache:
  paths:
    - '/root/.npm/**/*'

logs:
  cloudwatch:
    group-name: /aws/codebuild/my-app
    stream-name: nodejs-build
```

### Java Project

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo Installing Java dependencies...
      - apt-get update
      - apt-get install -y maven
  
  pre_build:
    commands:
      - echo Running unit tests...
      - mvn test
  
  build:
    commands:
      - echo Building Maven project...
      - mvn clean package -DskipTests
      - cp target/my-app.jar .
  
  post_build:
    commands:
      - echo Build completed

artifacts:
  files:
    - my-app.jar
    - appspec.yml
  name: JavaArtifact

cache:
  paths:
    - '/root/.m2/**/*'
```

### Docker Build

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/my-app
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG

images:
  - $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/my-app:latest
  - $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/my-app:$IMAGE_TAG
```

## Creating CodeBuild Project

### Using AWS Console

#### Step 1: Create Project
1. Go to CodeBuild
2. Click "Create build project"
3. Enter project name

#### Step 2: Source Configuration
- Source provider: AWS CodeCommit
- Repository: my-app
- Branch: main
- Webhook: Create webhook (optional)

#### Step 3: Environment
- Operating system: Amazon Linux 2
- Runtime: Node.js 18
- Runtime version: latest
- Image: Managed image
- Service role: Create new service role

#### Step 4: Buildspec
- Buildspec name: buildspec.yml
- Location: Repository root

#### Step 5: Artifacts
- Artifact type: S3
- Bucket: my-build-artifacts
- Artifact packaging: ZIP

#### Step 6: CloudWatch Logs
- Group name: /aws/codebuild/my-app
- Stream name: nodejs-build

### Using AWS CLI

```bash
aws codebuild create-project \
    --name my-app-build \
    --source type=CODECOMMIT,location=https://git-codecommit.us-east-1.amazonaws.com/v1/repos/my-app,gitCloneDepth=1 \
    --artifacts type=S3,location=my-build-artifacts \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux2-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role arn:aws:iam::123456789:role/CodeBuildRole
```

## Service Role and Permissions

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
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/codebuild/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GitPull"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-build-artifacts/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "arn:aws:ecr:*:*:repository/my-app"
    }
  ]
}
```

## Build Environment Variables

### Predefined Variables

| Variable | Value |
|----------|-------|
| `AWS_ACCOUNT_ID` | AWS account ID |
| `AWS_DEFAULT_REGION` | AWS region |
| `CODEBUILD_BUILD_ID` | Build ID |
| `CODEBUILD_BUILD_NUMBER` | Build sequence number |
| `CODEBUILD_SOURCE_VERSION` | Source version (branch/tag) |
| `CODEBUILD_SOURCE_REPO_URL` | Repository URL |
| `CODEBUILD_RESOLVED_SOURCE_VERSION` | Resolved commit SHA |
| `CODEBUILD_INITIATOR` | What triggered build |

### Custom Variables

#### In buildspec.yml
```yaml
env:
  variables:
    ENVIRONMENT: production
    LOG_LEVEL: debug
    
  parameter-store:
    DB_PASSWORD: /prod/db/password
    API_KEY: /prod/api/key
    
  secrets-manager:
    DOCKER_HUB_TOKEN: dockerhub:token
    GITHUB_PAT: github:personal-access-token
```

#### In AWS Console
1. Go to project settings
2. Environment → Additional configuration
3. Add variables

## Artifact Management

### Artifact Output

```yaml
artifacts:
  files:
    - application.zip
    - config.json
    - src/**/*
  
  name: MyArtifact
  
  # For multiple artifact sets
  secondary-artifacts:
    artifact-set-1:
      files:
        - file1.txt
      name: ArtifactOne
    artifact-set-2:
      files:
        - file2.txt
      name: ArtifactTwo
```

### S3 Artifact Storage

```bash
# Store artifacts with versioning
aws s3api put-bucket-versioning \
    --bucket my-build-artifacts \
    --versioning-configuration Status=Enabled

# Lifecycle policy: Keep for 90 days
aws s3api put-bucket-lifecycle-configuration \
    --bucket my-build-artifacts \
    --lifecycle-configuration '{
      "Rules": [
        {
          "Id": "DeleteOldArtifacts",
          "Status": "Enabled",
          "Expiration": {
            "Days": 90
          }
        }
      ]
    }'
```

## Build Cache for Performance

### Cache Configuration

```yaml
cache:
  paths:
    # Node.js
    - '/root/.npm/**/*'
    - '/root/.cache/**/*'
    
    # Python
    - '/root/.cache/pip/**/*'
    
    # Maven
    - '/root/.m2/**/*'
    
    # Custom paths
    - 'node_modules/**/*'
```

### Cache Benefits

- ⚡ Reduces build time by 50-80%
- 💰 Saves cost on build minutes
- 🚀 Faster feedback to developers
- 📦 Caches dependencies between builds

## Running Builds

### Trigger Build

```bash
# Start build manually
aws codebuild start-build --project-name my-app-build

# With specific source version
aws codebuild start-build \
    --project-name my-app-build \
    --source-version feature/new-feature

# With environment variables
aws codebuild start-build \
    --project-name my-app-build \
    --environment-variables name=ENVIRONMENT,value=staging,type=PLAINTEXT
```

### Monitor Build

```bash
# Get build info
aws codebuild batch-get-builds --ids build-id

# Get build logs
aws logs tail /aws/codebuild/my-app --follow

# List recent builds
aws codebuild list-builds-for-project --project-name my-app-build
```

## Test Reports

### JUnit XML Format

```yaml
reports:
  junit-report:
    files:
      - 'reports/test-results.xml'
    file-format: 'JUNITXML'
```

### Cobertura Coverage Format

```yaml
reports:
  coverage-report:
    files:
      - 'coverage/coverage.xml'
    file-format: 'COBERTURAXML'
```

### Custom Report

```yaml
reports:
  custom-report:
    files:
      - 'reports/custom-report.json'
    file-format: 'JSON'
```

## Troubleshooting Build Failures

### Common Issues

#### 1. Dependencies Not Found
```bash
# Add package manager update
phases:
  install:
    commands:
      - apt-get update
      - apt-get install -y [package]
```

#### 2. Out of Memory
```yaml
# Increase compute type
environment:
  compute-type: BUILD_GENERAL1_LARGE
```

#### 3. Timeout
```yaml
# Increase timeout
timeout-in-minutes: 60
```

#### 4. Permission Denied S3
```json
{
  "Effect": "Allow",
  "Action": ["s3:*"],
  "Resource": "arn:aws:s3:::my-build-artifacts/*"
}
```

### View Build Logs

```bash
# CloudWatch Logs
aws logs tail /aws/codebuild/my-app --follow

# Get last 100 lines
aws logs tail /aws/codebuild/my-app --max-items 100
```

## Advanced Build Options

### Local Build Testing

```bash
# Download CodeBuild agent
git clone https://github.com/aws/aws-codebuild-docker-images.git

# Run build locally
docker run -it \
  -v ~/.aws:/root/.aws \
  -v $(pwd):/tmp/input \
  -e CODEBUILD_BUILD_ID=test \
  aws/codebuild/amazonlinux2-x86_64-standard:5.0 \
  /bin/bash
```

### Matrix Builds

```yaml
# Test against multiple Node versions
matrix:
  dynamic:
    NODE_VERSION:
      - "16"
      - "18"
      - "20"
```

## Cost Optimization

- ✅ Use caching to reduce build time
- ✅ Choose appropriate compute type
- ✅ Use spot instances for non-critical builds
- ✅ Clean up old artifacts from S3
- ✅ Set build timeouts appropriately

## Best Practices

✅ Keep buildspec.yml in repository
✅ Use environment variables for configuration
✅ Cache dependencies
✅ Run tests in build phase
✅ Generate artifacts consistently
✅ Monitor build times and optimize
✅ Implement failure notifications
✅ Document custom build steps

## Next Steps

1. Create buildspec.yml
2. Create CodeBuild project
3. Test build locally
4. Integrate with CodePipeline
5. Read [CodeDeploy Guide](../05-CodeDeploy/README.md)

## Summary

- **CodeBuild** = Build and test service
- **buildspec.yml** = Build configuration
- **Artifacts** = Build outputs (S3)
- **Environment** = Docker container for builds
- **Service Role** = IAM permissions
- **Caching** = Performance optimization
- **Reports** = Test and coverage reports

---

**Next**: [CodeDeploy Guide](../05-CodeDeploy/README.md)
