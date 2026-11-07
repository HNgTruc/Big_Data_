"""Builders for clean (defect-free) table chunks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def _dates(rng: np.random.Generator, start, days: int, n: int) -> np.ndarray:
    offsets = rng.integers(0, days, n).astype("timedelta64[D]")
    return (np.datetime64(start) + offsets).astype(str).astype(object)


def build_products(rng: np.random.Generator, cfg: C.Config) -> pd.DataFrame:
    n = cfg.n_products
    return pd.DataFrame({
        "product_id": np.arange(1, n + 1, dtype=np.int64),
        "category": rng.choice(C.CATEGORIES, n),
        "list_price": np.round(rng.lognormal(3.5, 0.8, n) + 1.0, 2),
    })


def build_customers(rng: np.random.Generator, cfg: C.Config) -> pd.DataFrame:
    n = cfg.n_customers
    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1, dtype=np.int64),
        "region": rng.choice(C.REGIONS, n),
        "signup_date": _dates(rng, C.SIGNUP_START, C.SIGNUP_DAYS, n),
    })


def pick_products(rng: np.random.Generator, cfg: C.Config, n: int) -> np.ndarray:
    """Uniform product ids; with skew, `hot_share` of picks hit the first `hot_products` ids."""
    ids = rng.integers(1, cfg.n_products + 1, n)
    if cfg.skew:
        hot = rng.random(n) < cfg.hot_share
        ids[hot] = rng.integers(1, cfg.hot_products + 1, int(hot.sum()))
    return ids


def build_orders_chunk(rng: np.random.Generator, cfg: C.Config, start_id: int, n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "order_id": np.arange(start_id, start_id + n, dtype=np.int64),
        "customer_id": rng.integers(1, cfg.n_customers + 1, n),
        "order_date": _dates(rng, C.ORDER_START, C.ORDER_DAYS, n),
        "status": rng.choice(C.STATUSES, n, p=C.STATUS_WEIGHTS),
        "payment_method": rng.choice(C.PAYMENT_METHODS, n),
    })


def build_items_chunk(rng: np.random.Generator, cfg: C.Config, order_ids: np.ndarray,
                      list_prices: np.ndarray) -> pd.DataFrame:
    """1 + Poisson(items_mean - 1) items per order, capped at items_max.

    `line_no` runs 1..k inside each order, so (order_id, line_no) is the table key.
    """
    per_order = np.minimum(1 + rng.poisson(cfg.items_mean - 1.0, len(order_ids)), cfg.items_max)
    ids = np.repeat(order_ids, per_order)
    # Derived without drawing from rng, so all other columns keep their values for a given seed.
    order_starts = np.repeat(np.cumsum(per_order) - per_order, per_order)
    line_no = (np.arange(len(ids)) - order_starts + 1).astype(np.int32)
    product_ids = pick_products(rng, cfg, len(ids))
    return pd.DataFrame({
        "order_id": ids,
        "line_no": line_no,
        "product_id": product_ids,
        "quantity": rng.choice(C.QUANTITIES, len(ids), p=C.QUANTITY_WEIGHTS).astype(np.int32),
        "unit_price": list_prices[product_ids - 1],
    })


def build_events_chunk(rng: np.random.Generator, cfg: C.Config, start_id: int, n: int) -> pd.DataFrame:
    seconds = rng.integers(0, C.ORDER_DAYS * 86400, n).astype("timedelta64[s]")
    stamps = (np.datetime64(C.ORDER_START, "s") + seconds).astype(str)
    ids = np.arange(start_id, start_id + n)
    return pd.DataFrame({
        "event_id": np.char.add("E", np.char.zfill(ids.astype(str), 10)).astype(object),
        "event_time": np.char.replace(stamps, "T", " ").astype(object),
        "customer_id": rng.integers(1, cfg.n_customers + 1, n),
        "product_id": pick_products(rng, cfg, n),
        "event_type": rng.choice(C.EVENT_TYPES, n, p=C.EVENT_WEIGHTS),
    })
