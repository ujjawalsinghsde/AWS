"""
AWS Redshift - Boto3 Operations
Document: Redshift/redshift_operations.py

This module provides practical boto3 examples for common Redshift operations.
"""

import boto3
import json
import time
from datetime import datetime, timedelta

# Initialize Redshift and related clients
redshift_client = boto3.client('redshift', region_name='us-east-1')
redshift_data_client = boto3.client('redshift-data', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
secretsmanager_client = boto3.client('secretsmanager', region_name='us-east-1')


# ============================================================================
# 1. CLUSTER CREATION & MANAGEMENT
# ============================================================================

def create_development_cluster():
    """Create a development Redshift cluster (single node)"""
    try:
        response = redshift_client.create_cluster(
            ClusterIdentifier='dev-warehouse',
            NodeType='ra3.4xl',
            NumberOfNodes=1,  # Single node for dev
            DBName='analytics',
            MasterUsername='admin',
            MasterUserPassword='DevPassword123!@#',
            Port=5439,
            PubliclyAccessible=False,
            BackupRetentionPeriod=7,  # 1 week
            Tags=[
                {'Key': 'Environment', 'Value': 'development'},
                {'Key': 'Application', 'Value': 'analytics'}
            ]
        )
        print(f"✓ Development cluster created: {response['Cluster']['ClusterIdentifier']}")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error creating cluster: {e}")
        return None


def create_production_cluster():
    """Create a production Redshift cluster with all best practices"""
    try:
        response = redshift_client.create_cluster(
            # Cluster Identity
            ClusterIdentifier='prod-warehouse',
            ClusterType='multi-node',
            NodeType='ra3.4xl',
            NumberOfNodes=3,  # Multi-node for production

            # Database Configuration
            DBName='analytics',
            MasterUsername='admin',
            MasterUserPassword='ProdPassword123!@#SecureEnough',

            # Network Configuration
            Port=5439,
            PubliclyAccessible=False,
            VpcSecurityGroupIds=['sg-12345678'],
            ClusterSecurityGroups=['default'],

            # Backup Configuration
            BackupRetentionPeriod=35,  # Maximum retention
            PreferredBackupWindow='03:00-04:00',
            PreferredMaintenanceWindow='sun:04:00-sun:05:00',

            # Encryption Configuration
            Encrypted=True,
            KmsKeyId='arn:aws:kms:us-east-1:123456789:key/12345678-1234-1234-1234-123456789012',

            # Enhanced Monitoring
            EnhancedVpcRouting=True,

            # Tagging
            Tags=[
                {'Key': 'Environment', 'Value': 'production'},
                {'Key': 'Application', 'Value': 'analytics'},
                {'Key': 'CostCenter', 'Value': '12345'},
                {'Key': 'BackupRequired', 'Value': 'true'}
            ]
        )
        print(f"✓ Production cluster created: {response['Cluster']['ClusterIdentifier']}")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error creating production cluster: {e}")
        return None


def get_cluster_info(cluster_id):
    """Get detailed information about a cluster"""
    try:
        response = redshift_client.describe_clusters(
            ClusterIdentifier=cluster_id
        )
        cluster = response['Clusters'][0]

        info = {
            'ClusterIdentifier': cluster['ClusterIdentifier'],
            'Status': cluster['ClusterStatus'],
            'NodeType': cluster['NodeType'],
            'NumberOfNodes': cluster['NumberOfNodes'],
            'Endpoint': cluster.get('Endpoint', {}).get('Address'),
            'Port': cluster.get('Endpoint', {}).get('Port'),
            'DBName': cluster['DBName'],
            'MasterUsername': cluster['MasterUsername'],
            'AvailabilityZone': cluster['AvailabilityZone'],
            'CreateTime': str(cluster['CreateTime']),
            'Encrypted': cluster['Encrypted'],
            'VpcId': cluster.get('VpcId'),
            'MultiAZ': cluster.get('MultiAZ', False)
        }

        print(f"✓ Cluster Info for {cluster_id}:")
        print(json.dumps(info, indent=2))
        return cluster
    except Exception as e:
        print(f"✗ Error getting cluster info: {e}")
        return None


def list_all_clusters():
    """List all Redshift clusters"""
    try:
        response = redshift_client.describe_clusters()
        clusters = response['Clusters']

        print(f"✓ Found {len(clusters)} cluster(s):")
        for cluster in clusters:
            print(f"  - {cluster['ClusterIdentifier']}: {cluster['ClusterStatus']} ({cluster['NodeType']} x{cluster['NumberOfNodes']})")

        return clusters
    except Exception as e:
        print(f"✗ Error listing clusters: {e}")
        return []


def modify_cluster_nodes(cluster_id, new_node_count):
    """Modify cluster node count (horizontal scaling)"""
    try:
        response = redshift_client.modify_cluster(
            ClusterIdentifier=cluster_id,
            NumberOfNodes=new_node_count,
            ClusterType='multi-node'
        )

        print(f"✓ Cluster {cluster_id} modification initiated")
        print(f"  Scaling to {new_node_count} nodes")
        print(f"  Current status: {response['Cluster']['ClusterStatus']}")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error modifying cluster: {e}")
        return None


def modify_cluster_node_type(cluster_id, new_node_type):
    """Modify cluster node type (vertical scaling)"""
    try:
        response = redshift_client.modify_cluster(
            ClusterIdentifier=cluster_id,
            NodeType=new_node_type
        )

        print(f"✓ Node type modification initiated")
        print(f"  New node type: {new_node_type}")
        print(f"  Current status: {response['Cluster']['ClusterStatus']}")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error modifying node type: {e}")
        return None


def delete_cluster(cluster_id, skip_final_snapshot=False):
    """Delete a Redshift cluster"""
    try:
        response = redshift_client.delete_cluster(
            ClusterIdentifier=cluster_id,
            SkipFinalClusterSnapshot=skip_final_snapshot
        )

        print(f"✓ Cluster {cluster_id} deletion initiated")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error deleting cluster: {e}")
        return None


# ============================================================================
# 2. SNAPSHOT MANAGEMENT
# ============================================================================

def create_cluster_snapshot(cluster_id, snapshot_id):
    """Create a manual snapshot of a cluster"""
    try:
        response = redshift_client.create_cluster_snapshot(
            SnapshotIdentifier=snapshot_id,
            ClusterIdentifier=cluster_id,
            Tags=[
                {'Key': 'BackupType', 'Value': 'manual'},
                {'Key': 'Date', 'Value': datetime.now().isoformat()}
            ]
        )

        print(f"✓ Snapshot created: {snapshot_id}")
        print(f"  Status: {response['Snapshot']['Status']}")
        return response['Snapshot']
    except Exception as e:
        print(f"✗ Error creating snapshot: {e}")
        return None


def list_cluster_snapshots(cluster_id):
    """List all snapshots for a cluster"""
    try:
        response = redshift_client.describe_cluster_snapshots(
            ClusterIdentifier=cluster_id
        )

        snapshots = response['Snapshots']
        print(f"✓ Found {len(snapshots)} snapshot(s) for {cluster_id}:")
        for snap in snapshots:
            size_mb = snap.get('TotalBackupSizeInMegaBytes', 0)
            print(f"  - {snap['SnapshotIdentifier']}: {snap['Status']} ({size_mb}MB)")

        return snapshots
    except Exception as e:
        print(f"✗ Error listing snapshots: {e}")
        return []


def restore_from_snapshot(snapshot_id, new_cluster_id):
    """Restore a cluster from a snapshot"""
    try:
        response = redshift_client.restore_from_cluster_snapshot(
            ClusterIdentifier=new_cluster_id,
            SnapshotIdentifier=snapshot_id,
            NodeType='ra3.4xl'  # Can be different from original
        )

        print(f"✓ Restore initiated")
        print(f"  Snapshot: {snapshot_id}")
        print(f"  New cluster: {new_cluster_id}")
        return response['Cluster']
    except Exception as e:
        print(f"✗ Error restoring from snapshot: {e}")
        return None


def copy_cluster_snapshot_to_region(source_snapshot_id, target_snapshot_id, target_region):
    """Copy snapshot to another region (disaster recovery)"""
    try:
        response = redshift_client.copy_cluster_snapshot(
            SourceSnapshotIdentifier=source_snapshot_id,
            TargetSnapshotIdentifier=target_snapshot_id,
            SourceRegion='us-east-1',
            TargetRegion=target_region
        )

        print(f"✓ Snapshot copy initiated")
        print(f"  From: {source_snapshot_id} (us-east-1)")
        print(f"  To: {target_snapshot_id} ({target_region})")
        return response['Snapshot']
    except Exception as e:
        print(f"✗ Error copying snapshot: {e}")
        return None


# ============================================================================
# 3. QUERY EXECUTION (Redshift Data API)
# ============================================================================

def execute_query(cluster_id, database, sql_query, secret_arn=None):
    """Execute a query using Redshift Data API"""
    try:
        params = {
            'ClusterIdentifier': cluster_id,
            'Database': database,
            'Sql': sql_query
        }

        # Optional: Use secret for credentials
        if secret_arn:
            params['SecretArn'] = secret_arn
        else:
            params['DbUser'] = 'admin'  # Or use temp credentials

        response = redshift_data_client.execute_statement(**params)
        statement_id = response['Id']

        print(f"✓ Query submitted")
        print(f"  Statement ID: {statement_id}")
        print(f"  Query: {sql_query[:80]}...")
        return statement_id
    except Exception as e:
        print(f"✗ Error executing query: {e}")
        return None


def get_query_status(statement_id):
    """Check status of a query"""
    try:
        response = redshift_data_client.describe_statement(Id=statement_id)

        status = {
            'StatementId': statement_id,
            'Status': response['Status'],
            'QueryExecutionTime': response.get('QueryExecutionTime', 0),
            'QueryString': response.get('QueryString', '')[:100],
            'Error': response.get('Error', '')
        }

        print(f"✓ Query Status:")
        print(json.dumps(status, indent=2))
        return response
    except Exception as e:
        print(f"✗ Error getting query status: {e}")
        return None


def wait_for_query_completion(statement_id, max_wait_seconds=300):
    """Wait for query to complete"""
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        response = redshift_data_client.describe_statement(Id=statement_id)
        status = response['Status']

        if status in ['FINISHED', 'FAILED', 'ABORTED']:
            print(f"✓ Query completed with status: {status}")
            return response
        else:
            elapsed = int(time.time() - start_time)
            print(f"  Waiting... ({elapsed}s) Status: {status}")
            time.sleep(5)

    print(f"✗ Query timed out after {max_wait_seconds} seconds")
    return None


def get_query_results(statement_id):
    """Get results from a completed query"""
    try:
        response = redshift_data_client.get_statement_result(Id=statement_id)

        records = response['Records']
        print(f"✓ Retrieved {len(records)} record(s)")

        # Print results
        for i, record in enumerate(records[:10]):  # First 10 rows
            print(f"  Row {i}: {record}")

        if len(records) > 10:
            print(f"  ... and {len(records) - 10} more rows")

        return records
    except Exception as e:
        print(f"✗ Error getting results: {e}")
        return []


def execute_and_get_results(cluster_id, database, sql_query):
    """Execute query and get results (combined operation)"""
    # Submit query
    statement_id = execute_query(cluster_id, database, sql_query)

    if not statement_id:
        return None

    # Wait for completion
    result = wait_for_query_completion(statement_id)

    if not result or result['Status'] != 'FINISHED':
        return None

    # Get results
    records = get_query_results(statement_id)
    return records


# ============================================================================
# 4. TABLE AND SCHEMA OPERATIONS
# ============================================================================

def create_table_with_distribution_key():
    """SQL to create a table with optimal distribution key"""
    sql = """
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER DISTKEY,
        customer_id INTEGER,
        product_id INTEGER,
        order_date DATE SORTKEY,
        amount DECIMAL(10, 2),
        status VARCHAR(50)
    );
    """
    print("✓ SQL for creating orders table with DISTKEY and SORTKEY:")
    print(sql)
    return sql


def create_external_schema_spectrum():
    """SQL to create external schema for Redshift Spectrum"""
    sql = """
    CREATE EXTERNAL SCHEMA spectrum_schema
    FROM DATA CATALOG
    DATABASE 'spectrum_db'
    IAM_ROLE 'arn:aws:iam::123456789:role/SpectrumRole'
    REGION 'us-east-1';

    CREATE EXTERNAL TABLE spectrum_schema.raw_logs (
        log_id INTEGER,
        timestamp TIMESTAMP,
        event VARCHAR(256),
        user_id INTEGER,
        properties VARCHAR(MAX)
    )
    PARTITIONED BY (year INT, month INT, day INT)
    STORED AS PARQUET
    LOCATION 's3://my-logs-bucket/raw/';
    """
    print("✓ SQL for creating external schema and table:")
    print(sql)
    return sql


def get_table_size():
    """SQL to check table sizes"""
    sql = """
    SELECT
        schema,
        table_id,
        "table",
        unsorted_rows,
        size_in_megabytes,
        ROUND(100.0 * unsorted_rows / NULLIF(rows, 0), 2) unsorted_pct
    FROM svv_table_info
    ORDER BY size_in_megabytes DESC
    LIMIT 20;
    """
    print("✓ SQL to check table sizes:")
    print(sql)
    return sql


def get_slow_queries():
    """SQL to identify slow queries"""
    sql = """
    SELECT
        query,
        userid,
        starttime,
        endtime,
        DATEDIFF(seconds, starttime, endtime) duration_seconds,
        querytxt
    FROM stl_query
    WHERE DATEDIFF(seconds, starttime, endtime) > 60
    AND query > 0
    ORDER BY starttime DESC
    LIMIT 20;
    """
    print("✓ SQL to find slow queries:")
    print(sql)
    return sql


# ============================================================================
# 5. DATA LOADING (COPY command examples)
# ============================================================================

def copy_from_s3_parquet():
    """SQL for COPY command from S3 (Parquet format)"""
    sql = """
    COPY orders
    FROM 's3://my-data-bucket/orders/'
    IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
    FORMAT AS PARQUET
    ;
    """
    print("✓ COPY command for Parquet files:")
    print(sql)
    return sql


def copy_from_s3_csv():
    """SQL for COPY command from S3 (CSV format)"""
    sql = """
    COPY customers
    FROM 's3://my-data-bucket/customers/'
    IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
    DELIMITER ','
    IGNOREHEADER 1
    CSV
    NULL AS 'null'
    DATEFORMAT 'YYYY-MM-DD'
    ;
    """
    print("✓ COPY command for CSV files:")
    print(sql)
    return sql


def copy_with_manifest():
    """SQL for COPY command using manifest file"""
    sql = """
    COPY orders
    FROM 's3://my-data-bucket/manifest.json'
    IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
    MANIFEST
    ;
    """
    print("✓ COPY command using manifest:")
    print(sql)
    return sql


def unload_to_s3():
    """SQL to UNLOAD (export) data to S3"""
    sql = """
    UNLOAD (
        SELECT order_id, customer_id, amount, order_date
        FROM orders
        WHERE order_date >= '2024-01-01'
    )
    TO 's3://output-bucket/orders/'
    IAM_ROLE 'arn:aws:iam::123456789:role/RedshiftRole'
    PARQUET
    ENCRYPTED
    ;
    """
    print("✓ UNLOAD command to export data:")
    print(sql)
    return sql


# ============================================================================
# 6. MONITORING & PERFORMANCE
# ============================================================================

def get_cluster_cpu_utilization(cluster_id, hours=1):
    """Get CPU utilization from CloudWatch"""
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='CPUUtilization',
            Dimensions=[
                {'Name': 'ClusterIdentifier', 'Value': cluster_id}
            ],
            StartTime=datetime.utcnow() - timedelta(hours=hours),
            EndTime=datetime.utcnow(),
            Period=300,  # 5 minutes
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        print(f"✓ CPU Utilization for {cluster_id} (last {hours} hour(s)):")
        for point in response['Datapoints']:
            print(f"  {point['Timestamp']}: Avg={point['Average']:.1f}%, Max={point['Maximum']:.1f}%")

        return response['Datapoints']
    except Exception as e:
        print(f"✗ Error getting CPU metrics: {e}")
        return []


def get_cluster_connections(cluster_id, hours=1):
    """Get database connections from CloudWatch"""
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='DatabaseConnections',
            Dimensions=[
                {'Name': 'ClusterIdentifier', 'Value': cluster_id}
            ],
            StartTime=datetime.utcnow() - timedelta(hours=hours),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=['Average']
        )

        print(f"✓ Database Connections for {cluster_id}:")
        for point in response['Datapoints']:
            print(f"  {point['Timestamp']}: {point['Average']:.0f} connections")

        return response['Datapoints']
    except Exception as e:
        print(f"✗ Error getting connections: {e}")
        return []


def create_cloudwatch_alarm(cluster_id):
    """Create CloudWatch alarm for high CPU"""
    try:
        response = cloudwatch_client.put_metric_alarm(
            AlarmName=f'Redshift-HighCPU-{cluster_id}',
            MetricName='CPUUtilization',
            Namespace='AWS/Redshift',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=2,
            Threshold=80.0,
            ComparisonOperator='GreaterThanThreshold',
            Dimensions=[
                {'Name': 'ClusterIdentifier', 'Value': cluster_id}
            ],
            AlarmActions=[
                'arn:aws:sns:us-east-1:123456789:alerts-topic'
            ]
        )

        print(f"✓ Alarm created: Redshift-HighCPU-{cluster_id}")
        return response
    except Exception as e:
        print(f"✗ Error creating alarm: {e}")
        return None


# ============================================================================
# 7. WORKLOAD MANAGEMENT (WLM)
# ============================================================================

def get_wlm_query_stats():
    """SQL to get WLM queue statistics"""
    sql = """
    SELECT
        queue,
        run_minutes,
        exec_seconds,
        query_count,
        avg_run_minutes,
        max_run_minutes
    FROM stl_wlm_query
    WHERE date > CURRENT_DATE - 1
    GROUP BY queue
    ORDER BY queue;
    """
    print("✓ SQL to check WLM queue performance:")
    print(sql)
    return sql


def query_with_queue_priority(statement_id, queue_name):
    """Execute query with specific queue priority"""
    sql = f"""
    SET query_group TO '{queue_name}';
    SELECT * FROM large_table LIMIT 1000;
    RESET query_group;
    """
    print(f"✓ Query SQL with queue priority '{queue_name}':")
    print(sql)
    return sql


# ============================================================================
# 8. MAINTENANCE OPERATIONS
# ============================================================================

def vacuum_and_analyze_table():
    """SQL to vacuum and analyze a table"""
    sql = """
    -- Remove deleted rows and re-sort
    VACUUM sales;

    -- Update table statistics
    ANALYZE sales;

    -- Check compression opportunities
    ANALYZE COMPRESSION sales;
    """
    print("✓ SQL for VACUUM and ANALYZE:")
    print(sql)
    return sql


def check_compression_opportunities():
    """SQL to analyze compression potential"""
    sql = """
    SELECT
        schemaname,
        tablename,
        ROUND(100.0 * encoded_blockwid / NULLIF(blockwidth, 0), 2) compression_ratio,
        blockwid,
        encoded_blockwid,
        blockwidth
    FROM pg_class pc
    JOIN (
        SELECT * FROM stv_tbl_perm
        WHERE id NOT IN (
            SELECT tableid FROM stv_blocklist
            WHERE blocknum = 0
        )
    ) a ON a.id = pc.oid
    WHERE schemaname != 'information_schema'
    AND schemaname != 'pg_catalog'
    ORDER BY compression_ratio DESC;
    """
    print("✓ SQL to check compression opportunities:")
    print(sql)
    return sql


# ============================================================================
# 9. UTILITY FUNCTIONS
# ============================================================================

def run_example_workflow():
    """Run an example workflow"""
    print("=" * 70)
    print("REDSHIFT BOTO3 EXAMPLE WORKFLOW")
    print("=" * 70)

    # Step 1: List clusters
    print("\n[Step 1] Listing all clusters...")
    clusters = list_all_clusters()

    if not clusters:
        print("\n[Step 2] Creating a development cluster...")
        create_development_cluster()
    else:
        cluster_id = clusters[0]['ClusterIdentifier']

        # Step 2: Get cluster info
        print(f"\n[Step 2] Getting info for {cluster_id}...")
        get_cluster_info(cluster_id)

        # Step 3: Create snapshot
        print(f"\n[Step 3] Creating snapshot...")
        snapshot_id = f"{cluster_id}-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        create_cluster_snapshot(cluster_id, snapshot_id)

        # Step 4: Execute query
        print(f"\n[Step 4] Executing test query...")
        sql = "SELECT 1 AS test_value;"
        try:
            statement_id = execute_query(cluster_id, 'dev', sql)
            if statement_id:
                wait_for_query_completion(statement_id)
                get_query_results(statement_id)
        except Exception as e:
            print(f"  (Query execution requires Auth configured: {e})")

        # Step 5: Monitor metrics
        print(f"\n[Step 5] Getting cluster metrics...")
        get_cluster_cpu_utilization(cluster_id, hours=1)

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    # Run example workflow
    run_example_workflow()

    # Or run individual operations:
    # create_development_cluster()
    # list_all_clusters()
    # get_table_size()
    # vacuum_and_analyze_table()
