"""Tests for src/experiments/common/query_bench.py (Spark local mode).

Needs pyspark and a JVM: run inside the Spark image with tests/run_in_container.sh (see tests/README.md).
Skipped on Windows, where local Spark cannot run here (Python worker crash, no winutils).
"""
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
from src.etl import cleaning, pipeline  # noqa: E402
from src.etl.session import build_session  # noqa: E402
from src.experiments.common import query_bench as qb  # noqa: E402


def _rows(df):
    return sorted(tuple(r) for r in df.collect())


class QueryBenchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="qb_test_"))
        cls.root = cls.tmp.as_uri()
        # dirty_rate=0: raw data is already clean, so raw and curated must give the same answers
        generate(Config(orders=1500, chunk_size=600, dirty_rate=0.0, seed=11), cls.tmp / "raw" / "ds")
        cls.spark = build_session(cls.root, shuffle_partitions=2, app_name="query_bench_test")
        cls.spark.sparkContext.setLogLevel("ERROR")
        pipeline.run(cls.spark, pipeline.RunConfig(dataset="ds", storage_root=cls.root))

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_format_queries_agree_on_clean_raw_and_curated(self):
        raw = pipeline.read_raw(self.spark, pipeline.RunConfig(dataset="ds", storage_root=self.root))
        raw_q = qb.format_queries(raw["orders"].withColumn("order_date", cleaning.parse_date(F.col("order_date"))),
                                  raw["order_items"], raw["web_events"])
        cur = [self.spark.read.parquet(f"{self.root}/curated/ds/{t}") for t in ("orders", "order_items", "web_events")]
        cur_q = qb.format_queries(*cur)
        for name in ("q1_filter_count", "q2_events_by_type"):
            self.assertEqual(_rows(raw_q[name]), _rows(cur_q[name]), name)
        a, b = _rows(raw_q["q3_daily_revenue_join"]), _rows(cur_q["q3_daily_revenue_join"])
        self.assertEqual([r[0] for r in a], [r[0] for r in b])
        for (_, x), (_, y) in zip(a, b):
            self.assertAlmostEqual(x, y, places=6)

    def test_run_format_records_sizes_order_and_warmup(self):
        args = qb.parse_args(["format", "--dataset", "ds", "--storage-root", self.root, "--order", "curated-first",
                              "--out", str(self.tmp / "f.json")])
        result = qb.run_format(self.spark, args)
        self.assertEqual(result["format_order"], ["curated", "raw"])
        self.assertEqual(len(result["measurements"]), 2 * len(qb.FORMAT_QUERIES))
        self.assertEqual(result["measurements"][0]["format"], "curated")
        self.assertGreaterEqual(result["warmup_seconds"], 0)
        self.assertTrue(all(v and v["bytes"] > 0 for v in result["sizes"]["raw"].values()))
        self.assertIn("ReadSchema", result["measurements"][0]["plan_after_run"])

    def test_cache_gives_same_results_and_is_unpersisted(self):
        root = f"{self.root}/curated/ds"
        plain = {k: _rows(v) for k, v in qb.cache_queries(qb.cache_base(self.spark, root)).items()}
        cached_base = qb.cache_base(self.spark, root).cache()
        cached = {k: _rows(v) for k, v in qb.cache_queries(cached_base).items()}
        cached_base.unpersist(blocking=True)
        self.assertEqual(plain.keys(), cached.keys())
        for name in plain:
            self.assertEqual([r[0] for r in plain[name]], [r[0] for r in cached[name]], name)
        args = qb.parse_args(["cache", "--dataset", "ds", "--storage-root", self.root, "--mode", "cache",
                              "--k", "6", "--out", str(self.tmp / "c.json")])
        result = qb.run_cache(self.spark, args)
        self.assertEqual(len(result["measurements"]), 6)
        self.assertEqual(result["measurements"][5]["query"], qb.CACHE_QUERIES[0])  # list is cycled
        self.assertTrue(result["storage_after_materialize"])
        self.assertEqual(result["storage_after_unpersist"], [])
        self.assertIn("InMemoryTableScan", result["measurements"][0]["plan_after_run"])


if __name__ == "__main__":
    unittest.main()
