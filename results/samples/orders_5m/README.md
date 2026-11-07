# orders_5m — mẫu trước/sau xử lý

Mẫu **dữ liệu mô phỏng** của bộ `orders_5m` (5.000.000 đơn sinh với seed 42, tỉ lệ lỗi 2% mỗi loại; xem
`data/raw/orders_5m/manifest.json`). Mô tả từng file: [../README.md](../README.md).

## Lần chạy

| Mục | Giá trị |
|---|---|
| Ngày chạy | 2026-11-08 01:08:47–01:10:08 giờ Việt Nam (2026-11-07 18:08:47–18:10:08 UTC), thời gian đồng hồ của cả lệnh, không phải số đo hiệu năng |
| Commit | `7198a6c`; `src/etl/export_samples.py` lúc chạy **chưa được commit** (file mới trong cây làm việc) |
| Ứng dụng Spark | `app-20261107180856-0069`, Spark 4.0.0, cụm 2 worker, cấu hình mặc định của `session.build_session` |
| Tham số | `--dataset orders_5m`, `--rows-per-case 5`, `--agg-rows 10` (mặc định) |
| Đầu vào | `s3a://bigdata/raw/orders_5m/`, `curated/orders_5m/`, `quarantine/orders_5m/` |
| Log | `results/logs/export_samples_orders_5m.log` (dòng `SAMPLES_OK ... files=14 mismatches=0`) |

- Đầu ra ETL được đọc là của ứng dụng `app-20261106181012-0003` (thời điểm ghi object trên MinIO là 2026-11-06 18:10–18:11 UTC),
  trùng `app_id` trong `results/metrics/orders_5m.json`, nên so sánh trong `summary.csv` là cùng một lần ETL.
- `summary.csv` và `quarantine_by_reason.csv`: mọi số đếm trực tiếp đều khớp `results/metrics/orders_5m.json` (cột `matches_metrics` toàn `yes`).
- Tính xác định: chạy thêm một lần ra thư mục tạm, 14 file giống hệt từng byte (`diff -r`), sau đó xoá thư mục tạm.

## Lệnh

Trong `infra/`:

```powershell
docker compose run --rm --no-deps --name sample-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=sample-driver --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/export_samples.py --dataset orders_5m
```
