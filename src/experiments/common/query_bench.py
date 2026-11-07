"""Spark query benchmark for the experiments `format_compare` and `cache` (runs in the Spark container).

    spark-submit ... /opt/spark/work-dir/src/experiments/common/query_bench.py format \
        --dataset orders_5m --out /opt/spark/work-dir/results/metrics/<exp>/runs/<cfg>/r1/query_bench.json
    spark-submit ... query_bench.py cache --dataset orders_5m --mode cache --k 5 --out ...

`format`: the same queries on raw CSV/JSON (explicit schemas from src/etl/schemas.py, read exactly as
the ETL does) and on curated Parquet. `cache`: K aggregate queries over curated orders JOIN order_items,
with or without cache(). Times cover the action (collect) only; plans are captured after it.
Before any timed query an untimed warm-up runs (a small computation plus a read of the dataset's
products.parquet), so the first measured query does not pay executor JVM/codegen/S3A start-up.
Writes nothing to MinIO. Python 3.10 compatible (container interpreter).
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path

# spark-submit runs this file as a script, so make `src` importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pyspark.sql import DataFrame, SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from src.etl import cleaning, pipeline, session  # noqa: E402
from src.etl.aggregates import REVENUE_STATUSES  # noqa: E402

RAW_FILES = ("customers.csv", "orders.csv", "order_items.csv", "products.parquet", "web_events.jsonl")
CURATED_TABLES = ("customers", "products", "orders", "order_items", "web_events")
FORMAT_QUERIES = ("q1_filter_count", "q2_events_by_type", "q3_daily_revenue_join")
CACHE_QUERIES = ("revenue_by_date", "revenue_by_status", "top10_products_by_units",
                 "lines_by_payment_method", "avg_amount_by_line_no")


def explain_text(df: DataFrame, mode: str = "formatted") -> str:
    """Capture DataFrame.explain() output (it prints to stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        df.explain(mode=mode)
    return buf.getvalue()


def timed_collect(df: DataFrame) -> tuple[float, list]:
    """(seconds, rows) of df.collect()."""
    start = time.perf_counter()
    rows = df.collect()
    return round(time.perf_counter() - start, 3), rows


def path_size(spark: SparkSession, path: str) -> dict | None:
    """Bytes and file count under a path via the Hadoop FileSystem API (works for s3a://)."""
    jvm = spark.sparkContext._jvm
    p = jvm.org.apache.hadoop.fs.Path(path)
    fs = p.getFileSystem(spark.sparkContext._jsc.hadoopConfiguration())
    if not fs.exists(p):
        return None
    cs = fs.getContentSummary(p)
    return {"bytes": int(cs.getLength()), "files": int(cs.getFileCount())}


def warm_up(spark: SparkSession, storage_root: str, dataset: str) -> float:
    """Warm-up before the timed queries; returns its own duration (recorded, not part of any measurement)."""
    start = time.perf_counter()
    spark.range(0, 2_000_000, numPartitions=8).selectExpr("sum(id)").collect()
    spark.read.parquet(f"{storage_root}/raw/{dataset}/products.parquet").groupBy().count().collect()
    return round(time.perf_counter() - start, 3)


# ---- format_compare -------------------------------------------------------------------------

def format_queries(orders: DataFrame, items: DataFrame, events: DataFrame) -> dict[str, DataFrame]:
    """Same logical queries for both storage formats. `orders.order_date` must already be a date."""
    counted = orders.filter(F.col("status").isin(*REVENUE_STATUSES)).select("order_id", "order_date")
    return {
        # one column filtered, one scalar out
        "q1_filter_count": orders.filter(F.col("status") == "delivered").groupBy().count(),
        # one of five columns of the largest table (column pruning on Parquet; JSON must parse whole lines)
        "q2_events_by_type": events.groupBy("event_type").count(),
        # join + aggregate: revenue per day
        "q3_daily_revenue_join": (items.join(counted, "order_id")
                                  .groupBy("order_date")
                                  .agg(F.sum(F.col("quantity") * F.col("unit_price")).alias("revenue"))),
    }


def _result_summary(name: str, rows: list) -> dict:
    if name == "q1_filter_count":
        return {"count": rows[0][0] if rows else None}
    if name == "q2_events_by_type":
        return {"groups": {str(r[0]): r[1] for r in rows}}
    return {"rows": len(rows), "revenue_total": round(sum((r[1] or 0.0) for r in rows), 2)}


def run_format(spark: SparkSession, args: argparse.Namespace) -> dict:
    """Sizes, then every format query on raw and curated (order per --order); returns the result JSON."""
    cfg = pipeline.RunConfig(dataset=args.dataset, storage_root=args.storage_root)
    curated_root = f"{args.storage_root}/curated/{args.curated_label}"
    missing = [t for t in ("orders", "order_items", "web_events") if path_size(spark, f"{curated_root}/{t}") is None]
    if missing:
        raise FileNotFoundError(f"curated tables missing under {curated_root}: {missing}; "
                                "run the ETL for this dataset first or pass --curated-label")
    sizes = {
        "raw": {f: path_size(spark, cfg.raw(f)) for f in RAW_FILES},
        "curated": {t: path_size(spark, f"{curated_root}/{t}") for t in CURATED_TABLES},
    }
    warmup_seconds = warm_up(spark, args.storage_root, args.dataset)
    raw = pipeline.read_raw(spark, cfg)  # same reader options and schemas as the ETL
    sources = {
        "raw": (raw["orders"].withColumn("order_date", cleaning.parse_date(F.col("order_date"))),
                raw["order_items"], raw["web_events"]),
        "curated": tuple(spark.read.parquet(f"{curated_root}/{t}") for t in ("orders", "order_items", "web_events")),
    }
    built = {fmt: format_queries(*dfs) for fmt, dfs in sources.items()}
    fmt_order = ["raw", "curated"] if args.order == "raw-first" else ["curated", "raw"]
    measurements, seq = [], 0
    for name in FORMAT_QUERIES:
        for fmt in fmt_order:
            df = built[fmt][name]
            seconds, rows = timed_collect(df)
            plan = explain_text(df)
            print(f"QUERY {name} format={fmt} seconds={seconds}\n{plan}")
            measurements.append({"query": name, "format": fmt, "seq": seq, "seconds": seconds,
                                 "result": _result_summary(name, rows), "plan_after_run": plan})
            seq += 1
    curated_rows = {t: spark.read.parquet(f"{curated_root}/{t}").count()
                    for t in ("orders", "order_items", "web_events")}
    return {"bench": "format", "dataset": args.dataset, "curated_label": args.curated_label,
            "format_order": fmt_order, "warmup_seconds": warmup_seconds, "sizes": sizes, "curated_rows": curated_rows,
            "measurements": measurements}


# ---- cache ----------------------------------------------------------------------------------

def cache_base(spark: SparkSession, curated_root: str) -> DataFrame:
    """Curated order_items JOIN orders, with the line amount; the DataFrame reused by every query."""
    orders = spark.read.parquet(f"{curated_root}/orders").select("order_id", "order_date", "status", "payment_method")
    items = spark.read.parquet(f"{curated_root}/order_items")
    return items.join(orders, "order_id").withColumn("line_amount", F.col("quantity") * F.col("unit_price"))


def cache_queries(base: DataFrame) -> dict[str, DataFrame]:
    """The K-query workload of the cache benchmark (cycled in CACHE_QUERIES order)."""
    return {
        "revenue_by_date": base.groupBy("order_date").agg(F.sum("line_amount").alias("revenue")),
        "revenue_by_status": base.groupBy("status").agg(F.sum("line_amount").alias("revenue")),
        "top10_products_by_units": (base.groupBy("product_id").agg(F.sum("quantity").alias("units"))
                                    .orderBy(F.desc("units"), "product_id").limit(10)),
        "lines_by_payment_method": base.groupBy("payment_method").count(),
        "avg_amount_by_line_no": base.groupBy("line_no").agg(F.avg("line_amount").alias("avg_amount")),
    }


def storage_info(spark: SparkSession) -> list[dict]:
    """Cached RDD sizes as reported by the SparkContext (memory and disk bytes)."""
    try:
        infos = spark.sparkContext._jsc.sc().getRDDStorageInfo()
        return [{"name": str(i.name())[:200], "mem_bytes": int(i.memSize()), "disk_bytes": int(i.diskSize()),
                 "cached_partitions": int(i.numCachedPartitions()), "partitions": int(i.numPartitions()),
                 "storage_level": str(i.storageLevel().description())} for i in infos]
    except Exception as exc:  # internal API: record the failure instead of crashing the benchmark
        return [{"error": repr(exc)}]


def run_cache(spark: SparkSession, args: argparse.Namespace) -> dict:
    """K queries on curated orders JOIN order_items, cached or not; returns the result JSON."""
    curated_root = f"{args.storage_root}/curated/{args.curated_label}"
    missing = [t for t in ("orders", "order_items") if path_size(spark, f"{curated_root}/{t}") is None]
    if missing:
        raise FileNotFoundError(f"curated tables missing under {curated_root}: {missing}")
    warmup_seconds = warm_up(spark, args.storage_root, args.dataset)
    base = cache_base(spark, curated_root)
    out = {"bench": "cache", "dataset": args.dataset, "curated_label": args.curated_label, "mode": args.mode,
           "k": args.k, "warmup_seconds": warmup_seconds, "materialize_seconds": None, "storage_level": None,
           "storage_after_materialize": None}
    if args.mode == "cache":
        base = base.cache()
        out["storage_level"] = str(base.storageLevel)
        start = time.perf_counter()
        out["materialized_rows"] = base.count()
        out["materialize_seconds"] = round(time.perf_counter() - start, 3)
        out["storage_after_materialize"] = storage_info(spark)
        print(f"MATERIALIZE seconds={out['materialize_seconds']} rows={out['materialized_rows']}")
    queries = cache_queries(base)
    names = list(CACHE_QUERIES)
    measurements = []
    for i in range(args.k):
        name = names[i % len(names)]
        df = queries[name]
        seconds, rows = timed_collect(df)
        entry = {"index": i + 1, "query": name, "seconds": seconds, "result_rows": len(rows)}
        if i == 0:
            entry["plan_after_run"] = explain_text(df)  # shows InMemoryTableScan when cached
            print(entry["plan_after_run"])
        print(f"QUERY {i + 1} {name} mode={args.mode} seconds={seconds}")
        measurements.append(entry)
    if args.mode == "cache":
        base.unpersist(blocking=True)
        out["storage_after_unpersist"] = storage_info(spark)
    out["measurements"] = measurements
    out["queries_seconds_total"] = round(sum(m["seconds"] for m in measurements), 3)
    out["total_seconds"] = round(out["queries_seconds_total"] + (out["materialize_seconds"] or 0.0), 3)
    return out


# ---- CLI ------------------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    """Parse `format ...` / `cache ...` arguments; curated label defaults to the dataset name."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="bench", required=True)
    for name in ("format", "cache"):
        s = sub.add_parser(name)
        s.add_argument("--dataset", required=True)
        s.add_argument("--curated-label", help="folder under curated/ (default: the dataset name)")
        s.add_argument("--storage-root", default="s3a://bigdata")
        s.add_argument("--shuffle-partitions", type=int, default=8)
        s.add_argument("--out", required=True, help="JSON file to write (inside the container)")
    sub.choices["format"].add_argument("--order", choices=("raw-first", "curated-first"), default="raw-first")
    sub.choices["cache"].add_argument("--mode", choices=("cache", "nocache"), required=True)
    sub.choices["cache"].add_argument("--k", type=int, default=5, help="number of queries (cycles the list)")
    args = p.parse_args(argv)
    args.curated_label = args.curated_label or args.dataset
    return args


def main(argv=None) -> int:
    """Run one benchmark and write its JSON; 2 if curated tables are missing."""
    args = parse_args(argv)
    spark = session.build_session(args.storage_root, args.shuffle_partitions, app_name=f"query_bench_{args.bench}")
    try:
        result = run_format(spark, args) if args.bench == "format" else run_cache(spark, args)
    except FileNotFoundError as exc:
        print(f"QUERY_BENCH_ERROR {exc}")
        spark.stop()
        return 2
    result.update({"spark_version": spark.version, "app_id": spark.sparkContext.applicationId,
                   "default_parallelism": spark.sparkContext.defaultParallelism,
                   "resources": pipeline._resources(spark),  # same resource record as the ETL metrics
                   "conf": {k: spark.conf.get(k) for k in ("spark.sql.shuffle.partitions",
                                                           "spark.sql.adaptive.enabled",
                                                           "spark.sql.autoBroadcastJoinThreshold")}})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"QUERY_BENCH_OK bench={args.bench} out={out}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
