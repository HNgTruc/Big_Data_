---
name: order-items-key-dedupe
description: Why order_items is deduped on (order_id, line_no) instead of the full row; contract with the data generator
metadata:
  type: project
---

`order_items` is deduped on key (`order_id`, `line_no`); column order in order_items.csv is
order_id, line_no, product_id, quantity, unit_price. `line_no` is 1..k per order, never gets injected defects;
injected duplicates are full copies. Decided 2026-11-07, approved by the user.

**Why:** the old full-row `dropDuplicates()` deleted legitimate identical lines. On orders_5m_skew it removed
255,378 rows vs 200,008 injected and collapsed some defective rows (quarantine 41 short). Without skew the error
was ~100 rows per dataset.

**How to apply:** all ETL results produced before 2026-11-07 (500k, 1m, 2500k, 5m, 5m_skew) used the old schema and
must be regenerated and re-run; do not compare them against new runs on the items duplicate count. Any schema change
to order_items must be agreed with the data-generator agent (it owns src/data_generation/ and its tests).
