# AWS VPC (Virtual Private Cloud)

**Python boto3 code:** [vpc_operations.py](./vpc_operations.py)

---

## Table of Contents

1. [What is AWS VPC?](#1-what-is-aws-vpc)
2. [VPC Architecture & Components](#2-vpc-architecture--components)
3. [IP Addressing (CIDR)](#3-ip-addressing-cidr)
4. [Creating VPCs](#4-creating-vpcs)
5. [Subnets](#5-subnets)
6. [Route Tables](#6-route-tables)
7. [Internet Gateway](#7-internet-gateway)
8. [NAT Gateway & NAT Instance](#8-nat-gateway--nat-instance)
9. [Security Groups](#9-security-groups)
10. [Network ACLs](#10-network-acls)
11. [VPC Flow Logs](#11-vpc-flow-logs)
12. [VPC Peering](#12-vpc-peering)
13. [VPC Endpoints](#13-vpc-endpoints)
14. [Elastic IPs](#14-elastic-ips)
15. [DNS & DHCP](#15-dns--dhcp)
16. [Network Interfaces](#16-network-interfaces)
17. [VPN & Hybrid Connectivity](#17-vpn--hybrid-connectivity)
18. [Best Practices](#18-best-practices)
19. [CLI Cheat Sheet](#19-cli-cheat-sheet)
20. [Common Architectures](#20-common-architectures)

---

## 1. What is AWS VPC?

**AWS VPC** is a logically isolated network environment within AWS where you can launch resources.

### Key Characteristics

- **Isolated** - Logically separated from other VPCs
- **Customizable** - Define your own network architecture
- **Multi-AZ** - Can span multiple availability zones
- **Hybrid** - Can connect to on-premises networks
- **Secure** - Fine-grained access control
- **Scalable** - Grows with your business needs

### VPC vs Default VPC

| Aspect | Custom VPC | Default VPC |
|--------|-----------|------------|
| **CIDR** | You choose | 172.31.0.0/16 (fixed) |
| **Public subnets** | Manual setup | Auto-created |
| **NAT** | Manual setup | Provided |
| **Control** | Full | Limited |
| **Use case** | Production | Testing/Learning |

### When to Use VPC

```
✅ Any production workload
✅ Need security isolation
✅ Hybrid cloud setup
✅ Multi-tier application architecture
✅ Compliance requirements
```

---

## 2. VPC Architecture & Components

### VPC Building Blocks

```
┌─────────────────────────────────────────────────────┐
│                    AWS Region                        │
├─────────────────────────────────────────────────────┤
│  ┌────────────────┐          ┌────────────────┐    │
│  │ Availability   │          │ Availability   │    │
│  │ Zone 1         │          │ Zone 2         │    │
│  ├────────────────┤          ├────────────────┤    │
│  │┌──────────────┐│          │┌──────────────┐│    │
│  ││ Public       ││          ││ Private      ││    │
│  ││ Subnet       ││          ││ Subnet       ││    │
│  ││ 10.0.1.0/24 ││          ││ 10.0.3.0/24  ││    │
│  │└──────────────┘│          │└──────────────┘│    │
│  │┌──────────────┐│          │┌──────────────┐│    │
│  ││ Private      ││          ││ Database     ││    │
│  ││ Subnet       ││          ││ Subnet       ││    │
│  ││ 10.0.2.0/24 ││          ││ 10.0.4.0/24  ││    │
│  │└──────────────┘│          │└──────────────┘│    │
│  └────────────────┘          └────────────────┘    │
│           ▲                           ▲             │
│        IGW │                       NAT│             │
│           └───────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

### VPC Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **VPC** | Network container | 10.0.0.0/16 |
| **Subnet** | Segment of VPC in one AZ | 10.0.1.0/24 |
| **Route Table** | Rules for traffic routing | Send 0.0.0.0/0 to IGW |
| **Internet Gateway** | Access to/from internet | Attach to VPC |
| **NAT Gateway** | Outbound internet for private| Use EIP |
| **Security Group** | Firewall per instance | Allow 22, 443 |
| **Network ACL** | Subnet-level firewall | Allow/Deny rules |
| **VPC Peering** | Connect two VPCs | Route between VPCs |
| **VPC Endpoints** | Private AWS service access | S3, DynamoDB endpoints |

---

## 3. IP Addressing (CIDR)

### CIDR Notation

```
CIDR: Classless Inter-Domain Routing
Format: xxx.xxx.xxx.xxx/prefix

Example: 10.0.0.0/16
  - IP: 10.0.0.0
  - /16: First 16 bits are fixed, remaining 16 bits can vary
  - Range: 10.0.0.0 to 10.0.255.255
  - Usable: 65,536 addresses (65,536 - 5 reserved = 65,531)
```

### Common CIDR Blocks

```
10.0.0.0/8     - 16 million addresses (Large networks)
10.0.0.0/16    - 65,536 addresses (Standard VPC)
10.0.0.0/24    - 256 addresses (Subnet)
10.0.0.0/32    - 1 address (Host)

192.168.0.0/16 - 65,536 addresses
172.16.0.0/12  - 1 million addresses
```

### Subnet Planning

```
VPC: 10.0.0.0/16 (65,536 addresses)
  │
  ├─ Public Subnet 1:    10.0.1.0/24 (256 addresses)
  ├─ Private Subnet 1:   10.0.2.0/24 (256 addresses)
  ├─ Public Subnet 2:    10.0.3.0/24 (256 addresses)
  ├─ Database Subnet 1:  10.0.10.0/24 (256 addresses)
  └─ Database Subnet 2:  10.0.11.0/24 (256 addresses)

Remaining: ~63,500 addresses for future growth
```

### Reserved IP Addresses (per subnet)

```
For subnet 10.0.1.0/24 (256 addresses)

10.0.1.0       - Network address (reserved)
10.0.1.1       - VPC router (reserved)
10.0.1.2       - DNS server (reserved)
10.0.1.3       - Reserved by AWS
10.0.1.4-254   - Usable for instances (251 available)
10.0.1.255     - Broadcast address (reserved)
```

---

## 4. Creating VPCs

### Create VPC with Boto3

```python
import boto3

ec2 = boto3.client('ec2')

# Create VPC
vpc_response = ec2.create_vpc(
    CidrBlock='10.0.0.0/16',
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [
                {'Key': 'Name', 'Value': 'production-vpc'},
                {'Key': 'Environment', 'Value': 'production'}
            ]
        }
    ]
)

vpc_id = vpc_response['Vpc']['VpcId']
print(f"VPC created: {vpc_id}")

# Enable DNS
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsHostnames={'Value': True},
)
```

### List VPCs

```python
# List all VPCs
vpcs = ec2.describe_vpcs()

for vpc in vpcs['Vpcs']:
    print(f"VPC: {vpc['VpcId']} | CIDR: {vpc['CidrBlock']}")
```

---

## 5. Subnets

### Create Subnets

```python
# Create public subnet (AZ 1)
public_subnet = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.1.0/24',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'public-subnet-1a'}]
    }]
)

# Create private subnet (AZ 1)
private_subnet = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.2.0/24',
    AvailabilityZone='us-east-1a',
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'private-subnet-1a'}]
    }]
)

# Create database subnet (AZ 2)
db_subnet = ec2.create_subnet(
    VpcId=vpc_id,
    CidrBlock='10.0.10.0/24',
    AvailabilityZone='us-east-1b',
    TagSpecifications=[{
        'ResourceType': 'subnet',
        'Tags': [{'Key': 'Name', 'Value': 'db-subnet-1b'}]
    }]
)
```

### Subnet Types

```
🌐 PUBLIC SUBNET
   └─ Has route to Internet Gateway
   └─ Instances can reach internet if they have public IP
   └─ Use for: Web servers, load balancers

🔒 PRIVATE SUBNET
   └─ No direct internet access
   └─ Can access internet via NAT Gateway (if configured)
   └─ Use for: Application servers, internal services

🗄️ DATABASE SUBNET
   └─ No internet access
   └─ Use for: Databases, sensitive data
```

---

## 6. Route Tables

### Create & Configure Route Table

```python
# Create route table
rt_response = ec2.create_route_table(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'route-table',
        'Tags': [{'Key': 'Name', 'Value': 'public-routes'}]
    }]
)

route_table_id = rt_response['RouteTable']['RouteTableId']

# Add route to Internet Gateway
ec2.create_route(
    RouteTableId=route_table_id,
    DestinationCidrBlock='0.0.0.0/0',  # All traffic
    GatewayId=igw_id  # Send to IGW
)

# Associate with subnet
ec2.associate_route_table(
    RouteTableId=route_table_id,
    SubnetId=public_subnet['Subnet']['SubnetId']
)
```

### Route Table Examples

```
PUBLIC Route Table:
  Destination       │ Target
  ────────────────────────────────────
  10.0.0.0/16      │ local
  0.0.0.0/0        │ igw-12345678 (Internet Gateway)

PRIVATE Route Table:
  Destination       │ Target
  ────────────────────────────────────
  10.0.0.0/16      │ local
  0.0.0.0/0        │ nat-12345678 (NAT Gateway)

DATABASE Route Table:
  Destination       │ Target
  ────────────────────────────────────
  10.0.0.0/16      │ local
  (No route to internet)
```

---

## 7. Internet Gateway

### Create & Attach Internet Gateway

```python
# Create IGW
igw_response = ec2.create_internet_gateway(
    TagSpecifications=[{
        'ResourceType': 'internet-gateway',
        'Tags': [{'Key': 'Name', 'Value': 'main-igw'}]
    }]
)

igw_id = igw_response['InternetGateway']['InternetGatewayId']

# Attach to VPC
ec2.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
)

print(f"IGW attached: {igw_id}")
```

### Allocate Elastic IP for Public Instance

```python
# Allocate Elastic IP
eip_response = ec2.allocate_address(
    Domain='vpc'  # For EC2-VPC
)

alloc_id = eip_response['AllocationId']
public_ip = eip_response['PublicIp']

print(f"Elastic IP allocated: {public_ip}")

# Associate with EC2 instance
ec2.associate_address(
    AllocationId=alloc_id,
    InstanceId=instance_id
)
```

---

## 8. NAT Gateway & NAT Instance

### NAT Gateway (Managed - Recommended)

```python
# Allocate Elastic IP
eip = ec2.allocate_address(Domain='vpc')

# Create NAT Gateway (always in public subnet)
nat_response = ec2.create_nat_gateway(
    SubnetId=public_subnet_id,  # Must be in public subnet
    AllocationId=eip['AllocationId'],
    TagSpecifications=[{
        'ResourceType': 'nat-gateway',
        'Tags': [{'Key': 'Name', 'Value': 'nat-gateway-1'}]
    }]
)

nat_gateway_id = nat_response['NatGateway']['NatGatewayId']

# Add route in private subnet route table
ec2.create_route(
    RouteTableId=private_rt_id,
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_gateway_id
)
```

### NAT vs NAT Instance

| Feature | NAT Gateway | NAT Instance |
|---------|------------|------------|
| **Management** | Managed by AWS | You manage |
| **Availability** | Highly available | Single point of failure |
| **Bandwidth** | Scales automatically | Limited by instance type |
| **Cost** | Higher hourly + data | Lower hourly + data |
| **Performance** | Better | Dependent on instance |
| **HA Setup** | Simple | Complex (need multiple) |

---

## 9. Security Groups

### Create Security Group

```python
# Create security group
sg_response = ec2.create_security_group(
    GroupName='web-servers',
    Description='Security group for web servers',
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'security-group',
        'Tags': [{'Key': 'Name', 'Value': 'web-sg'}]
    }]
)

sg_id = sg_response['GroupId']
```

### Add Ingress Rules (Inbound)

```python
# Allow HTTP
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTP'}]
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Allow HTTPS'}]
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '203.0.113.0/32', 'Description': 'SSH from office'}]
        }
    ]
)
```

### Security Group vs Network ACL

| Feature | Security Group | Network ACL |
|---------|----------|------------|
| **Level** | Instance | Subnet |
| **Stateful** | Yes | No (must define return traffic) |
| **Rules** | Allow only | Allow + Deny |
| **Default** | Deny all inbound | Allow all |
| **Performance** | Slower (more granular) | Faster |

---

## 10. Network ACLs

### Create Network ACL

```python
# Create Network ACL
nacl_response = ec2.create_network_acl(
    VpcId=vpc_id,
    TagSpecifications=[{
        'ResourceType': 'network-acl',
        'Tags': [{'Key': 'Name', 'Value': 'db-nacl'}]
    }]
)

nacl_id = nacl_response['NetworkAcl']['NetworkAclId']

# Add inbound rule (allow SQL from app tier)
ec2.create_network_acl_entry(
    NetworkAclId=nacl_id,
    RuleNumber=100,
    Protocol='6',  # TCP
    RuleAction='allow',
    CidrBlock='10.0.2.0/24',  # From app subnet
    PortRange={'FromPort': 3306, 'ToPort': 3306}  # MySQL
)

# Add outbound rule (allow response)
ec2.create_network_acl_entry(
    NetworkAclId=nacl_id,
    RuleNumber=100,
    Protocol='6',
    RuleAction='allow',
    CidrBlock='10.0.2.0/24',
    PortRange={'FromPort': 1024, 'ToPort': 65535},  # Ephemeral ports
    Egress=True
)
```

---

## 11. VPC Flow Logs

### Enable VPC Flow Logs

```python
# Create IAM role for Flow Logs
# (Skip for brevity - create role with CloudWatch Logs permissions)

# Create Flow Logs
flow_logs_response = ec2.create_flow_logs(
    ResourceType='VPC',
    ResourceIds=[vpc_id],
    TrafficType='ALL',  # ALL, ACCEPT, REJECT
    LogDestinationType='cloud-watch-logs',
    LogGroupName='/aws/vpc/flowlogs',
    DeliverLogsPermissionIam='arn:aws:iam::123456789:role/flowlogsRole',
    Tags={'Name': 'vpc-flow-logs', 'Environment': 'production'}
)

print(f"Flow Logs enabled: {flow_logs_response['FlowLogIds']}")
```

### Analyze Flow Logs

```python
# Query Flow Logs in CloudWatch
logs = boto3.client('logs')

response = logs.start_query(
    logGroupName='/aws/vpc/flowlogs',
    startTime=int((datetime.now() - timedelta(hours=1)).timestamp()),
    endTime=int(datetime.now().timestamp()),
    queryString="""
    fields srcaddr, destaddr, srcport, destport, action, bytes
    | stats sum(bytes) as total_bytes by srcaddr, destaddr, action
    | sort total_bytes desc
    """
)
```

---

## 12. VPC Peering

### Create VPC Peering Connection

```python
# Peer VPC A and VPC B
peering_response = ec2.create_vpc_peering_connection(
    VpcId='vpc-12345678',  # VPC A (requester)
    PeerVpcId='vpc-87654321'  # VPC B (accepter)
)

peering_id = peering_response['VpcPeeringConnection']['VpcPeeringConnectionId']

# Accept peering (from accepter account/region)
ec2_b = boto3.client('ec2', region_name='us-west-1')
ec2_b.accept_vpc_peering_connection(
    VpcPeeringConnectionId=peering_id
)

# Add routes
ec2.create_route(
    RouteTableId=rt_a_id,
    DestinationCidrBlock='10.1.0.0/16',  # VPC B CIDR
    VpcPeeringConnectionId=peering_id
)

print(f"VPC Peering established: {peering_id}")
```

---

## 13. VPC Endpoints

### Gateway Endpoints (S3 & DynamoDB)

```python
# Create S3 Gateway Endpoint
endpoint_response = ec2.create_vpc_endpoint(
    VpcId=vpc_id,
    ServiceName='com.amazonaws.us-east-1.s3',
    VpcEndpointType='Gateway',
    RouteTableIds=[private_rt_id]
)

print(f"S3 Endpoint created: {endpoint_response['VpcEndpoint']['VpcEndpointId']}")

# EC2 in private subnet can now access S3 without NAT
```

### Interface Endpoints (Services like RDS, SNS, SQS)

```python
# Create RDS Interface Endpoint
endpoint_response = ec2.create_vpc_endpoint(
    VpcId=vpc_id,
    ServiceName='com.amazonaws.us-east-1.rds',
    VpcEndpointType='Interface',
    SubnetIds=[private_subnet_id],
    SecurityGroupIds=[sg_id],
    PrivateDnsEnabled=True
)

print(f"RDS Endpoint created: {endpoint_response['VpcEndpoint']['VpcEndpointId']}")
```

### Endpoint Benefits

```
✅ Private access to AWS services (no internet)
✅ Improved security (no IGW/NAT needed)
✅ Lower latency (AWS network)
✅ Lower costs (no NAT gateway charges)
✅ Data doesn't traverse internet
```

---

## 14. Elastic IPs

### Allocate & Associate Elastic IPs

```python
# Allocate Elastic IP
eip_response = ec2.allocate_address(Domain='vpc')

allocation_id = eip_response['AllocationId']
public_ip = eip_response['PublicIp']

# Release later if not needed
# ec2.release_address(AllocationId=allocation_id)

# Associate with instance
association = ec2.associate_address(
    AllocationId=allocation_id,
    InstanceId=instance_id
)
```

### Elastic IP Characteristics

```
✓ Persists across stop/start (unlike public IPs)
✓ Can be associated/disassociated
✓ Costs when not associated
✓ Limited per account (~5 per region by default)
✓ No charge while associated & instance running
```

---

## 15. DNS & DHCP

### Enable DNS

```python
# Enable DNS Hostnames
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsHostnames={'Value': True}
)

# Enable DNS Support
ec2.modify_vpc_attribute(
    VpcId=vpc_id,
    EnableDnsSupport={'Value': True}
)
```

### DHCP Option Sets

```python
# Create custom DHCP option set
dhcp_response = ec2.create_dhcp_options(
    DhcpConfigurations=[
        {
            'Key': 'domain-name',
            'Values': ['example.com']
        },
        {
            'Key': 'domain-name-servers',
            'Values': ['8.8.8.8', '8.8.4.4']
        }
    ]
)

dhcp_id = dhcp_response['DhcpOptions']['DhcpOptionsId']

# Associate with VPC
ec2.associate_dhcp_options(
    DhcpOptionsId=dhcp_id,
    VpcId=vpc_id
)
```

---

## 16. Network Interfaces

### Manage Elastic Network Interfaces

```python
# Create ENI
eni_response = ec2.create_network_interface(
    SubnetId=subnet_id,
    PrivateIpAddresses=[
        {'PrivateIpAddress': '10.0.1.50', 'DeviceIndex': 0}
    ],
    Groups=[sg_id],
    Description='Secondary network interface'
)

eni_id = eni_response['NetworkInterface']['NetworkInterfaceId']

# Attach to instance
ec2.attach_network_interface(
    NetworkInterfaceId=eni_id,
    InstanceId=instance_id,
    DeviceIndex=1  # eth1
)

# Assign secondary private IP
ec2.assign_private_ip_addresses(
    NetworkInterfaceId=eni_id,
    PrivateIpAddresses=['10.0.1.51']
)
```

---

## 17. VPN & Hybrid Connectivity

### Create VPN Connection

```python
# Create Customer Gateway (on-premises)
cgw_response = ec2.create_customer_gateway(
    Type='ipsec.1',
    PublicIp='203.0.113.0',  # On-premises public IP
    BgpAsn=65000
)

cgw_id = cgw_response['CustomerGateway']['CustomerGatewayId']

# Create Virtual Private Gateway
vgw_response = ec2.create_vpn_gateway(
    Type='ipsec.1',
    AmazonSideAsn=64512
)

vgw_id = vgw_response['VpnGateway']['VpnGatewayId']

# Attach to VPC
ec2.attach_vpn_gateway(
    VpnGatewayId=vgw_id,
    VpcId=vpc_id
)

# Create VPN Connection
vpn_response = ec2.create_vpn_connection(
    Type='ipsec.1',
    CustomerGatewayId=cgw_id,
    VpnGatewayId=vgw_id
)

vpn_id = vpn_response['VpnConnection']['VpnConnectionId']
print(f"VPN Connection created: {vpn_id}")
```

### Connectivity Options

```
🔌 VPN Connection
   └─ IPsec tunnel over internet
   └─ Bandwidth: ~1.25 Gbps
   └─ Latency: Variable (depends on internet)
   └─ Cost: Low
   └─ Setup: Hours

🔌 AWS Direct Connect
   └─ Dedicated network connection
   └─ Bandwidth: 1, 10, 100 Gbps
   └─ Latency: Consistent
   └─ Cost: Higher
   └─ Setup: Weeks

🔌 Transit Gateway
   └─ Hub-and-spoke architecture
   └─ Connect multiple VPCs/networks
   └─ Centralized routing
```

---

## 18. Best Practices

### Network Design

```
✓ Plan subnets carefully (leave growth room)
✓ Use separate subnets for different tiers (web, app, db)
✓ One NAT Gateway per AZ (HA)
✓ Use /24 subnets (balance: not too large, not too small)
✓ Reserve first and last subnet blocks

❌ DON'T make subnets too large (/16 per subnet)
❌ DON'T use single subnet for all tiers
❌ DON'T put all resources in one AZ
❌ DON'T use overlapping CIDR blocks
```

### Security

```
✓ Security groups: Allow only necessary ports
✓ NACLs: Additional layer for critical subnets
✓ Private subnets: For sensitive data (DB, backend)
✓ Enable VPC Flow Logs (for troubleshooting)
✓ Use VPC endpoints (avoid internet exposure)
✓ Regular security group/NACL audits

❌ DON'T allow 0.0.0.0/0 to SSH
❌ DON'T put databases in public subnets
❌ DON'T overly permissive security groups
```

### Cost Optimization

```
✓ NAT Gateway is cheaper if <5GB/day
✓ NAT Instance if >10GB/day to same AZ
✓ S3 Gateway Endpoint (free, no data charges)
✓ Delete unused Elastic IPs
✓ Consolidate NAT Gateways if possible

💡 Comparison:
   NAT Gateway:  $0.045/hour + $0.045/GB
   NAT Instance: t3.nano $0.0052/hour + $0.045/GB data
```

---

## 19. CLI Cheat Sheet

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnet
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a

# Create Internet Gateway
aws ec2 create-internet-gateway

# Attach IGW to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-12345678 \
  --vpc-id vpc-12345678

# Create Route Table
aws ec2 create-route-table --vpc-id vpc-12345678

# Add route
aws ec2 create-route \
  --route-table-id rtb-12345678 \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-12345678

# Create Security Group
aws ec2 create-security-group \
  --group-name web-sg \
  --description "Security group for web servers" \
  --vpc-id vpc-12345678

# Add security group rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Describe VPCs
aws ec2 describe-vpcs

# Describe subnets
aws ec2 describe-subnets

# Describe security groups
aws ec2 describe-security-groups
```

---

## 20. Common Architectures

### 3-Tier Web Application

```
┌─────────────────────────────────────────────────────┐
│                    Internet                          │
└────────────────────────┬────────────────────────────┘
                         │
                    ┌────▼────┐
                    │   IGW    │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼───┐        ┌───▼───┐       ┌───▼───┐
    │  ELB  │        │  ELB  │       │  ELB  │
    └───┬───┘        └───┬───┘       └───┬───┘
        │                │                │
    ┌───▼────────┐   ┌───▼────────┐   ┌───▼────────┐
    │ Public Sub │   │ Public Sub │   │ Public Sub │
    │ - Web Tier │   │ - Web Tier │   │ - Web Tier │
    └────────────┘   └────────────┘   └────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼────────┐   ┌───▼────────┐   ┌───▼────────┐
    │ Private Sub│   │ Private Sub│   │ Private Sub│
    │ - App Tier │   │ - App Tier │   │ - App Tier │
    └────────────┘   └────────────┘   └────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼────────┐   ┌───▼────────┐
    │  DB Sub 1  │   │  DB Sub 2  │
    │  RDS AZ1   │   │  RDS AZ2   │
    └────────────┘   └────────────┘
```

### Hybrid Network

```
┌─────────────────────────┐
│   On-Premises Network   │
│   10.10.0.0/16          │
│   ┌─────────────────┐   │
│   │ Corporate App  │   │
│   └────────┬────────┘   │
│            │            │
│   ┌────────▼────────┐   │
│   │ Customer GW     │   │
│   │ 203.0.113.0     │   │
│   └────────┬────────┘   │
└────────────┼─────────────┘
             │ IPsec VPN
             │
┌────────────▼─────────────┐
│      AWS VPC             │
│      10.0.0.0/16         │
│   ┌──────────────────┐   │
│   │ Virtual GW       │   │
│   └────────┬─────────┘   │
│            │             │
│  ┌─────────▼──────────┐  │
│  │ Private Subnet     │  │
│  │ - Internal Apps    │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

---

## Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [VPC Sizing and Planning](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html)
- [Security Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html)
