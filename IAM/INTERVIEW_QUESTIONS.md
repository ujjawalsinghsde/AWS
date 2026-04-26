# IAM Interview Questions - Comprehensive

## 1. Fundamental Questions

### Basic Concepts

1. **What is IAM (Identity & Access Management)?**
   - Service for managing AWS access and permissions
   - Controls: Who, What, When, Where
   - Who: Users, Groups, Roles
   - What: Actions/permissions (s3:GetObject)
   - When: Time-based conditions
   - Where: IP-based, MFA, resource-based

2. **Explain IAM components.**
   - **Users**: Individual with AWS account
   - **Groups**: Collection of users with same permissions
   - **Roles**: Assumable identity (no credentials)
   - **Policies**: JSON permission documents
   - **Temporary Credentials**: STS-issued, time-limited

3. **IAM policy structure (JSON).**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "S3Access",
         "Effect": "Allow",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::bucket/*",
         "Condition": {
           "IpAddress": {
             "aws:SourceIp": "203.0.113.0/24"
           }
         }
       }
     ]
   }
   ```

4. **Explain ARN (Amazon Resource Name).**
   - Unique identifier for AWS resources
   - Format: `arn:partition:service:region:account-id:resource-type/resource-id`
   - Examples:
     - `arn:aws:s3:::bucket-name`
     - `arn:aws:iam::account:role/role-name`
     - `arn:aws:rds:us-east-1:account:db:database`
   - Wildcards: * for any value

5. **Managed vs Inline Policies.**
   - **Managed Policies**: Standalone, reusable, version-controlled
     - AWS-managed: Pre-built by AWS
     - Customer-managed: Created and maintained by you
   - **Inline Policies**: Embedded in user/group/role, 1-to-1 relationship
   - Recommendation: Use managed policies (better governance)

---

## 2. Intermediate Scenarios

### Access Control & Authorization

6. **Scenario: Developer needs access to specific S3 bucket, nothing else.**
   - Least privilege policy:
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
           "arn:aws:s3:::specific-bucket",
           "arn:aws:s3:::specific-bucket/*"
         ]
       }
     ]
   }
   ```
   - Never: Use wildcards for production buckets
   - Never: Grant s3:* permission

7. **Scenario: EC2 instance needs to access RDS database.**
   - Use: Instance profile (no long-term credentials)
   - Steps:
     1. Create IAM role with RDS permissions
     2. Attach to EC2 instance (instance profile)
     3. EC2 SDK uses temporary credentials automatically
     4. RDS security group allows from EC2 instance role
   - Benefits: No hardcoded credentials, automatic rotation

### Cross-Account & Federation

8. **Cross-account access: Account A needs Account B resources.**
   - Account B setup:
     1. Create role with permissions
     2. Trust policy: Allow Account A to assume
   - Account A setup:
     1. User/role can assume role in Account B
   - Flow:
     1. User calls STS AssumeRole
     2. Gets temporary credentials
     3. Uses across to access Account B

9. **SAML Federation for enterprise SSO.**
   - External Identity Provider (Okta, AD)
   - SAML assertion: Contains user identity
   - IAM: Trust relationship with IdP
   - Flow:
     1. User authenticates with IdP
     2. IdP returns SAML assertion
     3. AWS STS converts to temporary credentials
     4. User accesses AWS resources
   - Benefit: Centralized user management

### Permission Boundaries

10. **Implement permission boundaries for safe delegation.**
    - Problem: Admin creates users with unlimited access
    - Solution: Permission boundary (maximum policy)
    - User effective permissions: User policy ∩ Boundary policy
    ```json
    {
      "PermissionsBoundary": {
        "PermissionsBoundaryArn": "arn:aws:iam::account:policy/boundary-policy"
      }
    }
    ```
    - Example: Team lead manages team, cannot elevate own privileges

---

## 3. Advanced Scenarios

### Security & Compliance

11. **Secure IAM strategy: Root account protection.**
    - Root account: Has all permissions, dangerous
    - Actions:
      1. Enable MFA on root (hardware security key)
      2. Never use for daily operations
      3. Create admin user instead
      4. Use root only for account recovery
      5. Monitor root login (CloudTrail)
    - Principle: Separation of duties

12. **Enforce MFA for production access.**
    - Policy: Deny all unless MFA present
    ```json
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
    ```
    - Except: Allow without MFA to set up MFA
    - Impact: Extra step but critical security control

13. **Rotate access keys every 90 days.**
    - Challenge: Applications use static credentials
    - Solution:
      1. Create new access key
      2. Update applications gradual
      3. Deactivate old key (2 week grace)
      4. Delete after grace period
    - CloudTrail: Audit who created/deleted keys
    - Tool: IAM Access Analyzer for unused credentials

### Tag-Based Access Control

14. **Use resource tags for fine-grained access control.**
    - Policy: Allow EC2 termination only on "Environment=dev"
    ```json
    {
      "Effect": "Allow",
      "Action": "ec2:TerminateInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringEquals": {
          "ec2:ResourceTag/Environment": "dev"
        }
      }
    }
    ```
    - Benefits: Flexibility, scalability, cleaner policies
    - Use case: Different access levels by environment, project, team

---

## 4. Real-World Scenarios

15. **Scenario: Developer accidentally deleted production database.**
    - Investigation:
      1. CloudTrail logs: Who, what, when
      2. IAM permissions: Was deletion allowed?
      3. Recovery: RDS snapshots restore
    - Prevention:
      1. IAM policy: Deny delete for production
      2. MFA requirement for production
      3. Approval gates for destructive actions
      4. Separate production/dev AWS accounts

16. **Implement least privilege in development team.**
    - Users: Junior, Mid-level, Senior
    - Junior:
      - EC2: Start/stop (can't terminate)
      - RDS: Read-only queries
      - No IAM/VPC changes
    - Senior:
      - All permissions
      - Approval required for sensitive actions

17. **Audit IAM permissions for compliance.**
    - Tools:
      - IAM Access Analyzer: Identifies unused permissions
      - CloudTrail: All API actions logged
      - Config: Monitors IAM configuration
    - Process:
      1. Monthly: Review new users/roles
      2. Quarterly: Audit permissions per user
      3. Remove: Unused permissions, inactive users
      4. Document: Approved use cases

---

## 5. Best Practices

18. **IAM best practices summary:**
    - Root account: MFA-protected, not for daily use
    - Users: One per person, specific not shared
    - Groups: Organize by role/team
    - Roles: For AWS services and federation
    - Policies: Least privilege, specific resources
    - MFA: Required for sensitive operations
    - Access keys: Rotate every 90 days
    - CloudTrail: Always enabled, audit logs
    - Review: Monthly access review, remove unused
    - Tags: Use for fine-grained access control
    - Federation: Use SAML/OIDC for external users

---

## 6. Hands-On Examples

19. **Create IAM user with access key (CLI) and policy:**
    ```python
    import boto3

    iam = boto3.client('iam')

    # Create user
    iam.create_user(UserName='john.doe')

    # Create access key
    key_response = iam.create_access_key(UserName='john.doe')
    print(f"Access Key: {key_response['AccessKey']['AccessKeyId']}")

    # Attach policy
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::my-bucket/*"
            }
        ]
    }

    iam.put_user_policy(
        UserName='john.doe',
        PolicyName='S3ReadPolicy',
        PolicyDocument=json.dumps(policy_document)
    )
    ```

20. **AssumeRole for cross-account access:**
    ```python
    import boto3

    sts = boto3.client('sts')

    # Assume role in another account
    response = sts.assume_role(
        RoleArn='arn:aws:iam::ACCOUNT-B:role/CrossAccountRole',
        RoleSessionName='cross-account-session'
    )

    # Use temporary credentials
    credentials = response['Credentials']

    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    # Access Account B resources
    response = s3.list_buckets()
    ```

21. **Policy to restrict by IP address:**
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "ec2:*",
          "Resource": "*",
          "Condition": {
            "IpAddress": {
              "aws:SourceIp": [
                "203.0.113.0/24",
                "198.51.100.0/24"
              ]
            }
          }
        },
        {
          "Effect": "Deny",
          "Action": "ec2:TerminateInstances",
          "Resource": "*"
        }
      ]
    }
    ```

---

## Tips for Interview Success

- **JSON policies**: Practice writing AWS IAM policies
- **Least privilege**: Default mindset for all questions
- **ARN format**: Know resource naming conventions
- **Cross-account**: Common real-world requirement
- **MFA importance**: Always mention for security
- **CloudTrail**: Essential for auditing and compliance
- **Resource-based policies**: S3 bucket policy, Lambda trust, etc.
- **Conditions**: Time-based, IP-based, MFA-based access control
- **Tags**: Modern approach to RBAC (role-based access control)
- **Federation**: Enterprise-scale user management

