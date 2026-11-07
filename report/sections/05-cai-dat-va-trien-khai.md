# Chương 5. Cài đặt và triển khai

Chương này liệt kê công nghệ và phiên bản đã dùng, cấu hình cụm, cấu trúc mã nguồn, cách chạy, kết quả kiểm thử và các sự cố đã gặp trong quá trình triển khai.

## 5.1 Công nghệ và phiên bản

Bảng: Công nghệ, phiên bản và vai trò {#tbl:cong-nghe}

| Công nghệ | Phiên bản | Vai trò trong kiến trúc |
|---|---|---|
| Apache Spark (PySpark) | 4.0.0, image `apache/spark:4.0.0-python3` | Xử lý phân tán: làm sạch, join, tổng hợp |
| Java (trong image Spark) | 17.0.15 | Môi trường chạy JVM của Spark |
| Python (trong image Spark) | 3.10.12 | Chạy job PySpark và kiểm thử trong container |
| Hadoop client / `hadoop-aws` | 3.4.1 / 3.4.1 | Connector S3A để Spark đọc ghi MinIO |
| AWS SDK bundle | 2.24.6 | Phụ thuộc của `hadoop-aws` |
| MinIO server và client `mc` | Image `cgr.dev/chainguard/minio:latest`, `cgr.dev/chainguard/minio-client:latest`; [CHƯA CÓ: số phiên bản MinIO trong image chưa kiểm] | Lưu trữ đối tượng S3 |
| Docker Desktop + WSL2 | Nhân WSL 6.18.54.1 | Chạy toàn bộ cụm trong container |
| Python trên host | 3.12.10 | Sinh dữ liệu, điều khiển thí nghiệm, baseline Pandas, vẽ hình |
| pandas / pyarrow / numpy | 3.1.1 / 26.0.1 / 2.5.4 | Sinh dữ liệu, baseline Pandas |
| matplotlib | 3.11.2 | Vẽ hình kết quả |

Nguồn: infra/.env.example, infra/README.md, results/logs/export_samples_orders_5m.log (Spark 4.0.0, Java 17.0.15, nhân WSL), results/logs/test_etl.log (Python 3.10.12), results/metrics/pandas_baseline/runs/orders_1m/r1/pandas_baseline.json (Python, pandas, pyarrow trên host), src/data_generation/README.md (numpy), tests/README.md (matplotlib)

**Lý do chọn Spark.** Đề gợi ý Apache Spark, PySpark, Spark SQL cho quy trình Storage → Processing. Spark xử lý dữ liệu trong bộ nhớ theo mô hình DAG, có DataFrame và Spark SQL với bộ tối ưu truy vấn, hỗ trợ broadcast join và cache (slide chương 5 [@slide-c5]). Phiên bản 4.0.0 được chọn vì image chính thức kéo được trên máy và chứa sẵn Hadoop 3.4.1, nên `hadoop-aws` phải cùng phiên bản 3.4.1.

**Lý do chọn MinIO và nguồn image Chainguard.** MinIO cung cấp API S3 chạy cục bộ, mô phỏng lớp lưu trữ đối tượng của Data Lake mà không cần dịch vụ đám mây. Khi triển khai (2026-11-06), các image `minio/minio`, `minio/mc` trên Docker Hub và `quay.io/minio/*` không kéo được trên máy. Image MinIO do Chainguard đóng gói kéo được, nên được dùng thay thế [@chainguard-minio] [@bex-minio]. Image client của Chainguard không có shell, nên mọi lệnh `mc` được gọi trực tiếp qua `docker compose run`.

## 5.2 Cấu hình cụm

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
| Dọn thư mục làm việc worker | `spark.worker.cleanup.enabled=true`, quét 10 phút/lần, xoá ứng dụng kết thúc quá 1 giờ | Xem mục 5.6 |

Nguồn: infra/docker-compose.yml, infra/.env.example, src/etl/session.py, results/metrics/scale_data/runs/orders_5m/r3/run_record.json (trường `metrics.conf`, `metrics.resources`, `default_parallelism`), results/logs/screenshots/01_spark_master_workers.png

Trường `resources` trong metrics ghi `spark.executor.memory` = `null`, nghĩa là không đặt và Spark dùng mặc định 1g [@spark-config]. Ảnh chụp tab Executors (@fig:ss-executors ở chương 7) cho thấy mỗi executor có Storage Memory 434,4 MiB: đây là vùng nhớ hợp nhất (thực thi và lưu trữ) tách ra từ heap 1 GB. Với 2 GB cho phép trên mỗi worker, việc giữ heap 1 GB để lại khoảng trống cho hệ điều hành, MinIO và master trong giới hạn 6 GB của WSL2. Đánh đổi là executor dễ tràn dữ liệu ra đĩa hơn khi shuffle hoặc cache (thấy rõ ở thí nghiệm (f), mục 6.9).

## 5.3 Cấu trúc mã nguồn

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

## 5.4 Cách chạy

Các bước tái lập toàn bộ (PowerShell; chi tiết ở `infra/README.md` và `src/experiments/README.md`):

1. Sinh dữ liệu trên host: `python -m src.data_generation.generate --orders 5000000` (thêm `--skew` cho bộ lệch).
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

5. Chạy toàn bộ bộ thí nghiệm từ thư mục gốc: `python -m src.experiments.run_all --group all`, rồi `python -m src.experiments.analyze_all` để dựng lại CSV và hình.

**Dùng `docker compose run` thay vì `docker compose exec`.** Mỗi lần chạy tạo một container driver mới có tên cố định (`etl-driver`, `bench-driver`) và đặt `spark.driver.host` bằng tên đó để executor gọi ngược về driver. Lúc đầu job được chạy bằng `exec` trong container master; khi engine Docker sập (mục 5.6), `exec` báo lỗi `500` hoặc `No such exec instance`. Dùng `run` thì driver tách khỏi master, container được xoá sau khi chạy (`--rm`), và bộ điều khiển thí nghiệm có thể kiểm tra không còn container driver cũ trước mỗi lần chạy.

**Bộ đệm Ivy.** `--packages` khiến Spark phân giải và tải `hadoop-aws` cùng phụ thuộc mỗi lần nộp job. Lệnh dùng `spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache` (thư mục `data/ivy_cache/` trên host, đã nằm trong bind mount), nên jar chỉ tải một lần. Trong bộ đo chính thức, thời gian tải jar ghi trong run record chỉ vài chục mili giây mỗi lần (ví dụ 46 ms ở `scale_data/orders_5m/r3`).

## 5.5 Kiểm thử

Bảng: Các bộ kiểm thử và kết quả {#tbl:kiem-thu}

| Tệp kiểm thử | Nội dung | Số test | Nơi chạy |
|---|---|---|---|
| `test_data_generation.py` | Lược đồ, tỉ lệ lỗi, khoá (`order_id`, `line_no`), manifest | 12 | Container và Windows |
| `test_etl.py` | ETL chạy local: quarantine và bỏ trùng khớp manifest, chuẩn hoá ngày, bỏ trùng theo khoá | 14 | Container |
| `test_query_bench.py` | Truy vấn `format` cho cùng kết quả trên dữ liệu thô sạch và Parquet; `cache` cùng kết quả có/không cache | 3 | Container |
| `test_export_samples.py` | Chọn mẫu xác định, so số đếm với metrics | 12 | Container |
| `test_experiments.py` | Thống kê, speedup/efficiency, dựng lệnh Docker, kiểm tra worker, run record, event log, cờ chất lượng | 29 | Windows |
| `test_experiments_pandas.py` | Luật làm sạch Pandas, đối chiếu hằng số với `src/etl/` | 15 | Windows |

Nguồn: tests/README.md; results/logs/test_etl.log

Lần chạy trong container Spark (Python 3.10.12, pyspark 4.0.0) cho kết quả **41 passed** trong 64,91 giây (12 + 14 + 3 + 12 test; log `results/logs/test_etl.log`). Hai bộ chạy trên Windows cho 44 passed theo `tests/README.md`; log của lần chạy này không được lưu trong `results/` [CHƯA CÓ: log kiểm thử phía host chưa lưu vào results/logs]. `test_etl.py` không chạy được trực tiếp trên Windows (Python worker của Spark bị lỗi và ghi Parquet cần `winutils.exe`), nên được chạy trong container.

Ngoài kiểm thử đơn vị, tính đúng của job được kiểm chứng bằng đối chiếu số đếm:

- Với cả năm bộ dữ liệu, số dòng thô, số dòng trùng đã bỏ và từng lý do cách ly khớp hoàn toàn với số lỗi đã chèn trong manifest (`docs/design/etl.md`).
- Mỗi lần chạy baseline Pandas thực hiện 49 phép đối chiếu với manifest và với metrics của Spark; cả 6 lần đều khớp, không lệch phép nào (`results/metrics/pandas_baseline/runs.csv`, cột `all_match`, `n_mismatch`).
- Job xuất mẫu đếm lại trực tiếp trên MinIO và so với metrics: `SAMPLES_OK ... mismatches=0` (`results/logs/export_samples_orders_5m.log`).
- Trong mọi bảng tổng hợp của bộ thí nghiệm, số dòng sạch, cách ly và trùng giống nhau giữa các lần chạy của cùng một bộ dữ liệu (cột `counts_consistent` = True trong các `summary.csv` của thí nghiệm ETL).

## 5.6 Sự cố đã gặp và cách xử lý

**Engine Docker Desktop sập (mã `0xc00000fd`).** Khi chạy job, toàn bộ container chuyển sang `Exited (255)` và engine WSL2 khởi động lại; log Docker Desktop ghi `wsl-bootstrap ... exit status 0xc00000fd`. Có báo cáo lỗi tương tự với cùng mã lỗi và cùng nhân WSL [@docker-767], nhưng nguyên nhân chưa được xác nhận ở đó. Lúc sập, giới hạn bộ nhớ của Docker là 9,7 GiB trên máy đang dùng khoảng 72% RAM. Sau khi đặt `.wslconfig` với `memory=6GB`, `processors=8`, job chạy thành công và không gặp lại sự cố trong bộ đo chính thức (69 lần chạy đều thành công). Đồ án không khẳng định áp lực bộ nhớ là nguyên nhân; đây chỉ là biện pháp đã có hiệu quả trong thực tế.

**Đầy đĩa do thư mục làm việc của worker.** Sau 7 lần chạy, `/opt/spark/work` trên mỗi worker chiếm khoảng 4,1 GB, vì mỗi ứng dụng chép lại các jar của `--packages` vào thư mục riêng và worker không tự xoá. Ổ C chỉ còn 2,6 GB vì tệp đĩa ảo của Docker (37,7 GB) nằm trên C. Cách xử lý: bật dọn dẹp tự động của worker (`spark.worker.cleanup.enabled`, quét 10 phút một lần, xoá thư mục của ứng dụng đã kết thúc quá 1 giờ) [@spark-standalone] và chuyển đĩa ảo Docker sang ổ D. Hệ quả: log executor chỉ còn trên worker khoảng 1 giờ; log driver vẫn lưu đầy đủ trong `results/logs/`. Vì C: và D: cùng một ổ vật lý, việc chuyển ổ chỉ giải quyết dung lượng, không giảm tranh chấp I/O.

**Tải lại jar mỗi lần chạy.** Bộ đệm Ivy mặc định nằm trong `/tmp` của container driver, mất đi khi container bị xoá, nên mỗi lần chạy phải tải lại `hadoop-aws` và AWS SDK. Chuyển bộ đệm vào `data/ivy_cache/` trên host (mục 5.4) loại bỏ chi phí này và loại bỏ sự phụ thuộc vào Internet trong lúc đo.

**Các trở ngại nhỏ khác.** Cổng 8080 trên máy đã bị chiếm nên Master UI được chuyển sang 8090. Lệnh `mc cp --recursive` chép cả thư mục nguồn vào đích, nên đích phải là `raw/` chứ không phải `raw/<bộ>`, nếu không dữ liệu bị lồng thêm một cấp. Trước khi đo chính thức, các ứng dụng nặng trên host được đóng, Windows Update được tạm dừng và các container không thuộc dự án được dừng.

Nguồn mục 5.6: infra/README.md (mục "Sự cố engine Docker Desktop sập", "Dung lượng đĩa", "Đưa dữ liệu thô lên MinIO"), src/experiments/README.md (mục "Bộ đệm Ivy").

<!-- VERIFY
- Java 17.0.15, Spark 4.0.0, nhân 6.18.54.1-microsoft-standard-WSL2: results/logs/export_samples_orders_5m.log dòng 29–31.
- Python 3.10.12, 41 passed in 64.91s: results/logs/test_etl.log.
- hadoop-aws 3.4.1, awssdk bundle 2.24.6: results/logs/export_samples_orders_5m.log dòng 10–16; infra/README.md.
- Python 3.12.10, pandas 3.1.1, pyarrow 26.0.1 trên host: results/metrics/pandas_baseline/runs/orders_1m/r1/pandas_baseline.json trường versions.
- numpy 2.5.4: src/data_generation/README.md (máy người dùng, ngày 2026-11-07); chưa chắc đây là môi trường của bộ đo.
- matplotlib 3.11.2: tests/README.md (.venv-exp).
- Image Chainguard và lý do (Docker Hub, quay.io không kéo được 2026-11-06): infra/README.md, infra/.env.example; hai bài blog trong infra/README.md (cần mở URL xác nhận nội dung).
- Spark chính thức chứa Hadoop 3.4.1 (hadoop-client-api-3.4.1.jar): infra/README.md.
- SPARK_DAEMON_MEMORY 512m, cleanup interval 600, appDataTtl 3600: infra/docker-compose.yml.
- Master UI 4,0 GiB, 1024,0 MiB mỗi executor: ảnh results/logs/screenshots/01_spark_master_workers.png.
- Storage Memory 434,4 MiB: ảnh 13 và results/logs/screenshots/README.md. "Vùng nhớ hợp nhất tách ra từ heap 1 GB": cần đối chiếu tài liệu Spark Tuning/Memory Management (chưa trích nguồn).
- spark.executor.memory mặc định 1g: Spark Configuration 4.0.0.
- ivy download 46 ms: results/metrics/scale_data/runs/orders_5m/r3/run_record.json trường ivy.download_ms.
- Số test 12/14/3/12/29/15 và 44 passed trên Windows: tests/README.md.
- 49 phép đối chiếu, all_match True ở cả 6 lần: results/metrics/pandas_baseline/runs.csv.
- counts_consistent True: results/metrics/{scale_data,scale_workers,join_strategy,skew,pandas_baseline}/summary.csv (format_compare và cache để trống cột này).
- Sự cố 0xc00000fd, 9,7 GiB, ~72%, 4,1 GB, 2,6 GB, 37,7 GB: infra/README.md. Issue docker/desktop-feedback #767: cần xác nhận URL.
- spark.worker.cleanup.*: Spark Standalone Mode 4.0.0.
- "không gặp lại sự cố trong bộ đo chính thức": suy từ 69/69 status ok trong runs.csv; không có ghi chép riêng về việc engine không sập ngoài lúc đo.
-->
