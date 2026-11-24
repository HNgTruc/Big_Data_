# Chương 5. Cài đặt và triển khai

Bảng phiên bản, cấu hình đầy đủ, cấu trúc mã, lệnh chạy, bảng kiểm thử và chi tiết sự cố nằm ở Phụ lục C.

## 5.1 Công nghệ và lý do chọn

Spark đảm nhận lớp xử lý, MinIO lớp lưu trữ, connector S3A (`hadoop-aws` 3.4.1) nối hai lớp, Docker Compose chạy toàn bộ cụm (@fig:kien-truc). Phiên bản và vai trò từng thành phần ở @tbl:cong-nghe (Phụ lục C).

**Lý do chọn Spark.** Đề gợi ý Apache Spark, PySpark, Spark SQL cho quy trình Storage → Processing. Spark xử lý dữ liệu phân tán theo partition, dùng DAG để lập lịch job, stage và task, có DataFrame và Spark SQL với bộ tối ưu Catalyst, có broadcast join và cache (slide chương 5, tr. 8, 31, 42, 51 [@slide-c5]). Nhóm chọn phiên bản 4.0.0 vì image chính thức `apache/spark:4.0.0-python3` kéo được trên máy. Image này chứa sẵn Hadoop 3.4.1, nên `hadoop-aws` phải cùng phiên bản 3.4.1.

**Lý do chọn MinIO.** MinIO cung cấp API tương thích S3 [@minio-docs] chạy cục bộ, mô phỏng lớp lưu trữ đối tượng của Data Lake mà không cần dịch vụ đám mây. Các image `minio/minio` và `quay.io/minio/*` không kéo được trên máy khi triển khai, nên nhóm dùng image MinIO miễn phí của Chainguard với thẻ `latest` [@chainguard-minio] (mục C.8).

**Lý do chọn Docker Compose.** Đề tài cần một cụm Spark nhiều worker nhưng nhóm chỉ có một máy. Với Docker Compose, một tệp cấu hình dựng đủ MinIO, master và 2 worker, cố định image Spark `apache/spark:4.0.0-python3` (MinIO dùng thẻ `latest`, xem mục 8.5 và F.2) và giới hạn số lõi, bộ nhớ của từng worker, nên cụm dựng lại giống nhau giữa các lần chạy. Đổi lại, các worker vẫn dùng chung phần cứng của một máy, nên kết quả không thay thế được phép đo trên cụm thật.

**Lý do chọn Pandas.** Pandas là thư viện xử lý bảng phổ biến trên một máy, cùng hệ sinh thái Python với PySpark. Chạy cùng các luật làm sạch bằng Pandas trong thí nghiệm (g) cho một mốc so sánh để xem ở quy mô dữ liệu này, chi phí xử lý phân tán có đáng hay không (mục 4.6, 6.10).

## 5.2 Cấu hình cụm

Cụm gồm 2 worker, mỗi worker 2 lõi (tổng 4 lõi) và cho phép tối đa 2 GB, mỗi worker chạy một executor với heap mặc định 1 GB. Job ETL mặc định dùng 8 phân vùng shuffle, bật AQE và ngưỡng broadcast tự động 10 MB. Toàn bộ giá trị ở @tbl:cau-hinh-cum (Phụ lục C). Giữ heap 1 GB để lại khoảng trống cho hệ điều hành, MinIO và master trong giới hạn 6 GB của WSL2 (nhận định của nhóm). Đánh đổi là executor dễ tràn dữ liệu ra đĩa hơn khi shuffle hoặc cache (thí nghiệm (f), mục 6.9).

## 5.3 Mã nguồn và cách chạy

Mã nguồn chia thành bộ sinh dữ liệu mô phỏng (`src/data_generation/`), job Spark (`src/etl/`) và bảy thí nghiệm (`src/experiments/`), kèm kiểm thử trong `tests/` và hạ tầng trong `infra/`. Cấu trúc chi tiết ở @tbl:cau-truc-ma (Phụ lục C). Để tái lập, nhóm sinh dữ liệu trên host, dựng cụm bằng `docker compose up -d`, chép dữ liệu thô lên MinIO bằng `mc cp`, rồi chạy job ETL hoặc cả bộ thí nghiệm bằng `python -m src.experiments.run_all --group all`. Lệnh đầy đủ và lý do dùng `docker compose run`, bộ đệm Ivy trên host ở mục C.3, hướng dẫn tái lập ở Phụ lục F.

## 5.4 Kiểm thử

Lần chạy trong container Spark (Python 3.10.12, pyspark 4.0.0) cho kết quả 41 passed trong 64,91 giây (log `results/logs/test_etl.log`). Lần chạy trên host Windows cho 70 passed trong 7,41 giây (log `results/logs/test_host.log`). Các bộ kiểm thử ở @tbl:kiem-thu (Phụ lục C).

Nhóm còn kiểm chứng job bằng đối chiếu số đếm. Với cả năm bộ dữ liệu, số dòng thô khớp manifest, còn số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp hoàn toàn số lỗi đã chèn (`docs/design/etl.md`). Mỗi lần chạy baseline Pandas làm 49 phép đối chiếu với manifest và với metrics của Spark, cả 6 lần đều khớp (`results/metrics/pandas_baseline/runs.csv`, cột `all_match`, `n_mismatch`). Job xuất mẫu đếm lại trực tiếp trên MinIO và so với metrics, log ghi `SAMPLES_OK ... mismatches=0` (`results/logs/export_samples_orders_5m.log`). Trong mọi bảng tổng hợp, số dòng sạch, cách ly và trùng giống nhau giữa các lần chạy của cùng một bộ dữ liệu (cột `counts_consistent` = True trong các `summary.csv` của thí nghiệm ETL).

## 5.5 Sự cố đã gặp và cách xử lý

Engine Docker Desktop sập với mã `0xc00000fd`, toàn bộ container chuyển sang `Exited (255)`. Sau khi nhóm đặt `.wslconfig` với `memory=6GB`, `processors=8`, job chạy thành công và không gặp lại sự cố trong bộ đo chính thức (69 lần chạy đều thành công). Đồ án không khẳng định áp lực bộ nhớ là nguyên nhân, đây chỉ là biện pháp đã có hiệu quả trong thực tế.

Sau 7 lần chạy, `/opt/spark/work` trên mỗi worker chiếm khoảng 4,1 GB và ổ C chỉ còn 2,6 GB. Nhóm rút ngắn chu kỳ dọn của worker và chuyển đĩa ảo Docker sang ổ D. Vì C: và D: cùng một ổ vật lý, việc chuyển ổ chỉ giải quyết dung lượng, không giảm tranh chấp I/O. Chi tiết hai sự cố này, việc tải lại jar và các trở ngại nhỏ khác ở mục C.9.

Hướng dẫn đo của đồ án (`infra/README.md`, `src/experiments/README.md`) yêu cầu đóng ứng dụng nặng và tạm dừng Windows Update trước khi đo, nhưng repo không có ghi nhận các bước này đã được làm lúc đo. Bằng chứng có được là không có container lạ: cột `foreign_containers` trống ở mọi lần chạy (`results/metrics/*/runs.csv`).

<!-- VERIFY
- Lý do chọn Docker Compose và Pandas: bản nháp do điều phối viên đề xuất, người dùng đồng ý (2026-11-09). Giới hạn lõi, bộ nhớ, image cố định: infra/docker-compose.yml, infra/.env.example.
- Python 3.10.12, 41 passed in 64.91s: results/logs/test_etl.log.
- 70 passed in 7.41s: results/logs/test_host.log (chạy lại 2026-11-16 sau khi thêm test căn lề mã nội dòng).
- hadoop-aws 3.4.1: results/logs/export_samples_orders_5m.log dòng 10–16; infra/README.md.
- Image miễn phí: chainguard-minio. quay.io không kéo được: quan sát của đồ án, infra/README.md. Thẻ latest: infra/.env.example.
- Spark chính thức chứa Hadoop 3.4.1 (hadoop-client-api-3.4.1.jar): infra/README.md.
- 49 phép đối chiếu, all_match True ở cả 6 lần: results/metrics/pandas_baseline/runs.csv.
- counts_consistent True: results/metrics/{scale_data,scale_workers,join_strategy,skew,pandas_baseline}/summary.csv (format_compare và cache để trống cột này).
- Sự cố 0xc00000fd, 4,1 GB, 2,6 GB: infra/README.md.
- "không gặp lại sự cố trong bộ đo chính thức": suy từ 69/69 status ok trong runs.csv; không có ghi chép riêng về việc engine không sập ngoài lúc đo.
- foreign_containers trống ở mọi lần chạy: results/metrics/*/runs.csv (verify-round1 mục B).
- Chi tiết đã chuyển: VERIFY ở Phụ lục C.
- Vòng 3: A1 (số dòng thô khớp manifest, lý do cách ly trực tiếp khớp số lỗi: docs/design/etl.md:60, 63); A2 (chỉ image Spark cố định, MinIO thẻ latest: infra/.env.example:4-6); A3 (image kéo được là lý do, Hadoop 3.4.1 là hệ quả: infra/README.md:8).
-->
