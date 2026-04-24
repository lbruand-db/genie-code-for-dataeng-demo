# Databricks notebook source
# =============================================================================
# BrickVault — Step 2: Catalog setup
# =============================================================================
# Creates the brickvault schema inside lucasbruand_catalog, plus a Volume for
# raw CSVs and Delta tables loaded from the files uploaded by 01_download_data.sh
#
# Run order: after 01_download_data.sh, before 03_semantic_metadata.py
# Cluster: any cluster with Unity Catalog enabled
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC ## BrickVault — Step 2: Catalog Setup
# MAGIC Creates the `brickvault` schema in `lucasbruand_catalog`, a Volume for
# MAGIC raw CSV files, and Delta tables for all Rebrickable source data.

# COMMAND ----------

CATALOG     = "lucasbruand_catalog"
SCHEMA      = "brickvault"
LANDING_VOL = f"/Volumes/{CATALOG}/{SCHEMA}/raw"

# COMMAND ----------

# MAGIC %md ### 1 — Schema and Volume

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.raw")

print(f"Schema {CATALOG}.{SCHEMA} and Volume raw ready.")

# COMMAND ----------

# MAGIC %md ### 2 — Helper: read CSV from Volume

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def read_csv(name: str) -> DataFrame:
    return (
        spark.read.format("csv")
        .option("header", "true")
        .option("inferSchema", "false")  # schemas defined explicitly below
        .load(f"{LANDING_VOL}/{name}.csv")
    )

# COMMAND ----------

# MAGIC %md ### 3 — sets

# COMMAND ----------

(
    read_csv("sets")
    .select(
        F.col("set_num").cast("string"),
        F.col("name").cast("string"),
        F.col("year").cast("int"),
        F.col("theme_id").cast("int"),
        F.col("num_parts").cast("int"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.sets")
)
print("sets written.")

# COMMAND ----------

# MAGIC %md ### 4 — themes

# COMMAND ----------

(
    read_csv("themes")
    .select(
        F.col("id").cast("int"),
        F.col("name").cast("string"),
        F.col("parent_id").cast("int"),  # null for root themes
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.themes")
)
print("themes written.")

# COMMAND ----------

# MAGIC %md ### 5 — parts

# COMMAND ----------

(
    read_csv("parts")
    .select(
        F.col("part_num").cast("string"),
        F.col("name").cast("string"),
        F.col("part_cat_id").cast("int"),
        F.col("part_material").cast("string"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.parts")
)
print("parts written.")

# COMMAND ----------

# MAGIC %md ### 6 — colors

# COMMAND ----------

(
    read_csv("colors")
    .select(
        F.col("id").cast("int"),
        F.col("name").cast("string"),
        F.col("rgb").cast("string"),
        # Rebrickable stores booleans as 't'/'f'
        (F.col("is_trans") == "t").alias("is_trans"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.colors")
)
print("colors written.")

# COMMAND ----------

# MAGIC %md ### 7 — inventories

# COMMAND ----------

(
    read_csv("inventories")
    .select(
        F.col("id").cast("int"),
        F.col("version").cast("int"),
        F.col("set_num").cast("string"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.inventories")
)
print("inventories written.")

# COMMAND ----------

# MAGIC %md ### 8 — inventory_parts
# MAGIC Largest table (~8M rows). May take a few minutes.

# COMMAND ----------

(
    read_csv("inventory_parts")
    .select(
        F.col("inventory_id").cast("int"),
        F.col("part_num").cast("string"),
        F.col("color_id").cast("int"),
        F.col("quantity").cast("int"),
        (F.col("is_spare") == "t").alias("is_spare"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.inventory_parts")
)
print("inventory_parts written.")

# COMMAND ----------

# MAGIC %md ### 9 — minifigs

# COMMAND ----------

(
    read_csv("minifigs")
    .select(
        F.col("fig_num").cast("string"),
        F.col("name").cast("string"),
        F.col("num_parts").cast("int"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.minifigs")
)
print("minifigs written.")

# COMMAND ----------

# MAGIC %md ### 10 — inventory_minifigs

# COMMAND ----------

(
    read_csv("inventory_minifigs")
    .select(
        F.col("inventory_id").cast("int"),
        F.col("fig_num").cast("string"),
        F.col("quantity").cast("int"),
    )
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{CATALOG}.{SCHEMA}.inventory_minifigs")
)
print("inventory_minifigs written.")

# COMMAND ----------

# MAGIC %md ### 11 — Verify

# COMMAND ----------

tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").collect()
print(f"{len(tables)} tables in {CATALOG}.{SCHEMA}:")
for t in tables:
    count = spark.table(f"{CATALOG}.{SCHEMA}.{t.tableName}").count()
    print(f"  {t.tableName:30s}  {count:>10,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC **Next step:** run `03_semantic_metadata.py` to apply descriptions,
# MAGIC column comments, and certified metric views.
