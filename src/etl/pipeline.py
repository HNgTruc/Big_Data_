"""ETL orchestration: read raw -> clean -> write curated/quarantine -> aggregate -> metrics."""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from . import aggregates, cleaning, schemas


@dataclass(frozen=True)
class RunConfig:
    dataset: str                      # folder under <root>/raw/, e.g. orders_500k
    storage_root: str = "s3a://bigdata"
    run_label: str | None = None      # output folder name; defaults to dataset
    join_strategy: str = "auto"       # auto | broadcast | shuffle
    metrics_dir: str | None = None    # local dir for the metrics JSON; None = do not write

    @property
    def label(self) -> str:
        return self.run_label or self.dataset

    def raw(self, name: str) -> str:
        return f"{self.storage_root}/raw/{self.dataset}/{name}"

    def curated(self, table: str) -> str:
        return f"{self.storage_root}/curated/{self.label}/{table}"

    def quarantine(self, table: str) -> str:
        return f"{self.storage_root}/quarantine/{self.label}/{table}"


@contextmanager
def _timed(timings: dict, name: str):
    start = time.perf_counter()
    yield
    timings[name] = round(time.perf_counter() - start, 3)


def _write(df: DataFrame, path: str) -> None:
    df.write.mode("overwrite").parquet(path)


def read_raw(spark: SparkSession, cfg: RunConfig) -> dict[str, DataFrame]:
    csv = {"header": True, "mode": "PERMISSIVE"}
    return {
        "customers": spark.read.csv(cfg.raw("customers.csv"), schema=schemas.CUSTOMERS, **csv),
        "orders": spark.read.csv(cfg.raw("orders.csv"), schema=schemas.ORDERS, **csv),
        "order_items": spark.read.csv(cfg.raw("order_items.csv"), schema=schemas.ORDER_ITEMS, **csv),
        "products": spark.read.parquet(cfg.raw("products.parquet")),
        "web_events": spark.read.schema(schemas.EVENTS).json(cfg.raw("web_events.jsonl")),
    }


def _table_stats(spark: SparkSession, cfg: RunConfig, raw: DataFrame, table: str, has_quarantine: bool) -> dict:
    clean_rows = spark.read.parquet(cfg.curated(table)).count()
    stats = {"raw_rows": raw.count(), "clean_rows": clean_rows, "quarantined_rows": 0, "quarantine_by_reason": {}}
    if has_quarantine:
        by_reason = spark.read.parquet(cfg.quarantine(table)).groupBy("reject_reason").count().collect()
        stats["quarantine_by_reason"] = {r["reject_reason"]: r["count"] for r in by_reason}
        stats["quarantined_rows"] = sum(stats["quarantine_by_reason"].values())
    stats["duplicates_removed"] = stats["raw_rows"] - clean_rows - stats["quarantined_rows"]
    return stats


def run(spark: SparkSession, cfg: RunConfig) -> dict:
    """Run the whole pipeline and return (and optionally save) the metrics."""
    raw = read_raw(spark, cfg)
    sec: dict[str, float] = {}

    with _timed(sec, "dimensions"):
        _write(cleaning.clean_customers(raw["customers"]), cfg.curated("customers"))
        _write(raw["products"], cfg.curated("products"))
    customers = spark.read.parquet(cfg.curated("customers"))
    products = spark.read.parquet(cfg.curated("products"))

    with _timed(sec, "orders"):
        clean, rejected = cleaning.clean_orders(raw["orders"], customers, cfg.join_strategy)
        _write(clean, cfg.curated("orders"))
        _write(rejected, cfg.quarantine("orders"))
    orders = spark.read.parquet(cfg.curated("orders"))

    with _timed(sec, "order_items"):
        clean, rejected = cleaning.clean_items(raw["order_items"], orders, products, cfg.join_strategy)
        _write(clean, cfg.curated("order_items"))
        _write(rejected, cfg.quarantine("order_items"))
    items = spark.read.parquet(cfg.curated("order_items"))

    with _timed(sec, "web_events"):
        clean, rejected = cleaning.clean_events(raw["web_events"])
        _write(clean, cfg.curated("web_events"))
        _write(rejected, cfg.quarantine("web_events"))
    events = spark.read.parquet(cfg.curated("web_events"))

    with _timed(sec, "aggregates"):
        _write(aggregates.daily_revenue(orders, items), cfg.curated("agg_daily_revenue"))
        _write(aggregates.revenue_by_region_category(orders, items, customers, products, cfg.join_strategy),
               cfg.curated("agg_revenue_by_region_category"))
        _write(aggregates.events_daily(events), cfg.curated("agg_events_daily"))

    # Statistics are computed after the timed stages and are NOT part of processing time.
    tables = {
        "customers": _table_stats(spark, cfg, raw["customers"], "customers", False),
        "products": _table_stats(spark, cfg, raw["products"], "products", False),
        "orders": _table_stats(spark, cfg, raw["orders"], "orders", True),
        "order_items": _table_stats(spark, cfg, raw["order_items"], "order_items", True),
        "web_events": _table_stats(spark, cfg, raw["web_events"], "web_events", True),
    }
    metrics = {
        "config": asdict(cfg),
        "spark_version": spark.version,
        "app_id": spark.sparkContext.applicationId,
        "default_parallelism": spark.sparkContext.defaultParallelism,
        "conf": {k: spark.conf.get(k) for k in (
            "spark.sql.shuffle.partitions", "spark.sql.adaptive.enabled",
            "spark.sql.autoBroadcastJoinThreshold")},
        "stage_seconds": sec,
        "processing_seconds_total": round(sum(sec.values()), 3),
        "tables": tables,
        "aggregate_rows": {name: spark.read.parquet(cfg.curated(name)).count() for name in (
            "agg_daily_revenue", "agg_revenue_by_region_category", "agg_events_daily")},
    }
    if cfg.metrics_dir:
        out = Path(cfg.metrics_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{cfg.label}.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
