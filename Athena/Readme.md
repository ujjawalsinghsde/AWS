# **📘 Athena**

## **1. AWS Athena Overview**

AWS Athena is a **serverless SQL query engine** used to analyze data stored in **Amazon S3**.

### **Key Points**

* No servers or clusters required.
* Uses **Presto/Trino** engine under the hood.
* Charged only for **data scanned**.
* Reads data formats: **Parquet, ORC, CSV, JSON, Avro, Iceberg**.
* Requires **schema metadata** to understand the structure of S3 data.
* Metadata can be stored in **Glue Catalog** or **Athena’s internal catalog**.

---

## **2. Why Athena Is Used**

Athena is widely used because:

* 🔹 **Very cost-efficient**, especially with Parquet.
* 🔹 **Fully serverless** → No infra management.
* 🔹 Ideal for **ad-hoc SQL**, quick debugging, and data validation.
* 🔹 Perfect for log analytics (CloudTrail, VPC Flow Logs, S3 access logs).
* 🔹 Great tool for querying S3 data lakes.
* 🔹 Integrates with **QuickSight** for dashboards.

---

## **3. Athena Requires Metadata (Mandatory Point)**

Athena **cannot** read files directly without schema.

### **But:**

* Metadata is **mandatory**
* Glue Catalog is **optional**

You must define:

* Column names
* Data types
* File format
* S3 location

### **Two ways to create metadata:**

1. **Glue Crawler** (Auto-detect schema and create table)
2. **CREATE TABLE in Athena** (Manual SQL)

---

## **4. Athena Insert & Write Capabilities**

Athena supports **limited write operations**:

### ✔ Supported

* `INSERT INTO`
* `INSERT OVERWRITE`
* `CTAS` (CREATE TABLE AS SELECT)

### ❌ Not Supported

* UPDATE
* DELETE
* MERGE / UPSERT
* ACID transactions
* Row-level updates
* Transaction logs

Athena is **NOT a transactional database**, mostly read-focused.

---

## **5. Iceberg vs Delta with Athena**

### **Apache Iceberg (Best choice on AWS)**

* Full ACID
* Time Travel
* Schema + Partition evolution
* Supported by **Athena, Glue ETL, EMR Spark, Redshift Spectrum**
* AWS-native lakehouse format

### **Delta Lake**

* Created by **Databricks**
* ACID supported **only in Spark/Databricks** environments
* Athena can **only read** Delta tables (read-only)
* Athena cannot write or maintain Delta `_delta_log`
* Not recommended for the AWS-native lakehouse architecture

### Summary:

| Feature            | Iceberg | Delta + Athena |
| ------------------ | ------- | -------------- |
| Full ACID          | ✔       | ❌              |
| Athena Read        | ✔       | ✔              |
| Athena Write       | ✔       | ❌              |
| AWS Native         | ✔       | ❌              |
| Multi-engine write | ✔       | ❌              |

---

## **6. Redshift → UNLOAD → S3 → Athena Workflow**

### **Step 1: UNLOAD From Redshift**

```sql
UNLOAD ('SELECT * FROM table')
TO 's3://bucket/path/'
IAM_ROLE 'arn:aws:iam::<role>'
FORMAT AS PARQUET;
```

This creates Parquet files in S3.

Example structure:

```
s3://bucket/path/
    part-0001.parquet
    part-0002.parquet
```

---

### **Step 2: Create Metadata**

You MUST create metadata using:

#### **Option 1: Glue Crawler**

* Auto reads Parquet schema
* Auto creates table in Glue Catalog
* Athena uses it directly

#### **Option 2: Manually**

```sql
CREATE EXTERNAL TABLE my_table (
  id BIGINT,
  amount DOUBLE,
  created_at TIMESTAMP
)
STORED AS PARQUET
LOCATION 's3://bucket/path/';
```

---

### **Step 3: Query in Athena**

```sql
SELECT * FROM my_table;
```

---

### **Step 4: Optional – Add Partitioning**

Partitioning reduces cost & increases speed.

```sql
PARTITIONED BY (year int, month int);
```

Add partitions:

```sql
MSCK REPAIR TABLE my_table;
```

---

## **7. Athena Capabilities Summary**

### ✔ Athena CAN:

* Query S3 data using SQL
* Insert (limited)
* Create tables (CTAS)
* Read Delta (read-only)
* Fully support Iceberg (ACID)
* Query Redshift UNLOAD data
* Work with Glue Catalog

### ❌ Athena CANNOT:

* UPDATE/DELETE rows
* MERGE (no UPSERT)
* Maintain ACID for Delta
* Query without schema metadata
* Work as a database

---

## **8. Recommendations**

### **If using AWS stack (Glue, Athena, EMR, Redshift):**

✔ Use **Iceberg tables** for full ACID lakehouse.

### **If using Databricks or heavy Spark workloads:**

✔ Use **Delta Lake**.

### **For cost-optimized analytics on S3:**

✔ Use **Athena + Parquet**.

### **For moving cold Redshift data:**

✔ Use **Redshift UNLOAD → S3 → Athena**.

---

# **📌 Final Summary**

* Athena = Serverless SQL on S3
* Metadata is mandatory (Glue optional)
* Athena writes are limited
* Iceberg = Best ACID format on AWS
* Delta = Good only for Databricks/Spark
* Redshift UNLOAD → S3 (Parquet) → Athena is common
* Athena cannot update or merge data
* Athena cannot work without schema
