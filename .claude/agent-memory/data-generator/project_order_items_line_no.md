---
name: project-order-items-line-no
description: order_items has key (order_id, line_no) since 2026-11-07; why it was added and the contract shared with the ETL
metadata:
  type: project
---

`order_items.csv` columns are `order_id, line_no, product_id, quantity, unit_price`; key = (order_id, line_no), line_no = 1..k per order, set in `build_items_chunk` without drawing from rng. Injected duplicates are full-row copies; no defects go into line_no. User approved 2026-11-07.

**Why:** the ETL deduped order_items by full row; with skew (hot products + fixed list price + few quantity values) legitimate distinct lines collided, so on orders_5m_skew it removed 255,378 rows vs 200,008 injected.

**How to apply:** this column order is a contract with the ETL (src/etl, owned by spark-etl-engineer) — do not reorder or dirty line_no without coordinating. All 5 datasets were regenerated 2026-11-07 with defaults (seed 42, chunk 500k, dirty 0.02); key dups == manifest duplicate_rows in all 5. See [[generator-params]].
