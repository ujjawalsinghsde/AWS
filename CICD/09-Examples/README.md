# CI/CD Examples - Complete Implementations

## Example 1: Python Flask API Deployment

### Project Structure
```
my-api/
├── src/
│   ├── app.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py
│   ├── models/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── buildspec.yml
├── appspec.yml
├── scripts/
│   ├── install-dependencies.sh
│   ├── start-server.sh
│   ├── stop-server.sh
│   └── validate-service.sh
├── requirements.txt
├── wsgi.py
└── README.md
```

### buildspec.yml

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo "Installing Python dependencies..."
      - apt-get update
      - apt-get install -y python3-pip python3-venv
      - pip install --upgrade pip
      - pip install -r requirements.txt
      - pip install pytest pytest-cov flake8
  
  pre_build:
    commands:
      - echo "Running code quality checks..."
      - flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
      - echo "Running tests..."
      - pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml
  
  build:
    commands:
      - echo "Building Python application..."
      - mkdir -p dist
      - cp -r src dist/
      - cp -r requirements.txt dist/
      - cp wsgi.py dist/
      - cd dist && zip -r ../application.zip . -x "*.pyc" "__pycache__/*"
  
  post_build:
    commands:
      - echo "Build completed on `date`"

artifacts:
  files:
    - application.zip
  name: PythonAPIArtifact

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
```

### appspec.yml

```yaml
version: 0.0
os: linux

Resources:
  - PythonApp:
      Type: AWS::EC2::Instance
      Properties:
        Name: my-api
        Port: 5000

Files:
  - source: /
    destination: /opt/my-api

Hooks:
  ApplicationStop:
    - Location: scripts/stop-server.sh
      Timeout: 300
      
  BeforeInstall:
    - Location: scripts/install-dependencies.sh
      Timeout: 600
      
  ApplicationStart:
    - Location: scripts/start-server.sh
      Timeout: 300
      
  ValidateService:
    - Location: scripts/validate-service.sh
      Timeout: 300

Permissions:
  - object: /opt/my-api
    owner: ec2-user
    group: ec2-user
    type:
      - directory
```

### requirements.txt

```
Flask==2.3.0
Flask-CORS==4.0.0
Gunicorn==21.0.0
python-dotenv==1.0.0
boto3==1.26.0
requests==2.31.0
```

### src/app.py

```python
from flask import Flask, jsonify
from flask_cors import CORS
import logging
from routes.api import api_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'my-api'})
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({'message': 'Python API running'})
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### src/routes/api.py

```python
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get API status"""
    return jsonify({'status': 'ok', 'version': '1.0.0'})

@api_bp.route('/data', methods=['GET'])
def get_data():
    """Get data endpoint"""
    return jsonify({
        'message': 'Data retrieved successfully',
        'data': [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
    })

@api_bp.route('/echo', methods=['POST'])
def echo_data():
    """Echo back posted data"""
    try:
        data = request.get_json()
        return jsonify({
            'message': 'Data echoed',
            'received': data
        })
    except Exception as e:
        logger.error(f"Echo error: {str(e)}")
        return jsonify({'error': 'Invalid JSON'}), 400
```

### wsgi.py

```python
import os
from src.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
```

### scripts/stop-server.sh

```bash
#!/bin/bash
set -e

echo "Stopping Python Flask server..."

# Kill gunicorn process
pkill -f "gunicorn" || true

# Or stop systemd service if running
systemctl stop my-api || true

echo "Server stopped"
exit 0
```

### scripts/install-dependencies.sh

```bash
#!/bin/bash
set -e

echo "Installing dependencies..."

cd /opt/my-api

# Install system packages
apt-get update
apt-get install -y python3-pip python3-venv curl

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn

echo "Dependencies installed"
exit 0
```

### scripts/start-server.sh

```bash
#!/bin/bash
set -e

echo "Starting Python Flask server..."

cd /opt/my-api

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_ENV=production
export FLASK_APP=wsgi.py
export PORT=5000

# Start gunicorn
gunicorn --workers 4 \
         --worker-class sync \
         --bind 0.0.0.0:5000 \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         wsgi:app &

# Save PID
echo $! > /opt/my-api/app.pid

# Wait for server to start
sleep 5

echo "Server started"
exit 0
```

### scripts/validate-service.sh

```bash
#!/bin/bash
set -e

echo "Validating service..."

sleep 5

# Health check
if ! curl -f http://localhost:5000/health; then
    echo "Health check failed"
    exit 1
fi

# API status check
RESPONSE=$(curl -s http://localhost:5000/api/status)
if [[ $RESPONSE == *"ok"* ]]; then
    echo "Status check passed"
else
    echo "Status check failed"
    exit 1
fi

# API data check
DATA_RESPONSE=$(curl -s http://localhost:5000/api/data)
if [[ $DATA_RESPONSE == *"Data retrieved"* ]]; then
    echo "Data endpoint working"
else
    echo "Data endpoint failed"
    exit 1
fi

echo "Validation successful"
exit 0
```

### tests/test_api.py

```python
import pytest
from src.app import create_app
import json

@pytest.fixture
def app():
    """Create application for tests"""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_health_check(client):
    """Test health endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_api_status(client):
    """Test API status endpoint"""
    response = client.get('/api/status')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_get_data(client):
    """Test data retrieval"""
    response = client.get('/api/data')
    assert response.status_code == 200
    assert 'data' in response.json
    assert len(response.json['data']) > 0

def test_echo_endpoint(client):
    """Test echo endpoint"""
    test_data = {'message': 'test'}
    response = client.post('/api/echo',
                          data=json.dumps(test_data),
                          content_type='application/json')
    assert response.status_code == 200
    assert response.json['received'] == test_data

def test_not_found(client):
    """Test 404 handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
```

## Example 2: Python Lambda Deployment

### Project Structure
```
my-lambda/
├── handlers/
│   ├── __init__.py
│   └── index.py
├── tests/
│   └── test_handler.py
├── buildspec.yml
├── appspec.yml
├── requirements.txt
└── serverless.yml
```

### buildspec.yml

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo "Installing Python dependencies..."
      - pip install -r requirements.txt
      - pip install pytest pytest-cov
  
  pre_build:
    commands:
      - echo "Running tests..."
      - pytest tests/ --cov=handlers --cov-report=xml
  
  build:
    commands:
      - echo "Building Lambda package..."
      - mkdir package
      - cp -r handlers package/
      - cp -r . package/ -x "tests/*"
      - cd package && zip -r ../lambda.zip .
  
  post_build:
    commands:
      - echo "Build completed"

artifacts:
  files:
    - lambda.zip
  name: PythonLambdaArtifact

reports:
  coverage:
    files:
      - coverage.xml
    file-format: COBERTURAXML
```

### appspec.yml (Lambda)

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
    - Location: hooks/pre-traffic.py
      
  AfterAllowTraffic:
    - Location: hooks/post-traffic.py
```

### handlers/index.py

```python
import json
import os
import boto3

def lambda_handler(event, context):
    """API handler"""
    try:
        # Get path
        path = event['path']
        method = event['httpMethod']
        
        if path == '/health' and method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }
        
        if path == '/api/data' and method == 'GET':
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Data retrieved'})
            }
        
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Example 3: Multi-Stage Pipeline

### pipeline.json

```json
{
  "pipeline": {
    "name": "complete-pipeline",
    "roleArn": "arn:aws:iam::123456789:role/CodePipelineRole",
    "artifactStore": {
      "type": "S3",
      "location": "pipeline-artifacts-bucket"
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
            "configuration": {
              "RepositoryName": "my-app",
              "BranchName": "main",
              "PollForSourceChanges": "false"
            },
            "outputArtifacts": [
              {"name": "SourceOutput"}
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
              {"name": "SourceOutput"}
            ],
            "outputArtifacts": [
              {"name": "BuildOutput"}
            ],
            "configuration": {
              "ProjectName": "my-app-build"
            }
          }
        ]
      },
      {
        "name": "Test",
        "actions": [
          {
            "name": "IntegrationTests",
            "actionTypeId": {
              "category": "Invoke",
              "owner": "AWS",
              "provider": "Lambda",
              "version": "1"
            },
            "configuration": {
              "FunctionName": "run-integration-tests"
            },
            "inputArtifacts": [
              {"name": "BuildOutput"}
            ]
          }
        ]
      },
      {
        "name": "ApprovalForProd",
        "actions": [
          {
            "name": "ManualApproval",
            "actionTypeId": {
              "category": "Approval",
              "owner": "AWS",
              "provider": "Manual",
              "version": "1"
            },
            "configuration": {
              "CustomData": "Review and approve for production deployment"
            }
          }
        ]
      },
      {
        "name": "DeployToProd",
        "actions": [
          {
            "name": "Deploy",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "CodeDeploy",
              "version": "1"
            },
            "configuration": {
              "ApplicationName": "my-app",
              "DeploymentGroupName": "production"
            },
            "inputArtifacts": [
              {"name": "BuildOutput"}
            ]
          }
        ]
      },
      {
        "name": "Validation",
        "actions": [
          {
            "name": "PostDeploymentTests",
            "actionTypeId": {
              "category": "Invoke",
              "owner": "AWS",
              "provider": "Lambda",
              "version": "1"
            },
            "configuration": {
              "FunctionName": "validate-deployment"
            }
          }
        ]
      }
    ]
  }
}
```

## Example 4: Complete Docker Deployment

### Dockerfile

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --production

FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e \
    "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

CMD ["npm", "start"]
```

### buildspec.yml (Docker)

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging to AWS ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/my-app
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  
  build:
    commands:
      - echo Building Docker image on `date`
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  
  post_build:
    commands:
      - echo Pushing Docker image to ECR on `date`
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Creating image definitions file...
      - printf '[{"name":"my-app","imageUri":"%s"}]' $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - appspec.yml
  name: DockerArtifact
```

## Example 5: Complete IAM Roles (Terraform)

```hcl
# CodePipeline Role
resource "aws_iam_role" "codepipeline_role" {
  name = "CodePipelineRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codepipeline.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "codepipeline_policy" {
  name   = "CodePipelinePolicy"
  role   = aws_iam_role.codepipeline_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "codecommit:*",
          "codebuild:*",
          "codedeploy:*",
          "lambda:*",
          "sns:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# CodeBuild Role
resource "aws_iam_role" "codebuild_role" {
  name = "CodeBuildRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name   = "CodeBuildPolicy"
  role   = aws_iam_role.codebuild_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:*",
          "codecommit:GitPull",
          "s3:*",
          "ecr:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# CodeDeploy Role
resource "aws_iam_role" "codedeploy_role" {
  name = "CodeDeployRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codedeploy.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy_policy" {
  role       = aws_iam_role.codedeploy_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForEC2"
}

# EC2 Instance Role
resource "aws_iam_role" "ec2_instance_role" {
  name = "EC2InstanceRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ec2_instance_policy" {
  name   = "EC2InstancePolicy"
  role   = aws_iam_role.ec2_instance_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "logs:*",
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "*"
      }
    ]
  })
}
```

## Deployment Checklist

- [ ] Create CodeCommit repository
- [ ] Setup local development environment
- [ ] Create buildspec.yml
- [ ] Create appspec.yml
- [ ] Create lifecycle scripts
- [ ] Create CodeBuild project
- [ ] Create CodeDeploy application
- [ ] Create CodePipeline
- [ ] Configure webhooks
- [ ] Setup SNS notifications
- [ ] Test pipeline end-to-end
- [ ] Implement approval gates
- [ ] Setup monitoring
- [ ] Document deployment process
- [ ] Train team on process

## Quick Start Commands

```bash
# Create repository
aws codecommit create-repository --repository-name my-app

# Create S3 bucket for artifacts
aws s3 mb s3://pipeline-artifacts

# Create CodeBuild project
aws codebuild create-project --name my-app-build ...

# Create CodeDeploy application
aws deploy create-app --application-name my-app

# Create CodePipeline
aws codepipeline create-pipeline --cli-input-json file://pipeline.json

# Start pipeline
aws codepipeline start-pipeline-execution --pipeline-name my-app-pipeline
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check buildspec.yml, view CodeBuild logs |
| Deploy fails | Check appspec.yml, check scripts, verify agents |
| Pipeline stuck | Check approval gate, retry failed stage |
| Permission denied | Verify IAM roles and policies |
| Artifacts missing | Check S3 bucket, verify artifacts section |

---

**Previous**: [Advanced Topics](../08-Advanced/README.md)
