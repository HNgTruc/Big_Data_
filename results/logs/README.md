# logs

Log từng lần chạy, kèm ngày giờ, phiên bản Spark, số worker, kích thước dữ liệu, seed.

- `etl_<bộ>.log`, `smoke_s3a.log`, `test_etl.log`: các lần chạy ETL/kiểm thử đầu tiên (một lần, chưa lặp lại).
- `<exp>/` (tạo khi chạy `src/experiments/<exp>/run.py`, kèm README): `<config>_r<k>.log` (stdout/stderr từng lần),
  `runner.log` (nhật ký bộ điều khiển: kiểm tra cụm, dừng/bật worker, lỗi), `eventlogs/` (event log Spark của
  `join_strategy`, `skew`; không đưa lên git).

Trạng thái thí nghiệm: chưa chạy.
