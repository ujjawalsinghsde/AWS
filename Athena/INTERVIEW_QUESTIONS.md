# Athena Interview Questions

## 1. Fundamental Questions

1. **What is Amazon Athena and its unique advantages?**
   - Serverless SQL query engine on S3 data
   - No server setup, pay per GB scanned
   - Supports multiple formats: CSV, JSON, Parquet, ORC
   - Queries S3 directly (no ETL needed)
   - Standard SQL, ANSI SQL compatible

2. **Athena vs Redshift vs Glue comparison:**
   - **Athena**: Ad-hoc queries on S3, pay-per-scan, no data loading
   - **Redshift**: Data warehouse, fast on structured data, requires loading
   - **Glue**: ETL tool for data transformation and cataloging
   - Choose: Athena for exploratory analytics, Redshift for structured data

3. **Explain partitioning in Athena.**
   - Partition pruning: Only scan relevant partitions
   - Structure: s3://bucket/year=2024/month=01/day=15/data.parquet
   - Partition keys: year, month, day
   - Performance: Reduces data scanned, faster queries, lower cost

4. **What is AWS Glue Data Catalog?**
   - Central metadata repository
   - Stores table definitions, schemas
   - Athena uses Data Catalog for table info
   - Crawlers auto-discover schema

5. **Athena cost optimization:**
   - Parquet format: 80-90% compression vs CSV
   - Partitioning: Only scan needed partitions
   - Projection: Partition pseudo-columns without listing S3
   - Bucketing: Group data by column
   - Query caching: Same query returns cached results

## 2. Real-World Scenarios

6. **Scenario: Analyze 1 TB CSV log files in S3. Optimize cost and speed.**
   - Current problem: Scan entire 1 TB each query (expensive)
   - Solutions:
     1. Convert to Parquet (200 GB with compression)
     2. Add partitioning (year/month/day)
     3. Run query: Scans only necessary partitions
     4. Result: 5-10 GB scanned vs 1 TB (90% cost reduction)

7. **Design data lake with Athena as query layer:**
   - Raw data → S3 (bronze layer)
   - Glue crawlers → Discover schema
   - ETL (Glue) → Transform → Parquet (silver layer)
   - Business queries → Athena on silver/gold layers
   - Benefits: Separation of concerns, cost-efficient

---

## Tips for Interview Success

- **Understand S3 interaction**: Athena queries S3, not traditional database
- **Cost focus**: Parquet compression, partitioning are critical
- **Data format**: Parquet is default recommendation
- **Integration**: Glue Catalog, QuickSight visualizations
- **Partition pruning**: How Athena reduces costs

