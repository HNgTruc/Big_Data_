# Phụ lục C. Chi tiết cài đặt

Chi tiết của chương 4 và chương 5: cấu hình cụm, cấu trúc mã nguồn, lệnh chạy, kiểm thử, thành phần hệ thống, luật làm sạch, phiên bản công nghệ, nguồn image MinIO và sự cố.

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
| Dọn thư mục làm việc worker | `spark.worker.cleanup.enabled=true`, quét 10 phút/lần (mặc định 30 phút), xoá ứng dụng kết thúc quá 1 giờ (mặc định 7 ngày) | Xem mục C.9 |

Nguồn: infra/docker-compose.yml, infra/.env.example, src/etl/session.py, results/metrics/scale_data/runs/orders_5m/r3/run_record.json (trường `metrics.conf`, `metrics.resources`, `default_parallelism`), results/logs/screenshots/01_spark_master_workers.png

Trường `resources` trong metrics ghi `spark.executor.memory` = `null`, nghĩa là không đặt và Spark dùng mặc định 1g [@spark-config]. Tab Executors (@fig:ss-executors, Phụ lục E) ghi mỗi executor có Storage Memory 434,4 MiB, là vùng nhớ hợp nhất (thực thi và lưu trữ) tách ra từ heap 1 GB, khớp công thức (1024 − 300) × 0,6 = 434,4 MiB ở tài liệu Spark [@spark-tuning].

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

Quy ước của mã:

- Lược đồ khai báo tường minh thay vì `inferSchema`.
- Tham số chạy (bộ dữ liệu, chiến lược join, số phân vùng) đi qua dòng lệnh.
- Thông tin đăng nhập MinIO lấy từ biến môi trường (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), không viết cứng.

## C.3 Cách chạy

Các bước tái lập toàn bộ (PowerShell, chi tiết ở `infra/README.md` và `src/experiments/README.md`):

1. Sinh dữ liệu trên host: `python -m src.data_generation.generate --orders 5000000` (thêm `--skew` cho bộ lệch, thêm `--overwrite` nếu thư mục đầu ra đã có `manifest.json`, như trên bản clone).
2. Dựng cụm trong `infra/`: `docker compose up -d`, kiểm tra Master UI tại http://localhost:8090 thấy 2 worker ALIVE.
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

5. Chạy cả bộ thí nghiệm từ thư mục gốc: `python -m src.experiments.run_all --group all` (thêm `--overwrite` nếu `results/metrics/` đã có bản ghi), rồi `python -m src.experiments.analyze_all` để dựng lại CSV và hình.

**Dùng `docker compose run` thay vì `docker compose exec`.** Mỗi lần chạy tạo một container driver mới có tên cố định (`etl-driver`, `bench-driver`) và đặt `spark.driver.host` bằng tên đó để executor gọi ngược về driver. Lúc đầu job chạy bằng `exec` trong container master, và khi engine Docker sập (mục C.9), `exec` báo lỗi `500` hoặc `No such exec instance`. Dùng `run` thì driver tách khỏi master, `--rm` xoá container sau khi chạy, và bộ điều khiển thí nghiệm kiểm tra được không còn container driver cũ trước mỗi lần chạy.

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
| `test_build_docx.py` | Script dựng Word của báo cáo trên fixture Markdown nhỏ | 14 | Windows |

Nguồn: tests/README.md; results/logs/test_etl.log; results/logs/test_host.log

Trong container, 41 test gồm 12 + 14 + 3 + 12. Trên host, 69 test gồm `test_build_docx.py` 13, `test_experiments.py` 29, `test_experiments_pandas.py` 15, `test_data_generation.py` 12. `test_etl.py` không chạy được trực tiếp trên Windows (Python worker của Spark bị lỗi và ghi Parquet cần `winutils.exe`), nên tệp này chạy trong container.

## C.5 Thành phần hệ thống

Bảng: Thành phần hệ thống và vai trò {#tbl:thanh-phan}

| Thành phần | Vai trò | Giao tiếp |
|---|---|---|
| `minio` | Lưu trữ đối tượng, API S3 và giao diện console | Cổng 9000 (S3), 9001 (console) |
| `minio-init` | Tạo bucket; dùng lại để chép dữ liệu thô bằng `mc` | S3 tới `minio:9000` |
| `spark-master` | Quản lý cụm, cấp executor cho ứng dụng, giao diện Master UI | 7077 (cụm), 8090 trên host (UI) |
| `spark-worker-1`, `spark-worker-2` | Chạy executor | Đăng ký với master |
| Container driver | Chạy chương trình driver của job PySpark: nộp ứng dụng tới master, gửi task cho executor | `spark.driver.host` = tên container |

Nguồn: infra/docker-compose.yml, infra/README.md

## C.6 Luật làm sạch

Bảng: Luật làm sạch theo bảng {#tbl:luat-lam-sach}

| Bảng | Bỏ trùng theo | Đưa vào quarantine (`reject_reason`) | Sửa tại chỗ |
|---|---|---|---|
| `orders` | `order_id` | `null_customer_id`, `invalid_order_date`, `orphan_customer_id` | Ngày sai định dạng thành `yyyy-MM-dd` |
| `order_items` | (`order_id`, `line_no`) | `null_unit_price`, `non_positive_quantity`, `non_positive_price`, `orphan_product_id`, `no_clean_order` | Không |
| `customers` | `customer_id` | Không có | `region` thiếu thành `unknown`; chuẩn hoá ngày |
| `web_events` | `event_id` | `null_customer_id`, `invalid_event_time` | Thời gian sai định dạng thành timestamp |
| `products` | Không | Không | Không |

Nguồn: docs/design/etl.md

Khi một dòng vi phạm nhiều luật, job áp dụng luật đứng trước trong cột quarantine (luật đầu tiên thắng), nên mỗi dòng chỉ có một lý do. Job nhận diện ngày bằng biểu thức chính quy cho bốn định dạng (ISO và ba định dạng lỗi), thời gian cho ba định dạng, chuỗi không khớp mẫu nào trả về `NULL`. Ở chế độ ANSI, ngày sai sẽ gây lỗi thay vì trả `NULL` [@spark-ansi], nên job đặt `spark.sql.ansi.enabled=false` và `spark.sql.legacy.timeParserPolicy=CORRECTED`.

## C.7 Công nghệ và phiên bản

Bảng: Công nghệ, phiên bản và vai trò {#tbl:cong-nghe}

| Công nghệ | Phiên bản | Vai trò trong kiến trúc |
|---|---|---|
| Apache Spark (PySpark) | 4.0.0, image `apache/spark:4.0.0-python3` | Xử lý phân tán: làm sạch, join, tổng hợp |
| Java (trong image Spark) | 17.0.15 | Môi trường chạy JVM của Spark |
| Python (trong image Spark) | 3.10.12 | Chạy job PySpark và kiểm thử trong container |
| pandas / pyarrow / numpy trong container | 2.3.3 / 25.0.1 / 2.2.6 | Chạy kiểm thử trong container |
| Hadoop client / `hadoop-aws` | 3.4.1 / 3.4.1 | Connector S3A để Spark đọc ghi MinIO |
| AWS SDK bundle | 2.24.6 | Phụ thuộc của `hadoop-aws` |
| MinIO server và client `mc` | Image `cgr.dev/chainguard/minio:latest`, `cgr.dev/chainguard/minio-client:latest`; server RELEASE.2026-10-23T20-06-51Z | Lưu trữ đối tượng S3 |
| Docker Desktop + WSL2 | Docker engine 29.9.2; nhân WSL 6.18.54.1 | Chạy toàn bộ cụm trong container |
| Python trên host | 3.12.10 | Sinh dữ liệu, điều khiển thí nghiệm, baseline Pandas, vẽ hình |
| pandas / pyarrow / numpy trên host | 3.1.1 / 26.0.1 / 2.5.4 | Môi trường sinh dữ liệu (ghi trong manifest); baseline Pandas ghi cùng phiên bản pandas và pyarrow |
| matplotlib | 3.11.2 (theo `tests/README.md`, không ghi trong `results/`) | Vẽ hình kết quả |

Nguồn: infra/.env.example, infra/README.md, results/logs/environment.txt (MinIO, Docker engine), results/logs/export_samples_orders_5m.log (Spark 4.0.0, Java 17.0.15, nhân WSL), results/logs/test_etl.log (Python 3.10.12 và thư viện trong container), data/raw/orders_5m/manifest.json (Python, numpy, pandas, pyarrow của bộ sinh), results/metrics/pandas_baseline/runs/orders_1m/r1/pandas_baseline.json (baseline Pandas), tests/README.md (matplotlib)

Spark vẫn có I/O lưu trữ, shuffle và tràn đĩa, nên không phải mọi dữ liệu đều nằm trong RAM (slide chương 5, tr. 6 [@slide-c5]).

## C.8 Nguồn image MinIO

Khi triển khai (2026-11-06), các image `minio/minio`, `minio/mc` trên Docker Hub và `quay.io/minio/*` đều không kéo được trên máy (quan sát của đồ án, `infra/README.md`). Với Docker Hub, một bài viết ghi nhận image MinIO đã bị xoá khỏi đó từ giữa tháng 9/2026 [@bex-minio]. Bài viết khuyên chuyển sang quay.io, nhưng trên máy này quay.io cũng không kéo được. Chainguard cung cấp image MinIO miễn phí [@chainguard-minio] và image này kéo được. Image client của Chainguard không có shell, nên nhóm gọi mọi lệnh `mc` trực tiếp qua `docker compose run`.

## C.9 Chi tiết sự cố

**Engine Docker Desktop sập (mã `0xc00000fd`).** Khi chạy job, toàn bộ container chuyển sang `Exited (255)` và engine WSL2 khởi động lại, log Docker Desktop ghi `wsl-bootstrap ... exit status 0xc00000fd`. Có báo cáo lỗi tương tự với cùng mã lỗi và cùng nhân WSL [@docker-767], nhưng báo cáo đó chưa xác định nguyên nhân. Lúc sập, giới hạn bộ nhớ của Docker là 9,7 GiB trên máy đang dùng khoảng 72% RAM.

**Đầy đĩa do thư mục làm việc của worker.** Mỗi ứng dụng chép lại các jar của `--packages` vào thư mục riêng trong `/opt/spark/work`. Spark 4.0.0 mặc định đã bật dọn dẹp thư mục làm việc (`spark.worker.cleanup.enabled` = true), nhưng chỉ quét 30 phút một lần (`interval` = 1800 giây) và chỉ xoá thư mục của ứng dụng đã kết thúc quá 7 ngày (`appDataTtl` = 604800 giây) [@spark-standalone]. Ổ C còn ít vì tệp đĩa ảo của Docker (37,7 GB) nằm trên C. Nhóm đổi `interval` từ 1800 xuống 600 giây và `appDataTtl` từ 604800 xuống 3600 giây (`infra/docker-compose.yml`). Hệ quả là log executor chỉ còn trên worker khoảng 1 giờ, log driver vẫn lưu đầy đủ trong `results/logs/`.

**Tải lại jar mỗi lần chạy.** Lúc đầu bộ đệm Ivy đặt ở `/tmp/.ivy` trong container driver, mất đi khi container bị xoá, nên mỗi lần chạy phải tải lại `hadoop-aws` và AWS SDK. Chuyển bộ đệm vào `data/ivy_cache/` trên host (mục C.3) giúp jar chỉ tải một lần, lần chạy đầu tiên của cả bộ vẫn tải (`src/experiments/README.md`).

**Các trở ngại nhỏ khác.** Cổng 8080 trên máy đã bị chiếm nên nhóm chuyển Master UI sang 8090. Lệnh `mc cp --recursive` chép cả thư mục nguồn vào đích, nên đích phải là `raw/` chứ không phải `raw/<bộ>`, nếu không dữ liệu bị lồng thêm một cấp.

Nguồn mục C.9: infra/README.md (mục "Sự cố engine Docker Desktop sập", "Dung lượng đĩa", "Đưa dữ liệu thô lên MinIO"), src/experiments/README.md (mục "Bộ đệm Ivy"), infra/docker-compose.yml.

<!-- VERIFY
- SPARK_DAEMON_MEMORY 512m, cleanup interval 600, appDataTtl 3600: infra/docker-compose.yml. Mặc định 1800 giây và 604800 giây: Spark Standalone Mode 4.0.0 (verify-round1 A2).
- Master UI 4,0 GiB, 1024,0 MiB mỗi executor: ảnh results/logs/screenshots/01_spark_master_workers.png.
- ivy download 46 ms: results/metrics/scale_data/runs/orders_5m/r3/run_record.json trường ivy.download_ms.
- Số test 12/14/3/12/29/15/14: tests/README.md, results/logs/test_etl.log (41 passed), results/logs/test_host.log (70 passed).
- test_build_docx.py 14 test: log test_host.log chạy lại 2026-11-16 sau khi thêm test căn lề mã nội dòng (70 = 14 + 29 + 15 + 12); phân bổ do điều phối viên đếm bằng pytest --co (log chỉ in tổng).
- Lệnh chạy: infra/README.md, src/experiments/README.md. `--overwrite`: src/data_generation/generate.py:128-130, src/experiments/common/runner.py:192-196, theo mã, chưa chạy thử (verify-round2 E1, E2).
- C.1 Storage Memory 434,4 MiB: ảnh 13 và results/logs/screenshots/README.md; (1024 − 300) × 0,6 khớp công thức ở Tuning - Spark 4.0.0 (verify-round1 mục C). spark.executor.memory mặc định 1g: Spark Configuration 4.0.0.
- C.5 Cổng 9000/9001/7077/8090: infra/docker-compose.yml, infra/README.md.
- C.6 Luật làm sạch, luật đầu tiên thắng, bốn định dạng ngày / ba định dạng thời gian: docs/design/etl.md. Spark 4 bật ANSI mặc định: tài liệu Spark ANSI compliance 4.0.0.
- C.7 Java 17.0.15, Spark 4.0.0, nhân 6.18.54.1-microsoft-standard-WSL2: results/logs/export_samples_orders_5m.log dòng 29–31. numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1: results/logs/test_etl.log. awssdk bundle 2.24.6: results/logs/export_samples_orders_5m.log dòng 10–16; infra/README.md. MinIO RELEASE.2026-10-23T20-06-51Z, Docker engine 29.9.2: results/logs/environment.txt. Python 3.12.10, numpy 2.5.4, pandas 3.1.1, pyarrow 26.0.1 của bộ sinh: data/raw/orders_5m/manifest.json. Baseline Pandas: results/metrics/pandas_baseline/runs/orders_1m/r1/pandas_baseline.json trường versions. matplotlib 3.11.2: chỉ có ở tests/README.md (.venv-exp).
- C.8 Docker Hub bị xoá giữa 9/2026, bài viết khuyên quay.io: bex-minio (verify-round1 A7). Image miễn phí: chainguard-minio.
- C.9 Sự cố 0xc00000fd, 9,7 GiB, ~72%, 37,7 GB: infra/README.md. Cùng nhân WSL trong issue #767: theo infra/README.md; verify-round1 A6 xác nhận issue tồn tại và nguyên nhân chưa xác định. spark.worker.cleanup.* mặc định true/1800/604800: Spark Standalone Mode 4.0.0 (verify-round1 A2); giá trị của đồ án 600/3600: infra/docker-compose.yml. /tmp/.ivy: lệnh ở infra/README.md và tuỳ chọn --no-ivy-cache ở src/experiments/README.md. Jar chỉ tải một lần, lần đầu của cả bộ vẫn tải: src/experiments/README.md:49 (vòng 3 A8, bỏ ý "Internet" không có nguồn).
-->
