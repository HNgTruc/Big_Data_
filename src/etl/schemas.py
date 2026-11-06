"""Explicit schemas for the raw files (no schema inference).

Date/time columns are read as strings on purpose: the raw data contains several
formats, which `cleaning.py` normalises.
"""
from pyspark.sql.types import (
    DoubleType, IntegerType, LongType, StringType, StructField, StructType,
)

ORDERS = StructType([
    StructField("order_id", LongType()),
    StructField("customer_id", LongType()),
    StructField("order_date", StringType()),
    StructField("status", StringType()),
    StructField("payment_method", StringType()),
])

ORDER_ITEMS = StructType([
    StructField("order_id", LongType()),
    StructField("product_id", LongType()),
    StructField("quantity", IntegerType()),
    StructField("unit_price", DoubleType()),
])

CUSTOMERS = StructType([
    StructField("customer_id", LongType()),
    StructField("region", StringType()),
    StructField("signup_date", StringType()),
])

EVENTS = StructType([
    StructField("event_id", StringType()),
    StructField("event_time", StringType()),
    StructField("customer_id", LongType()),
    StructField("product_id", LongType()),
    StructField("event_type", StringType()),
])
