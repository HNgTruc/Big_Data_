"""Business aggregates over the cleaned tables."""
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from .cleaning import hint

REVENUE_STATUSES = ("paid", "shipped", "delivered")


def _revenue_lines(orders: DataFrame, items: DataFrame) -> DataFrame:
    counted = orders.filter(F.col("status").isin(*REVENUE_STATUSES)).select("order_id", "customer_id", "order_date")
    return items.join(counted, "order_id").withColumn("line_amount", F.col("quantity") * F.col("unit_price"))


def daily_revenue(orders: DataFrame, items: DataFrame) -> DataFrame:
    return (_revenue_lines(orders, items).groupBy("order_date")
            .agg(F.countDistinct("order_id").alias("orders"), F.round(F.sum("line_amount"), 2).alias("revenue"))
            .orderBy("order_date"))


def revenue_by_region_category(orders: DataFrame, items: DataFrame, customers: DataFrame,
                               products: DataFrame, strategy: str) -> DataFrame:
    lines = (_revenue_lines(orders, items)
             .join(hint(customers.select("customer_id", "region"), strategy), "customer_id")
             .join(hint(products.select("product_id", "category"), strategy), "product_id"))
    return (lines.groupBy("region", "category")
            .agg(F.round(F.sum("line_amount"), 2).alias("revenue"), F.sum("quantity").alias("units"))
            .orderBy("region", "category"))


def events_daily(events: DataFrame) -> DataFrame:
    return (events.withColumn("event_date", F.to_date("event_time"))
            .groupBy("event_date", "event_type").count().orderBy("event_date", "event_type"))
