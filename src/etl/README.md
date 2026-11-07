# etl — job Spark Storage → Processing

Job PySpark: đọc dữ liệu thô từ MinIO theo schema khai báo, làm sạch, chuẩn hóa, join, tổng hợp, ghi Parquet vào `curated/` và dòng lỗi vào `quarantine/` (bucket MinIO). Agent phụ trách: `spark-etl-engineer`.
Thiết kế và quy tắc: [docs/design/etl.md](../../docs/design/etl.md).

| File | Vai trò |
|---|---|
| `schemas.py` | schema khai báo cho dữ liệu thô |
| `cleaning.py` | quy tắc làm sạch, trả về (sạch, bị loại + lý do) |
| `aggregates.py` | 3 bảng tổng hợp |
| `session.py` | tạo SparkSession (cấu hình ANSI, S3A, AQE...) |
| `pipeline.py` | điều phối, đo thời gian từng giai đoạn, ghi metrics |
| `etl_job.py` | CLI (`spark-submit`) |
| `smoke_s3a.py` | kiểm tra Spark ↔ MinIO (đã chạy thành công trên cụm) |
| `export_samples.py` | xuất mẫu CSV trước/sau xử lý + đối chiếu số dòng với metrics (chỉ đọc MinIO); kết quả và cách chạy ở [results/samples/](../../results/samples/README.md) |

Cách chạy trên cụm: xem [infra/README.md](../../infra/README.md), mục "Chạy job ETL".
Trạng thái: đã chạy trên cụm cả 5 bộ (`orders_500k` đến `orders_5m_skew`) với `order_items` bỏ trùng theo khoá (`order_id`, `line_no`); kết quả khớp manifest, xem `docs/design/etl.md`.
