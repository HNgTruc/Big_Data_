# Chương 4. Thiết kế hệ thống

Bảng thành phần và bảng luật làm sạch nằm ở Phụ lục C. Chỉ số đo, kiểm soát nhiễu và tham số thí nghiệm nằm ở Phụ lục B.

## 4.1 Kiến trúc tổng thể

Hệ thống gồm hai lớp chạy trong Docker Compose trên cùng một máy (thành phần và cổng ở @tbl:thanh-phan, Phụ lục C).

Lớp lưu trữ là MinIO, hệ lưu trữ đối tượng tương thích S3 [@minio-docs], giữ dữ liệu thô, dữ liệu sạch và dữ liệu cách ly trong bucket `bigdata`. Client truy cập object storage qua API theo bucket và object key thay vì đường dẫn tệp (slide chương 4, tr. 37 [@slide-c4]). Kiểu cụm cổ điển như HDFS/Hadoop đặt tính toán và lưu trữ cùng trên worker, còn mô hình đám mây có thể tách tính toán khỏi object storage (slide chương 2, tr. 28 [@slide-c2]). Trong đồ án, sự tách này chỉ ở mức dịch vụ vì MinIO và Spark chạy trên cùng một máy.

Lớp xử lý là cụm Apache Spark standalone gồm 1 master và 2 worker, mỗi worker cấp 2 lõi và tối đa 2 GB RAM. `spark-submit` nộp job PySpark từ một container driver riêng, job đọc ghi MinIO qua connector S3A của Hadoop (`hadoop-aws`) [@hadoop-s3a].

![Kiến trúc hệ thống](report/figures/kien-truc.png){#fig:kien-truc}

Nguồn: vẽ bằng script report/build/draw_architecture.py, theo infra/docker-compose.yml và src/etl/pipeline.py

Theo @fig:kien-truc, bộ sinh dữ liệu (`src/data_generation`, seed 42) chạy trên máy host và ghi `data/raw/<bộ>/` (CSV, Parquet, JSON lines, `manifest.json`). Container `minio-init` chép dữ liệu này lên vùng `raw/` của MinIO (`s3a://bigdata/raw/<bộ>/`, giao thức S3, cổng 9000) bằng lệnh `mc cp`. Driver chạy trong một container riêng (`etl-driver` hoặc `bench-driver`) do `docker compose run` tạo, gọi `spark-submit src/etl/etl_job.py` và nộp ứng dụng tới master qua `spark://spark-master:7077`. Master cấp executor trên các worker `spark-worker-1` và `spark-worker-2`, còn driver gửi task cho executor [@spark-cluster]. Mỗi worker chạy một executor (2 lõi, heap 1 GB). Executor đọc `raw/`, làm sạch, join, tổng hợp, rồi ghi `curated/<nhãn>/` và `quarantine/<nhãn>/` dạng Parquet qua S3A. Driver ghi metrics JSON về `results/` trên host qua thư mục gắn bind mount, còn bộ điều khiển trên host ghi lại stdout và stderr của driver làm log.

## 4.2 Tổ chức vùng lưu trữ trên MinIO

Tiền tố đường dẫn chia bucket `bigdata` thành các vùng. Data Lake có thể lưu cả dữ liệu thô và dữ liệu đã xử lý (slide chương 1, tr. 31 [@slide-c1]), và slide chương 4 minh hoạ cách chia vùng raw, clean, curated (tr. 47 [@slide-c4]). Đồ án giữ nguyên dữ liệu thô ở `raw/`, đặt dữ liệu đã xử lý ở `curated/`, còn vùng `quarantine/` là quyết định riêng của đồ án.

Bảng: Các vùng lưu trữ trong bucket bigdata {#tbl:vung-luu-tru}

| Tiền tố | Nội dung | Định dạng | Ghi bởi |
|---|---|---|---|
| `raw/<bộ>/` | Năm bảng thô và `manifest.json` của một bộ dữ liệu | CSV, Parquet, JSON lines | `mc cp` (một lần) |
| `curated/<nhãn>/` | Năm bảng sạch và ba bảng tổng hợp `agg_*` | Parquet | Job ETL |
| `quarantine/<nhãn>/` | Bản ghi lỗi của `orders`, `order_items`, `web_events`, có cột `reject_reason` | Parquet | Job ETL |
| `smoke/` | Dữ liệu của lần kiểm tra kết nối Spark ↔ MinIO | Parquet | `smoke_s3a.py` |

Nguồn: docs/design/etl.md, src/etl/pipeline.py, results/logs/screenshots/README.md

`<nhãn>` mặc định là tên bộ dữ liệu, các thí nghiệm dùng nhãn riêng dạng `<thí nghiệm>_<cấu hình>` để không ghi đè đầu ra chuẩn. Job không bao giờ ghi đè vùng `raw/`, nên mọi lần chạy đều xuất phát từ cùng một đầu vào.

## 4.3 Luồng xử lý ETL

Job `src/etl/etl_job.py` chia thành năm giai đoạn chạy tuần tự. Mỗi giai đoạn ghi kết quả ra Parquet rồi đọc lại làm đầu vào cho giai đoạn sau, nhờ đó job đo được thời gian từng giai đoạn độc lập.

1. dimensions: làm sạch `customers` (bỏ trùng theo `customer_id`, `region` thiếu thành `unknown`, chuẩn hoá ngày đăng ký), chép `products` sang `curated/`.
2. orders: bỏ trùng theo `order_id`, chuẩn hoá `order_date`, join với `customers` sạch để phát hiện `customer_id` mồ côi, tách bản ghi lỗi sang `quarantine/orders`.
3. order_items: bỏ trùng theo khoá (`order_id`, `line_no`), kiểm tra `unit_price` thiếu, `quantity` và `unit_price` không dương, join với `products` để phát hiện `product_id` mồ côi, join với `orders` sạch để loại dòng hàng thuộc đơn không còn hợp lệ.
4. web_events: bỏ trùng theo `event_id`, chuẩn hoá `event_time`, tách sự kiện thiếu `customer_id`.
5. aggregates: tính `agg_daily_revenue` (số đơn và doanh thu theo ngày), `agg_revenue_by_region_category` (doanh thu và số lượng theo khu vực × danh mục, join đủ bốn bảng) và `agg_events_daily` (số sự kiện theo ngày × loại). Doanh thu chỉ tính đơn có trạng thái `paid`, `shipped`, `delivered`, doanh thu một dòng = `quantity × unit_price`.

Sau năm giai đoạn, job đếm lại số dòng thô, sạch, cách ly theo lý do và số dòng trùng đã bỏ (số trùng = thô − sạch − cách ly). Bước thống kê này nằm ngoài `processing_seconds_total`, job đo riêng ở `stats_seconds`.

## 4.4 Luật làm sạch

Mỗi bảng có khoá bỏ trùng riêng, riêng `order_items` dùng (`order_id`, `line_no`). Job đưa bản ghi lỗi vào quarantine kèm `reject_reason`, mỗi dòng một lý do vì luật đứng trước thắng. Job sửa tại chỗ ngày sai định dạng và `region` thiếu, giữ nguyên `products`. Spark 4 bật ANSI mặc định nên job đặt `spark.sql.ansi.enabled=false` để ngày sai trả `NULL` thay vì gây lỗi [@spark-ansi]. Bảng luật đầy đủ ở @tbl:luat-lam-sach (mục C.6, Phụ lục C).

## 4.5 Lý do thiết kế

**Bỏ trùng `order_items` theo khoá (`order_id`, `line_no`).** Phiên bản đầu của lược đồ chưa có `line_no`, nên job bỏ trùng theo toàn bộ giá trị dòng và xoá nhầm những dòng hàng hợp lệ tình cờ giống hệt nhau trong cùng một đơn. Ở bộ lệch khoá, job bỏ 255.378 dòng trong khi chỉ chèn 200.008 dòng trùng, tức xoá nhầm 55.370 dòng hợp lệ, còn ở bộ cân bằng mức xoá nhầm chỉ khoảng 100 dòng. Sau khi thêm `line_no`, `orders_5m_skew` bỏ đúng 200.008 dòng trùng và mọi lý do cách ly khớp số lỗi đã chèn (`docs/design/etl.md`, metrics của lược đồ cũ trong commit `993d30b`). Hạn chế còn lại: nếu hai dòng cùng khoá mà khác nội dung, một dòng bị bỏ mà không vào quarantine. Với dữ liệu mô phỏng, điều này không xảy ra vì dòng trùng luôn là bản sao đầy đủ.

**Chuẩn hoá ngày thay vì cách ly.** Ngày sai định dạng vẫn chứa đủ ngày, tháng, năm. Cách ly những dòng này sẽ làm mất khoảng 2% đơn hàng hợp lệ và làm sai doanh thu, nên job nhận diện định dạng rồi chuyển về ISO. Chỉ chuỗi không nhận diện được mới thành `NULL` và bị cách ly với lý do `invalid_order_date` (hoặc `invalid_event_time`). Với dữ liệu hiện tại, không dòng nào bị cách ly vì lý do này (mục 6.3).

**`no_clean_order` là hệ quả dây chuyền.** Một dòng hàng không có lỗi nào vẫn có thể thuộc về một đơn đã bị cách ly. Giữ dòng đó trong `curated/` sẽ làm bảng sạch vi phạm toàn vẹn tham chiếu và cộng doanh thu của đơn không hợp lệ. Job join dòng hàng với bảng đơn sạch và cách ly với lý do riêng, nhờ đó số lỗi trực tiếp vẫn phải khớp đúng số lỗi đã chèn, còn `no_clean_order` phụ thuộc số đơn bị cách ly.

**Cách ly thay vì xoá.** `quarantine/` giữ bản ghi lỗi kèm lý do để kiểm tra, thống kê hoặc sửa sau này, và là căn cứ xuất mẫu dữ liệu trước và sau xử lý (chương 7).

**Parquet cho dữ liệu đã xử lý.** Parquet tổ chức dữ liệu theo cột, truy vấn có thể chỉ đọc những cột cần dùng và dữ liệu thường nén hiệu quả (slide chương 4, tr. 46 [@slide-c4]). Định dạng cột còn cho phép đẩy điều kiện lọc xuống, tuỳ khả năng của nguồn dữ liệu (slide chương 5, tr. 42, 44 [@slide-c5]). Thí nghiệm (c) đo trực tiếp lợi ích này (mục 6.6).

**Ghi rồi đọc lại giữa các giai đoạn.** Ngoài việc đo được từng giai đoạn, cách này cắt chuỗi phụ thuộc (lineage) của DataFrame, tránh việc Spark tính lại toàn bộ từ dữ liệu thô ở giai đoạn sau (nhận định của nhóm). Đổi lại, mỗi giai đoạn trả thêm chi phí ghi và đọc Parquet trên MinIO.

**Cấu hình Spark mặc định của job.** `spark.sql.shuffle.partitions` = 8, AQE bật, ngưỡng broadcast tự động 10 MB (giá trị ghi trong metrics). Lệnh nộp job không đặt `spark.executor.memory`, nên executor dùng heap mặc định 1 GB [@spark-config]. Nhóm giữ giá trị này để cụm nằm trong giới hạn 6 GB của WSL2, giới hạn được đặt sau một lần Docker Desktop sập (mục 5.5).

## 4.6 Thiết kế thí nghiệm

Các thí nghiệm (b) đến (f) gắn với các khái niệm trong slide: speedup (slide chương 2, tr. 21 [@slide-c2]), định dạng cột (slide chương 4, tr. 46 [@slide-c4]), broadcast join, data skew, AQE và cache (slide chương 5, tr. 31, 48, 50, 51 [@slide-c5]). Thí nghiệm (a) và (g) là câu hỏi do đồ án đặt ra, để quan sát xu hướng theo kích thước dữ liệu và so sánh với Pandas một máy.

Bảng: Bảy thí nghiệm, biến thay đổi và biến cố định {#tbl:thiet-ke-thi-nghiem}

| Thí nghiệm | Câu hỏi | Biến thay đổi | Biến cố định | Số lần chạy |
|---|---|---|---|---|
| (a) `scale_data` | Thời gian tăng thế nào khi dữ liệu tăng? | Bộ dữ liệu 0,5M / 1M / 2,5M / 5M đơn | Join `auto`, AQE bật, 8 phân vùng shuffle, 2 worker | 4 × 3 = 12 |
| (b) `scale_workers` | Thêm worker được bao nhiêu? | 1 hoặc 2 worker | orders_5m, cấu hình mặc định | 2 × 3 = 6 |
| (c) `format_compare` | Parquet nhanh và nhỏ hơn CSV/JSON bao nhiêu? | Định dạng nguồn: thô hoặc Parquet curated | orders_5m, cùng 3 truy vấn, 2 worker | 2 thứ tự × 3 = 6 |
| (d) `join_strategy` | Broadcast join so với sort-merge join | `auto`, `broadcast`, `shuffle_noauto` | orders_5m, AQE bật, 8 phân vùng | 3 × 3 = 9 |
| (e) `skew` | Lệch khoá ảnh hưởng thế nào, AQE giúp được không? | Bộ cân bằng/lệch × join `auto`/ép shuffle × AQE bật/tắt | 2 worker, cùng mã ETL | 8 × 3 = 24 |
| (f) `cache` | Cache DataFrame dùng lại có lợi không? | Không cache / có cache | orders_5m, K = 5 truy vấn | 2 × 3 = 6 |
| (g) `pandas_baseline` | Spark so với Pandas một máy | Bộ 0,5M / 1M | Cùng luật làm sạch và tổng hợp | 2 × 3 = 6 |

Nguồn: src/experiments/README.md và README của từng thí nghiệm

Tổng cộng 69 lần chạy, gồm 63 lần chạy Spark và 6 lần chạy Pandas. So sánh hiệu năng dùng `processing_seconds_total`, tổng thời gian năm giai đoạn do job tự đo (định nghĩa chỉ số ở mục B.4). Bộ điều khiển chạy xen kẽ lần 1 của mọi cấu hình, rồi lần 2, rồi lần 3, riêng (b) chạy theo khối. Trước mỗi lần chạy Spark, bộ điều khiển kiểm tra số worker ALIVE, tổng số lõi và không có ứng dụng khác (mục B.4). Mỗi lần chạy có một bản ghi `run_record.json`, ý nghĩa từng cờ ở @tbl:co-hop-le (Phụ lục B). Với (d) và (e), bộ phân tích đọc event log để đếm toán tử join đã chạy thay vì chỉ dựa vào cấu hình (mục B.5).

Theo tài liệu Spark, AQE chỉ tách một phân vùng của sort-merge join khi phân vùng đó lớn hơn cả `skewedPartitionFactor` × trung vị (mặc định 5) và `skewedPartitionThresholdInBytes` (mặc định 256 MB) [@spark-sql-tuning]. Với 8 phân vùng mặc định, phân vùng lớn nhất của bộ lệch chỉ khoảng 34,7 MB, nên AQE không thể tách. Vì vậy nhóm chủ động đặt cho biến thể ép shuffle 64 phân vùng, ngưỡng lệch 4 MiB và kích thước phân vùng tư vấn 2 MiB, dựa trên phép đo kích thước phân vùng thật (mục B.6).

<!-- VERIFY
- MinIO tương thích S3: README kho minio/minio, điều phối viên đã mở lại 2026-11-08 ("S3-compatible object storage"); kho ghi đã ngừng bảo trì.
- HDFS và tách tính toán (c2 tr. 28), object storage (c4 tr. 37), Data Lake (c1 tr. 31, c4 tr. 47), Parquet (c4 tr. 46, c5 tr. 42, 44), speedup (c2 tr. 21): đã đối chiếu slide (report/review/verify-slides.md). `raw/` giữ nguyên, `quarantine/`, thí nghiệm (a), (g): quyết định của đồ án.
- Master cấp executor, driver gửi task: Spark Cluster Mode Overview 4.0.0 (điều phối viên đã mở trang 2026-11-08: "allocate resources across applications"; "SparkContext sends tasks to the executors to run").
- @fig:kien-truc: report/figures/kien-truc.png, report/build/draw_architecture.py; đối chiếu infra/docker-compose.yml, src/etl/pipeline.py. Repo không ghi ai viết script (verify-round2 B7).
- Kiểm tra cụm chỉ áp dụng cho lần chạy Spark: verify-round2 A3.
- Metrics JSON do driver ghi qua bind mount (results/ mount vào /opt/spark/work-dir/results): infra/docker-compose.yml; log do bộ điều khiển trên host ghi: docstring và hàm của src/experiments/common/runner.py (stdout/stderr vào results/logs/<exp>/<config>_r<k>.log).
- Năm giai đoạn và thứ tự: src/etl/pipeline.py hàm run.
- Luật đầu tiên thắng: docs/design/etl.md. Spark 4 bật ANSI mặc định: tài liệu Spark ANSI compliance 4.0.0.
- 255.378 / 200.008 / 55.370 và ~100 dòng ở bộ cân bằng (112, 113, 103, 99): docs/design/etl.md; commit 993d30b.
- Doanh thu chỉ tính paid/shipped/delivered: docs/design/etl.md mục Tổng hợp.
- spark.executor.memory mặc định 1g: Spark Configuration 4.0.0.
- autoBroadcastJoinThreshold 10485760b, shuffle.partitions 8: results/metrics/scale_data/runs/orders_5m/r3/run_record.json trường metrics.conf.
- Số lần chạy từng thí nghiệm (12, 6, 6, 9, 24, 6, 6 = 69): src/experiments/README.md mục "Ước tính"; khớp số dòng runs.csv.
- Thứ tự xen kẽ / scale_workers blocked: src/experiments/common/README.md, src/experiments/scale_workers/README.md, run_record runner_options.order.
- skewedPartitionFactor 5, threshold 256 MB, điều kiện "cả hai": Spark SQL Performance Tuning 4.0.0 mục Optimizing Skew Join. 34,7 MB: src/experiments/skew/README.md và results/metrics/skew/partition_stats_summary.csv.
- Lineage bị cắt khi ghi rồi đọc lại: nhận định của người viết.
- Chi tiết đã chuyển: VERIFY ở Phụ lục B (chỉ số, nhiễu, event log, tham số) và Phụ lục C (thành phần, luật làm sạch).
- Vòng 3 A7: giới hạn lúc sập là 9,7 GiB, 6 GB đặt sau sự cố (infra/README.md:73). B6: job tự đo thời gian từng giai đoạn.
-->
