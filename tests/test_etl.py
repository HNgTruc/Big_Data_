"""ETL tests: generate a small dirty dataset, run the pipeline in local mode, check the results.

Needs pyspark, a JVM and the generator dependencies (numpy, pandas, pyarrow).
Run inside the Spark image with tests/run_in_container.sh (see tests/README.md); all pass there.
On Windows most tests fail for environment reasons (Python worker crash, no winutils.exe).
"""
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from pyspark.sql import functions as F

from src.data_generation.config import Config
from src.data_generation.generate import generate
from src.etl import cleaning, pipeline, schemas
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

    def test_item_duplicates_removed_by_key(self):
        stats = self.metrics["tables"]["order_items"]
        self.assertEqual(stats["duplicates_removed"],
                         self.manifest["defects_injected"]["order_items"]["duplicate_rows"])
        items = self.read("curated", "order_items")
        self.assertEqual(items.columns, ["order_id", "line_no", "product_id", "quantity", "unit_price"])
        self.assertEqual(items.count(), items.select("order_id", "line_no").distinct().count())
        self.assertIn("line_no", self.read("quarantine", "order_items").columns)

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


class CleanItemsTest(unittest.TestCase):
    """clean_items on hand-made rows: the dedupe key is (order_id, line_no), not the full row."""

    @classmethod
    def setUpClass(cls):
        cls.spark = build_session("file:///tmp", shuffle_partitions=1, app_name="clean_items_test")
        # Inputs are built JVM-side (range / VALUES) so the test needs no Python worker.
        cls.orders = cls.spark.range(1, 3).withColumnRenamed("id", "order_id")
        cls.products = cls.spark.range(10, 12).withColumnRenamed("id", "product_id")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def items(self, rows):
        values = ", ".join("(" + ", ".join("NULL" if v is None else repr(v) for v in row) + ")" for row in rows)
        names = ", ".join(schemas.ORDER_ITEMS.fieldNames())
        df = self.spark.sql(f"SELECT * FROM VALUES {values} AS t({names})")
        return df.select([F.col(f.name).cast(f.dataType) for f in schemas.ORDER_ITEMS.fields])

    def test_identical_lines_with_different_line_no_are_kept(self):
        raw = self.items([
            (1, 1, 10, 2, 5.0),
            (1, 2, 10, 2, 5.0),  # same values, distinct line: must be kept
            (1, 2, 10, 2, 5.0),  # exact copy of line 2: must be removed
            (2, 1, 11, 1, 3.0),
        ])
        clean, rejected = cleaning.clean_items(raw, self.orders, self.products, "auto")
        self.assertEqual(sorted((r["order_id"], r["line_no"]) for r in clean.collect()),
                         [(1, 1), (1, 2), (2, 1)])
        self.assertEqual(rejected.count(), 0)

    def test_rejected_rows_keep_line_no_and_reason(self):
        raw = self.items([
            (1, 1, 10, 0, 5.0),     # non_positive_quantity
            (1, 2, 99, 1, 5.0),     # orphan_product_id
            (3, 1, 10, 1, 5.0),     # no_clean_order
            (2, 1, 11, 1, None),    # null_unit_price
            (2, 2, 11, 1, -1.0),    # non_positive_price
            (2, 2, 11, 1, -1.0),    # exact copy: deduped before flagging
        ])
        clean, rejected = cleaning.clean_items(raw, self.orders, self.products, "auto")
        self.assertEqual(clean.count(), 0)
        self.assertEqual(rejected.columns,
                         ["order_id", "line_no", "product_id", "quantity", "unit_price", "reject_reason"])
        got = sorted((r["order_id"], r["line_no"], r["reject_reason"]) for r in rejected.collect())
        self.assertEqual(got, [(1, 1, "non_positive_quantity"), (1, 2, "orphan_product_id"),
                               (2, 1, "null_unit_price"), (2, 2, "non_positive_price"),
                               (3, 1, "no_clean_order")])


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
