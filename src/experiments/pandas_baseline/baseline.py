"""Single-machine pandas baseline of the ETL, timed with the same stages as src/etl/pipeline.py.

Run from the repository root (host, no Docker):
    python -m src.experiments.pandas_baseline.baseline --dataset orders_500k --metrics-out <file.json>

Reads data/raw/<dataset>/ from the local disk, writes Parquet to a temporary folder (deleted at the
end unless --keep-output), and compares row counts with manifest.json and the Spark metrics JSON.
Exit code 0 only if every check matches; 3 if any count differs (the JSON is still written), so the
experiment runner records the run as failed and keeps it out of the statistics.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import platform
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import pyarrow

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.pandas_baseline import pandas_etl as P  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
STAGES = ("dimensions", "orders", "order_items", "web_events", "aggregates")
# manifest defect name -> (table, quarantine reason) produced by the ETL rules
MANIFEST_REASONS = [
    ("orders", "null_customer_id", "null_customer_id"),
    ("orders", "orphan_customer_id", "orphan_customer_id"),
    ("order_items", "null_unit_price", "null_unit_price"),
    ("order_items", "zero_quantity", "non_positive_quantity"),
    ("order_items", "negative_unit_price", "non_positive_price"),
    ("order_items", "orphan_product_id", "orphan_product_id"),
    ("web_events", "null_customer_id", "null_customer_id"),
]
DUPLICATE_TABLES = ("customers", "orders", "order_items", "web_events")


def peak_rss_bytes() -> tuple[int | None, str]:
    """Peak resident memory of this process so far, and how it was measured."""
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            kernel32 = ctypes.WinDLL("kernel32")
            psapi = ctypes.WinDLL("psapi")
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize), "win32 GetProcessMemoryInfo.PeakWorkingSetSize"
        except OSError:
            pass
        return None, "unavailable"
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return (int(peak) if sys.platform == "darwin" else int(peak) * 1024), "resource.getrusage ru_maxrss"
    except (ImportError, OSError):
        return None, "unavailable"


def read_csv(path: Path, table: str) -> pd.DataFrame:
    # Spark's CSV reader treats only the empty string as null (nullValue=""); mirror that.
    """Read one raw CSV with the dtypes of src/etl/schemas.py."""
    return pd.read_csv(path, dtype=P.CSV_DTYPES[table], keep_default_na=False, na_values=[""])


def read_events(path: Path) -> pd.DataFrame:
    # dtype=False: no inference, so pandas does not turn the *_time column into datetimes on its own;
    # then cast to the types of src/etl/schemas.py (ids < 2**53, so the float -> Int64 cast is exact).
    """Read web_events.jsonl with the dtypes of src/etl/schemas.py."""
    return pd.read_json(path, lines=True, dtype=False).astype(P.EVENTS_DTYPES)


class StageTimer:
    """Wall-clock seconds per stage and per sub-step (read / transform / write)."""

    def __init__(self) -> None:
        self.stage_seconds: dict[str, float] = {}
        self.substeps: dict[str, dict[str, float]] = {}
        self.peak_after_stage: dict[str, int | None] = {}
        self._current: str | None = None

    @contextmanager
    def stage(self, name: str):
        """Time one ETL stage and record the peak memory after it."""
        self._current = name
        self.substeps[name] = {}
        start = time.perf_counter()
        yield
        self.stage_seconds[name] = round(time.perf_counter() - start, 3)
        self.peak_after_stage[name] = peak_rss_bytes()[0]

    @contextmanager
    def step(self, name: str):
        """Add the duration of one sub-step (read/transform/write) to the current stage."""
        start = time.perf_counter()
        yield
        steps = self.substeps[self._current]
        steps[name] = round(steps.get(name, 0.0) + time.perf_counter() - start, 3)


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _table_stats(raw_rows: int, clean_rows: int, rejected: pd.DataFrame | None) -> dict:
    by_reason = {} if rejected is None else {
        str(k): int(v) for k, v in rejected["reject_reason"].value_counts().items()}
    quarantined = sum(by_reason.values())
    return {"raw_rows": raw_rows, "clean_rows": clean_rows, "quarantined_rows": quarantined,
            "quarantine_by_reason": by_reason, "duplicates_removed": raw_rows - clean_rows - quarantined}


def run_baseline(raw_dir: Path, out_dir: Path) -> dict:
    """Run every stage; return timings, table statistics and aggregate row counts."""
    t = StageTimer()
    with t.stage("dimensions"):
        with t.step("read"):
            customers_raw = read_csv(raw_dir / "customers.csv", "customers")
            products = pd.read_parquet(raw_dir / "products.parquet")
        with t.step("transform"):
            customers = P.clean_customers(customers_raw)
        with t.step("write"):
            _write(customers, out_dir / "curated" / "customers.parquet")
            _write(products, out_dir / "curated" / "products.parquet")
    with t.stage("orders"):
        with t.step("read"):
            orders_raw = read_csv(raw_dir / "orders.csv", "orders")
        with t.step("transform"):
            orders, orders_rej = P.clean_orders(orders_raw, customers)
        with t.step("write"):
            _write(orders, out_dir / "curated" / "orders.parquet")
            _write(orders_rej, out_dir / "quarantine" / "orders.parquet")
    with t.stage("order_items"):
        with t.step("read"):
            items_raw = read_csv(raw_dir / "order_items.csv", "order_items")
        with t.step("transform"):
            items, items_rej = P.clean_items(items_raw, orders, products)
        with t.step("write"):
            _write(items, out_dir / "curated" / "order_items.parquet")
            _write(items_rej, out_dir / "quarantine" / "order_items.parquet")
    with t.stage("web_events"):
        with t.step("read"):
            events_raw = read_events(raw_dir / "web_events.jsonl")
        with t.step("transform"):
            events, events_rej = P.clean_events(events_raw)
        with t.step("write"):
            _write(events, out_dir / "curated" / "web_events.parquet")
            _write(events_rej, out_dir / "quarantine" / "web_events.parquet")
    with t.stage("aggregates"):
        with t.step("transform"):
            aggs = {"agg_daily_revenue": P.daily_revenue(orders, items),
                    "agg_revenue_by_region_category": P.revenue_by_region_category(orders, items, customers, products),
                    "agg_events_daily": P.events_daily(events)}
        with t.step("write"):
            for name, df in aggs.items():
                _write(df, out_dir / "curated" / f"{name}.parquet")

    # Statistics are computed after the timed stages, as in the Spark pipeline.
    tables = {
        "customers": _table_stats(len(customers_raw), len(customers), None),
        "products": _table_stats(len(products), len(products), None),
        "orders": _table_stats(len(orders_raw), len(orders), orders_rej),
        "order_items": _table_stats(len(items_raw), len(items), items_rej),
        "web_events": _table_stats(len(events_raw), len(events), events_rej),
    }
    peak, method = peak_rss_bytes()
    return {"stage_seconds": t.stage_seconds, "substep_seconds": t.substeps,
            "processing_seconds_total": round(sum(t.stage_seconds.values()), 3),
            "tables": tables, "aggregate_rows": {k: len(v) for k, v in aggs.items()},
            "peak_rss_bytes": peak, "peak_rss_method": method, "peak_rss_after_stage": t.peak_after_stage}


def compare(result: dict, manifest: dict | None, spark: dict | None) -> list[dict]:
    """Row-count checks against the generator manifest and the Spark metrics. ok=True means KHỚP."""
    checks = []

    def add(source: str, name: str, expected, actual) -> None:
        checks.append({"source": source, "check": name, "expected": expected, "actual": actual,
                       "ok": expected == actual})

    tables = result["tables"]
    if manifest:
        for table, rows in manifest.get("rows_written", {}).items():
            add("manifest", f"{table}.raw_rows", rows, tables[table]["raw_rows"])
        injected = manifest.get("defects_injected", {})
        for table in DUPLICATE_TABLES:
            add("manifest", f"{table}.duplicates_removed", injected.get(table, {}).get("duplicate_rows"),
                tables[table]["duplicates_removed"])
        for table, defect, reason in MANIFEST_REASONS:
            add("manifest", f"{table}.{reason}", injected.get(table, {}).get(defect),
                tables[table]["quarantine_by_reason"].get(reason, 0))
        # Wrong date formats are repaired, never rejected.
        add("manifest", "orders.invalid_order_date", 0,
            tables["orders"]["quarantine_by_reason"].get("invalid_order_date", 0))
        add("manifest", "web_events.invalid_event_time", 0,
            tables["web_events"]["quarantine_by_reason"].get("invalid_event_time", 0))
    if spark:
        for table, st in spark.get("tables", {}).items():
            mine = tables.get(table, {})
            for key in ("raw_rows", "clean_rows", "quarantined_rows", "duplicates_removed"):
                add("spark", f"{table}.{key}", st.get(key), mine.get(key))
            reasons = set(st.get("quarantine_by_reason", {})) | set(mine.get("quarantine_by_reason", {}))
            for reason in sorted(reasons):
                add("spark", f"{table}.{reason}", st.get("quarantine_by_reason", {}).get(reason, 0),
                    mine.get("quarantine_by_reason", {}).get(reason, 0))
        for name, rows in spark.get("aggregate_rows", {}).items():
            add("spark", f"{name}.rows", rows, result["aggregate_rows"].get(name))
    return checks


def parse_args(argv=None) -> argparse.Namespace:
    """Command-line options of the baseline."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", required=True, help="folder under --raw-root, e.g. orders_500k")
    p.add_argument("--raw-root", type=Path, default=REPO_ROOT / "data" / "raw")
    p.add_argument("--out-dir", type=Path, help="Parquet output folder (default: a new temporary folder)")
    p.add_argument("--keep-output", action="store_true", help="do not delete the Parquet output")
    p.add_argument("--spark-metrics", type=Path,
                   help="Spark metrics JSON to compare with (default: results/metrics/<dataset>.json)")
    p.add_argument("--metrics-out", type=Path, help="write the result JSON here")
    return p.parse_args(argv)


def main(argv=None) -> int:
    """Run the baseline once; 0 = all counts match, 2 = raw folder missing, 3 = some count differs."""
    # KHỚP/LỆCH must print even when stdout is a redirected file using a legacy Windows code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    raw_dir = args.raw_root / args.dataset
    if not raw_dir.is_dir():
        print(f"PANDAS_ERROR raw folder not found: {raw_dir}")
        return 2
    out_dir = args.out_dir or Path(tempfile.mkdtemp(prefix="pandas_baseline_"))
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        result = run_baseline(raw_dir, out_dir)
    finally:
        if not args.keep_output:
            shutil.rmtree(out_dir, ignore_errors=True)
    manifest_path = raw_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    spark_path = args.spark_metrics or REPO_ROOT / "results" / "metrics" / f"{args.dataset}.json"
    spark = json.loads(spark_path.read_text(encoding="utf-8")) if spark_path.exists() else None
    checks = compare(result, manifest, spark)
    for c in checks:
        verdict = "KHỚP" if c["ok"] else "LỆCH"
        print(f"{verdict} [{c['source']}] {c['check']}: expected={c['expected']} actual={c['actual']}")
    all_match = all(c["ok"] for c in checks)
    result.update({
        "dataset": args.dataset, "started_at": started, "raw_dir": str(raw_dir),
        "output_dir": str(out_dir), "output_kept": bool(args.keep_output),
        "seed": (manifest or {}).get("params", {}).get("seed"),
        "spark_metrics_compared": str(spark_path) if spark else None,
        "checks": checks, "all_match": all_match,
        "n_checks": len(checks), "n_mismatch": sum(not c["ok"] for c in checks),
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "pyarrow": pyarrow.__version__},
        "host": {"platform": platform.platform(), "machine": platform.machine()},
    })
    if args.metrics_out:
        args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_out.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    status = "PANDAS_OK" if all_match else "PANDAS_DONE"
    print(f"{status} processing_seconds_total={result['processing_seconds_total']} "
          f"stages={result['stage_seconds']} all_match={all_match} "
          f"checks={result['n_checks']} mismatches={result['n_mismatch']} peak_rss_bytes={result['peak_rss_bytes']}")
    if not all_match:
        print("PANDAS_ERROR row counts differ from the references (see LỆCH lines)")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
