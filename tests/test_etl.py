"""ETL tests: generate a small dirty dataset, run the pipeline in local mode, check the results.

Needs pyspark, a JVM and the generator dependencies (numpy, pandas, pyarrow).
Run from the repo root: python -m pytest -q tests/test_etl.py
NOT RUN YET: written before pyspark could be installed where the tests were authored.
"""
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.data_generation.config import Config
from src.data_generation.generate import generate
from src.etl import cleaning, pipeline
from src.etl.session import build_session

ORDERS = 2000


class EtlPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="etl_test_"))
        cls.root = cls.tmp.as_uri()
        cls.manifest = generate(Config(orders=ORDERS, chunk_size=700, dirty_rate=0.05, seed=7),
                                cls.tmp / "raw" / "ds")
        cls.spark = build_session(cls.root, shuffle_partitions=2, app_name="etl_test")
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.metrics = pipeline.run(cls.spark, pipeline.RunConfig(
            dataset="ds", storage_root=cls.root, metrics_dir=str(cls.tmp / "metrics")))

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def read(self, area, table):
        return self.spark.read.parquet(f"{self.root}/{area}/ds/{table}")

    def test_orders_quarantine_matches_injected_defects(self):
        injected = self.manifest["defects_injected"]["orders"]
        reasons = self.metrics["tables"]["orders"]["quarantine_by_reason"]
        self.assertEqual(reasons.get("null_customer_id", 0), injected["null_customer_id"])
        self.assertEqual(reasons.get("orphan_customer_id", 0), injected["orphan_customer_id"])
        self.assertNotIn("invalid_order_date", reasons)  # bad formats are normalised, not rejected

    def test_orders_are_unique_and_dates_normalised(self):
        orders = self.read("curated", "orders")
        self.assertEqual(orders.count(), orders.select("order_id").distinct().count())
        self.assertEqual(orders.filter("order_date IS NULL").count(), 0)
        stats = self.metrics["tables"]["orders"]
        self.assertEqual(stats["clean_rows"] + stats["quarantined_rows"], ORDERS)
        self.assertEqual(stats["duplicates_removed"], self.manifest["defects_injected"]["orders"]["duplicate_rows"])

    def test_item_defects_are_quarantined(self):
        injected = self.manifest["defects_injected"]["order_items"]
        reasons = self.metrics["tables"]["order_items"]["quarantine_by_reason"]
        self.assertEqual(reasons.get("null_unit_price", 0), injected["null_unit_price"])
        self.assertEqual(reasons.get("non_positive_quantity", 0), injected["zero_quantity"])
        self.assertEqual(reasons.get("non_positive_price", 0), injected["negative_unit_price"])
        self.assertEqual(reasons.get("orphan_product_id", 0), injected["orphan_product_id"])

    def test_clean_items_are_valid_and_reference_clean_orders(self):
        items = self.read("curated", "order_items")
        self.assertEqual(items.filter("quantity <= 0 OR unit_price <= 0 OR unit_price IS NULL").count(), 0)
        orphans = items.join(self.read("curated", "orders"), "order_id", "left_anti").count()
        self.assertEqual(orphans, 0)

    def test_customers_and_events(self):
        customers = self.read("curated", "customers")
        self.assertEqual(customers.filter("region IS NULL").count(), 0)
        self.assertEqual(customers.count(), self.manifest["params"]["n_customers"])
        events = self.metrics["tables"]["web_events"]["quarantine_by_reason"]
        self.assertEqual(events.get("null_customer_id", 0),
                         self.manifest["defects_injected"]["web_events"]["null_customer_id"])
        self.assertEqual(self.read("curated", "web_events").filter("event_time IS NULL").count(), 0)

    def test_aggregates_are_consistent(self):
        revenue = self.read("curated", "agg_daily_revenue").agg({"revenue": "sum"}).collect()[0][0]
        by_group = self.read("curated", "agg_revenue_by_region_category").agg({"revenue": "sum"}).collect()[0][0]
        self.assertGreater(revenue, 0)
        self.assertAlmostEqual(revenue, by_group, delta=max(1.0, 0.001 * revenue))

    def test_metrics_file_and_timings(self):
        saved = json.loads((self.tmp / "metrics" / "ds.json").read_text())
        self.assertEqual(saved["processing_seconds_total"], self.metrics["processing_seconds_total"])
        self.assertEqual(set(saved["stage_seconds"]), {"dimensions", "orders", "order_items", "web_events", "aggregates"})

    def test_all_join_strategies_give_same_aggregate(self):
        results = {}
        for strategy in cleaning.JOIN_STRATEGIES:
            label = f"ds_{strategy}"
            m = pipeline.run(self.spark, pipeline.RunConfig(dataset="ds", storage_root=self.root,
                                                            run_label=label, join_strategy=strategy))
            agg = self.spark.read.parquet(f"{self.root}/curated/{label}/agg_revenue_by_region_category")
            results[strategy] = sorted(tuple(r) for r in agg.collect())
            self.assertEqual(m["tables"]["orders"]["clean_rows"], self.metrics["tables"]["orders"]["clean_rows"])
        self.assertEqual(results["auto"], results["broadcast"])
        self.assertEqual(results["auto"], results["shuffle"])


class DateParsingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = build_session("file:///tmp", shuffle_partitions=1, app_name="parse_test")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_known_formats_and_garbage(self):
        values = ["2024-03-05", "05/03/2024", "20240305", "05-03-2024", "not a date", None]
        df = self.spark.createDataFrame([(v,) for v in values], "d string")
        parsed = [r[0] for r in df.select(cleaning.parse_date(df["d"])).collect()]
        self.assertEqual(parsed[:4], [date(2024, 3, 5)] * 4)
        self.assertEqual(parsed[4:], [None, None])

    def test_timestamp_formats(self):
        values = ["2024-03-05 01:02:03", "05/03/2024 01:02:03", "20240305010203", "garbage"]
        df = self.spark.createDataFrame([(v,) for v in values], "t string")
        parsed = [r[0] for r in df.select(cleaning.parse_timestamp(df["t"])).collect()]
        self.assertEqual(len({p for p in parsed[:3]}), 1)
        self.assertIsNone(parsed[3])

    def test_unknown_join_strategy_rejected(self):
        df = self.spark.range(1)
        with self.assertRaises(ValueError):
            cleaning.hint(df, "nope")


if __name__ == "__main__":
    unittest.main()
