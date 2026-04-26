# VPC & Networking Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is a VPC and why is it important?**
   - Virtual Private Cloud: Isolated network environment within AWS
   - Control over IP address range (CIDR block, e.g., 10.0.0.0/16)
   - Subnets: Network segments within VPC (public/private)
   - Security Groups: Stateful firewall for EC2/RDS/Lambda
   - NACLs: Stateless firewall at subnet level
   - Route Tables: Define traffic routing

2. **Explain public vs private subnets.**
   - **Public**: Has internet gateway, resources get public IPs, accessible from internet
   - **Private**: No direct internet access, resources have private IPs only
   - Private with internet: Use NAT Gateway (in public subnet)
   - Resources in private: Cannot initiate inbound from internet

3. **What are Security Groups and NACLs?**
   - **Security Groups**: Instance-level, stateful (return traffic auto-allowed), default DENY
   - **NACLs**: Subnet-level, stateless (need allow and deny rules), ordered rules
   - Security Groups: Allow access to specific resources
   - NACLs: Block ranges of IPs at subnet level

4. **Explain VPC peering and transit between VPCs.**
   - **VPC Peering**: Direct connection between two VPCs
   - Non-transitive: VPC A peers with B, B peers with C, but A doesn't connect to C
   - Use Transit Gateway for hub-and-spoke model
   - Same region or cross-region peering possible

5. **What are AWS endpoints and why use them?**
   - **Gateway Endpoints**: S3, DynamoDB (free, no charge for traffic)
   - **Interface Endpoints**: Other AWS services, Lambda, EC2, etc (charged)
   - Use case: Private access to AWS services without internet
   - Security: Keep data within AWS network (no NAT Gateway needed)

---

## 2. Intermediate Scenarios

### Connectivity
6. **Scenario: EC2 in private subnet needs to download packages from Internet. Solution?**
   - Answer: NAT Gateway
   - Setup:
      1. Create NAT Gateway in public subnet (requires Elastic IP)
      2. Add route in private subnet: 0.0.0.0/0 → NAT Gateway
      3. EC2 can now download packages
   - Cost: NAT Gateway charges per hour + data processing
   - High availability: Create NAT Gateway in each AZ

7. **Scenario: Your on-premises data center needs to connect to VPC. Design hybrid network.**
   - Options:
     1. **VPN**: Encrypted tunnel, slower, cheaper
     2. **Direct Connect**: Dedicated connection, faster, more expensive
     3. **VPN + Direct Connect**: Redundancy
   - With VPN:
     - CustomerGateway (on-premises router)
     - VirtualPrivateGateway (VPC side)
     - VPN connection between them
     - Enable route propagation

---

## 3. Advanced Scenarios

### Multi-AZ & Disaster Recovery
8. **Design a highly available VPC architecture across multiple AZs.**
   - Public subnets in 3 AZs:
     - Each has 1 NAT Gateway
     - Each has route to Internet Gateway
   - Private subnets in 3 AZs:
     - Each has route to its AZ's NAT Gateway
     - Or use VPC endpoints for AWS services
   - Application Load Balancer:
     - Spans 3 subnets for HA
     - Health checks ensure traffic only to healthy instances
   - RDS Multi-AZ: Synchronous replication to secondary subnet

9. **Scenario: Subnet runs out of IP addresses. Plan for IP growth.**
   - Amazon reserves 5 IPs per subnet (network, gateway, broadcast, etc)
   - Calculation: /24 subnet = 256 IPs, 5 reserved = 251 available
   - If running out:
     1. Don't reallocate subnet CIDR (EC2 instances already assigned)
     2. Create new subnet with larger CIDR
     3. Migrate instances to new subnet
     4. Or expand VPC CIDR (complex, all subnets affected)
   - Best practice: Plan IP space upfront

---

## 4. Security & Isolation

10. **Design a VPC for multi-tenant application (customer isolation).**
    - Approach 1: Shared VPC, different Security Groups per tenant
      - Cost-effective, simpler management
      - Isolation via NACLs and Security Groups
    - Approach 2: VPC per tenant
      - Complete isolation, easier compliance
      - Higher cost, management overhead
    - Choose based on compliance requirements

11. **Implement least-privilege security group rules.**
    - Default: Deny all (implicit)
    - Add only necessary inbound/outbound:
      - Web server: 80, 443
      - Database: 3306 only from app server SG
      - SSH: Only from bastion host (or use SSM Session Manager)
    - Never use 0.0.0.0/0 except for HTTP/HTTPS public services
    - Use security group references instead of CIDR (e.g., app-sg → db-sg)

---

## 5. Real-World Scenarios

12. **Scenario: Instances can't reach RDS in private subnet. Troubleshoot.**
    - Check:
      1. RDS security group: Allows port 3306 from EC2 SG
      2. Route table: Private subnet has route to RDS subnet
      3. NACLs: Both EC2 and RDS subnets allow traffic
      4. RDS endpoint: Correct endpoint used
    - Use VPC Flow Logs to see traffic:
      ```bash
      # Create flow logs, then query:
      SELECT srcaddr, dstaddr, dstport FROM athena_table
      WHERE dstaddr = 'rds-ip' AND dstport = 3306
      ```

---

## 6. Flow Logs & Monitoring

13. **How do you debug VPC connectivity issues?**
    - VPC Flow Logs:
      - Capture metadata (src IP, dst IP, port, protocol, accepted/rejected)
      - Send to CloudWatch Logs or S3
      - Use CloudWatch Insights to query
    - Tools: mtr, traceroute, ping from EC2
    - Test with: `nc -zv hostname port`

---

## 7. Hands-On

14. **Write Terraform to create VPC with public/private subnets:**
    ```hcl
    resource "aws_vpc" "main" {
      cidr_block           = "10.0.0.0/16"
      enable_dns_hostnames = true
    }

    resource "aws_subnet" "public" {
      vpc_id            = aws_vpc.main.id
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      map_public_ip_on_launch = true
    }

    resource "aws_subnet" "private" {
      vpc_id            = aws_vpc.main.id
      cidr_block        = "10.0.2.0/24"
      availability_zone = "us-east-1a"
    }

    resource "aws_internet_gateway" "main" {
      vpc_id = aws_vpc.main.id
    }

    resource "aws_route_table" "public" {
      vpc_id = aws_vpc.main.id

      route {
        cidr_block      = "0.0.0.0/0"
        gateway_id      = aws_internet_gateway.main.id
      }
    }

    resource "aws_route_table_association" "public" {
      subnet_id      = aws_subnet.public.id
      route_table_id = aws_route_table.public.id
    }
    ```

---

## Tips for Interview Success

- **Draw diagrams**: VPC questions benefit from visual explanation
- **Understand OSI layers**: Security Groups (L4), NACLs (L3-L4)
- **Stateful vs Stateless**: Key difference between SG and NACL
- **IP planning**: CIDR notation, subnet sizing
- **High availability**: Multi-AZ design is critical
- **Cost considerations**: NAT Gateway, data transfer charges

---

# IAM Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is IAM and its core components?**
   - Identity & Access Management: Control who (identity) can do what (actions) on which resources
   - Components:
     - Users: Individual AWS account holders
     - Groups: Collection of users with same permissions
     - Roles: Assumption-based identity (for services, cross-account, federation)
     - Policies: JSON documents defining permissions
     - Temporary security credentials: For federated access

2. **Explain IAM policy structure (JSON).**
   - Principal: Who (user, role, service)
   - Action: What (s3:GetObject, ec2:DescribeInstances)
   - Resource: Which (arn:aws:s3:::bucket-name/*)
   - Effect: Allow or Deny
   - Condition: When (IP address, time, etc)

3. **What are managed vs inline policies?**
   - **Managed Policies**: Standalone, reusable, version control, AWS-managed or customer-managed
   - **Inline Policies**: Embedded in user/group/role, one-to-one relationship, deleted with principal
   - Best practice: Use managed policies (better version control)

4. **Explain the principal of least privilege.**
   - Grant minimum permissions needed
   - Start with no access, add specific permissions as needed
   - Use conditions to further restrict (IP, time, MFA)
   - Audit regularly, remove unused permissions
   - Implement using resource-based policies + role assumptions

5. **What is an IAM role and when to use it?**
   - Temporary credentials without long-term keys
   - EC2: Use instance profiles instead of hardcoded creds
   - Lambda: Use execution role for AWS service access
   - Cross-account: AssumeRole for temporary access
   - Federation: SAML, OpenID Connect for external users

---

## 2. Intermediate Scenarios

### Cross-Account & Federation
6. **Scenario: Team in different AWS account needs to access S3 bucket. Design solution.**
   - Account A (S3): Create role with S3 permissions
   - Trust policy: Allow Account B role to assume
   - Account B: Create role users can assume
   - User in B: AssumeRole from A, get temporary credentials
   - Verification: Use sts:GetCallerIdentity to confirm identity

7. **Scenario: External partner needs temporary access to EC2 console. Solution?**
   - Don't: Create IAM user in your account (permission to delete)
   - Do:
     1. Create role with EC2 read-only permissions
     2. Accept SAML assertion from partner IdP
     3. Partner federation link → assumes role
     4. Get temporary credentials automatically
     5. Access expires when session ends
   - Alternative: Federate with Okta, Active Directory, Ping

### Permission Boundaries & Delegation
8. **Use permission boundaries to delegate AWS account management safely.**
   - Problem: Admin user can create new users with any permissions
   - Solution: Permission boundary (parent policy)
     - User + attached policy: Intersection determines effective permissions
     - Prevents privilege escalation
     - Example: Delegate team lead to manage team without granting admin
   - Implementation:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": "*",
           "Resource": "*",
           "Condition": {
             "StringEquals": {
               "iam:PermissionsBoundary": "boundary-policy"
             }
           }
         }
       ]
     }
     ```

---

## 3. Advanced Scenarios

### MFA & Security
9. **Design a secure IAM strategy with MFA.**
   - Enforce MFA for:
     - Console access (especially admin users)
     - API calls (using STS GetSessionToken)
     - Cross-account role assumption
   - AWS Config rules to detect non-MFA access
   - Deny all except MFA:
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

### Resource-Based Policies
10. **Use resource-based policies for secure cross-service access.**
    - Trust relationship: Role trusts EC2 service
    - S3 bucket policy: Allows specific role to GetObject
    - SNS topic policy: Allows Lambda to publish
    - Example: Lambda executes without explicit S3 permissions
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Effect": "Allow",
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

### Audit & Compliance
11. **Implement IAM auditing and compliance.**
    - CloudTrail: All API calls logged (who, what, when)
    - IAM Access Analyzer: Identifies external access
    - Config Rules: Check for unencrypted S3, root MFA, etc
    - credential_reports: API access keys by user
    - Access Advisor: Shows service access by principal
    - CloudWatch: Monitor unauthorized attempts
    - Regular reviews: Quarterly user access review

---

## 4. Real-World Scenarios

12. **Scenario: Developer's access keys compromised. Emergency response.**
    - Immediate:
      1. Deactivate the access key (not delete initially)
      2. Check CloudTrail for unauthorized API calls
      3. Review what was accessed
      4. Change important credentials (DB passwords, API keys)
      5. Enable MFA if not already
    - Investigation:
      - CloudTrail logs show who, what, when
      - Identify any resource changes
      - Check billing for unexpected costs
    - Long-term:
      - Delete old access key
      - Issue new access key
      - Implement access key rotation policy (every 90 days)
      - Educate team on credential security

13. **Scenario: Need to grant permissions to only specific EC2 instances by tag.**
    - Use resource tags in condition:
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
    - Only allows terminating instances tagged with Environment=dev

---

## 5. Best Practices

14. **IAM best practices checklist:**
    - Root account: MFA only, no access keys
    - Users: One per person, not applications
    - Groups: Organize permissions by role
    - Roles: For AWS services and cross-account
    - Policies: Least privilege, specific resources
    - Keys: Rotate every 90 days, use IAM Access Analyzer
    - Audit: CloudTrail logging enabled
    - Review: Monthly access review, removal of unused permissions
    - Federation: SAML/OIDC for external users instead of IAM users

---

## 6. Hands-On Examples

15. **Create a role for Lambda to access S3:**
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "s3:GetObject"
          ],
          "Resource": "arn:aws:s3:::my-bucket/*"
        }
      ]
    }
    ```

16. **Assume role from another AWS account:**
    ```python
    import boto3

    sts = boto3.client('sts')

    # Assume role in Account B
    response = sts.assume_role(
        RoleArn='arn:aws:iam::ACCOUNT_B:role/CrossAccountRole',
        RoleSessionName='session-name'
    )

    credentials = response['Credentials']

    # Use credentials to access resources in Account B
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    s3.list_buckets()
    ```

---

## Tips for Interview Success

- **JSON policies**: Practice reading and writing IAM policies
- **Least privilege**: Default mindset for all permission questions
- **Cross-account scenarios**: Common in real environments
- **MFA importance**: Always mention for security
- **CloudTrail**: Essential for auditing
- **Resource tags**: Powerful way to organize permissions
- **Roles vs Users**: Understand when to use each

