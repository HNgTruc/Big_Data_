# Phụ lục C. Chi tiết cài đặt

Phụ lục này ghi chi tiết của chương 5: bảng cấu hình cụm, cấu trúc mã nguồn, lệnh chạy và bảng kiểm thử.

## C.1 Cấu hình cụm

Bảng: Cấu hình cụm Spark và phiên Spark của job ETL {#tbl:cau-hinh-cum}

| Mục | Giá trị | Ghi chú |
|---|---|---|
| Số worker | 2 (thí nghiệm (b) có lúc 1) | `spark-worker-1`, `spark-worker-2` |
| Lõi mỗi worker | 2 (`SPARK_WORKER_CORES`) | Tổng 4 lõi, `default_parallelism` = 4 |
| RAM tối đa mỗi worker | 2 GB (`SPARK_WORKER_MEMORY`) | Master UI hiển thị 4,0 GiB tổng |
| Heap mỗi executor | 1 GB (mặc định, không đặt `spark.executor.memory`) | Master UI: 1024,0 MiB mỗi executor |
| Số executor | 2 (mỗi worker một executor) | `executor_count` = 2 trong metrics |
| Bộ nhớ tiến trình master/worker | 512 MB (`SPARK_DAEMON_MEMORY`) | Giảm từ mặc định để vừa giới hạn 6 GB |
| `spark.sql.shuffle.partitions` | 8 | Mặc định của job |
| `spark.sql.adaptive.enabled` (AQE) | true | Tắt trong một số cấu hình của (e) |
| `spark.sql.autoBroadcastJoinThreshold` | 10 MB (10485760 byte) | Tắt (-1) ở `shuffle_noauto` |
| `skewJoin.skewedPartitionFactor` / `skewedPartitionThresholdInBytes` | 5 / 256 MB | Giá trị mặc định ghi trong metrics |
| `advisoryPartitionSizeInBytes` | 64 MB | Giá trị mặc định ghi trong metrics |
| `spark.sql.ansi.enabled` / `timeParserPolicy` | false / CORRECTED | Để ngày sai trả `NULL` |
| Dọn thư mục làm việc worker | `spark.worker.cleanup.enabled=true`, quét 10 phút/lần (mặc định 30 phút), xoá ứng dụng kết thúc quá 1 giờ (mặc định 7 ngày) | Xem mục 5.5 |

Nguồn: infra/docker-compose.yml, infra/.env.example, src/etl/session.py, results/metrics/scale_data/runs/orders_5m/r3/run_record.json (trường `metrics.conf`, `metrics.resources`, `default_parallelism`), results/logs/screenshots/01_spark_master_workers.png

## C.2 Cấu trúc mã nguồn

Bảng: Cấu trúc mã nguồn chính {#tbl:cau-truc-ma}

| Đường dẫn | Nội dung |
|---|---|
| `src/data_generation/` | Bộ sinh dữ liệu mô phỏng: `config.py` (hằng số, `Config`), `tables.py` (dựng bảng sạch), `dirty.py` (chèn lỗi), `writer.py` (ghi CSV/Parquet/JSON lines), `generate.py` (CLI) |
| `src/etl/` | Job Spark: `schemas.py` (lược đồ tường minh), `cleaning.py` (luật làm sạch), `aggregates.py` (3 bảng tổng hợp), `session.py` (tạo SparkSession), `pipeline.py` (điều phối, đo thời gian, ghi metrics), `etl_job.py` (CLI), `smoke_s3a.py` (kiểm tra kết nối), `export_samples.py` (xuất mẫu trước/sau) |
| `src/experiments/` | Bảy thí nghiệm, mỗi thí nghiệm có `run.py` và `analyze.py`; `common/` chứa bộ điều khiển, run record, thống kê, đọc event log, vẽ hình, job truy vấn `query_bench.py`; `run_all.py`, `analyze_all.py` |
| `tests/` | Kiểm thử cho bộ sinh, ETL, bộ thí nghiệm, baseline Pandas, job truy vấn, job xuất mẫu |
| `infra/` | `docker-compose.yml`, `.env.example`, hướng dẫn hạ tầng |
| `results/` | Log, số đo, hình, ảnh chụp, mẫu dữ liệu |

Nguồn: src/README.md, src/etl/README.md, src/experiments/README.md, tests/README.md

Mã tuân theo một số quy ước: lược đồ khai báo tường minh thay vì `inferSchema`; tham số chạy (bộ dữ liệu, chiến lược join, số phân vùng) đi qua dòng lệnh; thông tin đăng nhập MinIO lấy từ biến môi trường (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), không viết cứng.

## C.3 Cách chạy

Các bước tái lập toàn bộ (PowerShell; chi tiết ở `infra/README.md` và `src/experiments/README.md`):

1. Sinh dữ liệu trên host: `python -m src.data_generation.generate --orders 5000000` (thêm `--skew` cho bộ lệch; thêm `--overwrite` nếu thư mục đầu ra đã có `manifest.json`, như trên bản clone).
2. Dựng cụm trong `infra/`: `docker compose up -d`; kiểm tra Master UI tại http://localhost:8090 thấy 2 worker ALIVE.
3. Chép dữ liệu thô lên MinIO: `docker compose run --rm minio-init cp --recursive /data/raw/orders_5m local/bigdata/raw/`.
4. Chạy job ETL một lần:

```
docker compose run --rm --no-deps --name etl-driver spark-master
  /opt/spark/bin/spark-submit --master spark://spark-master:7077
  --conf spark.driver.host=etl-driver
  --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache
  --packages org.apache.hadoop:hadoop-aws:3.4.1
  /opt/spark/work-dir/src/etl/etl_job.py --dataset orders_5m
```

5. Chạy toàn bộ bộ thí nghiệm từ thư mục gốc: `python -m src.experiments.run_all --group all` (thêm `--overwrite` nếu `results/metrics/` đã có bản ghi), rồi `python -m src.experiments.analyze_all` để dựng lại CSV và hình.

**Dùng `docker compose run` thay vì `docker compose exec`.** Mỗi lần chạy tạo một container driver mới có tên cố định (`etl-driver`, `bench-driver`) và đặt `spark.driver.host` bằng tên đó để executor gọi ngược về driver. Lúc đầu job được chạy bằng `exec` trong container master; khi engine Docker sập (mục 5.5), `exec` báo lỗi `500` hoặc `No such exec instance`. Dùng `run` thì driver tách khỏi master, container được xoá sau khi chạy (`--rm`), và bộ điều khiển thí nghiệm có thể kiểm tra không còn container driver cũ trước mỗi lần chạy.

**Bộ đệm Ivy.** `--packages` khiến Spark phân giải và tải `hadoop-aws` cùng phụ thuộc mỗi lần nộp job. Lệnh dùng `spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache` (thư mục `data/ivy_cache/` trên host, đã nằm trong bind mount), nên jar chỉ tải một lần. Trong bộ đo chính thức, thời gian tải jar ghi trong run record chỉ vài chục mili giây mỗi lần (ví dụ 46 ms ở `scale_data/orders_5m/r3`).

## C.4 Các bộ kiểm thử

Bảng: Các bộ kiểm thử và kết quả {#tbl:kiem-thu}

| Tệp kiểm thử | Nội dung | Số test | Nơi chạy |
|---|---|---|---|
| `test_data_generation.py` | Lược đồ, tỉ lệ lỗi, khoá (`order_id`, `line_no`), manifest | 12 | Container và Windows |
| `test_etl.py` | ETL chạy local: quarantine và bỏ trùng khớp manifest, chuẩn hoá ngày, bỏ trùng theo khoá | 14 | Container |
| `test_query_bench.py` | Truy vấn `format` cho cùng kết quả trên dữ liệu thô sạch và Parquet; `cache` cùng kết quả có/không cache | 3 | Container |
| `test_export_samples.py` | Chọn mẫu xác định, so số đếm với metrics | 12 | Container |
| `test_experiments.py` | Thống kê, speedup/efficiency, dựng lệnh Docker, kiểm tra worker, run record, event log, cờ chất lượng | 29 | Windows |
| `test_experiments_pandas.py` | Luật làm sạch Pandas, đối chiếu hằng số với `src/etl/` | 15 | Windows |
| `test_build_docx.py` | Script dựng Word của báo cáo trên fixture Markdown nhỏ | 13 | Windows |

Nguồn: tests/README.md; results/logs/test_etl.log; results/logs/test_host.log

<!-- VERIFY
- SPARK_DAEMON_MEMORY 512m, cleanup interval 600, appDataTtl 3600: infra/docker-compose.yml. Mặc định 1800 giây và 604800 giây: Spark Standalone Mode 4.0.0 (verify-round1 A2).
- Master UI 4,0 GiB, 1024,0 MiB mỗi executor: ảnh results/logs/screenshots/01_spark_master_workers.png.
- ivy download 46 ms: results/metrics/scale_data/runs/orders_5m/r3/run_record.json trường ivy.download_ms.
- Số test 12/14/3/12/29/15/13: tests/README.md, results/logs/test_etl.log (41 passed), results/logs/test_host.log (69 passed).
- test_build_docx.py 13 test: log test_host.log chạy lại 2026-11-08 (69 = 13 + 29 + 15 + 12).
- Lệnh chạy: infra/README.md, src/experiments/README.md. `--overwrite`: src/data_generation/generate.py:128-130, src/experiments/common/runner.py:192-196, theo mã, chưa chạy thử (verify-round2 E1, E2).
-->
