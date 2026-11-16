# Chương 6. Thực nghiệm và đánh giá

Số liệu lấy từ các tệp trong `results/` và làm tròn hai chữ số thập phân khi trình bày, số gốc nằm trong tệp nguồn ghi dưới mỗi bảng. Tỉ số do nhóm tự chia ghi rõ là "tính từ" tệp nguồn. Cấu hình chi tiết, bảng và hình phụ, lập luận từng bước của bảy thí nghiệm (a) đến (g) nằm ở Phụ lục D.

## 6.1 Môi trường thí nghiệm

Bộ đo chính thức chạy ngày 2026-11-07, từ 22:00:54 đến 23:41:37 (giờ Việt Nam), trên máy và cụm mô tả ở mục 3.8, với Spark 4.0.0, mã nguồn ở commit `8164042` và dữ liệu mô phỏng seed 42. Cả 69 lần chạy (63 Spark + 6 Pandas) có trạng thái `ok`, không lần nào bị loại. Bảng đầy đủ ở @tbl:moi-truong (Phụ lục D).

RAM của host chịu áp lực trong lúc đo. Trước lần chạy đầu tiên, host còn trống 4.168 MiB (mức dùng bộ nhớ 74%). Ngay sau lần đó, RAM trống xuống 351 MiB (97%), phù hợp với việc máy ảo WSL2 chiếm dần đến giới hạn 6 GB. Trước các lần chạy Spark còn lại, RAM trống chủ yếu khoảng 0,8 đến 1,1 GB, thấp nhất 400 MiB. Đây là một nguồn nhiễu có thể có (giả thuyết, chưa đo trực tiếp ảnh hưởng). Nguồn: cột `host_available_mib` trong các `runs.csv`, `host_before`, `host_after` trong `results/metrics/scale_data/runs/orders_500k/r1/run_record.json`.

Trong 69 bản ghi, 57 bản ghi có cờ `dirty` (cây mã có thay đổi chưa commit lúc chạy). `dirty_paths` của chúng chỉ gồm hai tệp bộ nhớ của agent đo trong `.claude/agent-memory/benchmark-analyst/`, agent ghi hai tệp này trong lúc bộ đo chạy, còn `src/` và `tests/` không đổi. Vì vậy cờ này không ảnh hưởng đến mã được đo. 12 lần chạy đầu tiên (thí nghiệm (a)) không có cờ này.

## 6.2 Phương pháp đo

Chỉ số chính là `processing_seconds_total`, tổng thời gian năm giai đoạn ETL do job tự đo, không gồm khởi động container và JVM, đăng ký executor và bước thống kê sau xử lý. Với (c) và (f), chỉ số là thời gian từng truy vấn, đo quanh lệnh `collect()` sau một bước khởi động không tính giờ. Mỗi cấu hình chạy 3 lần, bảng ghi trung bình ± độ lệch chuẩn mẫu, và nhóm đánh giá độ ổn định bằng hệ số biến thiên CV = độ lệch chuẩn / trung bình. Tiêu chí hợp lệ của từng lần chạy ở mục D.6.

Với `processing_seconds_total` của các thí nghiệm ETL, CV vượt 10% ở hai nhóm: `orders_5m` của (a) (11,92%) và `balanced_shuffle_noaqe` của (e) (12,70%). Các truy vấn ngắn của (c) và (f) có bảy nhóm vượt 10%, liệt kê ở mục D.6. Với n = 3, nhóm coi chênh lệch nhỏ hơn khoảng một độ lệch chuẩn là chưa phân biệt được với nhiễu.

## 6.3 Chất lượng dữ liệu trước và sau xử lý

Bảng: Số dòng trước và sau xử lý của bộ orders_5m, kèm số dòng cách ly theo lý do {#tbl:chat-luong-5m}

| Bảng | Thô | Sạch | Cách ly | Trùng đã bỏ | Lý do cách ly (`reject_reason`: số dòng) |
|---|---|---|---|---|---|
| customers | 510.000 | 500.000 | 0 | 10.000 | Không có |
| products | 20.000 | 20.000 | 0 | 0 | Không có |
| orders | 5.100.000 | 4.800.044 | 199.956 | 100.000 | `null_customer_id`: 99.579; `orphan_customer_id`: 100.377 |
| order_items | 10.201.505 | 9.024.635 | 976.840 | 200.030 | `null_unit_price`: 200.700; `non_positive_quantity`: 99.603; `non_positive_price`: 99.817; `orphan_product_id`: 200.490; `no_clean_order`: 376.230 |
| web_events | 5.100.000 | 4.900.063 | 99.937 | 100.000 | `null_customer_id`: 99.937 |
| **Tổng** | **20.931.505** | **19.244.742** | **1.276.733** | **410.030** | |

Nguồn: results/samples/orders_5m/summary.csv (đếm trực tiếp trên MinIO, cột matches_metrics = yes), results/samples/orders_5m/quarantine_by_reason.csv; khớp results/metrics/orders_5m.json; dòng Tổng do nhóm cộng

Job giữ lại khoảng 91,9% số dòng thô (tính từ @tbl:chat-luong-5m). Tổng thô bằng đúng tổng sạch + cách ly + trùng, không dòng nào mất mà không rõ lý do. Số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp số lỗi bộ sinh đã chèn ở cả năm bộ dữ liệu (`docs/design/etl.md`), và số đếm giống hệt nhau giữa mọi lần chạy của cùng bộ trong bộ thí nghiệm (`counts_consistent` = True).

`no_clean_order` chiếm 376.230 dòng, tức 38,5% số dòng hàng bị cách ly (tính từ @tbl:chat-luong-5m), là hệ quả dây chuyền của 199.956 đơn bị cách ly. Không dòng nào bị cách ly vì `invalid_order_date` hay `invalid_event_time`, vì job nhận diện và chuẩn hoá mọi ngày và thời gian sai định dạng. Ví dụ trước và sau ở chương 7, nhận xét chi tiết ở mục D.7.

## 6.4 Thí nghiệm (a): mở rộng theo kích thước dữ liệu

Thí nghiệm (a) đo thời gian ETL khi số đơn tăng từ 0,5 triệu lên 5 triệu, ở cấu hình mặc định. Giả thuyết của nhóm là thời gian tăng chậm hơn dữ liệu ở bộ nhỏ do chi phí cố định (lập lịch, khởi tạo, ghi nhiều tệp nhỏ), và thông lượng tăng dần rồi bão hoà.

![Thời gian xử lý theo số dòng thô (trung bình ± độ lệch chuẩn, n = 3)](results/figures/scale_data/processing_time_vs_rows.png){#fig:scale-thoi-gian}

Nguồn: results/metrics/scale_data/summary.csv

Phần về thời gian phù hợp giả thuyết. Dữ liệu tăng 10 lần, thời gian tăng 3,52 lần, từ 21,90 ± 0,74 giây ở orders_500k lên 77,14 ± 9,19 giây ở orders_5m (@fig:scale-thoi-gian, @tbl:scale-tong ở Phụ lục D). Thông lượng tăng từ khoảng 96 nghìn lên 274 nghìn dòng/giây. Từ 2,5M lên 5M, dữ liệu gấp đôi và thời gian gấp 1,82 lần (tính từ summary), nhưng con số này phụ thuộc lần r3 chậm bất thường, nên chưa đủ căn cứ để khẳng định thông lượng đã bão hoà.

Chi phí cố định thấy rõ ở giai đoạn `dimensions`. Bảng `customers` tăng 10 lần nhưng thời gian chỉ tăng từ 4,47 lên 6,29 giây (@tbl:scale-giai-doan-chi-tiet, Phụ lục D). Ở bộ nhỏ, mỗi giai đoạn tốn khoảng 4 đến 5 giây dù dữ liệu rất ít, phần lớn là chi phí lập lịch stage, ghi và đọc lại Parquet trên MinIO (nhận định của nhóm). `order_items`, bảng lớn nhất, tăng nhanh nhất, từ 4,29 lên 27,34 giây, gấp 6,4 lần, và chiếm nhiều thời gian nhất ở bộ 5M.

CV 11,92% của bộ 5M đến từ lần r3 (87,75 so với 71,40 và 72,28 giây). Lần này không có cờ bất thường nào, nguyên nhân chưa xác định. Lấy chính lần chậm nhất đó so với bộ 500k, tỉ lệ thời gian vẫn chỉ khoảng 4 lần cho 10 lần dữ liệu (phép tính ở mục D.8).

## 6.5 Thí nghiệm (b): mở rộng theo số worker

Trên orders_5m, thí nghiệm (b) tính speedup S = T(1 worker) / T(2 worker) và efficiency E = S / 2 (slide chương 2, tr. 21 [@slide-c2]). Cấu hình `w1` dừng `spark-worker-2`, `w2` dùng đủ 2 worker, chạy theo khối 3 lần `w1` rồi 3 lần `w2`. Giả thuyết: 1 < S < 2 vì có phần tuần tự (driver, ghi metadata, đọc từ MinIO dùng chung) và chi phí shuffle.

Bảng: Thời gian và speedup khi dùng 1 và 2 worker (orders_5m) {#tbl:workers}

| Chỉ số | 1 worker (s) | 2 worker (s) | Speedup S | Efficiency E |
|---|---|---|---|---|
| Thời gian xử lý | 105,85 ± 1,73 | 82,21 ± 6,39 | 1,29 | 0,64 |
| dimensions | 5,24 | 6,51 | 0,81 | 0,40 |
| orders | 22,28 | 15,84 | 1,41 | 0,70 |
| order_items | 37,46 | 28,09 | 1,33 | 0,67 |
| web_events | 28,01 | 21,66 | 1,29 | 0,65 |
| aggregates | 12,86 | 10,11 | 1,27 | 0,64 |
| Thời gian cả lệnh (wall) | 128,85 | 110,66 | 1,16 | 0,58 |

Nguồn: results/metrics/scale_workers/summary.csv (cột mean, speedup, efficiency)

Speedup tổng là 1,29 và efficiency 0,64, tức gấp đôi tài nguyên chỉ giảm khoảng 22% thời gian xử lý. Kết quả nằm trong khoảng giả thuyết nhưng gần 1 hơn 2. Bốn giai đoạn có xử lý dữ liệu lớn đạt S từ 1,27 đến 1,41, riêng `dimensions` chậm đi khi có 2 worker (S = 0,81). Giai đoạn này chỉ xử lý 510 nghìn khách hàng và 20 nghìn sản phẩm, nên chi phí phối hợp hai executor có thể lớn hơn phần lợi do song song (nhận định của nhóm, chưa kiểm chứng bằng event log).

Nguyên nhân của speedup thấp phần lớn còn là suy đoán vì đồ án không đo trực tiếp (@tbl:speedup-bang-chung, mục 8.2). Ước lượng thô theo định luật Amdahl (slide chương 2, tr. 22 [@slide-c2]) cho phần song song hoá hiệu dụng p ≈ 0,45 (nhận định của nhóm). Không nên hiểu con số này là 55% mã chạy tuần tự, vì nó gộp cả các chi phí không giảm khi thêm worker (mục D.9). Phép so sánh cũng nhân đôi tổng heap executor (1 lên 2 GB), nên S có thể gộp cả hiệu ứng bộ nhớ. Đồ án chưa tách được hai hiệu ứng này (mục 8.2).

Do chạy theo khối, nhiễu theo thời gian giữa `w1` và `w2` không được cân bằng như các thí nghiệm xen kẽ. Cùng cấu hình 2 worker mặc định trên orders_5m, bốn thí nghiệm cho trung bình 77,14 giây ((a)), 77,16 giây ((e), `balanced_auto_aqe`), 78,65 giây ((d), `auto`) và 82,21 giây ((b)), chênh nhau khoảng 7%. Speedup 1,29 vì vậy có sai số không nhỏ. Dùng 77,14 giây làm mẫu số thì S là khoảng 1,37 (tính từ hai summary).

## 6.6 Thí nghiệm (c): CSV/JSON thô so với Parquet

Ba truy vấn Spark chạy trên dữ liệu thô (CSV, JSON lines) và trên Parquet đã làm sạch của orders_5m, thí nghiệm (c) so thời gian và dung lượng. Giả thuyết là Parquet nhanh hơn rõ ở truy vấn dùng ít cột nhờ đọc theo cột và đẩy điều kiện lọc xuống, và nhỏ hơn nhờ nén theo cột (slide chương 4, tr. 46 [@slide-c4], slide chương 5, tr. 44 [@slide-c5]).

Bảng: Thời gian truy vấn trên dữ liệu thô và Parquet (orders_5m, n = 6) {#tbl:format-thoi-gian}

| Truy vấn | Thô (s) | Parquet (s) | Thô / Parquet |
|---|---|---|---|
| q1 lọc và đếm `orders` | 1,61 ± 0,27 | 0,76 ± 0,15 | 2,13 |
| q2 đếm `web_events` theo loại | 2,38 ± 0,16 | 0,87 ± 0,80 | 2,74 |
| q3 join và tổng doanh thu theo ngày | 7,51 ± 0,60 | 3,39 ± 0,71 | 2,22 |

Nguồn: results/metrics/format_compare/summary.csv (cột mean, std, ratio_raw_over_curated)

Parquet nhanh hơn 2,1 đến 2,7 lần ở cả ba truy vấn. Tỉ lệ này gộp cả hiệu ứng số dòng, vì các bảng thô tham gia truy vấn nhiều dòng hơn bảng sạch khoảng 4 đến 13% (tính từ @tbl:chat-luong-5m). q2 có tỉ lệ cao nhất, theo nhận định của nhóm vì với JSON lines, Spark phải phân tích cú pháp cả dòng dù chỉ cần cột `event_type`. Kết quả q2 kém ổn định: độ lệch chuẩn trên Parquet là 0,80 giây vì một lần đo 2,48 giây, và tỉ lệ đổi theo thứ tự chạy (mục D.10).

Về dung lượng, tổng thô là 1.089,70 MB, Parquet curated 226,24 MB (@tbl:format-kich-thuoc, Phụ lục D). Parquet nhỏ hơn 3,6 đến 5,9 lần ở bốn bảng chuyển từ CSV/JSON. Tỉ lệ này gộp nén theo cột với việc bảng curated ít dòng hơn, nhưng quy về byte trên mỗi dòng Parquet vẫn nhỏ hơn khoảng 3,2 đến 5,7 lần (tính từ @tbl:format-byte-dong, Phụ lục D), nên phần lớn chênh lệch đến từ định dạng. `products` vốn đã là Parquet nên tỉ lệ chỉ 1,23.

Truy vấn thẳng trên dữ liệu thô cho doanh thu q3 là 767.333.901,89, cao hơn khoảng 9,6% so với 700.264.598,73 trên dữ liệu sạch (cột `result` trong `runs.csv`), vì dữ liệu thô còn bản ghi trùng và lỗi. Con số này minh hoạ giá trị của bước làm sạch ngoài lợi ích về tốc độ.

## 6.7 Thí nghiệm (d): broadcast join so với sort-merge join

Thí nghiệm (d) so thời gian ETL trên orders_5m khi các join với bảng nhỏ dùng broadcast hash join hay sort-merge join [@spark-sql-tuning]. `auto` để Spark tự chọn theo ngưỡng 10 MB, `broadcast` gợi ý broadcast cho phía nhỏ, `shuffle_noauto` gợi ý `merge` và tắt broadcast tự động. Nhóm đặt giả thuyết broadcast nhanh hơn vì có thể tránh shuffle bảng lớn, dù bảng nhỏ vẫn truyền qua mạng (slide chương 5, tr. 51 [@slide-c5]).

Bảng: Thời gian ETL theo chiến lược join (orders_5m) {#tbl:join}

| Cấu hình | Thời gian xử lý (s) | Min–max (s) | orders (s) | order_items (s) | web_events (s) | aggregates (s) |
|---|---|---|---|---|---|---|
| auto | 78,65 ± 6,63 | 73,67–86,18 | 15,42 | 26,32 | 20,19 | 9,69 |
| broadcast | 74,92 ± 1,89 | 73,65–77,10 | 15,95 | 23,68 | 19,05 | 9,71 |
| shuffle_noauto | 84,00 ± 2,19 | 82,25–86,45 | 17,66 | 28,08 | 19,10 | 12,58 |

Nguồn: results/metrics/join_strategy/summary.csv

Ép sort-merge join cho mọi phép join làm job chậm hơn khoảng 7–12%: 84,00 giây so với 74,92 giây của `broadcast` (khoảng 12%) và 78,65 giây của `auto` (khoảng 7%, trong mức nhiễu). Lấy trung bình chung của hai cấu hình kia thì chênh lệch khoảng 9% (tính từ summary). Phần chậm thêm nằm ở ba giai đoạn có join. `web_events` không có join và gần như bằng nhau ở cả ba cấu hình (19,05 đến 20,19 giây), đóng vai trò đối chứng cho mức nhiễu.

Event log xác nhận cấu hình có hiệu lực: `shuffle_noauto` có 10 `SortMergeJoin`, không còn `BroadcastHashJoin` nào (@tbl:join-ke-hoach, Phụ lục D). `auto` và `broadcast` có cùng số toán tử join (4 sort-merge, 6 broadcast), nên nhóm suy luận gợi ý broadcast không đổi kế hoạch vì Spark đã tự broadcast các bảng nhỏ dưới ngưỡng 10 MB. Chênh lệch 3,7 giây giữa hai cấu hình này vì vậy được xem là nhiễu, chủ yếu do lần r2 của `auto` (mục D.11).

## 6.8 Thí nghiệm (e): lệch khoá, cách join và AQE

Thí nghiệm (e) so thời gian ETL trên bộ cân bằng (orders_5m) và bộ lệch khoá (orders_5m_skew), với hai cách join và AQE bật hoặc tắt, tổng 8 cấu hình. Giả thuyết có ba vế. Ở `auto`, chênh lệch nhỏ vì join theo `product_id` là broadcast. Ở biến thể ép shuffle, bộ lệch chậm hơn khi tắt AQE (vài task phải xử lý phần lớn dữ liệu). Bật AQE sẽ thu hẹp chênh lệch nhờ tách phân vùng lệch. Nhóm chủ động đặt cho biến thể ép shuffle 64 phân vùng shuffle, ngưỡng phân vùng lệch 4 MiB và kích thước tư vấn 2 MiB để AQE kích hoạt được (mục 4.6, căn cứ ở mục B.6 và D.12).

Bảng: Thời gian ETL theo 8 cấu hình lệch khoá × cách join × AQE {#tbl:skew-cau-hinh}

| Cấu hình | Thời gian xử lý (s) | Lệch / cân bằng | aggregates (s) | SMJ | BHJ | SMJ có tách lệch |
|---|---|---|---|---|---|---|
| balanced_auto_aqe | 77,16 ± 5,35 | | 9,42 | 4 | 6 | 0 |
| skew_auto_aqe | 84,07 ± 2,85 | 1,09 | 9,50 | 4 | 6 | 0 |
| balanced_auto_noaqe | 75,36 ± 7,24 | | 10,46 | 4 | 6 | 0 |
| skew_auto_noaqe | 73,89 ± 4,07 | 0,98 | 9,91 | 4 | 6 | 0 |
| balanced_shuffle_aqe | 111,30 ± 10,00 | | 12,90 | 10 | 0 | 0 |
| skew_shuffle_aqe | 106,52 ± 7,21 | 0,96 | 13,11 | 7 | 0 | 3 |
| balanced_shuffle_noaqe | 128,44 ± 16,31 | | 23,38 | 10 | 0 | 0 |
| skew_shuffle_noaqe | 122,22 ± 9,53 | 0,95 | 22,16 | 10 | 0 | 0 |

Nguồn: results/metrics/skew/summary.csv (processing_seconds_total, ratio_vs_balanced, stage_aggregates); results/metrics/skew/plan_check.csv (SMJ = SortMergeJoin, BHJ = BroadcastHashJoin, cột SortMergeJoin(skew=true); giống nhau ở cả 3 lần của mỗi cấu hình)

Kết quả trái giả thuyết ở biến thể ép shuffle: bộ lệch không chậm hơn rõ rệt so với bộ cân bằng. Tỉ lệ lệch/cân bằng nằm trong khoảng 0,95 đến 1,09 ở cả 4 cặp, và cặp duy nhất trên 1 là `auto` bật AQE. Kể cả khi ép shuffle và tắt AQE, nơi giả thuyết dự đoán chênh lệch lớn nhất, bộ lệch còn nhanh hơn một chút (122,22 so với 128,44 giây, chênh lệch nhỏ hơn độ lệch chuẩn). Vế giả thuyết ở `auto` không bị bác.

AQE có tách join lệch như thiết kế. Chỉ `skew_shuffle_aqe` có `SortMergeJoin(skew=true)`, 3 nút trong kế hoạch cuối ở cả 3 lần chạy, còn bộ cân bằng với cùng tham số không kích hoạt. Nút `AQEShuffleRead` ghi 49 lần tách phân vùng lệch ở bước ghi `order_items` sạch (@fig:ss-aqe-plan, Phụ lục E). Việc tách có san phẳng task nhưng lợi ích tuyệt đối rất nhỏ. Ở lần chạy r1, dữ liệu đọc lớn nhất của một task giảm từ 15,5 MiB (trung vị 1,5 MiB) xuống 1,9 MiB, task lâu nhất giảm từ 0,5 xuống 0,2 giây (@fig:ss-noaqe-tasks, @fig:ss-aqe-tasks, mục 7.4). Thời gian trung bình của `order_items` ở bộ lệch gần như không đổi khi bật AQE (34,40 so với 34,85 giây).

Ở biến thể ép shuffle, bật AQE giảm thời gian khoảng 13% ở cả hai bộ (128,44 xuống 111,30 giây, 122,22 xuống 106,52 giây, tính từ summary), nhưng phần giảm giống nhau ở bộ cân bằng, nơi không phân vùng nào bị tách. Nhóm cho rằng lợi ích này đến từ việc AQE gộp phân vùng nhỏ, phù hợp với mô tả tính năng gộp phân vùng sau shuffle của AQE [@spark-sql-tuning] (nhận định của nhóm, mục D.12). Ở `auto`, bật AQE không nhanh hơn (77,16 so với 75,36 giây và 84,07 so với 73,89 giây).

Ở `auto`, cấu hình thực tế của job, `products` được broadcast (@fig:ss-auto-plan, Phụ lục E) nên khoá lệch không đi qua shuffle. Tỉ lệ 1,09 của cặp `auto` bật AQE là cao nhất, nhưng `dimensions` và `orders`, hai giai đoạn không phụ thuộc khoá lệch, cũng chậm hơn khoảng 13%, nên nhóm cho rằng phần lớn là nhiễu, với n = 3 chưa kết luận được. `skew_auto_aqe` chậm hơn `skew_auto_noaqe` 10,18 giây dù cùng số toán tử join. Đồ án chưa kết luận được nguyên nhân và chưa khẳng định đây là ảnh hưởng thật của AQE, cần đọc event log để kiểm tra (mục D.12).

Ở quy mô 5 triệu đơn với 50% lượt chọn dồn vào 10 sản phẩm, lệch khoá không trở thành nút cổ chai trên cụm này. Muốn thấy tác động rõ của skew cần dữ liệu lớn hơn nhiều so với bộ nhớ executor, hoặc mức lệch cao hơn. Đó là hướng mở rộng, không phải kết quả đã đo.

## 6.9 Thí nghiệm (f): cache DataFrame dùng lại

K = 5 truy vấn tổng hợp chạy trên cùng một DataFrame `order_items ⋈ orders` đọc từ Parquet curated, không cache và có cache. Nhóm kỳ vọng không cache thì mỗi truy vấn đọc lại Parquet và làm lại join, còn có cache thì action đầu tiên materialize dữ liệu và các action sau có thể dùng lại thay vì chạy lại lineage (slide chương 5, tr. 31, 32 [@slide-c5]). Việc lần materialize tốn thêm thời gian và có lợi khi K đủ lớn là suy luận của nhóm.

Bảng: Tổng thời gian truy vấn không cache và có cache (orders_5m, n = 3) {#tbl:cache-tong}

| Bước | Không cache (s) | Có cache (s) | Không cache / có cache |
|---|---|---|---|
| Materialize (`cache()` + `count()`) | | 8,03 ± 0,66 | |
| Tổng 5 truy vấn | 15,75 ± 1,01 | 2,88 ± 0,09 | 5,48 |
| Tổng gồm materialize | 15,75 ± 1,01 | 10,90 ± 0,59 | 1,44 |

Nguồn: results/metrics/cache/summary.csv; cột tỉ lệ do nhóm tính

Có cache, mỗi truy vấn nhanh hơn 4,4 đến 8,3 lần (@tbl:cache-truy-van, Phụ lục D). Kế hoạch thực thi sau truy vấn đầu tiên có `InMemoryTableScan`, xác nhận job đọc từ cache (`results/metrics/cache/runs/cache/r1/query_bench.json`). Chi phí materialize 8,03 giây được bù sau khoảng 3,1 truy vấn, tức từ truy vấn thứ 4 trở đi (@tbl:cache-hoa-von, Phụ lục D). Với 5 truy vấn, cache tiết kiệm 4,85 giây (khoảng 31% tổng thời gian). Với 1 hoặc 2 truy vấn, cache sẽ làm chậm hơn, nên theo nhận định của nhóm chỉ nên cache dữ liệu được dùng lại.

Cache tràn một phần ra đĩa mà vẫn có lợi. Dữ liệu cache chiếm khoảng 216–252 MiB trong bộ nhớ và 20–41 MiB trên đĩa ở heap mặc định 1 GB (mục D.13).

## 6.10 Thí nghiệm (g): baseline Pandas một máy

Thí nghiệm (g) viết lại cùng luật làm sạch và ba bảng tổng hợp bằng Pandas, đo theo cùng năm giai đoạn trên orders_500k và orders_1m. Mỗi lần chạy Pandas đối chiếu 49 số đếm với manifest và với metrics của Spark, cả 6 lần đều khớp toàn bộ. Giả thuyết: ở kích thước nhỏ, Pandas có thể nhanh hơn Spark vì không có chi phí phân tán.

Bảng: Thời gian xử lý của Pandas và Spark {#tbl:pandas-spark}

| Bộ | Pandas (s) | Spark (s) | Spark / Pandas | Bộ nhớ đỉnh Pandas (MiB) |
|---|---|---|---|---|
| orders_500k | 3,62 ± 0,27 | 21,90 ± 0,74 | 6,05 | 906 |
| orders_1m | 7,06 ± 0,34 | 27,94 ± 0,36 | 3,95 | 1.682 |

Nguồn: results/metrics/pandas_baseline/comparison_spark.csv; bộ nhớ đỉnh (peak_rss_mib) từ results/metrics/pandas_baseline/summary.csv

Pandas nhanh hơn Spark 6,1 lần ở bộ 500k và 4,0 lần ở bộ 1M, phù hợp giả thuyết. Hai bên chạy trong môi trường khác nhau nên phép so sánh không hoàn toàn công bằng. Pandas chạy trực tiếp trên host Windows, không bị giới hạn 6 GB của WSL2, đọc đĩa cục bộ, còn Spark đọc MinIO qua mạng Docker. Ngược lại, Pandas dùng một lõi cho phần lớn thao tác (theo `src/experiments/pandas_baseline/README.md`, không đo mức dùng CPU), Spark dùng 4 lõi executor (mục D.14).

Bộ 500k và 1M quá nhỏ để kết luận về khả năng mở rộng. Khoảng cách đang thu hẹp: dữ liệu gấp đôi thì thời gian Pandas tăng 1,95 lần, Spark chỉ tăng 1,28 lần (tính từ bảng). Bộ nhớ đỉnh của Pandas tăng gần tỉ lệ với dữ liệu (906 lên 1.682 MiB). Nếu tiếp tục tăng tuyến tính, bộ 5M sẽ cần khoảng 8 GB RAM cho một tiến trình (ngoại suy thô của nhóm, chưa đo). Đồ án không chạy Pandas trên 2,5M và 5M theo phạm vi đã chốt, nên không có số đo kiểm chứng điểm giao nhau.

## 6.11 Tổng hợp kết quả

Bảng: Tóm tắt kết quả bảy thí nghiệm {#tbl:tong-hop}

| Thí nghiệm | Kết quả chính | So với giả thuyết |
|---|---|---|
| (a) Kích thước dữ liệu | Dữ liệu × 10, thời gian × 3,52; thông lượng 96 nghìn lên 274 nghìn dòng/s | Đúng về thời gian tăng chậm hơn dữ liệu; chưa xác nhận được bão hoà |
| (b) Số worker | S = 1,29, E = 0,64; `dimensions` chậm đi khi có 2 worker | Đúng (1 < S < 2), nhưng S thấp, gần 1 hơn 2 |
| (c) Định dạng | Parquet nhanh hơn 2,1–2,7 lần, nhỏ hơn 3,6–5,9 lần | Đúng |
| (d) Chiến lược join | Ép sort-merge chậm hơn khoảng 7–12%; `auto` và `broadcast` có cùng số toán tử join | Đúng |
| (e) Lệch khoá | Bộ lệch không chậm hơn rõ rệt (tỉ lệ 0,95–1,09 ở cả 4 cặp), lệch khoá không thành nút cổ chai ở quy mô này; AQE tách lệch; ở biến thể ép shuffle, bật AQE nhanh hơn khoảng 13%, nhóm cho là chủ yếu nhờ gộp phân vùng | Trái giả thuyết ở biến thể ép shuffle; vế `auto` không bị bác |
| (f) Cache | Truy vấn nhanh hơn 4,4–8,3 lần; hoà vốn sau khoảng 3,1 truy vấn | Đúng |
| (g) Pandas | Pandas nhanh hơn 6,1 lần (500k) và 4,0 lần (1M) | Đúng, ở quy mô nhỏ |

Nguồn: tổng hợp từ mục 6.4 đến 6.10 (results/metrics/*/summary.csv và các bảng phụ)

Các đoạn dưới đây là nhận định của nhóm, chương Thảo luận phân tích tiếp.

Chi phí cố định chi phối ở quy mô nhỏ. Mỗi giai đoạn tốn vài giây kể cả khi dữ liệu rất ít, cộng thêm khoảng 23 đến 24 giây ngoài thời gian xử lý mỗi lần chạy ở (a), và đến khoảng 32 giây ở các thí nghiệm khác. Vì vậy Spark thua Pandas ở bộ nhỏ và thông lượng tăng theo kích thước.

Một máy giới hạn khả năng mở rộng ngang. Hai worker chạy trên cùng CPU, cùng ổ đĩa và cùng giới hạn 6 GB, nên efficiency 0,64 phản ánh cả tranh chấp tài nguyên ngoài phần tuần tự của thuật toán.

Kế hoạch thực thi quan trọng hơn cấu hình danh nghĩa. Event log cho thấy `auto` và `broadcast` có cùng số toán tử join (4 sort-merge, 6 broadcast), nên nhóm suy luận gợi ý broadcast không đổi kế hoạch. Nếu chỉ nhìn thời gian, người đọc có thể kết luận sai rằng gợi ý broadcast nhanh hơn. Tương tự, skew chỉ thành vấn đề khi khoá lệch đi qua shuffle và phân vùng đủ lớn, còn ở cấu hình thực tế (`auto`) broadcast đã tránh được vấn đề.

Chất lượng dữ liệu ảnh hưởng trực tiếp đến kết quả phân tích: doanh thu tính trên dữ liệu thô cao hơn khoảng 9,6% so với dữ liệu sạch.

Độ tin cậy của số đo bị giới hạn bởi n = 3, áp lực RAM trên host và độ biến thiên. `processing_seconds_total` của các thí nghiệm ETL có CV trên 10% ở hai nhóm, và các truy vấn ngắn của (c), (f) có CV trên 10% ở bảy nhóm (mục 6.2). Nhóm xem các chênh lệch dưới khoảng 5 đến 10% giữa hai cấu hình là chưa phân biệt được. Tiêu chí này nới rộng hơn tiêu chí một độ lệch chuẩn ở mục 6.2, một chênh lệch chỉ được coi là rõ khi vượt cả hai.

<!-- VERIFY
- Thời gian bộ đo 22:00:54–23:41:37 +07: results/logs/scale_data/runner.log dòng 1; ended_at lớn nhất 2026-11-07T23:41:37 ở results/metrics/pandas_baseline/runs.csv (orders_1m r3).
- 69 lần, status ok, valid True: tất cả runs.csv (12+6+6+9+24+6+6). Riêng format_compare/cache runs.csv có nhiều dòng mỗi lần chạy (theo truy vấn/bước).
- 57/69 dirty: git_dirty True ở mọi runs.csv trừ scale_data; dirty_paths gồm đúng .claude/agent-memory/benchmark-analyst/MEMORY.md và env_limits.md ở cả 57 bản ghi (verify-round2, grep nhiều dòng).
- RAM host 4.168 MiB (74%) trước, 351 MiB (97%) sau lần đầu: results/metrics/scale_data/runs/orders_500k/r1/run_record.json. 400 MiB: scale_data orders_1m r1 trong runs.csv. Khoảng 0,8–1,1 GB: các giá trị host_available_mib khác.
- CV 11,92% = 9,193387/77,141667; CV 12,70% = 16,309134/128,436667.
- Bảng 6.3: results/samples/orders_5m/summary.csv, quarantine_by_reason.csv; gộp hai bảng cũ, không bỏ số; tổng 19.244.742 / 1.276.733 / 410.030 do người viết cộng; 91,9% = 19.244.742/20.931.505; 38,5% = 376.230/976.840.
- "Khớp số lỗi đã chèn ở cả năm bộ": docs/design/etl.md mục "Kết quả với schema có line_no".
- (a): scale_data/summary.csv; 1,82 = 77,141667/42,429333; 6,4 = 27,344667/4,289333; r3 87,745: scale_data/runs.csv. Phần ngoài thời gian xử lý đến khoảng 32 giây ở (e): verify-round2 A4.
- Bảng (b): scale_workers/summary.csv; p ≈ 0,45 từ 1/S = 1 − p/2 với S = 1,287569 (người viết tính); 22% = 1 − 82,206/105,846; 77,14 / 77,16 (skew/summary.csv) / 78,65 / 82,21; S ≈ 1,37 = 105,846/77,142.
- Bảng (c): format_compare/summary.csv; sizes.csv; tổng 1.089.695.264 và 226.238.030 byte. Số dòng thô so với sạch: web_events 5.100.000/4.900.063 = 1,04; orders 5.100.000/4.800.044 = 1,06; order_items 10.201.505/9.024.635 = 1,13 (người viết tính; verify-round2 F10 ghi khoảng 8% theo tổng năm bảng). q2 2,48 s: runs.csv curated_first r3. Doanh thu 767.333.901,89 / 700.264.598,73: runs.csv cột result; 9,6% = 767.333.901,89/700.264.598,73 − 1.
- Bảng (d): join_strategy/summary.csv, plan_check.csv; 12% = 83,996/74,920 − 1; 7% = 83,996/78,645 − 1; 9% so với trung bình chung 76,78 (verify-round2 B1). plan_check chỉ đếm toán tử, "không đổi kế hoạch" là suy luận (verify-round2 B4).
- Bảng (e): skew/summary.csv, plan_check.csv; 13% (13,3% và 12,8%); order_items 34,40 vs 34,85; 10,18 giây = 84,07 − 73,89 (verify-round1 mục C). `dimensions`, `orders` 1,13 ở skew_auto_aqe so với balanced_auto_aqe: verify-round2 B5. Số đọc từ ảnh 09, 10 là của r1: verify-round2 B6. Vế `auto` của giả thuyết: verify-round2 F2.
- Ảnh 07: 49 skewed partition splits; ảnh 09/10: 15,5 MiB / 1,5 MiB / 0,5 s và 1,9 MiB / 0,2 s: results/logs/screenshots/README.md mục "Số đọc được trên ảnh" và chính ảnh.
- AQE gộp phân vùng sau shuffle: Spark SQL Performance Tuning 4.0.0.
- Bảng (f): cache/summary.csv, break_even.csv; 31% = 4,849/15,75; bộ nhớ 215,9/251,9/215,9 MiB, đĩa 41,0/20,5/41,0 MiB: cache/runs/cache/r1..r3/query_bench.json (verify-round1 mục C); InMemoryTableScan trong plan_after_run của r1.
- Bảng (g): pandas_baseline/comparison_spark.csv, summary.csv; 49 checks, all_match True: pandas_baseline/runs.csv; 1,95 = 7,064/3,619; 1,28 = 27,936/21,895; ~8 GB ngoại suy = 1.682 × 5 (từ 1M lên 5M), chưa đo.
- Khác biệt môi trường Pandas/Spark: src/experiments/pandas_baseline/README.md.
- Speedup, efficiency (c2 tr. 21), Amdahl (c2 tr. 22), Parquet (c4 tr. 46, c5 tr. 44), broadcast (c5 tr. 51), cache (c5 tr. 31, 32): đã đối chiếu slide (report/review/verify-slides.md). Đã tính lại p ≈ 0,45: 1/1,29 = 0,775; p = 2 × (1 − 0,775).
- Rút gọn 2026-11-16: câu "Nguyên nhân của speedup thấp phần lớn còn là suy đoán" lấy từ chương 8, 9, không phải khẳng định mới. Chi tiết đã chuyển sang Phụ lục D, VERIFY tương ứng ở đó.
-->
