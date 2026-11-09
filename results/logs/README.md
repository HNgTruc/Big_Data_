# logs

Log từng lần chạy, kèm ngày giờ, phiên bản Spark, số worker, kích thước dữ liệu, seed.

- `etl_<bộ>.log`, `smoke_s3a.log`, `test_etl.log`: các lần chạy ETL/kiểm thử đầu tiên (một lần, chưa lặp lại).
- `<exp>/` (tạo khi chạy `src/experiments/<exp>/run.py`, kèm README): `<config>_r<k>.log` (stdout/stderr từng lần),
  `runner.log` (nhật ký bộ điều khiển: kiểm tra cụm, dừng/bật worker, lỗi), `eventlogs/` (event log Spark của
  `join_strategy`, `skew`; không đưa lên git).

- `skew/partition_stats.log`: log của phép đo kích thước phân vùng.
- `skew/plan_query4.txt`: cây kế hoạch đã chạy của truy vấn SQL số 4 ở ba ứng dụng, trích từ event log (event log không đưa lên git). Nguồn của sơ đồ so sánh kế hoạch ở mục 7.4 của báo cáo.
- `export_samples_<bộ>.log`: log của job xuất mẫu trước/sau xử lý `src/etl/export_samples.py` (đầu ra ở `results/samples/<bộ>/`).
- `test_etl.log`: lần chạy gần nhất của `tests/run_in_container.sh` (ETL, sinh dữ liệu, query bench, xuất mẫu).
- `environment.txt`: cấu hình máy thí nghiệm (CPU, RAM, ổ đĩa, Docker, giới hạn WSL, phiên bản MinIO).
- `test_host.log`: pytest các test chạy được trên host Windows (dựng báo cáo, bộ thí nghiệm, Pandas, sinh dữ liệu).
- `test_clone.log`: chạy thử các bước không cần Docker trên một bản clone mới (bộ sinh dữ liệu, `run_all`, pytest, `analyze_all`, dựng báo cáo), 2026-11-09.
- `screenshots/`: ảnh chụp Spark UI, Spark History Server, MinIO Console; danh sách ảnh và cách mở lại giao diện trong README của thư mục.

Trạng thái thí nghiệm: đã chạy bộ đo chính thức ngày 2026-11-07 (69 lần, commit 8164042).
