"""
AWS Glue Operations - Practical boto3 Examples
Covers all common Glue operations for development and production use
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time


class GlueOperations:
    """AWS Glue operations helper class"""

    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize Glue client"""
        self.glue = boto3.client('glue', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)

    # ============================================================================
    # CRAWLER OPERATIONS
    # ============================================================================

    def create_crawler(
        self,
        name: str,
        role_arn: str,
        s3_path: str,
        database_name: str,
        table_prefix: str = '',
        schedule_expression: Optional[str] = None,
        exclusions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Glue crawler for S3 data

        Args:
            name: Crawler name
            role_arn: IAM role ARN for crawler execution
            s3_path: S3 path to crawl (e.g., 's3://bucket/data/')
            database_name: Glue catalog database
            table_prefix: Prefix for created tables
            schedule_expression: Cron expression for scheduling
            exclusions: List of patterns to exclude

        Returns:
            Crawler creation response
        """
        crawler_config = {
            'Name': name,
            'Role': role_arn,
            'DatabaseName': database_name,
            'Targets': {
                'S3Targets': [
                    {
                        'Path': s3_path,
                        'Exclusions': exclusions or []
                    }
                ]
            },
            'SchemaChangePolicy': {
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            },
            'TablePrefix': table_prefix,
            'RecrawlPolicy': {
                'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'  # Faster for large datasets
            }
        }

        if schedule_expression:
            crawler_config['Schedule'] = {
                'ScheduleExpression': schedule_expression
            }

        try:
            response = self.glue.create_crawler(**crawler_config)
            print(f"✓ Crawler '{name}' created successfully")
            return response
        except self.glue.exceptions.AlreadyExistsException:
            print(f"⚠ Crawler '{name}' already exists")
            return {'Crawler': {'Name': name}}

    def create_jdbc_crawler(
        self,
        name: str,
        role_arn: str,
        connection_name: str,
        database_name: str,
        table_prefix: str = 'jdbc_'
    ) -> Dict[str, Any]:
        """
        Create a crawler for JDBC sources (RDS, etc.)

        Args:
            name: Crawler name
            role_arn: IAM role ARN
            connection_name: Glue connection name
            database_name: Glue catalog database
            table_prefix: Prefix for created tables

        Returns:
            Crawler creation response
        """
        response = self.glue.create_crawler(
            Name=name,
            Role=role_arn,
            DatabaseName=database_name,
            Targets={
                'JdbcTargets': [
                    {
                        'ConnectionName': connection_name,
                        'Path': '%',  # All tables in database
                        'Exclusions': []
                    }
                ]
            },
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            },
            TablePrefix=table_prefix
        )
        print(f"✓ JDBC Crawler '{name}' created")
        return response

    def start_crawler(self, crawler_name: str) -> Dict[str, Any]:
        """
        Start a crawler run

        Args:
            crawler_name: Name of crawler to start

        Returns:
            Response from start_crawler
        """
        response = self.glue.start_crawler(Name=crawler_name)
        print(f"✓ Crawler '{crawler_name}' started")
        return response

    def get_crawler_status(self, crawler_name: str) -> Dict[str, Any]:
        """
        Get crawler status and metrics

        Args:
            crawler_name: Name of crawler

        Returns:
            Crawler details and metrics
        """
        crawler = self.glue.get_crawler(Name=crawler_name)['Crawler']
        metrics = self.glue.get_crawler_metrics(
            CrawlerNameList=[crawler_name],
            MaxResults=1
        )['CrawlerMetricsList'][0] if crawler_name else {}

        return {
            'name': crawler['Name'],
            'state': crawler['State'],
            'last_crawl': crawler.get('LastCrawl'),
            'tables_created': metrics.get('TablesCreated', 0),
            'tables_updated': metrics.get('TablesUpdated', 0),
            'tables_deleted': metrics.get('TablesDeleted', 0)
        }

    def wait_for_crawler(self, crawler_name: str, max_wait_seconds: int = 600):
        """
        Wait for crawler to complete

        Args:
            crawler_name: Name of crawler
            max_wait_seconds: Maximum seconds to wait
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            status = self.get_crawler_status(crawler_name)
            print(f"Crawler state: {status['state']}")

            if status['state'] == 'READY':
                print(f"✓ Crawler finished. Tables: created={status['tables_created']}, "
                      f"updated={status['tables_updated']}, deleted={status['tables_deleted']}")
                return True

            time.sleep(5)

        raise TimeoutError(f"Crawler did not complete within {max_wait_seconds} seconds")

    def list_crawlers(self) -> List[str]:
        """List all crawlers in account"""
        response = self.glue.list_crawlers()
        return response.get('CrawlerNames', [])

    def delete_crawler(self, crawler_name: str) -> Dict[str, Any]:
        """Delete a crawler"""
        response = self.glue.delete_crawler(Name=crawler_name)
        print(f"✓ Crawler '{crawler_name}' deleted")
        return response

    # ============================================================================
    # GLUE JOB OPERATIONS
    # ============================================================================

    def create_spark_job(
        self,
        name: str,
        role_arn: str,
        script_location: str,
        num_workers: int = 10,
        worker_type: str = 'G.2X',
        timeout_minutes: int = 2880,
        glue_version: str = '3.0'
    ) -> Dict[str, Any]:
        """
        Create a Spark ETL job

        Args:
            name: Job name
            role_arn: IAM role ARN
            script_location: S3 path to job script
            num_workers: Number of workers
            worker_type: Worker type (G.1X, G.2X, Z.2X)
            timeout_minutes: Job timeout
            glue_version: Glue runtime version

        Returns:
            Job creation response
        """
        response = self.glue.create_job(
            Name=name,
            Role=role_arn,
            Command={
                'Name': 'glueetl',
                'ScriptLocation': script_location,
                'PythonVersion': '3'
            },
            DefaultArguments={
                '--job-bookmark-option': 'job-bookmark-enabled',
                '--enable-metrics': 'true',
                '--enable-glue-datacatalog': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': f's3://aws-glue-logs/{name}/'
            },
            ExecutionProperty={
                'MaxConcurrentRuns': 5
            },
            MaxRetries=1,
            Timeout=timeout_minutes,
            GlueVersion=glue_version,
            NumberOfWorkers=num_workers,
            WorkerType=worker_type,
            Tags={
                'Environment': 'production',
                'ManagedBy': 'terraform'
            }
        )
        print(f"✓ Spark job '{name}' created")
        return response

    def create_python_shell_job(
        self,
        name: str,
        role_arn: str,
        script_location: str,
        python_version: str = '3.9'
    ) -> Dict[str, Any]:
        """
        Create a Python Shell job (no Spark, simpler workloads)

        Args:
            name: Job name
            role_arn: IAM role ARN
            script_location: S3 path to job script
            python_version: Python version

        Returns:
            Job creation response
        """
        response = self.glue.create_job(
            Name=name,
            Role=role_arn,
            Command={
                'Name': 'pythonshell',
                'ScriptLocation': script_location,
                'PythonVersion': python_version
            },
            DefaultArguments={
                '--enable-metrics': 'true'
            },
            MaxRetries=1,
            Timeout=300,
            GlueVersion='1.0',
            WorkerType='G.1X'
        )
        print(f"✓ Python Shell job '{name}' created")
        return response

    def start_job_run(
        self,
        job_name: str,
        arguments: Optional[Dict[str, str]] = None,
        security_configuration: Optional[str] = None
    ) -> str:
        """
        Start a job run

        Args:
            job_name: Name of job to run
            arguments: Job parameters (e.g., {'--output_path': 's3://bucket/out/'})
            security_configuration: Security config name

        Returns:
            Job run ID
        """
        params = {
            'JobName': job_name,
            'Arguments': arguments or {}
        }

        if security_configuration:
            params['SecurityConfiguration'] = security_configuration

        response = self.glue.start_job_run(**params)
        job_run_id = response['JobRunId']

        print(f"✓ Job '{job_name}' started with run ID: {job_run_id}")
        return job_run_id

    def get_job_run_status(self, job_name: str, run_id: str) -> Dict[str, Any]:
        """
        Get job run status and details

        Args:
            job_name: Job name
            run_id: Job run ID

        Returns:
            Job run details
        """
        response = self.glue.get_job_run(
            JobName=job_name,
            RunId=run_id
        )

        run = response['JobRun']
        return {
            'run_id': run['Id'],
            'state': run['JobRunState'],
            'error_message': run.get('ErrorMessage', ''),
            'execution_time': run.get('ExecutionTime', 0),
            'start_time': run.get('StartedOn', {}).isoformat() if 'StartedOn' in run else None,
            'end_time': run.get('CompletedOn', {}).isoformat() if 'CompletedOn' in run else None,
            'dpu_seconds': run.get('DPUSeconds', 0)
        }

    def wait_for_job_completion(
        self,
        job_name: str,
        run_id: str,
        max_wait_seconds: int = 3600
    ) -> bool:
        """
        Wait for job to complete

        Args:
            job_name: Job name
            run_id: Job run ID
            max_wait_seconds: Maximum wait time

        Returns:
            True if succeeded, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            status = self.get_job_run_status(job_name, run_id)
            print(f"Job state: {status['state']}")

            if status['state'] == 'SUCCEEDED':
                print(f"✓ Job completed successfully")
                print(f"  Execution time: {status['execution_time']}s")
                print(f"  DPU-Seconds: {status['dpu_seconds']}")
                return True

            elif status['state'] == 'FAILED':
                print(f"✗ Job failed: {status['error_message']}")
                return False

            elif status['state'] in ['TIMEOUT', 'STOPPED']:
                print(f"✗ Job {status['state']}")
                return False

            time.sleep(10)

        raise TimeoutError(f"Job did not complete within {max_wait_seconds} seconds")

    def list_job_runs(
        self,
        job_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List recent job runs

        Args:
            job_name: Job name
            max_results: Maximum results to return

        Returns:
            List of job run summaries
        """
        response = self.glue.get_job_runs(
            JobName=job_name,
            MaxResults=max_results
        )

        runs = []
        for run in response.get('JobRuns', []):
            runs.append({
                'run_id': run['Id'],
                'state': run['JobRunState'],
                'started': run.get('StartedOn', {}).isoformat() if 'StartedOn' in run else None,
                'execution_time': run.get('ExecutionTime', 0),
                'error': run.get('ErrorMessage', '')
            })

        return runs

    def update_job(
        self,
        name: str,
        script_location: Optional[str] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update an existing job

        Args:
            name: Job name
            script_location: New script location
            max_workers: New max workers

        Returns:
            Update response
        """
        update_params = {'Name': name}

        if script_location:
            update_params['Command'] = {'ScriptLocation': script_location}

        if max_workers:
            update_params['ExecutionProperty'] = {'MaxConcurrentRuns': max_workers}

        response = self.glue.update_job(**update_params)
        print(f"✓ Job '{name}' updated")
        return response

    def delete_job(self, job_name: str) -> Dict[str, Any]:
        """Delete a job"""
        response = self.glue.delete_job(Name=job_name)
        print(f"✓ Job '{job_name}' deleted")
        return response

    # ============================================================================
    # DATA CATALOG OPERATIONS
    # ============================================================================

    def create_database(
        self,
        database_name: str,
        description: str = '',
        location_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Glue database

        Args:
            database_name: Name of database
            description: Database description
            location_uri: S3 location for database

        Returns:
            Creation response
        """
        db_input = {
            'Name': database_name,
            'Description': description
        }

        if location_uri:
            db_input['LocationUri'] = location_uri

        try:
            response = self.glue.create_database(DatabaseInput=db_input)
            print(f"✓ Database '{database_name}' created")
            return response
        except self.glue.exceptions.AlreadyExistsException:
            print(f"⚠ Database '{database_name}' already exists")
            return {}

    def get_databases(self) -> List[Dict[str, Any]]:
        """List all databases"""
        response = self.glue.get_databases()
        databases = []

        for db in response.get('DatabaseList', []):
            databases.append({
                'name': db['Name'],
                'description': db.get('Description', ''),
                'location': db.get('LocationUri', '')
            })

        return databases

    def create_table(
        self,
        database_name: str,
        table_name: str,
        columns: List[Dict[str, str]],
        s3_location: str,
        format_type: str = 'parquet',
        partition_keys: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a table in Glue Catalog

        Args:
            database_name: Database name
            table_name: Table name
            columns: List of column definitions [{'Name': 'col', 'Type': 'string'}, ...]
            s3_location: S3 path to data
            format_type: Data format (parquet, csv, json, orc)
            partition_keys: Partition column definitions

        Returns:
            Creation response
        """
        # Format-specific configuration
        format_config = {
            'parquet': {
                'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                'SerdeInfo': {
                    'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
                }
            },
            'csv': {
                'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTypeOutputFormat',
                'SerdeInfo': {
                    'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                    'Parameters': {'field.delim': ','}
                }
            },
            'json': {
                'InputFormat': 'com.amazon.emr.hive.serde.EchoTabSeparatedInputFormat',
                'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTypeOutputFormat',
                'SerdeInfo': {
                    'SerializationLibrary': 'com.amazon.emr.hive.serde.EchoTabSeparatedSerDe'
                }
            }
        }

        fmt = format_config.get(format_type, format_config['parquet'])

        table_input = {
            'Name': table_name,
            'StorageDescriptor': {
                'Columns': columns,
                'Location': s3_location,
                'InputFormat': fmt['InputFormat'],
                'OutputFormat': fmt['OutputFormat'],
                'SerdeInfo': fmt['SerdeInfo']
            },
            'PartitionKeys': partition_keys or []
        }

        response = self.glue.create_table(
            DatabaseName=database_name,
            TableInput=table_input
        )
        print(f"✓ Table '{table_name}' created in database '{database_name}'")
        return response

    def get_table_schema(self, database_name: str, table_name: str) -> Dict[str, Any]:
        """
        Get table schema (columns and types)

        Args:
            database_name: Database name
            table_name: Table name

        Returns:
            Table schema and metadata
        """
        response = self.glue.get_table(
            DatabaseName=database_name,
            Name=table_name
        )

        table = response['Table']
        storage = table['StorageDescriptor']

        return {
            'name': table['Name'],
            'columns': [
                {'name': col['Name'], 'type': col['Type']}
                for col in storage['Columns']
            ],
            'location': storage['Location'],
            'format': storage.get('SerdeInfo', {}).get('SerializationLibrary', 'unknown'),
            'partition_keys': [
                {'name': pk['Name'], 'type': pk['Type']}
                for pk in table.get('PartitionKeys', [])
            ]
        }

    def list_tables(self, database_name: str) -> List[str]:
        """List tables in database"""
        response = self.glue.get_tables(DatabaseName=database_name)
        return [table['Name'] for table in response.get('TableList', [])]

    def add_partition(
        self,
        database_name: str,
        table_name: str,
        partition_values: Dict[str, str],
        s3_location: str
    ) -> Dict[str, Any]:
        """
        Add a partition to a table

        Args:
            database_name: Database name
            table_name: Table name
            partition_values: Dict of partition key-value pairs
            s3_location: S3 path for this partition

        Returns:
            Add partition response
        """
        # Get table to get storage descriptor
        table_schema = self.get_table_schema(database_name, table_name)
        table = self.glue.get_table(DatabaseName=database_name, Name=table_name)['Table']
        storage = table['StorageDescriptor'].copy()
        storage['Location'] = s3_location

        response = self.glue.batch_create_partition(
            DatabaseName=database_name,
            TableName=table_name,
            PartitionInputList=[
                {
                    'Values': [partition_values[pk['name']] for pk in table_schema['partition_keys']],
                    'StorageDescriptor': storage
                }
            ]
        )
        print(f"✓ Partition added to '{table_name}'")
        return response

    def get_partitions(
        self,
        database_name: str,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get all partitions for a table

        Args:
            database_name: Database name
            table_name: Table name

        Returns:
            List of partitions
        """
        response = self.glue.get_partitions(
            DatabaseName=database_name,
            TableName=table_name
        )

        partitions = []
        for part in response.get('Partitions', []):
            partitions.append({
                'values': part.get('Values', []),
                'location': part['StorageDescriptor'].get('Location', '')
            })

        return partitions

    def delete_table(self, database_name: str, table_name: str) -> Dict[str, Any]:
        """Delete a table"""
        response = self.glue.delete_table(
            DatabaseName=database_name,
            Name=table_name
        )
        print(f"✓ Table '{table_name}' deleted")
        return response

    # ============================================================================
    # CONNECTIONS (for JDBC, etc.)
    # ============================================================================

    def create_connection(
        self,
        connection_name: str,
        connection_type: str,
        connection_properties: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Create a Glue connection (for JDBC, etc.)

        Args:
            connection_name: Connection name
            connection_type: Type (postgresql, mysql, oracle, etc.)
            connection_properties: Connection properties dict

        Returns:
            Creation response
        """
        response = self.glue.create_connection(
            ConnectionInput={
                'Name': connection_name,
                'ConnectionType': connection_type,
                'ConnectionProperties': connection_properties,
                'Description': f'Connection to {connection_type} database'
            }
        )
        print(f"✓ Connection '{connection_name}' created")
        return response

    def test_connection(self, connection_name: str) -> bool:
        """Test a connection"""
        try:
            response = self.glue.test_connection(Name=connection_name)
            status = response.get('ConnectionResponse', {}).get('Status')
            print(f"Connection status: {status}")
            return status == 'READY'
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False

    # ============================================================================
    # MONITORING & LOGGING
    # ============================================================================

    def get_cloudwatch_metrics(
        self,
        job_name: str,
        run_id: str,
        metric_name: str = 'glue.driver.aggregate.numStages'
    ) -> List[Dict[str, Any]]:
        """
        Get CloudWatch metrics for a job run

        Args:
            job_name: Job name
            run_id: Run ID
            metric_name: Metric to retrieve

        Returns:
            List of metric data points
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Glue',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'JobName', 'Value': job_name},
                {'Name': 'RunId', 'Value': run_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Average', 'Maximum', 'Minimum']
        )

        return response.get('Datapoints', [])

    def get_job_logs(self, job_name: str, run_id: str) -> str:
        """
        Get Glue job logs from CloudWatch Logs

        Args:
            job_name: Job name
            run_id: Run ID

        Returns:
            Log content
        """
        import boto3

        logs = boto3.client('logs')
        log_group = f'/aws-glue/jobs/output/{run_id}'

        try:
            response = logs.get_log_events(
                logGroupName=log_group,
                limit=100
            )

            events = response.get('events', [])
            log_lines = [event['message'] for event in events]
            return '\n'.join(log_lines)

        except Exception as e:
            print(f"Could not retrieve logs: {e}")
            return ""

    def put_metric_alarm(
        self,
        job_name: str,
        alarm_name: str,
        metric_name: str,
        threshold: float,
        comparison: str = 'GreaterThanThreshold'
    ):
        """
        Create CloudWatch alarm for job metric

        Args:
            job_name: Job name
            alarm_name: Alarm name
            metric_name: Metric to monitor
            threshold: Threshold value
            comparison: GreaterThanThreshold, LessThanThreshold, etc.
        """
        self.cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            MetricName=metric_name,
            Namespace='AWS/Glue',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=1,
            Threshold=threshold,
            ComparisonOperator=comparison,
            Dimensions=[
                {'Name': 'JobName', 'Value': job_name}
            ]
        )
        print(f"✓ Alarm '{alarm_name}' created")

    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================

    def batch_create_crawlers(
        self,
        crawler_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple crawlers efficiently

        Args:
            crawler_configs: List of crawler configurations

        Returns:
            Results of all operations
        """
        results = {'succeeded': [], 'failed': []}

        for config in crawler_configs:
            try:
                self.create_crawler(**config)
                results['succeeded'].append(config['name'])
            except Exception as e:
                results['failed'].append({
                    'name': config['name'],
                    'error': str(e)
                })

        print(f"✓ Created {len(results['succeeded'])} crawlers")
        if results['failed']:
            print(f"✗ Failed to create {len(results['failed'])} crawlers")

        return results

    def start_all_crawler_runs(
        self,
        crawler_names: List[str]
    ) -> Dict[str, str]:
        """Start multiple crawlers"""
        results = {}

        for name in crawler_names:
            try:
                self.start_crawler(name)
                results[name] = 'started'
            except Exception as e:
                results[name] = f'error: {str(e)}'

        return results

    def stop_all_job_runs(self, job_name: str) -> Dict[str, Any]:
        """
        Stop all running job instances

        Args:
            job_name: Job name

        Returns:
            Stop results
        """
        runs = self.list_job_runs(job_name, max_results=100)
        stopped = 0

        for run in runs:
            if run['state'] == 'RUNNING':
                try:
                    self.glue.batch_stop_job_run(
                        JobName=job_name,
                        JobRunIds=[run['run_id']]
                    )
                    stopped += 1
                except Exception as e:
                    print(f"Error stopping run {run['run_id']}: {e}")

        print(f"✓ Stopped {stopped} job runs")
        return {'stopped': stopped, 'total': len(runs)}


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_crawler_workflow():
    """Example: Create crawler, run it, and query results"""
    glue = GlueOperations()

    # 1. Create database
    glue.create_database('raw_data', 'Raw data from various sources')

    # 2. Create crawler
    glue.create_crawler(
        name='s3-data-crawler',
        role_arn='arn:aws:iam::123456789012:role/GlueServiceRole',
        s3_path='s3://my-data-bucket/raw/',
        database_name='raw_data',
        table_prefix='crawler_',
        schedule_expression='cron(0 8 * * ? *)',  # Daily at 8 AM
        exclusions=['*.log', '*/temp/*']
    )

    # 3. Start crawler
    glue.start_crawler('s3-data-crawler')

    # 4. Wait for completion
    glue.wait_for_crawler('s3-data-crawler')

    # 5. Check results
    tables = glue.list_tables('raw_data')
    print(f"Created tables: {tables}")

    # 6. Get table schema
    if tables:
        schema = glue.get_table_schema('raw_data', tables[0])
        print(f"Table schema: {json.dumps(schema, indent=2)}")


def example_job_workflow():
    """Example: Create job, run it, and monitor execution"""
    glue = GlueOperations()

    # 1. Create job
    glue.create_spark_job(
        name='etl-transform-job',
        role_arn='arn:aws:iam::123456789012:role/GlueServiceRole',
        script_location='s3://my-scripts/etl-job.py',
        num_workers=10
    )

    # 2. Start job
    run_id = glue.start_job_run(
        job_name='etl-transform-job',
        arguments={
            '--input_database': 'raw_data',
            '--input_table': 'customers',
            '--output_path': 's3://my-data-bucket/processed/'
        }
    )

    # 3. Wait for completion
    glue.wait_for_job_completion('etl-transform-job', run_id)

    # 4. Get metrics
    metrics = glue.get_cloudwatch_metrics(
        job_name='etl-transform-job',
        run_id=run_id
    )
    print(f"Job metrics: {json.dumps(metrics, indent=2, default=str)}")


def example_catalog_operations():
    """Example: Catalog management"""
    glue = GlueOperations()

    # Create database
    glue.create_database('analytics', 'Analytics data warehouse')

    # Create table
    glue.create_table(
        database_name='analytics',
        table_name='dim_customers',
        columns=[
            {'Name': 'customer_id', 'Type': 'bigint'},
            {'Name': 'name', 'Type': 'string'},
            {'Name': 'email', 'Type': 'string'},
            {'Name': 'signup_date', 'Type': 'date'}
        ],
        s3_location='s3://my-data-bucket/customers/',
        format_type='parquet',
        partition_keys=[
            {'Name': 'year', 'Type': 'int'},
            {'Name': 'month', 'Type': 'int'}
        ]
    )

    # Add partitions
    glue.add_partition(
        database_name='analytics',
        table_name='dim_customers',
        partition_values={'year': '2024', 'month': '03'},
        s3_location='s3://my-data-bucket/customers/year=2024/month=03/'
    )

    # Get partitions
    partitions = glue.get_partitions('analytics', 'dim_customers')
    print(f"Partitions: {json.dumps(partitions, indent=2)}")


if __name__ == '__main__':
    # Uncomment to run examples
    # example_crawler_workflow()
    # example_job_workflow()
    # example_catalog_operations()

    print("AWS Glue Operations module loaded")
    print("Use GlueOperations class to perform Glue operations")
