# Phụ lục D. Số liệu chi tiết của các thí nghiệm

Toàn bộ số đo dưới đây chạy trên dữ liệu mô phỏng. Phát hiện chính và kết luận nằm ở chương 6. D.1 đến D.5 ghi bảng số theo giai đoạn và truy vấn, D.6 đến D.14 ghi cấu hình, bảng và hình phụ, lập luận từng bước theo thứ tự mục 6.1 đến 6.10.

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

Nguồn: results/metrics/format_compare/sizes.csv (raw_bytes, curated_bytes, ratio_raw_over_curated); số dòng từ results/samples/orders_5m/summary.csv; cột byte/dòng và dòng Tổng do nhóm tính

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

Nguồn: results/metrics/cache/summary.csv; cột tỉ lệ do nhóm tính

## D.5 Thí nghiệm (g): thời gian từng giai đoạn của Pandas

Bảng: Thời gian từng giai đoạn của Pandas (giây) {#tbl:pandas-giai-doan}

| Bộ | dimensions | orders | order_items | web_events | aggregates |
|---|---|---|---|---|---|
| orders_500k | 0,14 | 0,89 | 0,36 | 1,83 | 0,39 |
| orders_1m | 0,19 | 1,73 | 0,74 | 3,65 | 0,76 |

Nguồn: results/metrics/pandas_baseline/summary.csv

## D.6 Môi trường và phương pháp đo

Bảng: Môi trường của bộ đo chính thức {#tbl:moi-truong}

| Mục | Giá trị |
|---|---|
| Máy | Một máy Windows 11 Pro, CPU Intel Core i5-14400F (10 nhân, 16 luồng), RAM 16 GB (hệ điều hành báo 15,76 GB); một ổ SSD NVMe MAXBY MAX3500 1TB chia hai phân vùng C: và D: |
| Docker | Docker Desktop (engine 29.9.2) trên WSL2, giới hạn 6 GB RAM (`.wslconfig`) |
| Cụm Spark | Standalone, 1 master + 2 worker, mỗi worker 2 lõi và tối đa 2 GB; mỗi executor heap 1 GB |
| Phần mềm | Spark 4.0.0, `hadoop-aws` 3.4.1, MinIO RELEASE.2026-10-23T20-06-51Z (image Chainguard) |
| Dữ liệu | Dữ liệu mô phỏng, seed 42, tỉ lệ lỗi 2% mỗi loại |
| Thời gian đo | 2026-11-07, 22:00:54 đến 23:41:37 (giờ Việt Nam) |
| Mã nguồn | Commit `8164042` |
| Số lần chạy | 69 (63 Spark + 6 Pandas), tất cả trạng thái `ok`, không lần nào bị loại |

Nguồn: results/logs/environment.txt (thu thập 2026-11-08, sau bộ đo, cùng máy), results/logs/scale_data/runner.log (dòng đầu), results/metrics/*/runs.csv (cột status, valid, git_commit, started_at, ended_at), infra/README.md

Các lần chạy ETL đầu tiên của từng bộ (`results/metrics/orders_*.json`) chỉ chạy một lần khi máy chưa ở trạng thái sạch. Nhóm chỉ dùng chúng để kiểm tra tính đúng và số đếm chất lượng, không dùng làm số đo hiệu năng.

63 lần chạy Spark đều qua kiểm tra trước khi chạy (số worker, số lõi, không có ứng dụng khác) và sau khi chạy (số worker không đổi). Khi phân tích, `src/experiments/common/analysis.py` (hàm `run_flags`, cờ `raw_rows_mismatch`) đối chiếu số dòng thô của các lần ETL với manifest, còn mỗi lần Pandas tự đối chiếu 49 số đếm. Không lần nào bị loại, mọi nhóm có `n` = 3 (hoặc 6 với (c)). Danh sách cờ ở @tbl:co-hop-le (Phụ lục B).

Các nhóm truy vấn ngắn có CV vượt 10% (tính từ các `summary.csv` tương ứng):

- Trong (c): q1 thô 17,0%, q1 Parquet 19,5%, q2 Parquet 91,5%, q3 Parquet 21,0%.
- Trong (f): q5 không cache 23,3%, q3 có cache 12,6%, q5 có cache 15,8%.

## D.7 Chất lượng dữ liệu: nhận xét chi tiết

Riêng `order_items`, job bỏ đúng 200.030 dòng trùng nhờ bỏ trùng theo khoá (`order_id`, `line_no`). 376.230 dòng `no_clean_order` trên 199.956 đơn bị cách ly là khoảng 1,9 dòng hàng mỗi đơn, sát mức trung bình 2 dòng/đơn của bộ sinh. Số đếm giống hệt nhau giữa mọi lần chạy (`counts_consistent` = True) cho thấy job cho kết quả xác định.

## D.8 Thí nghiệm (a): cấu hình, bảng và phân tích

Cấu hình: join `auto`, AQE bật, 8 phân vùng shuffle, 2 worker, 4 bộ × 3 lần, thứ tự xen kẽ.

Bảng: Thời gian xử lý và thông lượng theo kích thước dữ liệu {#tbl:scale-tong}

| Bộ | Dòng thô | Thời gian xử lý (s) | Min–max (s) | Thông lượng (dòng/s) | Tỉ lệ dữ liệu | Tỉ lệ thời gian |
|---|---|---|---|---|---|---|
| orders_500k | 2.092.960 | 21,90 ± 0,74 | 21,14–22,63 | 95.664 | 1,00 | 1,00 |
| orders_1m | 4.184.974 | 27,94 ± 0,36 | 27,54–28,26 | 149.821 | 2,00 | 1,28 |
| orders_2500k | 10.464.824 | 42,43 ± 0,19 | 42,31–42,65 | 246.645 | 5,00 | 1,94 |
| orders_5m | 20.931.505 | 77,14 ± 9,19 | 71,40–87,75 | 273.766 | 10,00 | 3,52 |

Nguồn: results/metrics/scale_data/summary.csv (processing_seconds_total, throughput_rows_per_s, data_ratio, time_ratio)

Thông lượng trong @tbl:scale-tong là trung bình của thông lượng từng lần chạy, nên khác một chút so với tổng dòng chia thời gian trung bình (ở orders_5m: 273.766 so với 271.340 dòng/s).

![Thông lượng (dòng thô/giây) theo kích thước dữ liệu](results/figures/scale_data/throughput.png){#fig:scale-thong-luong}

Nguồn: results/metrics/scale_data/summary.csv

![Thời gian từng giai đoạn ETL theo kích thước dữ liệu](results/figures/scale_data/stages.png){#fig:scale-giai-doan}

Nguồn: results/metrics/scale_data/summary.csv

@fig:scale-thong-luong vẽ thông lượng theo kích thước, @fig:scale-giai-doan vẽ thời gian từng giai đoạn. Giai đoạn `order_items` có hai phép join và một lần bỏ trùng. Ngoài thời gian xử lý, mỗi lần chạy tốn thêm khoảng 23 đến 24 giây gần như không đổi theo kích thước (`wall_seconds` − `processing_seconds_total`, tính từ summary), gồm khởi động container và JVM, đăng ký executor, bước thống kê và tắt Spark. Với bộ 500k, phần này lớn hơn cả thời gian xử lý.

Lần r3 của bộ 5M chậm chủ yếu ở `order_items` (35,27 so với khoảng 23,4 giây, `results/metrics/scale_data/runs.csv`). Lấy lần chậm nhất của bộ 5M chia cho trung bình của bộ 500k, tỉ lệ thời gian là 4,01 (87,745/21,895). Chia cho lần chậm nhất của bộ 500k là 3,88 (87,745/22,631), chia cho lần nhanh nhất của bộ 500k là 4,15 (87,745/21,144).

## D.9 Thí nghiệm (b): cấu hình, hình và lập luận

Cấu hình: orders_5m, cấu hình mặc định. `w1` dừng `spark-worker-2`, cụm còn 1 executor, 2 lõi, heap 1 GB. `w2` dùng đủ 2 worker.

![Thời gian ETL với 1 và 2 worker và speedup theo từng giai đoạn](results/figures/scale_workers/speedup.png){#fig:workers-speedup}

Nguồn: results/metrics/scale_workers/summary.csv

Theo @fig:workers-speedup, bốn giai đoạn đạt S từ 1,27 đến 1,41 là `orders`, `order_items`, `web_events`, `aggregates`. Ở `dimensions`, chi phí phối hợp gồm cả trao đổi dữ liệu shuffle qua mạng (nhận định của nhóm, chưa kiểm chứng bằng event log).

Ước lượng theo định luật Amdahl dùng công thức ở slide chương 2, tr. 22 [@slide-c2], ước lượng và diễn giải là nhận định của nhóm. Với N = 2 và S = 1,29, từ S = 1 / ((1 − p) + p/N) suy ra p ≈ 0,45. Ở đây p là phần song song, N là số worker, slide dùng s = 1 − p cho phần tuần tự và p cho số node. Con số gộp các chi phí không giảm khi thêm worker: lập lịch ở driver, ghi metadata, tranh chấp I/O vì MinIO, hai worker và hệ điều hành dùng chung một ổ đĩa vật lý, và áp lực RAM trên host.

Chuyển từ 1 lên 2 worker đổi cả số lõi lẫn bộ nhớ. Với 1 worker, dữ liệu shuffle có thể tràn ra đĩa nhiều hơn. Khối `w1` chạy từ 23:28 đến 23:35, khối `w2` từ 23:35 đến 23:41.

## D.10 Thí nghiệm (c): cấu hình, bảng, hình và lập luận

Cấu hình: orders_5m, cùng phiên Spark như ETL, 2 worker. q1 lọc `orders` theo `status = 'delivered'` rồi đếm, q2 đếm `web_events` theo `event_type`, q3 join `order_items` với `orders` và tính tổng doanh thu theo ngày. Hai cấu hình đảo thứ tự định dạng trong mỗi truy vấn, mỗi cấu hình 3 lần, số liệu gộp n = 6.

Bảng: Dung lượng lưu trữ thô và Parquet đã làm sạch (orders_5m, MB = 10^6 byte) {#tbl:format-kich-thuoc}

| Bảng | Định dạng thô | Thô (MB) | Parquet curated (MB) | Thô / curated |
|---|---|---|---|---|
| customers | CSV | 12,90 | 2,93 | 4,41 |
| orders | CSV | 216,90 | 51,78 | 4,19 |
| order_items | CSV | 235,52 | 65,63 | 3,59 |
| products | Parquet | 0,20 | 0,17 | 1,23 |
| web_events | JSON lines | 624,17 | 105,73 | 5,90 |
| **Tổng** | | **1.089,70** | **226,24** | **4,82** |

Nguồn: results/metrics/format_compare/sizes.csv (raw_bytes, curated_bytes, ratio_raw_over_curated); dòng Tổng do nhóm tính

![Thời gian ba truy vấn trên dữ liệu thô và Parquet](results/figures/format_compare/query_times_orders_5m.png){#fig:format-truy-van}

Nguồn: results/metrics/format_compare/summary.csv

![Dung lượng lưu trữ từng bảng: thô so với Parquet đã làm sạch](results/figures/format_compare/storage_orders_5m.png){#fig:format-dung-luong}

Nguồn: results/metrics/format_compare/sizes.csv

@fig:format-truy-van và @fig:format-dung-luong vẽ lại số liệu của @tbl:format-thoi-gian và @tbl:format-kich-thuoc. Độ lệch chuẩn của q2 trên Parquet lớn vì một lần đo 2,48 giây trong khi các lần khác 0,44 đến 0,70 giây (`results/metrics/format_compare/runs.csv`). Tách theo thứ tự chạy, tỉ lệ thô/Parquet của q2 là 5,46 khi đọc thô trước và 1,75 khi đọc Parquet trước (`summary_by_order.csv`). Cột `homogeneous` = False trong `summary.csv` là do gộp hai cấu hình thứ tự, đúng như thiết kế.

Kết quả truy vấn trên hai định dạng khác nhau. q1 đếm được 3.060.980 đơn trên dữ liệu thô so với 2.880.698 trên Parquet (cột `result` trong `runs.csv`).

## D.11 Thí nghiệm (d): cấu hình, bảng, hình và lập luận

Cấu hình: orders_5m, AQE bật, 8 phân vùng. Với `shuffle_noauto`, mọi join thành sort-merge. Sort-merge join thường cần shuffle cả hai phía.

Bảng: Toán tử join trong kế hoạch thực thi cuối (mỗi lần chạy, 27 truy vấn SQL) {#tbl:join-ke-hoach}

| Cấu hình | SortMergeJoin | BroadcastHashJoin | Giống nhau ở cả 3 lần |
|---|---|---|---|
| auto | 4 | 6 | Có |
| broadcast | 4 | 6 | Có |
| shuffle_noauto | 10 | 0 | Có |

Nguồn: results/metrics/join_strategy/plan_check.csv (đếm từ event log)

![Thời gian ETL theo chiến lược join](results/figures/join_strategy/join_strategy.png){#fig:join-strategy}

Nguồn: results/metrics/join_strategy/summary.csv

Trên @fig:join-strategy, ba giai đoạn chậm thêm khi ép sort-merge là `orders`, `order_items` và `aggregates` (`aggregates` tăng từ 9,71 lên 12,58 giây). Chênh lệch 3,7 giây giữa `auto` và `broadcast` chủ yếu do lần r2 của `auto` (86,18 giây, `order_items` 31,29 giây). `plan_check.csv` chỉ ghi số đếm, không ghi cặp bảng, nên nhóm suy luận bốn sort-merge join còn lại ở `auto` là các join mà cả hai phía đều vượt ngưỡng broadcast mặc định.

## D.12 Thí nghiệm (e): cấu hình, hình và lập luận

Cấu hình `auto` là cấu hình mặc định của ETL. Cấu hình `shuffle` (biến thể ép shuffle, cài đặt chủ động) tắt broadcast, dùng 64 phân vùng shuffle, ngưỡng phân vùng lệch 4 MiB, kích thước phân vùng tư vấn 2 MiB. Lý do chọn tham số ở mục B.6. Căn cứ là phép đo ở @tbl:partition-stats. Ở 64 phân vùng, phân vùng lớn nhất của bộ lệch gấp 10,54 lần trung vị và có 9 phân vùng vượt 5 lần trung vị. Ở 8 phân vùng, tỉ số này chỉ là 1,77 và không phân vùng nào vượt. Ở bộ cân bằng, tỉ số là 1,01 (8 phân vùng) và 1,18 (64 phân vùng).

![Thời gian ETL theo 8 cấu hình và theo giai đoạn](results/figures/skew/skew.png){#fig:skew}

Nguồn: results/metrics/skew/summary.csv

@fig:skew vẽ thời gian của 8 cấu hình ở @tbl:skew-cau-hinh, tách theo giai đoạn. Tổng số nút sort-merge của `skew_shuffle_aqe` vẫn là 10 như các cấu hình ép shuffle khác (7 thường, 3 có tách lệch). Bộ cân bằng không kích hoạt tách lệch, đúng như ngưỡng 4 MiB nhóm đã chọn.

Khi tắt AQE, stage đọc shuffle `order_items` ở lần r1 có 64 task. Khi bật AQE có 104 task, gồm các task tách ra từ phân vùng lệch. Số task khớp phép tính 64 − 9 + 49 = 104, tức 9 phân vùng vượt ngưỡng được thay bằng 49 phần tách (tính của nhóm từ @tbl:partition-stats và @fig:ss-aqe-plan). Chênh lệch dưới một giây mỗi task không đủ để thấy trên tổng thời gian khoảng 100 giây.

Phần giảm khi bật AQE ở biến thể ép shuffle tập trung ở `aggregates` (khoảng 23 xuống 13 giây) và `dimensions` (khoảng 11 xuống 6,5 giây). Với 64 phân vùng cho dữ liệu chỉ vài trăm MB, phần lớn phân vùng rất nhỏ, AQE gộp chúng lại nên giảm số task và số tệp nhỏ phải ghi (nhận định của nhóm).

Một phần chênh lệch 10,18 giây giữa `skew_auto_aqe` và `skew_auto_noaqe` (84,07 so với 73,89) nằm ở các giai đoạn không phụ thuộc khoá lệch (`dimensions`, `orders`), nên nhóm cho rằng có phần do nhiễu. Tuy vậy cả hai bộ đều cho `order_items` chậm hơn khi bật AQE ở `auto` (26,63 so với 22,58 giây ở bộ cân bằng, 28,85 so với 22,17 giây ở bộ lệch).

## D.13 Thí nghiệm (f): cấu hình, bảng, hình và lập luận

Cấu hình: orders_5m, `DataFrame.cache()`, 2 worker, mỗi chế độ 3 lần xen kẽ. q1 doanh thu theo ngày, q2 theo trạng thái, q3 top 10 sản phẩm theo số lượng, q4 số dòng theo phương thức thanh toán, q5 giá trị trung bình theo `line_no`.

Bảng: Phân tích hoà vốn của cache {#tbl:cache-hoa-von}

| Đại lượng | Giá trị |
|---|---|
| u: thời gian trung bình một truy vấn, không cache | 3,15 s |
| c: thời gian trung bình một truy vấn, có cache | 0,58 s |
| M: thời gian materialize | 8,03 s |
| Số truy vấn hoà vốn n* = M / (u − c) | 3,12 (làm tròn lên 4) |
| Tiết kiệm ở K = 5 | 4,85 s |

Nguồn: results/metrics/cache/break_even.csv

![Thời gian từng truy vấn và tổng thời gian khi không cache và có cache](results/figures/cache/cache.png){#fig:cache}

Nguồn: results/metrics/cache/summary.csv

@fig:cache vẽ thời gian từng truy vấn và tổng thời gian. Có cache, truy vấn đọc từ bộ nhớ đệm thay vì đọc lại Parquet trên MinIO và làm lại sort-merge join. Cả 3 lần chạy đều cache đủ 8/8 phân vùng (9.024.635 dòng) ở mức "Disk Memory Deserialized 1x Replicated", là mức mặc định MEMORY_AND_DISK_DESER của `DataFrame.cache()` [@pyspark-cache]. Số liệu bộ nhớ và đĩa (r1–r3) lấy từ `storage_after_materialize` trong `results/metrics/cache/runs/cache/r<k>/query_bench.json`. Với heap 1 GB, vùng nhớ lưu trữ không chứa hết DataFrame, phần dư ghi xuống đĩa cục bộ của worker, đọc lại vẫn rẻ hơn đọc lại Parquet và join lại (nhận định của nhóm, suy từ số đo ở @tbl:cache-tong).

Khi không cache, mỗi truy vấn chỉ đọc các cột cần thiết. Khi cache, DataFrame giữ toàn bộ cột. Kết quả ở mục 6.9 vì vậy đã tính đến chi phí giữ cột thừa.

## D.14 Thí nghiệm (g): cấu hình, hình và môi trường

Cấu hình: orders_500k và orders_1m, mỗi bộ 3 lần, mỗi lần một tiến trình Python mới. Thời gian Spark lấy từ thí nghiệm (a).

![Thời gian xử lý của Pandas (host) và Spark (cụm Docker)](results/figures/pandas_baseline/pandas_vs_spark.png){#fig:pandas}

Nguồn: results/metrics/pandas_baseline/comparison_spark.csv

@fig:pandas vẽ lại @tbl:pandas-spark. Pandas không có chi phí khởi động JVM, đăng ký ứng dụng và lập lịch task, trong khi Spark vẫn trả chi phí lập lịch trong từng giai đoạn. Ở bộ 500k và 1M, chi phí cố định mỗi giai đoạn có vẻ chi phối thời gian Spark (nhận định của nhóm, mục 6.4). Khi bộ nhớ đỉnh tăng tới mức ngoại suy khoảng 8 GB, giới hạn một máy của Pandas trở thành vấn đề (ngoại suy, chưa đo).

<!-- VERIFY
- D.1: results/metrics/scale_data/summary.csv (stage_*).
- D.2: results/metrics/format_compare/sizes.csv; byte/dòng = raw_bytes/raw_rows, curated_bytes/curated_rows (results/samples/orders_5m/summary.csv); products 203.748/20.000 = 10,2 và 165.869/20.000 = 8,3; tổng 1.089.695.264 và 226.238.030 byte, tỉ lệ 4,82.
- D.3: results/metrics/skew/partition_stats_summary.csv.
- D.4: results/metrics/cache/summary.csv; tỉ lệ từng truy vấn do người viết chia.
- D.5: results/metrics/pandas_baseline/summary.csv.
- D.6: CPU, RAM 15,76 GB, ổ, Docker engine 29.9.2, MinIO RELEASE.2026-10-23T20-06-51Z: results/logs/environment.txt. Tính hợp lệ: Pandas không kiểm tra cụm (workers_expected, cluster_before null: pandas_baseline/runs/orders_1m/r1/run_record.json; src/experiments/common/runner.py); raw_rows_mismatch chỉ xét kind etl (src/experiments/common/analysis.py) (verify-round2 A3). CV truy vấn (c), (f): verify-round1 A3.
- D.7: 1,9 = 376.230/199.956.
- D.8: scale_data/summary.csv; 273.766 là trung bình theo lần, 271.340 = 20.931.505/77,141667 (verify-round1 mục C); 23–24 s = wall − processing; order_items r3 35,273: scale_data/runs.csv; 4,01 và 3,88: verify-round1 A4; 4,15 = 87,745/21,144 (verify-round2 F1). Thông lượng 5M theo lần r1 289.581, r2 293.167, r3 238.549: verify-round2 B2.
- D.9: thời gian khối w1 23:28–23:35, w2 23:35–23:41: scale_workers/runs.csv. "Đổi cả số lõi lẫn bộ nhớ": viết lại câu "không chỉ đổi số lõi" của mục 6.5 cũ.
- D.10: sizes.csv; q2 các lần khác 0,44–0,70: runs.csv. 5,46 / 1,75: summary_by_order.csv. 3.060.980 / 2.880.698: runs.csv cột result.
- D.11: auto r2 86,178, order_items 31,292: join_strategy/runs.csv. Bốn sort-merge còn lại: suy luận của người viết (plan_check chỉ có số đếm).
- D.12: partition_stats_summary.csv; aggregates 23,38→12,90 và 22,16→13,11; dimensions 10,77→6,63 và 11,41→6,36; auto order_items 26,63/22,58 và 28,85/22,17 (verify-round1 mục C). 104 = 64 − 9 + 49: verify-round1 mục C; ảnh 07 và 10. 64 và 104 task: results/logs/screenshots/README.md và chính ảnh.
- D.13: cache/break_even.csv; 8/8 phân vùng, 9.024.635 dòng: cache/runs/cache/r1..r3/query_bench.json (verify-round1 mục C). Mức mặc định của DataFrame.cache() là MEMORY_AND_DISK_DESER: PySpark 4.0.0 (verify-round1 mục C).
- D.14: khác biệt môi trường: src/experiments/pandas_baseline/README.md. "Có vẻ chi phối" là nhận định (vòng 3 A6).
- D.6 vòng 3 B3: đối chiếu số dòng thô với manifest do src/experiments/common/analysis.py (run_flags, cờ raw_rows_mismatch) làm khi phân tích; runner.py chỉ ghi raw_rows_manifest. 49 số đếm do job Pandas tự đối chiếu (cột all_match).
-->
