# screenshots — ảnh chụp minh chứng

Ảnh chụp Spark UI, Spark History Server và MinIO Console, dùng cho chương 7 (Kết quả demo) và mục 7 của đề (minh chứng demo).
Tên file: `<số thứ tự>_<nội dung>.png`. Không sửa ảnh ngoài việc cắt khung.

## Cách mở lại giao diện

Chạy trong `infra/` (PowerShell):

- Spark Master UI: http://localhost:8090 (cụm phải đang chạy).
- MinIO Console: http://localhost:9001 (đăng nhập bằng tài khoản trong `infra/.env`).
- Spark History Server, đọc lại event log của thí nghiệm `skew` (24 ứng dụng):

  ```powershell
  docker compose run -d --rm --no-deps --name spark-history -p 18080:18080 `
    -e "SPARK_HISTORY_OPTS=-Dspark.history.fs.logDirectory=file:///opt/spark/work-dir/results/logs/skew/eventlogs" `
    spark-master /opt/spark/bin/spark-class org.apache.spark.deploy.history.HistoryServer
  ```

  Mở http://localhost:18080. Dừng: `docker stop spark-history`.
  Muốn xem `join_strategy` thì đổi `skew` thành `join_strategy` trong đường dẫn (event log không đưa lên git, chỉ có trên máy đã chạy đo).

Ứng dụng lần lặp r1 của từng cấu hình skew (lấy từ `results/metrics/skew/runs/<config>/r1/run_record.json`):

| Cấu hình | Application ID |
|---|---|
| balanced_auto_aqe | app-20261107153018-0026 |
| skew_auto_aqe | app-20261107153343-0028 |
| balanced_shuffle_aqe | app-20261107153716-0030 |
| balanced_shuffle_noaqe | app-20261107153933-0031 |
| skew_shuffle_aqe | app-20261107154233-0032 |
| skew_shuffle_noaqe | app-20261107154442-0033 |

## Danh sách ảnh

| File | Nơi chụp | Cần thấy trong ảnh | Trạng thái |
|---|---|---|---|
| `01_spark_master_workers.png` | Master UI, trang chủ | 2 worker ALIVE, 4 lõi, mỗi worker 2 GiB; executor 1024 MiB; danh sách ứng dụng đã hoàn thành | Đã có (2026-11-08) |
| `02_minio_bucket_root.png` | MinIO, bucket `bigdata` | Các thư mục `raw/`, `curated/`, `quarantine/` (và `smoke/` của lần kiểm tra kết nối) | Đã có (2026-11-08) |
| `03_minio_raw_orders_5m.png` | MinIO, `raw/orders_5m/` | 6 object (CSV, Parquet, JSON lines, manifest) kèm dung lượng | Đã có (2026-11-08) |
| `04_minio_curated_orders_5m.png` | MinIO, `curated/orders_5m/` | Các bảng sạch và bảng tổng hợp `agg_*` | Đã có (2026-11-08) |
| `05_minio_quarantine_orders_5m.png` | MinIO, `quarantine/orders_5m/` | Ba bảng cách ly: orders, order_items, web_events | Đã có (2026-11-08) |
| `06_history_app_list.png` | History Server, trang chủ | Danh sách ứng dụng skew đã đọc lại từ event log | Đã có (2026-11-08) |
| `07_skew_shuffle_aqe_sql_plan.png` | App `...-0032`, tab SQL / DataFrame, query ID 4 (ghi `order_items` sạch) | Sơ đồ kế hoạch có nút `SortMergeJoin(skew=true)` và `AQEShuffleRead` có partition bị tách (cùng tên nút mà `plan_check.csv` đếm) | Đã có (2026-11-08) |
| `08_skew_shuffle_noaqe_sql_plan.png` | App `...-0033`, tab SQL / DataFrame, query ID 4 | `SortMergeJoin` không có xử lý skew | Đã có (2026-11-08) |
| `09_skew_shuffle_noaqe_stage_tasks.png` | App `...-0033`, tab Stages, stage 19 (64 task, đọc shuffle 158 MiB) | Bảng Summary Metrics: thời gian task min/median/max lệch nhau | Đã có (2026-11-08) |
| `10_skew_shuffle_aqe_stage_tasks.png` | App `...-0032`, tab Stages, stage 32 (104 task: 64 + các task tách từ partition lệch) | Summary Metrics sau khi AQE tách partition | Đã có (2026-11-08) |
| `11_skew_auto_aqe_sql_plan.png` | App `...-0028`, tab SQL / DataFrame, query ID 4 | `BroadcastHashJoin` với `products`: không có shuffle theo khoá lệch | Đã có (2026-11-08) |
| `12_job_dag.png` | App `...-0032`, tab Jobs, mở một job | DAG Visualization: các stage và ranh giới shuffle | Đã có (2026-11-08) |
| `13_executors.png` | App `...-0032`, tab Executors | 2 executor trên 2 worker, task và dữ liệu shuffle mỗi executor | Đã có (2026-11-08) |

## Ghi chú khi dùng trong báo cáo

- Master UI ghi 68 ứng dụng đã hoàn thành: gồm 63 lần chạy Spark của bộ đo chính thức (69 lần trừ 6 lần Pandas chạy trên host)
  và các lần chạy thử trước đó. Số lần đo chính thức lấy từ `results/metrics/*/runs.csv`, không lấy từ ảnh.
- Tên nút và nhãn trong Spark UI có thể khác nhau giữa các phiên bản; chú thích ảnh theo đúng chữ hiện trên ảnh.

## Số đọc được trên ảnh (để trích trong báo cáo, nguồn là chính ảnh)

- `07`: `SortMergeJoin(skew=true)`, dòng "number of skewed partition splits: 49" ở nút `AQEShuffleRead` phía trên.
  Tổng duration của một WholeStageCodegen trên ảnh (vd 3.05 h) là tổng cộng dồn qua mọi task, không phải thời gian thực của lần chạy.
- `09` (không AQE, stage 19, 64 task): Shuffle Read median 1.5 MiB, max 15.5 MiB; Duration median 68 ms, max 0.5 s.
- `10` (có AQE, stage 32, 104 task): Shuffle Read median 1.5 MiB, max 1.9 MiB; Duration median 70 ms, max 0.2 s.
  Nghĩa là AQE san phẳng partition lệch, nhưng chênh lệch tuyệt đối dưới một giây mỗi task ở quy mô dữ liệu này.
- `11`: join với `products` là `BroadcastHashJoin` nên khoá lệch không đi qua shuffle; nút `HashAggregate` (bỏ trùng) phía trên có spill 1312.3 MiB.
- `13`: 2 executor, mỗi executor 2 lõi, Storage Memory 434.4 MiB (vùng nhớ hợp nhất của heap 1 GB mặc định), 609 và 637 task.
