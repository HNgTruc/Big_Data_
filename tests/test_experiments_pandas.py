"""Tests for the pandas baseline: same rules as src/etl (checked against the Spark source text, without
importing pyspark) and behaviour on small hand-made tables."""
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.experiments.pandas_baseline import baseline
from src.experiments.pandas_baseline import pandas_etl as P

ETL_DIR = Path(__file__).resolve().parents[1] / "src" / "etl"
SPARK_TO_PANDAS = {"LongType": "Int64", "IntegerType": "Int32", "DoubleType": "float64", "StringType": "string"}


def _module_constant(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def _spark_schema(name: str) -> dict:
    """{column: pandas dtype} from a StructType([...StructField("c", XType())...]) in schemas.py."""
    tree = ast.parse((ETL_DIR / "schemas.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == name:
            fields = node.value.args[0].elts
            return {f.args[0].value: SPARK_TO_PANDAS[f.args[1].func.id] for f in fields}
    raise KeyError(name)


# ---- drift guards against the Spark job ---------------------------------------------------

def test_rules_match_spark_cleaning_source():
    assert P.DATE_RULES == _module_constant(ETL_DIR / "cleaning.py", "DATE_RULES")
    assert P.TIMESTAMP_RULES == _module_constant(ETL_DIR / "cleaning.py", "TIMESTAMP_RULES")
    assert P.REVENUE_STATUSES == _module_constant(ETL_DIR / "aggregates.py", "REVENUE_STATUSES")


def test_dtypes_match_spark_schemas():
    assert P.CSV_DTYPES["orders"] == _spark_schema("ORDERS")
    assert P.CSV_DTYPES["order_items"] == _spark_schema("ORDER_ITEMS")
    assert P.CSV_DTYPES["customers"] == _spark_schema("CUSTOMERS")
    assert P.EVENTS_DTYPES == _spark_schema("EVENTS")


# ---- date parsing -------------------------------------------------------------------------

def test_java_to_strftime():
    assert P.java_to_strftime("dd/MM/yyyy HH:mm:ss") == "%d/%m/%Y %H:%M:%S"
    assert P.java_to_strftime("yyyyMMdd") == "%Y%m%d"


def test_parse_date_formats_and_failures():
    s = pd.Series(["2024-03-05", "05/03/2024", "20240305", "05-03-2024", "31/02/2024", "2024/03/05", None, ""],
                  dtype="string")
    out = P.parse_date(s)
    assert list(out[:4]) == [pd.Timestamp("2024-03-05")] * 4
    assert out[4:].isna().all()  # impossible date, unknown format, null, empty


def test_parse_timestamp_formats():
    s = pd.Series(["2024-03-05 01:02:03", "05/03/2024 01:02:03", "20240305010203", "2024-03-05"], dtype="string")
    out = P.parse_timestamp(s)
    assert list(out[:3]) == [pd.Timestamp("2024-03-05 01:02:03")] * 3
    assert pd.isna(out[3])


def test_assign_reasons_first_rule_wins():
    idx = pd.RangeIndex(3)
    r = P.assign_reasons(idx, [(np.array([True, True, False]), "a"), (np.array([True, False, True]), "b")])
    assert list(r) == ["a", "a", "b"]


# ---- cleaning rules -----------------------------------------------------------------------

def _customers():
    return pd.DataFrame({"customer_id": pd.array([1, 2, 2, 3], dtype="Int64"),
                         "region": pd.array(["north", None, None, "south"], dtype="string"),
                         "signup_date": pd.array(["2021-01-02", "02/01/2021", "02/01/2021", "x"], dtype="string")})


def test_clean_customers():
    c = P.clean_customers(_customers())
    assert list(c["customer_id"]) == [1, 2, 3]
    assert list(c["region"]) == ["north", "unknown", "south"]
    assert pd.isna(c["signup_date"].iloc[2]) and c["signup_date"].iloc[1] == pd.Timestamp("2021-01-02")


def _orders():
    return pd.DataFrame({
        "order_id": pd.array([1, 1, 2, 3, 4, 5], dtype="Int64"),
        "customer_id": pd.array([1, 1, None, 99, 2, None], dtype="Int64"),
        "order_date": pd.array(["2024-01-01", "2024-01-01", "2024-01-02", "03/01/2024", "bad", "bad"],
                               dtype="string"),
        "status": pd.array(["paid", "paid", "paid", "delivered", "paid", "paid"], dtype="string"),
        "payment_method": pd.array(["cod"] * 6, dtype="string")})


def test_clean_orders_reasons_and_priority():
    clean, rej = P.clean_orders(_orders(), P.clean_customers(_customers()))
    assert list(clean["order_id"]) == [1]
    assert clean["order_date"].iloc[0] == pd.Timestamp("2024-01-01")
    reasons = dict(zip(rej["order_id"], rej["reject_reason"]))
    # order 5 has a null customer AND a bad date: the first rule (null_customer_id) wins
    assert reasons == {2: "null_customer_id", 3: "orphan_customer_id", 4: "invalid_order_date",
                       5: "null_customer_id"}
    assert list(rej.columns) == ["order_id", "customer_id", "status", "payment_method", "order_date",
                                 "reject_reason"]
    assert rej.loc[rej["order_id"] == 4, "order_date"].iloc[0] == "bad"  # raw value kept


def test_clean_items_rule_order_and_dedupe_by_key():
    items = pd.DataFrame({
        "order_id": pd.array([1, 1, 1, 1, 1, 1, 1, 9], dtype="Int64"),
        "line_no": pd.array([1, 1, 2, 3, 4, 5, 6, 1], dtype="Int32"),
        "product_id": pd.array([10, 10, 10, 10, 10, 77, 10, 10], dtype="Int64"),
        "quantity": pd.array([1, 1, 1, 0, None, 1, 2, 1], dtype="Int32"),
        "unit_price": [5.0, 5.0, np.nan, -5.0, 5.0, 5.0, -1.0, 5.0]})
    orders = pd.DataFrame({"order_id": pd.array([1], dtype="Int64")})
    products = pd.DataFrame({"product_id": pd.array([10], dtype="Int64")})
    clean, rej = P.clean_items(items, orders, products)
    assert list(zip(clean["order_id"], clean["line_no"])) == [(1, 1)]  # (1, 1) duplicate removed
    reasons = dict(zip(rej["line_no"].astype(int) + 10 * (rej["order_id"].astype(int) == 9), rej["reject_reason"]))
    assert reasons == {2: "null_unit_price", 3: "non_positive_quantity", 4: "non_positive_quantity",
                       5: "orphan_product_id", 6: "non_positive_price", 11: "no_clean_order"}


def test_clean_events():
    ev = pd.DataFrame({"event_id": pd.array(["E1", "E1", "E2", "E3"], dtype="string"),
                       "event_time": pd.array(["2024-01-01 00:00:01"] * 2 + ["20240101000002", "bad"],
                                              dtype="string"),
                       "customer_id": pd.array([1, 1, None, 3], dtype="Int64"),
                       "product_id": pd.array([1, 1, 1, 1], dtype="Int64"),
                       "event_type": pd.array(["view"] * 4, dtype="string")})
    clean, rej = P.clean_events(ev)
    assert list(clean["event_id"]) == ["E1"]
    assert dict(zip(rej["event_id"], rej["reject_reason"])) == {"E2": "null_customer_id", "E3": "invalid_event_time"}


def test_aggregates():
    orders = pd.DataFrame({"order_id": pd.array([1, 2, 3], dtype="Int64"),
                           "customer_id": pd.array([1, 2, 1], dtype="Int64"),
                           "order_date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
                           "status": ["paid", "cancelled", "delivered"], "payment_method": ["cod"] * 3})
    items = pd.DataFrame({"order_id": pd.array([1, 1, 2, 3], dtype="Int64"),
                          "line_no": pd.array([1, 2, 1, 1], dtype="Int32"),
                          "product_id": pd.array([10, 11, 10, 10], dtype="Int64"),
                          "quantity": pd.array([2, 1, 5, 1], dtype="Int32"), "unit_price": [1.5, 2.0, 9.0, 4.0]})
    daily = P.daily_revenue(orders, items)
    assert list(daily["orders"]) == [1, 1] and list(daily["revenue"]) == [5.0, 4.0]  # cancelled excluded
    customers = pd.DataFrame({"customer_id": pd.array([1, 2], dtype="Int64"), "region": ["north", "south"]})
    products = pd.DataFrame({"product_id": pd.array([10, 11], dtype="Int64"), "category": ["toys", "books"]})
    by = P.revenue_by_region_category(orders, items, customers, products)
    assert by.to_dict("list") == {"region": ["north", "north"], "category": ["books", "toys"],
                                  "revenue": [2.0, 7.0], "units": [1, 3]}
    events = pd.DataFrame({"event_time": pd.to_datetime(["2024-01-01 10:00", "2024-01-01 11:00", "2024-01-02 00:00"]),
                           "event_type": ["view", "view", "purchase"]})
    assert list(P.events_daily(events)["count"]) == [2, 1]


# ---- end-to-end on a generated dataset ----------------------------------------------------

def test_baseline_matches_generator_manifest(tmp_path):
    from src.data_generation.config import Config
    from src.data_generation.generate import generate
    generate(Config(orders=2000, chunk_size=700, dirty_rate=0.05, seed=7), tmp_path / "raw" / "ds")
    out = tmp_path / "metrics.json"
    code = baseline.main(["--dataset", "ds", "--raw-root", str(tmp_path / "raw"), "--out-dir", str(tmp_path / "pq"),
                          "--spark-metrics", str(tmp_path / "missing.json"), "--metrics-out", str(out)])
    assert code == 0
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["all_match"], [c for c in result["checks"] if not c["ok"]]
    assert result["n_checks"] == 18 and set(result["stage_seconds"]) == set(baseline.STAGES)
    assert not (tmp_path / "pq").exists()  # temporary Parquet output removed


def test_compare_flags_mismatch():
    result = {"tables": {t: {"raw_rows": 1, "clean_rows": 1, "quarantined_rows": 0, "duplicates_removed": 0,
                             "quarantine_by_reason": {}} for t in baseline.DUPLICATE_TABLES + ("products",)},
              "aggregate_rows": {"agg_daily_revenue": 3}}
    spark = {"tables": {"orders": {"raw_rows": 2, "clean_rows": 1, "quarantined_rows": 0, "duplicates_removed": 1,
                                   "quarantine_by_reason": {}}}, "aggregate_rows": {"agg_daily_revenue": 3}}
    checks = {c["check"]: c["ok"] for c in baseline.compare(result, None, spark)}
    assert checks["orders.raw_rows"] is False and checks["orders.clean_rows"] is True
    assert checks["agg_daily_revenue.rows"] is True


def test_peak_rss_is_measured():
    peak, method = baseline.peak_rss_bytes()
    if sys.platform == "win32":
        assert method.startswith("win32") and peak > 0
    else:
        assert method and (peak is None or peak > 0)


def test_mismatch_gives_nonzero_exit(tmp_path):
    from src.data_generation.config import Config
    from src.data_generation.generate import generate
    generate(Config(orders=500, chunk_size=500, seed=3), tmp_path / "raw" / "ds")
    wrong = tmp_path / "spark.json"
    wrong.write_text(json.dumps({"tables": {"orders": {"raw_rows": 1}}, "aggregate_rows": {}}), encoding="utf-8")
    out = tmp_path / "m.json"
    code = baseline.main(["--dataset", "ds", "--raw-root", str(tmp_path / "raw"), "--spark-metrics", str(wrong),
                          "--metrics-out", str(out)])
    assert code == 3
    assert json.loads(out.read_text(encoding="utf-8"))["all_match"] is False
