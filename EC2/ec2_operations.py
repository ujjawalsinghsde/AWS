"""
AWS EC2 Operations using boto3
==============================

This module provides comprehensive examples of EC2 operations using boto3.
Covers instance management, AMIs, EBS, security groups, and more.

Prerequisites:
- pip install boto3
- AWS credentials configured (aws configure or IAM role)

Author: AWS Learning Repository
"""

import boto3
import time
import base64
from datetime import datetime, timedelta
from botocore.exceptions import ClientError


# ============================================================================
# CLIENT & RESOURCE INITIALIZATION
# ============================================================================

def get_ec2_client(region_name='us-east-1'):
    """Get EC2 client for a specific region."""
    return boto3.client('ec2', region_name=region_name)


def get_ec2_resource(region_name='us-east-1'):
    """Get EC2 resource for a specific region."""
    return boto3.resource('ec2', region_name=region_name)


# ============================================================================
# INSTANCE OPERATIONS
# ============================================================================

def launch_instance(
    image_id: str,
    instance_type: str = 't3.micro',
    key_name: str = None,
    security_group_ids: list = None,
    subnet_id: str = None,
    user_data: str = None,
    iam_instance_profile: str = None,
    tags: dict = None,
    min_count: int = 1,
    max_count: int = 1,
    region: str = 'us-east-1'
) -> dict:
    """
    Launch EC2 instance(s) with specified configuration.

    Args:
        image_id: AMI ID to use
        instance_type: EC2 instance type (default: t3.micro)
        key_name: SSH key pair name
        security_group_ids: List of security group IDs
        subnet_id: Subnet ID for VPC placement
        user_data: Bootstrap script (string)
        iam_instance_profile: IAM instance profile name
        tags: Dict of tags to apply
        min_count: Minimum number of instances
        max_count: Maximum number of instances
        region: AWS region

    Returns:
        Response containing instance details
    """
    ec2 = get_ec2_resource(region)

    # Build launch parameters
    params = {
        'ImageId': image_id,
        'InstanceType': instance_type,
        'MinCount': min_count,
        'MaxCount': max_count,
    }

    if key_name:
        params['KeyName'] = key_name

    if security_group_ids:
        params['SecurityGroupIds'] = security_group_ids

    if subnet_id:
        params['SubnetId'] = subnet_id

    if user_data:
        params['UserData'] = user_data

    if iam_instance_profile:
        params['IamInstanceProfile'] = {'Name': iam_instance_profile}

    if tags:
        tag_specs = [{
            'ResourceType': 'instance',
            'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
        }]
        params['TagSpecifications'] = tag_specs

    try:
        instances = ec2.create_instances(**params)
        instance_ids = [inst.id for inst in instances]
        print(f"Launched instances: {instance_ids}")
        return {'InstanceIds': instance_ids, 'Instances': instances}
    except ClientError as e:
        print(f"Error launching instance: {e}")
        raise


def launch_instance_with_user_data(
    image_id: str,
    instance_type: str = 't3.micro',
    key_name: str = None,
    security_group_ids: list = None,
    subnet_id: str = None,
    region: str = 'us-east-1'
) -> dict:
    """
    Launch EC2 instance with a sample user data script.
    Installs and starts nginx web server.
    """
    user_data_script = """#!/bin/bash
# Update system
yum update -y

# Install nginx
amazon-linux-extras install nginx1 -y

# Start and enable nginx
systemctl start nginx
systemctl enable nginx

# Create a simple index page
cat > /usr/share/nginx/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>EC2 Instance</title></head>
<body>
<h1>Hello from EC2!</h1>
<p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
<p>Availability Zone: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)</p>
</body>
</html>
EOF

echo "User data script completed at $(date)" >> /var/log/user-data.log
"""

    return launch_instance(
        image_id=image_id,
        instance_type=instance_type,
        key_name=key_name,
        security_group_ids=security_group_ids,
        subnet_id=subnet_id,
        user_data=user_data_script,
        tags={'Name': 'web-server', 'Environment': 'dev'},
        region=region
    )


def list_instances(
    filters: list = None,
    instance_ids: list = None,
    region: str = 'us-east-1'
) -> list:
    """
    List EC2 instances with optional filters.

    Args:
        filters: List of filter dicts [{'Name': 'tag:Name', 'Values': ['web*']}]
        instance_ids: Specific instance IDs to describe
        region: AWS region

    Returns:
        List of instance information dicts
    """
    ec2 = get_ec2_client(region)
    params = {}

    if filters:
        params['Filters'] = filters
    if instance_ids:
        params['InstanceIds'] = instance_ids

    try:
        response = ec2.describe_instances(**params)
        instances = []

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Get Name tag if exists
                name = ''
                if 'Tags' in instance:
                    name = next(
                        (t['Value'] for t in instance['Tags'] if t['Key'] == 'Name'),
                        ''
                    )

                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'Name': name,
                    'InstanceType': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'PublicIp': instance.get('PublicIpAddress', 'N/A'),
                    'PrivateIp': instance.get('PrivateIpAddress', 'N/A'),
                    'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S')
                })

        return instances
    except ClientError as e:
        print(f"Error listing instances: {e}")
        raise


def start_instances(instance_ids: list, region: str = 'us-east-1') -> dict:
    """Start stopped EC2 instances."""
    ec2 = get_ec2_client(region)
    try:
        response = ec2.start_instances(InstanceIds=instance_ids)
        print(f"Starting instances: {instance_ids}")
        return response
    except ClientError as e:
        print(f"Error starting instances: {e}")
        raise


def stop_instances(instance_ids: list, region: str = 'us-east-1') -> dict:
    """Stop running EC2 instances."""
    ec2 = get_ec2_client(region)
    try:
        response = ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopping instances: {instance_ids}")
        return response
    except ClientError as e:
        print(f"Error stopping instances: {e}")
        raise


def terminate_instances(instance_ids: list, region: str = 'us-east-1') -> dict:
    """Terminate EC2 instances (permanent deletion)."""
    ec2 = get_ec2_client(region)
    try:
        response = ec2.terminate_instances(InstanceIds=instance_ids)
        print(f"Terminating instances: {instance_ids}")
        return response
    except ClientError as e:
        print(f"Error terminating instances: {e}")
        raise


def reboot_instances(instance_ids: list, region: str = 'us-east-1') -> dict:
    """Reboot EC2 instances."""
    ec2 = get_ec2_client(region)
    try:
        response = ec2.reboot_instances(InstanceIds=instance_ids)
        print(f"Rebooting instances: {instance_ids}")
        return response
    except ClientError as e:
        print(f"Error rebooting instances: {e}")
        raise


def wait_for_instance_state(
    instance_id: str,
    target_state: str = 'running',
    timeout: int = 300,
    region: str = 'us-east-1'
) -> bool:
    """
    Wait for instance to reach target state.

    Args:
        instance_id: Instance ID to monitor
        target_state: Target state ('running', 'stopped', 'terminated')
        timeout: Maximum wait time in seconds
        region: AWS region

    Returns:
        True if state reached, False if timeout
    """
    ec2 = get_ec2_client(region)
    waiter_map = {
        'running': 'instance_running',
        'stopped': 'instance_stopped',
        'terminated': 'instance_terminated'
    }

    waiter_name = waiter_map.get(target_state)
    if not waiter_name:
        raise ValueError(f"Unsupported target state: {target_state}")

    try:
        waiter = ec2.get_waiter(waiter_name)
        waiter.wait(
            InstanceIds=[instance_id],
            WaiterConfig={'Delay': 15, 'MaxAttempts': timeout // 15}
        )
        print(f"Instance {instance_id} reached state: {target_state}")
        return True
    except Exception as e:
        print(f"Timeout waiting for instance state: {e}")
        return False


# ============================================================================
# AMI OPERATIONS
# ============================================================================

def create_ami(
    instance_id: str,
    name: str,
    description: str = '',
    no_reboot: bool = True,
    tags: dict = None,
    region: str = 'us-east-1'
) -> str:
    """
    Create AMI from an instance.

    Args:
        instance_id: Source instance ID
        name: AMI name
        description: AMI description
        no_reboot: If True, don't reboot instance during AMI creation
        tags: Dict of tags to apply
        region: AWS region

    Returns:
        AMI ID
    """
    ec2 = get_ec2_client(region)

    params = {
        'InstanceId': instance_id,
        'Name': name,
        'Description': description,
        'NoReboot': no_reboot
    }

    if tags:
        params['TagSpecifications'] = [{
            'ResourceType': 'image',
            'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
        }]

    try:
        response = ec2.create_image(**params)
        ami_id = response['ImageId']
        print(f"Creating AMI: {ami_id} from instance {instance_id}")
        return ami_id
    except ClientError as e:
        print(f"Error creating AMI: {e}")
        raise


def list_amis(
    owners: list = None,
    filters: list = None,
    region: str = 'us-east-1'
) -> list:
    """
    List AMIs with optional filters.

    Args:
        owners: List of owner IDs ('self', account IDs, 'amazon')
        filters: List of filter dicts
        region: AWS region

    Returns:
        List of AMI information dicts
    """
    ec2 = get_ec2_client(region)
    params = {}

    if owners:
        params['Owners'] = owners
    if filters:
        params['Filters'] = filters

    try:
        response = ec2.describe_images(**params)
        amis = []

        for image in response['Images']:
            amis.append({
                'ImageId': image['ImageId'],
                'Name': image.get('Name', 'N/A'),
                'State': image['State'],
                'CreationDate': image['CreationDate'],
                'Architecture': image['Architecture'],
                'Description': image.get('Description', '')
            })

        # Sort by creation date (newest first)
        amis.sort(key=lambda x: x['CreationDate'], reverse=True)
        return amis
    except ClientError as e:
        print(f"Error listing AMIs: {e}")
        raise


def copy_ami(
    source_ami_id: str,
    source_region: str,
    name: str,
    description: str = '',
    encrypted: bool = True,
    dest_region: str = 'us-east-1'
) -> str:
    """
    Copy AMI to another region.

    Args:
        source_ami_id: Source AMI ID
        source_region: Source region
        name: Name for new AMI
        description: Description for new AMI
        encrypted: Whether to encrypt the new AMI
        dest_region: Destination region

    Returns:
        New AMI ID in destination region
    """
    ec2 = get_ec2_client(dest_region)

    try:
        response = ec2.copy_image(
            SourceImageId=source_ami_id,
            SourceRegion=source_region,
            Name=name,
            Description=description,
            Encrypted=encrypted
        )
        new_ami_id = response['ImageId']
        print(f"Copying AMI {source_ami_id} from {source_region} to {dest_region}")
        print(f"New AMI ID: {new_ami_id}")
        return new_ami_id
    except ClientError as e:
        print(f"Error copying AMI: {e}")
        raise


def delete_ami(ami_id: str, region: str = 'us-east-1') -> None:
    """
    Delete (deregister) an AMI and its associated snapshots.

    Args:
        ami_id: AMI ID to delete
        region: AWS region
    """
    ec2 = get_ec2_client(region)

    try:
        # Get snapshot IDs associated with AMI
        response = ec2.describe_images(ImageIds=[ami_id])
        snapshot_ids = []

        if response['Images']:
            for mapping in response['Images'][0].get('BlockDeviceMappings', []):
                if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                    snapshot_ids.append(mapping['Ebs']['SnapshotId'])

        # Deregister AMI
        ec2.deregister_image(ImageId=ami_id)
        print(f"Deregistered AMI: {ami_id}")

        # Delete associated snapshots
        for snap_id in snapshot_ids:
            ec2.delete_snapshot(SnapshotId=snap_id)
            print(f"Deleted snapshot: {snap_id}")

    except ClientError as e:
        print(f"Error deleting AMI: {e}")
        raise


# ============================================================================
# SECURITY GROUP OPERATIONS
# ============================================================================

def create_security_group(
    name: str,
    description: str,
    vpc_id: str,
    region: str = 'us-east-1'
) -> str:
    """
    Create a security group.

    Args:
        name: Security group name
        description: Security group description
        vpc_id: VPC ID
        region: AWS region

    Returns:
        Security group ID
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.create_security_group(
            GroupName=name,
            Description=description,
            VpcId=vpc_id
        )
        sg_id = response['GroupId']
        print(f"Created security group: {sg_id}")
        return sg_id
    except ClientError as e:
        print(f"Error creating security group: {e}")
        raise


def add_security_group_rule(
    security_group_id: str,
    protocol: str,
    port: int,
    cidr: str = None,
    source_security_group_id: str = None,
    description: str = '',
    direction: str = 'ingress',
    region: str = 'us-east-1'
) -> None:
    """
    Add inbound or outbound rule to security group.

    Args:
        security_group_id: Security group ID
        protocol: Protocol (tcp, udp, icmp, -1 for all)
        port: Port number (use -1 for all ports with protocol -1)
        cidr: CIDR block (e.g., '0.0.0.0/0')
        source_security_group_id: Source SG (alternative to CIDR)
        description: Rule description
        direction: 'ingress' or 'egress'
        region: AWS region
    """
    ec2 = get_ec2_client(region)

    # Build IP permission
    ip_permission = {
        'IpProtocol': protocol,
    }

    if port != -1:
        ip_permission['FromPort'] = port
        ip_permission['ToPort'] = port

    if cidr:
        ip_permission['IpRanges'] = [{'CidrIp': cidr, 'Description': description}]
    elif source_security_group_id:
        ip_permission['UserIdGroupPairs'] = [{
            'GroupId': source_security_group_id,
            'Description': description
        }]

    try:
        if direction == 'ingress':
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            print(f"Added ingress rule to {security_group_id}")
        else:
            ec2.authorize_security_group_egress(
                GroupId=security_group_id,
                IpPermissions=[ip_permission]
            )
            print(f"Added egress rule to {security_group_id}")
    except ClientError as e:
        if 'InvalidPermission.Duplicate' in str(e):
            print("Rule already exists")
        else:
            print(f"Error adding security group rule: {e}")
            raise


def create_web_server_security_group(
    name: str,
    vpc_id: str,
    ssh_cidr: str = None,
    region: str = 'us-east-1'
) -> str:
    """
    Create a security group with typical web server rules.
    Opens HTTP (80), HTTPS (443), and optionally SSH (22).

    Args:
        name: Security group name
        vpc_id: VPC ID
        ssh_cidr: CIDR for SSH access (leave None to skip SSH rule)
        region: AWS region

    Returns:
        Security group ID
    """
    sg_id = create_security_group(
        name=name,
        description=f'Web server security group - {name}',
        vpc_id=vpc_id,
        region=region
    )

    # Allow HTTP from anywhere
    add_security_group_rule(
        security_group_id=sg_id,
        protocol='tcp',
        port=80,
        cidr='0.0.0.0/0',
        description='HTTP from anywhere',
        region=region
    )

    # Allow HTTPS from anywhere
    add_security_group_rule(
        security_group_id=sg_id,
        protocol='tcp',
        port=443,
        cidr='0.0.0.0/0',
        description='HTTPS from anywhere',
        region=region
    )

    # Optionally allow SSH from specific CIDR
    if ssh_cidr:
        add_security_group_rule(
            security_group_id=sg_id,
            protocol='tcp',
            port=22,
            cidr=ssh_cidr,
            description='SSH access',
            region=region
        )

    return sg_id


def delete_security_group(security_group_id: str, region: str = 'us-east-1') -> None:
    """Delete a security group."""
    ec2 = get_ec2_client(region)
    try:
        ec2.delete_security_group(GroupId=security_group_id)
        print(f"Deleted security group: {security_group_id}")
    except ClientError as e:
        print(f"Error deleting security group: {e}")
        raise


# ============================================================================
# KEY PAIR OPERATIONS
# ============================================================================

def create_key_pair(name: str, key_type: str = 'ed25519', region: str = 'us-east-1') -> str:
    """
    Create a new key pair and return private key.

    Args:
        name: Key pair name
        key_type: Key type ('rsa' or 'ed25519')
        region: AWS region

    Returns:
        Private key material (save this to a .pem file!)
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.create_key_pair(
            KeyName=name,
            KeyType=key_type
        )
        print(f"Created key pair: {name}")
        print("IMPORTANT: Save the private key material below to a .pem file!")
        return response['KeyMaterial']
    except ClientError as e:
        print(f"Error creating key pair: {e}")
        raise


def import_key_pair(name: str, public_key_path: str, region: str = 'us-east-1') -> str:
    """
    Import an existing public key as a key pair.

    Args:
        name: Key pair name
        public_key_path: Path to public key file
        region: AWS region

    Returns:
        Key pair fingerprint
    """
    ec2 = get_ec2_client(region)

    try:
        with open(public_key_path, 'rb') as f:
            public_key = f.read()

        response = ec2.import_key_pair(
            KeyName=name,
            PublicKeyMaterial=public_key
        )
        print(f"Imported key pair: {name}")
        return response['KeyFingerprint']
    except ClientError as e:
        print(f"Error importing key pair: {e}")
        raise


def list_key_pairs(region: str = 'us-east-1') -> list:
    """List all key pairs."""
    ec2 = get_ec2_client(region)
    try:
        response = ec2.describe_key_pairs()
        return [{
            'KeyName': kp['KeyName'],
            'KeyType': kp.get('KeyType', 'rsa'),
            'Fingerprint': kp['KeyFingerprint']
        } for kp in response['KeyPairs']]
    except ClientError as e:
        print(f"Error listing key pairs: {e}")
        raise


def delete_key_pair(name: str, region: str = 'us-east-1') -> None:
    """Delete a key pair."""
    ec2 = get_ec2_client(region)
    try:
        ec2.delete_key_pair(KeyName=name)
        print(f"Deleted key pair: {name}")
    except ClientError as e:
        print(f"Error deleting key pair: {e}")
        raise


# ============================================================================
# EBS VOLUME OPERATIONS
# ============================================================================

def create_ebs_volume(
    size_gb: int,
    availability_zone: str,
    volume_type: str = 'gp3',
    iops: int = None,
    throughput: int = None,
    encrypted: bool = True,
    kms_key_id: str = None,
    tags: dict = None,
    region: str = 'us-east-1'
) -> str:
    """
    Create an EBS volume.

    Args:
        size_gb: Volume size in GB
        availability_zone: AZ for the volume
        volume_type: Volume type (gp3, gp2, io2, io1, st1, sc1)
        iops: Provisioned IOPS (for io1, io2, gp3)
        throughput: Throughput in MB/s (for gp3)
        encrypted: Whether to encrypt the volume
        kms_key_id: KMS key for encryption
        tags: Dict of tags
        region: AWS region

    Returns:
        Volume ID
    """
    ec2 = get_ec2_client(region)

    params = {
        'Size': size_gb,
        'AvailabilityZone': availability_zone,
        'VolumeType': volume_type,
        'Encrypted': encrypted
    }

    if iops and volume_type in ['io1', 'io2', 'gp3']:
        params['Iops'] = iops

    if throughput and volume_type == 'gp3':
        params['Throughput'] = throughput

    if kms_key_id:
        params['KmsKeyId'] = kms_key_id

    if tags:
        params['TagSpecifications'] = [{
            'ResourceType': 'volume',
            'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
        }]

    try:
        response = ec2.create_volume(**params)
        volume_id = response['VolumeId']
        print(f"Created volume: {volume_id}")
        return volume_id
    except ClientError as e:
        print(f"Error creating volume: {e}")
        raise


def attach_volume(
    volume_id: str,
    instance_id: str,
    device: str = '/dev/sdf',
    region: str = 'us-east-1'
) -> None:
    """
    Attach an EBS volume to an instance.

    Args:
        volume_id: Volume ID
        instance_id: Instance ID
        device: Device name (e.g., /dev/sdf)
        region: AWS region
    """
    ec2 = get_ec2_client(region)

    try:
        ec2.attach_volume(
            VolumeId=volume_id,
            InstanceId=instance_id,
            Device=device
        )
        print(f"Attaching volume {volume_id} to {instance_id} as {device}")
    except ClientError as e:
        print(f"Error attaching volume: {e}")
        raise


def detach_volume(volume_id: str, force: bool = False, region: str = 'us-east-1') -> None:
    """Detach an EBS volume from an instance."""
    ec2 = get_ec2_client(region)

    try:
        ec2.detach_volume(VolumeId=volume_id, Force=force)
        print(f"Detaching volume: {volume_id}")
    except ClientError as e:
        print(f"Error detaching volume: {e}")
        raise


def create_snapshot(
    volume_id: str,
    description: str = '',
    tags: dict = None,
    region: str = 'us-east-1'
) -> str:
    """
    Create a snapshot of an EBS volume.

    Args:
        volume_id: Volume ID to snapshot
        description: Snapshot description
        tags: Dict of tags
        region: AWS region

    Returns:
        Snapshot ID
    """
    ec2 = get_ec2_client(region)

    params = {
        'VolumeId': volume_id,
        'Description': description
    }

    if tags:
        params['TagSpecifications'] = [{
            'ResourceType': 'snapshot',
            'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
        }]

    try:
        response = ec2.create_snapshot(**params)
        snapshot_id = response['SnapshotId']
        print(f"Creating snapshot: {snapshot_id}")
        return snapshot_id
    except ClientError as e:
        print(f"Error creating snapshot: {e}")
        raise


def delete_volume(volume_id: str, region: str = 'us-east-1') -> None:
    """Delete an EBS volume."""
    ec2 = get_ec2_client(region)
    try:
        ec2.delete_volume(VolumeId=volume_id)
        print(f"Deleted volume: {volume_id}")
    except ClientError as e:
        print(f"Error deleting volume: {e}")
        raise


# ============================================================================
# ELASTIC IP OPERATIONS
# ============================================================================

def allocate_elastic_ip(region: str = 'us-east-1') -> dict:
    """
    Allocate a new Elastic IP.

    Returns:
        Dict with AllocationId and PublicIp
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.allocate_address(Domain='vpc')
        print(f"Allocated Elastic IP: {response['PublicIp']}")
        return {
            'AllocationId': response['AllocationId'],
            'PublicIp': response['PublicIp']
        }
    except ClientError as e:
        print(f"Error allocating Elastic IP: {e}")
        raise


def associate_elastic_ip(
    allocation_id: str,
    instance_id: str = None,
    network_interface_id: str = None,
    region: str = 'us-east-1'
) -> str:
    """
    Associate Elastic IP with an instance or network interface.

    Args:
        allocation_id: Elastic IP allocation ID
        instance_id: Instance ID (use this OR network_interface_id)
        network_interface_id: ENI ID
        region: AWS region

    Returns:
        Association ID
    """
    ec2 = get_ec2_client(region)

    params = {'AllocationId': allocation_id}
    if instance_id:
        params['InstanceId'] = instance_id
    elif network_interface_id:
        params['NetworkInterfaceId'] = network_interface_id

    try:
        response = ec2.associate_address(**params)
        print(f"Associated Elastic IP, association ID: {response['AssociationId']}")
        return response['AssociationId']
    except ClientError as e:
        print(f"Error associating Elastic IP: {e}")
        raise


def release_elastic_ip(allocation_id: str, region: str = 'us-east-1') -> None:
    """Release (delete) an Elastic IP."""
    ec2 = get_ec2_client(region)
    try:
        ec2.release_address(AllocationId=allocation_id)
        print(f"Released Elastic IP: {allocation_id}")
    except ClientError as e:
        print(f"Error releasing Elastic IP: {e}")
        raise


# ============================================================================
# SPOT INSTANCE OPERATIONS
# ============================================================================

def request_spot_instance(
    image_id: str,
    instance_type: str,
    max_price: str,
    key_name: str = None,
    security_group_ids: list = None,
    subnet_id: str = None,
    region: str = 'us-east-1'
) -> dict:
    """
    Request a Spot Instance.

    Args:
        image_id: AMI ID
        instance_type: Instance type
        max_price: Maximum hourly price (e.g., '0.05')
        key_name: SSH key pair name
        security_group_ids: List of security group IDs
        subnet_id: Subnet ID
        region: AWS region

    Returns:
        Spot request details
    """
    ec2 = get_ec2_client(region)

    launch_spec = {
        'ImageId': image_id,
        'InstanceType': instance_type,
    }

    if key_name:
        launch_spec['KeyName'] = key_name
    if security_group_ids:
        launch_spec['SecurityGroupIds'] = security_group_ids
    if subnet_id:
        launch_spec['SubnetId'] = subnet_id

    try:
        response = ec2.request_spot_instances(
            SpotPrice=max_price,
            InstanceCount=1,
            Type='one-time',
            LaunchSpecification=launch_spec
        )
        request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        print(f"Spot request created: {request_id}")
        return response['SpotInstanceRequests'][0]
    except ClientError as e:
        print(f"Error requesting Spot Instance: {e}")
        raise


def get_spot_price_history(
    instance_types: list,
    product_descriptions: list = None,
    hours_back: int = 24,
    region: str = 'us-east-1'
) -> list:
    """
    Get Spot price history.

    Args:
        instance_types: List of instance types
        product_descriptions: List of product descriptions (e.g., ['Linux/UNIX'])
        hours_back: How many hours back to look
        region: AWS region

    Returns:
        List of price history entries
    """
    ec2 = get_ec2_client(region)

    start_time = datetime.utcnow() - timedelta(hours=hours_back)

    params = {
        'InstanceTypes': instance_types,
        'StartTime': start_time,
    }

    if product_descriptions:
        params['ProductDescriptions'] = product_descriptions

    try:
        response = ec2.describe_spot_price_history(**params)
        prices = []
        for item in response['SpotPriceHistory']:
            prices.append({
                'InstanceType': item['InstanceType'],
                'AvailabilityZone': item['AvailabilityZone'],
                'SpotPrice': item['SpotPrice'],
                'Timestamp': item['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            })
        return prices
    except ClientError as e:
        print(f"Error getting Spot price history: {e}")
        raise


# ============================================================================
# INSTANCE METADATA (from inside EC2)
# ============================================================================

def get_instance_metadata(path: str = '', use_imdsv2: bool = True) -> str:
    """
    Get instance metadata from within an EC2 instance.
    Must be run from inside an EC2 instance.

    Args:
        path: Metadata path (e.g., 'instance-id', 'public-ipv4')
        use_imdsv2: Use IMDSv2 with session token

    Returns:
        Metadata value
    """
    import urllib.request

    base_url = 'http://169.254.169.254/latest/meta-data/'

    try:
        if use_imdsv2:
            # Get session token
            token_request = urllib.request.Request(
                'http://169.254.169.254/latest/api/token',
                method='PUT',
                headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
            )
            with urllib.request.urlopen(token_request, timeout=2) as response:
                token = response.read().decode('utf-8')

            # Get metadata with token
            metadata_request = urllib.request.Request(
                base_url + path,
                headers={'X-aws-ec2-metadata-token': token}
            )
            with urllib.request.urlopen(metadata_request, timeout=2) as response:
                return response.read().decode('utf-8')
        else:
            # IMDSv1 (not recommended)
            with urllib.request.urlopen(base_url + path, timeout=2) as response:
                return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error getting instance metadata: {e}")
        print("Note: This function must be run from inside an EC2 instance")
        raise


# ============================================================================
# TAGGING OPERATIONS
# ============================================================================

def add_tags(resource_ids: list, tags: dict, region: str = 'us-east-1') -> None:
    """
    Add tags to EC2 resources.

    Args:
        resource_ids: List of resource IDs (instances, volumes, etc.)
        tags: Dict of tags to add
        region: AWS region
    """
    ec2 = get_ec2_client(region)

    tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]

    try:
        ec2.create_tags(Resources=resource_ids, Tags=tag_list)
        print(f"Added tags to {resource_ids}")
    except ClientError as e:
        print(f"Error adding tags: {e}")
        raise


# ============================================================================
# MONITORING & STATUS
# ============================================================================

def get_instance_status(instance_ids: list, region: str = 'us-east-1') -> list:
    """
    Get detailed status of instances including system and instance status checks.

    Args:
        instance_ids: List of instance IDs
        region: AWS region

    Returns:
        List of instance status info
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.describe_instance_status(
            InstanceIds=instance_ids,
            IncludeAllInstances=True
        )

        statuses = []
        for status in response['InstanceStatuses']:
            statuses.append({
                'InstanceId': status['InstanceId'],
                'State': status['InstanceState']['Name'],
                'SystemStatus': status['SystemStatus']['Status'],
                'InstanceStatus': status['InstanceStatus']['Status'],
                'AvailabilityZone': status['AvailabilityZone']
            })

        return statuses
    except ClientError as e:
        print(f"Error getting instance status: {e}")
        raise


def get_console_output(instance_id: str, region: str = 'us-east-1') -> str:
    """
    Get system console output (boot logs) from an instance.

    Args:
        instance_id: Instance ID
        region: AWS region

    Returns:
        Console output string
    """
    ec2 = get_ec2_client(region)

    try:
        response = ec2.get_console_output(InstanceId=instance_id)
        output = response.get('Output', '')
        if output:
            # Output is base64 encoded
            return base64.b64decode(output).decode('utf-8', errors='replace')
        return "No console output available"
    except ClientError as e:
        print(f"Error getting console output: {e}")
        raise


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Example: List all running instances
    print("=== Running Instances ===")
    running_instances = list_instances(
        filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    for inst in running_instances:
        print(f"  {inst['InstanceId']} - {inst['Name']} - {inst['InstanceType']} - {inst['PublicIp']}")

    # Example: List your custom AMIs
    print("\n=== Custom AMIs ===")
    my_amis = list_amis(owners=['self'])
    for ami in my_amis[:5]:  # Show first 5
        print(f"  {ami['ImageId']} - {ami['Name']} - {ami['State']}")

    # Example: List key pairs
    print("\n=== Key Pairs ===")
    key_pairs = list_key_pairs()
    for kp in key_pairs:
        print(f"  {kp['KeyName']} ({kp['KeyType']})")

    # Example: Get Spot prices
    print("\n=== Current Spot Prices (t3.micro) ===")
    spot_prices = get_spot_price_history(
        instance_types=['t3.micro'],
        product_descriptions=['Linux/UNIX'],
        hours_back=1
    )
    for price in spot_prices[:5]:  # Show first 5
        print(f"  {price['AvailabilityZone']}: ${price['SpotPrice']}")

    print("\n=== Example: Launch Instance (commented out) ===")
    print("""
    # Uncomment to launch an instance:
    # instance = launch_instance(
    #     image_id='ami-0123456789abcdef0',  # Replace with valid AMI
    #     instance_type='t3.micro',
    #     key_name='my-key-pair',
    #     security_group_ids=['sg-0123456789abcdef0'],
    #     subnet_id='subnet-0123456789abcdef0',
    #     tags={'Name': 'my-test-instance', 'Environment': 'dev'}
    # )
    """)
