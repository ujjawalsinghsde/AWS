# AWS S3 (Simple Storage Service)

**Python boto3 code:** [s3_operations.py](./s3_operations.py)

---

## Table of Contents

1. [What is AWS S3?](#1-what-is-aws-s3)
2. [Core Concepts](#2-core-concepts)
3. [Storage Classes](#3-storage-classes)
4. [Bucket Configuration](#4-bucket-configuration)
5. [S3 Security](#5-s3-security)
6. [S3 Encryption](#6-s3-encryption)
7. [Data Access Patterns](#7-data-access-patterns)
8. [Versioning & Lifecycle Management](#8-versioning--lifecycle-management)
9. [S3 Replication](#9-s3-replication)
10. [S3 Performance Optimization](#10-s3-performance-optimization)
11. [S3 Event Notifications & Integrations](#11-s3-event-notifications--integrations)
12. [Advanced Features](#12-advanced-features)
13. [S3 Pricing Model](#13-s3-pricing-model)
14. [Common Architectures & Use Cases](#14-common-architectures--use-cases)
15. [S3 CLI Cheat Sheet](#15-s3-cli-cheat-sheet)
16. [Best Practices](#16-best-practices)

---

## 1. What is AWS S3?

**Amazon S3 (Simple Storage Service)** is an object storage service offered by AWS that provides industry-leading scalability, data availability, security, and performance.

### Key Characteristics

- **Object Storage** — Stores data as objects (not files or blocks). Each object = data + metadata + unique key.
- **Unlimited Storage** — No limit on total data; individual objects up to **5 TB**.
- **Global Service** — Buckets are created in specific AWS Regions, but the S3 namespace is global.
- **11 nines durability** — 99.999999999% designed durability (data is redundantly stored across multiple AZs).
- **99.99% availability** — For Standard storage class.
- **Eventual consistency** — S3 provides strong read-after-write consistency for PUTs and DELETEs of objects (since Dec 2020).

### What S3 is NOT

- Not a file system (no true directory hierarchy, no file locking)
- Not a database (no querying by content without S3 Select or Athena)
- Not block storage (use EBS for that)

---

## 2. Core Concepts

### 2.1 Buckets

A **bucket** is a container for objects stored in S3.

- Bucket names are **globally unique** across all AWS accounts.
- Name rules: 3–63 characters, lowercase letters, numbers, hyphens; must start/end with letter or number; no underscores.
- A bucket belongs to a single AWS Region.
- You can create up to **100 buckets** per account by default (can be increased to 1000 via Service Quota).

```text
Example bucket name: my-company-data-lake-prod
```

### 2.2 Objects

An **object** is the fundamental entity stored in S3.

| Component        | Description                                               |
|------------------|-----------------------------------------------------------|
| **Key**          | Unique identifier for the object within a bucket (the "path") |
| **Value**        | The actual data (bytes)                                   |
| **Version ID**   | Used when versioning is enabled                           |
| **Metadata**     | Key-value pairs (system or user-defined)                  |
| **Tags**         | Up to 10 key-value pairs for cost allocation, lifecycle   |
| **Storage Class**| Determines cost/availability trade-off                    |

```text
Object URL format:
https://<bucket-name>.s3.<region>.amazonaws.com/<key>

Example:
https://my-data-bucket.s3.us-east-1.amazonaws.com/reports/2025/january.csv
```

### 2.3 Keys and "Folders"

S3 has a **flat namespace** — there are no real folders. A `/` in a key name is just a character. The S3 console simulates folders for usability.

```text
Key: "reports/2025/january.csv"
     └─ "reports/" and "2025/" are just prefixes, not real directories
```

### 2.4 S3 URL Formats

```text
Path-style (older):    https://s3.<region>.amazonaws.com/<bucket>/<key>
Virtual-hosted style:  https://<bucket>.s3.<region>.amazonaws.com/<key>
```

AWS is deprecating path-style URLs. **Virtual-hosted style is recommended.**

---

## 3. Storage Classes

S3 offers multiple storage classes to optimize cost vs. access frequency.

| Storage Class                    | Use Case                                  | Availability | Min Duration | Retrieval Fee |
|----------------------------------|-------------------------------------------|--------------|--------------|---------------|
| **S3 Standard**                  | Frequently accessed data                  | 99.99%       | None         | None          |
| **S3 Intelligent-Tiering**       | Unknown or changing access patterns       | 99.9%        | None         | None          |
| **S3 Standard-IA**               | Infrequent access, rapid retrieval        | 99.9%        | 30 days      | Per GB        |
| **S3 One Zone-IA**               | Infrequent, non-critical, single AZ       | 99.5%        | 30 days      | Per GB        |
| **S3 Glacier Instant Retrieval** | Archive, milliseconds retrieval           | 99.9%        | 90 days      | Per GB        |
| **S3 Glacier Flexible Retrieval**| Archive, minutes to hours retrieval       | 99.99%       | 90 days      | Per GB        |
| **S3 Glacier Deep Archive**      | Long-term archive, 12-48 hour retrieval   | 99.99%       | 180 days     | Per GB        |
| **S3 Express One Zone**          | Ultra-high performance, single AZ         | 99.95%       | None         | None          |

### Storage Class Decision Guide

```
Access > once a month?
  YES → S3 Standard
  NO  → Access pattern known?
          YES → Infrequent access → S3 Standard-IA or One Zone-IA
          NO  → S3 Intelligent-Tiering (auto-moves between tiers)

Need archive?
  Millisecond retrieval → Glacier Instant Retrieval
  Minutes/hours OK      → Glacier Flexible Retrieval
  Hours OK, cheapest    → Glacier Deep Archive
```

### S3 Intelligent-Tiering

Automatically moves objects between access tiers based on usage patterns. No retrieval fees.

| Tier                        | Triggered After     | Cost vs Standard |
|-----------------------------|---------------------|------------------|
| Frequent Access (default)   | —                   | Same as Standard |
| Infrequent Access           | 30 days no access   | ~40% cheaper     |
| Archive Instant Access      | 90 days no access   | ~68% cheaper     |
| Archive Access (optional)   | 90–730 days         | ~71% cheaper     |
| Deep Archive Access (opt.)  | 180–730 days        | ~95% cheaper     |

---

## 4. Bucket Configuration

### 4.1 Creating a Bucket (AWS CLI)

```bash
# Create bucket in us-east-1
aws s3api create-bucket \
  --bucket my-bucket-name \
  --region us-east-1

# Create bucket in other regions (requires LocationConstraint)
aws s3api create-bucket \
  --bucket my-bucket-name \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1
```

### 4.2 Bucket Versioning

Versioning maintains multiple versions of an object. Protects against accidental deletes and overwrites.

```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket my-bucket-name \
  --versioning-configuration Status=Enabled

# List object versions
aws s3api list-object-versions --bucket my-bucket-name
```

**States:** `Disabled` (default) → `Enabled` → `Suspended` (cannot go back to Disabled)

When you delete a versioned object, S3 adds a **delete marker** instead of removing data.

### 4.3 Bucket Tagging

```bash
aws s3api put-bucket-tagging \
  --bucket my-bucket-name \
  --tagging 'TagSet=[{Key=Environment,Value=Production},{Key=Team,Value=DataEngineering}]'
```

### 4.4 Static Website Hosting

```bash
aws s3 website s3://my-bucket-name/ \
  --index-document index.html \
  --error-document error.html
```

Website endpoint format: `http://<bucket>.s3-website-<region>.amazonaws.com`

### 4.5 Block Public Access

**Enabled by default** at both bucket and account level. Four independent settings:

| Setting                              | Description                                              |
|--------------------------------------|----------------------------------------------------------|
| `BlockPublicAcls`                    | Reject PUT requests that include public ACLs             |
| `IgnorePublicAcls`                   | Ignore all public ACLs on bucket and objects             |
| `BlockPublicPolicy`                  | Reject bucket policies that grant public access          |
| `RestrictPublicBuckets`              | Restrict access to principals within the bucket's account |

```bash
# Disable all public access blocks (use carefully)
aws s3api put-public-access-block \
  --bucket my-bucket-name \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

---

## 5. S3 Security

### 5.1 Security Layers Overview

```
Request to S3 Object
        │
        ▼
  IAM Policies         ← Identity-based (who can do what)
        │
        ▼
  Bucket Policies      ← Resource-based (what can be done to this bucket)
        │
        ▼
  ACLs (legacy)        ← Object/bucket level (mostly deprecated)
        │
        ▼
  Block Public Access  ← Override safety net
        │
        ▼
  Encryption / VPC     ← Data protection & network controls
```

### 5.2 IAM Policies

Control what S3 actions an IAM user/role/group can perform.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket-name/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::my-bucket-name"
    }
  ]
}
```

> **Note:** `ListBucket` applies to the bucket ARN; `GetObject`/`PutObject` apply to `bucket/*`.

### 5.3 Bucket Policies

Resource-based policies attached to a bucket. Can grant access to other AWS accounts, services, or public access.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket-name/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/ABCDEFGHIJKLMN"
        }
      }
    }
  ]
}
```

**Cross-account access example:**

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::987654321098:root"
      },
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-bucket-name/*"
    }
  ]
}
```

### 5.4 Access Control Lists (ACLs)

**Legacy mechanism** — AWS recommends disabling ACLs and using bucket policies instead.

ACL canned values: `private`, `public-read`, `public-read-write`, `authenticated-read`, `bucket-owner-read`, `bucket-owner-full-control`

To disable ACLs (recommended):
```bash
aws s3api put-bucket-ownership-controls \
  --bucket my-bucket-name \
  --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
```

### 5.5 VPC Endpoint for S3

Keep S3 traffic within AWS network using a **Gateway VPC Endpoint** (free).

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxxxxx \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-xxxxxxxx
```

Then restrict bucket access to VPC only:
```json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": ["arn:aws:s3:::my-bucket-name", "arn:aws:s3:::my-bucket-name/*"],
      "Condition": {
        "StringNotEquals": {
          "aws:SourceVpce": "vpce-xxxxxxxx"
        }
      }
    }
  ]
}
```

### 5.6 S3 Access Points

Access Points simplify managing access for shared datasets at scale. Each access point has its own DNS name, network origin control, and access point policy.

```bash
# Create an access point
aws s3control create-access-point \
  --account-id 123456789012 \
  --name my-access-point \
  --bucket my-bucket-name

# Access point ARN format:
# arn:aws:s3:us-east-1:123456789012:accesspoint/my-access-point
```

---

## 6. S3 Encryption

### 6.1 Encryption Types

| Type             | Name                         | Who Manages Keys           |
|------------------|------------------------------|----------------------------|
| **SSE-S3**       | Server-Side with S3 keys     | AWS (fully managed)        |
| **SSE-KMS**      | Server-Side with KMS keys    | AWS KMS (customer-managed) |
| **SSE-C**        | Server-Side with Customer keys | You (key in request headers) |
| **CSE**          | Client-Side Encryption       | You (encrypt before upload)|
| **DSSE-KMS**     | Dual-layer SSE with KMS      | AWS KMS (double encryption)|

### 6.2 SSE-S3 (Default since Jan 2023)

All objects encrypted by default using AES-256. No extra cost.

```bash
# Upload with explicit SSE-S3
aws s3 cp file.csv s3://my-bucket/ \
  --sse AES256
```

### 6.3 SSE-KMS

Provides audit trail via CloudTrail, fine-grained key control, and automatic key rotation.

```bash
# Upload with SSE-KMS using default key
aws s3 cp file.csv s3://my-bucket/ \
  --sse aws:kms

# Upload with SSE-KMS using specific CMK
aws s3 cp file.csv s3://my-bucket/ \
  --sse aws:kms \
  --sse-kms-key-id arn:aws:kms:us-east-1:123456789012:key/mrk-xxxxx
```

**Enforce SSE-KMS via bucket policy:**
```json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

### 6.4 Enforce Default Encryption at Bucket Level

```bash
aws s3api put-bucket-encryption \
  --bucket my-bucket-name \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/mrk-xxxxx"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

> **Bucket Key:** Reduces KMS API calls (and cost) by generating a short-lived bucket-level key. Enable `BucketKeyEnabled: true`.

---

## 7. Data Access Patterns

### 7.1 Pre-Signed URLs

Generate a time-limited URL to allow temporary access to private objects without AWS credentials.

```bash
# Generate pre-signed URL valid for 1 hour (3600 seconds)
aws s3 presign s3://my-bucket/report.pdf \
  --expires-in 3600

# Output:
# https://my-bucket.s3.amazonaws.com/report.pdf?X-Amz-Algorithm=...&X-Amz-Expires=3600...
```

Use cases: share files temporarily, allow uploads without exposing credentials.

**Pre-signed URL for upload (PUT):**
```python
import boto3

s3 = boto3.client('s3')
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'uploads/file.csv'},
    ExpiresIn=3600
)
```

### 7.2 S3 Select

Query data inside an object using SQL — retrieve only the subset you need, reducing data transfer and cost.

Supported formats: **CSV, JSON, Parquet**

```bash
aws s3api select-object-content \
  --bucket my-bucket \
  --key data/records.csv \
  --expression "SELECT * FROM S3Object WHERE age > 30" \
  --expression-type SQL \
  --input-serialization '{"CSV": {"FileHeaderInfo": "USE"}}' \
  --output-serialization '{"CSV": {}}' \
  output.csv
```

### 7.3 S3 Batch Operations

Run operations on billions of objects at scale using a job manifest.

Supported operations:
- `CopyObject`
- `InvokeAWSLambda`
- `DeleteObject`
- `RestoreObject` (from Glacier)
- `PutObjectTagging` / `DeleteObjectTagging`
- `PutObjectAcl`

```bash
# Create a Batch Operations job
aws s3control create-job \
  --account-id 123456789012 \
  --operation '{"LambdaInvoke": {"FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:my-func"}}' \
  --manifest '{"Spec":{"Format":"S3BatchOperations_CSV_20180820","Fields":["Bucket","Key"]},"Location":{"ObjectArn":"arn:aws:s3:::manifests/manifest.csv","ETag":"abc123"}}' \
  --report '{"Bucket":"arn:aws:s3:::reports","Format":"Report_CSV_20180820","Enabled":true,"Prefix":"batch-reports","ReportScope":"AllTasks"}' \
  --priority 10 \
  --role-arn arn:aws:iam::123456789012:role/S3BatchRole
```

### 7.4 Multipart Upload

For objects larger than **100 MB**, use multipart upload for better throughput, resumability, and parallelism. **Required for objects > 5 GB.**

```python
import boto3

s3 = boto3.client('s3')

# Initiate upload
response = s3.create_multipart_upload(Bucket='my-bucket', Key='large-file.bin')
upload_id = response['UploadId']

# Upload parts (each ≥ 5 MB, except last)
part1 = s3.upload_part(
    Bucket='my-bucket', Key='large-file.bin',
    UploadId=upload_id, PartNumber=1, Body=chunk_data
)

# Complete upload
s3.complete_multipart_upload(
    Bucket='my-bucket', Key='large-file.bin',
    UploadId=upload_id,
    MultipartUpload={'Parts': [{'PartNumber': 1, 'ETag': part1['ETag']}]}
)
```

```bash
# High-level CLI (handles multipart automatically)
aws s3 cp large-file.bin s3://my-bucket/ \
  --storage-class STANDARD \
  --expected-size 10737418240  # 10 GB
```

---

## 8. Versioning & Lifecycle Management

### 8.1 Versioning

```text
Versioning States:
  Unversioned (default) → Enabled → Suspended

Enabling versioning:
  - New objects get a version ID
  - Existing objects remain unversioned (version = null)
  - DELETE adds a "delete marker" — does not erase data
  - To permanently delete: must specify version ID
```

```bash
# Delete a specific version permanently
aws s3api delete-object \
  --bucket my-bucket \
  --key file.csv \
  --version-id abc123xyz

# Restore deleted object (by deleting its delete marker)
aws s3api delete-object \
  --bucket my-bucket \
  --key file.csv \
  --version-id <delete-marker-version-id>
```

### 8.2 Lifecycle Rules

Automatically transition objects between storage classes or expire them.

```json
{
  "Rules": [
    {
      "ID": "archive-old-logs",
      "Status": "Enabled",
      "Filter": { "Prefix": "logs/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER" },
        { "Days": 365, "StorageClass": "DEEP_ARCHIVE" }
      ],
      "Expiration": { "Days": 2555 },
      "NoncurrentVersionTransitions": [
        { "NoncurrentDays": 30, "StorageClass": "STANDARD_IA" }
      ],
      "NoncurrentVersionExpiration": { "NoncurrentDays": 90 },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
  ]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration file://lifecycle.json
```

> **Always add `AbortIncompleteMultipartUpload`** — incomplete multipart uploads accumulate storage cost silently.

---

## 9. S3 Replication

### 9.1 Cross-Region Replication (CRR)

Copies objects from a bucket in one region to another region.

**Use cases:** compliance, latency reduction for geographically distributed users, disaster recovery.

### 9.2 Same-Region Replication (SRR)

Copies objects within the same region to another bucket.

**Use cases:** log aggregation across accounts, live replication to test/dev environments.

### 9.3 Replication Configuration

**Prerequisites:** Versioning must be enabled on both source and destination buckets.

```json
{
  "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
  "Rules": [
    {
      "ID": "replicate-data-folder",
      "Status": "Enabled",
      "Filter": { "Prefix": "data/" },
      "Destination": {
        "Bucket": "arn:aws:s3:::destination-bucket",
        "StorageClass": "STANDARD_IA",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": { "Minutes": 15 }
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": { "Minutes": 15 }
        }
      },
      "DeleteMarkerReplication": { "Status": "Enabled" }
    }
  ]
}
```

```bash
aws s3api put-bucket-replication \
  --bucket source-bucket \
  --replication-configuration file://replication.json
```

### 9.4 Replication Behavior

| Scenario                                  | Replicated? |
|-------------------------------------------|-------------|
| New objects after replication enabled     | Yes         |
| Existing objects before rule was created  | No (use S3 Batch to copy) |
| Delete markers                            | Optional (configurable) |
| Objects encrypted with SSE-C             | No          |
| Objects in Glacier/Deep Archive          | No          |

---

## 10. S3 Performance Optimization

### 10.1 Request Rate Limits

S3 scales automatically. Per prefix:

- **3,500 PUT/COPY/POST/DELETE** requests/second
- **5,500 GET/HEAD** requests/second

**To scale beyond this:** use multiple prefixes (S3 partitions by prefix).

```text
Bad (single prefix bottleneck):
  logs/2025/01/file1.csv
  logs/2025/01/file2.csv

Good (multiple prefixes):
  a1b2/logs/file1.csv
  f3g4/logs/file2.csv
  x9y0/logs/file3.csv
```

### 10.2 Transfer Acceleration

Routes uploads/downloads through AWS CloudFront edge locations — faster for geographically distant clients.

```bash
# Enable Transfer Acceleration
aws s3api put-bucket-accelerate-configuration \
  --bucket my-bucket \
  --accelerate-configuration Status=Enabled

# Use the accelerate endpoint
aws s3 cp file.csv s3://my-bucket/ \
  --endpoint-url https://my-bucket.s3-accelerate.amazonaws.com
```

### 10.3 Byte-Range Fetches

Download specific byte ranges of an object in parallel — dramatically speeds up large file downloads.

```bash
# Download bytes 0-9999999 (first 10 MB)
aws s3api get-object \
  --bucket my-bucket \
  --key large-file.bin \
  --range bytes=0-9999999 \
  output-part1.bin
```

### 10.4 S3 Express One Zone

Newest, highest-performance storage class (2023). Millisecond latency, 10x higher request rate than S3 Standard.

```text
Bucket type: "Directory bucket" (different from general purpose bucket)
Good for: ML training data, HPC, real-time analytics
```

---

## 11. S3 Event Notifications & Integrations

### 11.1 Event Notification Destinations

S3 can send event notifications to:

| Destination             | Use Case                                      |
|-------------------------|-----------------------------------------------|
| **Amazon SNS**          | Fan-out to multiple subscribers               |
| **Amazon SQS**          | Queue events for worker processing            |
| **AWS Lambda**          | Trigger serverless functions                  |
| **Amazon EventBridge**  | Complex routing, filtering, multiple targets  |

### 11.2 Configuring Event Notifications

```json
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:process-upload",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            { "Name": "prefix", "Value": "uploads/" },
            { "Name": "suffix", "Value": ".csv" }
          ]
        }
      }
    }
  ]
}
```

```bash
aws s3api put-bucket-notification-configuration \
  --bucket my-bucket \
  --notification-configuration file://notification.json
```

### 11.3 EventBridge Integration (Recommended)

Enable S3 → EventBridge for advanced routing:

```bash
aws s3api put-bucket-notification-configuration \
  --bucket my-bucket \
  --notification-configuration '{"EventBridgeConfiguration": {}}'
```

Then create EventBridge rules to route events to any target.

### 11.4 Common Integrations

```text
S3 PUT → Lambda → Process data → Write to DynamoDB/RDS
S3 PUT → SQS → EC2 Worker → ETL to Redshift
S3 PUT → SNS → Email notification + SQS queue
S3 PUT → EventBridge → Step Functions → Orchestration pipeline
S3 + Athena → Query data directly using SQL
S3 + Glue → ETL and cataloging
S3 + CloudFront → CDN for static content delivery
```

---

## 12. Advanced Features

### 12.1 S3 Object Lock

Prevents objects from being deleted or overwritten for a fixed period or indefinitely. Supports **WORM** (Write Once Read Many) compliance.

**Modes:**

| Mode           | Who Can Override         | Use Case                         |
|----------------|--------------------------|----------------------------------|
| **Governance** | Users with special IAM permission | Internal data protection     |
| **Compliance** | Nobody (not even root)   | Regulatory compliance (SEC, FINRA)|

```bash
# Enable Object Lock (must be set at bucket creation)
aws s3api create-bucket \
  --bucket compliance-bucket \
  --object-lock-enabled-for-bucket

# Apply retention on an object
aws s3api put-object-retention \
  --bucket compliance-bucket \
  --key report.pdf \
  --retention '{"Mode":"COMPLIANCE","RetainUntilDate":"2030-01-01T00:00:00Z"}'

# Legal Hold (no expiry date — holds until removed)
aws s3api put-object-legal-hold \
  --bucket compliance-bucket \
  --key report.pdf \
  --legal-hold Status=ON
```

### 12.2 S3 Inventory

Generates scheduled reports (daily or weekly) listing all objects in a bucket with their metadata.

```bash
aws s3api put-bucket-inventory-configuration \
  --bucket my-bucket \
  --id all-objects-inventory \
  --inventory-configuration '{
    "Id": "all-objects-inventory",
    "IsEnabled": true,
    "Destination": {
      "S3BucketDestination": {
        "Bucket": "arn:aws:s3:::inventory-output-bucket",
        "Format": "Parquet"
      }
    },
    "Schedule": { "Frequency": "Daily" },
    "IncludedObjectVersions": "All",
    "OptionalFields": ["Size","LastModifiedDate","StorageClass","ETag","EncryptionStatus","IntelligentTieringAccessTier"]
  }'
```

### 12.3 Requester Pays

Make the requester (not bucket owner) pay for requests and data transfer out.

```bash
aws s3api put-bucket-request-payment \
  --bucket my-bucket \
  --request-payment-configuration Payer=Requester
```

### 12.4 S3 Storage Lens

Organization-wide visibility into S3 usage and activity. Provides metrics like:
- Total storage by account/region/bucket
- Request metrics (GET, PUT rates)
- Cost efficiency recommendations
- Data protection scores

```bash
# Create a Storage Lens dashboard
aws s3control put-storage-lens-configuration \
  --account-id 123456789012 \
  --config-id my-lens \
  --storage-lens-configuration file://lens-config.json
```

### 12.5 CORS (Cross-Origin Resource Sharing)

Required when a web app in one domain accesses S3 resources.

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["https://mywebsite.com"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

```bash
aws s3api put-bucket-cors \
  --bucket my-bucket \
  --cors-configuration file://cors.json
```

---

## 13. S3 Pricing Model

Pricing has four main dimensions:

| Dimension                | What You Pay For                                          |
|--------------------------|-----------------------------------------------------------|
| **Storage**              | Per GB per month (varies by storage class)                |
| **Requests**             | Per 1,000 PUT/GET/LIST/DELETE requests                    |
| **Data Transfer Out**    | Per GB transferred out to internet or other regions       |
| **Management Features**  | Inventory, Analytics, S3 Lens, Object Tagging, Batch Ops  |

### Data Transfer Rules

| Transfer Type                            | Cost   |
|------------------------------------------|--------|
| Upload to S3 (data-in)                   | Free   |
| S3 to EC2/Lambda in **same region**      | Free   |
| S3 to EC2/Lambda in **different region** | Paid   |
| S3 to Internet                           | Paid   |
| S3 → CloudFront (all regions)            | Free   |
| CloudFront → Internet                    | Charged to CloudFront (cheaper) |

### Cost Optimization Tips

1. Use **Intelligent-Tiering** for unpredictable workloads.
2. Set **Lifecycle rules** to move old data to Glacier.
3. Enable **Bucket Key** for KMS-encrypted buckets (reduces KMS API costs ~99%).
4. Delete **incomplete multipart uploads** via lifecycle rules.
5. Use **CloudFront** in front of S3 for frequently downloaded public content.
6. Use **S3 Select** instead of downloading entire objects.
7. Delete **old versions** and **delete markers** if using versioning.

---

## 14. Common Architectures & Use Cases

### 14.1 Data Lake

```text
Ingest → S3 (raw zone)
       → Glue ETL → S3 (processed zone, Parquet/ORC)
       → Athena or Redshift Spectrum (query via SQL)
       → QuickSight (dashboards)
```

### 14.2 Static Website + CDN

```text
S3 (static files: HTML/CSS/JS)
  └→ CloudFront (CDN distribution)
       └→ Route 53 (custom domain, HTTPS)
       └→ Certificate Manager (SSL/TLS)
```

### 14.3 Serverless File Processing

```text
User uploads file
  → S3 (PUT event)
  → Lambda trigger
  → Process file (resize image, parse CSV, etc.)
  → Store result in S3 / DynamoDB / RDS
```

### 14.4 Backup & Disaster Recovery

```text
Source bucket (region A)
  → CRR → Replica bucket (region B)
         → Object Lock (WORM compliance)
         → Glacier lifecycle (long-term retention)
```

### 14.5 ML Training Pipeline

```text
Raw data → S3 Standard (landing)
         → Glue/Lambda (clean & transform)
         → S3 (training datasets, Parquet)
         → SageMaker (read directly from S3)
         → S3 (model artifacts, outputs)
```

---

## 15. S3 CLI Cheat Sheet

```bash
# ── Bucket Operations ──────────────────────────────────────────
aws s3 mb s3://my-bucket                         # Create bucket
aws s3 rb s3://my-bucket --force                 # Delete bucket + contents
aws s3 ls                                        # List all buckets
aws s3 ls s3://my-bucket/                        # List bucket contents
aws s3 ls s3://my-bucket/ --recursive            # List recursively

# ── Object Operations ──────────────────────────────────────────
aws s3 cp file.txt s3://my-bucket/               # Upload file
aws s3 cp s3://my-bucket/file.txt ./             # Download file
aws s3 cp s3://bucket-a/k s3://bucket-b/k        # Copy between buckets
aws s3 mv s3://my-bucket/old.txt s3://my-bucket/new.txt   # Move/rename
aws s3 rm s3://my-bucket/file.txt                # Delete object
aws s3 rm s3://my-bucket/ --recursive            # Delete all objects

# ── Sync ───────────────────────────────────────────────────────
aws s3 sync ./local-folder s3://my-bucket/prefix/    # Upload folder
aws s3 sync s3://my-bucket/prefix/ ./local-folder    # Download folder
aws s3 sync s3://bucket-a/ s3://bucket-b/            # Sync buckets
aws s3 sync ./folder s3://my-bucket/ --delete        # Delete files not in source

# ── With Options ───────────────────────────────────────────────
aws s3 cp file.csv s3://my-bucket/ \
  --storage-class STANDARD_IA \
  --sse aws:kms \
  --metadata "author=data-team,version=1.0"

# ── API Level ──────────────────────────────────────────────────
aws s3api head-object --bucket my-bucket --key file.csv   # Get object metadata
aws s3api get-object --bucket my-bucket --key file.csv out.csv
aws s3api list-objects-v2 --bucket my-bucket --prefix logs/
aws s3api get-bucket-location --bucket my-bucket
```

---

## 16. Best Practices

### Security
- Enable **Block Public Access** at the account level (on by default — keep it on).
- Use **bucket policies** over ACLs.
- Enforce **SSE-KMS encryption** via bucket policy.
- Audit access using **CloudTrail data events** for S3.
- Use **VPC Endpoints** to avoid S3 traffic traversing the public internet.
- Apply **least privilege** in IAM and bucket policies.
- Enable **MFA Delete** for critical buckets to prevent accidental deletion.

### Cost
- Set lifecycle rules to transition/expire data based on access patterns.
- Use Intelligent-Tiering for data with unpredictable access.
- Always abort incomplete multipart uploads (lifecycle rule: `AbortIncompleteMultipartUpload`).
- Monitor usage with S3 Storage Lens.

### Reliability & Durability
- Enable **Versioning** for important data.
- Use **CRR** for cross-region disaster recovery.
- Set up **Object Lock** for compliance-sensitive data.
- Test restore procedures from Glacier regularly.

### Performance
- Use multiple key prefixes to distribute load.
- Use **Transfer Acceleration** for globally distributed users.
- Use **Byte-Range Fetches** for large object downloads.
- Use **multipart upload** for all objects > 100 MB.
- Use **S3 Select** to reduce data scan on large objects.

### Naming & Organization
- Design key prefixes to support your query patterns (especially for Athena partitioning).
- Use consistent tag strategies (Environment, Team, Project) for cost allocation.
- Avoid sequential timestamp prefixes at the start of keys (causes hot partitions at high request rates).
