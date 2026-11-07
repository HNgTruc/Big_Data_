# Bộ nhớ của agent spark-etl-engineer

Agent tự cập nhật file này khi làm việc (giữ dưới 200 dòng). Chỉ ghi điều đã xác nhận.

- [order_items key dedupe](order_items_key_dedupe.md) — dedupe on (order_id, line_no) since 2026-11-07; older runs used full-row, must re-run
- [Local Windows test env](local_windows_test_env.md) — pyspark 4.0.0 in .venv; Python worker crashes, no winutils; build test inputs JVM-side
