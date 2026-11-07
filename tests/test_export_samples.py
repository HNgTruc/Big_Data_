"""Tests for src/etl/export_samples.py: sample selection on hand-built frames, count comparison, end-to-end export.

Needs pyspark and a JVM: run inside the Spark image with tests/run_in_container.sh (see tests/README.md).
Skipped on Windows, where local Spark cannot run here (Python worker crash, no winutils).
"""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

pytest.importorskip("pyspark")
if sys.platform == "win32":
    pytest.skip("local Spark does not run on this Windows host; use run_in_container.sh", allow_module_level=True)

from pyspark.sql import functions as F  # noqa: E402

from src.data_generation.config import Config  # noqa: E402
from src.data_generation.generate import generate  # noqa: E402
from src.etl import cleaning, pipeline, schemas  # noqa: E402
from src.etl import export_samples as es  # noqa: E402
from src.etl.session import build_session  # noqa: E402

RAW_ORDERS = [
    (1, 10, "2024-01-05", "paid", "card"),
    (2, 11, "05/01/2024", "paid", "cod"),      # dd/MM/yyyy
    (2, 11, "05/01/2024", "paid", "cod"),      # duplicate of order 2
    (3, 12, "20240106", "shipped", "card"),    # yyyyMMdd
    (4, 13, "07-01-2024", "paid", "e_wallet"),  # dd-MM-yyyy
    (4, 13, "07-01-2024", "paid", "e_wallet"),  # duplicate of order 4
    (5, None, "2024-01-08", "paid", "cod"),
    (5, None, "2024-01-08", "paid", "cod"),    # duplicate, but quarantined -> not in curated
    (6, 14, "09/01/2024", "paid", "card"),
    (7, 15, "2024-01-10", "paid", "card"),
    (7, 15, "2024-01-10", "paid", "card"),
    (10, 15, "2024-01-11", "paid", "card"),
    (10, 15, "2024-01-11", "paid", "card"),   # two-digit key: must sort after 7, not as the string "10"
]


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class SampleSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = build_session("file:///tmp", shuffle_partitions=2, app_name="export_samples_test")
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.raw_orders = cls.spark.createDataFrame(RAW_ORDERS, schemas.ORDERS)
        customers = cls.spark.createDataFrame([(i, "north", "2021-01-01") for i in range(10, 16)], schemas.CUSTOMERS)
        cls.clean_orders, cls.rejected_orders = cleaning.clean_orders(cls.raw_orders, customers, "auto")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_duplicates_keep_smallest_keys_present_in_curated(self):
        rows = [r.asDict() for r in es.duplicate_sample(self.raw_orders, self.clean_orders, ["order_id"], 2).collect()]
        # Order 5 is duplicated but quarantined, so the two smallest kept keys are 2 and 4.
        self.assertEqual([(r["stage"], r["order_id"]) for r in rows],
                         [("raw", "2"), ("raw", "2"), ("curated", "2"), ("raw", "4"), ("raw", "4"), ("curated", "4")])
        curated_2 = next(r for r in rows if r["stage"] == "curated" and r["order_id"] == "2")
        self.assertEqual(curated_2["order_date"], "2024-01-05")

    def test_duplicates_are_sorted_by_numeric_key(self):
        rows = es.duplicate_sample(self.raw_orders, self.clean_orders, ["order_id"], 4).collect()
        curated = [r["order_id"] for r in rows if r["stage"] == "curated"]
        self.assertEqual(curated, ["2", "4", "7", "10"])

    def test_bad_dates_are_labelled_and_paired_with_curated_value(self):
        df = es.bad_format_sample(self.raw_orders, self.clean_orders, "order_id", "order_date",
                                  cleaning.DATE_RULES, 1)
        rows = [tuple(r) for r in df.collect()]
        # One row per non-standard format; for dd/MM/yyyy the smaller key (2) wins over 6.
        self.assertEqual(rows, [
            (4, "07-01-2024", "dd-MM-yyyy", "2024-01-07"),
            (2, "05/01/2024", "dd/MM/yyyy", "2024-01-05"),
            (3, "20240106", "yyyyMMdd", "2024-01-06"),
        ])

    def test_quarantine_sample_limits_rows_per_reason(self):
        q = self.spark.createDataFrame(
            [(9, 1, "null_unit_price"), (3, 1, "null_unit_price"), (5, 2, "null_unit_price"),
             (4, 1, "orphan_product_id")], "order_id long, line_no int, reject_reason string")
        rows = [tuple(r) for r in es.quarantine_sample(q, ["order_id", "line_no"], 2).collect()]
        self.assertEqual(rows, [("null_unit_price", 3, 1), ("null_unit_price", 5, 2), ("orphan_product_id", 4, 1)])

    def test_missing_region_shows_raw_null_and_curated_unknown(self):
        raw = self.spark.createDataFrame([(3, None, "01/02/2021"), (1, "south", "2021-01-01"), (2, None, "2021-03-04"),
                                          (2, None, "2021-03-04")], schemas.CUSTOMERS)
        rows = [tuple(r) for r in es.missing_region_sample(raw, cleaning.clean_customers(raw), 5).collect()]
        self.assertEqual(rows, [(2, None, "unknown", "2021-03-04", "2021-03-04"),
                                (3, None, "unknown", "01/02/2021", "2021-02-01")])

    def test_samples_are_deterministic(self):
        first = es.duplicate_sample(self.raw_orders, self.clean_orders, ["order_id"], 3).collect()
        second = es.duplicate_sample(self.raw_orders.repartition(3), self.clean_orders, ["order_id"], 3).collect()
        self.assertEqual(first, second)


COUNTS = {"tables": {"orders": {"raw_rows": 10, "curated_rows": 7, "quarantined_rows": 2,
                                "quarantine_by_reason": {"null_customer_id": 2}}},
          "aggregates": {"agg_daily_revenue": 3}}


class CompareCountsTest(unittest.TestCase):

    def test_match_and_mismatch_are_reported(self):
        metrics = {"tables": {"orders": {"raw_rows": 10, "clean_rows": 7, "quarantined_rows": 2,
                                         "duplicates_removed": 1,
                                         "quarantine_by_reason": {"null_customer_id": 1, "orphan_customer_id": 1}}},
                   "aggregate_rows": {"agg_daily_revenue": 3}}
        summary, reasons = es.compare_counts(COUNTS, metrics)
        self.assertEqual([r["matches_metrics"] for r in summary], ["yes", "yes"])
        self.assertEqual(summary[0]["duplicates_removed"], 1)
        self.assertEqual([(r["reject_reason"], r["rows"], r["metrics_rows"], r["matches_metrics"]) for r in reasons],
                         [("null_customer_id", 2, 1, "no"), ("orphan_customer_id", 0, 1, "no")])

    def test_missing_metrics_is_not_a_match(self):
        summary, reasons = es.compare_counts(COUNTS, None)
        self.assertEqual({r["matches_metrics"] for r in summary + reasons}, {"no_metrics"})


class ExportEndToEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="samples_test_"))
        cls.root = cls.tmp.as_uri()
        generate(Config(orders=2000, chunk_size=700, dirty_rate=0.05, seed=7), cls.tmp / "raw" / "ds")
        cls.spark = build_session(cls.root, shuffle_partitions=2, app_name="export_samples_e2e")
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.metrics = pipeline.run(cls.spark, pipeline.RunConfig(
            dataset="ds", storage_root=cls.root, metrics_dir=str(cls.tmp / "metrics")))
        cls.out = cls.tmp / "samples"
        cls.result = es.export(cls.spark, pipeline.RunConfig(dataset="ds", storage_root=cls.root), cls.out, 3, 4,
                               json.loads((cls.tmp / "metrics" / "ds.json").read_text(encoding="utf-8")))

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_case_file_has_rows_and_counts_match_metrics(self):
        self.assertEqual(self.result["mismatches"], 0)
        self.assertEqual(len(self.result["files"]), 14)
        for name in self.result["files"]:
            self.assertGreater(len(_read_csv(self.out / name)), 0, name)
        self.assertEqual({r["matches_metrics"] for r in _read_csv(self.out / "summary.csv")}, {"yes"})

    def test_bad_dates_are_normalised_in_curated(self):
        rows = _read_csv(self.out / "bad_dates_orders.csv")
        self.assertEqual({r["raw_format"] for r in rows}, {"dd/MM/yyyy", "yyyyMMdd", "dd-MM-yyyy"})
        for r in rows:
            self.assertRegex(r["curated_order_date"], r"^\d{4}-\d{2}-\d{2}$")
        times = _read_csv(self.out / "bad_times_web_events.csv")
        self.assertTrue(times and all(r["curated_event_time"] for r in times))

    def test_quarantine_files_cover_every_reason(self):
        for table in ("orders", "order_items", "web_events"):
            got = {r["reject_reason"] for r in _read_csv(self.out / f"quarantine_{table}.csv")}
            self.assertEqual(got, set(self.metrics["tables"][table]["quarantine_by_reason"]), table)

    def test_duplicates_appear_once_in_curated(self):
        rows = _read_csv(self.out / "duplicates_orders.csv")
        curated = [r["order_id"] for r in rows if r["stage"] == "curated"]
        self.assertEqual(curated, sorted(curated, key=int))
        self.assertEqual(len(curated), 3)
        self.assertEqual(len(set(curated)), 3)
        for key in curated:
            self.assertGreater(sum(r["stage"] == "raw" and r["order_id"] == key for r in rows), 1)
        self.assertEqual(self.spark.read.parquet(f"{self.root}/curated/ds/orders")
                         .filter(F.col("order_id").isin([int(k) for k in curated])).count(), 3)
