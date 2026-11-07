"""Cleaning rules. Each `clean_*` returns (clean_df, rejected_df).

Rejected rows keep the raw columns plus `reject_reason`. When several rules
apply to one row, the first rule listed in the `when` chain wins.
"""
from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

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
JOIN_STRATEGIES = ("auto", "broadcast", "shuffle")


def _first_match(col: Column, rules, parse) -> Column:
    expr = None
    for pattern, fmt in rules:
        branch = parse(col, fmt)
        expr = F.when(col.rlike(pattern), branch) if expr is None else expr.when(col.rlike(pattern), branch)
    return expr


def parse_date(col: Column) -> Column:
    """Date from any known format; null when no format matches."""
    return _first_match(col, DATE_RULES, F.to_date)


def parse_timestamp(col: Column) -> Column:
    return _first_match(col, TIMESTAMP_RULES, F.to_timestamp)


def hint(df: DataFrame, strategy: str) -> DataFrame:
    """Apply the join strategy under test to the (small) side of a join."""
    if strategy == "broadcast":
        return F.broadcast(df)
    if strategy == "shuffle":
        return df.hint("merge")
    if strategy == "auto":
        return df
    raise ValueError(f"unknown join strategy {strategy!r}; use one of {JOIN_STRATEGIES}")


def _split(flagged: DataFrame, clean_cols: list, reject_cols: list) -> tuple[DataFrame, DataFrame]:
    clean = flagged.filter(F.col("reject_reason").isNull()).select(*clean_cols)
    rejected = flagged.filter(F.col("reject_reason").isNotNull()).select(*reject_cols, "reject_reason")
    return clean, rejected


def clean_customers(raw: DataFrame) -> DataFrame:
    """Dedupe by key; missing region -> 'unknown'; signup_date normalised (null if unparseable)."""
    return (raw.dropDuplicates(["customer_id"])
            .withColumn("region", F.coalesce(F.col("region"), F.lit("unknown")))
            .withColumn("signup_date", parse_date(F.col("signup_date"))))


def clean_orders(raw: DataFrame, customers: DataFrame, strategy: str) -> tuple[DataFrame, DataFrame]:
    known = customers.select("customer_id").withColumn("_known", F.lit(True))
    flagged = (raw.dropDuplicates(["order_id"])
               .withColumn("_date", parse_date(F.col("order_date")))
               .join(hint(known, strategy), "customer_id", "left")
               .withColumn("reject_reason",
                           F.when(F.col("customer_id").isNull(), "null_customer_id")
                           .when(F.col("_date").isNull(), "invalid_order_date")
                           .when(F.col("_known").isNull(), "orphan_customer_id")))
    cols = ["order_id", "customer_id", "status", "payment_method"]
    return _split(flagged,
                  ["order_id", "customer_id", F.col("_date").alias("order_date"), "status", "payment_method"],
                  [*cols, "order_date"])


def clean_items(raw: DataFrame, orders: DataFrame, products: DataFrame, strategy: str) -> tuple[DataFrame, DataFrame]:
    """Dedupe on the key (order_id, line_no), then flag invalid lines.

    Input: raw items, curated orders and products. Output: (clean, rejected); both keep `line_no`.
    """
    known_products = products.select("product_id").withColumn("_p", F.lit(True))
    known_orders = orders.select("order_id").withColumn("_o", F.lit(True))
    flagged = (raw.dropDuplicates(["order_id", "line_no"])
               .join(hint(known_products, strategy), "product_id", "left")
               .join(known_orders, "order_id", "left")
               .withColumn("reject_reason",
                           F.when(F.col("unit_price").isNull(), "null_unit_price")
                           .when(F.col("quantity").isNull() | (F.col("quantity") <= 0), "non_positive_quantity")
                           .when(F.col("unit_price") <= 0, "non_positive_price")
                           .when(F.col("_p").isNull(), "orphan_product_id")
                           .when(F.col("_o").isNull(), "no_clean_order")))
    cols = ["order_id", "line_no", "product_id", "quantity", "unit_price"]
    return _split(flagged, cols, cols)


def clean_events(raw: DataFrame) -> tuple[DataFrame, DataFrame]:
    flagged = (raw.dropDuplicates(["event_id"])
               .withColumn("_time", parse_timestamp(F.col("event_time")))
               .withColumn("reject_reason",
                           F.when(F.col("customer_id").isNull(), "null_customer_id")
                           .when(F.col("_time").isNull(), "invalid_event_time")))
    cols = ["event_id", "customer_id", "product_id", "event_type"]
    return _split(flagged,
                  ["event_id", F.col("_time").alias("event_time"), *cols[1:]],
                  [*cols, "event_time"])
