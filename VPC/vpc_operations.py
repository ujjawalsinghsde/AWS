"""
AWS VPC (Virtual Private Cloud) - Boto3 Operations
Document: VPC/vpc_operations.py

This module provides practical boto3 examples for common VPC operations.
"""

import boto3
import json
from datetime import datetime

# Initialize EC2 client
ec2 = boto3.client('ec2', region_name='us-east-1')


# ============================================================================
# 1. VPC OPERATIONS
# ============================================================================

def create_vpc(cidr_block, vpc_name='my-vpc'):
    """Create a new VPC"""
    try:
        response = ec2.create_vpc(
            CidrBlock=cidr_block,
            TagSpecifications=[{
                'ResourceType': 'vpc',
                'Tags': [
                    {'Key': 'Name', 'Value': vpc_name},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            }]
        )

        vpc_id = response['Vpc']['VpcId']
        print(f"✓ VPC created: {vpc_id}")
        print(f"  CIDR: {cidr_block}")

        # Enable DNS
        ec2.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsHostnames={'Value': True}
        )
        ec2.modify_vpc_attribute(
            VpcId=vpc_id,
            EnableDnsSupport={'Value': True}
        )

        print(f"  DNS enabled")
        return response
    except Exception as e:
        print(f"✗ Error creating VPC: {e}")
        return None


def list_vpcs():
    """List all VPCs"""
    try:
        response = ec2.describe_vpcs()
        print(f"\n📡 VPCs ({len(response['Vpcs'])} total):")
        print("-" * 80)
        for vpc in response['Vpcs']:
            is_default = "DEFAULT" if vpc['IsDefault'] else ""
            print(f"  {vpc['VpcId']:15} | {vpc['CidrBlock']:15} | {is_default}")
        return response
    except Exception as e:
        print(f"✗ Error listing VPCs: {e}")
        return None


def describe_vpc(vpc_id):
    """Get detailed information about a VPC"""
    try:
        response = ec2.describe_vpcs(VpcIds=[vpc_id])
        vpc = response['Vpcs'][0]

        print(f"\n📡 VPC Details: {vpc_id}")
        print("-" * 80)
        print(f"  CIDR Block:         {vpc['CidrBlock']}")
        print(f"  State:              {vpc['State']}")
        print(f"  Is Default:         {vpc['IsDefault']}")
        print(f"  Owner ID:           {vpc['OwnerId']}")
        print(f"  Tags:               {vpc.get('Tags', [])}")

        return vpc
    except Exception as e:
        print(f"✗ Error describing VPC: {e}")
        return None


def delete_vpc(vpc_id):
    """Delete a VPC (all resources must be removed first)"""
    try:
        ec2.delete_vpc(VpcId=vpc_id)
        print(f"✓ VPC deleted: {vpc_id}")
        return True
    except Exception as e:
        print(f"✗ Error deleting VPC: {e}")
        return None


# ============================================================================
# 2. SUBNET OPERATIONS
# ============================================================================

def create_subnet(vpc_id, cidr_block, availability_zone, subnet_name='subnet'):
    """Create a subnet"""
    try:
        response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr_block,
            AvailabilityZone=availability_zone,
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': [{'Key': 'Name', 'Value': subnet_name}]
            }]
        )

        subnet_id = response['Subnet']['SubnetId']
        print(f"✓ Subnet created: {subnet_id}")
        print(f"  CIDR: {cidr_block}")
        print(f"  AZ: {availability_zone}")
        return response
    except Exception as e:
        print(f"✗ Error creating subnet: {e}")
        return None


def list_subnets(vpc_id=None):
    """List subnets (optionally filtered by VPC)"""
    try:
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        response = ec2.describe_subnets(Filters=filters)

        print(f"\n🌐 Subnets ({len(response['Subnets'])} total):")
        print("-" * 100)
        for subnet in response['Subnets']:
            print(f"  {subnet['SubnetId']:20} | {subnet['CidrBlock']:18} | {subnet['AvailabilityZone']:10}")
        return response
    except Exception as e:
        print(f"✗ Error listing subnets: {e}")
        return None


def enable_public_ip_on_launch(subnet_id):
    """Enable auto-assign public IP on launch for a subnet"""
    try:
        ec2.modify_subnet_attribute(
            SubnetId=subnet_id,
            MapPublicIpOnLaunch={'Value': True}
        )
        print(f"✓ Public IP auto-assign enabled for: {subnet_id}")
        return True
    except Exception as e:
        print(f"✗ Error enabling public IP: {e}")
        return None


# ============================================================================
# 3. INTERNET GATEWAY OPERATIONS
# ============================================================================

def create_internet_gateway(igw_name='igw'):
    """Create an Internet Gateway"""
    try:
        response = ec2.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': [{'Key': 'Name', 'Value': igw_name}]
            }]
        )

        igw_id = response['InternetGateway']['InternetGatewayId']
        print(f"✓ Internet Gateway created: {igw_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating IGW: {e}")
        return None


def attach_internet_gateway(igw_id, vpc_id):
    """Attach Internet Gateway to VPC"""
    try:
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        print(f"✓ Internet Gateway attached to VPC: {vpc_id}")
        return True
    except Exception as e:
        print(f"✗ Error attaching IGW: {e}")
        return None


def list_internet_gateways():
    """List all Internet Gateways"""
    try:
        response = ec2.describe_internet_gateways()
        print(f"\n🌐 Internet Gateways ({len(response['InternetGateways'])} total):")
        print("-" * 80)
        for igw in response['InternetGateways']:
            attachments = igw['Attachments']
            vpc_str = attachments[0]['VpcId'] if attachments else 'Not attached'
            print(f"  {igw['InternetGatewayId']:20} | VPC: {vpc_str:15}")
        return response
    except Exception as e:
        print(f"✗ Error listing IGWs: {e}")
        return None


# ============================================================================
# 4. ROUTE TABLE OPERATIONS
# ============================================================================

def create_route_table(vpc_id, rt_name='route-table'):
    """Create a route table"""
    try:
        response = ec2.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags': [{'Key': 'Name', 'Value': rt_name}]
            }]
        )

        rt_id = response['RouteTable']['RouteTableId']
        print(f"✓ Route Table created: {rt_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating route table: {e}")
        return None


def add_route(route_table_id, destination_cidr, gateway_id=None, nat_gateway_id=None, instance_id=None):
    """Add a route to a route table"""
    try:
        params = {
            'RouteTableId': route_table_id,
            'DestinationCidrBlock': destination_cidr
        }

        if gateway_id:
            params['GatewayId'] = gateway_id
        elif nat_gateway_id:
            params['NatGatewayId'] = nat_gateway_id
        elif instance_id:
            params['InstanceId'] = instance_id

        ec2.create_route(**params)
        target = gateway_id or nat_gateway_id or instance_id or 'local'
        print(f"✓ Route added: {destination_cidr} -> {target}")
        return True
    except Exception as e:
        print(f"✗ Error adding route: {e}")
        return None


def associate_route_table(route_table_id, subnet_id):
    """Associate route table with subnet"""
    try:
        response = ec2.associate_route_table(
            RouteTableId=route_table_id,
            SubnetId=subnet_id
        )
        print(f"✓ Route table associated with subnet: {subnet_id}")
        return response
    except Exception as e:
        print(f"✗ Error associating route table: {e}")
        return None


def list_route_tables(vpc_id=None):
    """List route tables"""
    try:
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        response = ec2.describe_route_tables(Filters=filters)

        print(f"\n📋 Route Tables ({len(response['RouteTables'])} total):")
        print("-" * 100)
        for rt in response['RouteTables']:
            print(f"  {rt['RouteTableId']:20} | VPC: {rt['VpcId']:15}")
            for route in rt['Routes']:
                dest = route.get('DestinationCidrBlock', route.get('DestinationIpv6CidrBlock', 'N/A'))
                target = route.get('GatewayId') or route.get('NatGatewayId') or route.get('InstanceId') or 'local'
                state = route.get('State', 'active')
                print(f"    -> {dest:20} | Target: {target:20} | State: {state}")

        return response
    except Exception as e:
        print(f"✗ Error listing route tables: {e}")
        return None


# ============================================================================
# 5. SECURITY GROUP OPERATIONS
# ============================================================================

def create_security_group(vpc_id, group_name, description):
    """Create a security group"""
    try:
        response = ec2.create_security_group(
            GroupName=group_name,
            Description=description,
            VpcId=vpc_id,
            TagSpecifications=[{
                'ResourceType': 'security-group',
                'Tags': [{'Key': 'Name', 'Value': group_name}]
            }]
        )

        sg_id = response['GroupId']
        print(f"✓ Security Group created: {sg_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating security group: {e}")
        return None


def add_security_group_ingress(sg_id, protocol, from_port, to_port, cidr_ip=None, source_sg_id=None):
    """Add ingress rule to security group"""
    try:
        ip_permissions = [{
            'IpProtocol': protocol,
            'FromPort': from_port,
            'ToPort': to_port
        }]

        if cidr_ip:
            ip_permissions[0]['IpRanges'] = [{'CidrIp': cidr_ip}]
        elif source_sg_id:
            ip_permissions[0]['UserIdGroupPairs'] = [{'GroupId': source_sg_id}]

        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=ip_permissions
        )

        source = cidr_ip or f"SG: {source_sg_id}"
        print(f"✓ Ingress rule added: {protocol} {from_port}-{to_port} from {source}")
        return True
    except Exception as e:
        print(f"✗ Error adding ingress rule: {e}")
        return None


def add_security_group_egress(sg_id, protocol, from_port, to_port, cidr_ip='0.0.0.0/0'):
    """Add egress rule to security group"""
    try:
        ec2.authorize_security_group_egress(
            GroupId=sg_id,
            IpPermissions=[{
                'IpProtocol': protocol,
                'FromPort': from_port,
                'ToPort': to_port,
                'IpRanges': [{'CidrIp': cidr_ip}]
            }]
        )

        print(f"✓ Egress rule added: {protocol} {from_port}-{to_port} to {cidr_ip}")
        return True
    except Exception as e:
        print(f"✗ Error adding egress rule: {e}")
        return None


def list_security_groups(vpc_id=None):
    """List security groups"""
    try:
        filters = [{'Name': 'vpc-id', 'Values': [vpc_id]}] if vpc_id else []
        response = ec2.describe_security_groups(Filters=filters)

        print(f"\n🔐 Security Groups ({len(response['SecurityGroups'])} total):")
        print("-" * 100)
        for sg in response['SecurityGroups']:
            print(f"  {sg['GroupId']:20} | {sg['GroupName']:30} | VPC: {sg['VpcId']}")

        return response
    except Exception as e:
        print(f"✗ Error listing security groups: {e}")
        return None


def describe_security_group(sg_id):
    """Get detailed information about a security group"""
    try:
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response['SecurityGroups'][0]

        print(f"\n🔐 Security Group: {sg_id}")
        print("-" * 80)
        print(f"  Name: {sg['GroupName']}")
        print(f"  VPC: {sg['VpcId']}")

        print(f"\n  Ingress Rules:")
        if sg['IpPermissions']:
            for rule in sg['IpPermissions']:
                proto = rule.get('IpProtocol', 'N/A')
                from_port = rule.get('FromPort', 'All')
                to_port = rule.get('ToPort', 'All')
                cidr = rule.get('IpRanges', [])
                source_sg = rule.get('UserIdGroupPairs', [])

                print(f"    {proto:6} {from_port}-{to_port}")
                for ip_range in cidr:
                    print(f"      From: {ip_range.get('CidrIp')}")
                for pair in source_sg:
                    print(f"      From SG: {pair.get('GroupId')}")
        else:
            print("    (No ingress rules)")

        print(f"\n  Egress Rules:")
        for rule in sg.get('IpPermissionsEgress', []):
            proto = rule.get('IpProtocol', 'N/A')
            from_port = rule.get('FromPort', 'All')
            to_port = rule.get('ToPort', 'All')
            cidr = rule.get('IpRanges', [{'CidrIp': 'N/A'}])

            print(f"    {proto:6} {from_port}-{to_port}")
            for ip_range in cidr:
                print(f"      To: {ip_range.get('CidrIp')}")

        return sg
    except Exception as e:
        print(f"✗ Error describing security group: {e}")
        return None


# ============================================================================
# 6. NETWORK ACL OPERATIONS
# ============================================================================

def create_network_acl(vpc_id, nacl_name='nacl'):
    """Create a Network ACL"""
    try:
        response = ec2.create_network_acl(
            VpcId=vpc_id,
            TagSpecifications=[{
                'ResourceType': 'network-acl',
                'Tags': [{'Key': 'Name', 'Value': nacl_name}]
            }]
        )

        nacl_id = response['NetworkAcl']['NetworkAclId']
        print(f"✓ Network ACL created: {nacl_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating NACL: {e}")
        return None


def add_network_acl_entry(nacl_id, rule_number, protocol, from_port, to_port, cidr, allow=True, egress=False):
    """Add rule to Network ACL"""
    try:
        ec2.create_network_acl_entry(
            NetworkAclId=nacl_id,
            RuleNumber=rule_number,
            Protocol=protocol,
            RuleAction='allow' if allow else 'deny',
            CidrBlock=cidr,
            PortRange={'FromPort': from_port, 'ToPort': to_port},
            Egress=egress
        )

        direction = "Egress" if egress else "Ingress"
        action = "Allow" if allow else "Deny"
        print(f"✓ {direction} rule #{rule_number} added: {action} {protocol} {from_port}-{to_port} from {cidr}")
        return True
    except Exception as e:
        print(f"✗ Error adding NACL rule: {e}")
        return None


# ============================================================================
# 7. NAT GATEWAY OPERATIONS
# ============================================================================

def create_nat_gateway(subnet_id, allocation_id_or_eip=None):
    """Create a NAT Gateway"""
    try:
        # Allocate new Elastic IP if not provided
        if not allocation_id_or_eip:
            eip_response = ec2.allocate_address(Domain='vpc')
            alloc_id = eip_response['AllocationId']
        else:
            alloc_id = allocation_id_or_eip

        response = ec2.create_nat_gateway(
            SubnetId=subnet_id,
            AllocationId=alloc_id,
            TagSpecifications=[{
                'ResourceType': 'natgateway',
                'Tags': [{'Key': 'Name', 'Value': 'nat-gateway'}]
            }]
        )

        nat_id = response['NatGateway']['NatGatewayId']
        print(f"✓ NAT Gateway created: {nat_id}")
        print(f"  Elastic IP: {response['NatGateway']['NatGatewayAddresses'][0].get('PublicIp')}")
        return response
    except Exception as e:
        print(f"✗ Error creating NAT Gateway: {e}")
        return None


def list_nat_gateways():
    """List all NAT Gateways"""
    try:
        response = ec2.describe_nat_gateways()
        print(f"\n🌐 NAT Gateways ({len(response['NatGateways'])} total):")
        print("-" * 100)
        for nat in response['NatGateways']:
            state = nat['State']
            subnet = nat['SubnetId']
            public_ip = nat['NatGatewayAddresses'][0].get('PublicIp', 'N/A') if nat['NatGatewayAddresses'] else 'N/A'
            print(f"  {nat['NatGatewayId']:20} | State: {state:15} | Subnet: {subnet:20} | IP: {public_ip}")
        return response
    except Exception as e:
        print(f"✗ Error listing NAT Gateways: {e}")
        return None


# ============================================================================
# 8. ELASTIC IP OPERATIONS
# ============================================================================

def allocate_elastic_ip():
    """Allocate an Elastic IP"""
    try:
        response = ec2.allocate_address(Domain='vpc')

        alloc_id = response['AllocationId']
        public_ip = response['PublicIp']

        print(f"✓ Elastic IP allocated")
        print(f"  Public IP: {public_ip}")
        print(f"  Allocation ID: {alloc_id}")
        return response
    except Exception as e:
        print(f"✗ Error allocating Elastic IP: {e}")
        return None


def list_elastic_ips():
    """List all Elastic IPs"""
    try:
        response = ec2.describe_addresses()
        print(f"\n📍 Elastic IPs ({len(response['Addresses'])} total):")
        print("-" * 100)
        for addr in response['Addresses']:
            public_ip = addr.get('PublicIp', 'N/A')
            instance = addr.get('InstanceId', 'Not associated')
            state = 'Associated' if instance != 'Not associated' else 'Not associated'
            print(f"  {public_ip:15} | {addr.get('AllocationId', 'N/A'):25} | {state:20}")
        return response
    except Exception as e:
        print(f"✗ Error listing Elastic IPs: {e}")
        return None


# ============================================================================
# 9. VPC PEERING
# ============================================================================

def create_vpc_peering(vpc_id_requester, vpc_id_accepter):
    """Create VPC peering connection"""
    try:
        response = ec2.create_vpc_peering_connection(
            VpcId=vpc_id_requester,
            PeerVpcId=vpc_id_accepter
        )

        peering_id = response['VpcPeeringConnection']['VpcPeeringConnectionId']
        print(f"✓ VPC Peering created: {peering_id}")
        print(f"  Requester VPC: {vpc_id_requester}")
        print(f"  Accepter VPC: {vpc_id_accepter}")
        return response
    except Exception as e:
        print(f"✗ Error creating VPC peering: {e}")
        return None


def accept_vpc_peering(peering_id):
    """Accept VPC peering connection"""
    try:
        response = ec2.accept_vpc_peering_connection(
            VpcPeeringConnectionId=peering_id
        )
        print(f"✓ VPC Peering accepted: {peering_id}")
        return response
    except Exception as e:
        print(f"✗ Error accepting VPC peering: {e}")
        return None


# ============================================================================
# 10. VPC FLOW LOGS
# ============================================================================

def enable_vpc_flow_logs(vpc_id, log_group_name, iam_role_arn):
    """Enable VPC Flow Logs"""
    try:
        response = ec2.create_flow_logs(
            ResourceType='VPC',
            ResourceIds=[vpc_id],
            TrafficType='ALL',
            LogDestinationType='cloud-watch-logs',
            LogGroupName=log_group_name,
            DeliverLogsPermissionIam=iam_role_arn,
            Tags={'Name': 'vpc-flow-logs', 'Environment': 'production'}
        )

        print(f"✓ VPC Flow Logs enabled for: {vpc_id}")
        print(f"  Log Group: {log_group_name}")
        return response
    except Exception as e:
        print(f"✗ Error enabling Flow Logs: {e}")
        return None


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AWS VPC Boto3 Operations Examples")
    print("=" * 80)

    # Example 1: List VPCs
    print("\n[1] Listing VPCs...")
    list_vpcs()

    # Example 2: List Subnets
    print("\n[2] Listing Subnets...")
    list_subnets()

    # Example 3: List Security Groups
    print("\n[3] Listing Security Groups...")
    list_security_groups()

    # Example 4: List Route Tables
    print("\n[4] Listing Route Tables...")
    list_route_tables()

    print("\n✓ Examples completed!")
