"""Controlled defect injection.

Each defect type draws from a disjoint slice of one uniform sample, so every
type hits ~`dirty_rate` of the rows and no row gets two defects. Duplicates are
exact copies appended afterwards. Every function returns the dirty frame and a
dict of exactly how many defects were injected.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def _masks(rng: np.random.Generator, n: int, rate: float, k: int) -> list[np.ndarray]:
    u = rng.random(n)
    return [(u >= i * rate) & (u < (i + 1) * rate) for i in range(k)]


def _bad_format(values: pd.Series, formats: list[str], rng: np.random.Generator) -> np.ndarray:
    parsed = pd.to_datetime(values)
    choice = rng.integers(0, len(formats), len(values))
    out = np.empty(len(values), dtype=object)
    for i, fmt in enumerate(formats):
        m = choice == i
        out[m] = parsed[m].dt.strftime(fmt).to_numpy()
    return out


def _add_duplicates(df: pd.DataFrame, rng: np.random.Generator, rate: float) -> tuple[pd.DataFrame, int]:
    k = int(round(rate * len(df)))
    if k == 0:
        return df.reset_index(drop=True), 0
    copies = df.iloc[rng.choice(len(df), k, replace=False)]
    merged = pd.concat([df, copies], ignore_index=True)
    return merged.iloc[rng.permutation(len(merged))].reset_index(drop=True), k


def dirty_orders(df: pd.DataFrame, rng: np.random.Generator, cfg: C.Config) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    m_null, m_orphan, m_date = _masks(rng, len(df), cfg.dirty_rate, 3)
    df["customer_id"] = df["customer_id"].astype("Int64")
    df.loc[m_null, "customer_id"] = pd.NA
    df.loc[m_orphan, "customer_id"] = cfg.n_customers + 1 + rng.integers(0, 1000, int(m_orphan.sum()))
    df.loc[m_date, "order_date"] = _bad_format(df.loc[m_date, "order_date"], C.BAD_DATE_FORMATS, rng)
    df, dups = _add_duplicates(df, rng, cfg.dirty_rate)
    return df, {"null_customer_id": int(m_null.sum()), "orphan_customer_id": int(m_orphan.sum()),
                "bad_order_date": int(m_date.sum()), "duplicate_rows": dups}


def dirty_items(df: pd.DataFrame, rng: np.random.Generator, cfg: C.Config) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    m_null, m_invalid, m_orphan = _masks(rng, len(df), cfg.dirty_rate, 3)
    df.loc[m_null, "unit_price"] = np.nan
    zero_qty = m_invalid & (rng.random(len(df)) < 0.5)
    neg_price = m_invalid & ~zero_qty
    df.loc[zero_qty, "quantity"] = 0
    df.loc[neg_price, "unit_price"] = -df.loc[neg_price, "unit_price"]
    df.loc[m_orphan, "product_id"] = cfg.n_products + 1 + rng.integers(0, 1000, int(m_orphan.sum()))
    df, dups = _add_duplicates(df, rng, cfg.dirty_rate)
    return df, {"null_unit_price": int(m_null.sum()), "zero_quantity": int(zero_qty.sum()),
                "negative_unit_price": int(neg_price.sum()), "orphan_product_id": int(m_orphan.sum()),
                "duplicate_rows": dups}


def dirty_customers(df: pd.DataFrame, rng: np.random.Generator, cfg: C.Config) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    m_null, m_date = _masks(rng, len(df), cfg.dirty_rate, 2)
    df.loc[m_null, "region"] = None
    df.loc[m_date, "signup_date"] = _bad_format(df.loc[m_date, "signup_date"], C.BAD_DATE_FORMATS, rng)
    df, dups = _add_duplicates(df, rng, cfg.dirty_rate)
    return df, {"null_region": int(m_null.sum()), "bad_signup_date": int(m_date.sum()),
                "duplicate_rows": dups}


def dirty_events(df: pd.DataFrame, rng: np.random.Generator, cfg: C.Config) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    m_null, m_time = _masks(rng, len(df), cfg.dirty_rate, 2)
    df["customer_id"] = df["customer_id"].astype("Int64")
    df.loc[m_null, "customer_id"] = pd.NA
    df.loc[m_time, "event_time"] = _bad_format(df.loc[m_time, "event_time"], C.BAD_TIME_FORMATS, rng)
    df, dups = _add_duplicates(df, rng, cfg.dirty_rate)
    return df, {"null_customer_id": int(m_null.sum()), "bad_event_time": int(m_time.sum()),
                "duplicate_rows": dups}
