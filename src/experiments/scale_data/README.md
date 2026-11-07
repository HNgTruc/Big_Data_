# scale_data — (a) mở rộng theo kích thước dữ liệu

**Trạng thái: chưa chạy.**

- **Mục tiêu:** đo thời gian ETL (`src/etl/etl_job.py`) khi số đơn tăng 0,5M → 1M → 2,5M → 5M, cấu hình mặc định.
- **Giả thuyết (chưa kiểm chứng):** thời gian tăng chậm hơn tỉ lệ dữ liệu ở bộ nhỏ (chi phí cố định: lập lịch, khởi tạo, ghi nhiều file nhỏ) và tiến gần tuyến tính ở bộ lớn; thông lượng (dòng thô/giây) tăng theo kích thước rồi bão hoà.
- **Biến thay đổi:** bộ dữ liệu (`--datasets`).
- **Biến cố định:** `--join-strategy auto`, AQE bật, `spark.sql.shuffle.partitions=8`, 2 worker × 2 lõi × 2 GB, seed 42, Spark 4.0.0.
- **Chỉ số:** `processing_seconds_total` và thời gian từng giai đoạn (do job đo, không gồm khởi động); `wall_seconds` (cả lệnh docker); thông lượng = tổng dòng thô 5 bảng / `processing_seconds_total`; `data_ratio` và `time_ratio` so với bộ nhỏ nhất. Mỗi cấu hình 3 lần, ghi từng lần + mean, std (mẫu), min, max, n.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.scale_data.run --dry-run
python -m src.experiments.scale_data.run                       # 4 bộ × 3 lần, xen kẽ (r1 của mọi bộ, rồi r2, ...)
python -m src.experiments.scale_data.analyze
```

## Đầu ra

`results/metrics/scale_data/{runs/, runs.csv, summary.csv}`, `results/logs/scale_data/`, `results/figures/scale_data/{processing_time_vs_rows,throughput,stages}.png`. Trên MinIO: `curated/scale_data_<bộ>/` (ghi đè giữa các lần lặp; xoá bằng `--cleanup-curated` hoặc `python -m src.experiments.cleanup --exps scale_data`).

## Lưu ý

`wall_seconds` gồm cả việc tải jar `hadoop-aws` mỗi lần (phụ thuộc mạng); so sánh hiệu năng dùng `processing_seconds_total`.
