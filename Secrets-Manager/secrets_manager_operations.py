"""
AWS Secrets Manager Operations
===============================
Practical examples for managing secrets using boto3

Key operations:
- Create, retrieve, update, and delete secrets
- Manage versions and labels
- Configure automatic rotation
- Access control and encryption
"""

import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List
import time

# Initialize Secrets Manager client
client = boto3.client('secretsmanager', region_name='us-east-1')


# ============================================================================
# 1. CREATE SECRETS
# ============================================================================

def create_simple_secret(secret_name: str, secret_value: str,
                        description: str = "", tags: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Create a simple string secret

    Args:
        secret_name: Name of the secret (e.g., 'prod/api/stripe-key')
        secret_value: The secret value
        description: Optional description
        tags: Optional key-value tags

    Returns:
        Response with ARN and version ID
    """
    try:
        params = {
            'Name': secret_name,
            'SecretString': secret_value,
        }

        if description:
            params['Description'] = description

        if tags:
            params['Tags'] = [{'Key': k, 'Value': v} for k, v in tags.items()]

        response = client.create_secret(**params)
        print(f"✓ Created secret: {secret_name}")
        print(f"  ARN: {response['ARN']}")
        return response

    except ClientError as e:
        print(f"✗ Error creating secret: {e}")
        raise


def create_json_secret(secret_name: str, secret_dict: Dict[str, Any],
                       description: str = "", tags: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Create a JSON secret (useful for database credentials, API keys with metadata)

    Args:
        secret_name: Name of the secret
        secret_dict: Dictionary to store as JSON
        description: Optional description
        tags: Optional tags

    Returns:
        Response with ARN and version ID
    """
    try:
        response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_dict),
            Description=description or f"JSON secret: {secret_name}",
            Tags=[{'Key': k, 'Value': v} for k, v in (tags or {}).items()]
        )
        print(f"✓ Created JSON secret: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error creating JSON secret: {e}")
        raise


def create_database_secret(secret_name: str, username: str, password: str,
                          host: str, port: int, engine: str,
                          description: str = "") -> Dict[str, Any]:
    """
    Create a database credentials secret

    Args:
        secret_name: Name of the secret
        username: Database username
        password: Database password
        host: Database host/endpoint
        port: Database port
        engine: Database engine (mysql, postgres, oracle, etc.)
        description: Optional description

    Returns:
        Response with ARN
    """
    db_secret = {
        "username": username,
        "password": password,
        "engine": engine,
        "host": host,
        "port": port
    }

    return create_json_secret(secret_name, db_secret, description)


# ============================================================================
# 2. RETRIEVE SECRETS
# ============================================================================

def get_secret_value(secret_name: str, version_id: str = None,
                     version_stage: str = "AWSCURRENT") -> Dict[str, Any]:
    """
    Retrieve a secret value

    Args:
        secret_name: Name of the secret
        version_id: Optional specific version ID
        version_stage: Version stage (AWSCURRENT, AWSPENDING, or custom)

    Returns:
        Response with SecretString or SecretBinary
    """
    try:
        params = {'SecretId': secret_name}

        if version_id:
            params['VersionId'] = version_id
        else:
            params['VersionStage'] = version_stage

        response = client.get_secret_value(**params)
        print(f"✓ Retrieved secret: {secret_name}")
        return response

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"✗ Secret not found: {secret_name}")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print(f"✗ Secret is scheduled for deletion: {secret_name}")
        else:
            print(f"✗ Error retrieving secret: {e}")
        raise


def get_secret_string(secret_name: str, version_stage: str = "AWSCURRENT") -> str:
    """
    Get secret value as string (convenience function)
    """
    response = get_secret_value(secret_name, version_stage=version_stage)
    return response.get('SecretString', '')


def get_secret_json(secret_name: str, version_stage: str = "AWSCURRENT") -> Dict[str, Any]:
    """
    Get secret value parsed as JSON (for JSON secrets)
    """
    secret_str = get_secret_string(secret_name, version_stage=version_stage)
    return json.loads(secret_str) if secret_str else {}


def get_database_credentials(secret_name: str) -> Dict[str, Any]:
    """
    Get database credentials from a secret

    Returns dict with: username, password, host, port, engine
    """
    return get_secret_json(secret_name)


# ============================================================================
# 3. UPDATE SECRETS
# ============================================================================

def update_secret_value(secret_name: str, new_value: str) -> Dict[str, Any]:
    """
    Update a secret's value (creates new version)

    Args:
        secret_name: Name of the secret
        new_value: New secret value

    Returns:
        Response with new version ID
    """
    try:
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=new_value
        )
        print(f"✓ Updated secret: {secret_name}")
        print(f"  New version: {response['VersionId']}")
        return response

    except ClientError as e:
        print(f"✗ Error updating secret: {e}")
        raise


def update_secret_json(secret_name: str, secret_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a JSON secret
    """
    return update_secret_value(secret_name, json.dumps(secret_dict))


def update_secret_description(secret_name: str, new_description: str) -> Dict[str, Any]:
    """
    Update secret description (metadata) without changing value
    """
    try:
        response = client.update_secret(
            SecretId=secret_name,
            Description=new_description
        )
        print(f"✓ Updated description for: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error updating description: {e}")
        raise


def update_database_password(secret_name: str, new_password: str) -> Dict[str, Any]:
    """
    Update only the password in a database credentials secret
    """
    current = get_secret_json(secret_name)
    current['password'] = new_password
    return update_secret_json(secret_name, current)


# ============================================================================
# 4. MANAGE METADATA
# ============================================================================

def describe_secret(secret_name: str) -> Dict[str, Any]:
    """
    Get secret metadata (ARN, creation date, rotation info, etc.)
    DO NOT return the secret value itself
    """
    try:
        response = client.describe_secret(SecretId=secret_name)
        print(f"✓ Retrieved metadata for: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error describing secret: {e}")
        raise


def add_tags(secret_name: str, tags: Dict[str, str]) -> None:
    """
    Add or update tags on a secret
    """
    try:
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        client.tag_resource(
            SecretId=secret_name,
            Tags=tag_list
        )
        print(f"✓ Added tags to: {secret_name}")

    except ClientError as e:
        print(f"✗ Error adding tags: {e}")
        raise


def remove_tags(secret_name: str, tag_keys: List[str]) -> None:
    """
    Remove tags from a secret
    """
    try:
        client.untag_resource(
            SecretId=secret_name,
            TagKeys=tag_keys
        )
        print(f"✓ Removed tags from: {secret_name}")

    except ClientError as e:
        print(f"✗ Error removing tags: {e}")
        raise


def list_secrets(filters: Dict[str, List[str]] = None) -> List[Dict[str, Any]]:
    """
    List all secrets with optional filtering

    Args:
        filters: Dict with 'name', 'description', or 'tag-key' filters
            Example: {'name': ['prod/database']}

    Returns:
        List of secrets
    """
    try:
        params = {}

        if filters:
            filter_list = []
            for key, values in filters.items():
                filter_list.append({'Key': key, 'Values': values})
            params['Filters'] = filter_list

        response = client.list_secrets(**params)
        secrets = response.get('SecretList', [])
        print(f"✓ Retrieved {len(secrets)} secrets")
        return secrets

    except ClientError as e:
        print(f"✗ Error listing secrets: {e}")
        raise


# ============================================================================
# 5. VERSION MANAGEMENT
# ============================================================================

def list_secret_versions(secret_name: str) -> List[Dict[str, Any]]:
    """
    Get version history of a secret
    """
    try:
        response = client.list_secret_version_ids(SecretId=secret_name)
        print(f"✓ Retrieved versions for: {secret_name}")
        return response.get('Versions', [])

    except ClientError as e:
        print(f"✗ Error listing versions: {e}")
        raise


def label_version(secret_name: str, version_id: str, label: str) -> None:
    """
    Add a custom label to a specific version
    """
    try:
        client.update_secret_version_stage(
            SecretId=secret_name,
            VersionStage=label,
            MoveToVersionId=version_id
        )
        print(f"✓ Labeled version {version_id} as '{label}'")

    except ClientError as e:
        print(f"✗ Error labeling version: {e}")
        raise


def remove_label_from_version(secret_name: str, version_id: str, label: str) -> None:
    """
    Remove a label from a specific version
    """
    try:
        client.update_secret_version_stage(
            SecretId=secret_name,
            VersionStage=label,
            RemoveFromVersionId=version_id
        )
        print(f"✓ Removed label '{label}' from version {version_id}")

    except ClientError as e:
        print(f"✗ Error removing label: {e}")
        raise


def get_secret_by_version_stage(secret_name: str, stage: str = "AWSCURRENT") -> Dict[str, Any]:
    """
    Get secret value for a specific stage (typically AWSCURRENT or AWSPENDING)
    """
    return get_secret_value(secret_name, version_stage=stage)


# ============================================================================
# 6. PASSWORD ROTATION
# ============================================================================

def enable_rotation(secret_name: str, lambda_arn: str,
                    rotation_days: int = 30) -> Dict[str, Any]:
    """
    Enable automatic password rotation for a secret

    Args:
        secret_name: Name of the secret
        lambda_arn: ARN of the Lambda function to handle rotation
        rotation_days: Rotation interval in days

    Returns:
        Response from rotate_secret call
    """
    try:
        response = client.rotate_secret(
            SecretId=secret_name,
            RotationRules={"AutomaticallyAfterDays": rotation_days},
            RotationLambdaARN=lambda_arn
        )
        print(f"✓ Enabled rotation for: {secret_name}")
        print(f"  Interval: Every {rotation_days} days")
        print(f"  Lambda: {lambda_arn}")
        return response

    except ClientError as e:
        print(f"✗ Error enabling rotation: {e}")
        raise


def disable_rotation(secret_name: str) -> Dict[str, Any]:
    """
    Disable automatic rotation for a secret
    """
    try:
        response = client.update_secret(
            SecretId=secret_name,
            RotationRules={'AutomaticallyAfterDays': 0}
        )
        print(f"✓ Disabled rotation for: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error disabling rotation: {e}")
        raise


def rotate_secret_immediately(secret_name: str) -> Dict[str, Any]:
    """
    Trigger immediate rotation of a secret
    """
    try:
        response = client.rotate_secret(SecretId=secret_name, RotateImmediately=True)
        print(f"✓ Triggered immediate rotation for: {secret_name}")
        print(f"  Rotation ID: {response['VersionId']}")
        return response

    except ClientError as e:
        print(f"✗ Error rotating secret: {e}")
        raise


def get_rotation_status(secret_name: str) -> Dict[str, Any]:
    """
    Get rotation configuration and status
    """
    metadata = describe_secret(secret_name)
    return {
        'RotationEnabled': metadata.get('RotationEnabled', False),
        'RotationRules': metadata.get('RotationRules'),
        'RotationLambdaARN': metadata.get('RotationLambdaARN'),
        'LastRotatedDate': metadata.get('LastRotatedDate'),
        'LastFailedRotationDate': metadata.get('LastFailedRotationDate')
    }


# ============================================================================
# 7. DELETE SECRETS
# ============================================================================

def delete_secret_with_recovery(secret_name: str,
                                recovery_window_days: int = 7) -> Dict[str, Any]:
    """
    Schedule secret for deletion with recovery window (recommended)

    Args:
        secret_name: Name of the secret
        recovery_window_days: Days before permanent deletion (7-30)

    Returns:
        Response with deletion date
    """
    try:
        response = client.delete_secret(
            SecretId=secret_name,
            RecoveryWindowInDays=recovery_window_days
        )
        print(f"✓ Scheduled deletion for: {secret_name}")
        print(f"  Recovery window: {recovery_window_days} days")
        print(f"  Deletion date: {response['DeletionDate']}")
        return response

    except ClientError as e:
        print(f"✗ Error deleting secret: {e}")
        raise


def delete_secret_immediately(secret_name: str) -> Dict[str, Any]:
    """
    IMMEDIATELY and permanently delete a secret (no recovery)
    Use with caution!
    """
    try:
        response = client.delete_secret(
            SecretId=secret_name,
            ForceDeleteWithoutRecovery=True
        )
        print(f"✓ PERMANENTLY deleted: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error deleting secret: {e}")
        raise


def restore_secret(secret_name: str) -> Dict[str, Any]:
    """
    Cancel a scheduled deletion and restore the secret
    """
    try:
        response = client.restore_secret(SecretId=secret_name)
        print(f"✓ Restored secret: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error restoring secret: {e}")
        raise


# ============================================================================
# 8. ADVANCED OPERATIONS
# ============================================================================

def replicate_secret_to_region(secret_name: str, target_region: str,
                              kms_key_id: str = None) -> Dict[str, Any]:
    """
    Replicate a secret to another region (for disaster recovery)

    Args:
        secret_name: Name of the secret
        target_region: Target AWS region
        kms_key_id: Optional KMS key in target region

    Returns:
        Response with replication status
    """
    try:
        replica_config = {
            'RegionCode': target_region
        }
        if kms_key_id:
            replica_config['KmsKeyId'] = kms_key_id

        response = client.replicate_secret_to_regions(
            SecretId=secret_name,
            AddReplicaRegions=[replica_config]
        )
        print(f"✓ Replicating secret to region: {target_region}")
        return response

    except ClientError as e:
        print(f"✗ Error replicating secret: {e}")
        raise


def put_secret_value(secret_name: str, secret_value: str,
                     client_request_token: str = None,
                     version_stages: List[str] = None) -> Dict[str, Any]:
    """
    Put a new secret value (typically used in rotation Lambda functions)

    Args:
        secret_name: Name of the secret
        secret_value: New secret value
        client_request_token: Idempotency token
        version_stages: Version stages (e.g., ['AWSPENDING'])

    Returns:
        Response with new version ID
    """
    try:
        params = {
            'SecretId': secret_name,
            'SecretString': secret_value
        }

        if client_request_token:
            params['ClientRequestToken'] = client_request_token

        if version_stages:
            params['VersionStages'] = version_stages

        response = client.put_secret_value(**params)
        print(f"✓ Put new secret value: {secret_name}")
        return response

    except ClientError as e:
        print(f"✗ Error putting secret value: {e}")
        raise


def get_random_password(length: int = 32, exclude_chars: str = "") -> str:
    """
    Generate a random password using Secrets Manager's random generator

    Args:
        length: Password length (8-4096 bytes)
        exclude_chars: Characters to exclude

    Returns:
        Random password string
    """
    try:
        response = client.get_random_password(
            PasswordLength=length,
            ExcludeCharacters=exclude_chars
        )
        password = response['RandomPassword']
        print(f"✓ Generated random password ({length} chars)")
        return password

    except ClientError as e:
        print(f"✗ Error generating password: {e}")
        raise


# ============================================================================
# 9. HELPER & UTILITY FUNCTIONS
# ============================================================================

def secret_exists(secret_name: str) -> bool:
    """
    Check if a secret exists
    """
    try:
        client.describe_secret(SecretId=secret_name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False
    except ClientError:
        return False


def print_secret_info(secret_name: str) -> None:
    """
    Pretty-print secret metadata (NOT the value)
    """
    try:
        metadata = describe_secret(secret_name)

        print(f"\n{'='*60}")
        print(f"Secret: {metadata['Name']}")
        print(f"{'='*60}")
        print(f"ARN:            {metadata['ARN']}")
        print(f"Created:        {metadata.get('CreatedDate')}")
        print(f"Last Updated:   {metadata.get('LastChangedDate')}")
        print(f"Last Accessed:  {metadata.get('LastAccessedDate')}")
        print(f"Description:    {metadata.get('Description', 'N/A')}")

        if metadata.get('Tags'):
            print(f"\nTags:")
            for tag in metadata['Tags']:
                print(f"  {tag['Key']}: {tag['Value']}")

        if metadata.get('RotationEnabled'):
            print(f"\nRotation:")
            print(f"  Enabled:      True")
            print(f"  Lambda ARN:   {metadata.get('RotationLambdaARN')}")
            print(f"  Rules:        {metadata.get('RotationRules')}")
            print(f"  Last Rotated: {metadata.get('LastRotatedDate')}")

        print(f"\nVersions:")
        for vid, stages in metadata.get('VersionIdsToStages', {}).items():
            print(f"  {vid}: {stages}")
        print(f"{'='*60}\n")

    except ClientError as e:
        print(f"✗ Error: {e}")


# ============================================================================
# 10. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("AWS Secrets Manager Examples\n")

    # Example 1: Create a simple API key secret
    print("\n--- Creating Simple Secret ---")
    try:
        create_simple_secret(
            secret_name="demo/api/example-key",
            secret_value="sk-12345abcdefghij",
            description="Example API key",
            tags={"Environment": "Demo", "Service": "API"}
        )
    except:
        pass

    # Example 2: Create database credentials
    print("\n--- Creating Database Secret ---")
    try:
        create_database_secret(
            secret_name="demo/database/mysql",
            username="admin",
            password="SecureP@ssw0rd123!",
            host="mysql.example.com",
            port=3306,
            engine="mysql",
            description="MySQL production database"
        )
    except:
        pass

    # Example 3: List secrets
    print("\n--- Listing Secrets ---")
    try:
        secrets = list_secrets()
        for secret in secrets[:5]:  # Show first 5
            print(f"  - {secret['Name']}")
    except:
        pass

    # Example 4: Retrieve a secret value
    print("\n--- Retrieving Secret ---")
    try:
        secret = get_secret_json("demo/database/mysql")
        print(f"  Host: {secret.get('host')}")
        print(f"  Port: {secret.get('port')}")
        print(f"  Engine: {secret.get('engine')}")
    except:
        pass

    # Example 5: Print secret info
    print("\n--- Secret Metadata ---")
    try:
        print_secret_info("demo/database/mysql")
    except:
        pass

    # Example 6: Update a secret
    print("\n--- Updating Secret ---")
    try:
        update_secret_value(
            "demo/api/example-key",
            "sk-new-key-xyz"
        )
    except:
        pass

    # Example 7: Add tags
    print("\n--- Adding Tags ---")
    try:
        add_tags(
            "demo/api/example-key",
            {"Team": "Backend", "CostCenter": "Engineering"}
        )
    except:
        pass

    # Example 8: Version history
    print("\n--- Version History ---")
    try:
        versions = list_secret_versions("demo/database/mysql")
        print(f"  Total versions: {len(versions)}")
        for v in versions:
            print(f"    {v['VersionId']}: {v.get('VersionStages', [])}")
    except:
        pass

    # Example 9: Schedule deletion
    print("\n--- Schedule Deletion (7-day recovery) ---")
    try:
        delete_secret_with_recovery("demo/api/example-key", recovery_window_days=7)
    except:
        pass

    print("\n✓ Examples complete!")
