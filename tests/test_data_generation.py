"""Tests for src.data_generation (run on small data)."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from src.data_generation import tables
from src.data_generation.config import Config
from src.data_generation.generate import FILES, generate, main


def _run(tmp_path, name="out", **kw):
    kw.setdefault("orders", 2000)
    kw.setdefault("chunk_size", 700)  # forces several chunks
    out = tmp_path / name
    manifest = generate(Config(**kw), out)
    return out, manifest


def _digest(out):
    return {f: hashlib.sha256((out / f).read_bytes()).hexdigest() for f in FILES.values()}


def test_files_and_schema(tmp_path):
    out, _ = _run(tmp_path)
    assert list(pd.read_csv(out / "orders.csv").columns) == [
        "order_id", "customer_id", "order_date", "status", "payment_method"]
    assert list(pd.read_csv(out / "order_items.csv").columns) == [
        "order_id", "line_no", "product_id", "quantity", "unit_price"]
    assert list(pd.read_csv(out / "customers.csv").columns) == ["customer_id", "region", "signup_date"]
    assert list(pd.read_parquet(out / "products.parquet").columns) == ["product_id", "category", "list_price"]
    events = pd.read_json(out / "web_events.jsonl", lines=True, dtype=False)
    assert list(events.columns) == ["event_id", "event_time", "customer_id", "product_id", "event_type"]


def test_same_seed_same_bytes_and_different_seed_differs(tmp_path):
    a, _ = _run(tmp_path, "a", seed=1)
    b, _ = _run(tmp_path, "b", seed=1)
    c, _ = _run(tmp_path, "c", seed=2)
    assert _digest(a) == _digest(b)
    assert _digest(a)["orders.csv"] != _digest(c)["orders.csv"]


def test_manifest_matches_files(tmp_path):
    out, m = _run(tmp_path, dirty_rate=0.05)
    assert json.loads((out / "manifest.json").read_text()) == m
    orders = pd.read_csv(out / "orders.csv")
    assert len(orders) == m["rows_written"]["orders"]
    uniq = orders.drop_duplicates()
    d = m["defects_injected"]["orders"]
    assert len(orders) - len(uniq) == d["duplicate_rows"]
    assert uniq["customer_id"].isna().sum() == d["null_customer_id"]
    parsed = pd.to_datetime(uniq["order_date"], format="%Y-%m-%d", errors="coerce")
    assert parsed.isna().sum() == d["bad_order_date"]
    assert (uniq["customer_id"] > m["params"]["n_customers"]).sum() == d["orphan_customer_id"]


def test_item_defects_match_manifest(tmp_path):
    out, m = _run(tmp_path, dirty_rate=0.05)
    items = pd.read_csv(out / "order_items.csv").drop_duplicates()
    d = m["defects_injected"]["order_items"]
    assert items["unit_price"].isna().sum() == d["null_unit_price"]
    assert (items["quantity"] == 0).sum() == d["zero_quantity"]
    assert (items["unit_price"] < 0).sum() == d["negative_unit_price"]
    assert (items["product_id"] > m["params"]["n_products"]).sum() == d["orphan_product_id"]


def test_item_key_unique_and_key_duplicates_match_manifest(tmp_path):
    cfg = Config(orders=2000, chunk_size=700, dirty_rate=0.05, skew=True)
    rng = np.random.default_rng(cfg.seed)
    prices = tables.build_products(rng, cfg)["list_price"].to_numpy()
    clean = tables.build_items_chunk(rng, cfg, np.arange(1, 2001, dtype=np.int64), prices)
    assert not clean.duplicated(["order_id", "line_no"]).any()
    sizes = clean.groupby("order_id")["line_no"].agg(["min", "max", "count"])
    assert (sizes["min"] == 1).all() and (sizes["max"] == sizes["count"]).all()

    out, m = _run(tmp_path, dirty_rate=0.05, skew=True)
    items = pd.read_csv(out / "order_items.csv")
    key_dups = items.duplicated(["order_id", "line_no"]).sum()
    assert key_dups == m["defects_injected"]["order_items"]["duplicate_rows"]
    # Injected duplicates are full-row copies, so key and full-row dedupe agree.
    assert key_dups == items.duplicated().sum()


def test_rate_is_close_to_target(tmp_path):
    _, m = _run(tmp_path, orders=20000, chunk_size=20000, dirty_rate=0.02)
    for key, count in m["defects_injected"]["orders"].items():
        assert 0.015 * 20000 <= count <= 0.025 * 20000, key


def test_zero_rate_is_clean(tmp_path):
    out, m = _run(tmp_path, dirty_rate=0.0)
    assert all(v == 0 for t in m["defects_injected"].values() for v in t.values())
    orders = pd.read_csv(out / "orders.csv")
    assert not orders.isna().any().any() and not orders.duplicated().any()
    assert pd.to_datetime(orders["order_date"], format="%Y-%m-%d").notna().all()
    items = pd.read_csv(out / "order_items.csv")
    assert (items["quantity"] > 0).all() and (items["unit_price"] > 0).all()
    assert orders["order_id"].tolist() == list(range(1, 2001))


def test_skew_concentrates_on_hot_products(tmp_path):
    def hot_share(skew):
        out, m = _run(tmp_path, f"s{skew}", orders=20000, chunk_size=20000, dirty_rate=0.0, skew=skew)
        items = pd.read_csv(out / "order_items.csv")
        return (items["product_id"] <= m["params"]["hot_products"]).mean()

    assert hot_share(False) < 0.2
    assert hot_share(True) > 0.4


def test_refuses_non_empty_output_dir(tmp_path):
    (tmp_path / "x.txt").write_text("keep")
    assert main(["--orders", "100", "--out", str(tmp_path)]) == 1
    assert (tmp_path / "x.txt").read_text() == "keep"


@pytest.mark.parametrize("kw", [{"orders": 0}, {"dirty_rate": 0.9}, {"hot_products": 10_000}])
def test_invalid_config_rejected(kw):
    with pytest.raises(ValueError):
        Config(**{"orders": 100, **kw})
