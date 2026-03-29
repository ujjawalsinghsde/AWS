# Local Development Setup

## Prerequisites

### System Requirements
- Windows/Mac/Linux
- 4GB RAM minimum
- 10GB free disk space
- Administrator access

## Step 1: Install Git

### Windows
```bash
# Download from https://git-scm.com/download/win
# Or use Chocolatey
choco install git
```

### Verify Installation
```bash
git --version
# Output: git version 2.x.x
```

## Step 2: Install AWS CLI v2

### Windows
```powershell
# Download from https://awscli.amazonaws.com/AWSCLIV2.msi
# Or use Chocolatey
choco install awscliv2
```

### Mac/Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Verify Installation
```bash
aws --version
# Output: aws-cli/2.x.x
```

## Step 3: Configure AWS Credentials

### Option 1: AWS CLI Configuration (Recommended)
```bash
aws configure

# Enter the following:
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: xxxxxxx
# Default region name: us-east-1
# Default output format: json
```

### Verify Configuration
```bash
aws sts get-caller-identity
# Returns: Account, UserId, ARN
```

### Option 2: Environment Variables (for CI/CD)
```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID = "AKIA..."
$env:AWS_SECRET_ACCESS_KEY = "xxxxxxx"
$env:AWS_DEFAULT_REGION = "us-east-1"

# Linux/Mac
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="xxxxxxx"
export AWS_DEFAULT_REGION="us-east-1"
```

### Option 3: AWS Credentials File
```
~/.aws/credentials:

[default]
aws_access_key_id = AKIA...
aws_secret_access_key = xxxxxxx

[dev-profile]
aws_access_key_id = AKIA...
aws_secret_access_key = xxxxxxx
```

```
~/.aws/config:

[default]
region = us-east-1
output = json

[profile dev-profile]
region = us-west-2
output = json
```

## Step 4: Setup Git Configuration

### Configure Git User
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify
git config --global user.name
git config --global user.email
```

### Setup SSH Keys for CodeCommit

#### Windows PowerShell
```powershell
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\id_rsa_aws

# Add to SSH agent
$env:GIT_SSH_COMMAND = "ssh -i $env:USERPROFILE\.ssh\id_rsa_aws"

# Display public key
Get-Content $env:USERPROFILE\.ssh\id_rsa_aws.pub
```

#### Linux/Mac
```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_aws

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa_aws

# Display public key
cat ~/.ssh/id_rsa_aws.pub
```

### Upload SSH Key to AWS

1. Go to AWS Console → IAM → Users → Your User
2. Click "Upload SSH public key"
3. Paste your public key content
4. Save SSH Key ID

### Configure Git to Use SSH
```bash
# Add to ~/.ssh/config (or %USERPROFILE%\.ssh\config)

Host git-codecommit.*.amazonaws.com
    User [SSH Key ID from AWS]
    IdentityFile ~/.ssh/id_rsa_aws
```

## Step 5: Install IDE/Editor

### Visual Studio Code (Recommended)
```bash
# Download from https://code.visualstudio.com
# Or use package manager
choco install vscode
```

### Extensions for VS Code
1. AWS Toolkit
2. Git Graph
3. Python (for Python development)
4. Pylance (Python language server)
5. Docker (optional)
6. CloudFormation (optional)

## Step 6: Install Language-Specific Tools

### Python (for Python projects)
```bash
# Download from https://python.org
# Or use package manager (Windows)
choco install python

# Verify installation
python --version

# Upgrade pip
python -m pip install --upgrade pip

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install common Python tools
pip install --upgrade setuptools wheel
pip install flask gunicorn pytest pytest-cov boto3
```

### Python Development Best Practices
```bash
# Create project with proper structure
mkdir my-project
cd my-project
python -m venv venv
source venv/bin/activate

# Create requirements.txt
pip install flask gunicorn boto3 python-dotenv
pip freeze > requirements.txt

# Create .pythonversion for pyenv (optional)
echo "3.11" > .python-version

# Create .env file for development
echo "FLASK_ENV=development" > .env
```

### Node.js (for JavaScript projects)
```bash
# Download from https://nodejs.org
# Or use NVM (Node Version Manager)

# Windows (using Chocolatey)
choco install nodejs

# Or using NVM on Windows
# Download nvm-windows installer

# Mac/Linux (using NVM)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18.0.0
nvm use 18.0.0

# Verify
node --version
npm --version
```

### Java (for Java projects)
```bash
choco install openjdk

# Verify
java -version
```

## Step 7: Clone Repository from CodeCommit

### Using HTTPS
```bash
git clone https://git-codecommit.[region].amazonaws.com/v1/repos/[repo-name]
```

### Using SSH
```bash
git clone ssh://git-codecommit.[region].amazonaws.com/v1/repos/[repo-name]
```

### Test Connection
```bash
# SSH test
ssh -T [SSH Key ID]@git-codecommit.[region].amazonaws.com

# Expected output: "You have successfully authenticated"
```

## Step 8: Create Local Project Structure

```
my-project/
├── src/                    # Source code
│   ├── main.js            # Main application
│   └── utils/             # Utility functions
├── tests/                 # Test files
│   └── main.test.js
├── buildspec.yml          # CodeBuild configuration
├── appspec.yml            # CodeDeploy configuration
├── package.json           # Dependencies (Node.js)
├── requirements.txt       # Dependencies (Python)
├── .gitignore            # Git ignore rules
├── .env.example          # Environment variables template
├── README.md             # Project documentation
└── Makefile              # Build commands (optional)
```

## Step 9: Initialize Git Repository

```bash
# Navigate to project directory
cd my-project

# Initialize git (if not cloned)
git init

# Create main branch
git branch -M main

# Add files
git add .

# Initial commit
git commit -m "Initial commit"

# Add remote (if not cloned)
git remote add origin [repository-url]

# Push to CodeCommit
git push -u origin main
```

## Step 10: Create .gitignore

```
# Node.js
node_modules/
npm-debug.log
*.tgz
dist/
build/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Artifacts
artifacts/
*.zip
*.jar
```

## Step 11: Test Local Development

### Node.js Project
```bash
# Install dependencies
npm install

# Run tests
npm test

# Build
npm run build

# Start application
npm start
```

### Python Project
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run application
python main.py
```

## Step 12: Create buildspec.yml

```yaml
version: 0.2

phases:
  install:
    commands:
      - echo Installing dependencies...
      - npm install
  
  pre_build:
    commands:
      - echo Running tests...
      - npm test
      - echo Build started on `date`
  
  build:
    commands:
      - echo Building application...
      - npm run build
      - echo Creating deployment package...
      - zip -r application.zip . -x "node_modules/*" "tests/*" ".git/*"
  
  post_build:
    commands:
      - echo Build completed on `date`

artifacts:
  files:
    - application.zip
  name: BuiltArtifact

cache:
  paths:
    - '/root/.npm/**/*'
```

## Step 13: Create appspec.yml

```yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::EC2::Instance
      Properties:
        Name: MyApp
        Port: 3000

Hooks:
  ApplicationStop:
    - Location: scripts/stop-server.sh
      Timeout: 180
  
  BeforeInstall:
    - Location: scripts/install-dependencies.sh
      Timeout: 180
  
  ApplicationStart:
    - Location: scripts/start-server.sh
      Timeout: 180
  
  ValidateService:
    - Location: scripts/validate-service.sh
      Timeout: 180
```

## Common Local Commands

### Git Commands
```bash
# Check status
git status

# View changes
git diff

# Commit changes
git add .
git commit -m "message"

# Push to CodeCommit
git push origin main

# Create feature branch
git checkout -b feature/new-feature
git push -u origin feature/new-feature

# View commit history
git log --oneline

# View branches
git branch -a
```

### AWS CLI Commands
```bash
# List CodeCommit repositories
aws codecommit list-repositories

# Create CodeCommit repository
aws codecommit create-repository --repository-name my-repo

# List CodeBuild projects
aws codebuild list-projects

# Start CodeBuild
aws codebuild batch-get-builds --ids build-id

# Describe CodePipeline
aws codepipeline get-pipeline --name pipeline-name
```

## Environment Variables Setup

### Create .env File
```
ENVIRONMENT=development
AWS_REGION=us-east-1
DATABASE_URL=localhost:5432
API_PORT=3000
LOG_LEVEL=debug
```

### Create .env.example
```
ENVIRONMENT=development
AWS_REGION=us-east-1
DATABASE_URL=db_url_here
API_PORT=3000
LOG_LEVEL=debug
```

## Troubleshooting

### AWS CLI Issues
```bash
# Check credentials
aws sts get-caller-identity

# Check region
aws configure get region

# Check output format
aws configure get output

# Reset credentials
aws configure --profile default
```

### Git/CodeCommit Issues
```bash
# Test SSH connection
ssh -T your-ssh-key-id@git-codecommit.us-east-1.amazonaws.com

# Debug SSH
ssh -v your-ssh-key-id@git-codecommit.us-east-1.amazonaws.com

# View Git config
git config --global --list

# Update Git SSH URL
git remote set-url origin ssh://new-url
```

### Build Issues
```bash
# Run buildspec locally
# Use AWS CodeBuild local agent:
docker run -it -v ~/.aws:/root/.aws -v $(pwd):/tmp/input amazonlinux:latest

# Inside container
cd /tmp/input
# Add bash if needed: yum install -y bash
bash
```

## Local Testing Checklist

- [ ] Git configured with correct user
- [ ] AWS credentials configured
- [ ] SSH keys created and uploaded
- [ ] CodeCommit repository cloned
- [ ] Project dependencies installed
- [ ] Tests pass locally
- [ ] Build succeeds locally
- [ ] buildspec.yml validated
- [ ] appspec.yml validated
- [ ] .gitignore configured
- [ ] Environment variables setup

## Next Steps

1. Create initial commit and push to CodeCommit
2. Read [CodeCommit Guide](../03-CodeCommit/README.md)
3. Configure CodeBuild project
4. Test local build process

## Summary

- Install Git, AWS CLI, IDE, language tools
- Configure AWS credentials (access keys or IAM)
- Setup SSH for CodeCommit
- Clone repository
- Install dependencies
- Create buildspec.yml and appspec.yml
- Test locally before committing

---

**Next**: [CodeCommit Guide](../03-CodeCommit/README.md)
