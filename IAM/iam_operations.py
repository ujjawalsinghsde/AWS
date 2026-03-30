"""
AWS IAM (Identity and Access Management) - Boto3 Operations
Document: IAM/iam_operations.py

This module provides practical boto3 examples for common IAM operations.
"""

import boto3
import json
from datetime import datetime, timedelta

# Initialize IAM client
iam = boto3.client('iam')
sts = boto3.client('sts')


# ============================================================================
# 1. MANAGE USERS
# ============================================================================

def create_user(username, tags=None):
    """Create a new IAM user"""
    try:
        user_tags = tags or [
            {'Key': 'Environment', 'Value': 'development'},
            {'Key': 'ManagedBy', 'Value': 'automation'}
        ]

        response = iam.create_user(
            UserName=username,
            Tags=user_tags
        )
        print(f"✓ User created: {username}")
        return response
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        return None


def list_users():
    """List all IAM users"""
    try:
        response = iam.list_users()
        print(f"\n👥 IAM Users ({len(response['Users'])} total):")
        print("-" * 80)
        for user in response['Users']:
            print(f"  {user['UserName']:30} | Created: {user['CreateDate']}")
        return response
    except Exception as e:
        print(f"✗ Error listing users: {e}")
        return None


def get_user_details(username):
    """Get detailed information about a user"""
    try:
        response = iam.get_user(UserName=username)
        user = response['User']

        print(f"\n📋 User Details: {username}")
        print("-" * 80)
        print(f"  Username:  {user['UserName']}")
        print(f"  User ID:   {user['UserId']}")
        print(f"  ARN:       {user['Arn']}")
        print(f"  Created:   {user['CreateDate']}")
        print(f"  Tags:      {user.get('Tags', [])}")

        # List access keys
        keys = iam.list_access_keys(UserName=username)
        print(f"\n  Access Keys:")
        for key in keys['AccessKeyMetadata']:
            age_days = (datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']).days
            print(f"    - {key['AccessKeyId']} | Status: {key['Status']} | Age: {age_days} days")

        # List groups
        groups = iam.list_groups_for_user(UserName=username)
        print(f"\n  Groups ({len(groups['Groups'])} total):")
        for group in groups['Groups']:
            print(f"    - {group['GroupName']}")

        # List policies
        policies = iam.list_attached_user_policies(UserName=username)
        print(f"\n  Attached Policies ({len(policies['AttachedPolicies'])} total):")
        for policy in policies['AttachedPolicies']:
            print(f"    - {policy['PolicyName']}")

        return response
    except Exception as e:
        print(f"✗ Error getting user details: {e}")
        return None


def delete_user(username):
    """Delete an IAM user (all policies must be removed first)"""
    try:
        # Remove from groups
        groups = iam.list_groups_for_user(UserName=username)
        for group in groups['Groups']:
            iam.remove_user_from_group(GroupName=group['GroupName'], UserName=username)

        # Detach inline policies
        inline_policies = iam.list_user_policies(UserName=username)
        for policy_name in inline_policies['PolicyNames']:
            iam.delete_user_policy(UserName=username, PolicyName=policy_name)

        # Detach managed policies
        managed_policies = iam.list_attached_user_policies(UserName=username)
        for policy in managed_policies['AttachedPolicies']:
            iam.detach_user_policy(UserName=username, PolicyArn=policy['PolicyArn'])

        # Delete access keys
        keys = iam.list_access_keys(UserName=username)
        for key in keys['AccessKeyMetadata']:
            iam.delete_access_key(UserName=username, AccessKeyId=key['AccessKeyId'])

        # Delete user
        iam.delete_user(UserName=username)
        print(f"✓ User deleted: {username}")
        return True
    except Exception as e:
        print(f"✗ Error deleting user: {e}")
        return None


# ============================================================================
# 2. MANAGE GROUPS
# ============================================================================

def create_group(group_name):
    """Create an IAM group"""
    try:
        response = iam.create_group(GroupName=group_name)
        print(f"✓ Group created: {group_name}")
        return response
    except Exception as e:
        print(f"✗ Error creating group: {e}")
        return None


def list_groups():
    """List all IAM groups"""
    try:
        response = iam.list_groups()
        print(f"\n📁 IAM Groups ({len(response['Groups'])} total):")
        print("-" * 80)
        for group in response['Groups']:
            print(f"  {group['GroupName']:30} | Created: {group['CreateDate']}")
        return response
    except Exception as e:
        print(f"✗ Error listing groups: {e}")
        return None


def add_user_to_group(group_name, username):
    """Add user to a group"""
    try:
        iam.add_user_to_group(GroupName=group_name, UserName=username)
        print(f"✓ Added {username} to group {group_name}")
        return True
    except Exception as e:
        print(f"✗ Error adding user to group: {e}")
        return None


def list_group_members(group_name):
    """List members of a group"""
    try:
        response = iam.get_group(GroupName=group_name)
        print(f"\n👥 Members of {group_name} ({len(response['Users'])} total):")
        print("-" * 80)
        for user in response['Users']:
            print(f"  - {user['UserName']}")
        return response
    except Exception as e:
        print(f"✗ Error listing group members: {e}")
        return None


def remove_user_from_group(group_name, username):
    """Remove user from a group"""
    try:
        iam.remove_user_from_group(GroupName=group_name, UserName=username)
        print(f"✓ Removed {username} from group {group_name}")
        return True
    except Exception as e:
        print(f"✗ Error removing user from group: {e}")
        return None


# ============================================================================
# 3. MANAGE ROLES
# ============================================================================

def create_lambda_role(role_name):
    """Create an IAM role for Lambda"""
    try:
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

        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Lambda execution'
        )
        print(f"✓ Lambda role created: {role_name}")
        return response
    except Exception as e:
        print(f"✗ Error creating role: {e}")
        return None


def create_ec2_role(role_name):
    """Create an IAM role for EC2"""
    try:
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for EC2 instances'
        )
        print(f"✓ EC2 role created: {role_name}")
        return response
    except Exception as e:
        print(f"✗ Error creating role: {e}")
        return None


def list_roles():
    """List all IAM roles"""
    try:
        response = iam.list_roles()
        print(f"\n🎭 IAM Roles ({len(response['Roles'])} total):")
        print("-" * 80)
        for role in response['Roles']:
            print(f"  {role['RoleName']:30} | Created: {role['CreateDate']}")
        return response
    except Exception as e:
        print(f"✗ Error listing roles: {e}")
        return None


def get_role_details(role_name):
    """Get detailed information about a role"""
    try:
        response = iam.get_role(RoleName=role_name)
        role = response['Role']

        print(f"\n📋 Role Details: {role_name}")
        print("-" * 80)
        print(f"  Role Name:  {role['RoleName']}")
        print(f"  Role ID:    {role['RoleId']}")
        print(f"  ARN:        {role['Arn']}")
        print(f"  Created:    {role['CreateDate']}")

        # List attached policies
        policies = iam.list_attached_role_policies(RoleName=role_name)
        print(f"\n  Attached Policies ({len(policies['AttachedPolicies'])} total):")
        for policy in policies['AttachedPolicies']:
            print(f"    - {policy['PolicyName']} ({policy['PolicyArn']})")

        return response
    except Exception as e:
        print(f"✗ Error getting role details: {e}")
        return None


def delete_role(role_name):
    """Delete an IAM role (all policies must be removed first)"""
    try:
        # Detach inline policies
        inline_policies = iam.list_role_policies(RoleName=role_name)
        for policy_name in inline_policies['PolicyNames']:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

        # Detach managed policies
        managed_policies = iam.list_attached_role_policies(RoleName=role_name)
        for policy in managed_policies['AttachedPolicies']:
            iam.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])

        # Delete role
        iam.delete_role(RoleName=role_name)
        print(f"✓ Role deleted: {role_name}")
        return True
    except Exception as e:
        print(f"✗ Error deleting role: {e}")
        return None


# ============================================================================
# 4. MANAGE POLICIES
# ============================================================================

def create_s3_policy(policy_name, bucket_name):
    """Create a policy for S3 access"""
    try:
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }

        response = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description=f'Policy for S3 access to {bucket_name}'
        )
        print(f"✓ Policy created: {policy_name}")
        return response
    except Exception as e:
        print(f"✗ Error creating policy: {e}")
        return None


def attach_policy_to_user(username, policy_arn):
    """Attach a managed policy to a user"""
    try:
        iam.attach_user_policy(
            UserName=username,
            PolicyArn=policy_arn
        )
        print(f"✓ Policy attached to user: {username}")
        return True
    except Exception as e:
        print(f"✗ Error attaching policy: {e}")
        return None


def attach_policy_to_group(group_name, policy_arn):
    """Attach a managed policy to a group"""
    try:
        iam.attach_group_policy(
            GroupName=group_name,
            PolicyArn=policy_arn
        )
        print(f"✓ Policy attached to group: {group_name}")
        return True
    except Exception as e:
        print(f"✗ Error attaching policy: {e}")
        return None


def attach_policy_to_role(role_name, policy_arn):
    """Attach a managed policy to a role"""
    try:
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print(f"✓ Policy attached to role: {role_name}")
        return True
    except Exception as e:
        print(f"✗ Error attaching policy: {e}")
        return None


def list_policies():
    """List all customer-managed policies"""
    try:
        response = iam.list_policies(Scope='Local')
        print(f"\n📋 Customer-Managed Policies ({len(response['Policies'])} total):")
        print("-" * 80)
        for policy in response['Policies']:
            print(f"  {policy['PolicyName']:30} | ARN: {policy['Arn']}")
        return response
    except Exception as e:
        print(f"✗ Error listing policies: {e}")
        return None


def get_policy_details(policy_arn):
    """Get detailed information about a policy"""
    try:
        policy = iam.get_policy(PolicyArn=policy_arn)
        policy_doc = iam.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=policy['Policy']['DefaultVersionId']
        )

        print(f"\n📋 Policy Details: {policy['Policy']['PolicyName']}")
        print("-" * 80)
        print(f"  ARN:           {policy['Policy']['Arn']}")
        print(f"  Created:       {policy['Policy']['CreateDate']}")
        print(f"  Updated:       {policy['Policy']['UpdateDate']}")
        print(f"  Attachment Count: {policy['Policy']['AttachmentCount']}")

        print(f"\n  Policy Document:")
        print(json.dumps(policy_doc['PolicyVersion']['Document'], indent=2))

        return policy_doc
    except Exception as e:
        print(f"✗ Error getting policy details: {e}")
        return None


# ============================================================================
# 5. MANAGE ACCESS KEYS
# ============================================================================

def create_access_key(username):
    """Create access key for a user"""
    try:
        response = iam.create_access_key(UserName=username)
        key = response['AccessKey']

        print(f"\n🔑 Access Key Created for {username}")
        print("-" * 80)
        print(f"  Access Key ID:     {key['AccessKeyId']}")
        print(f"  Secret Access Key: {key['SecretAccessKey']}")
        print(f"  Status:            {key['Status']}")
        print(f"  Created:           {key['CreateDate']}")

        print("\n⚠️  SAVE THIS IMMEDIATELY - Secret key cannot be retrieved later!")
        return response
    except Exception as e:
        print(f"✗ Error creating access key: {e}")
        return None


def list_access_keys(username):
    """List access keys for a user"""
    try:
        response = iam.list_access_keys(UserName=username)
        print(f"\n🔑 Access Keys for {username} ({len(response['AccessKeyMetadata'])} total):")
        print("-" * 80)
        for key in response['AccessKeyMetadata']:
            age_days = (datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']).days
            print(f"  {key['AccessKeyId']:30} | Status: {key['Status']:8} | Age: {age_days} days")
            if age_days > 90:
                print(f"    ⚠️  ROTATE KEY - Over 90 days old!")
        return response
    except Exception as e:
        print(f"✗ Error listing access keys: {e}")
        return None


def deactivate_access_key(username, access_key_id):
    """Deactivate an access key"""
    try:
        iam.update_access_key(
            UserName=username,
            AccessKeyId=access_key_id,
            Status='Inactive'
        )
        print(f"✓ Access key deactivated: {access_key_id}")
        return True
    except Exception as e:
        print(f"✗ Error deactivating access key: {e}")
        return None


def delete_access_key(username, access_key_id):
    """Delete an access key"""
    try:
        iam.delete_access_key(
            UserName=username,
            AccessKeyId=access_key_id
        )
        print(f"✓ Access key deleted: {access_key_id}")
        return True
    except Exception as e:
        print(f"✗ Error deleting access key: {e}")
        return None


# ============================================================================
# 6. MFA & AUTHENTICATION
# ============================================================================

def setup_virtual_mfa(username, device_name=None):
    """Create virtual MFA device for a user"""
    try:
        if not device_name:
            device_name = f"{username}-mfa"

        response = iam.create_virtual_mfa_device(
            VirtualMFADeviceName=device_name
        )

        print(f"\n🔐 MFA Device Created: {device_name}")
        print("-" * 80)
        print(f"  Serial Number: {response['VirtualMFADevice']['SerialNumber']}")
        print(f"  Base32 String: {response['VirtualMFADevice']['Base32StringSeed']}")
        print("\n  Scan QR Code with authenticator app (Google Authenticator, Authy, etc)")
        print("  Then enable with: enable_mfa_device()")

        return response
    except Exception as e:
        print(f"✗ Error setting up MFA: {e}")
        return None


def enable_mfa_device(username, serial_number, code1, code2):
    """Enable MFA device for a user"""
    try:
        iam.enable_mfa_device(
            UserName=username,
            SerialNumber=serial_number,
            AuthenticationCode1=code1,
            AuthenticationCode2=code2
        )
        print(f"✓ MFA enabled for user: {username}")
        return True
    except Exception as e:
        print(f"✗ Error enabling MFA: {e}")
        return None


def list_mfa_devices(username):
    """List MFA devices for a user"""
    try:
        response = iam.list_mfa_devices(UserName=username)
        print(f"\n🔐 MFA Devices for {username}:")
        print("-" * 80)
        for device in response['MFADevices']:
            print(f"  Serial: {device['SerialNumber']}")
            print(f"  Enabled: {device['EnableDate']}")
        return response
    except Exception as e:
        print(f"✗ Error listing MFA devices: {e}")
        return None


# ============================================================================
# 7. STS (Security Token Service)
# ============================================================================

def get_caller_identity():
    """Get information about the caller"""
    try:
        response = sts.get_caller_identity()
        print(f"\n👤 Caller Identity")
        print("-" * 80)
        print(f"  Account ID:  {response['Account']}")
        print(f"  User ID:     {response['UserId']}")
        print(f"  ARN:         {response['Arn']}")
        return response
    except Exception as e:
        print(f"✗ Error getting caller identity: {e}")
        return None


def assume_role(role_arn, session_name, duration_seconds=3600):
    """Assume a role and get temporary credentials"""
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=duration_seconds
        )

        credentials = response['Credentials']
        print(f"\n🔐 Assumed Role: {role_arn}")
        print("-" * 80)
        print(f"  Access Key ID:       {credentials['AccessKeyId']}")
        print(f"  Secret Access Key:   {credentials['SecretAccessKey']}")
        print(f"  Session Token:       {credentials['SessionToken']}")
        print(f"  Expires:             {credentials['Expiration']}")

        return credentials
    except Exception as e:
        print(f"✗ Error assuming role: {e}")
        return None


def get_session_token(mfa_serial, mfa_token, duration_seconds=43200):
    """Get temporary session token using MFA"""
    try:
        response = sts.get_session_token(
            SerialNumber=mfa_serial,
            TokenCode=mfa_token,
            DurationSeconds=duration_seconds
        )

        credentials = response['Credentials']
        print(f"\n🔐 Session Token Generated (with MFA)")
        print("-" * 80)
        print(f"  Access Key ID:       {credentials['AccessKeyId']}")
        print(f"  Secret Access Key:   {credentials['SecretAccessKey']}")
        print(f"  Session Token:       {credentials['SessionToken']}")
        print(f"  Expires:             {credentials['Expiration']}")

        return credentials
    except Exception as e:
        print(f"✗ Error getting session token: {e}")
        return None


# ============================================================================
# 8. POLICY SIMULATION & ANALYSIS
# ============================================================================

def simulate_policy(principal_arn, actions, resources):
    """Simulate an API call to check permissions"""
    try:
        response = iam.simulate_principal_policy(
            PolicySourceArn=principal_arn,
            ActionNames=actions,
            ResourceArns=resources
        )

        print(f"\n🔍 Policy Simulation Results")
        print("-" * 80)
        for result in response['EvaluationResults']:
            decision = result['EvalDecision']  # allowed, explicitDeny, implicitDeny
            action = result['EvalActionName']

            status_icon = "✓" if decision == "allowed" else "✗"
            print(f"  {status_icon} {action:30} | {decision}")

        return response
    except Exception as e:
        print(f"✗ Error simulating policy: {e}")
        return None


def get_credential_report():
    """Generate credential report for all users"""
    try:
        # Request report generation
        iam.generate_credential_report()

        # Wait for report to be ready
        import time
        time.sleep(2)

        # Get report
        response = iam.get_credential_report()

        # Parse CSV
        import csv
        import io

        csv_data = csv.DictReader(io.StringIO(response['Content'].decode('utf-8')))

        print(f"\n📊 Credential Report")
        print("-" * 100)
        for row in csv_data:
            user = row['user']
            password_enabled = row['password_enabled']
            mfa_active = row['mfa_active']
            print(f"  {user:20} | Password: {password_enabled:5} | MFA: {mfa_active:5}")

        return response
    except Exception as e:
        print(f"✗ Error generating credential report: {e}")
        return None


# ============================================================================
# 9. INSTANCE PROFILES (for EC2)
# ============================================================================

def create_instance_profile(profile_name, role_name):
    """Create instance profile and attach role"""
    try:
        # Create instance profile
        profile_response = iam.create_instance_profile(
            InstanceProfileName=profile_name
        )

        # Add role to instance profile
        iam.add_role_to_instance_profile(
            InstanceProfileName=profile_name,
            RoleName=role_name
        )

        print(f"✓ Instance profile created: {profile_name}")
        return profile_response
    except Exception as e:
        print(f"✗ Error creating instance profile: {e}")
        return None


# ============================================================================
# 10. PERMISSIONS BOUNDARIES
# ============================================================================

def set_permissions_boundary(username, boundary_arn):
    """Set permissions boundary for a user"""
    try:
        iam.put_user_permissions_boundary(
            UserName=username,
            PermissionsBoundary=boundary_arn
        )
        print(f"✓ Permissions boundary set for user: {username}")
        return True
    except Exception as e:
        print(f"✗ Error setting permissions boundary: {e}")
        return None


def set_role_permissions_boundary(role_name, boundary_arn):
    """Set permissions boundary for a role"""
    try:
        iam.put_role_permissions_boundary(
            RoleName=role_name,
            PermissionsBoundary=boundary_arn
        )
        print(f"✓ Permissions boundary set for role: {role_name}")
        return True
    except Exception as e:
        print(f"✗ Error setting permissions boundary: {e}")
        return None


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AWS IAM Boto3 Operations Examples")
    print("=" * 80)

    # Example 1: List users
    print("\n[1] Listing IAM Users...")
    list_users()

    # Example 2: Get caller identity
    print("\n[2] Getting Caller Identity...")
    get_caller_identity()

    # Example 3: List roles
    print("\n[3] Listing IAM Roles...")
    list_roles()

    # Example 4: List policies
    print("\n[4] Listing Policies...")
    list_policies()

    print("\n✓ Examples completed!")
