"""Smoke test: Spark cluster <-> MinIO over S3A.

Writes a small Parquet dataset to s3a://<bucket>/smoke/ and reads it back.
Run it with the command in infra/README.md (section "Kiểm tra Spark - MinIO").
"""
import os

from pyspark.sql import SparkSession

BUCKET = os.environ.get("MINIO_BUCKET", "bigdata")
ROWS = 1_000_000


def build_session() -> SparkSession:
    return (
        SparkSession.builder.appName("smoke_s3a")
        .config("spark.hadoop.fs.s3a.endpoint", os.environ["AWS_ENDPOINT_URL"])
        .config("spark.hadoop.fs.s3a.access.key", os.environ["AWS_ACCESS_KEY_ID"])
        .config("spark.hadoop.fs.s3a.secret.key", os.environ["AWS_SECRET_ACCESS_KEY"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )


def main() -> None:
    spark = build_session()
    path = f"s3a://{BUCKET}/smoke/range"
    df = spark.range(ROWS, numPartitions=4)
    df.write.mode("overwrite").parquet(path)
    back = spark.read.parquet(path)
    print(f"SMOKE_OK rows_written={ROWS} rows_read={back.count()} path={path}")
    spark.stop()


if __name__ == "__main__":
    main()
