# AWS EC2 (Elastic Compute Cloud)

**Python boto3 code:** [ec2_operations.py](./ec2_operations.py)

---

## Table of Contents

1. [What is AWS EC2?](#1-what-is-aws-ec2)
2. [Core Concepts](#2-core-concepts)
3. [Instance Types & Families](#3-instance-types--families)
4. [Amazon Machine Images (AMI)](#4-amazon-machine-images-ami)
5. [Instance Lifecycle](#5-instance-lifecycle)
6. [EC2 Purchasing Options](#6-ec2-purchasing-options)
7. [EC2 Storage Options](#7-ec2-storage-options)
8. [EC2 Networking](#8-ec2-networking)
9. [Security Groups & Key Pairs](#9-security-groups--key-pairs)
10. [Elastic IP & ENI](#10-elastic-ip--eni)
11. [EC2 User Data & Metadata](#11-ec2-user-data--metadata)
12. [EC2 Placement Groups](#12-ec2-placement-groups)
13. [Auto Scaling](#13-auto-scaling)
14. [Elastic Load Balancing](#14-elastic-load-balancing)
15. [EC2 Monitoring & Troubleshooting](#15-ec2-monitoring--troubleshooting)
16. [EC2 Pricing Model](#16-ec2-pricing-model)
17. [EC2 CLI Cheat Sheet](#17-ec2-cli-cheat-sheet)
18. [Common Architectures & Use Cases](#18-common-architectures--use-cases)
19. [Best Practices](#19-best-practices)
20. [Advanced Features](#20-advanced-features)

---

## 1. What is AWS EC2?

**Amazon EC2 (Elastic Compute Cloud)** is AWS's core compute service that provides resizable virtual servers (instances) in the cloud. It's the backbone of AWS compute services.

### Key Characteristics

- **Virtual Servers** — Run Linux, Windows, or macOS instances on AWS infrastructure.
- **Elastic** — Scale up/down within minutes; add or remove instances as needed.
- **Pay-as-you-go** — Pay only for compute time you use (per second or hour).
- **Global Availability** — Available in all AWS Regions and Availability Zones.
- **Complete Control** — Root access, choice of OS, instance type, storage, and networking.
- **Integrated** — Works seamlessly with VPC, EBS, S3, IAM, CloudWatch, and other AWS services.

### What EC2 Provides

| Component | Description |
|-----------|-------------|
| **Compute** | Virtual CPUs (vCPUs) powered by Intel, AMD, or AWS Graviton processors |
| **Memory** | RAM from 0.5 GB to 24 TB depending on instance type |
| **Storage** | EBS (persistent) or Instance Store (ephemeral) |
| **Networking** | VPC integration, Elastic IPs, multiple network interfaces |
| **Security** | Security Groups, Key Pairs, IAM roles, dedicated hosts |

### EC2 vs Other Compute Services

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     AWS Compute Services Comparison                     │
├──────────────┬────────────────────────────────────────────────────────┤
│ EC2          │ Full control, any workload, persistent servers         │
│ Lambda       │ Serverless, event-driven, max 15 min execution         │
│ ECS/EKS      │ Container orchestration (Docker/Kubernetes)            │
│ Fargate      │ Serverless containers (no EC2 management)              │
│ Lightsail    │ Simplified VPS for small workloads                     │
│ Batch        │ Managed batch processing jobs                          │
└──────────────┴────────────────────────────────────────────────────────┘
```

---

## 2. Core Concepts

### 2.1 Instances

An **instance** is a virtual server running on AWS physical hardware.

```text
Instance = AMI + Instance Type + Storage + Network/Security Configuration
```

### 2.2 Regions and Availability Zones

```text
AWS Global Infrastructure:
  Region (e.g., us-east-1)           → Geographic area
    └── Availability Zone (AZ)       → Isolated data center(s)
         (e.g., us-east-1a, us-east-1b)
```

- **Region:** Physical location containing multiple AZs (e.g., `us-east-1`, `ap-south-1`)
- **Availability Zone:** One or more discrete data centers with redundant power/networking
- **Best Practice:** Deploy instances across multiple AZs for high availability

### 2.3 Tenancy Options

| Tenancy | Description | Use Case |
|---------|-------------|----------|
| **Shared (default)** | Multiple customers share physical hardware | Most workloads |
| **Dedicated Instance** | Hardware dedicated to your account | Compliance requirements |
| **Dedicated Host** | Entire physical server dedicated to you | Licensing (BYOL), compliance |

### 2.4 Instance Naming Convention

```text
Instance Type: m5.xlarge

  m     →  Instance Family (General Purpose)
  5     →  Generation (5th generation)
  xlarge→  Size (determines vCPU, memory, network)

Full format: [family][generation].[size]
Examples: t3.micro, c6i.2xlarge, r6g.metal
```

---

## 3. Instance Types & Families

EC2 offers instance types optimized for different use cases.

### 3.1 Instance Family Categories

| Category | Families | Optimized For | Example Use Cases |
|----------|----------|---------------|-------------------|
| **General Purpose** | T, M | Balanced compute/memory/network | Web servers, dev environments, small DBs |
| **Compute Optimized** | C | High-performance processors | Batch processing, gaming, ML inference |
| **Memory Optimized** | R, X, z | Large in-memory datasets | In-memory DBs, real-time analytics |
| **Storage Optimized** | I, D, H | High sequential read/write | Data warehousing, distributed file systems |
| **Accelerated Computing** | P, G, Inf, Trn | GPUs, custom hardware | ML training, graphics rendering, HPC |

### 3.2 Common Instance Types Detailed

#### General Purpose (T-series: Burstable)

```text
t3.micro   →  2 vCPU,  1 GB RAM   → Free tier eligible
t3.small   →  2 vCPU,  2 GB RAM
t3.medium  →  2 vCPU,  4 GB RAM
t3.large   →  2 vCPU,  8 GB RAM
t3.xlarge  →  4 vCPU, 16 GB RAM
t3.2xlarge →  8 vCPU, 32 GB RAM
```

**Burstable Performance:**
- T-series uses CPU credits for bursting above baseline
- Earn credits when idle, spend when busy
- `unlimited` mode: burst beyond credits (pay extra)

#### General Purpose (M-series: Fixed Performance)

```text
m6i.large   →   2 vCPU,   8 GB RAM
m6i.xlarge  →   4 vCPU,  16 GB RAM
m6i.2xlarge →   8 vCPU,  32 GB RAM
m6i.4xlarge →  16 vCPU,  64 GB RAM
m6i.8xlarge →  32 vCPU, 128 GB RAM
m6i.metal   →  128 vCPU, 512 GB RAM (bare metal)
```

#### Compute Optimized (C-series)

```text
c6i.large   →   2 vCPU,  4 GB RAM
c6i.xlarge  →   4 vCPU,  8 GB RAM
c6i.2xlarge →   8 vCPU, 16 GB RAM
c6i.4xlarge →  16 vCPU, 32 GB RAM
```

#### Memory Optimized (R-series)

```text
r6i.large    →   2 vCPU,  16 GB RAM
r6i.xlarge   →   4 vCPU,  32 GB RAM
r6i.2xlarge  →   8 vCPU,  64 GB RAM
r6i.4xlarge  →  16 vCPU, 128 GB RAM
r6i.24xlarge →  96 vCPU, 768 GB RAM
```

### 3.3 Processor Types

| Suffix | Processor | Notes |
|--------|-----------|-------|
| (none) | Intel | Default option |
| `a` | AMD EPYC | ~10% cheaper, similar performance |
| `g` | AWS Graviton (ARM) | ~20-40% cheaper, best price/performance |

```text
Examples:
  m6i.xlarge  → Intel Xeon
  m6a.xlarge  → AMD EPYC
  m6g.xlarge  → AWS Graviton2 (ARM64)
  m7g.xlarge  → AWS Graviton3 (ARM64, latest)
```

### 3.4 Instance Size Comparison

```text
Size Scale (multiplier of resources):

nano → micro → small → medium → large → xlarge → 2xlarge → ... → 24xlarge → metal

Each step roughly doubles the resources:
  t3.micro  =  2 vCPU,  1 GB
  t3.small  =  2 vCPU,  2 GB
  t3.medium =  2 vCPU,  4 GB
  t3.large  =  2 vCPU,  8 GB
  t3.xlarge =  4 vCPU, 16 GB
```

### 3.5 How to Choose Instance Type

```text
Decision Tree:

1. What's your workload type?
   ├── Balanced (web/app servers)     → M-series or T-series
   ├── CPU-intensive (batch, compute) → C-series
   ├── Memory-intensive (databases)   → R-series or X-series
   ├── Storage-intensive (analytics)  → I-series or D-series
   └── ML/GPU workloads               → P-series, G-series, Inf

2. Do you need consistent performance?
   ├── Yes → M-series (fixed performance)
   └── No (variable) → T-series (burstable, cheaper)

3. Processor preference?
   ├── Compatibility required → Intel (default)
   ├── Cost savings (10%) → AMD (a suffix)
   └── Best value (20-40% savings) → Graviton (g suffix)
```

---

## 4. Amazon Machine Images (AMI)

An **AMI** is a template that contains the software configuration (OS, application server, applications) required to launch an instance.

### 4.1 AMI Components

```text
AMI Contents:
├── Root Volume Template (EBS snapshot or instance store template)
├── Launch Permissions (who can use the AMI)
├── Block Device Mapping (volumes to attach at launch)
└── Metadata (name, description, architecture, etc.)
```

### 4.2 AMI Types

| Type | Provider | Description |
|------|----------|-------------|
| **AWS-provided** | Amazon | Amazon Linux, Windows Server, Ubuntu, etc. |
| **Marketplace** | Third-party | Pre-configured software stacks (cost may apply) |
| **Community** | Users | Shared publicly by AWS community |
| **Custom/Private** | You | Your own AMIs for your account |

### 4.3 Common AWS-Provided AMIs

```text
Amazon Linux 2023        → AWS-optimized Linux, latest
Amazon Linux 2           → Previous generation, LTS until 2025
Ubuntu Server 22.04 LTS  → Popular Linux distribution
Windows Server 2022      → Latest Windows Server
Red Hat Enterprise Linux → Enterprise Linux with support
macOS Monterey/Ventura   → For Mac development (Mac instances only)
```

### 4.4 Creating Custom AMIs

**Why create custom AMIs?**
- Pre-baked configurations (faster launch time)
- Consistent environment across instances
- Disaster recovery / backup
- Compliance and security hardening

```bash
# Create AMI from a running instance
aws ec2 create-image \
  --instance-id i-0123456789abcdef0 \
  --name "my-app-server-v1.0" \
  --description "App server with nginx, Node.js, monitoring agents" \
  --no-reboot

# List your AMIs
aws ec2 describe-images \
  --owners self \
  --query 'Images[*].[ImageId,Name,CreationDate]' \
  --output table

# Copy AMI to another region (for DR)
aws ec2 copy-image \
  --source-region us-east-1 \
  --source-image-id ami-0123456789abcdef0 \
  --name "my-app-server-v1.0-copy" \
  --region ap-south-1

# Share AMI with another account
aws ec2 modify-image-attribute \
  --image-id ami-0123456789abcdef0 \
  --launch-permission "Add=[{UserId=123456789012}]"

# Delete (deregister) an AMI
aws ec2 deregister-image --image-id ami-0123456789abcdef0

# Also delete the associated snapshot
aws ec2 delete-snapshot --snapshot-id snap-0123456789abcdef0
```

### 4.5 AMI Architecture

| Architecture | Description | Instance Types |
|--------------|-------------|----------------|
| **x86_64** | Intel/AMD 64-bit | Most instance types |
| **arm64** | AWS Graviton (ARM) | Instance types with 'g' suffix |
| **i386** | 32-bit (legacy) | Very old instances only |

### 4.6 AMI Virtualization Types

| Type | Description | Performance |
|------|-------------|-------------|
| **HVM** | Hardware Virtual Machine (full virtualization) | Best performance, recommended |
| **PV** | Paravirtual (legacy) | Older, limited instance types |

---

## 5. Instance Lifecycle

### 5.1 Instance States

```text
         ┌──────────┐
         │ pending  │ ← Instance launching
         └────┬─────┘
              │
              ▼
         ┌──────────┐
    ┌───►│ running  │◄───┐
    │    └────┬─────┘    │
    │         │          │
    │    Stop │          │ Start
    │         ▼          │
    │    ┌──────────┐    │
    │    │ stopping │    │
    │    └────┬─────┘    │
    │         │          │
    │         ▼          │
    │    ┌──────────┐    │
    └────│ stopped  │────┘
         └────┬─────┘
              │
              │ Terminate
              ▼
         ┌────────────┐
         │ shutting-  │
         │   down     │
         └─────┬──────┘
               │
               ▼
         ┌────────────┐
         │ terminated │
         └────────────┘
```

### 5.2 State Descriptions

| State | Description | Billing |
|-------|-------------|---------|
| **pending** | Instance is launching | No charge |
| **running** | Instance is running and accessible | Charged |
| **stopping** | Instance is preparing to stop | Charged |
| **stopped** | Instance is stopped | No compute charge (EBS charged) |
| **shutting-down** | Instance is preparing to terminate | No charge |
| **terminated** | Instance is deleted | No charge |

### 5.3 Stop vs Terminate

| Action | Result | Data Persistence |
|--------|--------|------------------|
| **Stop** | Instance stops, can be restarted | EBS volumes preserved |
| **Terminate** | Instance deleted permanently | EBS deleted (unless `DeleteOnTermination=false`) |
| **Hibernate** | RAM contents saved to EBS, faster restart | EBS + RAM state preserved |

### 5.4 Instance Lifecycle Commands

```bash
# Start an instance
aws ec2 start-instances --instance-ids i-0123456789abcdef0

# Stop an instance
aws ec2 stop-instances --instance-ids i-0123456789abcdef0

# Reboot an instance (doesn't change public IP)
aws ec2 reboot-instances --instance-ids i-0123456789abcdef0

# Terminate an instance
aws ec2 terminate-instances --instance-ids i-0123456789abcdef0

# Hibernate an instance (must be enabled at launch)
aws ec2 stop-instances --instance-ids i-0123456789abcdef0 --hibernate
```

### 5.5 Instance Hibernation

Hibernation saves RAM contents to EBS root volume, enabling faster startup.

**Requirements:**
- Instance must be EBS-backed
- Root volume must be encrypted
- Root volume must be large enough for RAM
- Must be explicitly enabled at launch
- Supported instance families: C, M, R, T (most types)

```bash
# Launch instance with hibernation enabled
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type m5.large \
  --hibernation-options Configured=true \
  --block-device-mappings '[{
    "DeviceName": "/dev/xvda",
    "Ebs": {
      "VolumeSize": 30,
      "Encrypted": true
    }
  }]'
```

---

## 6. EC2 Purchasing Options

### 6.1 Overview

| Option | Commitment | Discount | Best For |
|--------|------------|----------|----------|
| **On-Demand** | None | None (baseline) | Variable workloads, testing |
| **Reserved (RI)** | 1 or 3 years | Up to 72% | Steady-state workloads |
| **Savings Plans** | $/hour commitment | Up to 72% | Flexible, steady spend |
| **Spot** | None | Up to 90% | Fault-tolerant, flexible workloads |
| **Dedicated Hosts** | Per host | Varies | Licensing, compliance |
| **Dedicated Instances** | Per instance | ~10% premium | Compliance |
| **Capacity Reservations** | None | None | Guaranteed capacity |

### 6.2 On-Demand Instances

**Pay by the second** (minimum 60 seconds) for Linux/Windows.

```bash
# Launch On-Demand instance
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0
```

### 6.3 Reserved Instances (RIs)

Reserve capacity for 1 or 3 years for significant discounts.

**RI Types:**

| Type | Flexibility | Discount |
|------|-------------|----------|
| **Standard RI** | Fixed instance type, region | Highest (up to 72%) |
| **Convertible RI** | Can change instance type | Lower (up to 54%) |

**Payment Options:**

| Payment | Discount |
|---------|----------|
| All Upfront | Highest |
| Partial Upfront | Medium |
| No Upfront | Lowest |

```bash
# Purchase Reserved Instance
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id offering-id \
  --instance-count 2

# List your Reserved Instances
aws ec2 describe-reserved-instances \
  --query 'ReservedInstances[*].[InstanceType,State,InstanceCount,End]'
```

### 6.4 Savings Plans

**Commit to a consistent amount of usage ($/hour)** for 1 or 3 years.

| Plan Type | Flexibility | Discount |
|-----------|-------------|----------|
| **Compute Savings Plan** | Any instance type, region, OS, tenancy | Up to 66% |
| **EC2 Instance Savings Plan** | Specific instance family in a region | Up to 72% |

```text
Example:
  Commit: $10/hour for 1 year
  Usage: Mix of m5.xlarge, c5.2xlarge, or Lambda
  Result: Automatic discount applied to matching usage
```

### 6.5 Spot Instances

Use spare EC2 capacity at up to **90% discount**. Can be interrupted with 2-minute warning.

```bash
# Request Spot Instance
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type c5.xlarge \
  --instance-market-options 'MarketType=spot,SpotOptions={MaxPrice=0.05,SpotInstanceType=one-time}'

# Request Spot Fleet (multiple instances)
aws ec2 request-spot-fleet \
  --spot-fleet-request-config file://spot-fleet-config.json

# Check Spot price history
aws ec2 describe-spot-price-history \
  --instance-types c5.xlarge \
  --product-descriptions "Linux/UNIX" \
  --start-time $(date -u +%Y-%m-%dT%H:%M:%SZ -d '1 hour ago')
```

**Spot Instance Interruption Handling:**

```bash
# Check for interruption notice (from inside instance)
curl http://169.254.169.254/latest/meta-data/spot/instance-action

# Response if being interrupted:
# {"action": "terminate", "time": "2024-01-15T12:30:00Z"}
```

**Best Practices for Spot:**
- Use multiple instance types and AZs
- Design for fault tolerance (stateless apps, containers)
- Use Spot Fleet for automatic capacity management
- Combine with On-Demand for baseline capacity

### 6.6 Purchasing Option Comparison

```text
Workload Decision Tree:

Is workload fault-tolerant & flexible?
├── YES → Can it be interrupted?
│         ├── YES → Spot Instances (90% savings)
│         └── NO  → On-Demand or Reserved
└── NO → Is workload steady/predictable?
         ├── YES → Reserved Instances or Savings Plans (72% savings)
         └── NO  → On-Demand (most flexible)

Hybrid Strategy (common):
┌────────────────────────────────────────────────────────┐
│  Reserved/Savings Plan  │  On-Demand  │     Spot       │
│     (baseline)          │  (spikes)   │  (extra)       │
│        40%              │    20%      │     40%        │
└────────────────────────────────────────────────────────┘
```

---

## 7. EC2 Storage Options

### 7.1 Storage Types Overview

| Type | Persistence | Performance | Use Case |
|------|-------------|-------------|----------|
| **EBS** | Persistent | Variable (SSD/HDD) | Root volumes, databases |
| **Instance Store** | Ephemeral | Highest | Temp data, caches, buffers |
| **EFS** | Persistent, Shared | Variable | Shared file storage |
| **FSx** | Persistent, Shared | High | Windows, Lustre workloads |

### 7.2 Amazon EBS (Elastic Block Store)

Network-attached block storage that persists independently of instance.

#### EBS Volume Types

| Type | Name | IOPS (max) | Throughput | Use Case |
|------|------|------------|------------|----------|
| **gp3** | General Purpose SSD | 16,000 | 1,000 MB/s | Most workloads |
| **gp2** | General Purpose SSD | 16,000 | 250 MB/s | Legacy default |
| **io2** | Provisioned IOPS SSD | 256,000 | 4,000 MB/s | Critical databases |
| **io1** | Provisioned IOPS SSD | 64,000 | 1,000 MB/s | Database workloads |
| **st1** | Throughput HDD | 500 | 500 MB/s | Big data, logs |
| **sc1** | Cold HDD | 250 | 250 MB/s | Infrequent access |

#### EBS Volume Commands

```bash
# Create EBS volume
aws ec2 create-volume \
  --volume-type gp3 \
  --size 100 \
  --iops 3000 \
  --throughput 125 \
  --availability-zone us-east-1a \
  --encrypted \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=my-volume}]'

# Attach volume to instance
aws ec2 attach-volume \
  --volume-id vol-0123456789abcdef0 \
  --instance-id i-0123456789abcdef0 \
  --device /dev/sdf

# Detach volume
aws ec2 detach-volume --volume-id vol-0123456789abcdef0

# Create snapshot
aws ec2 create-snapshot \
  --volume-id vol-0123456789abcdef0 \
  --description "Backup before upgrade"

# Modify volume (resize or change type)
aws ec2 modify-volume \
  --volume-id vol-0123456789abcdef0 \
  --size 200 \
  --volume-type gp3 \
  --iops 4000
```

#### EBS Encryption

- Uses AWS KMS keys (AWS managed or customer managed)
- Encryption happens on EC2 servers (transparent to instance)
- Encrypted snapshots produce encrypted volumes
- Cannot directly encrypt an unencrypted volume (must snapshot → copy with encryption → create volume)

```bash
# Create encrypted volume
aws ec2 create-volume \
  --encrypted \
  --kms-key-id alias/my-key \
  --volume-type gp3 \
  --size 100 \
  --availability-zone us-east-1a

# Enable encryption by default for all new volumes in region
aws ec2 enable-ebs-encryption-by-default
```

### 7.3 Instance Store (Ephemeral Storage)

Physically attached to the host computer. **Data is lost when instance stops/terminates.**

**Characteristics:**
- Highest I/O performance (NVMe, millions of IOPS)
- Included in instance price (no additional cost)
- Size/count fixed by instance type
- Cannot be detached or attached to another instance

**Use Cases:**
- Temporary data (scratch space)
- Caches and buffers
- Shuffle storage for big data

```text
Instance Store Availability by Instance Type:
  c5d.xlarge  →  1 × 100 GB NVMe SSD
  c5d.4xlarge →  1 × 400 GB NVMe SSD
  i3.8xlarge  →  4 × 1,900 GB NVMe SSD
  d3.8xlarge  → 24 × 2,000 GB HDD
```

### 7.4 Storage Decision Guide

```text
Need persistent data?
├── NO → Instance Store (temporary, fastest)
└── YES → Need shared access?
          ├── YES → EFS (Linux NFS) or FSx (Windows/Lustre)
          └── NO → EBS
                   └── IOPS requirement?
                       ├── < 16,000 → gp3 (SSD, general purpose)
                       ├── > 16,000 → io2 (SSD, high IOPS)
                       └── Throughput-focused → st1/sc1 (HDD, cheaper)
```

---

## 8. EC2 Networking

### 8.1 VPC Fundamentals for EC2

Every EC2 instance launches inside a **VPC (Virtual Private Cloud)** subnet.

```text
VPC (10.0.0.0/16)
├── Public Subnet (10.0.1.0/24)
│   ├── Internet Gateway attached
│   ├── Route table: 0.0.0.0/0 → IGW
│   └── EC2 with public IP can access internet
│
├── Private Subnet (10.0.2.0/24)
│   ├── No direct internet access
│   ├── Route table: 0.0.0.0/0 → NAT Gateway
│   └── EC2 can initiate outbound internet via NAT
│
└── Isolated Subnet (10.0.3.0/24)
    └── No internet connectivity (internal only)
```

### 8.2 IP Addressing

| IP Type | Persistence | Assignment | Cost |
|---------|-------------|------------|------|
| **Private IP** | Permanent (within instance life) | Automatic | Free |
| **Public IP** | Lost on stop | Auto-assign optional | Free |
| **Elastic IP** | Persistent (until released) | Manual | Free if attached, $0.005/hr if idle |

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Associate with instance
aws ec2 associate-address \
  --instance-id i-0123456789abcdef0 \
  --allocation-id eipalloc-0123456789abcdef0

# Disassociate
aws ec2 disassociate-address --association-id eipassoc-0123456789abcdef0

# Release (if no longer needed)
aws ec2 release-address --allocation-id eipalloc-0123456789abcdef0
```

### 8.3 Network Performance

| Instance Size | Network Bandwidth |
|---------------|-------------------|
| nano - medium | Low to Moderate |
| large | Moderate |
| xlarge | High |
| 2xlarge - 4xlarge | Up to 10 Gbps |
| 8xlarge+ | 10-100 Gbps |
| metal | 100-400 Gbps |

**Enhanced Networking (ENA):**
- Higher bandwidth, lower latency, lower jitter
- Enabled by default on most current-gen instances
- SR-IOV based

```bash
# Check if ENA is enabled
aws ec2 describe-instances \
  --instance-ids i-0123456789abcdef0 \
  --query 'Reservations[].Instances[].EnaSupport'
```

---

## 9. Security Groups & Key Pairs

### 9.1 Security Groups

A **Security Group** is a virtual firewall that controls inbound and outbound traffic for instances.

**Characteristics:**
- **Stateful** — Return traffic automatically allowed
- **Default deny** — All inbound blocked by default
- **Allow rules only** — Cannot create deny rules
- **Multiple SGs** — Instance can have up to 5 security groups

```text
Security Group Rules Structure:
┌─────────────────────────────────────────────────────────────┐
│  Type     Protocol   Port Range   Source/Destination        │
├─────────────────────────────────────────────────────────────┤
│  SSH      TCP        22           My IP (203.0.113.5/32)    │
│  HTTP     TCP        80           0.0.0.0/0 (anywhere)      │
│  HTTPS    TCP        443          0.0.0.0/0 (anywhere)      │
│  Custom   TCP        3000-3100    sg-xxxx (another SG)      │
│  All      All        All          10.0.0.0/8 (VPC CIDR)     │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Create security group
aws ec2 create-security-group \
  --group-name my-web-sg \
  --description "Web server security group" \
  --vpc-id vpc-0123456789abcdef0

# Add inbound rule (SSH from specific IP)
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.5/32

# Add inbound rule (HTTP from anywhere)
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Add inbound rule (from another security group)
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 3306 \
  --source-group sg-9876543210fedcba0

# Remove rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.5/32

# List security group rules
aws ec2 describe-security-groups \
  --group-ids sg-0123456789abcdef0
```

### 9.2 Security Group Best Practices

```text
✔ Use least privilege (specific IPs, not 0.0.0.0/0 for SSH)
✔ Reference other SGs instead of IPs when possible
✔ Separate SGs by function (web-sg, app-sg, db-sg)
✔ Document rules with descriptions
✔ Regularly audit unused rules
✔ Use VPC Flow Logs to monitor traffic

✖ Don't open all ports (0-65535)
✖ Don't allow 0.0.0.0/0 for SSH/RDP
✖ Don't use default security group for production
```

### 9.3 Key Pairs

Key pairs provide secure SSH/RDP access to instances.

**Types:**
- **RSA** — Traditional, widely compatible
- **ED25519** — Newer, more secure, smaller keys

```bash
# Create key pair (AWS generates it)
aws ec2 create-key-pair \
  --key-name my-key-pair \
  --key-type ed25519 \
  --query 'KeyMaterial' \
  --output text > my-key-pair.pem

# Set permissions (Linux/Mac)
chmod 400 my-key-pair.pem

# Import existing public key
aws ec2 import-key-pair \
  --key-name my-imported-key \
  --public-key-material fileb://~/.ssh/id_rsa.pub

# List key pairs
aws ec2 describe-key-pairs

# Delete key pair
aws ec2 delete-key-pair --key-name my-key-pair
```

### 9.4 Connecting to Instances

```bash
# SSH to Linux instance
ssh -i my-key-pair.pem ec2-user@<public-ip>

# SSH to Ubuntu
ssh -i my-key-pair.pem ubuntu@<public-ip>

# SSH to Debian
ssh -i my-key-pair.pem admin@<public-ip>

# SCP file to instance
scp -i my-key-pair.pem file.txt ec2-user@<public-ip>:/home/ec2-user/

# Connect via Session Manager (no SSH key needed)
aws ssm start-session --target i-0123456789abcdef0

# EC2 Instance Connect (browser-based)
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-0123456789abcdef0 \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub
```

---

## 10. Elastic IP & ENI

### 10.1 Elastic IP (EIP)

A **static, public IPv4 address** that you can allocate and associate with instances.

**Use Cases:**
- Maintain fixed public IP across instance failures
- Point DNS records to a static IP
- Failover between instances

```bash
# Allocate EIP
aws ec2 allocate-address --domain vpc --network-border-group us-east-1

# Associate with instance
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --instance-id i-0123456789abcdef0

# Associate with network interface
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --network-interface-id eni-0123456789abcdef0

# Move to different instance (reassociate)
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --instance-id i-9876543210fedcba0 \
  --allow-reassociation
```

### 10.2 Elastic Network Interface (ENI)

A **virtual network card** that you can attach to instances.

**Attributes:**
- Primary private IPv4 address
- Secondary private IPv4 addresses
- Elastic IP per private IP
- Public IPv4 address
- Security groups
- MAC address
- Source/destination check flag

**Use Cases:**
- Multiple IPs per instance
- Network appliances
- Dual-homed instances
- License management (MAC-based)

```bash
# Create ENI
aws ec2 create-network-interface \
  --subnet-id subnet-0123456789abcdef0 \
  --groups sg-0123456789abcdef0 \
  --description "Secondary ENI"

# Attach to instance
aws ec2 attach-network-interface \
  --network-interface-id eni-0123456789abcdef0 \
  --instance-id i-0123456789abcdef0 \
  --device-index 1

# Detach
aws ec2 detach-network-interface \
  --attachment-id eni-attach-0123456789abcdef0

# Assign secondary private IP
aws ec2 assign-private-ip-addresses \
  --network-interface-id eni-0123456789abcdef0 \
  --secondary-private-ip-address-count 2
```

---

## 11. EC2 User Data & Metadata

### 11.1 User Data (Bootstrap Scripts)

**User Data** runs scripts at first boot to configure instances.

**Characteristics:**
- Runs as root
- Executes only on first boot (by default)
- Limited to 16 KB
- Can be shell script or cloud-init directive

```bash
#!/bin/bash
# Example User Data script

# Update system
yum update -y

# Install nginx
amazon-linux-extras install nginx1 -y

# Start nginx
systemctl start nginx
systemctl enable nginx

# Download application
aws s3 cp s3://my-bucket/app.tar.gz /opt/
cd /opt && tar -xzf app.tar.gz
```

**Launch instance with user data:**

```bash
# From file
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --user-data file://bootstrap.sh

# Inline (base64 encoded)
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --user-data "IyEvYmluL2Jhc2gKeXVtIHVwZGF0ZSAteQ=="
```

### 11.2 Instance Metadata Service (IMDS)

**Metadata** provides information about the running instance accessible from within.

**Endpoint:** `http://169.254.169.254/latest/meta-data/`

```bash
# Get instance ID
curl http://169.254.169.254/latest/meta-data/instance-id

# Get public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Get private IP
curl http://169.254.169.254/latest/meta-data/local-ipv4

# Get instance type
curl http://169.254.169.254/latest/meta-data/instance-type

# Get security groups
curl http://169.254.169.254/latest/meta-data/security-groups

# Get IAM role credentials
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role

# Get availability zone
curl http://169.254.169.254/latest/meta-data/placement/availability-zone

# Get user data
curl http://169.254.169.254/latest/user-data

# List all metadata categories
curl http://169.254.169.254/latest/meta-data/
```

### 11.3 IMDSv2 (Recommended)

IMDSv2 requires a session token for security (protects against SSRF attacks).

```bash
# Get token
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Use token to get metadata
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id
```

**Enforce IMDSv2:**

```bash
# At launch
aws ec2 run-instances \
  --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled"

# Modify running instance
aws ec2 modify-instance-metadata-options \
  --instance-id i-0123456789abcdef0 \
  --http-tokens required \
  --http-endpoint enabled
```

---

## 12. EC2 Placement Groups

Placement groups control how instances are placed on underlying hardware.

### 12.1 Placement Group Types

| Type | Placement | Use Case | Limits |
|------|-----------|----------|--------|
| **Cluster** | Same rack, same AZ | HPC, low latency | Up to 10 Gbps between instances |
| **Spread** | Distinct racks, can span AZs | Critical instances, HA | Max 7 instances per AZ |
| **Partition** | Separate partitions (rack groups) | HDFS, Cassandra, Kafka | Up to 7 partitions per AZ |

### 12.2 Visual Representation

```text
CLUSTER (Same rack = lowest latency)
┌─────────────────────────────────┐
│           Same Rack             │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │
│  │EC2│ │EC2│ │EC2│ │EC2│ │EC2│  │
│  └───┘ └───┘ └───┘ └───┘ └───┘  │
└─────────────────────────────────┘

SPREAD (Different racks = max isolation)
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Rack 1  │ │ Rack 2  │ │ Rack 3  │
│ ┌───┐   │ │ ┌───┐   │ │ ┌───┐   │
│ │EC2│   │ │ │EC2│   │ │ │EC2│   │
│ └───┘   │ │ └───┘   │ │ └───┘   │
└─────────┘ └─────────┘ └─────────┘

PARTITION (Isolated groups within AZ)
┌───────────────────────────────────────┐
│  Partition 1    Partition 2    Partition 3
│  ┌───┐ ┌───┐    ┌───┐ ┌───┐    ┌───┐ ┌───┐
│  │EC2│ │EC2│    │EC2│ │EC2│    │EC2│ │EC2│
│  └───┘ └───┘    └───┘ └───┘    └───┘ └───┘
└───────────────────────────────────────┘
```

### 12.3 Placement Group Commands

```bash
# Create cluster placement group
aws ec2 create-placement-group \
  --group-name my-cluster-pg \
  --strategy cluster

# Create spread placement group
aws ec2 create-placement-group \
  --group-name my-spread-pg \
  --strategy spread

# Create partition placement group
aws ec2 create-placement-group \
  --group-name my-partition-pg \
  --strategy partition \
  --partition-count 3

# Launch instance in placement group
aws ec2 run-instances \
  --placement GroupName=my-cluster-pg \
  --instance-type c5n.18xlarge \
  --image-id ami-0123456789abcdef0

# List placement groups
aws ec2 describe-placement-groups

# Delete placement group
aws ec2 delete-placement-group --group-name my-cluster-pg
```

---

## 13. Auto Scaling

### 13.1 Auto Scaling Components

```text
┌─────────────────────────────────────────────────────────────┐
│                      Auto Scaling Group                      │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │  Launch Template    │    │   Scaling Policies   │        │
│  │  (what to launch)   │    │  (when to scale)     │        │
│  └─────────────────────┘    └─────────────────────┘        │
│                                                             │
│  Min Size: 2    Desired: 4    Max Size: 10                 │
│                                                             │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐                                   │
│  │EC2│ │EC2│ │EC2│ │EC2│  ← Current running instances       │
│  └───┘ └───┘ └───┘ └───┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### 13.2 Launch Template

Defines instance configuration for Auto Scaling.

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name my-template \
  --launch-template-data '{
    "ImageId": "ami-0123456789abcdef0",
    "InstanceType": "t3.micro",
    "KeyName": "my-key-pair",
    "SecurityGroupIds": ["sg-0123456789abcdef0"],
    "UserData": "IyEvYmluL2Jhc2gKeXVtIHVwZGF0ZSAteQ==",
    "IamInstanceProfile": {"Name": "my-instance-profile"},
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/xvda",
      "Ebs": {"VolumeSize": 20, "VolumeType": "gp3"}
    }],
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Environment", "Value": "Production"}]
    }]
  }'

# Create new version
aws ec2 create-launch-template-version \
  --launch-template-name my-template \
  --source-version 1 \
  --launch-template-data '{"InstanceType": "t3.small"}'
```

### 13.3 Auto Scaling Group

```bash
# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --launch-template LaunchTemplateName=my-template,Version='$Latest' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 4 \
  --vpc-zone-identifier "subnet-abc123,subnet-def456" \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --target-group-arns "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-tg/abc123"

# Update capacity
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name my-asg \
  --desired-capacity 6

# Update ASG configuration
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --min-size 3 \
  --max-size 15

# Describe ASG
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg
```

### 13.4 Scaling Policies

| Policy Type | Description | Use Case |
|-------------|-------------|----------|
| **Target Tracking** | Maintain specific metric value | Keep CPU at 50% |
| **Step Scaling** | Scale based on alarm thresholds | Tiered response to load |
| **Simple Scaling** | Scale after cooldown period | Basic scaling |
| **Scheduled** | Scale at specific times | Predictable patterns |
| **Predictive** | ML-based, forecast scaling | Traffic patterns |

```bash
# Target Tracking Policy (maintain CPU at 50%)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-asg \
  --policy-name cpu-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 50.0
  }'

# Scheduled Scaling (scale up at 9 AM)
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name my-asg \
  --scheduled-action-name scale-up-morning \
  --recurrence "0 9 * * MON-FRI" \
  --desired-capacity 10

# Step Scaling Policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-asg \
  --policy-name step-scale-out \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments '[
    {"MetricIntervalLowerBound": 0, "MetricIntervalUpperBound": 20, "ScalingAdjustment": 2},
    {"MetricIntervalLowerBound": 20, "ScalingAdjustment": 4}
  ]'
```

### 13.5 Instance Refresh (Rolling Updates)

```bash
# Start instance refresh (replace instances with new template)
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name my-asg \
  --preferences '{
    "MinHealthyPercentage": 90,
    "InstanceWarmup": 300
  }'

# Check status
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name my-asg
```

---

## 14. Elastic Load Balancing

### 14.1 Load Balancer Types

| Type | Layer | Protocols | Use Case |
|------|-------|-----------|----------|
| **Application LB (ALB)** | Layer 7 | HTTP, HTTPS, gRPC | Web applications, microservices |
| **Network LB (NLB)** | Layer 4 | TCP, UDP, TLS | Ultra-high performance, gaming |
| **Gateway LB (GWLB)** | Layer 3 | IP | Security appliances, firewalls |
| **Classic LB (CLB)** | Layer 4/7 | HTTP, HTTPS, TCP | Legacy (avoid for new apps) |

### 14.2 ALB Architecture

```text
Internet
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│                Application Load Balancer                  │
│                                                          │
│  Listeners: HTTP:80, HTTPS:443                          │
│  Rules: Path-based, Host-based routing                  │
└──────────────────────────────────────────────────────────┘
    │                    │                    │
    ▼                    ▼                    ▼
┌────────────┐    ┌────────────┐    ┌────────────┐
│ Target     │    │ Target     │    │ Target     │
│ Group: API │    │ Group: Web │    │ Group: Auth│
│ /api/*     │    │ /*         │    │ /auth/*    │
├────────────┤    ├────────────┤    ├────────────┤
│ EC2  EC2   │    │ EC2  EC2   │    │ Lambda     │
└────────────┘    └────────────┘    └────────────┘
```

### 14.3 Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name my-alb \
  --subnets subnet-abc123 subnet-def456 \
  --security-groups sg-0123456789abcdef0 \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create Target Group
aws elbv2 create-target-group \
  --name my-target-group \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-0123456789abcdef0 \
  --target-type instance \
  --health-check-path /health \
  --health-check-interval-seconds 30

# Register targets
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:...:targetgroup/my-tg/xxx \
  --targets Id=i-0123456789abcdef0 Id=i-9876543210fedcba0

# Create Listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:...:loadbalancer/app/my-alb/xxx \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/my-tg/xxx

# Create HTTPS Listener with certificate
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:...:loadbalancer/app/my-alb/xxx \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:...:certificate/xxx \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/my-tg/xxx
```

### 14.4 ALB Routing Rules

```bash
# Path-based routing
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:...:listener/app/my-alb/xxx/xxx \
  --priority 10 \
  --conditions '[{"Field": "path-pattern", "Values": ["/api/*"]}]' \
  --actions '[{"Type": "forward", "TargetGroupArn": "arn:aws:elasticloadbalancing:...:targetgroup/api-tg/xxx"}]'

# Host-based routing
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:...:listener/app/my-alb/xxx/xxx \
  --priority 20 \
  --conditions '[{"Field": "host-header", "Values": ["api.example.com"]}]' \
  --actions '[{"Type": "forward", "TargetGroupArn": "arn:aws:elasticloadbalancing:...:targetgroup/api-tg/xxx"}]'
```

### 14.5 Network Load Balancer (NLB)

```bash
# Create NLB
aws elbv2 create-load-balancer \
  --name my-nlb \
  --subnets subnet-abc123 subnet-def456 \
  --type network \
  --scheme internet-facing

# Create TCP Target Group
aws elbv2 create-target-group \
  --name my-tcp-tg \
  --protocol TCP \
  --port 80 \
  --vpc-id vpc-0123456789abcdef0 \
  --target-type instance

# Create TCP Listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:...:loadbalancer/net/my-nlb/xxx \
  --protocol TCP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/my-tcp-tg/xxx
```

---

## 15. EC2 Monitoring & Troubleshooting

### 15.1 CloudWatch Metrics

**Default metrics (5-minute interval, free):**

| Metric | Description |
|--------|-------------|
| `CPUUtilization` | Percentage of allocated CPU used |
| `DiskReadOps` | Read operations (instance store only) |
| `DiskWriteOps` | Write operations (instance store only) |
| `NetworkIn` | Bytes received on all interfaces |
| `NetworkOut` | Bytes sent on all interfaces |
| `StatusCheckFailed` | Combined instance + system status |

**Detailed monitoring (1-minute interval, additional cost):**

```bash
# Enable detailed monitoring
aws ec2 monitor-instances --instance-ids i-0123456789abcdef0

# Disable detailed monitoring
aws ec2 unmonitor-instances --instance-ids i-0123456789abcdef0
```

### 15.2 CloudWatch Alarms

```bash
# Create CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name HighCPU-i-0123456789abcdef0 \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:my-topic

# Create StatusCheckFailed alarm with auto-recover
aws cloudwatch put-metric-alarm \
  --alarm-name StatusCheckFailed-i-0123456789abcdef0 \
  --metric-name StatusCheckFailed \
  --namespace AWS/EC2 \
  --statistic Maximum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:automate:us-east-1:ec2:recover
```

### 15.3 Status Checks

| Check Type | What It Checks | Resolution |
|------------|----------------|------------|
| **System Status** | AWS infrastructure (network, power, hardware) | Wait or stop/start to migrate |
| **Instance Status** | OS-level issues (failed boot, kernel panic) | Reboot or troubleshoot OS |

```bash
# View instance status checks
aws ec2 describe-instance-status \
  --instance-ids i-0123456789abcdef0

# Report instance issue (custom check)
aws ec2 report-instance-status \
  --instance-id i-0123456789abcdef0 \
  --status impaired \
  --reason-codes instance-stuck-in-state
```

### 15.4 System Log & Console Output

```bash
# Get system log (serial console output)
aws ec2 get-console-output \
  --instance-id i-0123456789abcdef0

# Get screenshot (Windows or Linux with GUI)
aws ec2 get-console-screenshot \
  --instance-id i-0123456789abcdef0
```

### 15.5 EC2 Serial Console

Direct console access for advanced troubleshooting.

```bash
# Enable serial console access (account level)
aws ec2 enable-serial-console-access

# Connect via AWS CLI
aws ec2-instance-connect send-serial-console-ssh-public-key \
  --instance-id i-0123456789abcdef0 \
  --serial-port 0 \
  --ssh-public-key file://~/.ssh/id_rsa.pub
```

### 15.6 Troubleshooting Common Issues

```text
Issue: Cannot SSH to instance
├── Check: Security group allows port 22 from your IP?
├── Check: Instance in public subnet with public IP or EIP?
├── Check: Route table has 0.0.0.0/0 → IGW for public subnet?
├── Check: Network ACL allows inbound/outbound traffic?
├── Check: Key pair correct? chmod 400?
└── Check: Instance status checks passing?

Issue: Instance unreachable
├── Check: Instance running (not stopped/terminated)?
├── Check: Status checks passing?
├── Check: Security group rules?
├── Check: Network configuration (VPC, subnet, routing)?
└── Try: Stop/start to migrate to new hardware

Issue: Slow performance
├── Check: CPU/memory metrics in CloudWatch
├── Check: EBS volume IOPS/throughput
├── Check: Network bandwidth (check instance type limits)
├── Check: T-series CPU credits (if burstable)
└── Consider: Upgrade instance type or optimize application
```

---

## 16. EC2 Pricing Model

### 16.1 Pricing Components

| Component | Billing |
|-----------|---------|
| **Instance hours** | Per second (min 60 sec) for Linux/Windows |
| **EBS storage** | Per GB-month provisioned |
| **EBS IOPS** | Per provisioned IOPS (io1/io2 only) |
| **Data transfer OUT** | Per GB (first 100 GB/month free) |
| **Elastic IPs** | Free if attached, $0.005/hr if idle |
| **Snapshots** | Per GB-month stored |

### 16.2 Data Transfer Costs

```text
Data Transfer Pricing:
┌──────────────────────────────────────────────────────────────┐
│ Transfer Type                              │ Cost            │
├────────────────────────────────────────────┼─────────────────┤
│ Data IN from internet                      │ Free            │
│ Data OUT to internet (first 100 GB/mo)     │ Free            │
│ Data OUT to internet (next 10 TB)          │ ~$0.09/GB       │
│ Between AZs (same region)                  │ $0.01/GB each way│
│ Between regions                            │ $0.02/GB+       │
│ Same AZ (private IP)                       │ Free            │
│ EC2 → S3 (same region)                     │ Free            │
│ EC2 → CloudFront                           │ Free            │
└────────────────────────────────────────────┴─────────────────┘
```

### 16.3 Cost Optimization Strategies

```text
Strategy 1: Right-sizing
├── Use CloudWatch metrics to identify underutilized instances
├── AWS Compute Optimizer recommendations
└── Downsize or switch to T-series for variable workloads

Strategy 2: Purchase Options
├── Reserved Instances for baseline (72% savings)
├── Savings Plans for flexible commitment (66% savings)
├── Spot for fault-tolerant workloads (90% savings)
└── On-Demand only for unpredictable/short-term

Strategy 3: Architecture
├── Use Graviton instances (20-40% better price/performance)
├── Auto Scaling to match demand
├── Schedule non-production instances (stop nights/weekends)
└── Use multiple AZs but minimize cross-AZ traffic

Strategy 4: Storage
├── Delete unused EBS volumes and snapshots
├── Use gp3 instead of gp2 (20% cheaper)
├── Use lifecycle policies for snapshots
└── S3 for backups instead of EBS snapshots where possible
```

---

## 17. EC2 CLI Cheat Sheet

```bash
# ══════════════════════════════════════════════════════════════
# INSTANCE OPERATIONS
# ══════════════════════════════════════════════════════════════

# Launch instance
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --count 1

# List instances
aws ec2 describe-instances \
  --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name,IP:PublicIpAddress}'

# Filter by tag
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=Production"

# Start/Stop/Terminate
aws ec2 start-instances --instance-ids i-xxx
aws ec2 stop-instances --instance-ids i-xxx
aws ec2 terminate-instances --instance-ids i-xxx
aws ec2 reboot-instances --instance-ids i-xxx

# Modify instance type (must be stopped)
aws ec2 modify-instance-attribute \
  --instance-id i-xxx \
  --instance-type "{\"Value\": \"t3.large\"}"

# Add/modify tags
aws ec2 create-tags \
  --resources i-xxx \
  --tags Key=Name,Value=my-instance Key=Environment,Value=Prod

# ══════════════════════════════════════════════════════════════
# AMI OPERATIONS
# ══════════════════════════════════════════════════════════════

# Create AMI
aws ec2 create-image --instance-id i-xxx --name "my-ami" --no-reboot

# List AMIs
aws ec2 describe-images --owners self

# Copy AMI to another region
aws ec2 copy-image --source-region us-east-1 --source-image-id ami-xxx --region eu-west-1

# Deregister AMI
aws ec2 deregister-image --image-id ami-xxx

# ══════════════════════════════════════════════════════════════
# EBS OPERATIONS
# ══════════════════════════════════════════════════════════════

# Create volume
aws ec2 create-volume --size 100 --volume-type gp3 --availability-zone us-east-1a

# Attach volume
aws ec2 attach-volume --volume-id vol-xxx --instance-id i-xxx --device /dev/sdf

# Create snapshot
aws ec2 create-snapshot --volume-id vol-xxx --description "Backup"

# Modify volume
aws ec2 modify-volume --volume-id vol-xxx --size 200 --volume-type gp3

# ══════════════════════════════════════════════════════════════
# SECURITY GROUPS
# ══════════════════════════════════════════════════════════════

# Create security group
aws ec2 create-security-group --group-name my-sg --description "My SG" --vpc-id vpc-xxx

# Add inbound rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx --protocol tcp --port 22 --cidr 0.0.0.0/0

# Remove inbound rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxx --protocol tcp --port 22 --cidr 0.0.0.0/0

# ══════════════════════════════════════════════════════════════
# KEY PAIRS
# ══════════════════════════════════════════════════════════════

# Create key pair
aws ec2 create-key-pair --key-name my-key --query 'KeyMaterial' --output text > my-key.pem

# Import key pair
aws ec2 import-key-pair --key-name my-key --public-key-material fileb://~/.ssh/id_rsa.pub

# List key pairs
aws ec2 describe-key-pairs

# ══════════════════════════════════════════════════════════════
# NETWORKING
# ══════════════════════════════════════════════════════════════

# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Associate Elastic IP
aws ec2 associate-address --allocation-id eipalloc-xxx --instance-id i-xxx

# Create ENI
aws ec2 create-network-interface --subnet-id subnet-xxx --groups sg-xxx

# ══════════════════════════════════════════════════════════════
# AUTO SCALING
# ══════════════════════════════════════════════════════════════

# Create launch template
aws ec2 create-launch-template --launch-template-name my-lt --launch-template-data file://lt.json

# Create ASG
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name my-asg \
  --launch-template LaunchTemplateName=my-lt \
  --min-size 2 --max-size 10 --desired-capacity 4 \
  --vpc-zone-identifier "subnet-xxx,subnet-yyy"

# Update desired capacity
aws autoscaling set-desired-capacity --auto-scaling-group-name my-asg --desired-capacity 6
```

---

## 18. Common Architectures & Use Cases

### 18.1 Basic Web Server

```text
Internet
    │
Internet Gateway
    │
┌───────────────────────────────────────┐
│           Public Subnet               │
│  ┌─────────────────────────────────┐  │
│  │  EC2 (Web Server)               │  │
│  │  - nginx/Apache                 │  │
│  │  - Public IP or EIP             │  │
│  │  - Security Group: 80, 443, 22  │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

### 18.2 Three-Tier Web Application

```text
                    Internet
                        │
                   Route 53 (DNS)
                        │
                  ┌─────┴─────┐
                  │    ALB    │
                  └─────┬─────┘
         ┌──────────────┼──────────────┐
         │              │              │
     ┌───┴───┐     ┌───┴───┐     ┌───┴───┐
     │ EC2   │     │ EC2   │     │ EC2   │   ← Web Tier (Public)
     │ (web) │     │ (web) │     │ (web) │     Auto Scaling Group
     └───┬───┘     └───┬───┘     └───┬───┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                  ┌─────┴─────┐
                  │    ALB    │   ← Internal ALB
                  └─────┬─────┘
         ┌──────────────┼──────────────┐
         │              │              │
     ┌───┴───┐     ┌───┴───┐     ┌───┴───┐
     │ EC2   │     │ EC2   │     │ EC2   │   ← App Tier (Private)
     │ (app) │     │ (app) │     │ (app) │     Auto Scaling Group
     └───┬───┘     └───┬───┘     └───┬───┘
         │              │              │
         └──────────────┼──────────────┘
                        │
               ┌────────┴────────┐
               │                 │
           ┌───┴───┐         ┌───┴───┐
           │ RDS   │         │ RDS   │   ← Database Tier (Private)
           │Primary│         │Standby│     Multi-AZ
           └───────┘         └───────┘
```

### 18.3 Microservices on ECS/EKS

```text
                      ALB
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   /api/users     /api/products   /api/orders
        │              │              │
   ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
   │ ECS     │    │ ECS     │    │ ECS     │
   │ Service │    │ Service │    │ Service │
   │ (EC2/   │    │ (EC2/   │    │ (EC2/   │
   │ Fargate)│    │ Fargate)│    │ Fargate)│
   └────┬────┘    └────┬────┘    └────┬────┘
        │              │              │
   ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
   │ DynamoDB│    │ RDS     │    │ ElastiC │
   │         │    │         │    │ ache    │
   └─────────┘    └─────────┘    └─────────┘
```

### 18.4 Hybrid Cloud (On-Premises + AWS)

```text
┌─────────────────┐          ┌─────────────────────────────────┐
│   On-Premises   │          │            AWS VPC              │
│                 │          │                                 │
│  ┌───────────┐  │   VPN/   │  ┌───────────┐  ┌───────────┐  │
│  │ App       │  │  Direct  │  │ EC2       │  │ RDS       │  │
│  │ Server    │──┼──Connect─┼──│ (hybrid   │  │ (database)│  │
│  └───────────┘  │          │  │  workload)│  └───────────┘  │
│                 │          │  └───────────┘                 │
│  ┌───────────┐  │          │                                │
│  │ Database  │  │          │  ┌───────────┐                 │
│  │ (legacy)  │  │          │  │ S3        │                 │
│  └───────────┘  │          │  │ (storage) │                 │
└─────────────────┘          │  └───────────┘                 │
                             └─────────────────────────────────┘
```

### 18.5 Big Data / Analytics

```text
Data Sources                Processing                 Storage/Query
─────────────              ──────────                 ─────────────
┌───────────┐     S3      ┌───────────┐             ┌───────────┐
│ Kinesis   │────────────▶│ EMR       │────────────▶│ S3        │
│ (stream)  │             │ (Spark,   │             │ (data     │
└───────────┘             │  Hadoop)  │             │  lake)    │
                          └───────────┘             └─────┬─────┘
┌───────────┐                  │                         │
│ EC2       │                  │                   ┌─────┴─────┐
│ (batch    │──────────────────┘                   │           │
│  upload)  │                                 ┌────┴────┐ ┌────┴────┐
└───────────┘                                 │ Athena  │ │Redshift │
                                              │ (SQL)   │ │(warehouse)
                                              └─────────┘ └─────────┘
```

---

## 19. Best Practices

### Security

```text
✔ Use IAM roles (not access keys) for EC2 to access AWS services
✔ Use IMDSv2 (session tokens) instead of IMDSv1
✔ Enable EBS encryption by default
✔ Use private subnets + NAT Gateway for non-public instances
✔ Restrict security group rules (no 0.0.0.0/0 for SSH)
✔ Use Systems Manager Session Manager instead of SSH bastion
✔ Enable VPC Flow Logs for network monitoring
✔ Rotate SSH keys regularly
✔ Use AWS Config rules for compliance checking
✔ Enable termination protection for critical instances
```

### Cost

```text
✔ Right-size instances using CloudWatch and Compute Optimizer
✔ Use Reserved Instances or Savings Plans for steady workloads
✔ Use Spot for fault-tolerant workloads
✔ Use Graviton instances for better price/performance
✔ Auto Scale to match actual demand
✔ Schedule development instances to stop outside work hours
✔ Delete unused EBS volumes and snapshots
✔ Use gp3 instead of gp2 volumes
✔ Monitor data transfer costs between AZs/regions
```

### Reliability

```text
✔ Deploy across multiple AZs
✔ Use Auto Scaling with health checks
✔ Use ELB for distributing traffic
✔ Implement health checks at application level
✔ Create AMIs for quick recovery
✔ Set up CloudWatch alarms with auto-recovery actions
✔ Test failover scenarios regularly
✔ Use placement groups for HA (spread) or performance (cluster)
✔ Back up EBS volumes with snapshots
```

### Performance

```text
✔ Choose the right instance type for your workload
✔ Use enhanced networking (ENA) for high throughput
✔ Use placement groups for low-latency communication
✔ Use EBS-optimized instances for storage-heavy workloads
✔ Use instance store for highest I/O (if data is ephemeral)
✔ Use gp3 with provisioned IOPS when needed
✔ Consider NVMe instances (i3, d3) for extreme storage performance
✔ Use Transfer Acceleration or CloudFront for global users
```

### Operations

```text
✔ Use Launch Templates (not Launch Configurations)
✔ Tag all resources consistently (Environment, Team, Project)
✔ Use Systems Manager for patch management
✔ Use CloudWatch Logs agent for log aggregation
✔ Set up CloudTrail for API auditing
✔ Use Instance Connect or Session Manager for secure access
✔ Automate AMI creation with EC2 Image Builder
✔ Use Infrastructure as Code (CloudFormation, Terraform)
```

---

## 20. Advanced Features

### 20.1 EC2 Fleet

Launch and manage multiple instance types across purchase options.

```bash
aws ec2 create-fleet \
  --launch-template-configs '[{
    "LaunchTemplateSpecification": {
      "LaunchTemplateId": "lt-xxx",
      "Version": "$Latest"
    },
    "Overrides": [
      {"InstanceType": "c5.large"},
      {"InstanceType": "c5.xlarge"},
      {"InstanceType": "m5.large"}
    ]
  }]' \
  --target-capacity-specification '{
    "TotalTargetCapacity": 10,
    "OnDemandTargetCapacity": 2,
    "SpotTargetCapacity": 8,
    "DefaultTargetCapacityType": "spot"
  }'
```

### 20.2 EC2 Image Builder

Automated pipeline for creating, testing, and distributing AMIs.

```text
Pipeline:
  Source Image (Amazon Linux 2)
       │
       ▼
  Build Components (Install software, configure)
       │
       ▼
  Test Components (Run validation tests)
       │
       ▼
  Distribute (Copy to regions, share with accounts)
       │
       ▼
  Output AMI
```

### 20.3 Nitro System

AWS's custom hypervisor and security chip powering modern EC2 instances.

**Benefits:**
- Near bare-metal performance
- Enhanced security (hardware root of trust)
- Fast EBS with dedicated hardware
- Higher network performance

**Nitro-based instances:** C5, M5, R5, T3, and all newer generations

### 20.4 Nitro Enclaves

Isolated compute environments for processing sensitive data.

```text
EC2 Instance
┌─────────────────────────────────────┐
│  Parent Instance                    │
│  (can't access enclave memory)      │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Nitro Enclave               │   │
│  │  - Isolated CPU/memory       │   │
│  │  - No network access         │   │
│  │  - No persistent storage     │   │
│  │  - Cryptographic attestation │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 20.5 Bare Metal Instances

Full access to hardware without virtualization overhead.

```text
Use cases:
- Non-virtualized workloads
- License compliance (per-core/per-socket)
- Custom hypervisors (VMware, nested virtualization)
- Direct hardware access requirements

Instance types: *.metal (e.g., m5.metal, c5.metal, i3.metal)
```

### 20.6 Capacity Reservations

Guarantee EC2 capacity in a specific AZ.

```bash
# Create Capacity Reservation
aws ec2 create-capacity-reservation \
  --instance-type m5.xlarge \
  --instance-platform Linux/UNIX \
  --availability-zone us-east-1a \
  --instance-count 10 \
  --end-date-type unlimited

# Launch instance into reservation
aws ec2 run-instances \
  --capacity-reservation-specification CapacityReservationTarget={CapacityReservationId=cr-xxx}
```

### 20.7 Dedicated Hosts

Entire physical server dedicated to your use.

```bash
# Allocate Dedicated Host
aws ec2 allocate-hosts \
  --instance-type m5.xlarge \
  --quantity 1 \
  --availability-zone us-east-1a \
  --host-recovery on

# Launch instance on Dedicated Host
aws ec2 run-instances \
  --host-id h-xxx \
  --instance-type m5.xlarge \
  --tenancy host
```

---

## Summary

| Topic | Key Points |
|-------|------------|
| **Instance Types** | Choose based on workload: General (M/T), Compute (C), Memory (R), Storage (I/D), GPU (P/G) |
| **Purchasing** | On-Demand (flexibility), Reserved/Savings Plans (commitment), Spot (cost savings) |
| **Storage** | EBS (persistent), Instance Store (ephemeral), EFS (shared) |
| **Networking** | VPC, Subnets, Security Groups, ENI, Elastic IP |
| **Security** | Security Groups, Key Pairs, IAM Roles, IMDSv2 |
| **Scaling** | Auto Scaling Groups, Launch Templates, Scaling Policies |
| **Load Balancing** | ALB (HTTP/S), NLB (TCP/UDP), Target Groups |
| **Monitoring** | CloudWatch Metrics, Alarms, Status Checks |
