# AWS Glue Interview Questions

## 1. Fundamental Questions

1. **What is AWS Glue and its main components?**
   - Managed ETL (Extract, Transform, Load) service
   - Components: Data Catalog, Crawlers, Jobs, Studio
   - Serverless, scales on demand
   - Pay per DPU-hour (data processing unit)

2. **Explain Glue Data Catalog.**
   - Central metadata repository
   - Auto-discovery via crawlers
   - Schema versioning
   - Integration with Athena, Redshift, EMR
   - Time-based retention for old schemas

3. **What are Glue crawlers and job bookmarks?**
   - **Crawlers**: Auto-detect data schema from S3, DB, etc
   - **Bookmarks**: Remember previous run, process only new data
   - Benefit: Incremental processing, avoids re-processing

4. **Glue job types:**
   - **Spark Jobs**: Distributed processing, Python/Scala
   - **Python Shell**: Single-node, simple scripts
   - **Ray Jobs**: ML workloads
   - Choose based on data size and complexity

5. **Glue pricing:**
   - DPU-hours: 1 DPU minimum, scales with parallelism
   - Spark default 10 DPU, can increase
   - Crawlers: Charged per crawl execution
   - Data Catalog: First 1M objects free, then per object

## 2. Real-World Scenarios

6. **Scenario: Daily ETL job transforms data from RDS to S3 (Parquet).**
   - Glue Crawler: Discovers RDS schema
   - Glue Job (Spark):
     - Read from RDS using JDBC
     - Transform: Clean, filter, aggregate
     - Write as Parquet to S3 (partitioned)
   - Scheduling: Glue Trigger (daily 2 AM)
   - Monitoring: CloudWatch logs, DynamoDB job bookmarks

7. **Design data pipeline with incremental loads:**
   - Job Bookmarks: Track last processed row
   - Incremental query: WHERE last_modified > bookmark_timestamp
   - Process only new data
   - Cost-effective, faster execution

8. **Handle late arrivals in ETL:**
   - Partition by event_date, load_date separate
   - Allow backfilling (2 days late data)
   - Implement idempotent writes (overwrite partition if rerun)
   - Monitoring: Alert if late data received

---

## Tips for Interview Success

- **Metadata management**: Data Catalog is key
- **Incremental processing**: Job bookmarks save cost
- **Format choice**: Parquet for analytical workloads
- **Error handling**: Glue job error notifications
- **Performance**: Parallelism via DPU count
- **Integration**: With Athena, Redshift, EMR

