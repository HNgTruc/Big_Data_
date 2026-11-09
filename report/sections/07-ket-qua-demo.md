# Chương 7. Kết quả demo

Chương này tập hợp minh chứng hệ thống đã chạy thật: ảnh chụp giao diện Spark và MinIO, và mẫu dữ liệu trước và sau xử lý. Các ảnh chụp còn lại, mẫu bảng tổng hợp và trích đoạn log nằm ở Phụ lục E. Toàn bộ dữ liệu trong ảnh và bảng là **dữ liệu mô phỏng**. Ảnh được chụp ngày 2026-11-08, sau bộ đo chính thức; ảnh từ Spark History Server được dựng lại từ event log của thí nghiệm (e). Ảnh chụp trong báo cáo là bản cắt khung và thêm viền của ảnh gốc, không sửa nội dung bên trong; ảnh gốc ghi ở dòng Nguồn của từng hình. Riêng @fig:ke-hoach-so-sanh là sơ đồ vẽ lại, không phải ảnh chụp.

## 7.1 Cụm Spark và tài nguyên

![Spark Master UI: 2 worker ALIVE, tổng 4 lõi và 4,0 GiB, mỗi executor 1024 MiB, 68 ứng dụng đã hoàn thành](report/figures/screenshots/01_spark_master_workers.png){#fig:ss-master}

Nguồn: results/logs/screenshots/01_spark_master_workers.png

@fig:ss-master cho thấy cụm standalone ở trạng thái ALIVE với 2 worker, mỗi worker 2 lõi và 2,0 GiB, và cột "Memory per Executor" là 1024,0 MiB, tức heap mặc định 1 GB. Master UI ghi 68 ứng dụng đã hoàn thành: 63 lần chạy Spark của bộ đo chính thức (mã ứng dụng `-0005` đến `-0067`, liên tục) và 5 lần chạy thử trước đó (`-0000` đến `-0004`); ảnh được chụp trước hai ứng dụng `-0068` và `-0069`. Số lần đo chính thức được lấy từ `results/metrics/*/runs.csv`, không lấy từ ảnh này.

Tab Executors của một lần chạy `skew_shuffle_aqe` (@fig:ss-executors, Phụ lục E) cho thấy hai executor nằm trên hai địa chỉ worker khác nhau, lần lượt hoàn thành 609 và 637 task, tức công việc được chia tương đối đều giữa hai worker.

## 7.2 Lưu trữ trên MinIO

![Vùng raw/orders_5m: sáu object gồm ba tệp CSV, một tệp Parquet, một tệp JSON lines và manifest](report/figures/screenshots/03_minio_raw_orders_5m.png){#fig:ss-minio-raw}

Nguồn: results/logs/screenshots/03_minio_raw_orders_5m.png

Bucket `bigdata` có đúng các vùng đã thiết kế ở @tbl:vung-luu-tru (@fig:ss-minio-goc, Phụ lục E). Vùng `raw/orders_5m/` (@fig:ss-minio-raw) chứa đúng ba định dạng của bộ dữ liệu; `web_events.jsonl` là tệp lớn nhất. Vùng `curated/orders_5m/` (@fig:ss-minio-curated, Phụ lục E) chứa đầu ra Parquet của job, mỗi bảng là một thư mục gồm nhiều tệp phần (part file); vùng `quarantine/orders_5m/` chứa ba bảng cách ly (@fig:ss-minio-quarantine, Phụ lục E).

## 7.3 Mẫu dữ liệu trước và sau xử lý

Các mẫu dưới đây do job `src/etl/export_samples.py` trích từ MinIO: đọc `raw/`, `curated/`, `quarantine/` của bộ `orders_5m`, sắp theo khoá rồi lấy 5 dòng đầu cho mỗi trường hợp. Đầu ra được đọc là của lần chạy ETL `app-20261106181012-0003` (lần chạy đầu ngày 06/11, cũng là `results/metrics/orders_5m.json`), không phải từ các lần chạy của bộ đo chính thức. Mẫu chỉ để minh hoạ cách xử lý, không đại diện thống kê cho cả bộ. Chạy lại cho kết quả giống hệt từng byte (`results/samples/orders_5m/README.md`).

**Bản ghi trùng được bỏ.** Mỗi khoá xuất hiện hai lần trong dữ liệu thô và còn đúng một lần sau xử lý.

Bảng: Bỏ bản ghi trùng của orders (trích 2 khoá) {#tbl:mau-trung}

| Giai đoạn | order_id | customer_id | order_date | status | payment_method |
|---|---|---|---|---|---|
| raw | 30 | 25619 | 2024-07-24 | paid | e_wallet |
| raw | 30 | 25619 | 2024-07-24 | paid | e_wallet |
| curated | 30 | 25619 | 2024-07-24 | paid | e_wallet |
| raw | 37 | 162760 | 2024-10-28 | delivered | card |
| raw | 37 | 162760 | 2024-10-28 | delivered | card |
| curated | 37 | 162760 | 2024-10-28 | delivered | card |

Nguồn: results/samples/orders_5m/duplicates_orders.csv

**Ngày và thời gian sai định dạng được chuẩn hoá, không bị cách ly.**

Bảng: Chuẩn hoá ngày đặt hàng và thời gian sự kiện (trích) {#tbl:mau-ngay}

| Khoá | Giá trị thô | Định dạng nhận diện | Sau xử lý |
|---|---|---|---|
| order_id 113 | 25-01-2024 | dd-MM-yyyy | 2024-01-25 |
| order_id 224 | 09/07/2025 | dd/MM/yyyy | 2025-07-09 |
| order_id 8 | 20250117 | yyyyMMdd | 2025-01-17 |
| event_id E0000000078 | 02/03/2025 09:10:59 | dd/MM/yyyy HH:mm:ss | 2025-03-02 09:10:59 |
| event_id E0000000027 | 20250417182524 | yyyyMMddHHmmss | 2025-04-17 18:25:24 |

Nguồn: results/samples/orders_5m/bad_dates_orders.csv, bad_times_web_events.csv

**Bản ghi lỗi được cách ly kèm lý do.** Ô trống là giá trị thiếu trong dữ liệu thô.

Bảng: Dòng hàng bị cách ly theo từng lý do (trích một dòng mỗi lý do) {#tbl:mau-cach-ly}

| reject_reason | order_id | line_no | product_id | quantity | unit_price |
|---|---|---|---|---|---|
| null_unit_price | 2 | 4 | 10929 | 1 | |
| non_positive_quantity | 5 | 2 | 15468 | 0 | 8.17 |
| non_positive_price | 196 | 1 | 12471 | 1 | -185.08 |
| orphan_product_id | 25 | 1 | 20818 | 1 | 28.96 |
| no_clean_order | 7 | 1 | 10349 | 1 | 79.08 |

Nguồn: results/samples/orders_5m/quarantine_order_items.csv

Dòng `no_clean_order` của đơn 7 minh hoạ hệ quả dây chuyền: dòng hàng không có lỗi, nhưng đơn 7 đã bị cách ly vì thiếu `customer_id` (dòng đầu tiên của `results/samples/orders_5m/quarantine_orders.csv`). Dòng `orphan_product_id` có `product_id` 20818, vượt quá 20.000 sản phẩm của bộ dữ liệu.

**Giá trị thiếu được xử lý tại chỗ.** Khách hàng thiếu `region` không bị cách ly mà được gán `unknown`.

Bảng: Gán region thiếu thành unknown (trích) {#tbl:mau-region}

| customer_id | region thô | region sau xử lý | signup_date |
|---|---|---|---|
| 32 | (trống) | unknown | 2023-09-21 |
| 82 | (trống) | unknown | 2023-08-12 |
| 178 | (trống) | unknown | 2021-08-04 |

Nguồn: results/samples/orders_5m/missing_region_customers.csv

**Bảng tổng hợp đầu ra.** Ba bảng tổng hợp có 731 dòng (`agg_daily_revenue`, một dòng mỗi ngày), 56 dòng (`agg_revenue_by_region_category`, 7 khu vực gồm cả `unknown` × 8 danh mục) và 2.193 dòng (`agg_events_daily`, 731 ngày × 3 loại sự kiện) (`results/samples/orders_5m/summary.csv`). Các dòng đầu của hai bảng ở @tbl:mau-agg-ngay và @tbl:mau-agg-khu-vuc (Phụ lục E).

## 7.4 Kế hoạch thực thi và task trên Spark UI

Mục này so sánh kế hoạch và task giữa các cấu hình của thí nghiệm (e). Danh sách ứng dụng đọc lại từ event log (@fig:ss-history) và ảnh DAG minh hoạ ranh giới stage tại shuffle (@fig:ss-dag) ở mục E.2 (Phụ lục E).

![Ba kế hoạch đã chạy của bước ghi order_items sạch: phép join theo product_id khác nhau giữa các cấu hình, các bước còn lại giống nhau](report/figures/ke-hoach-so-sanh.png){#fig:ke-hoach-so-sanh}

Nguồn: vẽ bằng script report/build/draw_plan_comparison.py; cấu trúc theo event log của truy vấn SQL số 4 (results/logs/skew/plan_query4.txt), số liệu theo ảnh 07, 09, 10, 11 trong results/logs/screenshots/

@fig:ke-hoach-so-sanh so sánh cùng một phép join qua ba cấu hình. Khi tắt AQE (a), join theo `product_id` là `SortMergeJoin` thường. Khi bật AQE (b), join đó được đánh dấu `skew=true`, và `AQEShuffleRead` ở phía trước ghi "number of skewed partition splits: 49". Ảnh chụp giao diện tương ứng là @fig:ss-aqe-plan, @fig:ss-noaqe-plan và @fig:ss-auto-plan (mục E.2, Phụ lục E).

![Summary Metrics của stage đọc shuffle khi tắt AQE (64 task): dữ liệu đọc lớn nhất 15,5 MiB, task lâu nhất 0,5 s](report/figures/screenshots/09_skew_shuffle_noaqe_stage_tasks.png){#fig:ss-noaqe-tasks}

Nguồn: results/logs/screenshots/09_skew_shuffle_noaqe_stage_tasks.png; mã ứng dụng app-20261107154442-0033 và stage 19 theo results/logs/screenshots/README.md (không hiện trên phần ảnh đã cắt)

![Summary Metrics của stage tương ứng khi bật AQE (104 task): dữ liệu đọc lớn nhất 1,9 MiB, task lâu nhất 0,2 s](report/figures/screenshots/10_skew_shuffle_aqe_stage_tasks.png){#fig:ss-aqe-tasks}

Nguồn: results/logs/screenshots/10_skew_shuffle_aqe_stage_tasks.png; mã ứng dụng app-20261107154233-0032 và stage 32 theo results/logs/screenshots/README.md (không hiện trên phần ảnh đã cắt)

Hai ảnh @fig:ss-noaqe-tasks và @fig:ss-aqe-tasks cho thấy trực tiếp tác dụng của tách phân vùng lệch: trung vị dữ liệu đọc của một task giữ khoảng 1,5 MiB, nhưng giá trị lớn nhất giảm từ 15,5 MiB xuống 1,9 MiB. Khi tắt AQE, Shuffle Write lớn nhất của một task là 1.059.025 bản ghi, trùng chính xác `rows_max` của phép đo `partition_stats` ở 64 phân vùng (`results/metrics/skew/partition_stats_summary.csv`), còn Shuffle Read lớn nhất là 1.059.341 bản ghi. Sự trùng khớp này cho thấy phép đo dùng để chọn tham số phản ánh đúng phân vùng lớn nhất khi chạy thật.

Ở cấu hình mặc định (cột (c) của @fig:ke-hoach-so-sanh), join `order_items` với `products` là `BroadcastHashJoin`, nên dữ liệu không bị shuffle theo `product_id`. @fig:ss-auto-plan (Phụ lục E) cũng cho thấy nút `HashAggregate` của bước bỏ trùng phía trên có spill 1312,3 MiB: với heap 1 GB, phép bỏ trùng trên 10 triệu dòng hàng phải tràn ra đĩa (nhận định của nhóm).

<!-- VERIFY
- Ảnh chụp 2026-11-08: results/logs/screenshots/README.md cột Trạng thái.
- Ảnh 01: 2 Alive, 4 lõi, 4,0 GiB, 2,0 GiB mỗi worker, 1024,0 MiB, 68 Completed. 68 = 63 (-0005 đến -0067) + 5 chạy thử (-0000 đến -0004), chụp trước -0068, -0069: verify-round1 mục C.
- Ảnh 13: 609 và 637 task, Storage Memory 434,4 MiB, 2 lõi mỗi executor.
- Ảnh 03: sáu object (customers.csv, manifest.json, order_items.csv, orders.csv, products.parquet, web_events.jsonl), web_events lớn nhất 595,3 MiB.
- Mẫu đọc từ đầu ra ETL app-20261106181012-0003: results/samples/orders_5m/README.md, trường app_id trong results/metrics/orders_5m.json.
- Mẫu dữ liệu: các tệp CSV trong results/samples/orders_5m/; tính xác định: results/samples/orders_5m/README.md.
- Đơn 7 bị cách ly null_customer_id: results/samples/orders_5m/quarantine_orders.csv dòng 2.
- product_id 20818 > 20.000 sản phẩm: products raw_rows 20.000 trong results/metrics/orders_5m.json (giả định product_id đánh số 1..20.000, cần kiểm src/data_generation/tables.py).
- 731 / 56 / 2.193: results/samples/orders_5m/summary.csv; 7 khu vực gồm unknown × 8 danh mục: docs/design/etl.md.
- Ảnh 07, 09, 10, 11: số đọc từ screenshots/README.md mục "Số đọc được trên ảnh" và chính ảnh. Ảnh 09: Shuffle Write max 13.7 MiB / 1059025, Shuffle Read max 15.5 MiB / 1059341 (đã xem ảnh); rows_max 1059025 ở partition_stats_summary.csv dòng orders_5m_skew, 64.
- ID ứng dụng và stage của ảnh 09, 10 không hiện trên ảnh đã cắt: verify-round1 mục B; nguồn là results/logs/screenshots/README.md.
- 3.05 h là tổng cộng dồn: screenshots/README.md.
- Tên bảng `products` không hiện trên ảnh 11 đã cắt; event log xác nhận join theo product_id là BroadcastHashJoin (results/logs/skew/plan_query4.txt).
- @fig:ke-hoach-so-sanh: cấu trúc của cả ba cột và số phân vùng (64, 8) đã đối chiếu với results/logs/skew/plan_query4.txt; đã lược các nút WholeStageCodegen, InputAdapter, ColumnarToRow, Project, Filter phía trước join. Số liệu 15,5 MiB, 0,5 s, 64 task: ảnh 09; 1,9 MiB, 0,2 s, 104 task: ảnh 10; 49: ảnh 07; 10.000.351, 1312,3 MiB: ảnh 11. Đều của lần r1.
- Spill 1312,3 MiB ở HashAggregate: ảnh 11. Diễn giải "phải tràn ra đĩa do heap 1 GB" là nhận định của người viết.
- Câu "phép đo phản ánh đúng phân vùng lớn nhất" là nhận định của người viết từ sự trùng khớp số.
-->
