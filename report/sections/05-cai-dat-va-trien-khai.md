# Chương 5. Cài đặt và triển khai

Chương này liệt kê công nghệ và phiên bản đã dùng, tóm tắt cấu hình cụm, mã nguồn và cách chạy, nêu kết quả kiểm thử và các sự cố đã gặp trong quá trình triển khai. Bảng cấu hình đầy đủ, cấu trúc mã, lệnh chạy và bảng kiểm thử nằm ở Phụ lục C.

## 5.1 Công nghệ và phiên bản

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

**Lý do chọn Spark.** Đề gợi ý Apache Spark, PySpark, Spark SQL cho quy trình Storage → Processing. Spark là engine xử lý dữ liệu phân tán theo partition, dùng DAG để lập lịch job, stage và task, có DataFrame và Spark SQL với bộ tối ưu Catalyst, hỗ trợ broadcast join và cache (slide chương 5, tr. 8, 31, 42, 51 [@slide-c5]). Spark vẫn có I/O lưu trữ, shuffle và tràn đĩa, nên không phải mọi dữ liệu đều nằm trong RAM (slide chương 5, tr. 6 [@slide-c5]). Phiên bản 4.0.0 được chọn vì image chính thức kéo được trên máy và chứa sẵn Hadoop 3.4.1, nên `hadoop-aws` phải cùng phiên bản 3.4.1.

**Lý do chọn MinIO và nguồn image Chainguard.** MinIO cung cấp API tương thích S3 [@minio-docs] chạy cục bộ, mô phỏng lớp lưu trữ đối tượng của Data Lake mà không cần dịch vụ đám mây. Khi triển khai (2026-11-06), các image `minio/minio`, `minio/mc` trên Docker Hub và `quay.io/minio/*` đều không kéo được trên máy (quan sát của đồ án, `infra/README.md`). Với Docker Hub, một bài viết ghi nhận image MinIO đã bị xoá khỏi đó từ giữa tháng 9/2026 [@bex-minio]; bài viết khuyên chuyển sang quay.io, nhưng trên máy này quay.io cũng không kéo được. Chainguard cung cấp image MinIO miễn phí [@chainguard-minio]; image này kéo được nên được dùng thay thế. Image client của Chainguard không có shell, nên mọi lệnh `mc` được gọi trực tiếp qua `docker compose run`.

## 5.2 Cấu hình cụm

Cụm gồm 2 worker, mỗi worker 2 lõi (tổng 4 lõi) và cho phép tối đa 2 GB; mỗi worker chạy một executor với heap mặc định 1 GB. Job ETL mặc định dùng 8 phân vùng shuffle, bật AQE và ngưỡng broadcast tự động 10 MB. Toàn bộ giá trị ở @tbl:cau-hinh-cum (Phụ lục C).

Trường `resources` trong metrics ghi `spark.executor.memory` = `null`, nghĩa là không đặt và Spark dùng mặc định 1g [@spark-config]. Ảnh chụp tab Executors (@fig:ss-executors, Phụ lục E) cho thấy mỗi executor có Storage Memory 434,4 MiB: đây là vùng nhớ hợp nhất (thực thi và lưu trữ) tách ra từ heap 1 GB, khớp công thức (1024 − 300) × 0,6 = 434,4 MiB ở tài liệu Spark [@spark-tuning]. Với 2 GB cho phép trên mỗi worker, việc giữ heap 1 GB để lại khoảng trống cho hệ điều hành, MinIO và master trong giới hạn 6 GB của WSL2 (nhận định của người viết). Đánh đổi là executor dễ tràn dữ liệu ra đĩa hơn khi shuffle hoặc cache (thấy rõ ở thí nghiệm (f), mục 6.9).

## 5.3 Mã nguồn và cách chạy

Mã nguồn chia thành bộ sinh dữ liệu mô phỏng (`src/data_generation/`), job Spark (`src/etl/`) và bảy thí nghiệm (`src/experiments/`), kèm kiểm thử trong `tests/` và hạ tầng trong `infra/`; cấu trúc chi tiết ở @tbl:cau-truc-ma (Phụ lục C). Để tái lập: sinh dữ liệu trên host, dựng cụm bằng `docker compose up -d`, chép dữ liệu thô lên MinIO bằng `mc cp`, rồi chạy job ETL hoặc cả bộ thí nghiệm bằng `python -m src.experiments.run_all --group all`; lệnh đầy đủ ở mục C.3. Job được nộp bằng `docker compose run` chứ không phải `docker compose exec`, nên mỗi lần chạy có một container driver mới tách khỏi master. Bộ đệm Ivy đặt trên host để jar chỉ tải một lần; lý do của hai lựa chọn này cũng ở mục C.3.

## 5.4 Kiểm thử

Các bộ kiểm thử được liệt kê ở @tbl:kiem-thu (Phụ lục C). Lần chạy trong container Spark (Python 3.10.12, pyspark 4.0.0) cho kết quả **41 passed** trong 64,91 giây (12 + 14 + 3 + 12 test; log `results/logs/test_etl.log`). Lần chạy trên host Windows cho **69 passed** trong 4,42 giây (`test_build_docx.py` 13, `test_experiments.py` 29, `test_experiments_pandas.py` 15, `test_data_generation.py` 12 test; log `results/logs/test_host.log`). `test_etl.py` không chạy được trực tiếp trên Windows (Python worker của Spark bị lỗi và ghi Parquet cần `winutils.exe`), nên được chạy trong container.

Ngoài kiểm thử đơn vị, tính đúng của job được kiểm chứng bằng đối chiếu số đếm:

- Với cả năm bộ dữ liệu, số dòng thô, số dòng trùng đã bỏ và từng lý do cách ly khớp hoàn toàn với số lỗi đã chèn trong manifest (`docs/design/etl.md`).
- Mỗi lần chạy baseline Pandas thực hiện 49 phép đối chiếu với manifest và với metrics của Spark; cả 6 lần đều khớp, không lệch phép nào (`results/metrics/pandas_baseline/runs.csv`, cột `all_match`, `n_mismatch`).
- Job xuất mẫu đếm lại trực tiếp trên MinIO và so với metrics: `SAMPLES_OK ... mismatches=0` (`results/logs/export_samples_orders_5m.log`).
- Trong mọi bảng tổng hợp của bộ thí nghiệm, số dòng sạch, cách ly và trùng giống nhau giữa các lần chạy của cùng một bộ dữ liệu (cột `counts_consistent` = True trong các `summary.csv` của thí nghiệm ETL).

## 5.5 Sự cố đã gặp và cách xử lý

**Engine Docker Desktop sập (mã `0xc00000fd`).** Khi chạy job, toàn bộ container chuyển sang `Exited (255)` và engine WSL2 khởi động lại; log Docker Desktop ghi `wsl-bootstrap ... exit status 0xc00000fd`. Có báo cáo lỗi tương tự với cùng mã lỗi và cùng nhân WSL [@docker-767], nhưng nguyên nhân chưa được xác định ở đó. Lúc sập, giới hạn bộ nhớ của Docker là 9,7 GiB trên máy đang dùng khoảng 72% RAM. Sau khi đặt `.wslconfig` với `memory=6GB`, `processors=8`, job chạy thành công và không gặp lại sự cố trong bộ đo chính thức (69 lần chạy đều thành công). Đồ án không khẳng định áp lực bộ nhớ là nguyên nhân; đây chỉ là biện pháp đã có hiệu quả trong thực tế.

**Đầy đĩa do thư mục làm việc của worker.** Sau 7 lần chạy, `/opt/spark/work` trên mỗi worker chiếm khoảng 4,1 GB, vì mỗi ứng dụng chép lại các jar của `--packages` vào thư mục riêng. Spark 4.0.0 mặc định đã bật dọn dẹp thư mục làm việc (`spark.worker.cleanup.enabled` = true), nhưng chỉ quét 30 phút một lần (`interval` = 1800 giây) và chỉ xoá thư mục của ứng dụng đã kết thúc quá 7 ngày (`appDataTtl` = 604800 giây) [@spark-standalone]. Ổ C chỉ còn 2,6 GB vì tệp đĩa ảo của Docker (37,7 GB) nằm trên C. Cách xử lý: rút ngắn chu kỳ dọn của worker, `interval` từ 1800 xuống 600 giây và `appDataTtl` từ 604800 xuống 3600 giây (`infra/docker-compose.yml`), đồng thời chuyển đĩa ảo Docker sang ổ D. Hệ quả: log executor chỉ còn trên worker khoảng 1 giờ; log driver vẫn lưu đầy đủ trong `results/logs/`. Vì C: và D: cùng một ổ vật lý, việc chuyển ổ chỉ giải quyết dung lượng, không giảm tranh chấp I/O.

**Tải lại jar mỗi lần chạy.** Lúc đầu bộ đệm Ivy đặt ở `/tmp/.ivy` trong container driver, mất đi khi container bị xoá, nên mỗi lần chạy phải tải lại `hadoop-aws` và AWS SDK. Chuyển bộ đệm vào `data/ivy_cache/` trên host (mục C.3) loại bỏ chi phí này và loại bỏ sự phụ thuộc vào Internet trong lúc đo.

**Các trở ngại nhỏ khác.** Cổng 8080 trên máy đã bị chiếm nên Master UI được chuyển sang 8090. Lệnh `mc cp --recursive` chép cả thư mục nguồn vào đích, nên đích phải là `raw/` chứ không phải `raw/<bộ>`, nếu không dữ liệu bị lồng thêm một cấp.

**Điều kiện máy trong lúc đo.** Hướng dẫn đo của đồ án (`infra/README.md`, `src/experiments/README.md`) yêu cầu đóng ứng dụng nặng và tạm dừng Windows Update trước khi đo, nhưng repo không có ghi nhận các bước này đã được làm lúc đo. Bằng chứng có được là không có container lạ: cột `foreign_containers` trống ở mọi lần chạy (`results/metrics/*/runs.csv`).

Nguồn mục 5.5: infra/README.md (mục "Sự cố engine Docker Desktop sập", "Dung lượng đĩa", "Đưa dữ liệu thô lên MinIO"), src/experiments/README.md (mục "Bộ đệm Ivy"), infra/docker-compose.yml.

<!-- VERIFY
- Java 17.0.15, Spark 4.0.0, nhân 6.18.54.1-microsoft-standard-WSL2: results/logs/export_samples_orders_5m.log dòng 29–31.
- Python 3.10.12, numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1, 41 passed in 64.91s: results/logs/test_etl.log.
- 69 passed in 4.42s: results/logs/test_host.log (chạy lại 2026-11-08 sau khi thêm test phụ lục); phân bổ 13/29/15/12 do điều phối viên đếm bằng pytest --co (log chỉ in tổng).
- hadoop-aws 3.4.1, awssdk bundle 2.24.6: results/logs/export_samples_orders_5m.log dòng 10–16; infra/README.md.
- MinIO RELEASE.2026-10-23T20-06-51Z, Docker engine 29.9.2: results/logs/environment.txt.
- Python 3.12.10, numpy 2.5.4, pandas 3.1.1, pyarrow 26.0.1 của bộ sinh: data/raw/orders_5m/manifest.json. Baseline Pandas: results/metrics/pandas_baseline/runs/orders_1m/r1/pandas_baseline.json trường versions.
- matplotlib 3.11.2: chỉ có ở tests/README.md (.venv-exp).
- Docker Hub bị xoá giữa 9/2026, bài viết khuyên quay.io: bex-minio (verify-round1 A7). Image miễn phí: chainguard-minio. quay.io không kéo được: quan sát của đồ án, infra/README.md.
- Spark chính thức chứa Hadoop 3.4.1 (hadoop-client-api-3.4.1.jar): infra/README.md.
- Storage Memory 434,4 MiB: ảnh 13 và results/logs/screenshots/README.md; (1024 − 300) × 0,6 khớp công thức ở Tuning - Spark 4.0.0 (verify-round1 mục C).
- spark.executor.memory mặc định 1g: Spark Configuration 4.0.0.
- 49 phép đối chiếu, all_match True ở cả 6 lần: results/metrics/pandas_baseline/runs.csv.
- counts_consistent True: results/metrics/{scale_data,scale_workers,join_strategy,skew,pandas_baseline}/summary.csv (format_compare và cache để trống cột này).
- Sự cố 0xc00000fd, 9,7 GiB, ~72%, 4,1 GB, 2,6 GB, 37,7 GB: infra/README.md. Cùng nhân WSL trong issue #767: theo infra/README.md; verify-round1 A6 xác nhận issue tồn tại và nguyên nhân chưa xác định.
- spark.worker.cleanup.* mặc định true/1800/604800: Spark Standalone Mode 4.0.0 (verify-round1 A2); giá trị của đồ án 600/3600: infra/docker-compose.yml.
- "không gặp lại sự cố trong bộ đo chính thức": suy từ 69/69 status ok trong runs.csv; không có ghi chép riêng về việc engine không sập ngoài lúc đo.
- /tmp/.ivy: lệnh ở infra/README.md và tuỳ chọn --no-ivy-cache ở src/experiments/README.md.
- foreign_containers trống ở mọi lần chạy: results/metrics/*/runs.csv (verify-round1 mục B).
-->
