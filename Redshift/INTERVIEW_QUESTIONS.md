# Redshift Interview Questions

## 1. Fundamental Questions

1. **What is Amazon Redshift?**
   - Petabyte-scale data warehouse
   - Columnar storage (optimized for analytical queries)
   - Distributed architecture (leader + compute nodes)
   - Fast queries on massive datasets
   - SQL interface (ANSI SQL compatible)

2. **Redshift cluster architecture:**
   - **Leader Node**: Coordinates, parses queries, aggregates
   - **Compute Nodes**: Store data, execute queries in parallel
   - Scaling: Add/remove nodes for compute/storage
   - Replication: Across AZs with snapshots

3. **Redshift vs RDS:**
   - **RDS**: OLTP (transactional), row-based, small-medium datasets
   - **Redshift**: OLAP (analytical), column-based, petabyte-scale
   - Choose: RDS for apps, Redshift for analytics

4. **Redshift compression techniques:**
   - Columnar format: Similar values grouped
   - Encoding: LZO, ZSTD for text
   - Automatic compression: ANALYZE COMPRESSION
   - Benefit: Reduce storage, improve I/O

5. **Redshift pricing:**
   - Per-node per-hour (DC2, RA3 nodes)
   - RA3 with managed storage: Pay only for storage used
   - Free tier: 2 months dc2.large

## 2. Real-World Scenarios

6. **Scenario: Load 100 GB daily from S3 into Redshift.**
   - COPY command: Load from S3 directly
   - Parallelism: Multiple files load in parallel
   - Batch size: Stage files, load once daily
   - Transformation: Use manifest file or data transformation tools
   - Monitoring: STL_LOAD_COMMITS, query performance

7. **Design analytics schema for e-commerce:**
   - Fact table: Orders (transactional)
   - Dimensions: Customers, Products, Date
   - Star schema: Optimize for common queries
   - Materialized views: Pre-aggregate for dashboards
   - Partitioning: By date for time-series analysis

8. **Optimize slow Redshift query:**
   - ANALYZE: Update statistics
   - Query plan: Explain query, check distribution
   - Sort key: Choose wisely for range queries
   - Distribution: Avoid skew (one node processes most data)
   - Vacuuming: Reclaim deleted row space

---

## Tips for Interview Success

- **Columnar advantage**: Why analytical queries are fast
- **Distribution strategy**: Critical for performance
- **Compression**: Reduces storage and I/O
- **COPY optimization**: Parallel loading is key
- **Materialized views**: Pre-computed aggregations
- **Monitoring**: Use STL tables for performance insights

