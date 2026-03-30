"""
AWS RDS (Relational Database Service) - Boto3 Operations
Document: RDS/rds_operations.py

This module provides practical boto3 examples for common RDS operations.
"""

import boto3
import json
from datetime import datetime, timedelta

# Initialize RDS client
rds_client = boto3.client('rds', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')


# ============================================================================
# 1. CREATE RDS INSTANCES
# ============================================================================

def create_dev_db_instance():
    """Create a simple development RDS instance"""
    try:
        response = rds_client.create_db_instance(
            DBInstanceIdentifier='dev-postgres-db',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            EngineVersion='15.3',
            MasterUsername='postgres',
            MasterUserPassword='DevPassword123!',
            AllocatedStorage=20,
            StorageType='gp2',
            PubliclyAccessible=True,
            BackupRetentionPeriod=1,  # Minimal backups
            MultiAZ=False,
            Tags=[
                {'Key': 'Environment', 'Value': 'development'},
                {'Key': 'Application', 'Value': 'learningdb'}
            ]
        )
        print(f"✓ Created DB Instance: {response['DBInstance']['DBInstanceIdentifier']}")
        print(f"  Endpoint: {response['DBInstance'].get('Endpoint', 'Creating...')}")
        return response
    except Exception as e:
        print(f"✗ Error creating instance: {e}")
        return None


def create_production_db_instance():
    """Create a production-grade RDS instance with all best practices"""
    try:
        response = rds_client.create_db_instance(
            # Basic Configuration
            DBInstanceIdentifier='prod-postgres-db',
            DBInstanceClass='db.r5.large',
            Engine='postgres',
            EngineVersion='15.3',

            # Credentials (use AWS Secrets Manager in production)
            MasterUsername='admin',
            MasterUserPassword='ProdSecurePassword123!@#',

            # Storage Configuration
            AllocatedStorage=100,
            StorageType='gp3',
            Iops=3000,
            MaxAllocatedStorage=500,  # Auto-scaling up to 500GB
            StorageEncrypted=True,

            # Backup Configuration
            BackupRetentionPeriod=35,
            PreferredBackupWindow='03:00-04:00',
            PreferredMaintenanceWindow='sun:04:00-sun:05:00',

            # High Availability
            MultiAZ=True,

            # Networking
            PubliclyAccessible=False,
            DBSubnetGroupName='default',
            VpcSecurityGroupIds=['sg-0123456789abcdef0'],

            # Security & Monitoring
            StorageEncrypted=True,
            EnableIAMDatabaseAuthentication=True,
            EnableCloudwatchLogsExports=['postgresql', 'upgrade'],
            EnableEnhancedMonitoring=True,
            MonitoringInterval=60,
            MonitoringRoleArn='arn:aws:iam::123456789:role/RDSMonitoringRole',

            # Performance Insights
            EnablePerformanceInsights=True,
            PerformanceInsightsRetentionPeriod=7,

            # Additional Protection
            DeletionProtection=True,
            CopyTagsToSnapshot=True,

            Tags=[
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'CostCenter', 'Value': 'engineering'},
                {'Key': 'Backup', 'Value': 'critical'}
            ]
        )
        print(f"✓ Created production DB Instance: {response['DBInstance']['DBInstanceIdentifier']}")
        return response
    except Exception as e:
        print(f"✗ Error creating production instance: {e}")
        return None


# ============================================================================
# 2. MANAGE DB INSTANCES
# ============================================================================

def list_db_instances():
    """List all RDS instances in the region"""
    try:
        response = rds_client.describe_db_instances()
        print(f"\n📊 RDS Instances ({len(response['DBInstances'])} total):")
        print("-" * 80)
        for db in response['DBInstances']:
            status = db['DBInstanceStatus']
            engine = db['Engine']
            class_type = db['DBInstanceClass']
            endpoint = db.get('Endpoint', {}).get('Address', 'N/A')
            print(f"  {db['DBInstanceIdentifier']:30} | {engine:10} | {status:10} | {class_type}")
            if endpoint != 'N/A':
                print(f"    └─ Endpoint: {endpoint}")
        return response
    except Exception as e:
        print(f"✗ Error listing instances: {e}")
        return None


def describe_db_instance(db_instance_id):
    """Get detailed information about a specific RDS instance"""
    try:
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_id
        )
        db = response['DBInstances'][0]

        print(f"\n📋 Details for: {db_instance_id}")
        print("-" * 80)
        print(f"  Engine:              {db['Engine']} {db['EngineVersion']}")
        print(f"  Instance Class:      {db['DBInstanceClass']}")
        print(f"  Status:              {db['DBInstanceStatus']}")
        print(f"  Storage:             {db['AllocatedStorage']} GB ({db['StorageType']})")
        print(f"  Multi-AZ:            {db['MultiAZ']}")
        print(f"  Backup Retention:    {db['BackupRetentionPeriod']} days")
        print(f"  Connections:         {db.get('DBInstancePortConnection', 'N/A')}")
        if db.get('Endpoint'):
            print(f"  Endpoint:            {db['Endpoint']['Address']}:{db['Endpoint']['Port']}")
        print(f"  Availability Zone:   {db['AvailabilityZone']}")
        print(f"  Created:             {db['InstanceCreateTime']}")
        return db
    except Exception as e:
        print(f"✗ Error describing instance: {e}")
        return None


def reboot_db_instance(db_instance_id, force_failover=False):
    """Reboot a DB instance (optionally force failover if Multi-AZ)"""
    try:
        response = rds_client.reboot_db_instance(
            DBInstanceIdentifier=db_instance_id,
            ForceFailover=force_failover
        )
        action = "Failover" if force_failover else "Reboot"
        print(f"✓ {action} initiated for: {db_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error rebooting instance: {e}")
        return None


def delete_db_instance(db_instance_id, skip_snapshot=False):
    """Delete a DB instance (optionally create final snapshot)"""
    try:
        params = {
            'DBInstanceIdentifier': db_instance_id,
            'SkipFinalSnapshot': skip_snapshot
        }
        if not skip_snapshot:
            params['FinalDBSnapshotIdentifier'] = f"{db_instance_id}-final-snapshot"

        response = rds_client.delete_db_instance(**params)
        print(f"✓ Delete initiated for: {db_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error deleting instance: {e}")
        return None


# ============================================================================
# 3. SCALING & MODIFICATIONS
# ============================================================================

def modify_instance_class(db_instance_id, new_class, apply_immediately=False):
    """Scale instance to a different instance class"""
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            DBInstanceClass=new_class,
            ApplyImmediately=apply_immediately
        )
        print(f"✓ Scaling initiated to {new_class}")
        return response
    except Exception as e:
        print(f"✗ Error modifying instance: {e}")
        return None


def enable_storage_autoscaling(db_instance_id, max_storage_gb=1000):
    """Enable automatic storage scaling"""
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            MaxAllocatedStorage=max_storage_gb,
            ApplyImmediately=True
        )
        print(f"✓ Storage autoscaling enabled (max: {max_storage_gb} GB)")
        return response
    except Exception as e:
        print(f"✗ Error enabling storage autoscaling: {e}")
        return None


def modify_to_multiaz(db_instance_id):
    """Enable Multi-AZ for high availability"""
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            MultiAZ=True,
            ApplyImmediately=False  # Applied during maintenance window
        )
        print(f"✓ Multi-AZ modification scheduled for: {db_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error enabling Multi-AZ: {e}")
        return None


# ============================================================================
# 4. BACKUPS AND SNAPSHOTS
# ============================================================================

def create_manual_snapshot(db_instance_id, snapshot_id=None):
    """Create a manual snapshot of the database"""
    try:
        if not snapshot_id:
            snapshot_id = f"{db_instance_id}-snapshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        response = rds_client.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceIdentifier=db_instance_id,
            Tags=[
                {'Key': 'Type', 'Value': 'manual'},
                {'Key': 'CreatedDate', 'Value': datetime.now().isoformat()}
            ]
        )
        print(f"✓ Snapshot created: {snapshot_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating snapshot: {e}")
        return None


def list_snapshots(db_instance_id=None):
    """List all snapshots (optionally filtered by DB instance)"""
    try:
        params = {}
        if db_instance_id:
            params['DBInstanceIdentifier'] = db_instance_id

        response = rds_client.describe_db_snapshots(**params)
        print(f"\n📸 Snapshots ({len(response['DBSnapshots'])} total):")
        print("-" * 100)
        for snapshot in response['DBSnapshots']:
            db_id = snapshot['DBInstanceIdentifier']
            snap_id = snapshot['DBSnapshotIdentifier']
            status = snapshot['Status']
            size = snapshot['AllocatedStorage']
            created = snapshot['SnapshotCreateTime']
            print(f"  {snap_id:40} | {db_id:20} | {status:10} | {size}GB | {created}")
        return response
    except Exception as e:
        print(f"✗ Error listing snapshots: {e}")
        return None


def restore_from_snapshot(snapshot_id, new_instance_id):
    """Restore a new DB instance from a snapshot"""
    try:
        response = rds_client.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=new_instance_id,
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceClass='db.t3.micro'  # Can be different from original
        )
        print(f"✓ Restore initiated from snapshot: {snapshot_id}")
        print(f"  New instance: {new_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error restoring from snapshot: {e}")
        return None


def restore_to_point_in_time(source_instance_id, new_instance_id, restore_time=None):
    """Restore to a specific point in time"""
    try:
        params = {
            'SourceDBInstanceIdentifier': source_instance_id,
            'TargetDBInstanceIdentifier': new_instance_id
        }

        if restore_time:
            params['RestoreTime'] = restore_time
        else:
            params['UseLatestRestorableTime'] = True

        response = rds_client.restore_db_instance_to_point_in_time(**params)
        print(f"✓ PITR restore initiated for: {source_instance_id}")
        print(f"  New instance: {new_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error with PITR: {e}")
        return None


def delete_snapshot(snapshot_id):
    """Delete a manual snapshot"""
    try:
        response = rds_client.delete_db_snapshot(
            DBSnapshotIdentifier=snapshot_id
        )
        print(f"✓ Snapshot deleted: {snapshot_id}")
        return response
    except Exception as e:
        print(f"✗ Error deleting snapshot: {e}")
        return None


# ============================================================================
# 5. READ REPLICAS
# ============================================================================

def create_read_replica(source_instance_id, replica_id, region=None):
    """Create a read replica (same region or cross-region)"""
    try:
        params = {
            'DBInstanceIdentifier': replica_id,
            'SourceDBInstanceIdentifier': source_instance_id
        }

        if region:
            params['SourceRegion'] = region

        response = rds_client.create_db_instance_read_replica(**params)
        replica_type = "cross-region" if region else "same-region"
        print(f"✓ {replica_type.upper()} read replica created: {replica_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating read replica: {e}")
        return None


def promote_read_replica(replica_id):
    """Promote a read replica to standalone DB instance"""
    try:
        response = rds_client.promote_read_replica(
            DBInstanceIdentifier=replica_id,
            BackupRetentionPeriod=7  # Now needs its own backups
        )
        print(f"✓ Read replica promoted to standalone: {replica_id}")
        return response
    except Exception as e:
        print(f"✗ Error promoting read replica: {e}")
        return None


# ============================================================================
# 6. MONITORING & METRICS
# ============================================================================

def get_cpu_metrics(db_instance_id, hours=1):
    """Get CPU utilization metrics for a DB instance"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='CPUUtilization',
            Dimensions=[
                {'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5-minute intervals
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        print(f"\n📊 CPU Metrics for {db_instance_id} (last {hours} hour(s)):")
        print("-" * 80)
        for dp in sorted(response['Datapoints'], key=lambda x: x['Timestamp']):
            print(f"  {dp['Timestamp']} | Avg: {dp['Average']:.2f}% | Max: {dp['Maximum']:.2f}%")

        return response
    except Exception as e:
        print(f"✗ Error getting metrics: {e}")
        return None


def get_database_connections(db_instance_id, hours=1):
    """Get active database connections metric"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='DatabaseConnections',
            Dimensions=[
                {'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum']
        )

        print(f"\n📊 Database Connections for {db_instance_id}:")
        print("-" * 80)
        for dp in sorted(response['Datapoints'], key=lambda x: x['Timestamp']):
            print(f"  {dp['Timestamp']} | Avg: {dp['Average']:.0f} | Max: {dp['Maximum']:.0f}")

        return response
    except Exception as e:
        print(f"✗ Error getting connections: {e}")
        return None


def get_read_latency(db_instance_id, hours=1):
    """Get read latency metric (in milliseconds)"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='ReadLatency',
            Dimensions=[
                {'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum']
        )

        print(f"\n📊 Read Latency for {db_instance_id}:")
        print("-" * 80)
        for dp in sorted(response['Datapoints'], key=lambda x: x['Timestamp']):
            print(f"  {dp['Timestamp']} | Avg: {dp['Average']:.2f}ms | Max: {dp['Maximum']:.2f}ms")

        return response
    except Exception as e:
        print(f"✗ Error getting latency: {e}")
        return None


# ============================================================================
# 7. SECURITY & AUTHENTICATION
# ============================================================================

def enable_iam_auth(db_instance_id):
    """Enable IAM database authentication"""
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            EnableIAMDatabaseAuthentication=True,
            ApplyImmediately=True
        )
        print(f"✓ IAM authentication enabled for: {db_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error enabling IAM auth: {e}")
        return None


def generate_auth_token(db_endpoint, db_port, db_user):
    """Generate an IAM database authentication token"""
    try:
        token = rds_client.generate_db_auth_token(
            DBHostname=db_endpoint,
            Port=db_port,
            DBUser=db_user
        )
        print(f"✓ Auth token generated for user: {db_user}")
        print(f"  Token valid for 15 minutes")
        return token
    except Exception as e:
        print(f"✗ Error generating token: {e}")
        return None


def enable_encryption(db_instance_id, kms_key_id=None):
    """Enable encryption at rest (for new snapshots/instances)"""
    try:
        # Note: Cannot enable encryption on existing instance
        # Must restore from snapshot with encryption enabled
        print("⚠️  Cannot enable encryption on existing instance")
        print("   Solution: Create encrypted backup and restore")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def modify_security_groups(db_instance_id, security_group_ids):
    """Update security groups for a DB instance"""
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            VpcSecurityGroupIds=security_group_ids,
            ApplyImmediately=True
        )
        print(f"✓ Security groups updated for: {db_instance_id}")
        return response
    except Exception as e:
        print(f"✗ Error modifying security groups: {e}")
        return None


# ============================================================================
# 8. MAINTENANCE & PATCHING
# ============================================================================

def get_pending_maintenance(db_instance_id):
    """Check for pending maintenance actions"""
    try:
        response = rds_client.describe_pending_maintenance_actions()

        for action in response.get('PendingMaintenanceActions', []):
            resource = action.get('ResourceIdentifier', '').split(':')[-1]
            if resource == db_instance_id:
                print(f"✓ Pending maintenance for: {db_instance_id}")
                for item in action.get('PendingMaintenanceActionDetails', []):
                    print(f"  - {item['Action']}")
                    print(f"    Auto-applied: {item.get('AutoAppliedAfterDate', 'N/A')}")
                return action

        print(f"✓ No pending maintenance for: {db_instance_id}")
        return None
    except Exception as e:
        print(f"✗ Error checking maintenance: {e}")
        return None


def modify_maintenance_window(db_instance_id, day_of_week, start_hour):
    """Modify maintenance window"""
    try:
        # Format: ddd:hh:mm-ddd:hh:mm (UTC)
        maintenance_window = f"{day_of_week}:{start_hour:02d}:00-{day_of_week}:{start_hour+1:02d}:00"

        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            PreferredMaintenanceWindow=maintenance_window,
            ApplyImmediately=False
        )
        print(f"✓ Maintenance window updated to: {maintenance_window}")
        return response
    except Exception as e:
        print(f"✗ Error modifying maintenance window: {e}")
        return None


# ============================================================================
# 9. RDS PROXY OPERATIONS
# ============================================================================

def list_rds_proxies():
    """List all RDS proxies"""
    try:
        response = rds_client.describe_db_proxies()
        print(f"\n🔌 RDS Proxies ({len(response['DBProxies'])} total):")
        print("-" * 80)
        for proxy in response['DBProxies']:
            print(f"  {proxy['DBProxyName']:30} | Status: {proxy['Status']}")
        return response
    except Exception as e:
        print(f"✗ Error listing proxies: {e}")
        return None


# ============================================================================
# 10. EXPORT & IMPORT
# ============================================================================

def export_snapshot_to_s3(snapshot_id, s3_bucket, s3_prefix, iam_role_arn):
    """Export DB snapshot to Parquet files in S3"""
    try:
        response = rds_client.start_export_task(
            ExportTaskIdentifier=f"export-{snapshot_id}",
            SourceArn=f"arn:aws:rds:us-east-1:123456789:snapshot:{snapshot_id}",
            S3BucketName=s3_bucket,
            S3Prefix=s3_prefix,
            IamRoleArn=iam_role_arn,
            ExportOnly=[],  # Export all tables; can specify specific tables
            ExportFormat='PARQUET'
        )
        print(f"✓ Export task started: {snapshot_id} → s3://{s3_bucket}/{s3_prefix}")
        return response
    except Exception as e:
        print(f"✗ Error exporting snapshot: {e}")
        return None


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AWS RDS Boto3 Operations Examples")
    print("=" * 80)

    # Example 1: Create a dev instance
    print("\n[1] Creating Development Instance...")
    create_dev_db_instance()

    # Example 2: List instances
    print("\n[2] Listing RDS Instances...")
    list_db_instances()

    # Example 3: Get metrics
    print("\n[3] Getting CPU Metrics...")
    # get_cpu_metrics('dev-postgres-db', hours=1)

    print("\n✓ Examples completed!")
