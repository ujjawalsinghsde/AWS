# AWS Secrets Manager

**Python boto3 code:** [secrets_manager_operations.py](./secrets_manager_operations.py)

---

## Table of Contents

1. [What is AWS Secrets Manager?](#1-what-is-aws-secrets-manager)
2. [Core Concepts](#2-core-concepts)
3. [Types of Secrets](#3-types-of-secrets)
4. [Creating and Managing Secrets](#4-creating-and-managing-secrets)
5. [Secret Versioning](#5-secret-versioning)
6. [Retrieving Secrets](#6-retrieving-secrets)
7. [Database Authentication & Password Rotation](#7-database-authentication--password-rotation)
8. [Security & Encryption](#8-security--encryption)
9. [Access Control with IAM](#9-access-control-with-iam)
10. [Secret Management Best Practices](#10-secret-management-best-practices)
11. [Integration with AWS Services](#11-integration-with-aws-services)
12. [Pricing & Cost Optimization](#12-pricing--cost-optimization)
13. [Monitoring & Auditing](#13-monitoring--auditing)
14. [Secrets Manager CLI Cheat Sheet](#14-secrets-manager-cli-cheat-sheet)
15. [Common Use Cases & Architectures](#15-common-use-cases--architectures)
16. [Troubleshooting & Common Issues](#16-troubleshooting--common-issues)

---

## 1. What is AWS Secrets Manager?

**AWS Secrets Manager** is a managed service that helps you protect access to your applications, services, and IT resources. It allows you to store, rotate, and manage secrets like database credentials, API keys, OAuth tokens, and other sensitive information.

### Key Characteristics

- **Centralized Secret Storage** — One place to manage all secrets across your organization
- **Automated Password Rotation** — Rotate database credentials automatically without downtime
- **Encryption at Rest & Transit** — Uses AWS KMS for encryption; secrets encrypted by default
- **Access Control** — Fine-grained IAM policies to control who can access specific secrets
- **Audit Trail** — CloudTrail integration for compliance tracking and audit logging
- **High Availability** — Secrets replicated across multiple Availability Zones
- **Simple API** — Easy integration with applications and AWS services
- **Cost-Effective** — Pay only for secrets stored and rotations performed

### What Problems Does It Solve?

| Problem | Solution |
|---------|----------|
| Hardcoded credentials in code | Store in Secrets Manager, retrieve at runtime |
| Manual password rotation | Automate with Lambda-based rotation |
| Shared credentials across teams | Use IAM policies to grant fine-grained access |
| Credential exposure in logs | Automatic masking in CloudTrail logs |
| No audit trail of secret access | Full CloudTrail integration |

---

## 2. Core Concepts

### 2.1 Secret

A **secret** is the sensitive information stored in Secrets Manager. It can contain:
- Database passwords
- API keys and tokens
- OAuth credentials
- SSH keys and certificates
- Custom strings with JSON

```text
Example Secret:
Name: prod/database/mysql-primary
Value: {
  "username": "admin",
  "password": "SecureP@ssw0rd123!",
  "engine": "mysql",
  "host": "db.example.com",
  "port": 3306
}
```

### 2.2 Secret Metadata

Each secret has associated metadata:

| Metadata | Description |
|----------|-------------|
| **Name** | Unique identifier (can include `/` for logical grouping) |
| **Description** | Human-readable information about the secret |
| **Tags** | Key-value pairs for organization and cost allocation |
| **KMS Key ARN** | Which encryption key to use (default: AWS managed key) |
| **Rotation Rules** | Automatic rotation configuration |
| **Versioning** | Multiple versions of the secret (labeled & staged) |
| **Created Date** | When the secret was first created |
| **Last Accessed** | Timestamp of last retrieval |
| **ARN** | Amazon Resource Name for the secret |

### 2.3 Secret Versions

Secrets support versioning to enable seamless rotation:

```text
Secret: prod/db/password
├── Version 1: C7D9E3F2 (AWSCURRENT) — Currently in use
├── Version 2: A1B2C3D4 (AWSPENDING) — Staged for rotation
└── Version 3: X9Y8Z7W6 (Old version)
```

- **AWSCURRENT** — The version currently in use by applications
- **AWSPENDING** — The new version staged during rotation (not yet promoted)
- **Labeling** — Custom labels for versions (e.g., "production", "staging")

### 2.4 Rotation

**Rotation** is the process of updating a secret (usually a password) to a new value. Secrets Manager can automate this using Lambda functions.

```text
Rotation Process:
1. Create new secret version (AWSPENDING)
2. Lambda function updates the resource (e.g., database password)
3. Lambda tests the new credentials
4. If successful, new version becomes AWSCURRENT
5. Old version is labeled or deleted
```

---

## 3. Types of Secrets

### 3.1 Database Secrets

Secrets Manager has built-in rotation support for databases (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, MongoDB).

```json
{
  "username": "admin",
  "password": "Secure@Pass123",
  "engine": "mysql",
  "host": "mydb.123456789.us-east-1.rds.amazonaws.com",
  "port": 3306,
  "dbname": "mydb"
}
```

### 3.2 API Keys & OAuth Tokens

Store API keys for third-party services:

```json
{
  "api_key": "sk-12345abcdefghijklmnop",
  "api_secret": "sks-98765zyxwvutsrqponmlk",
  "service": "stripe",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 3.3 SSH Keys & Certificates

```json
{
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
  "public_key": "ssh-rsa AAAA...",
  "key_name": "prod-deployment-key",
  "passphrase": "KeyPassphrase123"
}
```

### 3.4 Custom Secrets

Plain text or JSON for any sensitive data:

```text
Simple string: MySecretPassword123!

Or complex JSON:
{
  "stripe_key": "sk-abc123",
  "slack_token": "xoxb-token",
  "sendgrid_api": "SG.abc123"
}
```

---

## 4. Creating and Managing Secrets

### 4.1 AWS Console

Navigate to **Secrets Manager** > **Store a new secret**

1. Choose secret type (credentials for database, API key, other)
2. Enter secret value (plain text or JSON)
3. Configure encryption (default or custom KMS key)
4. Add secret name and description
5. Add tags for organization
6. Configure rotation (optional)
7. Review and store

### 4.2 AWS CLI

**Create a simple secret:**
```bash
aws secretsmanager create-secret \
  --name prod/api/stripe-key \
  --description "Stripe API key for production" \
  --secret-string "sk-12345abcdefghijklmnop" \
  --tags Key=Environment,Value=Production Key=Service,Value=Payments
```

**Create a JSON secret:**
```bash
aws secretsmanager create-secret \
  --name prod/database/mysql \
  --secret-string '{
    "username": "admin",
    "password": "MyP@ssw0rd!",
    "host": "db.example.com",
    "port": 3306
  }'
```

**Create from a file:**
```bash
aws secretsmanager create-secret \
  --name prod/tls/certificate \
  --secret-string file:///path/to/cert.pem
```

### 4.3 Update an Existing Secret

**Update secret value:**
```bash
aws secretsmanager update-secret \
  --secret-id prod/api/stripe-key \
  --secret-string "sk-new-key-xyz"
```

**Update description and tags:**
```bash
aws secretsmanager update-secret \
  --secret-id prod/database/mysql \
  --description "Updated MySQL database credentials" \
  --tags Key=UpdatedDate,Value=2025-03-01
```

### 4.4 Add/Update Tags

```bash
aws secretsmanager tag-resource \
  --secret-id prod/database/mysql \
  --tags Key=CostCenter,Value=Engineering Key=Compliance,Value=SOC2
```

### 4.5 Delete a Secret

**Immediate deletion (not recommended for production):**
```bash
aws secretsmanager delete-secret \
  --secret-id prod/test/temp-key \
  --force-delete-without-recovery
```

**Schedule deletion with recovery window (recommended):**
```bash
aws secretsmanager delete-secret \
  --secret-id prod/test/temp-key \
  --recovery-window-in-days 30
```

This gives 30 days to cancel the deletion.

### 4.6 List All Secrets

```bash
aws secretsmanager list-secrets \
  --filters Key=name,Values=prod
```

**Output includes:**
```json
{
  "SecretList": [
    {
      "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/mysql-ABC123",
      "Name": "prod/database/mysql",
      "Description": "MySQL production credentials",
      "LastChangedDate": "2025-03-15T10:30:00Z",
      "LastAccessedDate": "2025-03-15T14:22:00Z",
      "Tags": [ { "Key": "Environment", "Value": "Production" } ],
      "SecretVersionsToStages": {
        "c7d9e3f2-1234-5678-abcd-ef1234567890": ["AWSCURRENT"],
        "a1b2c3d4-5678-9012-abcd-ef9876543210": ["AWSPENDING"]
      }
    }
  ]
}
```

---

## 5. Secret Versioning

### 5.1 Understanding Version Stages

When you update a secret, a new version is created. Each version can have labels:

```bash
# View all versions of a secret
aws secretsmanager list-secret-version-ids \
  --secret-id prod/database/mysql
```

**Response:**
```json
{
  "Versions": [
    {
      "VersionId": "c7d9e3f2",
      "VersionStages": ["AWSCURRENT"],
      "CreatedDate": "2025-03-15T14:00:00Z"
    },
    {
      "VersionId": "a1b2c3d4",
      "VersionStages": ["AWSPENDING"],
      "CreatedDate": "2025-03-15T13:00:00Z"
    },
    {
      "VersionId": "x9y8z7w6",
      "VersionStages": ["old-version"],
      "CreatedDate": "2025-03-14T10:00:00Z"
    }
  ]
}
```

### 5.2 Get Specific Version

```bash
# Get current version
aws secretsmanager get-secret-value \
  --secret-id prod/database/mysql \
  --version-stage AWSCURRENT

# Get by version ID
aws secretsmanager get-secret-value \
  --secret-id prod/database/mysql \
  --version-id c7d9e3f2

# Get by custom label
aws secretsmanager get-secret-value \
  --secret-id prod/database/mysql \
  --version-stage production
```

### 5.3 Label Versions

```bash
# Add custom label
aws secretsmanager update-secret-version-stage \
  --secret-id prod/database/mysql \
  --version-stage "staging" \
  --move-to-version-id a1b2c3d4

# Remove label from version
aws secretsmanager update-secret-version-stage \
  --secret-id prod/database/mysql \
  --version-stage "old-version" \
  --remove-from-version-id x9y8z7w6
```

---

## 6. Retrieving Secrets

### 6.1 Get Secret Value (CLI)

```bash
# Get current secret value
aws secretsmanager get-secret-value \
  --secret-id prod/database/mysql

# Output:
# {
#   "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/mysql-ABC123",
#   "Name": "prod/database/mysql",
#   "VersionId": "c7d9e3f2",
#   "SecretString": "{\"username\":\"admin\",\"password\":\"MyP@ssw0rd!\",...}",
#   "VersionStages": ["AWSCURRENT"],
#   "CreatedDate": "2025-03-15T14:00:00Z"
# }
```

### 6.2 Retrieving in Application Code

**Python Example:**

```python
import json
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')

try:
    response = client.get_secret_value(SecretId='prod/database/mysql')

    # Parse secret
    if 'SecretString' in response:
        secret = json.loads(response['SecretString'])
        username = secret['username']
        password = secret['password']
        host = secret['host']
    else:
        # Binary secret
        secret = response['SecretBinary']

except client.exceptions.ResourceNotFoundException:
    print("Secret not found")
except client.exceptions.InvalidRequestException:
    print("Invalid request")
except client.exceptions.InvalidParameterException:
    print("Invalid parameter")
```

**Node.js Example:**

```javascript
const AWS = require('aws-sdk');
const client = new AWS.SecretsManager({ region: 'us-east-1' });

async function getSecret() {
  try {
    const response = await client.getSecretValue({ SecretId: 'prod/database/mysql' }).promise();

    const secret = JSON.parse(response.SecretString);
    const { username, password, host } = secret;

    return { username, password, host };
  } catch (error) {
    console.error('Error retrieving secret:', error);
  }
}
```

**Java Example:**

```java
import software.amazon.awssdk.services.secretsmanager.SecretsManagerClient;
import software.amazon.awssdk.services.secretsmanager.model.GetSecretValueRequest;
import software.amazon.awssdk.services.secretsmanager.model.GetSecretValueResponse;

String secretName = "prod/database/mysql";
SecretsManagerClient client = SecretsManagerClient.builder().build();

GetSecretValueRequest request = GetSecretValueRequest.builder()
    .secretId(secretName)
    .build();

GetSecretValueResponse response = client.getSecretValue(request);
String secret = response.secretString();
```

### 6.3 Caching Secrets

For performance, cache secrets in memory and refresh periodically:

```python
import json
import time
from datetime import datetime

class SecretCache:
    def __init__(self, client, ttl_seconds=3600):
        self.client = client
        self.ttl_seconds = ttl_seconds
        self.cache = {}

    def get_secret(self, secret_id):
        now = time.time()

        if secret_id in self.cache:
            cached_value, timestamp = self.cache[secret_id]
            if now - timestamp < self.ttl_seconds:
                return cached_value

        # Fetch from Secrets Manager
        response = self.client.get_secret_value(SecretId=secret_id)
        secret = json.loads(response['SecretString'])

        # Cache it
        self.cache[secret_id] = (secret, now)
        return secret
```

---

## 7. Database Authentication & Password Rotation

### 7.1 Automatic Database Rotation

Secrets Manager provides built-in Lambda functions for rotating database passwords.

**Supported Databases:**
- MySQL
- PostgreSQL
- Oracle
- SQL Server
- MariaDB
- MongoDB

### 7.2 Enable Rotation (Console)

1. Select secret
2. **Rotation** > **Enable rotation**
3. Choose rotation interval (30/60/90 days recommended)
4. Select rotation Lambda function
5. Verify secret has required permissions

### 7.3 Enable Rotation (CLI)

```bash
aws secretsmanager rotate-secret \
  --secret-id prod/database/mysql \
  --rotation-rules AutomaticallyAfterDays=30 \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsManagerMysqlRotation-1A2B3C4D
```

### 7.4 Manual Rotation Trigger

```bash
aws secretsmanager rotate-secret \
  --secret-id prod/database/mysql \
  --rotate-immediately
```

### 7.5 Custom Rotation with Lambda

Create a Lambda function that handles rotation:

```python
import json
import boto3
import pymysql

secrets_client = boto3.client('secretsmanager')

def lambda_handler(event, context):
    service_client_id = event['service_client_id']
    secret_id = event['ClientRequestToken']
    step = event['ClientRequestToken']
    secret_version = event['ClientRequestToken']

    metadata = secrets_client.describe_secret(SecretId=secret_id)
    current_version = None
    for version in metadata['VersionIdsToStages']:
        if 'AWSCURRENT' in metadata['VersionIdsToStages'][version]:
            current_version = version
            break

    # Get current and new secret
    current_secret = secrets_client.get_secret_value(
        SecretId=secret_id,
        VersionId=current_version,
        VersionStage='AWSCURRENT'
    )
    current_dict = json.loads(current_secret['SecretString'])

    if step == 'create':
        # Generate new password
        new_password = secrets_client.get_random_password(
            PasswordLength=32,
            ExcludeCharacters='/@"\''
        )['RandomPassword']

        # Store pending version
        secrets_client.put_secret_value(
            SecretId=secret_id,
            ClientRequestToken=secret_version,
            SecretString=json.dumps({
                **current_dict,
                'password': new_password
            }),
            VersionStages=['AWSPENDING']
        )

    elif step == 'set':
        # Update password in database
        pending_secret = secrets_client.get_secret_value(
            SecretId=secret_id,
            VersionId=secret_version,
            VersionStage='AWSPENDING'
        )
        pending_dict = json.loads(pending_secret['SecretString'])

        connection = pymysql.connect(
            host=pending_dict['host'],
            user=current_dict['username'],
            password=current_dict['password'],
            database=pending_dict.get('dbname', 'mysql')
        )

        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER USER '{pending_dict['username']}'@'%' IDENTIFIED BY %s",
                (pending_dict['password'],)
            )
        connection.commit()
        connection.close()

    elif step == 'test':
        # Verify new credentials work
        pending_secret = secrets_client.get_secret_value(
            SecretId=secret_id,
            VersionId=secret_version,
            VersionStage='AWSPENDING'
        )
        pending_dict = json.loads(pending_secret['SecretString'])

        connection = pymysql.connect(
            host=pending_dict['host'],
            user=pending_dict['username'],
            password=pending_dict['password'],
            database=pending_dict.get('dbname', 'mysql')
        )
        connection.close()

    elif step == 'finish':
        # Promote AWSPENDING to AWSCURRENT
        secrets_client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage='AWSCURRENT',
            MoveToVersionId=secret_version,
            RemoveFromVersionId=current_version
        )

    return {'statusCode': 200}
```

---

## 8. Security & Encryption

### 8.1 Encryption at Rest

By default, Secrets Manager encrypts secrets using AWS managed KMS keys:

```bash
# Create secret with custom KMS key
aws secretsmanager create-secret \
  --name prod/database/mysql \
  --secret-string "MyPassword" \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
```

### 8.2 Encryption in Transit

- Secrets are encrypted in transit using TLS 1.2+
- API calls use HTTPS
- All communication encrypted end-to-end

### 8.3 Enabling AWS CloudTrail Logging

Track all API calls to Secrets Manager:

```bash
# Enable data events for GetSecretValue
aws cloudtrail put-insight-selectors \
  --trail-name secrets-mgr-trail \
  --insight-selectors AttributeKey=eventName,AttributeValue=GetSecretValue
```

### 8.4 Enable Rotation for Key Expiry

When using CMK (Customer Managed Keys), ensure key rotation is enabled:

```bash
aws kms enable-key-rotation \
  --key-id arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
```

---

## 9. Access Control with IAM

### 9.1 IAM Policies

**Allow specific user to retrieve a secret:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/mysql-*"
    }
  ]
}
```

**Allow specific actions on multiple secrets:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/*"
      ]
    }
  ]
}
```

**Allow creating and managing secrets (for CI/CD):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:UpdateSecret",
        "secretsmanager:PutSecretValue",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cicd/*"
    }
  ]
}
```

### 9.2 Resource-Based Policies

Attach a policy to the secret itself (for cross-account access):

```bash
aws secretsmanager put-resource-policy \
  --secret-id prod/database/mysql \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::987654321098:role/CrossAccountRole"
        },
        "Action": "secretsmanager:GetSecretValue",
        "Resource": "*"
      }
    ]
  }'
```

### 9.3 Deny Specific Actions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "secretsmanager:DeleteSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/*"
    }
  ]
}
```

---

## 10. Secret Management Best Practices

### 10.1 Naming Conventions

Use hierarchical naming for organization:

```text
Good:
prod/database/mysql-primary
prod/database/mysql-replica
prod/api/stripe-key
prod/api/sendgrid-key
staging/database/mysql
dev/api/stripe-key

Avoid:
mysql_password
api-key-123
Password
secret1
```

### 10.2 Redundancy & Backup

Enable multi-region replication for critical secrets:

```bash
aws secretsmanager replicate-secret-to-regions \
  --secret-id prod/database/mysql \
  --add-replica-regions RegionCode=us-west-2,KmsKeyId=arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012
```

### 10.3 Least Privilege Access

- Grant read-only access unless modification is needed
- Use resource-based policies for cross-account access
- Avoid wildcard (`*`) permissions on critical secrets
- Regularly audit IAM policies with `aws iam simulate-custom-policy`

### 10.4 Secret Rotation Policy

- **Database passwords** — Every 30 days
- **API keys** — Every 90 days
- **OAuth tokens** — Follow provider's recommendation
- **SSH keys** — Every 6-12 months or on each deployment

### 10.5 Logging & Monitoring

```bash
# Enable CloudTrail logging for Secrets Manager
aws cloudtrail create-trail \
  --name secrets-manager-trail \
  --s3-bucket-name my-cloudtrail-bucket

# Create CloudWatch alarm for failed GetSecretValue
aws cloudwatch put-metric-alarm \
  --alarm-name SecretsManagerFailedAccess \
  --alarm-description "Alert on failed secret access" \
  --metric-name UserErrorCount \
  --namespace AWS/SecretsManager \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### 10.6 Never Hardcode Secrets

**❌ Bad:**
```python
password = "MyP@ssw0rd123"
api_key = "sk-12345abcdefgh"
```

**✅ Good:**
```python
secrets_client = boto3.client('secretsmanager')
response = secrets_client.get_secret_value(SecretId='prod/database/mysql')
secret = json.loads(response['SecretString'])
password = secret['password']
```

### 10.7 Cleanup & Deletion

- Use recovery window before permanent deletion
- Audit deleted secrets via CloudTrail
- Document deletion reason in tags before deletion

```bash
# Schedule deletion with 7-day recovery
aws secretsmanager delete-secret \
  --secret-id prod/database/test \
  --recovery-window-in-days 7
```

---

## 11. Integration with AWS Services

### 11.1 Lambda Integration

Lambda functions can retrieve secrets without explicit credential storage:

```python
# Lambda execution role needs permission to read secrets
# Trust relationship with SecretsManager

import json
import boto3

def lambda_handler(event, context):
    sm = boto3.client('secretsmanager')

    # Retrieve credentials
    secret = sm.get_secret_value(SecretId='prod/database/mysql')
    db_creds = json.loads(secret['SecretString'])

    # Use credentials
    import pymysql
    conn = pymysql.connect(
        host=db_creds['host'],
        user=db_creds['username'],
        password=db_creds['password']
    )
```

### 11.2 RDS Proxy Integration

RDS Proxy can automatically use Secrets Manager credentials:

```bash
aws rds create-db-proxy \
  --db-proxy-name mysql-proxy \
  --engine-family MYSQL \
  --role-arn arn:aws:iam::123456789012:role/RDSProxyRole \
  --auth '{"AuthScheme":"SECRETS","SecretArn":"arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/mysql","IAMAuth":"DISABLED"}'
```

### 11.3 CloudFormation Integration

Define secrets in Infrastructure as Code:

```yaml
Resources:
  DatabaseSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: prod/database/mysql
      Description: MySQL database credentials
      SecretString: |
        {
          "username": "admin",
          "password": "GeneratedPassword123",
          "host": "db.example.com"
        }
      KmsKeyId: !GetAtt EncryptionKey.Arn
      Tags:
        - Key: Environment
          Value: Production

  SecretTargetAttachment:
    Type: AWS::SecretsManager::SecretTargetAttachment
    Properties:
      SecretId: !Ref DatabaseSecret
      TargetId: !Ref DBInstance
      TargetType: AWS::RDS::DBInstance
```

### 11.4 CodeBuild Integration

Inject secrets into build environment:

```yaml
phases:
  pre_build:
    commands:
      - |
        secret=$(aws secretsmanager get-secret-value \
          --secret-id prod/api/github-token \
          --query SecretString \
          --output text)
      - git config --global url."https://${secret}@github.com/".insteadOf "https://github.com/"
```

### 11.5 Step Functions Integration

Use secrets in Step Functions workflows:

```json
{
  "Comment": "Workflow using Secrets Manager",
  "StartAt": "RetrieveCredentials",
  "States": {
    "RetrieveCredentials": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:secretsmanager:getSecretValue",
      "Parameters": {
        "SecretId": "prod/database/mysql"
      },
      "Next": "ProcessData"
    },
    "ProcessData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessDatabase",
      "End": true
    }
  }
}
```

---

## 12. Pricing & Cost Optimization

### 12.1 Pricing Model

| Component | Cost |
|-----------|------|
| Secret stored | $0.40 per secret per month |
| Secret rotation | $0.05 per rotation |
| API calls | No per-call charge (included) |

### 12.2 Cost Optimization

**Consolidate related secrets:**

```json
// Instead of 5 separate secrets
prod/api/stripe-key
prod/api/sendgrid-key
prod/api/github-token
prod/api/slack-token
prod/api/twilio-key

// Use one multi-purpose secret
prod/api/keys
{
  "stripe_key": "sk-...",
  "sendgrid_key": "SG.-...",
  "github_token": "ghp_...",
  "slack_token": "xoxb-...",
  "twilio_key": "AC..."
}
```

**Example savings:** From 5 secrets @ $0.40 = $2.00/month to 1 secret = $0.40/month

**Disable rotation for non-critical secrets:**

Rotation cost = $0.05 per rotation. For daily rotation: $1.50/month per secret.

**Use standard rotation intervals:**

- Instead of: Weekly rotation ($2.60/month)
- Better: 30-day rotation ($1.80/month)
- Best: 90-day rotation ($0.60/month) — for non-critical

### 12.3 Monitoring Costs

```bash
# Get secret count and rotation frequency
aws secretsmanager list-secrets --query 'length(SecretList)'

# Check rotation configuration
aws secretsmanager describe-secret \
  --secret-id prod/database/mysql \
  --query 'RotationRules'
```

---

## 13. Monitoring & Auditing

### 13.1 CloudTrail Integration

All Secrets Manager API calls are logged in CloudTrail:

```bash
# Query CloudTrail for secret access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=prod/database/mysql \
  --max-items 10
```

### 13.2 CloudWatch Metrics

Monitor secret usage:

```bash
# Put custom metric for secret access
aws cloudwatch put-metric-data \
  --namespace CustomMetrics \
  --metric-name SecretAccess \
  --value 1 \
  --dimensions SecretName=prod/database/mysql
```

### 13.3 EventBridge Integration

Trigger actions on secret changes:

```json
{
  "Name": "SecretRotationNotification",
  "EventPattern": {
    "source": ["aws.secretsmanager"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventSource": ["secretsmanager.amazonaws.com"],
      "eventName": ["PutSecretValue", "RotateSecret"]
    }
  },
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:sns:us-east-1:123456789012:SecretRotationTopic",
      "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole"
    }
  ]
}
```

### 13.4 Audit Secret Access

```bash
# View who accessed a secret and when
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
  --start-time 2025-03-01T00:00:00Z \
  --end-time 2025-03-31T23:59:59Z
```

---

## 14. Secrets Manager CLI Cheat Sheet

### Create & Store

```bash
# Create simple secret
aws secretsmanager create-secret --name prod/api/key --secret-string "value"

# Create from JSON
aws secretsmanager create-secret --name prod/db/mysql \
  --secret-string '{"user":"admin","pass":"pwd"}'

# Create with tags
aws secretsmanager create-secret --name prod/db/mysql \
  --secret-string "pwd" \
  --tags Key=Env,Value=Prod Key=Team,Value=Backend
```

### Retrieve & View

```bash
# Get secret value
aws secretsmanager get-secret-value --secret-id prod/api/key

# Get only the string (useful for scripts)
aws secretsmanager get-secret-value --secret-id prod/api/key \
  --query SecretString --output text

# Parse JSON secret
aws secretsmanager get-secret-value --secret-id prod/db/mysql \
  --query 'SecretString' --output text | jq .

# Get specific version
aws secretsmanager get-secret-value --secret-id prod/api/key \
  --version-stage AWSCURRENT

# Describe secret (metadata only, no value)
aws secretsmanager describe-secret --secret-id prod/api/key
```

### Update & Modify

```bash
# Update secret value
aws secretsmanager update-secret --secret-id prod/api/key \
  --secret-string "newvalue"

# Update description
aws secretsmanager update-secret --secret-id prod/api/key \
  --description "Updated description"

# Add tags
aws secretsmanager tag-resource --secret-id prod/api/key \
  --tags Key=NewTag,Value=NewValue

# Remove tags
aws secretsmanager untag-resource --secret-id prod/api/key \
  --tag-keys OldTag
```

### List & Search

```bash
# List all secrets
aws secretsmanager list-secrets

# Filter by name prefix
aws secretsmanager list-secrets --filters Key=name,Values=prod

# Get version history
aws secretsmanager list-secret-version-ids --secret-id prod/api/key
```

### Rotation

```bash
# Enable rotation
aws secretsmanager rotate-secret --secret-id prod/db/mysql \
  --rotation-rules AutomaticallyAfterDays=30 \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:Rotation

# Manually trigger rotation
aws secretsmanager rotate-secret --secret-id prod/db/mysql \
  --rotate-immediately

# Check rotation status
aws secretsmanager describe-secret --secret-id prod/db/mysql \
  --query 'RotationEnabled'
```

### Delete

```bash
# Schedule deletion (with recovery window)
aws secretsmanager delete-secret --secret-id prod/temp/key \
  --recovery-window-in-days 7

# Force immediate deletion
aws secretsmanager delete-secret --secret-id prod/temp/key \
  --force-delete-without-recovery

# Cancel scheduled deletion
aws secretsmanager restore-secret --secret-id prod/temp/key
```

---

## 15. Common Use Cases & Architectures

### 15.1 Web Application with Database Credentials

```
Application → Query Secrets Manager → Retrieve DB credentials → Connect to RDS
     ↓
  IAM role with GetSecretValue permission
```

**Implementation:**

```python
import json
import boto3
from flask import Flask

app = Flask(__name__)
sm = boto3.client('secretsmanager')

def get_db_connection():
    # Retrieve credentials (cached in production)
    secret = sm.get_secret_value(SecretId='prod/database/mysql')
    creds = json.loads(secret['SecretString'])

    return connect_to_database(
        host=creds['host'],
        user=creds['username'],
        password=creds['password']
    )

@app.route('/api/data')
def get_data():
    db = get_db_connection()
    # ... use connection
```

### 15.2 CI/CD Pipeline with Repository Access

```
GitHub Action → Retrieve GitHub Token from Secrets Manager → Clone private repos
IAM role with GetSecretValue permission
```

```yaml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - name: Assume AWS role
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Get GitHub token from Secrets Manager
        run: |
          TOKEN=$(aws secretsmanager get-secret-value \
            --secret-id cicd/github/token \
            --query SecretString --output text)
          git config --global url."https://$TOKEN@github.com/".insteadOf "https://github.com/"

      - name: Clone and deploy
        run: git clone https://github.com/myorg/private-repo.git
```

### 15.3 Microservices with Shared API Keys

```
Service A ─┐
Service B ─┼→ Secrets Manager (prod/api/stripe-key) ← Shared secret
Service C ─┘

Each service has IAM role with read permission
```

### 15.4 Compliance & Audit Use Case

```
Secrets Manager ─→ CloudTrail ─→ CloudWatch ─→ Alerts & Reports
└─ All access logged
└─ Centralized audit trail
└─ Compliance proof
```

---

## 16. Troubleshooting & Common Issues

### 16.1 AccessDeniedException

**Problem:** Getting "User is not authorized to perform: secretsmanager:GetSecretValue"

**Diagnosis:**
```bash
# Check IAM policy
aws iam get-user-policy --user-name myuser --policy-name myPolicy

# Simulate policy
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/myuser \
  --action-names secretsmanager:GetSecretValue \
  --resource-arns arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/api/key
```

**Solution:**
- Add necessary permission to IAM user/role policy
- Ensure secret ARN is correctly specified (includes `-XXXXXX` suffix)

### 16.2 ResourceNotFoundException

**Problem:** "Secrets Manager can't find the specified secret"

**Solutions:**
```bash
# Verify secret exists
aws secretsmanager describe-secret --secret-id prod/api/key

# Check if secret is in recovery
aws secretsmanager list-secrets | grep prod/api/key

# Check region
aws ec2 describe-availability-zones --region us-east-1
```

### 16.3 Rotation Failure

**Problem:** Secret rotation fails silently

**Diagnosis:**
```bash
# Check Lambda role has required permissions
aws iam list-role-policies --role-name SecretsManagerRotationRole

# Check Lambda logs
aws logs tail /aws/lambda/SecretsManagerRotation --follow

# Manually test rotation
aws secretsmanager rotate-secret --secret-id prod/db/mysql --rotate-immediately
```

### 16.4 SecretStringLength Exceeded

**Problem:** "Secret value exceeds maximum allowed length"

**Cause:** Secrets limited to 65,536 bytes

**Solution:**
- Compress data if possible
- Split into multiple related secrets
- Consider S3 + KMS for very large secrets

### 16.5 Binary Secrets Not Retrieving Correctly

**Problem:** Getting garbled data from binary secrets

```python
# ❌ Wrong
response = client.get_secret_value(SecretId='mykey')
data = response['SecretString']  # This is None for binary

# ✅ Correct
response = client.get_secret_value(SecretId='mykey')
if 'SecretBinary' in response:
    data = response['SecretBinary']
    import base64
    binary_data = base64.b64decode(data)
```

### 16.6 Slow Secret Retrieval

**Problem:** GetSecretValue calls are taking > 100ms

**Solutions:**
1. **Cache secrets** — Store in memory with TTL
2. **Use RDS Proxy** — For database credentials (built-in caching)
3. **Batch operations** — Retrieve multiple at once if possible
4. **Check network latency** — Ensure EC2/Lambda in same region

```python
# Implement caching
from datetime import datetime, timedelta

secret_cache = {}
CACHE_TTL = 3600  # 1 hour

def get_cached_secret(secret_id):
    if secret_id in secret_cache:
        value, timestamp = secret_cache[secret_id]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            return value

    # Fetch from Secrets Manager
    response = sm.get_secret_value(SecretId=secret_id)
    value = response['SecretString']
    secret_cache[secret_id] = (value, datetime.now())
    return value
```

---

## Summary

AWS Secrets Manager provides a secure, centralized way to manage sensitive data. Key takeaways:

- ✅ **Never hardcode secrets** — Use Secrets Manager
- ✅ **Enable automatic rotation** — For database passwords
- ✅ **Use IAM policies** — Implement least privilege
- ✅ **Cache credentials** — For performance
- ✅ **Enable CloudTrail** — For audit and compliance
- ✅ **Encrypt with KMS** — For maximum security
- ✅ **Test rotation processes** — Before using in production

Secrets Manager is essential for production applications and recommended security practice across AWS deployments.
