"""Single-machine pandas version of the ETL rules in src/etl/cleaning.py and src/etl/aggregates.py.

The rules are copied (pyspark is not needed here); tests/test_experiments_pandas.py checks that the
date patterns, revenue statuses and column types still match the Spark sources. Each `clean_*`
returns (clean, rejected); `rejected` keeps the raw columns plus `reject_reason`, and when several
rules apply the first one listed wins, as in the Spark `when` chain.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

# Same (regex, Java pattern) pairs as src/etl/cleaning.py.
DATE_RULES = [
    (r"^\d{4}-\d{2}-\d{2}$", "yyyy-MM-dd"),
    (r"^\d{2}/\d{2}/\d{4}$", "dd/MM/yyyy"),
    (r"^\d{8}$", "yyyyMMdd"),
    (r"^\d{2}-\d{2}-\d{4}$", "dd-MM-yyyy"),
]
TIMESTAMP_RULES = [
    (r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "yyyy-MM-dd HH:mm:ss"),
    (r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", "dd/MM/yyyy HH:mm:ss"),
    (r"^\d{14}$", "yyyyMMddHHmmss"),
]
REVENUE_STATUSES = ("paid", "shipped", "delivered")
_JAVA_TOKENS = (("yyyy", "%Y"), ("MM", "%m"), ("dd", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S"))

# pandas dtypes equivalent to src/etl/schemas.py (nullable integers mirror Spark's nullable LongType).
CSV_DTYPES = {
    "customers": {"customer_id": "Int64", "region": "string", "signup_date": "string"},
    "orders": {"order_id": "Int64", "customer_id": "Int64", "order_date": "string",
               "status": "string", "payment_method": "string"},
    "order_items": {"order_id": "Int64", "line_no": "Int32", "product_id": "Int64",
                    "quantity": "Int32", "unit_price": "float64"},
}
EVENTS_DTYPES = {"event_id": "string", "event_time": "string", "customer_id": "Int64",
                 "product_id": "Int64", "event_type": "string"}


def java_to_strftime(pattern: str) -> str:
    """'dd/MM/yyyy HH:mm:ss' -> '%d/%m/%Y %H:%M:%S' (only the tokens used by the ETL)."""
    out = pattern
    for java, py in _JAVA_TOKENS:
        out = out.replace(java, py)
    return out


def _mask(cond) -> np.ndarray:
    """Boolean numpy array; missing values (pd.NA) count as False."""
    return pd.Series(cond).astype("boolean").fillna(False).to_numpy(dtype=bool)


def parse_first_match(values: pd.Series, rules) -> pd.Series:
    """Datetime from the first rule whose regex matches; NaT if none matches or parsing fails.

    A row matched by a rule is not retried with later rules (Spark `when` chain semantics).
    `re.ASCII` makes `\\d` mean [0-9] as in Java regex.
    """
    out = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    remaining = _mask(values.notna())
    text = values.astype("string")
    for pattern, java in rules:
        hit = remaining & _mask(text.str.contains(pattern, regex=True, flags=re.ASCII, na=False))
        if hit.any():
            out[hit] = pd.to_datetime(text[hit], format=java_to_strftime(java), errors="coerce")
        remaining &= ~hit
    return out


def parse_date(values: pd.Series) -> pd.Series:
    return parse_first_match(values, DATE_RULES)


def parse_timestamp(values: pd.Series) -> pd.Series:
    return parse_first_match(values, TIMESTAMP_RULES)


def assign_reasons(index: pd.Index, rules: list[tuple[np.ndarray, str]]) -> pd.Series:
    """First matching rule wins; rows matching no rule get None (clean)."""
    reason = np.full(len(index), None, dtype=object)
    free = np.ones(len(index), dtype=bool)
    for cond, name in rules:
        hit = free & cond
        reason[hit] = name
        free &= ~hit
    return pd.Series(reason, index=index, dtype=object)


def _split(df: pd.DataFrame, reason: pd.Series, clean_cols: list[str],
           reject_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    bad = reason.notna().to_numpy()
    clean = df.loc[~bad, clean_cols].reset_index(drop=True)
    rejected = df.loc[bad, reject_cols].assign(reject_reason=reason[bad].to_numpy()).reset_index(drop=True)
    return clean, rejected


def clean_customers(raw: pd.DataFrame) -> pd.DataFrame:
    """Dedupe by key; missing region -> 'unknown'; signup_date normalised (NaT if unparseable)."""
    df = raw.drop_duplicates(subset=["customer_id"], keep="first").copy()
    df["region"] = df["region"].fillna("unknown")
    df["signup_date"] = parse_date(df["signup_date"])
    return df.reset_index(drop=True)


def clean_orders(raw: pd.DataFrame, customers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.drop_duplicates(subset=["order_id"], keep="first").copy()
    df["_date"] = parse_date(df["order_date"])
    known = _mask(df["customer_id"].isin(customers["customer_id"].dropna()))
    reason = assign_reasons(df.index, [
        (_mask(df["customer_id"].isna()), "null_customer_id"),
        (_mask(df["_date"].isna()), "invalid_order_date"),
        (~known, "orphan_customer_id"),
    ])
    clean, rejected = _split(df, reason, ["order_id", "customer_id", "_date", "status", "payment_method"],
                             ["order_id", "customer_id", "status", "payment_method", "order_date"])
    return clean.rename(columns={"_date": "order_date"}), rejected


def clean_items(raw: pd.DataFrame, orders: pd.DataFrame, products: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dedupe on the key (order_id, line_no), then flag invalid lines."""
    df = raw.drop_duplicates(subset=["order_id", "line_no"], keep="first")
    known_p = _mask(df["product_id"].isin(products["product_id"].dropna()))
    known_o = _mask(df["order_id"].isin(orders["order_id"].dropna()))
    qty, price = df["quantity"], df["unit_price"]
    reason = assign_reasons(df.index, [
        (_mask(price.isna()), "null_unit_price"),
        (_mask(qty.isna()) | _mask(qty <= 0), "non_positive_quantity"),
        (_mask(price <= 0), "non_positive_price"),
        (~known_p, "orphan_product_id"),
        (~known_o, "no_clean_order"),
    ])
    cols = ["order_id", "line_no", "product_id", "quantity", "unit_price"]
    return _split(df, reason, cols, cols)


def clean_events(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.drop_duplicates(subset=["event_id"], keep="first").copy()
    df["_time"] = parse_timestamp(df["event_time"])
    reason = assign_reasons(df.index, [
        (_mask(df["customer_id"].isna()), "null_customer_id"),
        (_mask(df["_time"].isna()), "invalid_event_time"),
    ])
    clean, rejected = _split(df, reason, ["event_id", "_time", "customer_id", "product_id", "event_type"],
                             ["event_id", "customer_id", "product_id", "event_type", "event_time"])
    return clean.rename(columns={"_time": "event_time"}), rejected


def _revenue_lines(orders: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    counted = orders.loc[_mask(orders["status"].isin(REVENUE_STATUSES)), ["order_id", "customer_id", "order_date"]]
    lines = items.merge(counted, on="order_id", how="inner")
    lines["line_amount"] = lines["quantity"].astype("float64") * lines["unit_price"]
    return lines


def daily_revenue(orders: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Orders and revenue per day. Rounding is NumPy half-to-even (Spark uses HALF_UP)."""
    out = (_revenue_lines(orders, items).groupby("order_date", dropna=False)
           .agg(orders=("order_id", "nunique"), revenue=("line_amount", "sum")).reset_index())
    out["revenue"] = out["revenue"].round(2)
    return out.sort_values("order_date").reset_index(drop=True)


def revenue_by_region_category(orders: pd.DataFrame, items: pd.DataFrame, customers: pd.DataFrame,
                               products: pd.DataFrame) -> pd.DataFrame:
    lines = (_revenue_lines(orders, items)
             .merge(customers[["customer_id", "region"]], on="customer_id", how="inner")
             .merge(products[["product_id", "category"]], on="product_id", how="inner"))
    out = (lines.groupby(["region", "category"], dropna=False)
           .agg(revenue=("line_amount", "sum"), units=("quantity", "sum")).reset_index())
    out["revenue"] = out["revenue"].round(2)
    return out.sort_values(["region", "category"]).reset_index(drop=True)


def events_daily(events: pd.DataFrame) -> pd.DataFrame:
    df = events.assign(event_date=events["event_time"].dt.normalize())
    out = df.groupby(["event_date", "event_type"], dropna=False).size().reset_index(name="count")
    return out.sort_values(["event_date", "event_type"]).reset_index(drop=True)
