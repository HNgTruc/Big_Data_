# Chương 7. Kết quả demo

Chương này tập hợp minh chứng hệ thống đã chạy thật: ảnh chụp giao diện Spark và MinIO, mẫu dữ liệu trước và sau xử lý, và trích đoạn log. Toàn bộ dữ liệu trong ảnh và bảng là **dữ liệu mô phỏng**. Ảnh được chụp ngày 2026-11-08, sau bộ đo chính thức; ảnh từ Spark History Server được dựng lại từ event log của thí nghiệm (e).

## 7.1 Cụm Spark và tài nguyên

![Spark Master UI: 2 worker ALIVE, tổng 4 lõi và 4,0 GiB, mỗi executor 1024 MiB, 68 ứng dụng đã hoàn thành](results/logs/screenshots/01_spark_master_workers.png){#fig:ss-master}

Nguồn: results/logs/screenshots/01_spark_master_workers.png

@fig:ss-master cho thấy cụm standalone ở trạng thái ALIVE với 2 worker, mỗi worker 2 lõi và 2,0 GiB, và cột "Memory per Executor" là 1024,0 MiB, tức heap mặc định 1 GB. Master UI ghi 68 ứng dụng đã hoàn thành: gồm 63 lần chạy Spark của bộ đo chính thức và các lần chạy thử trước đó. Số lần đo chính thức được lấy từ `results/metrics/*/runs.csv`, không lấy từ ảnh này.

![Tab Executors của một lần chạy skew_shuffle_aqe: 2 executor trên 2 worker, mỗi executor 2 lõi, Storage Memory 434,4 MiB](results/logs/screenshots/13_executors.png){#fig:ss-executors}

Nguồn: results/logs/screenshots/13_executors.png (ứng dụng app-20261107154233-0032)

Trong @fig:ss-executors, hai executor nằm trên hai địa chỉ worker khác nhau, lần lượt hoàn thành 609 và 637 task, cho thấy công việc được chia tương đối đều giữa hai worker. Storage Memory 434,4 MiB mỗi executor là vùng nhớ hợp nhất tách ra từ heap 1 GB (mục 5.2).

## 7.2 Lưu trữ trên MinIO

![MinIO Console: bucket bigdata với các vùng raw, curated, quarantine và smoke](results/logs/screenshots/02_minio_bucket_root.png){#fig:ss-minio-goc}

Nguồn: results/logs/screenshots/02_minio_bucket_root.png

![Vùng raw/orders_5m: sáu object gồm ba tệp CSV, một tệp Parquet, một tệp JSON lines và manifest](results/logs/screenshots/03_minio_raw_orders_5m.png){#fig:ss-minio-raw}

Nguồn: results/logs/screenshots/03_minio_raw_orders_5m.png

![Vùng curated/orders_5m: năm bảng sạch và ba bảng tổng hợp agg_*](results/logs/screenshots/04_minio_curated_orders_5m.png){#fig:ss-minio-curated}

Nguồn: results/logs/screenshots/04_minio_curated_orders_5m.png

![Vùng quarantine/orders_5m: ba bảng cách ly orders, order_items, web_events](results/logs/screenshots/05_minio_quarantine_orders_5m.png){#fig:ss-minio-quarantine}

Nguồn: results/logs/screenshots/05_minio_quarantine_orders_5m.png

Bốn ảnh trên tương ứng với cách tổ chức vùng lưu trữ ở @tbl:vung-luu-tru. Vùng `raw/orders_5m/` (@fig:ss-minio-raw) chứa đúng ba định dạng của bộ dữ liệu; `web_events.jsonl` là tệp lớn nhất. Vùng `curated/orders_5m/` (@fig:ss-minio-curated) chứa đầu ra Parquet của job, mỗi bảng là một thư mục gồm nhiều tệp phần (part file).

## 7.3 Mẫu dữ liệu trước và sau xử lý

Các mẫu dưới đây do job `src/etl/export_samples.py` trích từ MinIO: đọc `raw/`, `curated/`, `quarantine/` của bộ `orders_5m`, sắp theo khoá rồi lấy 5 dòng đầu cho mỗi trường hợp. Mẫu chỉ để minh hoạ cách xử lý, không đại diện thống kê cho cả bộ. Chạy lại cho kết quả giống hệt từng byte (`results/samples/orders_5m/README.md`).

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

**Bảng tổng hợp đầu ra.** Ba bảng tổng hợp có 731 dòng (`agg_daily_revenue`, một dòng mỗi ngày), 56 dòng (`agg_revenue_by_region_category`, 7 khu vực gồm cả `unknown` × 8 danh mục) và 2.193 dòng (`agg_events_daily`, 731 ngày × 3 loại sự kiện) (`results/samples/orders_5m/summary.csv`).

Bảng: Ba dòng đầu của agg_daily_revenue {#tbl:mau-agg-ngay}

| order_date | orders | revenue |
|---|---|---|
| 2024-01-01 | 5507 | 970430.76 |
| 2024-01-02 | 5477 | 987062.4 |
| 2024-01-03 | 5555 | 969962.09 |

Nguồn: results/samples/orders_5m/agg_daily_revenue.csv

Bảng: Ba dòng đầu của agg_revenue_by_region_category {#tbl:mau-agg-khu-vuc}

| region | category | revenue | units |
|---|---|---|---|
| central | beauty | 14376359.5 | 301502 |
| central | books | 14463827.41 | 300801 |
| central | electronics | 14134348.73 | 304495 |

Nguồn: results/samples/orders_5m/agg_revenue_by_region_category.csv

## 7.4 Kế hoạch thực thi và task trên Spark UI

![Spark History Server: danh sách ứng dụng của thí nghiệm skew dựng lại từ event log](results/logs/screenshots/06_history_app_list.png){#fig:ss-history}

Nguồn: results/logs/screenshots/06_history_app_list.png

![DAG của một job: các stage và ranh giới shuffle (ứng dụng skew_shuffle_aqe)](results/logs/screenshots/12_job_dag.png){#fig:ss-dag}

Nguồn: results/logs/screenshots/12_job_dag.png (ứng dụng app-20261107154233-0032)

@fig:ss-dag minh hoạ cách Spark chia một job thành các stage tại ranh giới shuffle (nút `Exchange`), theo mô hình DAG ở slide chương 5 [@slide-c5]. Hai stage đầu (33 và 37) được đánh dấu "skipped" vì kết quả shuffle của chúng đã có từ job trước và được dùng lại; chỉ stage 38 (join rồi `WriteFiles`) thực sự chạy.

![Kế hoạch SQL của skew_shuffle_aqe, bước ghi order_items sạch: SortMergeJoin(skew=true) và AQEShuffleRead với 49 lần tách phân vùng lệch](results/logs/screenshots/07_skew_shuffle_aqe_sql_plan.png){#fig:ss-aqe-plan}

Nguồn: results/logs/screenshots/07_skew_shuffle_aqe_sql_plan.png (ứng dụng app-20261107154233-0032, truy vấn SQL số 4)

![Kế hoạch SQL của skew_shuffle_noaqe, cùng bước: SortMergeJoin không có xử lý lệch](results/logs/screenshots/08_skew_shuffle_noaqe_sql_plan.png){#fig:ss-noaqe-plan}

Nguồn: results/logs/screenshots/08_skew_shuffle_noaqe_sql_plan.png (ứng dụng app-20261107154442-0033, truy vấn SQL số 4)

So sánh @fig:ss-aqe-plan với @fig:ss-noaqe-plan: khi bật AQE, nút join được đánh dấu `skew=true` và phía trên có `AQEShuffleRead` ghi "number of skewed partition splits: 49". Lưu ý khi đọc ảnh: tổng thời gian của một khối WholeStageCodegen hiển thị trên ảnh (ví dụ 3.05 h) là tổng cộng dồn thời gian của mọi task chạy song song, không phải thời gian thực của lần chạy, nên không được dùng làm số đo thời gian xử lý.

![Summary Metrics của stage đọc shuffle khi tắt AQE (64 task): dữ liệu đọc lớn nhất 15,5 MiB, task lâu nhất 0,5 s](results/logs/screenshots/09_skew_shuffle_noaqe_stage_tasks.png){#fig:ss-noaqe-tasks}

Nguồn: results/logs/screenshots/09_skew_shuffle_noaqe_stage_tasks.png (ứng dụng app-20261107154442-0033, stage 19)

![Summary Metrics của stage tương ứng khi bật AQE (104 task): dữ liệu đọc lớn nhất 1,9 MiB, task lâu nhất 0,2 s](results/logs/screenshots/10_skew_shuffle_aqe_stage_tasks.png){#fig:ss-aqe-tasks}

Nguồn: results/logs/screenshots/10_skew_shuffle_aqe_stage_tasks.png (ứng dụng app-20261107154233-0032, stage 32)

Hai ảnh @fig:ss-noaqe-tasks và @fig:ss-aqe-tasks cho thấy trực tiếp tác dụng của tách phân vùng lệch: trung vị dữ liệu đọc của một task giữ khoảng 1,5 MiB, nhưng giá trị lớn nhất giảm từ 15,5 MiB xuống 1,9 MiB. Số dòng của task lớn nhất khi tắt AQE (1.059.341 dòng) gần bằng phân vùng lớn nhất đo bằng `partition_stats` ở 64 phân vùng (1.059.025 dòng, `results/metrics/skew/partition_stats_summary.csv`), khớp với phép đo dùng để chọn tham số.

![Kế hoạch SQL của skew_auto_aqe: join với products là BroadcastHashJoin, khoá lệch không đi qua shuffle](results/logs/screenshots/11_skew_auto_aqe_sql_plan.png){#fig:ss-auto-plan}

Nguồn: results/logs/screenshots/11_skew_auto_aqe_sql_plan.png (ứng dụng app-20261107153343-0028, truy vấn SQL số 4)

Ở cấu hình mặc định (@fig:ss-auto-plan), join `order_items` với `products` là `BroadcastHashJoin`, nên dữ liệu không bị shuffle theo `product_id`. Ảnh cũng cho thấy nút `HashAggregate` của bước bỏ trùng phía trên có spill 1312,3 MiB: với heap 1 GB, phép bỏ trùng trên 10 triệu dòng hàng phải tràn ra đĩa.

## 7.5 Log chạy

Mỗi lần chạy lưu log đầy đủ của driver trong `results/logs/<thí nghiệm>/<cấu hình>_r<k>.log` và nhật ký của bộ điều khiển trong `runner.log`. Một số trích đoạn:

Dòng kết thúc thành công của một lần ETL trên orders_5m (`results/logs/scale_data/orders_5m_r3.log`):

```
ETL_OK processing_seconds_total=87.745 stages={'dimensions': 6.237,
  'orders': 14.288, 'order_items': 35.273, 'web_events': 22.301, 'aggregates': 9.646}
```

Nhật ký bộ điều khiển khi bắt đầu và kết thúc thí nghiệm (a) (`results/logs/scale_data/runner.log`, rút gọn lệnh):

```
[2026-11-07T22:00:54+07:00] [scale_data] start: 12 run(s), reps=3, order=interleaved, git=8164042... dirty=False
[2026-11-07T22:01:42+07:00] [scale_data] orders_500k r1: ok wall=47.429s processing=21.144
[2026-11-07T22:14:12+07:00] [scale_data] done: failures=0 status=0
```

Job xuất mẫu đối chiếu số đếm với metrics (`results/logs/export_samples_orders_5m.log`):

```
SAMPLES_OK out_dir=/opt/spark/work-dir/results/samples/orders_5m files=14 mismatches=0
```

Kiểm thử trong container Spark (`results/logs/test_etl.log`):

```
versions numpy 2.2.6 pandas 2.3.3 pyarrow 25.0.1 pyspark 4.0.0
41 passed in 64.91s (0:01:04)
```

Event log của Spark cho thí nghiệm (d) và (e) được lưu trong `results/logs/<thí nghiệm>/eventlogs/` trên máy đo nhưng không đưa lên git vì dung lượng lớn; @fig:ss-history đến @fig:ss-auto-plan được dựng lại từ các event log này.

<!-- VERIFY
- Ảnh chụp 2026-11-08: results/logs/screenshots/README.md cột Trạng thái.
- Ảnh 01: 2 Alive, 4 lõi, 4,0 GiB, 2,0 GiB mỗi worker, 1024,0 MiB, 68 Completed (đã xem ảnh). 68 = 63 + chạy thử: screenshots/README.md mục "Ghi chú khi dùng trong báo cáo". Lưu ý: app ID của export_samples là ...-0069, cần xác nhận ảnh 01 chụp trước hay sau lần chạy đó.
- Ảnh 13: 609 và 637 task, Storage Memory 434,4 MiB, 2 lõi mỗi executor (đã xem ảnh).
- Ảnh 03: sáu object (customers.csv, manifest.json, order_items.csv, orders.csv, products.parquet, web_events.jsonl), web_events lớn nhất 595,3 MiB (đã xem ảnh).
- Ảnh 04: 8 thư mục (3 agg_* + 5 bảng) (đã xem ảnh). Ảnh 02: curated, quarantine, raw, smoke (đã xem). Ảnh 12: stage 33, 37 skipped, stage 38 có WriteFiles (đã xem); diễn giải "skipped vì dùng lại kết quả shuffle" theo hành vi chuẩn của Spark UI, cần đối chiếu tài liệu. Ảnh 05, 06, 08 chưa được người viết mở trực tiếp; mô tả dựa trên screenshots/README.md.
- Mẫu dữ liệu: các tệp CSV trong results/samples/orders_5m/; tính xác định: results/samples/orders_5m/README.md.
- Đơn 7 bị cách ly null_customer_id: results/samples/orders_5m/quarantine_orders.csv dòng 2.
- product_id 20818 > 20.000 sản phẩm: products raw_rows 20.000 trong results/metrics/orders_5m.json (giả định product_id đánh số 1..20.000, cần kiểm src/data_generation/tables.py).
- 731 / 56 / 2.193: results/samples/orders_5m/summary.csv; 7 khu vực gồm unknown × 8 danh mục: docs/design/etl.md.
- Ảnh 07, 09, 10, 11: số đọc từ screenshots/README.md mục "Số đọc được trên ảnh" và chính ảnh (đã xem 07, 09, 10, 11); 1.059.341 dòng (ảnh 09, Shuffle Read Records max) và 1.059.025 dòng (partition_stats_summary.csv rows_max, skew, 64).
- 3.05 h là tổng cộng dồn: screenshots/README.md.
- Spill 1312,3 MiB ở HashAggregate: ảnh 11. Diễn giải "phải tràn ra đĩa do heap 1 GB" là nhận định của người viết.
- Trích log: results/logs/scale_data/orders_5m_r3.log (dòng 2613), runner.log dòng 1, 3, 26, export_samples_orders_5m.log dòng 3199, test_etl.log.
- Event log không đưa lên git: src/experiments/join_strategy/README.md, results/logs/README.md.
-->
