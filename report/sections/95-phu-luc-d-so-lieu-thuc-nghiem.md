# Phụ lục D. Số liệu chi tiết của các thí nghiệm

Phụ lục này ghi các bảng số chi tiết của chương 6. Phân tích và kết luận từ các bảng này nằm trong chương 6, ở mục tương ứng. Toàn bộ là số đo trên **dữ liệu mô phỏng**.

## D.1 Thí nghiệm (a): thời gian từng giai đoạn

Bảng: Thời gian trung bình từng giai đoạn theo kích thước dữ liệu (giây) {#tbl:scale-giai-doan-chi-tiet}

| Bộ | dimensions | orders | order_items | web_events | aggregates |
|---|---|---|---|---|---|
| orders_500k | 4,47 | 5,21 | 4,29 | 3,99 | 3,93 |
| orders_1m | 5,22 | 6,07 | 5,57 | 6,26 | 4,82 |
| orders_2500k | 5,59 | 9,38 | 11,49 | 9,77 | 6,20 |
| orders_5m | 6,29 | 14,05 | 27,34 | 20,12 | 9,34 |

Nguồn: results/metrics/scale_data/summary.csv (stage_*)

## D.2 Thí nghiệm (c): dung lượng và số byte trên mỗi dòng

Bảng: Dung lượng lưu trữ thô và Parquet đã làm sạch, kèm byte/dòng (orders_5m, MB = 10^6 byte) {#tbl:format-byte-dong}

| Bảng | Định dạng thô | Thô (MB) | Parquet curated (MB) | Thô / curated | Byte/dòng thô | Byte/dòng curated |
|---|---|---|---|---|---|---|
| customers | CSV | 12,90 | 2,93 | 4,41 | 25,3 | 5,9 |
| orders | CSV | 216,90 | 51,78 | 4,19 | 42,5 | 10,8 |
| order_items | CSV | 235,52 | 65,63 | 3,59 | 23,1 | 7,3 |
| products | Parquet | 0,20 | 0,17 | 1,23 | 10,2 | 8,3 |
| web_events | JSON lines | 624,17 | 105,73 | 5,90 | 122,4 | 21,6 |
| **Tổng** | | **1.089,70** | **226,24** | **4,82** | | |

Nguồn: results/metrics/format_compare/sizes.csv (raw_bytes, curated_bytes, ratio_raw_over_curated); số dòng từ results/samples/orders_5m/summary.csv; cột byte/dòng và dòng Tổng do người viết tính

## D.3 Thí nghiệm (e): kích thước phân vùng

Bảng: Kích thước phân vùng khi băm order_items theo product_id (MB = 10^6 byte) {#tbl:partition-stats}

| Bộ | Số phân vùng | Lớn nhất (MB) | Trung vị (MB) | Lớn nhất / trung vị | Số phân vùng > 5 × trung vị |
|---|---|---|---|---|---|
| orders_5m | 8 | 24,77 | 24,47 | 1,01 | 0 |
| orders_5m | 64 | 3,47 | 2,94 | 1,18 | 0 |
| orders_5m_skew | 8 | 34,71 | 19,58 | 1,77 | 0 |
| orders_5m_skew | 64 | 16,18 | 1,54 | 10,54 | 9 |

Nguồn: results/metrics/skew/partition_stats_summary.csv

## D.4 Thí nghiệm (f): thời gian từng truy vấn

Bảng: Thời gian từng truy vấn không cache và có cache (orders_5m, n = 3) {#tbl:cache-truy-van}

| Bước | Không cache (s) | Có cache (s) | Không cache / có cache |
|---|---|---|---|
| Materialize (`cache()` + `count()`) | | 8,03 ± 0,66 | |
| q1 doanh thu theo ngày | 4,37 | 0,75 | 5,86 |
| q2 doanh thu theo trạng thái | 3,33 | 0,69 | 4,83 |
| q3 top 10 sản phẩm | 2,78 | 0,63 | 4,41 |
| q4 số dòng theo thanh toán | 2,32 | 0,45 | 5,10 |
| q5 trung bình theo `line_no` | 2,95 | 0,35 | 8,32 |
| Tổng 5 truy vấn | 15,75 ± 1,01 | 2,88 ± 0,09 | 5,48 |
| Tổng gồm materialize | 15,75 ± 1,01 | 10,90 ± 0,59 | 1,44 |

Nguồn: results/metrics/cache/summary.csv; cột tỉ lệ do người viết tính

## D.5 Thí nghiệm (g): thời gian từng giai đoạn của Pandas

Bảng: Thời gian từng giai đoạn của Pandas (giây) {#tbl:pandas-giai-doan}

| Bộ | dimensions | orders | order_items | web_events | aggregates |
|---|---|---|---|---|---|
| orders_500k | 0,14 | 0,89 | 0,36 | 1,83 | 0,39 |
| orders_1m | 0,19 | 1,73 | 0,74 | 3,65 | 0,76 |

Nguồn: results/metrics/pandas_baseline/summary.csv

<!-- VERIFY
- D.1: results/metrics/scale_data/summary.csv (stage_*).
- D.2: results/metrics/format_compare/sizes.csv; byte/dòng = raw_bytes/raw_rows, curated_bytes/curated_rows (results/samples/orders_5m/summary.csv); products 203.748/20.000 = 10,2 và 165.869/20.000 = 8,3; tổng 1.089.695.264 và 226.238.030 byte, tỉ lệ 4,82.
- D.3: results/metrics/skew/partition_stats_summary.csv.
- D.4: results/metrics/cache/summary.csv; tỉ lệ từng truy vấn do người viết chia.
- D.5: results/metrics/pandas_baseline/summary.csv.
-->
