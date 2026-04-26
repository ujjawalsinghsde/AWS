# EC2 Interview Questions

## 1. Fundamental Questions

### Basic Concepts
1. **What is Amazon EC2 and how does it work?**
   - Answer: EC2 provides resizable compute capacity in the cloud. It allows you to launch virtual servers (instances) with various configurations, pay only for what you use, and scale up/down based on demand.

2. **What are the different types of EC2 instances?**
   - General Purpose (m-series): Balanced compute, memory, networking
   - Compute Optimized (c-series): High-performance processors
   - Memory Optimized (r-series, x-series): In-memory databases, caches
   - Storage Optimized (i-series, d-series): High sequential read/write
   - Accelerated Computing (p-series, g-series): GPU/FPGA hardware

3. **Explain EC2 pricing models**
   - On-Demand: Pay per second, no commitment
   - Reserved Instances: 1-3 year commitment, up to 72% discount
   - Spot Instances: Up to 90% discount, can be interrupted
   - Dedicated Hosts: Physical server for compliance
   - Savings Plan: Compute savings across regions

4. **What is an AMI (Amazon Machine Image)?**
   - A template containing the OS, application software, and configurations needed to launch an instance
   - Can be AWS-provided, community-built, or custom-built

5. **Explain instance states**
   - pending, running, stopping, stopped, shutting-down, terminated
   - Stopped instances retain storage, terminated instances are deleted

---

## 2. Intermediate Scenario-Based Questions

### Security & Networking
6. **Scenario: You need to allow SSH access to an EC2 instance from your office. How would you do it?**
   - Answer:
     - Create/modify a Security Group
     - Add inbound rule: Protocol=TCP, Port=22, Source=Your Office IP/VPN CIDR
     - Ensure key pair is secure (chmod 400)
     - Never use 0.0.0.0/0 for SSH in production

7. **How do you secure EC2 instances? List best practices.**
   - Use Security Groups (stateful firewall)
   - Implement NACLs (Network ACLs) at subnet level
   - Use VPC endpoints for private AWS service access
   - Enable VPC Flow Logs for monitoring
   - Implement EC2 Instance Connect instead of SSH
   - Use IAM instance profiles for AWS API access
   - Encrypt data in transit (TLS) and at rest
   - Keep AMIs and patches updated
   - Use Systems Manager Session Manager instead of SSH

8. **Scenario: You have a production app running on EC2. A security audit requires rotating SSH keys. How do you do this without downtime?**
   - Create a new AMI with updated keys
   - Launch new instances from the updated AMI
   - Use load balancer to shift traffic gradually
   - Terminate old instances after verification
   - Alternative: Use EC2 Instance Connect (no SSH keys needed)

### High Availability & Fault Tolerance
9. **How do you achieve high availability for EC2 instances?**
   - Use Auto Scaling Groups across multiple AZs
   - Place instances behind a load balancer (ALB/NLB)
   - Use AMIs for quick recovery
   - Implement health checks
   - Use RDS Multi-AZ for databases
   - Use EBS snapshots for backup
   - Configure CloudWatch alarms

10. **Scenario: Your application needs 99.99% uptime. Design the architecture.**
    - Use Multi-AZ deployment
    - Auto Scaling Group across 3+ AZs
    - Application Load Balancer with health checks
    - RDS Multi-AZ database
    - Route 53 with failover routing
    - CloudWatch alarms for auto-recovery
    - EBS snapshots and backup strategy
    - Test failover regularly

11. **What's the difference between EBS vs Instance Store?**
    - **EBS**: Network storage, persistent after stop, supports snapshots, gp2/gp3/io1/io2
    - **Instance Store**: Physically attached, ephemeral (lost on stop/terminate), higher IOPS, no snapshots

---

## 3. Advanced Problem-Solving Questions

### Performance & Optimization
12. **Scenario: Your EC2 application is experiencing 90% CPU utilization with slow response times. What's your troubleshooting approach?**
    - Steps:
      1. Check CloudWatch metrics (CPU, Memory, Disk I/O, Network)
      2. SSH into instance and check: `top`, `ps aux`, disk space
      3. Review application logs
      4. Check if CPU throttling is occurring
      5. Solutions:
         - Upgrade instance type (vertical scaling)
         - Add more instances (horizontal scaling with Auto Scaling)
         - Optimize application code
         - Use caching (ElastiCache)
         - Offload processing (SQS, Lambda)

13. **How do you monitor and troubleshoot networking issues on EC2?**
    - Use VPC Flow Logs to analyze traffic patterns
    - Check Security Group and NACL rules
    - Use `mtr`, `traceroute`, `ping` for connectivity
    - Monitor with CloudWatch metrics
    - Check route tables in VPC
    - Use AWS Systems Manager Session Manager for secure access
    - Review ENI settings and elastic IPs

14. **You need to migrate 100 workloads from on-premises to EC2. Design a migration strategy.**
    - Assessment Phase: Use AWS Migration Evaluator
    - Rehost (Lift & Shift): AWS DataSync, AWS SMS
    - Replatform: Update OS/middleware but same application
    - Refactor: Containerize or serverless
    - Test phase: AWS Application Discovery Service
    - Cutover: Use Route 53 for DNS switching
    - Validation: Monitor and optimize post-migration

### Auto Scaling & Load Balancing
15. **Scenario: You have a web app with variable traffic (peaks at 10x baseline). Design the scaling approach.**
    - Create Auto Scaling Group with:
      - Min: 2 instances (high availability)
      - Desired: Based on traffic history
      - Max: Cost limit consideration
    - Scaling Policies:
      - Target Tracking: Maintain CPU at 70%
      - Step Scaling: Aggressive scale for traffic spikes
      - Scheduled Scaling: For known patterns
    - Use Application Load Balancer with health checks
    - Implement connection draining
    - Use CloudWatch alarms

16. **How do you ensure graceful shutdown of EC2 instances during scale-down?**
    - Set termination policy in ASG: Oldest Launch Template, Default
    - Configure connection draining timeout (300-3900 seconds)
    - Implement SIGTERM handlers in application
    - Use lifecycle hooks for cleanup tasks
    - Drain long-running connections before termination

### Cost Optimization
17. **Scenario: Your EC2 costs increased 3x without new deployments. How do you investigate and reduce costs?**
    - Use Cost Explorer to identify expensive instances
    - Check for orphaned resources (stopped instances, unused volumes)
    - Optimize instance types (use right-sizing recommendations)
    - Switch to Spot Instances for non-critical workloads
    - Use Reserved Instances for baseline workloads
    - Implement Savings Plans
    - Use Auto Scaling to match demand
    - Review data transfer costs

---

## 4. Best Practices & Optimization

18. **What's the best way to backup EC2 instances?**
    - Use AWS Backup for automatic snapshots
    - Create AMIs for application-level backups
    - Use EBS snapshots with lifecycle policies
    - Store snapshots in different regions for DR
    - Document backup schedule and retention
    - Test restore process regularly

19. **How do you implement disaster recovery for EC2?**
    - **RPO (Recovery Point Objective)**: Regular snapshots/backups
    - **RTO (Recovery Time Objective)**:
      - Pilot light: Keep minimal standby capacity
      - Warm standby: Scale-up ready infrastructure
      - Hot standby: Full capacity ready
    - Use Route 53 with health checks for failover
    - Keep AMIs updated in DR region
    - Document and test DR procedures

20. **What are EC2 lifecycle hooks and when to use them?**
    - Allow 15-30 min for graceful shutdown
    - Use for database checkpoints, log uploads, connection draining
    - Send SNS notifications to admin
    - Example: ASG lifecycle hook → SNS → Lambda for cleanup

---

## 5. Real-World Scenarios & Tricky Questions

21. **Scenario: You receive an alert that an instance has been compromised. Walk through your response plan.**
    - Immediate:
      1. Isolate instance: Change security group (no inbound/outbound)
      2. Take EBS snapshot for forensics
      3. Create AMI for investigation
    - Investigation:
      - Review CloudTrail logs
      - Check VPC Flow Logs
      - Analyze system logs from instance
      - Check for unauthorized SSH keys
    - Recovery:
      - Patch vulnerabilities
      - Create new AMI
      - Launch fresh instances
      - Update security baselines
      - Document incident

22. **Explain the "split-brain" scenario in multi-region EC2 setup and how to prevent it.**
    - Issue: Two regions process the same request independently
    - Solutions:
      - Use Route 53 with active-passive failover
      - Implement distributed locking (DynamoDB)
      - Use SQS for idempotent processing
      - Database replication with primary/secondary
      - Document failover procedures

23. **You have a 50 GB database running on EC2 with high I/O. What are your options?**
    - Upgrade to io2 EBS volume (high IOPS)
    - Use EBS-optimized instances for guaranteed bandwidth
    - Move to RDS or DynamoDB (managed)
    - Implement read replicas if applicable
    - Use ElastiCache for frequently accessed data
    - Optimize query patterns

24. **What happens if you stop vs terminate an EC2 instance?**
    - **Stop**: EBS volumes retained, instance charges pause, elastic IP retained, can restart
    - **Terminate**: EBS volumes deleted (unless delete on termination=false), instance charges stop, elastic IP released
    - **Implication**: For long-term, stopping is cheaper; for temporary workloads, terminating is better

25. **Scenario: How do you handle a "rolling" deployment with zero downtime?**
    - Use Auto Scaling Group with ALB
    - Create new Launch Template with updated AMI
    - Set min healthy percentage to 100%
    - Update ASG with new template
    - ASG replaces instances one by one
    - ALB removes unhealthy instances during update
    - Monitored with CloudWatch alarms

---

## 6. Comparative Questions

26. **EC2 vs Lambda - when to use each?**
    - **EC2**: Long-running apps, stateful workloads, complex OS requirements
    - **Lambda**: Event-driven, short-living tasks, microservices, no server management

27. **Single Large Instance vs Multiple Small Instances?**
    - **Large**: Simpler management, but single point of failure
    - **Small**: HA, fault tolerance, easier scaling, better cost optimization with spot instances

28. **EBS Volume Types: gp2 vs gp3 vs io1 vs io2?**
    - **gp2**: General purpose, 100-16,000 IOPS, burstable
    - **gp3**: Baseline 3,000 IOPS, up to 16,000, independent scaling
    - **io1**: Consistent 100-64,000 IOPS, provisioned
    - **io2**: Higher durability, 100-64,000 IOPS, block express

---

## 7. Hands-On Coding Questions

29. **Write a Python script to list all running EC2 instances in your account and their current CPU utilization.**
    ```python
    import boto3
    from datetime import datetime, timedelta

    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')

    # List all running instances
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']

            # Get CPU utilization
            cpu_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(hours=1),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )

            avg_cpu = cpu_response['Datapoints'][-1]['Average'] if cpu_response['Datapoints'] else 0
            print(f"{instance_id}: CPU Utilization = {avg_cpu:.2f}%")
    ```

30. **Write a Lambda function to automatically stop EC2 instances tagged with 'auto-stop=true' during off-hours.**
    ```python
    import boto3
    import json
    from datetime import datetime

    ec2 = boto3.client('ec2')

    def lambda_handler(event, context):
        # Define off-hours: 6 PM to 6 AM
        current_hour = datetime.now().hour
        is_off_hours = current_hour >= 18 or current_hour < 6

        if not is_off_hours:
            return {'statusCode': 200, 'body': 'Within business hours'}

        # Find instances with auto-stop tag
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:auto-stop', 'Values': ['true']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        instances_to_stop = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances_to_stop.append(instance['InstanceId'])

        if instances_to_stop:
            ec2.stop_instances(InstanceIds=instances_to_stop)
            return {
                'statusCode': 200,
                'body': f"Stopped {len(instances_to_stop)} instances"
            }

        return {'statusCode': 200, 'body': 'No instances to stop'}
    ```

---

## Tips for Interview Success

- **Prepare practical examples**: Be ready to explain real deployments you've worked on
- **Know the trade-offs**: Cost vs Performance, Availability vs Complexity
- **Understand AWS best practices**: HA, security, cost optimization from AWS Well-Architected Framework
- **Practice with hands-on**: Build small projects using EC2
- **Master Security Groups**: Can't separate from EC2 understanding
- **Know VPC basics**: EC2 lives within VPC, understand networking
- **Understand Auto Scaling deeply**: Real-world requirement for scalable apps

