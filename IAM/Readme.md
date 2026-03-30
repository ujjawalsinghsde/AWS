# AWS IAM (Identity and Access Management)

**Python boto3 code:** [iam_operations.py](./iam_operations.py)

---

## Table of Contents

1. [What is AWS IAM?](#1-what-is-aws-iam)
2. [Core IAM Concepts](#2-core-iam-concepts)
3. [Users & Groups](#3-users--groups)
4. [Roles](#4-roles)
5. [Policies & Permissions](#5-policies--permissions)
6. [Policy Structure & Syntax](#6-policy-structure--syntax)
7. [Resource-Based Policies](#7-resource-based-policies)
8. [Cross-Account Access](#8-cross-account-access)
9. [Temporary Credentials & STS](#9-temporary-credentials--sts)
10. [MFA (Multi-Factor Authentication)](#10-mfa-multi-factor-authentication)
11. [Access Keys & Secrets](#11-access-keys--secrets)
12. [IAM Best Practices](#12-iam-best-practices)
13. [Troubleshooting & Debugging](#13-troubleshooting--debugging)
14. [Security Analysis Tools](#14-security-analysis-tools)
15. [Advanced Topics](#15-advanced-topics)
16. [CLI Cheat Sheet](#16-cli-cheat-sheet)
17. [Common Scenarios](#17-common-scenarios)
18. [Best Practices Summary](#18-best-practices-summary)

---

## 1. What is AWS IAM?

**AWS IAM** is a web service that helps you control access to AWS resources securely by managing identities and permissions.

### Key Characteristics

- **Identity Management** - Users, roles, and temporary credentials
- **Access Control** - Fine-grained permissions for specific resources
- **Centralized** - Single place to manage all AWS access
- **Flexible** - Supports complex authorization scenarios
- **Audit Trail** - CloudTrail logs all IAM actions
- **Global** - IAM is globally replicated (no regional selection needed)
- **Free** - No additional cost for IAM (charged only for actual API calls)

### IAM Core Components

```
┌──────────────────────────────┐
│     AWS Account               │
├──────────────────────────────┤
│  ✓ Users (People)            │
│  ✓ Roles (Services)          │
│  ✓ Groups (Collections)      │
│  ✓ Policies (Permissions)    │
│  ✓ Resources (AWS Services)  │
└──────────────────────────────┘

Flow: Principal × Action × Resource × Condition = Allow/Deny
```

### When to Use IAM

| Component | Use Case |
|-----------|----------|
| **Users** | Individual people accessing AWS |
| **Roles** | Services/applications accessing resources |
| **Groups** | Team-level permission management |
| **Policies** | Define what actions are allowed |
| **MFA** | Extra security for human users |

---

## 2. Core IAM Concepts

### Principals

**A principal is an AWS entity that can take actions.**

```
┌─ Principal Types
├─ AWS Root Account (Account Owner - rarely used for daily work)
├─ IAM Users (People or applications with long-term credentials)
├─ IAM Roles (Services with temporary credentials)
├─ Federated Users (External identities via SAML/OIDC)
└─ Temporary Security Credentials (STS tokens)
```

### Actions

**An action is what a principal can do.**

```
Examples:
✓ s3:GetObject          - Read object from S3
✓ s3:PutObject         - Upload object to S3
✓ s3:*                 - All S3 actions
✓ ec2:StartInstances   - Start EC2 instance
✓ iam:CreateUser       - Create new IAM user
✓ *                    - All AWS actions (Admin)
```

### Resources

**A resource is what an action is performed on.**

```
ARN Format: arn:partition:service:region:account-id:resource

Examples:
arn:aws:s3:::my-bucket                    - S3 bucket
arn:aws:s3:::my-bucket/*                  - All objects in bucket
arn:aws:ec2:us-east-1:123456789:instance/i-1234567890abcdef0
arn:aws:rds:us-east-1:123456789:db:mydb
arn:aws:iam::123456789:user/alice
*                                         - All resources
```

### Conditions

**Conditions control when a permission applies.**

```python
"Condition": {
    "StringEquals": {
        "aws:PrincipalOrgID": "o-1234567890"   # Only this organization
    },
    "IpAddress": {
        "aws:SourceIp": "203.0.113.0/24"       # Only from this IP range
    },
    "StringLike": {
        "aws:username": "dev-*"                # Usernames starting with dev-
    },
    "DateGreaterThan": {
        "aws:CurrentTime": "2024-01-01T00:00:00Z"  # After date
    }
}
```

### Authentication vs Authorization

```
🔑 AUTHENTICATION (who are you?)
   └─ Prove identity: Username/password, access keys, MFA
   └─ Result: Credentials / Session token

🔐 AUTHORIZATION (what can you do?)
   └─ Check permissions: What does your policy allow?
   └─ Result: Allow / Deny
```

---

## 3. Users & Groups

### Creating IAM Users

```python
import boto3

iam = boto3.client('iam')

# Create a user
response = iam.create_user(
    UserName='alice',
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Team', 'Value': 'engineering'}
    ]
)

print(f"User created: {response['User']['UserName']}")
```

### Creating Groups & Adding Users

```python
# Create a group
iam.create_group(GroupName='developers')

# Add user to group
iam.add_user_to_group(
    GroupName='developers',
    UserName='alice'
)

# List users in group
members = iam.get_group(GroupName='developers')
for user in members['Users']:
    print(f"  - {user['UserName']}")
```

### Listing & Deleting Users

```python
# List all users
users = iam.list_users()
for user in users['Users']:
    print(f"{user['UserName']:20} | Created: {user['CreateDate']}")

# Delete user (all attached policies must be removed first)
iam.detach_user_policy(
    UserName='alice',
    PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
)
iam.delete_user(UserName='alice')
```

### User vs Role Lifecycle

| Aspect | User | Role |
|--------|------|------|
| **Credentials** | Long-term (access keys, password) | Temporary (STS token, ~1 hour) |
| **For** | People, applications with fixed identity | Services, cross-account access |
| **Created by** | IAM | IAM |
| **Managed by** | Interactive login or API | Trust relationship |
| **Credential rotation** | Manual (every 90 days recommended) | Automatic (STS re-assumes) |

---

## 4. Roles

### Creating IAM Roles

```python
# Role trust policy (who can assume this role)
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

# Create role
response = iam.create_role(
    RoleName='LambdaExecutionRole',
    AssumeRolePolicyDocument=json.dumps(trust_policy),
    Description='Role for Lambda to access AWS services'
)

print(f"Role created: {response['Role']['Arn']}")
```

### Attaching Policies to Roles

```python
# Attach AWS managed policy
iam.attach_role_policy(
    RoleName='LambdaExecutionRole',
    PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
)

# Attach inline policy
inline_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::my-bucket/*"
        }
    ]
}

iam.put_role_policy(
    RoleName='LambdaExecutionRole',
    PolicyName='S3Access',
    PolicyDocument=json.dumps(inline_policy)
)
```

### Common Service Roles

```
Lambda:
  - AWSLambdaBasicExecutionRole      (CloudWatch Logs)
  - AWSLambdaVPCAccessExecutionRole  (EC2 network permissions)
  - AWSLambdaFullAccess              (Full AWS access)

EC2:
  - AmazonEC2FullAccess
  - AmazonEC2RoleforSSM              (Systems Manager access)

RDS:
  - AmazonRDSEnhancedMonitoringRole

S3:
  - AmazonS3FullAccess
  - AmazonS3ReadOnlyAccess
```

### Assuming a Role

```python
# Use STS to assume a role
sts = boto3.client('sts')

response = sts.assume_role(
    RoleArn='arn:aws:iam::123456789:role/LambdaExecutionRole',
    RoleSessionName='MySession',
    DurationSeconds=900  # 15 minutes
)

credentials = response['Credentials']
print(f"Access Key:  {credentials['AccessKeyId']}")
print(f"Secret Key:  {credentials['SecretAccessKey']}")
print(f"Session Token:  {credentials['SessionToken']}")

# Use assumed role credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)
```

---

## 5. Policies & Permissions

### Types of Policies

```
📋 Identity-Based Policies
   └─ Attached to: Users, Groups, Roles
   └─ Define: What actions principal can perform
   └─ Example: "Allow Alice to read S3 buckets"

📋 Resource-Based Policies
   └─ Attached to: S3 buckets, SQS queues, Lambda, KMS keys
   └─ Define: Who can access this resource
   └─ Example: "Allow Bob's Lambda to read this S3 bucket"

📋 Permissions Boundaries
   └─ Attached to: Users, Roles
   └─ Define: Maximum permissions (don't grant, but limit)
   └─ Example: "Can't access databases, max 10 EC2 instances"

📋 Organization SCPs (Service Control Policies)
   └─ Attached to: Organization, OUs, accounts
   └─ Define: Account-wide limits
   └─ Example: "No one can disable CloudTrail"
```

### Policy Evaluation Logic

```
Request arrives
  ↓
1. Check Organization SCP
   └─ If Deny → ACCESS DENIED
   └─ If implicit Deny → continue
  ↓
2. Check Resource-Based Policy
   └─ If Allow → continue checking Identity-Based
   └─ If Deny → ACCESS DENIED
  ↓
3. Check Identity-Based Policy (User/Role)
   └─ If Allow → check Permissions Boundary
   └─ If Deny → ACCESS DENIED
  ↓
4. Check Permissions Boundary
   └─ If Boundary allows → ACCESS ALLOWED
   └─ If Boundary Deny → ACCESS DENIED
  ↓
Result: ACCESS ALLOWED
```

### AWS Managed vs Customer Managed Policies

```
AWS Managed Policies:
  - Created by AWS
  - Maintained by AWS
  - Read-only
  - Can't be modified
  - Examples: AdministratorAccess, PowerUserAccess

  List:
  - arn:aws:iam::aws:policy/AdministratorAccess
  - arn:aws:iam::aws:policy/PowerUserAccess
  - arn:aws:iam::aws:policy/ReadOnlyAccess

Customer Managed Policies:
  - Created by you
  - You maintain and update
  - Can be modified/versioned
  - Full control
  - Can be attached to multiple principals
```

---

## 6. Policy Structure & Syntax

### Basic Policy Structure

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket/*"
    },
    {
      "Effect": "Deny",
      "Action": "iam:*",
      "Resource": "*"
    }
  ]
}
```

### Common Statement Combinations

```python
# 1. Allow specific action on specific resource
{
    "Effect": "Allow",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/documents/*"
}

# 2. Allow multiple actions on multiple resources
{
    "Effect": "Allow",
    "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
    ],
    "Resource": [
        "arn:aws:s3:::my-bucket/*",
        "arn:aws:s3:::backup-bucket/*"
    ]
}

# 3. Deny all (explicit deny overrides allow)
{
    "Effect": "Deny",
    "Action": "*",
    "Resource": "*"
}

# 4. Conditional access
{
    "Effect": "Allow",
    "Action": "s3:*",
    "Resource": "*",
    "Condition": {
        "IpAddress": {
            "aws:SourceIp": "203.0.113.0/24"
        },
        "TimeGreaterThan": {
            "aws:CurrentTime": "2024-01-01T00:00:00Z"
        }
    }
}
```

### Principal Specification (for Resource Policies)

```json
"Principal": {
  "AWS": "arn:aws:iam::123456789:user/alice",    // Specific user
  "Service": "lambda.amazonaws.com",               // Service
  "AWS": "*",                                      // Anyone
  "AWS": "arn:aws:iam::123456789:root"            // Account root
}
```

### Action & Resource Wildcards

```
s3:GetObject        - Exact action
s3:*                - All S3 actions
*                   - All AWS services & actions

arn:aws:s3:::bucket-name              - Entire bucket
arn:aws:s3:::bucket-name/prefix/*     - Prefix in bucket
arn:aws:s3:::bucket-name/*            - All objects
*                                     - All resources
```

---

## 7. Resource-Based Policies

### S3 Bucket Policy

```python
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Principal": {
                "AWS": "arn:aws:iam::123456789:user/alice"
            },
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::my-bucket/*"
        },
        {
            "Principal": "*",
            "Effect": "Deny",
            "Action": "s3:*",
            "Resource": "*",
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}

s3 = boto3.client('s3')
s3.put_bucket_policy(
    Bucket='my-bucket',
    Policy=json.dumps(bucket_policy)
)
```

### Lambda Resource Policy

```python
lambda_client = boto3.client('lambda')

lambda_client.add_permission(
    FunctionName='my-function',
    StatementId='AllowS3Invoke',
    Action='lambda:InvokeFunction',
    Principal='s3.amazonaws.com',
    SourceArn='arn:aws:s3:::my-bucket'
)
```

### SQS Queue Policy

```python
sqs = boto3.client('sqs')

queue_policy = {
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "sns.amazonaws.com"
            },
            "Action": "SQS:SendMessage",
            "Resource": "arn:aws:sqs:us-east-1:123456789:MyQueue",
            "Condition": {
                "ArnEquals": {
                    "aws:SourceArn": "arn:aws:sns:us-east-1:123456789:MyTopic"
                }
            }
        }
    ]
}

sqs.set_queue_attributes(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789/MyQueue',
    Attributes={
        'Policy': json.dumps(queue_policy)
    }
)
```

---

## 8. Cross-Account Access

### Setup Cross-Account Role

```
Account A (Trusting Account)
Account B (Trusted Account - your AWS account)

Want: Allow specific role in Account B to access resources in Account A
```

### Step 1: Create Role in Account A

```python
# In Account A
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::222222222222:role/CrossAccountRole"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

iam.create_role(
    RoleName='CrossAccountAccessRole',
    AssumeRolePolicyDocument=json.dumps(trust_policy),
    Description='Allows cross-account access from Account B'
)
```

### Step 2: Add Permissions to Cross-Account Role

```python
# Grant permissions in Account A
permissions_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::account-a-bucket",
                "arn:aws:s3:::account-a-bucket/*"
            ]
        }
    ]
}

iam.put_role_policy(
    RoleName='CrossAccountAccessRole',
    PolicyName='S3Access',
    PolicyDocument=json.dumps(permissions_policy)
)
```

### Step 3: Assume Cross-Account Role from Account B

```python
# In Account B
sts = boto3.client('sts')

response = sts.assume_role(
    RoleArn='arn:aws:iam::111111111111:role/CrossAccountAccessRole',
    RoleSessionName='CrossAccountSession'
)

# Use cross-account credentials
credentials = response['Credentials']
s3 = boto3.client(
    's3',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

# Now access Account A resources
response = s3.list_objects_v2(Bucket='account-a-bucket')
```

---

## 9. Temporary Credentials & STS

### STS Services

```
AWS Security Token Service (STS) provides:
  1. AssumeRole - Get credentials for a role
  2. AssumeRoleWithWebIdentity - Assume role using web identity (Cognito, Google, etc)
  3. AssumeRoleWithSAML - Assume role using SAML
  4. GetSessionToken - Get temporary credentials for MFA
  5. GetCallerIdentity - Check who you are
```

### GetSessionToken with MFA

```python
# Get temporary credentials with MFA
sts = boto3.client('sts')

response = sts.get_session_token(
    DurationSeconds=3600,  # 1 hour
    SerialNumber='arn:aws:iam::123456789:mfa/alice',
    TokenCode='123456'  # 6-digit MFA code
)

credentials = response['Credentials']
# These credentials are valid for 1 hour even if MFA device is offline
```

### GetCallerIdentity

```python
# Check who you are
response = sts.get_caller_identity()

print(f"Account ID:  {response['Account']}")
print(f"User ID:     {response['UserId']}")
print(f"ARN:         {response['Arn']}")
# Returns: arn:aws:iam::123456789:user/alice
```

### Temporary Credentials Structure

```
AccessKeyId:        ASIXXXXXXXXX (starts with ASIA)
SecretAccessKey:    wJXXXXXXX...
SessionToken:       FwoGZXIvYXdzEAX...

Valid for:          15 minutes to 12 hours (role-dependent)
Can refresh:        Yes, need to re-assume role
```

---

## 10. MFA (Multi-Factor Authentication)

### Setting Up MFA

```python
# Create virtual MFA device
response = iam.create_virtual_mfa_device(
    VirtualMFADeviceName='alice-mfa'
)

# Response includes QR code
# User scans with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)

base32_string_for_qr = response['VirtualMFADevice']['Base32StringSeed']
print(f"QR Code String: {base32_string_for_qr}")

# User provides two consecutive MFA codes to enable
iam.enable_mfa_device(
    UserName='alice',
    SerialNumber=response['VirtualMFADevice']['SerialNumber'],
    AuthenticationCode1='123456',  # First code from app
    AuthenticationCode2='654321'   # Second code from app (30s later)
)

print("✓ MFA enabled for alice")
```

### Accessing AWS with MFA

```python
# CLI with MFA
"""
aws s3 ls \
  --serial-number arn:aws:iam::123456789:mfa/alice \
  --token-code 123456
"""

# Boto3 with MFA
sts = boto3.client('sts')

response = sts.get_session_token(
    DurationSeconds=43200,  # 12 hours
    SerialNumber='arn:aws:iam::123456789:mfa/alice',
    TokenCode='123456'
)

# Use returned credentials
session = boto3.Session(
    aws_access_key_id=response['Credentials']['AccessKeyId'],
    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
    aws_session_token=response['Credentials']['SessionToken']
)

s3 = session.client('s3')
```

### MFA Best Practices

```
✓ Enable MFA for all human users (especially privileged)
✓ Use FIDO2/U2F if possible (most secure)
✓ Virtual MFA (Google Authenticator) if FIDO2 unavailable
✓ Never disable MFA for production users
✓ Keep backup recovery codes safe
```

---

## 11. Access Keys & Secrets

### Creating Access Keys

```python
# Create access key for a user
response = iam.create_access_key(UserName='alice')

access_key_id = response['AccessKey']['AccessKeyId']
secret_access_key = response['AccessKey']['SecretAccessKey']

print(f"Access Key ID:  {access_key_id}")
print(f"Secret Access Key:  {secret_access_key}")

# ⚠️ IMPORTANT: Save secret key immediately - can't retrieve later!
# Store in secure location (AWS Secrets Manager, parameter store)
```

### Active Keys & Rotation

```python
# List access keys for a user
response = iam.list_access_keys(UserName='alice')

for key_metadata in response['AccessKeyMetadata']:
    print(f"{key_metadata['AccessKeyId']} | Status: {key_metadata['Status']}")
    print(f"  Created: {key_metadata['CreateDate']}")

# Access key age
age = (datetime.now(key_metadata['CreateDate'].tzinfo) -
       key_metadata['CreateDate']).days
print(f"  Age: {age} days")

# Rotate access keys
# Step 1: Create new key
new_key = iam.create_access_key(UserName='alice')

# Step 2: Update application to use new key
# (Verify new key works)

# Step 3: Deactivate old key
iam.update_access_key(
    UserName='alice',
    AccessKeyId='AKIXXXXXXXXX',
    Status='Inactive'
)

# Step 4: After verification, delete old key
iam.delete_access_key(
    UserName='alice',
    AccessKeyId='AKIXXXXXXXXX'
)
```

### Access Key Security

```
⚠️ NEVER commit access keys to version control
⚠️ NEVER share access keys over email/Slack
⚠️ Rotate every 90 days (or immediately if leaked)
⚠️ Use environment variables or AWS credentials file, not hardcoded
⚠️ Use IAM roles for EC2/Lambda (no access keys needed)

✓ Store in AWS Secrets Manager
✓ Use least privilege
✓ Monitor with CloudTrail
✓ Deactivate if unused
✓ Use temporary credentials (STS) when possible
```

---

## 12. IAM Best Practices

### Principle of Least Privilege

```
❌ DON'T: Give AdministratorAccess to everyone
❌ DON'T: Save passwords in code
❌ DON'T: Share AWS account credentials

✓ DO: Grant only what's needed for the job
✓ DO: Use roles instead of users
✓ DO: Separate environments (dev/staging/prod)
✓ DO: Regular access reviews
```

### IAM Best Practices Checklist

```
[✓] Enforce strong passwords/MFA
[✓] Use roles for applications (not users)
[✓] Enable CloudTrail for all API calls
[✓] Regularly review permissions
[✓] Rotate access keys every 90 days
[✓] Remove unused users/roles
[✓] Use permissions boundaries
[✓] Tag resources for cost allocation
[✓] Monitor with CloudWatch/IAM Access Analyzer
[✓] Document access decisions
```

---

## 13. Troubleshooting & Debugging

### AccessDenied Errors

```python
# Check user's permissions
response = iam.get_user_policy(
    UserName='alice',
    PolicyName='S3Access'
)

# Check all policies attached to user
policies = iam.list_user_policies(UserName='alice')
attached = iam.list_attached_user_policies(UserName='alice')

# Get attached policy details
for policy in attached['AttachedPolicies']:
    policy_version = iam.get_policy(PolicyArn=policy['PolicyArn'])
    policy_document = iam.get_policy_version(
        PolicyArn=policy['PolicyArn'],
        VersionId=policy_version['Policy']['DefaultVersionId']
    )
    print(json.dumps(policy_document['PolicyVersion']['Document'], indent=2))
```

### Simulating Access

```python
# Simulate API call without actually making it
response = iam.simulate_principal_policy(
    PolicySourceArn='arn:aws:iam::123456789:user/alice',
    ActionNames=['s3:GetObject'],
    ResourceArns=['arn:aws:s3:::my-bucket/file.txt']
)

for result in response['EvaluationResults']:
    print(f"Action: {result['EvalActionName']}")
    print(f"Result: {result['EvalDecision']}")  # allowed/explicitDeny/implicitDeny
    print(f"Matched:  {result.get('EvalResourceName')}")
```

### CloudTrail for Debugging

```python
# Find who made a specific API call
cloudtrail = boto3.client('cloudtrail')

events = cloudtrail.lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'ResourceType',
            'AttributeValue': 's3'
        }
    ],
    MaxResults=10
)

for event in events['Events']:
    print(f"Event: {event['EventName']}")
    print(f"Who: {event['Username']}")
    print(f"When: {event['EventTime']}")
```

---

## 14. Security Analysis Tools

### IAM Access Analyzer

```python
# Create analyzer
access_analyzer = boto3.client('accessanalyzer')

analyzer = access_analyzer.create_analyzer(
    analyzerName='MyAnalyzer',
    type='ACCOUNT'  # or 'ORGANIZATION'
)

# Validate policies
response = access_analyzer.validate_policy(
    policyDocument=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:*",
                "Resource": "*"
            }
        ]
    }),
    policyType='IDENTITY_POLICY'
)

for finding in response['findings']:
    print(f"Finding: {finding['findingType']}")
    print(f"Message: {finding['issueCode']}")
```

### IAM Credential Report

```python
# Generate credential report
iam.generate_credential_report()

import time
time.sleep(2)  # Report generation takes a few seconds

# Get report
report = iam.get_credential_report()

# Parse CSV
import csv
import io

csv_data = csv.DictReader(io.StringIO(report['Content'].decode('utf-8')))

for row in csv_data:
    user = row['user']
    password_enabled = row['password_enabled']
    password_last_changed = row['password_last_changed']
    print(f"{user:20} | Password: {password_enabled:5} | Last changed: {password_last_changed}")
```

---

## 15. Advanced Topics

### Permissions Boundaries

```python
# Create permissions boundary policy
boundary_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        },
        {
            "Effect": "Deny",
            "Action": [
                "iam:*",
                "rds:*"
            ],
            "Resource": "*"
        }
    ]
}

# Create policy
iam.create_policy(
    PolicyName='S3OnlyBoundary',
    PolicyDocument=json.dumps(boundary_policy)
)

# Apply to user (doesn't grant permission, just limits max)
iam.put_user_permissions_boundary(
    UserName='alice',
    PermissionsBoundary='arn:aws:iam::123456789:policy/S3OnlyBoundary'
)

# Now alice's permissions = intersection of:
# - Policies attached to alice
# - S3OnlyBoundary
```

### Session Tags

```python
# Use tags to control access dynamically
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

# Allow only if department tag matches
access_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalTag/Department": "Engineering"
                }
            }
        }
    ]
}
```

### Custom Policies with Variables

```python
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::my-bucket/${aws:username}/*"
        }
    ]
}

# Each user can only access their own prefix
# alice → arn:aws:s3:::my-bucket/alice/*
# bob → arn:aws:s3:::my-bucket/bob/*

# AWS IAM Variable references:
# ${aws:PrincipalTag/TagKey}     - User's tags
# ${aws:username}                - Username
# ${aws:userid}                  - User ID
# ${aws:SourceVpc}               - VPC where request came from
```

---

## 16. CLI Cheat Sheet

```bash
# Create user
aws iam create-user --user-name alice

# List users
aws iam list-users

# Create access key
aws iam create-access-key --user-name alice

# Enable MFA
aws iam enable-mfa-device \
  --user-name alice \
  --serial-number arn:aws:iam::123456789:mfa/alice-device \
  --authentication-code1 123456 \
  --authentication-code2 654321

# Attach policy to user
aws iam attach-user-policy \
  --user-name alice \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create role
aws iam create-role \
  --role-name LambdaRole \
  --assume-role-policy-document file://trust-policy.json

# Get policy
aws iam get-user-policy \
  --user-name alice \
  --policy-name S3Access

# Simulate API call
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789:user/alice \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::my-bucket/*

# Assume role
aws sts assume-role \
  --role-arn arn:aws:iam::123456789:role/LambdaRole \
  --role-session-name my-session
```

---

## 17. Common Scenarios

### Scenario 1: Lambda Needs S3 Access

```python
# 1. Create role with Lambda trust policy
lambda_trust = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role = iam.create_role(
    RoleName='LambdaS3Role',
    AssumeRolePolicyDocument=json.dumps(lambda_trust)
)

# 2. Attach S3 policy to role
s3_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject"],
        "Resource": "arn:aws:s3:::my-bucket/*"
    }]
}

iam.put_role_policy(
    RoleName='LambdaS3Role',
    PolicyName='S3Access',
    PolicyDocument=json.dumps(s3_policy)
)

# 3. Attach role to Lambda function
lambda_client = boto3.client('lambda')
lambda_client.create_function(
    FunctionName='MyFunction',
    Runtime='python3.9',
    Role=role['Role']['Arn'],  # Use role ARN
    Handler='index.handler',
    Code={'ZipFile': b'...'}
)
```

### Scenario 2: EC2 Instance Assumes Role

```python
# 1. Create instance profile
instance_profile = iam.create_instance_profile(
    InstanceProfileName='EC2S3Profile'
)

# 2. Create role
ec2_trust = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

role = iam.create_role(
    RoleName='EC2S3Role',
    AssumeRolePolicyDocument=json.dumps(ec2_trust)
)

# 3. Attach policy to role
s3_policy = {"Version": "2012-10-17", "Statement": [...]}
iam.put_role_policy(
    RoleName='EC2S3Role',
    PolicyName='S3Access',
    PolicyDocument=json.dumps(s3_policy)
)

# 4. Add role to instance profile
iam.add_role_to_instance_profile(
    InstanceProfileName='EC2S3Profile',
    RoleName='EC2S3Role'
)

# 5. Launch EC2 with instance profile
ec2 = boto3.client('ec2')
ec2.run_instances(
    ImageId='ami-0c55b159cbfafe1f0',
    MinCount=1,
    MaxCount=1,
    IamInstanceProfile={'Name': 'EC2S3Profile'}
)
```

### Scenario 3: Cross-Account S3 Bucket Access

```
AccountA (has bucket): 111111111111
Account B (wants access): 222222222222

Flow:
1. Create role in Account A
2. Trust Account B
3. Account B assumes role
4. Access S3 in Account A
```

---

## 18. Best Practices Summary

```
🔒 Security
  ├─ Root account: MFA-only access, not for daily work
  ├─ Users: One per person, never share
  ├─ Roles: Use for services/cross-account
  ├─ Passwords: 12+ characters, enforced history
  ├─ MFA: Required for all human users
  └─ Keys: Rotate every 90 days

👤 Access Control
  ├─ Least privilege: Only needed permissions
  ├─ Deny overrides Allow: Explicit denies matter
  ├─ Boundaries: Limit max permissions
  ├─ Conditions: Restrict by IP, time, VPC
  └─ Resources: Specific ARNs, not wildcards

📋 Management
  ├─ Groups: Team-level permissions
  ├─ Policies: Version and tag
  ├─ Review: Quarterly access reviews
  ├─ Audit: CloudTrail all API calls
  └─ Monitor: CloudWatch for suspicious activity

🚀 Automation
  ├─ IaC: Infrastructure as Code (CloudFormation/Terraform)
  ├─ CI/CD: Automated testing of policies
  ├─ Secrets: AWS Secrets Manager for rotation
  ├─ Federation: SSO for centralized identity
  └─ Automation: Lambda for compliance checking
```
