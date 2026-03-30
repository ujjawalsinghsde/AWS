# AWS

A comprehensive collection of AWS service documentation and study notes — basic to advanced, designed for developers learning cloud architecture.

## Core Services

### Compute & Serverless
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **Lambda**     | Serverless compute — event-driven architecture, scaling, deployment, observability | [Readme](./Lambda/Readme.md) · [boto3 Python](./Lambda/lambda_operations.py) |
| **EC2**        | Virtual servers in the cloud — provisioning, networking, security groups, and instance management | [Readme](./EC2/Readme.md) · [boto3 Python](./EC2/ec2_operations.py) |

### Database Services
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **RDS**        | Managed relational database — multi-AZ, read replicas, backups, high availability, performance | [Readme](./RDS/Readme.md) · [boto3 Python](./RDS/rds_operations.py) |
| **DynamoDB**   | NoSQL database — tables, indexes, TTL, streams, transactions, scaling, cost optimization | [Readme](./DynamoDB/Readme.md) · [boto3 Python](./DynamoDB/dynamodb_operations.py) |

### Storage & Content Delivery
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **S3**         | Object storage — basics, security, performance, advanced features | [Readme](./S3/Readme.md) · [boto3 Python](./S3/s3_operations.py) |

### Networking & Security
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **VPC**        | Virtual private cloud — subnets, routing, security groups, NAT, VPC peering, flow logs | [Readme](./VPC/Readme.md) · [boto3 Python](./VPC/vpc_operations.py) |
| **IAM**        | Identity & access management — users, roles, policies, MFA, cross-account access, STS | [Readme](./IAM/Readme.md) · [boto3 Python](./IAM/iam_operations.py) |

### Monitoring & Observability
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **CloudWatch** | Monitoring & observability — metrics, logs, alarms, dashboards, log insights, anomaly detection | [Readme](./CloudWatch/README.md) |

### Messaging & Queuing
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **SQS**        | Message queuing — standard & FIFO queues, visibility timeout, DLQ, batch operations, cost optimization | [Readme](./SQS/Readme.md) · [boto3 Python](./SQS/sqs_operations.py) |
| **SNS**        | Pub/Sub messaging — topics, subscriptions, fan-out patterns, filtering, multiple protocols | [Readme](./SNS/Readme.md) · [boto3 Python](./SNS/sns_operations.py) |
| **SES**        | Email service — identity verification, templates, configuration sets, bulk sending, compliance | [Readme](./SES/Readme.md) · [boto3 Python](./SES/ses_operations.py) |

### Analytics & Data
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **Athena**     | Serverless SQL query engine on S3 data               | [Readme](./Athena/Readme.md) |

### CI/CD
| Service        | Description                                          | Link |
|----------------|------------------------------------------------------|------|
| **CICD**       | Continuous integration and deployment pipelines      | [Readme](./CICD/Readme.md) |
