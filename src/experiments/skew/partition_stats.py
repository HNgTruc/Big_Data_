"""Rows and shuffle bytes per hash partition of order_items.product_id (evidence for the skew parameters).

Runs in Spark local mode inside the cluster image, reading data/raw/ from the bind mount (no MinIO,
no cluster). From infra/:

    docker compose run --rm --no-deps spark-master /opt/spark/bin/spark-submit --master local[2] \
        /opt/spark/work-dir/src/experiments/skew/partition_stats.py \
        --out /opt/spark/work-dir/results/metrics/skew/partition_stats.csv

For each dataset and partition count N, order_items is deduplicated on (order_id, line_no) as in the
ETL and shuffled with `repartition(N, "product_id")`, i.e. the same HashPartitioning (Murmur3 hash,
pmod N) a sort-merge join on product_id uses. AQE is off so the N partitions are not coalesced.
Rows per partition come from the shuffle-read metrics of the reduce tasks, bytes are the shuffle
bytes those tasks read (compressed blocks, the sizes AQE's skew detection compares).
Output: one CSV row per (dataset, N, partition) plus a printed summary per (dataset, N).
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pyspark.sql import SparkSession  # noqa: E402

from src.etl import schemas  # noqa: E402

TASK_END = "SparkListenerTaskEnd"


def shuffle_reads(event_log: Path) -> dict[int, list[tuple[int, int]]]:
    """stage id -> [(records read, bytes read)] of tasks that read shuffle data, from an event log."""
    stages: dict[int, list[tuple[int, int]]] = {}
    with event_log.open(encoding="utf-8") as fh:
        for line in fh:
            if TASK_END not in line:
                continue
            ev = json.loads(line)
            sr = (ev.get("Task Metrics") or {}).get("Shuffle Read Metrics") or {}
            records = int(sr.get("Total Records Read", 0))
            if records == 0 and not sr.get("Local Bytes Read") and not sr.get("Remote Bytes Read"):
                continue
            nbytes = int(sr.get("Local Bytes Read", 0)) + int(sr.get("Remote Bytes Read", 0))
            stages.setdefault(int(ev["Stage ID"]), []).append((records, nbytes))
    return stages


def measure(raw_root: str, dataset: str, n: int, work: Path) -> list[dict]:
    """Run one repartition job in its own SparkSession (own event log) and return per-partition rows."""
    log_dir = work / f"{dataset}_{n}"
    log_dir.mkdir(parents=True)
    spark = (SparkSession.builder.appName(f"partition_stats_{dataset}_{n}")
             .config("spark.sql.adaptive.enabled", "false")
             .config("spark.sql.shuffle.partitions", str(n))
             .config("spark.eventLog.enabled", "true")
             .config("spark.eventLog.dir", log_dir.as_uri())
             .config("spark.eventLog.compress", "false")
             .config("spark.eventLog.rolling.enabled", "false")
             .getOrCreate())
    items = spark.read.csv(f"{raw_root}/{dataset}/order_items.csv", schema=schemas.ORDER_ITEMS, header=True)
    (items.dropDuplicates(["order_id", "line_no"]).repartition(n, "product_id")
     .write.format("noop").mode("overwrite").save())
    spark.stop()
    log = next(p for p in log_dir.iterdir() if not p.name.startswith("."))
    stages = shuffle_reads(log)
    # the repartition stage is the last one that reads shuffle data and has exactly n tasks
    tasks = next(v for k, v in sorted(stages.items(), reverse=True) if len(v) == n)
    return [{"dataset": dataset, "partitions": n, "partition_rank": i, "rows": r, "shuffle_bytes": b}
            for i, (r, b) in enumerate(sorted(tasks, reverse=True))]


def summarize(rows: list[dict]) -> dict:
    """Max/median rows and bytes of one (dataset, N) measurement."""
    sizes = [r["shuffle_bytes"] for r in rows]
    counts = [r["rows"] for r in rows]
    med_b, med_r = statistics.median(sizes), statistics.median(counts)
    return {"dataset": rows[0]["dataset"], "partitions": rows[0]["partitions"], "rows_total": sum(counts),
            "rows_max": max(counts), "rows_median": med_r, "bytes_max": max(sizes), "bytes_median": med_b,
            "max_over_median_bytes": max(sizes) / med_b if med_b else None,
            "partitions_over_5x_median": sum(1 for s in sizes if s > 5 * med_b),
            "bytes_per_row": sum(sizes) / sum(counts) if sum(counts) else None}


def parse_args(argv=None) -> argparse.Namespace:
    """Command-line options of the partition statistics job."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw-root", default="file:///opt/spark/work-dir/data/raw")
    p.add_argument("--datasets", default="orders_5m,orders_5m_skew")
    p.add_argument("--partitions", default="8,64", help="comma-separated partition counts")
    p.add_argument("--out", required=True, help="CSV path (per partition); a *_summary.csv is written next to it")
    return p.parse_args(argv)


def main(argv=None) -> int:
    """Measure every (dataset, N) and write the two CSV files."""
    args = parse_args(argv)
    work = Path(tempfile.mkdtemp(prefix="partition_stats_"))
    per_partition, summary = [], []
    try:
        for dataset in [d for d in args.datasets.split(",") if d]:
            for n in [int(x) for x in args.partitions.split(",") if x]:
                rows = measure(args.raw_root, dataset, n, work)
                per_partition += rows
                summary.append(summarize(rows))
                print(f"PARTITION_STATS {json.dumps(summary[-1])}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for path, data in ((out, per_partition), (out.with_name(out.stem + "_summary.csv"), summary)):
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print(f"PARTITION_STATS_OK out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
