# S3 Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is Amazon S3 and its basic architecture?**
   - Simple Storage Service: Object storage (key-value)
   - Regional service with global namespace (bucket names unique globally)
   - Not a traditional file system (no hierarchical folders)
   - Objects: Key (path), Value (data), Metadata, Version ID
   - Buckets: Container for objects, max 100 per account (can request increase)

2. **Explain S3 storage classes and when to use each.**
   - **S3 Standard**: Default, high durability, immediate access
   - **S3 Intelligent-Tiering**: Auto moves to cheaper tiers based on access
   - **S3 Standard-IA**: Infrequent access, lower cost, retrieval fee
   - **S3 One Zone-IA**: Single AZ, cheapest for infrequent access
   - **Glacier**: Long-term backup, minutes/hours/days retrieval
   - **Glacier Deep Archive**: Long-term archival, hours/days retrieval
   - **S3 Outposts**: On-premises S3 equivalent

3. **Explain S3 pricing components.**
   - Storage cost: Per GB/month
   - Request cost: Per 1000 requests (GET, PUT)
   - Data transfer: Out of region (egress), into region (free)
   - Lifecycle transitions: Cost per transition
   - Storage class analysis: Enabling analysis costs

4. **What is S3 versioning and why is it important?**
   - Keep previous versions of objects
   - Enables accidental deletion recovery
   - Enables rollback to previous versions
   - Can suspend versioning (but can't disable)
   - Each version is separate object (storage cost)
   - MFA Delete: Additional protection against deletion

5. **Explain S3 bucket vs object ACL and bucket policies.**
   - **ACLs**: Older approach, permission at object/bucket level
   - **Bucket Policies**: JSON-based, more flexible, recommended
   - **Access Control Lists**: Canned ACLs (public-read, etc)
   - Note: Block All Public Access overrides any public settings

---

## 2. Intermediate Scenario-Based Questions

### Security & Access Control
6. **Design a secure S3 architecture for sensitive data (PII).**
   - Answer:
     - Bucket

 encryption: SSE-S3 or SSE-KMS (KMS recommended)
     - Enable versioning for recovery
     - Enable MFA Delete for critical data
     - Block All Public Access
     - Enable logging to separate bucket
     - Enforce TLS for data in transit
     - Use bucket policies to restrict to specific IAM roles
     - CloudTrail logging for API access
     - Enable Object Lock for WORM (Write Once Read Many)
     - Implement lifecycle policies to archive old data

7. **Scenario: Your S3 bucket is accidentally public. Investigate and secure.**
   - Trace root cause:
     - Check bucket permissions (public read)
     - Check individual object ACLs
     - Check bucket policy
   - Immediate action:
     - Enable Block All Public Access
     - Remove public ACLs/permissions
     - Verify logs for who accessed
   - Long-term:
     - Implement S3 Bucket Key for cost reduction
     - Enable CloudTrail
     - Use bucket policies exclusively (no ACL)

8. **How do you grant EC2 instance access to S3 without hardcoding credentials?**
   - Use IAM instance role:
     1. Create IAM role with S3 permissions
     2. Attach to EC2 instance
     3. EC2 SDK uses temporary credentials automatically
     4. No hardcoded credentials needed
     - Benefits: Automatic credential rotation, audit trail via CloudTrail

### Data Transfer & Performance
9. **Scenario: Need to upload 500 GB of data to S3. What's the optimal approach?**
   - Single PUT requests: Only works up to 5 GB, slow
   - Multipart upload:
     - Split into 5 MB parts minimum
     - Upload in parallel
     - Faster, resumable, can retry parts
     - Max 10,000 parts per upload
   - AWS DataSync: Automated data transfer with scheduling
   - AWS Snowball: Physical device for massive transfers (>100 TB)
   - S3 Transfer Acceleration: CloudFront for uploads

10. **Your application reads from S3 frequently. Performance is slow. Optimize.**
    - Add caching layer (CloudFront)
    - Use S3 Select to filter before download
    - Implement application-level caching (ElastiCache)
    - Use multipart downloads in parallel
    - Check S3 request rate (if bucket > 3,500 PUT, 5,500 GET per second)
    - Use S3 Intelligent-Tiering if access patterns variable

---

## 3. Advanced Problem-Solving Questions

### Lifecycle & Data Management
11. **Design a data retention policy for S3 with different retention requirements.**
    - Policy example:
      - Recent data (0-30 days): S3 Standard (immediate access)
      - Warm data (30-90 days): S3 Standard-IA (infrequent, retrieve fast)
      - Cold data (90-1 year): Glacier (deep archival)
      - Archive (>1 year or never): Glacier Deep Archive or delete
    - Implementation:
      - Lifecycle rules with transitions
      - Expiration rules for deletion
      - Different rules per prefix (prod/analytics/backup)
      - Use object tags for flexible rules

12. **Scenario: Your S3 bill tripled. Identify and reduce costs.**
    - Investigation:
      1. Check storage by class (S3 Intelligent-Tiering analysis)
      2. Review request counts (expensive GET/PUT operations)
      3. Check data transfer (egress costs)
      4. Analyze lifecycle rule effectiveness
      5. Find incomplete multipart uploads (orphaned parts)
    - Cost reduction:
      - Move cold data to Glacier
      - Enable S3 Intelligent-Tiering
      - Delete old versions (versioning cost)
      - Use S3 Bucket Key (reduces KMS costs)
      - Clean up incomplete multipart uploads

13. **Design a backup solution using S3 with cross-region replication.**
    - Primary region: Regional S3 bucket (versioning enabled)
    - Secondary region: Replication destination
    - Use S3 Replication:
      - Automatic, asynchronous replication
      - Can replicate previous versions
      - Can change storage class during replication
    - Disaster recovery:
      - Failover to replicated bucket
      - Update DNS to point to replicated bucket
      - RPO: Minutes (replication lag)
      - RTO: Less than 1 minute (DNS switch)

### Compliance & Auditing
14. **Implement tamper-proof archival using S3 Object Lock.**
    - Object Lock modes:
      - **Governance mode**: AWS can delete with special permission
      - **Compliance mode**: No one can delete until retention expires (immutable)
    - Use case: Regulatory compliance (HIPAA, SOX), audit logs
    - Implementation:
      - Enable Object Lock on bucket creation (can't disable)
      - Set retention period or legal hold
      - Use governance for internal compliance
      - Use compliance for external requirements

15. **Design an audit trail system using S3 logging and monitoring.**
    - S3 Server Access Logging:
      - Logs all requests to separate bucket
      - Contains: Requester, action, object, timestamp
      - Delivery within hours (not real-time)
    - CloudTrail:
      - Logs API calls (CreateBucket, PutObject, etc)
      - Real-time delivery
    - CloudWatch:
      - Monitor request metrics
      - Alarms on unusual activity
      - Query logs with CloudWatch Insights

---

## 4. Best Practices

16. **What are S3 best practices?**
    - Enable versioning for important buckets
    - Enable MFA Delete for sensitive data
    - Block all public access by default
    - Use bucket policies instead of ACLs
    - Enable encryption (SSE-S3 or SSE-KMS)
    - Enable logging (S3 and CloudTrail)
    - Implement lifecycle policies for cost optimization
    - Use CloudFront for frequent access
    - Monitor with CloudWatch and alarms
    - Regular backup to different region
    - Use S3 Bucket Key to reduce KMS costs

17. **Compare S3 and EBS for storage.**
    - **S3**: Object storage, unlimited scale, slow random access, good for backups
    - **EBS**: Block storage, attached to EC2, fast access, limited by volume size
    - Use S3: Media, logs, backups, big data
    - Use EBS: Operating systems, databases, applications

---

## 5. Real-World Scenarios

18. **Scenario: S3 bucket has 10 TB of data, but you only need last 1 month. Reduce storage.**
    - Solution:
      1. Use S3 Select queries to identify old data
      2. Create Athena query to list objects by date
      3. Delete objects older than 30 days
      4. Implement lifecycle rule for future data
      5. Estimate cost savings

19. **Design a multi-tenant S3 architecture where each customer has isolated data.**
    - Approach 1 (Simple): Single bucket, separate prefixes per customer
      - `/customer1/`, `/customer2/`
      - Apply IAM policy to restrict each customer to their prefix
      - Cost-effective, simpler management
    - Approach 2 (Isolated): Separate bucket per customer
      - More isolation, easier backups
      - Higher management overhead
      - Higher costs
    - Choose Approach 1 unless compliance requires isolation

20. **Scenario: User accidentally deletes files from S3. Recovery plan?**
    - If versioning enabled:
      - List all versions of deleted object
      - Restore (copy latest version)
      - User can do self-service restoration
    - If versioning not enabled:
      - No recovery possible
      - Implement versioning + MFA Delete for future
      - CloudTrail shows who deleted
    - Best practice: Always enable versioning

21. **Design a secure file-sharing system with temporary access URLs.**
    - Use S3 Presigned URLs:
      - Generate signed URL with 15-minute expiry
      - User can download without credentials
      - No public access needed
    - Implementation:
      ```python
      s3_client.generate_presigned_url(
          'get_object',
          Params={'Bucket': bucket, 'Key': key},
          ExpiresIn=900  # 15 minutes
      )
      ```
    - Security: URLs are time-limited, user-specific (if custom policy)

---

## 6. S3 Select & Advanced Features

22. **What is S3 Select and when do you use it?**
    - Query data in S3 using SQL without downloading entire object
    - Supports: CSV, JSON, Parquet
    - Up to 400% faster than downloading entire object
    - Use case: Extract specific rows from 100 GB CSV file
    - Cost: Per GB scanned (cheaper than data transfer)

23. **How do you use Athena with S3?**
    - Run SQL queries directly on S3 data
    - No ETL needed, data stays in place
    - Supports: CSV, JSON, Parquet, ORC
    - Use case: Analytics on logs, big data queries
    - Cost: Per GB scanned, cheaper than Redshift for one-off queries

---

## 7. Hands-On Coding

24. **Write Python code for multipart S3 upload:**
    ```python
    import boto3

    s3 = boto3.client('s3')

    def upload_large_file(bucket, key, file_path):
        config = boto3.s3.transfer.S3TransferConfig(
            max_concurrency=10,
            max_io_queue_size=100,
            max_bandwidth=100 * 1024 * 1024  # 100 MB/s
        )

        s3.upload_file(
            file_path,
            bucket,
            key,
            Config=config,
            Callback=print_progress
        )

    def print_progress(bytes_transferred):
        print(f"Transferred: {bytes_transferred / (1024**3):.2f} GB")
    ```

25. **Write code for S3 Presigned URL generation:**
    ```python
    import boto3
    from datetime import datetime, timedelta

    s3 = boto3.client('s3')

    def generate_presigned_url(bucket, key, expiration_minutes=15):
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration_minutes * 60
        )
        return url

    def generate_presigned_post(bucket, key):
        # For form-based uploads
        response = s3.generate_presigned_post(
            bucket,
            key,
            Fields={"acl": "private"},
            Conditions=[
                ["content-length-range", 0, 1000000]  # Max 1 MB
            ],
            ExpiresIn=3600
        )
        return response
    ```

---

## Tips for Interview Success

- **Understand storage classes**: When to use each based on access patterns
- **Security by default**: Block public access, encryption, logging
- **Cost optimization**: Lifecycle rules, S3 Intelligent-Tiering
- **Data patterns**: S3 design is prefix-based, not hierarchical
- **Versioning importance**: For compliance and disaster recovery
- **Encryption options**: Know when to use S3-KMS vs KMS
- **Regional considerations**: Replication, egress costs
- **Know related tools**: CloudFront for caching, Athena for analytics
- **Multipart uploads**: For large files and performance

