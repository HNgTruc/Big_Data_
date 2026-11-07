"""Export small before/after samples of one ETL run as CSV evidence (report section 5.7).

Reads raw/<dataset>/, curated/<dataset>/ and quarantine/<dataset>/ (the standard ETL run, not experiment
labels), never writes to storage, and writes one small CSV per case into --out-dir on the driver:

    spark-submit ... /opt/spark/work-dir/src/etl/export_samples.py --dataset orders_5m

Samples are deterministic: every selection sorts by the table key before limiting (no random sampling).
Row counts in summary.csv are counted directly and compared with results/metrics/<dataset>.json.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql import functions as F

# spark-submit runs this file as a script, so make `src.etl` importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.etl import cleaning, pipeline, session  # noqa: E402

QUARANTINE_KEYS = {"orders": ["order_id"], "order_items": ["order_id", "line_no"], "web_events": ["event_id"]}
AGGREGATE_KEYS = {
    "agg_daily_revenue": ["order_date"],
    "agg_revenue_by_region_category": ["region", "category"],
    "agg_events_daily": ["event_date", "event_type"],
}
SUMMARY_FIELDS = ["table", "raw_rows", "curated_rows", "quarantined_rows", "duplicates_removed",
                  "metrics_raw_rows", "metrics_clean_rows", "metrics_quarantined_rows",
                  "metrics_duplicates_removed", "matches_metrics"]
REASON_FIELDS = ["table", "reject_reason", "rows", "metrics_rows", "matches_metrics"]


def _matching(big: DataFrame, small: DataFrame, keys: list[str]) -> DataFrame:
    """Rows of `big` whose keys occur in the tiny `small`, via a broadcast semi join (no shuffle of `big`).

    An outer join cannot broadcast its preserved side, so callers outer-join on this filtered result instead.
    """
    return big.join(F.broadcast(small.select(*keys)), keys, "left_semi")


def duplicate_sample(raw: DataFrame, curated: DataFrame, keys: list[str], n: int) -> DataFrame:
    """Raw rows of the n smallest keys that occur more than once in raw and survive into curated.

    Output: `stage` (raw | curated) + the raw columns as strings (raw dates are strings, curated ones typed),
    sorted by the typed key, raw rows first.
    """
    dup_keys = (raw.groupBy(*keys).count().filter(F.col("count") > 1).select(*keys)
                .join(curated.select(*keys), keys, "left_semi")
                .orderBy(*keys).limit(n))
    cols = raw.columns
    sort_keys = [f"_sort_{k}" for k in keys]

    def staged(df: DataFrame, stage: str) -> DataFrame:
        # Keep typed copies of the keys for sorting: string keys would sort "140" before "30".
        return df.select(F.lit(stage).alias("stage"), *[F.col(k).alias(s) for k, s in zip(keys, sort_keys)],
                         *[F.col(c).cast("string").alias(c) for c in cols])

    both = staged(_matching(raw, dup_keys, keys), "raw").unionByName(
        staged(_matching(curated, dup_keys, keys), "curated"))
    order = F.when(F.col("stage") == "raw", 0).otherwise(1)
    return both.orderBy(*sort_keys, order).select("stage", *cols)


def format_label(col: Column, rules: list[tuple[str, str]]) -> Column:
    """Name of the first non-standard format (rules[1:]) the string matches; null for standard/unknown."""
    expr = None
    for pattern, fmt in rules[1:]:  # rules[0] is the standard ISO format
        expr = F.when(col.rlike(pattern), F.lit(fmt)) if expr is None else expr.when(col.rlike(pattern), F.lit(fmt))
    return expr


def bad_format_sample(raw: DataFrame, curated: DataFrame, key: str, column: str,
                      rules: list[tuple[str, str]], n: int) -> DataFrame:
    """Up to n raw rows per non-standard format (smallest keys first) next to the curated value.

    Output columns: key, raw_<column>, raw_format, curated_<column> (string; empty if not in curated).
    """
    labelled = (raw.select(key, column).withColumn("raw_format", format_label(F.col(column), rules))
                .filter(F.col("raw_format").isNotNull()).dropDuplicates([key]))
    rank = F.row_number().over(Window.partitionBy("raw_format").orderBy(key))
    picked = (labelled.withColumn("_rank", rank).filter(F.col("_rank") <= n)
              .select(key, F.col(column).alias(f"raw_{column}"), "raw_format"))
    after = _matching(curated, picked, [key]).select(key, F.col(column).cast("string").alias(f"curated_{column}"))
    return (picked.join(after, key, "left")
            .select(key, f"raw_{column}", "raw_format", f"curated_{column}")
            .orderBy("raw_format", key))


def quarantine_sample(quarantine: DataFrame, keys: list[str], n: int) -> DataFrame:
    """Up to n quarantined rows per reject_reason, smallest keys first; reject_reason is the first column."""
    rank = F.row_number().over(Window.partitionBy("reject_reason").orderBy(*keys))
    cols = ["reject_reason", *[c for c in quarantine.columns if c != "reject_reason"]]
    return (quarantine.withColumn("_rank", rank).filter(F.col("_rank") <= n)
            .select(*cols).orderBy("reject_reason", *keys))


def missing_region_sample(raw: DataFrame, curated: DataFrame, n: int) -> DataFrame:
    """Raw customers with a null region (n smallest ids) next to their curated row (region filled in)."""
    picked = (raw.filter(F.col("region").isNull()).dropDuplicates(["customer_id"])
              .orderBy("customer_id").limit(n)
              .select("customer_id", F.col("region").alias("raw_region"),
                      F.col("signup_date").alias("raw_signup_date")))
    after = _matching(curated, picked, ["customer_id"]).select(
        "customer_id", F.col("region").alias("curated_region"),
        F.col("signup_date").cast("string").alias("curated_signup_date"))
    return (picked.join(after, "customer_id", "left")
            .select("customer_id", "raw_region", "curated_region", "raw_signup_date", "curated_signup_date")
            .orderBy("customer_id"))


def head_sorted(df: DataFrame, keys: list[str], n: int) -> DataFrame:
    """First n rows of df in key order."""
    return df.orderBy(*keys).limit(n)


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def write_rows(path: Path, fields: list[str], rows: list[dict]) -> int:
    """Write rows (dicts) to one CSV file; returns the number of data rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({f: _cell(row.get(f)) for f in fields})
    return len(rows)


def write_df(df: DataFrame, path: Path) -> int:
    """Collect a small (already limited) DataFrame to the driver and write it as a single CSV file."""
    return write_rows(path, df.columns, [r.asDict() for r in df.collect()])


def _match(counted, expected) -> str:
    if expected is None:
        return "no_metrics"
    return "yes" if counted == expected else "no"


def compare_counts(counts: dict, metrics: dict | None) -> tuple[list[dict], list[dict]]:
    """Build summary rows and per-reason rows; compare each counted value with the metrics JSON.

    counts: {"tables": {t: {raw_rows, curated_rows, quarantined_rows, quarantine_by_reason}},
             "aggregates": {name: rows}}. metrics: the ETL metrics dict, or None if missing.
    """
    m_tables = (metrics or {}).get("tables", {})
    m_aggs = (metrics or {}).get("aggregate_rows", {})
    summary, reasons = [], []
    for table, c in counts["tables"].items():
        m = m_tables.get(table, {})
        dups = c["raw_rows"] - c["curated_rows"] - c["quarantined_rows"]
        expected = (m.get("raw_rows"), m.get("clean_rows"), m.get("quarantined_rows"), m.get("duplicates_removed"))
        got = (c["raw_rows"], c["curated_rows"], c["quarantined_rows"], dups)
        summary.append({"table": table, "raw_rows": got[0], "curated_rows": got[1], "quarantined_rows": got[2],
                        "duplicates_removed": got[3], "metrics_raw_rows": expected[0],
                        "metrics_clean_rows": expected[1], "metrics_quarantined_rows": expected[2],
                        "metrics_duplicates_removed": expected[3],
                        "matches_metrics": _match(got, None if not m else expected)})
        m_reasons = m.get("quarantine_by_reason", {})
        for reason in sorted(set(c["quarantine_by_reason"]) | set(m_reasons)):
            rows = c["quarantine_by_reason"].get(reason, 0)
            exp = m_reasons.get(reason, 0) if m else None
            reasons.append({"table": table, "reject_reason": reason, "rows": rows, "metrics_rows": exp,
                            "matches_metrics": _match(rows, exp)})
    for name, rows in counts["aggregates"].items():
        exp = m_aggs.get(name)
        summary.append({"table": name, "curated_rows": rows, "metrics_clean_rows": exp,
                        "matches_metrics": _match(rows, exp)})
    return summary, reasons


def count_all(spark: SparkSession, cfg: pipeline.RunConfig, raw: dict[str, DataFrame]) -> dict:
    """Direct row counts of raw, curated and quarantine for the five tables, plus aggregate sizes."""
    tables = {}
    for table in ("customers", "products", "orders", "order_items", "web_events"):
        stats = {"raw_rows": raw[table].count(), "curated_rows": spark.read.parquet(cfg.curated(table)).count(),
                 "quarantined_rows": 0, "quarantine_by_reason": {}}
        if table in QUARANTINE_KEYS:
            by_reason = spark.read.parquet(cfg.quarantine(table)).groupBy("reject_reason").count().collect()
            stats["quarantine_by_reason"] = {r["reject_reason"]: r["count"] for r in by_reason}
            stats["quarantined_rows"] = sum(stats["quarantine_by_reason"].values())
        tables[table] = stats
    aggregates = {name: spark.read.parquet(cfg.curated(name)).count() for name in AGGREGATE_KEYS}
    return {"tables": tables, "aggregates": aggregates}


def export(spark: SparkSession, cfg: pipeline.RunConfig, out_dir: Path, n: int, agg_rows: int,
           metrics: dict | None) -> dict:
    """Write every sample CSV into out_dir; returns {file name: data rows} and the mismatch count."""
    raw = pipeline.read_raw(spark, cfg)
    cur = {t: spark.read.parquet(cfg.curated(t)) for t in ("customers", "orders", "order_items", "web_events")}
    written = {}

    def out(name: str, df: DataFrame) -> None:
        written[name] = write_df(df, out_dir / name)

    out("duplicates_orders.csv", duplicate_sample(raw["orders"], cur["orders"], ["order_id"], n))
    out("duplicates_order_items.csv",
        duplicate_sample(raw["order_items"], cur["order_items"], ["order_id", "line_no"], n))
    out("bad_dates_orders.csv",
        bad_format_sample(raw["orders"], cur["orders"], "order_id", "order_date", cleaning.DATE_RULES, n))
    out("bad_times_web_events.csv",
        bad_format_sample(raw["web_events"], cur["web_events"], "event_id", "event_time",
                          cleaning.TIMESTAMP_RULES, n))
    out("bad_dates_customers.csv",
        bad_format_sample(raw["customers"], cur["customers"], "customer_id", "signup_date", cleaning.DATE_RULES, n))
    for table, keys in QUARANTINE_KEYS.items():
        out(f"quarantine_{table}.csv", quarantine_sample(spark.read.parquet(cfg.quarantine(table)), keys, n))
    out("missing_region_customers.csv", missing_region_sample(raw["customers"], cur["customers"], n))
    for name, keys in AGGREGATE_KEYS.items():
        out(f"{name}.csv", head_sorted(spark.read.parquet(cfg.curated(name)), keys, agg_rows))

    summary, reasons = compare_counts(count_all(spark, cfg, raw), metrics)
    written["summary.csv"] = write_rows(out_dir / "summary.csv", SUMMARY_FIELDS, summary)
    written["quarantine_by_reason.csv"] = write_rows(out_dir / "quarantine_by_reason.csv", REASON_FIELDS, reasons)
    mismatches = sum(r["matches_metrics"] == "no" for r in summary + reasons)
    return {"files": written, "mismatches": mismatches}


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default="orders_5m", help="folder under <root>/raw/, curated/, quarantine/")
    p.add_argument("--storage-root", default="s3a://bigdata")
    p.add_argument("--out-dir", help="local output dir (default: /opt/spark/work-dir/results/samples/<dataset>)")
    p.add_argument("--rows-per-case", type=int, default=5,
                   help="keys per duplicate case, rows per date format / reject reason / missing-value case")
    p.add_argument("--agg-rows", type=int, default=10, help="first rows of each aggregate table")
    p.add_argument("--metrics-file", help="ETL metrics JSON to compare counts with "
                                          "(default: /opt/spark/work-dir/results/metrics/<dataset>.json)")
    return p.parse_args(argv)


def main(argv=None) -> int:
    """Export the samples; exit code 3 when a direct count disagrees with the metrics JSON."""
    args = parse_args(argv)
    out_dir = Path(args.out_dir or f"/opt/spark/work-dir/results/samples/{args.dataset}")
    metrics_file = Path(args.metrics_file or f"/opt/spark/work-dir/results/metrics/{args.dataset}.json")
    metrics = json.loads(metrics_file.read_text(encoding="utf-8")) if metrics_file.exists() else None
    spark = session.build_session(args.storage_root, app_name="export_samples")
    cfg = pipeline.RunConfig(dataset=args.dataset, storage_root=args.storage_root)
    result = export(spark, cfg, out_dir, args.rows_per_case, args.agg_rows, metrics)
    print(f"SAMPLES_INFO app_id={spark.sparkContext.applicationId} spark={spark.version} "
          f"metrics_file={metrics_file if metrics else 'missing'}")
    for name, rows in result["files"].items():
        print(f"SAMPLES_FILE {name} rows={rows}")
    print(f"SAMPLES_OK out_dir={out_dir} files={len(result['files'])} mismatches={result['mismatches']}")
    spark.stop()
    return 3 if result["mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
