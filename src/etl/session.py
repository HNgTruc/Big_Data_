"""SparkSession factory shared by the ETL job and the tests."""
from __future__ import annotations

import os

from pyspark.sql import SparkSession


def build_session(storage_root: str, shuffle_partitions: int = 8, aqe: bool = True,
                  auto_broadcast: bool = True, app_name: str = "ecommerce_etl") -> SparkSession:
    builder = (SparkSession.builder.appName(app_name)
               # Spark 4 enables ANSI mode by default; bad dates must yield NULL, not an error.
               .config("spark.sql.ansi.enabled", "false")
               .config("spark.sql.legacy.timeParserPolicy", "CORRECTED")
               .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
               .config("spark.sql.adaptive.enabled", str(aqe).lower()))
    if not auto_broadcast:
        builder = builder.config("spark.sql.autoBroadcastJoinThreshold", "-1")
    if storage_root.startswith("s3a://"):
        builder = (builder
                   .config("spark.hadoop.fs.s3a.endpoint", os.environ["AWS_ENDPOINT_URL"])
                   .config("spark.hadoop.fs.s3a.access.key", os.environ["AWS_ACCESS_KEY_ID"])
                   .config("spark.hadoop.fs.s3a.secret.key", os.environ["AWS_SECRET_ACCESS_KEY"])
                   .config("spark.hadoop.fs.s3a.path.style.access", "true")
                   .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false"))
    return builder.getOrCreate()
