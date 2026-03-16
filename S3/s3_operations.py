"""
AWS S3 Operations 
boto3 Python Reference

Sections:
  1.  Setup & Client Initialization
  2.  Bucket Operations
  3.  Object Operations (Upload / Download / Copy / Delete)
  4.  Object Metadata & Tags
  5.  Storage Classes
  6.  Block Public Access
  7.  Bucket Policy
  8.  ACLs & Ownership Controls
  9.  S3 Access Points
  10. Encryption (SSE-S3, SSE-KMS, SSE-C, Default Encryption)
  11. Pre-Signed URLs
  12. S3 Select
  13. Multipart Upload
  14. Versioning
  15. Lifecycle Rules
  16. Replication
  17. Transfer Acceleration
  18. Byte-Range Fetches
  19. Event Notifications (Lambda / SQS / SNS / EventBridge)
  20. Object Lock & Legal Hold
  21. S3 Inventory
  22. CORS
  23. Static Website Hosting
  24. Requester Pays
  25. S3 Batch Operations
  26. MFA Delete
  27. Restore from Glacier
  28. Sync-Style Folder Upload / Download (TransferManager)
"""

import json
import os
import hashlib
import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig


# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP & CLIENT INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

# Low-level client — maps 1:1 to S3 API
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    # Credentials are picked up from:
    #   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    #   - ~/.aws/credentials file
    #   - IAM role attached to EC2/Lambda
    # Explicit credentials (avoid hardcoding in production):
    # aws_access_key_id="AKIA...",
    # aws_secret_access_key="...",
)

# High-level resource — Pythonic OOP interface
s3_resource = boto3.resource("s3", region_name="us-east-1")

BUCKET = "my-demo-bucket"
REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


# ─────────────────────────────────────────────────────────────────────────────
# 2. BUCKET OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def create_bucket(bucket_name: str, region: str = "us-east-1") -> dict:
    """Create an S3 bucket. us-east-1 does NOT use LocationConstraint."""
    if region == "us-east-1":
        response = s3_client.create_bucket(Bucket=bucket_name)
    else:
        response = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
    print(f"Bucket created: {bucket_name}")
    return response


def list_buckets() -> list:
    """List all S3 buckets in the account."""
    response = s3_client.list_buckets()
    buckets = response.get("Buckets", [])
    for bucket in buckets:
        print(f"  {bucket['Name']}  (created: {bucket['CreationDate']})")
    return buckets


def get_bucket_location(bucket_name: str) -> str:
    """Return the region a bucket lives in."""
    response = s3_client.get_bucket_location(Bucket=bucket_name)
    location = response["LocationConstraint"] or "us-east-1"
    print(f"Bucket {bucket_name} is in region: {location}")
    return location


def delete_bucket(bucket_name: str) -> None:
    """Delete an empty bucket."""
    s3_client.delete_bucket(Bucket=bucket_name)
    print(f"Bucket deleted: {bucket_name}")


def delete_bucket_force(bucket_name: str) -> None:
    """Delete a bucket and all objects/versions inside it."""
    bucket = s3_resource.Bucket(bucket_name)
    # Delete all object versions (handles versioning)
    bucket.object_versions.delete()
    # Delete the bucket itself
    bucket.delete()
    print(f"Bucket and all contents deleted: {bucket_name}")


def put_bucket_tags(bucket_name: str, tags: dict) -> None:
    """Apply tags to a bucket."""
    tag_set = [{"Key": k, "Value": v} for k, v in tags.items()]
    s3_client.put_bucket_tagging(
        Bucket=bucket_name,
        Tagging={"TagSet": tag_set},
    )
    print(f"Tags applied to {bucket_name}: {tags}")


def get_bucket_tags(bucket_name: str) -> list:
    """Retrieve tags on a bucket."""
    try:
        response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        return response["TagSet"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchTagSet":
            return []
        raise


# ─────────────────────────────────────────────────────────────────────────────
# 3. OBJECT OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def upload_file(local_path: str, bucket_name: str, key: str) -> None:
    """Upload a local file to S3."""
    s3_client.upload_file(local_path, bucket_name, key)
    print(f"Uploaded {local_path} → s3://{bucket_name}/{key}")


def upload_fileobj(file_obj, bucket_name: str, key: str) -> None:
    """Upload a file-like object (e.g., open() or BytesIO) to S3."""
    s3_client.upload_fileobj(file_obj, bucket_name, key)


def put_object(bucket_name: str, key: str, data: bytes | str) -> dict:
    """Upload raw bytes/string directly to S3."""
    body = data.encode("utf-8") if isinstance(data, str) else data
    response = s3_client.put_object(Bucket=bucket_name, Key=key, Body=body)
    print(f"Object written: s3://{bucket_name}/{key}")
    return response


def download_file(bucket_name: str, key: str, local_path: str) -> None:
    """Download an S3 object to a local file."""
    s3_client.download_file(bucket_name, key, local_path)
    print(f"Downloaded s3://{bucket_name}/{key} → {local_path}")


def download_fileobj(bucket_name: str, key: str, file_obj) -> None:
    """Download an S3 object into a file-like object."""
    s3_client.download_fileobj(bucket_name, key, file_obj)


def get_object(bucket_name: str, key: str) -> bytes:
    """Read an S3 object into memory and return its bytes."""
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    body = response["Body"].read()
    print(f"Read {len(body)} bytes from s3://{bucket_name}/{key}")
    return body


def copy_object(
    src_bucket: str, src_key: str, dst_bucket: str, dst_key: str
) -> dict:
    """Copy an object within or between buckets."""
    copy_source = {"Bucket": src_bucket, "Key": src_key}
    response = s3_client.copy_object(
        CopySource=copy_source,
        Bucket=dst_bucket,
        Key=dst_key,
    )
    print(f"Copied s3://{src_bucket}/{src_key} → s3://{dst_bucket}/{dst_key}")
    return response


def move_object(
    src_bucket: str, src_key: str, dst_bucket: str, dst_key: str
) -> None:
    """Move (copy then delete) an object."""
    copy_object(src_bucket, src_key, dst_bucket, dst_key)
    delete_object(src_bucket, src_key)


def delete_object(bucket_name: str, key: str) -> dict:
    """Delete an object (adds delete marker if versioning is on)."""
    response = s3_client.delete_object(Bucket=bucket_name, Key=key)
    print(f"Deleted s3://{bucket_name}/{key}")
    return response


def delete_objects_batch(bucket_name: str, keys: list[str]) -> dict:
    """Delete up to 1,000 objects in a single API call."""
    objects = [{"Key": k} for k in keys]
    response = s3_client.delete_objects(
        Bucket=bucket_name,
        Delete={"Objects": objects, "Quiet": False},
    )
    deleted = len(response.get("Deleted", []))
    errors = len(response.get("Errors", []))
    print(f"Batch delete: {deleted} deleted, {errors} errors")
    return response


def list_objects(bucket_name: str, prefix: str = "", max_keys: int = 1000) -> list:
    """List objects under a prefix. Uses pagination for > 1,000 objects."""
    objects = []
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, PaginationConfig={"MaxItems": max_keys})
    for page in pages:
        for obj in page.get("Contents", []):
            objects.append(obj)
            print(f"  {obj['Key']}  size={obj['Size']}  class={obj['StorageClass']}")
    return objects


# ─────────────────────────────────────────────────────────────────────────────
# 4. OBJECT METADATA & TAGS
# ─────────────────────────────────────────────────────────────────────────────

def head_object(bucket_name: str, key: str) -> dict:
    """Retrieve metadata for an object without downloading it."""
    response = s3_client.head_object(Bucket=bucket_name, Key=key)
    print(f"ContentType : {response.get('ContentType')}")
    print(f"ContentLength: {response.get('ContentLength')}")
    print(f"ETag        : {response.get('ETag')}")
    print(f"StorageClass: {response.get('StorageClass', 'STANDARD')}")
    print(f"Encryption  : {response.get('ServerSideEncryption')}")
    print(f"VersionId   : {response.get('VersionId')}")
    print(f"User Metadata: {response.get('Metadata')}")
    return response


def upload_with_metadata(
    bucket_name: str, key: str, data: bytes, metadata: dict, content_type: str
) -> dict:
    """Upload an object with custom metadata and content type."""
    return s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type,
        Metadata=metadata,  # user-defined, all values must be strings
    )


def put_object_tags(bucket_name: str, key: str, tags: dict) -> None:
    """Set tags on an existing object."""
    tag_set = [{"Key": k, "Value": v} for k, v in tags.items()]
    s3_client.put_object_tagging(
        Bucket=bucket_name,
        Key=key,
        Tagging={"TagSet": tag_set},
    )


def get_object_tags(bucket_name: str, key: str) -> list:
    """Get tags on an object."""
    response = s3_client.get_object_tagging(Bucket=bucket_name, Key=key)
    return response["TagSet"]


def delete_object_tags(bucket_name: str, key: str) -> None:
    """Remove all tags from an object."""
    s3_client.delete_object_tagging(Bucket=bucket_name, Key=key)


# ─────────────────────────────────────────────────────────────────────────────
# 5. STORAGE CLASSES
# ─────────────────────────────────────────────────────────────────────────────

STORAGE_CLASSES = [
    "STANDARD",
    "INTELLIGENT_TIERING",
    "STANDARD_IA",
    "ONEZONE_IA",
    "GLACIER_IR",          # Glacier Instant Retrieval
    "GLACIER",             # Glacier Flexible Retrieval
    "DEEP_ARCHIVE",
    "EXPRESS_ONEZONE",     # S3 Express One Zone (directory bucket)
]


def upload_with_storage_class(
    local_path: str, bucket_name: str, key: str, storage_class: str
) -> None:
    """Upload a file to a specific storage class."""
    s3_client.upload_file(
        local_path,
        bucket_name,
        key,
        ExtraArgs={"StorageClass": storage_class},
    )
    print(f"Uploaded {local_path} with StorageClass={storage_class}")


def change_storage_class(bucket_name: str, key: str, new_class: str) -> None:
    """Change an object's storage class by copying it over itself."""
    copy_source = {"Bucket": bucket_name, "Key": key}
    s3_client.copy_object(
        CopySource=copy_source,
        Bucket=bucket_name,
        Key=key,
        StorageClass=new_class,
        MetadataDirective="COPY",
    )
    print(f"Storage class changed to {new_class}: s3://{bucket_name}/{key}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. BLOCK PUBLIC ACCESS
# ─────────────────────────────────────────────────────────────────────────────

def enable_block_public_access(bucket_name: str) -> None:
    """Enable all four Block Public Access settings (most secure)."""
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print(f"Block Public Access fully enabled on {bucket_name}")


def get_block_public_access(bucket_name: str) -> dict:
    """Retrieve the current Block Public Access settings."""
    response = s3_client.get_public_access_block(Bucket=bucket_name)
    config = response["PublicAccessBlockConfiguration"]
    print(json.dumps(config, indent=2))
    return config


def disable_block_public_access(bucket_name: str) -> None:
    """Disable all Block Public Access settings (use with caution)."""
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. BUCKET POLICY
# ─────────────────────────────────────────────────────────────────────────────

def put_bucket_policy(bucket_name: str, policy: dict) -> None:
    """Attach a bucket policy. policy must be a Python dict."""
    s3_client.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(policy),
    )
    print(f"Bucket policy applied to {bucket_name}")


def get_bucket_policy(bucket_name: str) -> dict:
    """Retrieve the current bucket policy."""
    try:
        response = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy = json.loads(response["Policy"])
        print(json.dumps(policy, indent=2))
        return policy
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            print("No bucket policy exists.")
            return {}
        raise


def delete_bucket_policy(bucket_name: str) -> None:
    """Remove the bucket policy."""
    s3_client.delete_bucket_policy(Bucket=bucket_name)
    print(f"Bucket policy deleted from {bucket_name}")


# Example: Allow read-only public access to all objects
PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET}/*",
        }
    ],
}

# Example: Deny all non-HTTPS requests
HTTPS_ONLY_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyHTTP",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{BUCKET}",
                f"arn:aws:s3:::{BUCKET}/*",
            ],
            "Condition": {
                "Bool": {"aws:SecureTransport": "false"}
            },
        }
    ],
}

# Example: Cross-account access
CROSS_ACCOUNT_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::987654321098:root"
            },
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            "Resource": [
                f"arn:aws:s3:::{BUCKET}",
                f"arn:aws:s3:::{BUCKET}/*",
            ],
        }
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 8. ACLs & OWNERSHIP CONTROLS
# ─────────────────────────────────────────────────────────────────────────────

def disable_acls(bucket_name: str) -> None:
    """Set BucketOwnerEnforced — disables ACLs (AWS recommended)."""
    s3_client.put_bucket_ownership_controls(
        Bucket=bucket_name,
        OwnershipControls={
            "Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]
        },
    )
    print(f"ACLs disabled (BucketOwnerEnforced) on {bucket_name}")


def set_bucket_acl_private(bucket_name: str) -> None:
    """Set the bucket ACL to private (only owner has full control)."""
    s3_client.put_bucket_acl(Bucket=bucket_name, ACL="private")


def set_object_acl(bucket_name: str, key: str, acl: str) -> None:
    """Set a canned ACL on an object.
    acl values: private | public-read | public-read-write |
                authenticated-read | bucket-owner-read | bucket-owner-full-control
    """
    s3_client.put_object_acl(Bucket=bucket_name, Key=key, ACL=acl)


# ─────────────────────────────────────────────────────────────────────────────
# 9. S3 ACCESS POINTS
# ─────────────────────────────────────────────────────────────────────────────

def create_access_point(
    account_id: str, bucket_name: str, access_point_name: str
) -> dict:
    """Create an S3 Access Point for simplified access management."""
    s3control = boto3.client("s3control", region_name=REGION)
    response = s3control.create_access_point(
        AccountId=account_id,
        Name=access_point_name,
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    arn = response["AccessPointArn"]
    print(f"Access Point created: {arn}")
    return response


def put_access_point_policy(
    account_id: str, access_point_name: str, policy: dict
) -> None:
    """Attach a resource policy to an Access Point."""
    s3control = boto3.client("s3control", region_name=REGION)
    s3control.put_access_point_policy(
        AccountId=account_id,
        Name=access_point_name,
        Policy=json.dumps(policy),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. ENCRYPTION
# ─────────────────────────────────────────────────────────────────────────────

# ── 10a. Upload with SSE-S3 (AES-256) ─────────────────────────────────────

def upload_sse_s3(bucket_name: str, key: str, data: bytes) -> dict:
    """Upload an object with SSE-S3 (AES-256, managed by AWS)."""
    return s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=data,
        ServerSideEncryption="AES256",
    )


# ── 10b. Upload with SSE-KMS ───────────────────────────────────────────────

def upload_sse_kms(
    bucket_name: str, key: str, data: bytes, kms_key_id: str = None
) -> dict:
    """Upload an object with SSE-KMS.
    kms_key_id: ARN or alias of the CMK. If None, uses the AWS managed key.
    """
    kwargs = {
        "Bucket": bucket_name,
        "Key": key,
        "Body": data,
        "ServerSideEncryption": "aws:kms",
    }
    if kms_key_id:
        kwargs["SSEKMSKeyId"] = kms_key_id
    return s3_client.put_object(**kwargs)


def upload_file_sse_kms(
    local_path: str, bucket_name: str, key: str, kms_key_id: str
) -> None:
    """Upload a file with SSE-KMS using the high-level upload_file method."""
    s3_client.upload_file(
        local_path,
        bucket_name,
        key,
        ExtraArgs={
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": kms_key_id,
        },
    )


# ── 10c. Upload with SSE-C (Customer-Provided Keys) ───────────────────────

def _make_sse_c_params(customer_key: bytes) -> dict:
    """Build SSE-C header params from a 32-byte AES-256 key."""
    import base64
    key_b64 = base64.b64encode(customer_key).decode("utf-8")
    key_md5 = hashlib.md5(customer_key).digest()
    key_md5_b64 = base64.b64encode(key_md5).decode("utf-8")
    return {
        "SSECustomerAlgorithm": "AES256",
        "SSECustomerKey": key_b64,
        "SSECustomerKeyMD5": key_md5_b64,
    }


def upload_sse_c(
    bucket_name: str, key: str, data: bytes, customer_key: bytes
) -> dict:
    """Upload an object with SSE-C. You must store the key yourself."""
    params = _make_sse_c_params(customer_key)
    return s3_client.put_object(
        Bucket=bucket_name, Key=key, Body=data, **params
    )


def download_sse_c(
    bucket_name: str, key: str, customer_key: bytes
) -> bytes:
    """Download an SSE-C encrypted object (must supply the same key)."""
    params = _make_sse_c_params(customer_key)
    response = s3_client.get_object(
        Bucket=bucket_name, Key=key, **params
    )
    return response["Body"].read()


# ── 10d. Set Default Bucket Encryption ────────────────────────────────────

def set_default_encryption_sse_s3(bucket_name: str) -> None:
    """Set default bucket encryption to SSE-S3 (AES-256)."""
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    },
                    "BucketKeyEnabled": False,
                }
            ]
        },
    )


def set_default_encryption_sse_kms(bucket_name: str, kms_key_id: str) -> None:
    """Set default bucket encryption to SSE-KMS with Bucket Key enabled
    (reduces KMS API calls and cost ~99%)."""
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms",
                        "KMSMasterKeyID": kms_key_id,
                    },
                    "BucketKeyEnabled": True,  # Recommended: reduces KMS cost
                }
            ]
        },
    )
    print(f"Default SSE-KMS encryption set on {bucket_name}")


def get_bucket_encryption(bucket_name: str) -> dict:
    """Retrieve the current default encryption configuration."""
    try:
        response = s3_client.get_bucket_encryption(Bucket=bucket_name)
        rules = response["ServerSideEncryptionConfiguration"]["Rules"]
        print(json.dumps(rules, indent=2, default=str))
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            print("No default encryption set.")
            return {}
        raise


# ─────────────────────────────────────────────────────────────────────────────
# 11. PRE-SIGNED URLS
# ─────────────────────────────────────────────────────────────────────────────

def generate_presigned_get_url(
    bucket_name: str, key: str, expiry_seconds: int = 3600
) -> str:
    """Generate a pre-signed URL to GET (download) a private object."""
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": key},
        ExpiresIn=expiry_seconds,
    )
    print(f"Pre-signed GET URL (expires in {expiry_seconds}s):\n{url}")
    return url


def generate_presigned_put_url(
    bucket_name: str, key: str, expiry_seconds: int = 3600,
    content_type: str = "application/octet-stream"
) -> str:
    """Generate a pre-signed URL to PUT (upload) an object directly from client."""
    url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket_name,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expiry_seconds,
    )
    print(f"Pre-signed PUT URL:\n{url}")
    return url


def generate_presigned_post(
    bucket_name: str, key_prefix: str, expiry_seconds: int = 3600,
    max_size_bytes: int = 10 * 1024 * 1024
) -> dict:
    """Generate a pre-signed POST for browser-based uploads (HTML forms).
    Returns a dict with 'url' and 'fields' to include in the form POST.
    """
    response = s3_client.generate_presigned_post(
        Bucket=bucket_name,
        Key=f"{key_prefix}${{filename}}",  # ${{filename}} auto-filled by browser
        Fields={"Content-Type": "application/octet-stream"},
        Conditions=[
            ["content-length-range", 1, max_size_bytes],
            {"Content-Type": "application/octet-stream"},
        ],
        ExpiresIn=expiry_seconds,
    )
    return response  # Use: requests.post(response['url'], data=response['fields'], files={'file': ...})


# ─────────────────────────────────────────────────────────────────────────────
# 12. S3 SELECT
# ─────────────────────────────────────────────────────────────────────────────

def s3_select_csv(
    bucket_name: str, key: str, sql_expression: str
) -> str:
    """Run a SQL query on a CSV object. Returns result as a string."""
    response = s3_client.select_object_content(
        Bucket=bucket_name,
        Key=key,
        ExpressionType="SQL",
        Expression=sql_expression,
        InputSerialization={
            "CSV": {
                "FileHeaderInfo": "USE",   # USE | IGNORE | NONE
                "RecordDelimiter": "\n",
                "FieldDelimiter": ",",
            },
            "CompressionType": "NONE",     # NONE | GZIP | BZIP2
        },
        OutputSerialization={"CSV": {}},
    )
    result = ""
    for event in response["Payload"]:
        if "Records" in event:
            result += event["Records"]["Payload"].decode("utf-8")
        elif "Stats" in event:
            stats = event["Stats"]["Details"]
            print(f"S3 Select Stats: scanned={stats['BytesScanned']}, returned={stats['BytesReturned']}")
    return result


def s3_select_json(
    bucket_name: str, key: str, sql_expression: str
) -> str:
    """Run a SQL query on a JSON Lines object."""
    response = s3_client.select_object_content(
        Bucket=bucket_name,
        Key=key,
        ExpressionType="SQL",
        Expression=sql_expression,
        InputSerialization={
            "JSON": {"Type": "LINES"},   # DOCUMENT or LINES
            "CompressionType": "NONE",
        },
        OutputSerialization={"JSON": {"RecordDelimiter": "\n"}},
    )
    result = ""
    for event in response["Payload"]:
        if "Records" in event:
            result += event["Records"]["Payload"].decode("utf-8")
    return result


def s3_select_parquet(
    bucket_name: str, key: str, sql_expression: str
) -> str:
    """Run a SQL query on a Parquet object. No CompressionType for Parquet."""
    response = s3_client.select_object_content(
        Bucket=bucket_name,
        Key=key,
        ExpressionType="SQL",
        Expression=sql_expression,
        InputSerialization={"Parquet": {}},
        OutputSerialization={"CSV": {}},
    )
    result = ""
    for event in response["Payload"]:
        if "Records" in event:
            result += event["Records"]["Payload"].decode("utf-8")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 13. MULTIPART UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

def multipart_upload_manual(
    bucket_name: str, key: str, local_path: str, part_size: int = 100 * 1024 * 1024
) -> dict:
    """Manual multipart upload. part_size default: 100 MB.
    Each part must be >= 5 MB except the last.
    """
    # 1. Initiate
    mpu = s3_client.create_multipart_upload(Bucket=bucket_name, Key=key)
    upload_id = mpu["UploadId"]
    parts = []
    part_number = 1

    try:
        with open(local_path, "rb") as f:
            while True:
                chunk = f.read(part_size)
                if not chunk:
                    break
                # 2. Upload each part
                response = s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                print(f"  Uploaded part {part_number} ({len(chunk) / 1024 / 1024:.1f} MB)")
                part_number += 1

        # 3. Complete
        result = s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        print(f"Multipart upload complete: s3://{bucket_name}/{key}")
        return result

    except Exception as e:
        # 4. Abort on failure to avoid partial charges
        s3_client.abort_multipart_upload(
            Bucket=bucket_name, Key=key, UploadId=upload_id
        )
        print(f"Multipart upload aborted: {e}")
        raise


def multipart_upload_managed(
    local_path: str, bucket_name: str, key: str
) -> None:
    """High-level managed multipart upload using boto3 TransferConfig.
    boto3 handles part splitting, parallelism, and retries automatically.
    """
    config = TransferConfig(
        multipart_threshold=100 * 1024 * 1024,  # 100 MB threshold
        multipart_chunksize=100 * 1024 * 1024,  # 100 MB part size
        max_concurrency=10,                      # parallel threads
        use_threads=True,
    )
    s3_client.upload_file(
        local_path,
        bucket_name,
        key,
        Config=config,
    )
    print(f"Managed multipart upload complete: s3://{bucket_name}/{key}")


def list_multipart_uploads(bucket_name: str) -> list:
    """List all in-progress multipart uploads (potential hidden cost)."""
    response = s3_client.list_multipart_uploads(Bucket=bucket_name)
    uploads = response.get("Uploads", [])
    for u in uploads:
        print(f"  UploadId={u['UploadId']}  Key={u['Key']}  Initiated={u['Initiated']}")
    return uploads


def abort_multipart_upload(bucket_name: str, key: str, upload_id: str) -> None:
    """Abort a specific in-progress multipart upload."""
    s3_client.abort_multipart_upload(
        Bucket=bucket_name, Key=key, UploadId=upload_id
    )
    print(f"Aborted multipart upload {upload_id}")


# ─────────────────────────────────────────────────────────────────────────────
# 14. VERSIONING
# ─────────────────────────────────────────────────────────────────────────────

def enable_versioning(bucket_name: str) -> None:
    """Enable versioning on a bucket. Cannot be disabled once enabled — only suspended."""
    s3_client.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"},
    )
    print(f"Versioning enabled on {bucket_name}")


def suspend_versioning(bucket_name: str) -> None:
    """Suspend versioning. Existing versions are retained."""
    s3_client.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Suspended"},
    )


def get_versioning_status(bucket_name: str) -> str:
    """Returns versioning status: Enabled | Suspended | '' (never enabled)."""
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    status = response.get("Status", "Not enabled")
    print(f"Versioning status: {status}")
    return status


def list_object_versions(bucket_name: str, key: str) -> dict:
    """List all versions and delete markers for a specific key."""
    response = s3_client.list_object_versions(
        Bucket=bucket_name, Prefix=key
    )
    versions = response.get("Versions", [])
    markers = response.get("DeleteMarkers", [])
    print(f"Versions ({len(versions)}):")
    for v in versions:
        print(f"  VersionId={v['VersionId']}  IsLatest={v['IsLatest']}  LastModified={v['LastModified']}")
    print(f"Delete Markers ({len(markers)}):")
    for m in markers:
        print(f"  VersionId={m['VersionId']}  IsLatest={m['IsLatest']}")
    return response


def get_object_version(
    bucket_name: str, key: str, version_id: str
) -> bytes:
    """Download a specific version of an object."""
    response = s3_client.get_object(
        Bucket=bucket_name, Key=key, VersionId=version_id
    )
    return response["Body"].read()


def delete_object_version(
    bucket_name: str, key: str, version_id: str
) -> dict:
    """Permanently delete a specific object version."""
    return s3_client.delete_object(
        Bucket=bucket_name, Key=key, VersionId=version_id
    )


def restore_deleted_object(bucket_name: str, key: str) -> None:
    """Restore a soft-deleted object by removing its latest delete marker."""
    response = s3_client.list_object_versions(
        Bucket=bucket_name, Prefix=key
    )
    delete_markers = response.get("DeleteMarkers", [])
    # Find the latest delete marker (IsLatest == True)
    for marker in delete_markers:
        if marker["IsLatest"] and marker["Key"] == key:
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=key,
                VersionId=marker["VersionId"],
            )
            print(f"Restored {key} by deleting delete marker {marker['VersionId']}")
            return
    print(f"No delete marker found for {key}")


def enable_mfa_delete(bucket_name: str, mfa_serial: str, mfa_token: str) -> None:
    """Enable MFA Delete — requires physical MFA device confirmation.
    mfa_serial: ARN of the MFA device (e.g., arn:aws:iam::123456789012:mfa/user)
    mfa_token: current TOTP code from the MFA device
    """
    s3_client.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={
            "MFADelete": "Enabled",
            "Status": "Enabled",
        },
        MFA=f"{mfa_serial} {mfa_token}",  # "serial token" space-separated
    )
    print(f"MFA Delete enabled on {bucket_name}")


# ─────────────────────────────────────────────────────────────────────────────
# 15. LIFECYCLE RULES
# ─────────────────────────────────────────────────────────────────────────────

def put_lifecycle_configuration(bucket_name: str, rules: list) -> None:
    """Apply lifecycle rules to a bucket."""
    s3_client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={"Rules": rules},
    )
    print(f"Lifecycle configuration applied to {bucket_name}")


def get_lifecycle_configuration(bucket_name: str) -> list:
    """Retrieve current lifecycle rules."""
    try:
        response = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return response["Rules"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return []
        raise


def delete_lifecycle_configuration(bucket_name: str) -> None:
    """Remove all lifecycle rules from a bucket."""
    s3_client.delete_bucket_lifecycle(Bucket=bucket_name)


# Lifecycle rule examples ─────────────────────────────────────────────────

# Rule 1: Multi-tier transition + expiry for logs
LOG_LIFECYCLE_RULE = {
    "ID": "archive-logs",
    "Status": "Enabled",
    "Filter": {"Prefix": "logs/"},
    "Transitions": [
        {"Days": 30,  "StorageClass": "STANDARD_IA"},
        {"Days": 90,  "StorageClass": "GLACIER"},
        {"Days": 365, "StorageClass": "DEEP_ARCHIVE"},
    ],
    "Expiration": {"Days": 2555},  # 7 years total retention
    # Manage old versions
    "NoncurrentVersionTransitions": [
        {"NoncurrentDays": 30, "StorageClass": "STANDARD_IA"},
    ],
    "NoncurrentVersionExpiration": {"NoncurrentDays": 90},
    # Always abort incomplete multipart uploads
    "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
}

# Rule 2: Delete temp files after 1 day
TEMP_FILE_RULE = {
    "ID": "delete-temp-files",
    "Status": "Enabled",
    "Filter": {"Prefix": "tmp/"},
    "Expiration": {"Days": 1},
}

# Rule 3: Move to Intelligent-Tiering after 1 day (then auto-managed)
INTELLIGENT_TIERING_RULE = {
    "ID": "move-to-intelligent-tiering",
    "Status": "Enabled",
    "Filter": {"Prefix": "data/"},
    "Transitions": [
        {"Days": 1, "StorageClass": "INTELLIGENT_TIERING"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 16. REPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def put_bucket_replication(
    source_bucket: str,
    destination_bucket_arn: str,
    replication_role_arn: str,
    prefix: str = "",
    dest_storage_class: str = "STANDARD",
    enable_rrt: bool = False,
) -> None:
    """Configure CRR or SRR on a bucket.
    Both source and destination must have versioning enabled.
    """
    rule = {
        "ID": "replication-rule-1",
        "Status": "Enabled",
        "Filter": {"Prefix": prefix},
        "Destination": {
            "Bucket": destination_bucket_arn,
            "StorageClass": dest_storage_class,
        },
        "DeleteMarkerReplication": {"Status": "Enabled"},
    }

    if enable_rrt:
        # Replication Time Control — guarantees 99.99% objects replicated in 15 min
        rule["Destination"]["ReplicationTime"] = {
            "Status": "Enabled",
            "Time": {"Minutes": 15},
        }
        rule["Destination"]["Metrics"] = {
            "Status": "Enabled",
            "EventThreshold": {"Minutes": 15},
        }

    s3_client.put_bucket_replication(
        Bucket=source_bucket,
        ReplicationConfiguration={
            "Role": replication_role_arn,
            "Rules": [rule],
        },
    )
    print(f"Replication configured: {source_bucket} → {destination_bucket_arn}")


def get_bucket_replication(bucket_name: str) -> dict:
    """Get the replication configuration for a bucket."""
    try:
        return s3_client.get_bucket_replication(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ReplicationConfigurationNotFoundError":
            print("No replication configuration.")
            return {}
        raise


def delete_bucket_replication(bucket_name: str) -> None:
    """Remove replication configuration from a bucket."""
    s3_client.delete_bucket_replication(Bucket=bucket_name)


# ─────────────────────────────────────────────────────────────────────────────
# 17. TRANSFER ACCELERATION
# ─────────────────────────────────────────────────────────────────────────────

def enable_transfer_acceleration(bucket_name: str) -> None:
    """Enable Transfer Acceleration for faster global uploads via CloudFront edge."""
    s3_client.put_bucket_accelerate_configuration(
        Bucket=bucket_name,
        AccelerateConfiguration={"Status": "Enabled"},
    )
    print(f"Transfer Acceleration enabled on {bucket_name}")


def upload_via_accelerated_endpoint(
    local_path: str, bucket_name: str, key: str
) -> None:
    """Upload using the accelerated endpoint."""
    accelerated_client = boto3.client(
        "s3",
        region_name=REGION,
        config=boto3.session.Config(s3={"use_accelerate_endpoint": True}),
    )
    accelerated_client.upload_file(local_path, bucket_name, key)
    print(f"Uploaded via Transfer Acceleration: s3://{bucket_name}/{key}")


def disable_transfer_acceleration(bucket_name: str) -> None:
    """Disable Transfer Acceleration."""
    s3_client.put_bucket_accelerate_configuration(
        Bucket=bucket_name,
        AccelerateConfiguration={"Status": "Suspended"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# 18. BYTE-RANGE FETCHES
# ─────────────────────────────────────────────────────────────────────────────

def download_byte_range(
    bucket_name: str, key: str, start_byte: int, end_byte: int
) -> bytes:
    """Download a specific byte range of an object.
    Useful for parallel downloads or reading headers from large files.
    """
    response = s3_client.get_object(
        Bucket=bucket_name,
        Key=key,
        Range=f"bytes={start_byte}-{end_byte}",
    )
    data = response["Body"].read()
    print(f"Downloaded bytes {start_byte}-{end_byte} ({len(data)} bytes)")
    return data


def parallel_download(
    bucket_name: str, key: str, local_path: str, num_parts: int = 8
) -> None:
    """Download a large file in parallel byte-range chunks using TransferConfig."""
    file_size = s3_client.head_object(Bucket=bucket_name, Key=key)["ContentLength"]
    chunk_size = file_size // num_parts

    config = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,   # 8 MB
        max_concurrency=num_parts,
        multipart_chunksize=chunk_size,
        use_threads=True,
    )
    s3_client.download_file(bucket_name, key, local_path, Config=config)
    print(f"Parallel download complete: {local_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 19. EVENT NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def put_lambda_notification(
    bucket_name: str,
    lambda_arn: str,
    events: list = None,
    prefix: str = "",
    suffix: str = "",
) -> None:
    """Trigger a Lambda function on S3 events.
    You must also add a Lambda resource policy granting s3.amazonaws.com invoke permission.
    """
    if events is None:
        events = ["s3:ObjectCreated:*"]

    filter_rules = []
    if prefix:
        filter_rules.append({"Name": "prefix", "Value": prefix})
    if suffix:
        filter_rules.append({"Name": "suffix", "Value": suffix})

    config = {
        "LambdaFunctionConfigurations": [
            {
                "LambdaFunctionArn": lambda_arn,
                "Events": events,
                "Filter": {"Key": {"FilterRules": filter_rules}} if filter_rules else {},
            }
        ]
    }
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration=config,
    )
    print(f"Lambda notification configured: {lambda_arn}")


def put_sqs_notification(
    bucket_name: str, sqs_arn: str, events: list = None, prefix: str = ""
) -> None:
    """Send S3 event notifications to an SQS queue.
    The SQS queue policy must allow s3.amazonaws.com to send messages.
    """
    if events is None:
        events = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]

    filter_rules = [{"Name": "prefix", "Value": prefix}] if prefix else []

    config = {
        "QueueConfigurations": [
            {
                "QueueArn": sqs_arn,
                "Events": events,
                "Filter": {"Key": {"FilterRules": filter_rules}} if filter_rules else {},
            }
        ]
    }
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration=config,
    )


def put_sns_notification(
    bucket_name: str, sns_arn: str, events: list = None
) -> None:
    """Send S3 event notifications to an SNS topic."""
    if events is None:
        events = ["s3:ObjectCreated:*"]

    config = {
        "TopicConfigurations": [
            {"TopicArn": sns_arn, "Events": events}
        ]
    }
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration=config,
    )


def enable_eventbridge_notifications(bucket_name: str) -> None:
    """Enable S3 → EventBridge for advanced event routing.
    After this, create rules in EventBridge to route events to any target.
    """
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={"EventBridgeConfiguration": {}},
    )
    print(f"EventBridge notifications enabled on {bucket_name}")


def get_notification_configuration(bucket_name: str) -> dict:
    """Retrieve current event notification configuration."""
    response = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
    response.pop("ResponseMetadata", None)
    print(json.dumps(response, indent=2, default=str))
    return response


# ─────────────────────────────────────────────────────────────────────────────
# 20. OBJECT LOCK & LEGAL HOLD
# ─────────────────────────────────────────────────────────────────────────────

def create_bucket_with_object_lock(bucket_name: str, region: str) -> dict:
    """Create a bucket with Object Lock enabled.
    Object Lock must be requested at bucket creation — cannot be added later.
    """
    if region == "us-east-1":
        response = s3_client.create_bucket(
            Bucket=bucket_name,
            ObjectLockEnabledForBucket=True,
        )
    else:
        response = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
            ObjectLockEnabledForBucket=True,
        )
    # Object Lock requires versioning — it's auto-enabled
    print(f"Bucket with Object Lock created: {bucket_name}")
    return response


def put_object_lock_configuration(
    bucket_name: str, mode: str, days: int = None, years: int = None
) -> None:
    """Set a default Object Lock retention policy on a bucket.
    mode: 'GOVERNANCE' or 'COMPLIANCE'
    """
    retention = {"Mode": mode}
    if days:
        retention["Days"] = days
    elif years:
        retention["Years"] = years

    s3_client.put_object_lock_configuration(
        Bucket=bucket_name,
        ObjectLockConfiguration={
            "ObjectLockEnabled": "Enabled",
            "Rule": {"DefaultRetention": retention},
        },
    )
    print(f"Object Lock default retention: {mode} for {days or years} {'days' if days else 'years'}")


def put_object_retention(
    bucket_name: str, key: str, mode: str, retain_until: str, version_id: str = None
) -> None:
    """Apply retention to a specific object.
    mode: 'GOVERNANCE' or 'COMPLIANCE'
    retain_until: ISO 8601 datetime string, e.g. '2030-01-01T00:00:00Z'
    """
    kwargs = {
        "Bucket": bucket_name,
        "Key": key,
        "Retention": {"Mode": mode, "RetainUntilDate": retain_until},
    }
    if version_id:
        kwargs["VersionId"] = version_id
    s3_client.put_object_retention(**kwargs)
    print(f"Retention set: {mode} until {retain_until}")


def get_object_retention(bucket_name: str, key: str, version_id: str = None) -> dict:
    """Get the retention configuration for an object."""
    kwargs = {"Bucket": bucket_name, "Key": key}
    if version_id:
        kwargs["VersionId"] = version_id
    response = s3_client.get_object_retention(**kwargs)
    print(json.dumps(response.get("Retention", {}), indent=2, default=str))
    return response


def put_legal_hold_on(bucket_name: str, key: str, version_id: str = None) -> None:
    """Apply a Legal Hold to an object (no expiry — holds until explicitly removed)."""
    kwargs = {
        "Bucket": bucket_name,
        "Key": key,
        "LegalHold": {"Status": "ON"},
    }
    if version_id:
        kwargs["VersionId"] = version_id
    s3_client.put_object_legal_hold(**kwargs)
    print(f"Legal Hold ON: {key}")


def put_legal_hold_off(bucket_name: str, key: str, version_id: str = None) -> None:
    """Remove a Legal Hold from an object."""
    kwargs = {
        "Bucket": bucket_name,
        "Key": key,
        "LegalHold": {"Status": "OFF"},
    }
    if version_id:
        kwargs["VersionId"] = version_id
    s3_client.put_object_legal_hold(**kwargs)
    print(f"Legal Hold OFF: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# 21. S3 INVENTORY
# ─────────────────────────────────────────────────────────────────────────────

def put_bucket_inventory(
    source_bucket: str,
    destination_bucket_arn: str,
    inventory_id: str = "full-inventory",
    frequency: str = "Daily",
) -> None:
    """Configure S3 Inventory to generate daily/weekly object reports.
    frequency: 'Daily' or 'Weekly'
    """
    s3_client.put_bucket_inventory_configuration(
        Bucket=source_bucket,
        Id=inventory_id,
        InventoryConfiguration={
            "Id": inventory_id,
            "IsEnabled": True,
            "Destination": {
                "S3BucketDestination": {
                    "Bucket": destination_bucket_arn,
                    "Format": "Parquet",   # CSV | ORC | Parquet
                    "Prefix": "s3-inventory",
                }
            },
            "Schedule": {"Frequency": frequency},
            "IncludedObjectVersions": "All",
            "OptionalFields": [
                "Size",
                "LastModifiedDate",
                "StorageClass",
                "ETag",
                "EncryptionStatus",
                "IntelligentTieringAccessTier",
                "ChecksumAlgorithm",
            ],
        },
    )
    print(f"Inventory configured on {source_bucket} ({frequency})")


def list_bucket_inventories(bucket_name: str) -> list:
    """List all inventory configurations on a bucket."""
    response = s3_client.list_bucket_inventory_configurations(Bucket=bucket_name)
    configs = response.get("InventoryConfigurationList", [])
    for c in configs:
        print(f"  ID={c['Id']}  Enabled={c['IsEnabled']}")
    return configs


# ─────────────────────────────────────────────────────────────────────────────
# 22. CORS
# ─────────────────────────────────────────────────────────────────────────────

def put_bucket_cors(bucket_name: str, allowed_origins: list) -> None:
    """Configure CORS on a bucket for browser-based access."""
    s3_client.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                    "AllowedOrigins": allowed_origins,
                    "ExposeHeaders": ["ETag", "x-amz-request-id"],
                    "MaxAgeSeconds": 3000,
                }
            ]
        },
    )
    print(f"CORS configured for origins: {allowed_origins}")


def get_bucket_cors(bucket_name: str) -> list:
    """Retrieve CORS rules for a bucket."""
    try:
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        return response["CORSRules"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
            return []
        raise


def delete_bucket_cors(bucket_name: str) -> None:
    """Remove CORS configuration from a bucket."""
    s3_client.delete_bucket_cors(Bucket=bucket_name)


# ─────────────────────────────────────────────────────────────────────────────
# 23. STATIC WEBSITE HOSTING
# ─────────────────────────────────────────────────────────────────────────────

def enable_static_website(
    bucket_name: str,
    index_document: str = "index.html",
    error_document: str = "error.html",
) -> None:
    """Enable static website hosting on a bucket."""
    s3_client.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": index_document},
            "ErrorDocument": {"Key": error_document},
        },
    )
    print(f"Static website enabled: http://{bucket_name}.s3-website-{REGION}.amazonaws.com")


def enable_website_redirect(bucket_name: str, redirect_host: str) -> None:
    """Configure the bucket to redirect all requests to another host."""
    s3_client.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            "RedirectAllRequestsTo": {
                "HostName": redirect_host,
                "Protocol": "https",
            }
        },
    )


def get_website_configuration(bucket_name: str) -> dict:
    """Retrieve the static website configuration of a bucket."""
    try:
        return s3_client.get_bucket_website(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchWebsiteConfiguration":
            return {}
        raise


def disable_static_website(bucket_name: str) -> None:
    """Disable static website hosting."""
    s3_client.delete_bucket_website(Bucket=bucket_name)


# ─────────────────────────────────────────────────────────────────────────────
# 24. REQUESTER PAYS
# ─────────────────────────────────────────────────────────────────────────────

def enable_requester_pays(bucket_name: str) -> None:
    """Make requesters (not bucket owner) pay for requests and data transfer."""
    s3_client.put_bucket_request_payment(
        Bucket=bucket_name,
        RequestPaymentConfiguration={"Payer": "Requester"},
    )
    print(f"Requester Pays enabled on {bucket_name}")


def get_object_requester_pays(
    bucket_name: str, key: str, local_path: str
) -> None:
    """Download from a Requester Pays bucket. Must pass RequestPayer header."""
    s3_client.download_file(
        bucket_name,
        key,
        local_path,
        ExtraArgs={"RequestPayer": "requester"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# 25. S3 BATCH OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

def create_batch_copy_job(
    account_id: str,
    role_arn: str,
    manifest_arn: str,
    manifest_etag: str,
    destination_bucket: str,
    report_bucket_arn: str,
) -> dict:
    """Create an S3 Batch Operations job to copy objects listed in a manifest CSV."""
    s3control = boto3.client("s3control", region_name=REGION)
    response = s3control.create_job(
        AccountId=account_id,
        ConfirmationRequired=False,
        Operation={
            "S3PutObjectCopy": {
                "TargetResource": destination_bucket,
                "StorageClass": "STANDARD",
                "MetadataDirective": "COPY",
            }
        },
        Manifest={
            "Spec": {
                "Format": "S3BatchOperations_CSV_20180820",
                "Fields": ["Bucket", "Key"],
            },
            "Location": {
                "ObjectArn": manifest_arn,
                "ETag": manifest_etag,
            },
        },
        Report={
            "Bucket": report_bucket_arn,
            "Format": "Report_CSV_20180820",
            "Enabled": True,
            "Prefix": "batch-reports",
            "ReportScope": "AllTasks",
        },
        Priority=10,
        RoleArn=role_arn,
        Description="Batch copy job",
    )
    job_id = response["JobId"]
    print(f"Batch job created: {job_id}")
    return response


def create_batch_lambda_job(
    account_id: str,
    role_arn: str,
    manifest_arn: str,
    manifest_etag: str,
    lambda_arn: str,
    report_bucket_arn: str,
) -> dict:
    """Create a Batch Operations job that invokes Lambda for each object."""
    s3control = boto3.client("s3control", region_name=REGION)
    response = s3control.create_job(
        AccountId=account_id,
        ConfirmationRequired=False,
        Operation={
            "LambdaInvoke": {"FunctionArn": lambda_arn}
        },
        Manifest={
            "Spec": {
                "Format": "S3BatchOperations_CSV_20180820",
                "Fields": ["Bucket", "Key"],
            },
            "Location": {"ObjectArn": manifest_arn, "ETag": manifest_etag},
        },
        Report={
            "Bucket": report_bucket_arn,
            "Format": "Report_CSV_20180820",
            "Enabled": True,
            "Prefix": "lambda-batch-reports",
            "ReportScope": "AllTasks",
        },
        Priority=5,
        RoleArn=role_arn,
    )
    return response


def describe_batch_job(account_id: str, job_id: str) -> dict:
    """Get the status and details of a Batch Operations job."""
    s3control = boto3.client("s3control", region_name=REGION)
    response = s3control.describe_job(AccountId=account_id, JobId=job_id)
    job = response["Job"]
    print(f"Job {job_id}: Status={job['Status']}  Progress={job.get('ProgressSummary', {})}")
    return response


# ─────────────────────────────────────────────────────────────────────────────
# 26. RESTORE FROM GLACIER
# ─────────────────────────────────────────────────────────────────────────────

def restore_object_from_glacier(
    bucket_name: str,
    key: str,
    days: int = 7,
    tier: str = "Standard",
) -> None:
    """Initiate a temporary restore of an archived object.
    tier: 'Expedited' (1-5 min) | 'Standard' (3-5 hrs) | 'Bulk' (5-12 hrs)
    For Glacier Instant Retrieval, no restore is needed.
    """
    s3_client.restore_object(
        Bucket=bucket_name,
        Key=key,
        RestoreRequest={
            "Days": days,
            "GlacierJobParameters": {"Tier": tier},
        },
    )
    print(f"Restore initiated for {key} (tier={tier}, available for {days} days)")


def check_restore_status(bucket_name: str, key: str) -> str:
    """Check whether a Glacier restore is in progress or complete.
    Returns: 'in-progress', 'restored', or 'not-restored'
    """
    response = s3_client.head_object(Bucket=bucket_name, Key=key)
    restore_header = response.get("Restore", "")
    if not restore_header:
        return "not-restored"
    if 'ongoing-request="true"' in restore_header:
        return "in-progress"
    return "restored"


# ─────────────────────────────────────────────────────────────────────────────
# 27. FOLDER-STYLE SYNC (TransferManager)
# ─────────────────────────────────────────────────────────────────────────────

def upload_directory(local_dir: str, bucket_name: str, s3_prefix: str) -> None:
    """Upload an entire local directory to S3 (mirrors aws s3 sync behavior)."""
    for root, dirs, files in os.walk(local_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            # Compute relative key
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = f"{s3_prefix}/{relative_path.replace(os.sep, '/')}".lstrip("/")
            s3_client.upload_file(local_path, bucket_name, s3_key)
            print(f"  Uploaded {local_path} → s3://{bucket_name}/{s3_key}")


def download_directory(bucket_name: str, s3_prefix: str, local_dir: str) -> None:
    """Download all objects under an S3 prefix to a local directory."""
    os.makedirs(local_dir, exist_ok=True)
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=s3_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            relative_key = key[len(s3_prefix):].lstrip("/")
            local_path = os.path.join(local_dir, relative_key.replace("/", os.sep))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            s3_client.download_file(bucket_name, key, local_path)
            print(f"  Downloaded s3://{bucket_name}/{key} → {local_path}")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Bucket CRUD ──────────────────────────────────────────────────────────
    # create_bucket("my-demo-bucket", "us-east-1")
    # list_buckets()
    # delete_bucket("my-demo-bucket")

    # ── Object operations ────────────────────────────────────────────────────
    # upload_file("data.csv", BUCKET, "uploads/data.csv")
    # download_file(BUCKET, "uploads/data.csv", "data_local.csv")
    # content = get_object(BUCKET, "uploads/data.csv")
    # head_object(BUCKET, "uploads/data.csv")

    # ── Encryption ───────────────────────────────────────────────────────────
    # set_default_encryption_sse_kms(BUCKET, "arn:aws:kms:us-east-1:123456789012:key/mrk-xxx")
    # upload_sse_kms(BUCKET, "secure/data.csv", b"sensitive,data", "arn:aws:kms:...")

    # ── Pre-signed URL ───────────────────────────────────────────────────────
    # url = generate_presigned_get_url(BUCKET, "uploads/data.csv", expiry_seconds=3600)

    # ── S3 Select ────────────────────────────────────────────────────────────
    # result = s3_select_csv(BUCKET, "data/records.csv", "SELECT * FROM S3Object WHERE age > 30")
    # print(result)

    # ── Multipart Upload ─────────────────────────────────────────────────────
    # multipart_upload_managed("large_file.bin", BUCKET, "large/file.bin")

    # ── Versioning ───────────────────────────────────────────────────────────
    # enable_versioning(BUCKET)
    # list_object_versions(BUCKET, "uploads/data.csv")

    # ── Lifecycle ────────────────────────────────────────────────────────────
    # put_lifecycle_configuration(BUCKET, [LOG_LIFECYCLE_RULE, TEMP_FILE_RULE])

    # ── Event Notifications ──────────────────────────────────────────────────
    # enable_eventbridge_notifications(BUCKET)
    # put_lambda_notification(BUCKET, "arn:aws:lambda:us-east-1:123:function:my-fn", prefix="uploads/", suffix=".csv")

    # ── Object Lock ──────────────────────────────────────────────────────────
    # create_bucket_with_object_lock("compliance-bucket", "us-east-1")
    # put_object_retention("compliance-bucket", "report.pdf", "COMPLIANCE", "2030-01-01T00:00:00Z")

    # ── S3 Select ────────────────────────────────────────────────────────────
    # result = s3_select_parquet(BUCKET, "data/sales.parquet", "SELECT name, amount FROM S3Object WHERE amount > 1000")

    print("S3 operations module loaded. Uncomment example calls to run them.")
