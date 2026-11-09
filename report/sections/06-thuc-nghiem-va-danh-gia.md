# Chương 6. Thực nghiệm và đánh giá

Chương này trình bày môi trường và phương pháp đo, chất lượng dữ liệu trước và sau xử lý, rồi lần lượt kết quả bảy thí nghiệm (a) đến (g). Mỗi thí nghiệm gồm mục tiêu và giả thuyết, cấu hình, bảng số, hình và nhận xét; các bảng số chi tiết nằm ở Phụ lục D. Mọi con số lấy từ các tệp trong `results/`; số trong bảng được làm tròn hai chữ số thập phân khi trình bày, số gốc nằm trong tệp nguồn ghi dưới mỗi bảng. Các tỉ số do người viết tự chia được ghi rõ là "tính từ" tệp nguồn.

## 6.1 Môi trường thí nghiệm

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

Trong 69 bản ghi, 57 bản ghi có cờ `dirty` (cây mã có thay đổi chưa commit lúc chạy). Danh sách `dirty_paths` của các bản ghi này chỉ gồm hai tệp bộ nhớ của agent đo trong `.claude/agent-memory/benchmark-analyst/`, được ghi trong lúc bộ đo đang chạy; thư mục `src/` và `tests/` không thay đổi. Vì vậy cờ này không ảnh hưởng đến mã được đo. 12 lần chạy đầu tiên (thí nghiệm (a)) không có cờ này.

**RAM của máy host chịu áp lực trong lúc đo.** Trước lần chạy đầu tiên, host còn trống 4.168 MiB (mức sử dụng bộ nhớ 74%). Ngay sau lần chạy đó, RAM trống xuống 351 MiB (97%), phù hợp với việc máy ảo WSL2 chiếm dần đến giới hạn 6 GB. Trước các lần chạy Spark còn lại, RAM trống của host chủ yếu khoảng 0,8 đến 1,1 GB, thấp nhất 400 MiB. Áp lực bộ nhớ trên host là một nguồn nhiễu có thể có (giả thuyết, chưa đo trực tiếp ảnh hưởng). Nguồn: cột `host_available_mib` trong các `runs.csv`; `host_before`, `host_after` trong `results/metrics/scale_data/runs/orders_500k/r1/run_record.json`.

Các lần chạy ETL đầu tiên của từng bộ (`results/metrics/orders_*.json`) chỉ chạy một lần khi máy chưa ở trạng thái sạch; chúng chỉ dùng để kiểm tra tính đúng và số đếm chất lượng, không dùng làm số đo hiệu năng.

## 6.2 Phương pháp đo

- **Chỉ số chính** là `processing_seconds_total`: tổng thời gian năm giai đoạn ETL do job tự đo, không gồm khởi động container và JVM, đăng ký executor và bước thống kê sau xử lý. Với (c) và (f), chỉ số là thời gian từng truy vấn (đo quanh lệnh `collect()`), sau một bước khởi động không tính giờ.
- **Lặp lại:** mỗi cấu hình 3 lần; bảng ghi trung bình ± độ lệch chuẩn mẫu và khoảng min–max. Hệ số biến thiên CV = độ lệch chuẩn / trung bình được dùng để đánh giá độ ổn định.
- **Tính hợp lệ:** mọi lần chạy đều qua kiểm tra trước khi chạy (số worker, số lõi, không có ứng dụng khác) và sau khi chạy (số worker không đổi, số dòng thô khớp manifest). Không lần nào bị loại; mọi nhóm có `n` = 3 (hoặc 6 với (c)).
- **Nhiễu đáng chú ý:** với `processing_seconds_total` của các thí nghiệm ETL, CV vượt 10% ở hai nhóm: `orders_5m` của (a) (11,92%) và `balanced_shuffle_noaqe` của (e) (12,70%). Với các truy vấn ngắn, CV vượt 10% ở nhiều nhóm hơn: trong (c) là q1 thô 17,0%, q1 Parquet 19,5%, q2 Parquet 91,5%, q3 Parquet 21,0%; trong (f) là q5 không cache 23,3%, q3 có cache 12,6%, q5 có cache 15,8% (tính từ các `summary.csv` tương ứng). Với n = 3, các chênh lệch nhỏ hơn khoảng một độ lệch chuẩn được coi là chưa phân biệt được với nhiễu.

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

Nguồn: results/samples/orders_5m/summary.csv (đếm trực tiếp trên MinIO, cột matches_metrics = yes), results/samples/orders_5m/quarantine_by_reason.csv; khớp results/metrics/orders_5m.json; dòng Tổng do người viết cộng

Nhận xét:

- Khoảng 91,9% số dòng thô được giữ lại sau làm sạch (tính từ @tbl:chat-luong-5m). Tổng thô bằng đúng tổng sạch + cách ly + trùng, không có dòng nào bị mất mà không rõ lý do.
- Số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp số lỗi bộ sinh đã chèn ở cả năm bộ dữ liệu (`docs/design/etl.md`). Riêng `order_items` bỏ đúng 200.030 dòng trùng nhờ bỏ trùng theo khoá (`order_id`, `line_no`).
- `no_clean_order` chiếm 376.230 dòng, tức 38,5% số dòng hàng bị cách ly (tính từ @tbl:chat-luong-5m). Đây là hệ quả dây chuyền của 199.956 đơn bị cách ly, khoảng 1,9 dòng hàng mỗi đơn, sát mức trung bình 2 dòng/đơn của bộ sinh.
- **Không có dòng nào bị cách ly vì `invalid_order_date` hay `invalid_event_time`:** mọi ngày và thời gian sai định dạng đã được nhận diện và chuẩn hoá. Ví dụ trước và sau ở chương 7.
- Số đếm chất lượng giống hệt nhau giữa mọi lần chạy của cùng bộ dữ liệu trong bộ thí nghiệm (`counts_consistent` = True), tức job cho kết quả xác định.

## 6.4 Thí nghiệm (a): mở rộng theo kích thước dữ liệu

**Mục tiêu và giả thuyết.** Đo thời gian ETL khi số đơn tăng từ 0,5 triệu lên 5 triệu, cấu hình mặc định. Giả thuyết: thời gian tăng chậm hơn dữ liệu ở bộ nhỏ do chi phí cố định (lập lịch, khởi tạo, ghi nhiều tệp nhỏ), và thông lượng tăng dần rồi bão hoà.

**Cấu hình.** Join `auto`, AQE bật, 8 phân vùng shuffle, 2 worker; 4 bộ × 3 lần, thứ tự xen kẽ.

Bảng: Thời gian xử lý và thông lượng theo kích thước dữ liệu {#tbl:scale-tong}

| Bộ | Dòng thô | Thời gian xử lý (s) | Min–max (s) | Thông lượng (dòng/s) | Tỉ lệ dữ liệu | Tỉ lệ thời gian |
|---|---|---|---|---|---|---|
| orders_500k | 2.092.960 | 21,90 ± 0,74 | 21,14–22,63 | 95.664 | 1,00 | 1,00 |
| orders_1m | 4.184.974 | 27,94 ± 0,36 | 27,54–28,26 | 149.821 | 2,00 | 1,28 |
| orders_2500k | 10.464.824 | 42,43 ± 0,19 | 42,31–42,65 | 246.645 | 5,00 | 1,94 |
| orders_5m | 20.931.505 | 77,14 ± 9,19 | 71,40–87,75 | 273.766 | 10,00 | 3,52 |

Nguồn: results/metrics/scale_data/summary.csv (processing_seconds_total, throughput_rows_per_s, data_ratio, time_ratio)

Thông lượng trong @tbl:scale-tong là trung bình của thông lượng từng lần chạy, nên khác một chút so với tổng dòng chia thời gian trung bình (ở orders_5m: 273.766 so với 271.340 dòng/s).

![Thời gian xử lý theo số dòng thô (trung bình ± độ lệch chuẩn, n = 3)](results/figures/scale_data/processing_time_vs_rows.png){#fig:scale-thoi-gian}

Nguồn: results/metrics/scale_data/summary.csv

![Thông lượng (dòng thô/giây) theo kích thước dữ liệu](results/figures/scale_data/throughput.png){#fig:scale-thong-luong}

Nguồn: results/metrics/scale_data/summary.csv

![Thời gian từng giai đoạn ETL theo kích thước dữ liệu](results/figures/scale_data/stages.png){#fig:scale-giai-doan}

Nguồn: results/metrics/scale_data/summary.csv

**Nhận xét.**

- Kết quả phù hợp giả thuyết. Dữ liệu tăng 10 lần nhưng thời gian chỉ tăng 3,52 lần (@tbl:scale-tong, @fig:scale-thoi-gian). Thông lượng tăng từ khoảng 96 nghìn lên 274 nghìn dòng/giây (@fig:scale-thong-luong); từ 2,5M lên 5M, dữ liệu gấp đôi và thời gian gấp 1,82 lần (tính từ summary), nên thông lượng bắt đầu chững lại.
- Chi phí cố định thấy rõ ở giai đoạn `dimensions`: bảng `customers` tăng 10 lần nhưng thời gian chỉ tăng từ 4,47 lên 6,29 giây (@fig:scale-giai-doan; số liệu ở @tbl:scale-giai-doan-chi-tiet, Phụ lục D). Ở bộ nhỏ, mỗi giai đoạn tốn khoảng 4 đến 5 giây dù dữ liệu rất ít; phần lớn thời gian này là chi phí lập lịch stage, ghi và đọc lại Parquet trên MinIO (nhận định của người viết).
- Giai đoạn `order_items` (bảng lớn nhất, có hai phép join và một lần bỏ trùng) tăng nhanh nhất: từ 4,29 lên 27,34 giây, gấp 6,4 lần. Đây là giai đoạn chiếm nhiều thời gian nhất ở bộ 5M.
- Ngoài thời gian xử lý, mỗi lần chạy tốn thêm khoảng 23 đến 24 giây gần như không đổi theo kích thước (`wall_seconds` − `processing_seconds_total`, tính từ summary), gồm khởi động container và JVM, đăng ký executor, bước thống kê và tắt Spark. Với bộ 500k, phần này lớn hơn cả thời gian xử lý.
- CV của bộ 5M là 11,92% do lần r3 chậm hơn hẳn (87,75 so với 71,40 và 72,28 giây), chủ yếu ở giai đoạn `order_items` (35,27 so với khoảng 23,4 giây) (`results/metrics/scale_data/runs.csv`). Không có cờ bất thường nào ở lần này; nguyên nhân chưa xác định. Lấy lần chậm nhất của bộ 5M chia cho trung bình của bộ 500k, tỉ lệ thời gian là 4,01 (87,745/21,895); chia cho lần chậm nhất của bộ 500k là 3,88 (87,745/22,631). Như vậy kể cả trong trường hợp xấu nhất, thời gian cũng chỉ tăng khoảng 4 lần cho 10 lần dữ liệu.

## 6.5 Thí nghiệm (b): mở rộng theo số worker

**Mục tiêu và giả thuyết.** Tính speedup S = T(1 worker) / T(2 worker) và efficiency E = S / 2 trên orders_5m (slide chương 2, tr. 21 [@slide-c2]). Giả thuyết: 1 < S < 2 vì có phần tuần tự (driver, ghi metadata, đọc từ MinIO dùng chung) và chi phí shuffle.

**Cấu hình.** orders_5m, cấu hình mặc định. Cấu hình `w1` dừng `spark-worker-2` (cụm còn 1 executor, 2 lõi, heap 1 GB); `w2` dùng đủ 2 worker. Chạy theo khối: 3 lần `w1` rồi 3 lần `w2`.

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

![Thời gian ETL với 1 và 2 worker và speedup theo từng giai đoạn](results/figures/scale_workers/speedup.png){#fig:workers-speedup}

Nguồn: results/metrics/scale_workers/summary.csv

**Nhận xét.**

- Speedup tổng là 1,29 và efficiency 0,64: gấp đôi tài nguyên chỉ giảm khoảng 22% thời gian xử lý. Kết quả nằm trong khoảng 1 < S < 2 như giả thuyết.
- Các giai đoạn có xử lý dữ liệu lớn (`orders`, `order_items`, `web_events`, `aggregates`) đạt S từ 1,27 đến 1,41. Riêng `dimensions` chậm đi khi có 2 worker (S = 0,81). Giai đoạn này chỉ xử lý 510 nghìn khách hàng và 20 nghìn sản phẩm; với dữ liệu nhỏ như vậy, chi phí phối hợp hai executor và trao đổi dữ liệu shuffle qua mạng có thể lớn hơn phần lợi do song song (nhận định của người viết, chưa kiểm chứng bằng event log).
- **Ước lượng theo định luật Amdahl** (công thức ở slide chương 2, tr. 22 [@slide-c2]; ước lượng và diễn giải là nhận định của người viết, chỉ là ước lượng thô): với N = 2 và S = 1,29, từ S = 1 / ((1 − p) + p/N) suy ra phần có thể song song hoá hiệu dụng p ≈ 0,45. Ở đây p là phần song song, N là số worker; slide dùng s = 1 − p cho phần tuần tự và p cho số node. Con số này không nên hiểu là 55% mã chạy tuần tự. Nó gộp cả các chi phí không giảm khi thêm worker: lập lịch ở driver, ghi metadata, tranh chấp I/O vì MinIO, hai worker và hệ điều hành dùng chung một ổ đĩa vật lý, và áp lực RAM trên host.
- Phép so sánh này không chỉ đổi số lõi: chuyển từ 1 lên 2 worker cũng nhân đôi bộ nhớ executor (1 lên 2 GB tổng). Với 1 worker, dữ liệu shuffle có thể tràn ra đĩa nhiều hơn, nên S đo được phản ánh cả hiệu ứng bộ nhớ.
- Do chạy theo khối, `w1` và `w2` diễn ra ở hai khoảng thời gian khác nhau (23:28 đến 23:35 và 23:35 đến 23:41), nên nhiễu theo thời gian không được cân bằng như các thí nghiệm xen kẽ. Cùng cấu hình 2 worker mặc định trên orders_5m, ba thí nghiệm cho trung bình 77,14 giây ((a)), 78,65 giây ((d), `auto`) và 82,21 giây ((b)), tức chênh nhau khoảng 7% giữa các đợt chạy. Speedup 1,29 vì vậy có sai số không nhỏ; dùng 77,14 giây làm mẫu số thì S sẽ là khoảng 1,37 (tính từ hai summary).

## 6.6 Thí nghiệm (c): CSV/JSON thô so với Parquet

**Mục tiêu và giả thuyết.** Chạy cùng ba truy vấn Spark trên dữ liệu thô (CSV, JSON lines) và trên Parquet đã làm sạch, so thời gian và dung lượng. Giả thuyết: Parquet nhanh hơn rõ ở truy vấn dùng ít cột nhờ đọc theo cột và đẩy điều kiện lọc xuống, và nhỏ hơn nhờ nén theo cột (slide chương 4, tr. 46 [@slide-c4]; slide chương 5, tr. 44 [@slide-c5]).

**Cấu hình.** orders_5m, cùng phiên Spark như ETL, 2 worker. Truy vấn q1: lọc `orders` theo `status = 'delivered'` rồi đếm; q2: đếm `web_events` theo `event_type`; q3: join `order_items` với `orders`, tổng doanh thu theo ngày. Hai cấu hình đảo thứ tự định dạng trong mỗi truy vấn, mỗi cấu hình 3 lần; số liệu gộp n = 6.

Bảng: Thời gian truy vấn trên dữ liệu thô và Parquet (orders_5m, n = 6) {#tbl:format-thoi-gian}

| Truy vấn | Thô (s) | Parquet (s) | Thô / Parquet |
|---|---|---|---|
| q1 lọc và đếm `orders` | 1,61 ± 0,27 | 0,76 ± 0,15 | 2,13 |
| q2 đếm `web_events` theo loại | 2,38 ± 0,16 | 0,87 ± 0,80 | 2,74 |
| q3 join và tổng doanh thu theo ngày | 7,51 ± 0,60 | 3,39 ± 0,71 | 2,22 |

Nguồn: results/metrics/format_compare/summary.csv (cột mean, std, ratio_raw_over_curated)

Bảng: Dung lượng lưu trữ thô và Parquet đã làm sạch (orders_5m, MB = 10^6 byte) {#tbl:format-kich-thuoc}

| Bảng | Định dạng thô | Thô (MB) | Parquet curated (MB) | Thô / curated |
|---|---|---|---|---|
| customers | CSV | 12,90 | 2,93 | 4,41 |
| orders | CSV | 216,90 | 51,78 | 4,19 |
| order_items | CSV | 235,52 | 65,63 | 3,59 |
| products | Parquet | 0,20 | 0,17 | 1,23 |
| web_events | JSON lines | 624,17 | 105,73 | 5,90 |
| **Tổng** | | **1.089,70** | **226,24** | **4,82** |

Nguồn: results/metrics/format_compare/sizes.csv (raw_bytes, curated_bytes, ratio_raw_over_curated); dòng Tổng do người viết tính

![Thời gian ba truy vấn trên dữ liệu thô và Parquet](results/figures/format_compare/query_times_orders_5m.png){#fig:format-truy-van}

Nguồn: results/metrics/format_compare/summary.csv

![Dung lượng lưu trữ từng bảng: thô so với Parquet đã làm sạch](results/figures/format_compare/storage_orders_5m.png){#fig:format-dung-luong}

Nguồn: results/metrics/format_compare/sizes.csv

**Nhận xét.**

- Parquet nhanh hơn 2,1 đến 2,7 lần ở cả ba truy vấn (@tbl:format-thoi-gian). Truy vấn q2 có tỉ lệ cao nhất; theo nhận định của người viết, lý do là với JSON lines, Spark phải phân tích cú pháp cả dòng dù chỉ cần một cột `event_type`.
- Parquet nhỏ hơn 3,6 đến 5,9 lần ở bốn bảng chuyển từ CSV/JSON (@tbl:format-kich-thuoc). Tỉ lệ này **gộp hai hiệu ứng**: nén theo cột và việc bảng curated ít dòng hơn (đã bỏ trùng và bản ghi lỗi). Quy về byte trên mỗi dòng, Parquet vẫn nhỏ hơn khoảng 3,2 đến 5,7 lần (tính từ @tbl:format-byte-dong, Phụ lục D), nên phần lớn chênh lệch đến từ định dạng. Bảng `products` vốn đã là Parquet nên tỉ lệ chỉ 1,23.
- Độ lệch chuẩn của q2 trên Parquet lớn (0,80 giây) vì một lần đo 2,48 giây trong khi các lần khác 0,44 đến 0,70 giây (`results/metrics/format_compare/runs.csv`). Thứ tự chạy cũng có ảnh hưởng: tách theo thứ tự, tỉ lệ thô/Parquet của q2 là 5,46 khi đọc thô trước và 1,75 khi đọc Parquet trước (`summary_by_order.csv`). Cột `homogeneous` = False trong `summary.csv` là do gộp hai cấu hình thứ tự, đúng như thiết kế.
- Kết quả truy vấn trên hai định dạng khác nhau vì dữ liệu thô còn bản ghi trùng và lỗi: q1 đếm được 3.060.980 đơn trên dữ liệu thô so với 2.880.698 trên Parquet; tổng doanh thu q3 là 767.333.901,89 trên dữ liệu thô so với 700.264.598,73 trên dữ liệu sạch (cột `result` trong `runs.csv`). Truy vấn thẳng trên dữ liệu thô sẽ cho doanh thu cao hơn khoảng 9,6% (tính từ hai số trên). Đây là minh hoạ cụ thể cho giá trị của bước làm sạch, ngoài lợi ích về tốc độ.

## 6.7 Thí nghiệm (d): broadcast join so với sort-merge join

**Mục tiêu và giả thuyết.** So thời gian ETL khi các join với bảng nhỏ dùng broadcast hash join hay sort-merge join [@spark-sql-tuning] (thường cần shuffle cả hai phía). Giả thuyết: broadcast nhanh hơn vì có thể tránh shuffle bảng lớn, dù bảng nhỏ vẫn truyền qua mạng (slide chương 5, tr. 51 [@slide-c5]).

**Cấu hình.** orders_5m, AQE bật, 8 phân vùng. `auto`: Spark tự chọn theo ngưỡng 10 MB; `broadcast`: gợi ý broadcast cho phía nhỏ; `shuffle_noauto`: gợi ý `merge` và tắt broadcast tự động, nên mọi join thành sort-merge.

Bảng: Thời gian ETL theo chiến lược join (orders_5m) {#tbl:join}

| Cấu hình | Thời gian xử lý (s) | Min–max (s) | orders (s) | order_items (s) | web_events (s) | aggregates (s) |
|---|---|---|---|---|---|---|
| auto | 78,65 ± 6,63 | 73,67–86,18 | 15,42 | 26,32 | 20,19 | 9,69 |
| broadcast | 74,92 ± 1,89 | 73,65–77,10 | 15,95 | 23,68 | 19,05 | 9,71 |
| shuffle_noauto | 84,00 ± 2,19 | 82,25–86,45 | 17,66 | 28,08 | 19,10 | 12,58 |

Nguồn: results/metrics/join_strategy/summary.csv

Bảng: Toán tử join trong kế hoạch thực thi cuối (mỗi lần chạy, 27 truy vấn SQL) {#tbl:join-ke-hoach}

| Cấu hình | SortMergeJoin | BroadcastHashJoin | Giống nhau ở cả 3 lần |
|---|---|---|---|
| auto | 4 | 6 | Có |
| broadcast | 4 | 6 | Có |
| shuffle_noauto | 10 | 0 | Có |

Nguồn: results/metrics/join_strategy/plan_check.csv (đếm từ event log)

![Thời gian ETL theo chiến lược join](results/figures/join_strategy/join_strategy.png){#fig:join-strategy}

Nguồn: results/metrics/join_strategy/summary.csv

**Nhận xét.**

- Ép sort-merge join cho mọi phép join làm job chậm hơn: 84,00 giây so với 74,92 giây của `broadcast`, chậm hơn khoảng 12% (tính từ summary). Phần chậm thêm tập trung ở ba giai đoạn có join: `orders`, `order_items` và `aggregates` (tăng từ 9,71 lên 12,58 giây). Giai đoạn `web_events` không có join và gần như bằng nhau ở cả ba cấu hình (19,05 đến 20,19 giây), đóng vai trò đối chứng cho mức nhiễu.
- Kế hoạch thực thi xác nhận cấu hình có hiệu lực: `shuffle_noauto` không còn `BroadcastHashJoin` nào (@tbl:join-ke-hoach).
- `auto` và `broadcast` có **cùng kế hoạch** (4 sort-merge, 6 broadcast). Spark tự broadcast các bảng nhỏ vì chúng dưới ngưỡng 10 MB, nên gợi ý broadcast không thay đổi gì. Chênh lệch 3,7 giây giữa hai cấu hình này vì vậy là nhiễu; nó chủ yếu do lần r2 của `auto` (86,18 giây, `order_items` 31,29 giây).
- Bốn sort-merge join còn lại ở `auto`: `plan_check.csv` chỉ ghi số đếm, không ghi cặp bảng. Người viết suy luận đây là các join mà cả hai phía đều vượt ngưỡng broadcast mặc định.

## 6.8 Thí nghiệm (e): lệch khoá, cách join và AQE

**Mục tiêu và giả thuyết.** So thời gian ETL trên bộ cân bằng (orders_5m) và bộ lệch khoá (orders_5m_skew), với hai cách join và AQE bật hoặc tắt (8 cấu hình). Giả thuyết: ở `auto`, chênh lệch nhỏ vì join theo `product_id` là broadcast; ở biến thể ép shuffle, bộ lệch chậm hơn khi tắt AQE (vài task phải xử lý phần lớn dữ liệu), và AQE bật sẽ thu hẹp chênh lệch nhờ tách phân vùng lệch.

**Cấu hình.** `auto`: cấu hình mặc định của ETL. `shuffle` (biến thể ép shuffle, cài đặt chủ động): tắt broadcast, 64 phân vùng shuffle, ngưỡng phân vùng lệch 4 MiB, kích thước phân vùng tư vấn 2 MiB. Lý do chọn các tham số nằm ở mục 4.6. Căn cứ là phép đo kích thước phân vùng khi băm `order_items` theo `product_id` (@tbl:partition-stats, Phụ lục D): ở 64 phân vùng, phân vùng lớn nhất của bộ lệch gấp 10,54 lần trung vị và có 9 phân vùng vượt 5 lần trung vị; ở 8 phân vùng, tỉ số này chỉ là 1,77 và không phân vùng nào vượt; ở bộ cân bằng, tỉ số là 1,01 (8 phân vùng) và 1,18 (64 phân vùng).

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

![Thời gian ETL theo 8 cấu hình và theo giai đoạn](results/figures/skew/skew.png){#fig:skew}

Nguồn: results/metrics/skew/summary.csv

**Nhận xét.**

- **Kết quả trái giả thuyết: bộ lệch không chậm hơn rõ rệt so với bộ cân bằng.** Tỉ lệ lệch/cân bằng nằm trong khoảng 0,95 đến 1,09 ở cả 4 cặp (@tbl:skew-cau-hinh); cặp duy nhất có tỉ lệ trên 1 là `auto` bật AQE. Kể cả ở biến thể ép shuffle và tắt AQE, nơi giả thuyết dự đoán chênh lệch lớn nhất, bộ lệch còn nhanh hơn một chút (122,22 so với 128,44 giây, chênh lệch nhỏ hơn độ lệch chuẩn).
- **AQE có tách join lệch, đúng như thiết kế.** Chỉ cấu hình `skew_shuffle_aqe` có `SortMergeJoin(skew=true)` (3 nút trong kế hoạch cuối, như nhau ở cả 3 lần chạy; tổng số nút sort-merge vẫn là 10 như các cấu hình ép shuffle khác); bộ cân bằng với cùng tham số không kích hoạt tách lệch, đúng như ngưỡng 4 MiB được chọn. Ảnh kế hoạch thực thi (@fig:ss-aqe-plan ở chương 7) cho thấy nút `AQEShuffleRead` ghi 49 lần tách phân vùng lệch (`number of skewed partition splits: 49`) ở bước ghi `order_items` sạch.
- **Tách lệch có san phẳng task, nhưng lợi ích tuyệt đối rất nhỏ.** So hai ảnh chụp bảng Summary Metrics của stage đọc shuffle `order_items` (@fig:ss-noaqe-tasks, @fig:ss-aqe-tasks): khi tắt AQE (64 task), dữ liệu shuffle đọc lớn nhất của một task là 15,5 MiB so với trung vị 1,5 MiB, task lâu nhất 0,5 giây; khi bật AQE (104 task, gồm các task tách ra từ phân vùng lệch), lớn nhất chỉ còn 1,9 MiB và task lâu nhất 0,2 giây. Số task khớp phép tính 64 − 9 + 49 = 104: 9 phân vùng vượt ngưỡng được thay bằng 49 phần tách (tính của người viết từ @tbl:partition-stats và @fig:ss-aqe-plan). Chênh lệch dưới một giây mỗi task không đủ để thấy trên tổng thời gian khoảng 100 giây. Giai đoạn `order_items` gần như không đổi khi bật AQE ở bộ lệch (34,40 so với 34,85 giây).
- **Lợi ích chính của AQE đến từ việc gộp phân vùng, không phải xử lý lệch.** Ở biến thể ép shuffle, bật AQE giảm thời gian khoảng 13% ở cả hai bộ (128,44 xuống 111,30 giây ở bộ cân bằng, 122,22 xuống 106,52 giây ở bộ lệch; tính từ summary). Phần giảm tập trung ở `aggregates` (khoảng 23 xuống 13 giây) và `dimensions` (khoảng 11 xuống 6,5 giây), và giống nhau ở bộ cân bằng, nơi không có phân vùng nào bị tách. Với 64 phân vùng cho dữ liệu chỉ vài trăm MB, phần lớn phân vùng rất nhỏ; AQE gộp chúng lại, giảm số task và số tệp nhỏ phải ghi (nhận định của người viết, phù hợp với mô tả tính năng gộp phân vùng sau shuffle của AQE [@spark-sql-tuning]).
- **Ở chế độ `auto`, khoá lệch không đi qua shuffle.** Bảng `products` được broadcast (@fig:ss-auto-plan), nên join theo `product_id` không tạo phân vùng lệch. Đây là cấu hình thực tế của job, và vì thế lệch khoá hầu như không ảnh hưởng.
- Ở `auto`, `skew_auto_aqe` chậm hơn `skew_auto_noaqe` 10,18 giây (84,07 so với 73,89) dù hai cấu hình có cùng số toán tử join. Một phần chênh lệch nằm ở các giai đoạn không phụ thuộc khoá lệch (`dimensions`, `orders`), nên người viết cho rằng có phần do nhiễu; tuy vậy cả hai bộ đều cho `order_items` chậm hơn khi bật AQE ở `auto` (26,63 so với 22,58 giây ở bộ cân bằng, 28,85 so với 22,17 giây ở bộ lệch). Với n = 3, đồ án chưa kết luận được nguyên nhân và chưa khẳng định đây là ảnh hưởng thật của AQE; cần đọc event log để kiểm tra.
- **Kết luận cho thí nghiệm này:** ở quy mô 5 triệu đơn với 50% lượt chọn dồn vào 10 sản phẩm, lệch khoá không trở thành nút cổ chai trên cụm này. Muốn thấy tác động rõ của skew cần dữ liệu lớn hơn nhiều so với bộ nhớ executor, hoặc mức lệch cao hơn; đó là hướng mở rộng, không phải kết quả đã đo.

## 6.9 Thí nghiệm (f): cache DataFrame dùng lại

**Mục tiêu và giả thuyết.** Chạy K = 5 truy vấn tổng hợp trên cùng một DataFrame `order_items ⋈ orders` (đọc từ Parquet curated), so không cache với có cache. Giả thuyết: không cache thì mỗi truy vấn đọc lại Parquet và làm lại join; có cache thì action đầu tiên materialize dữ liệu, các action sau có thể dùng lại thay vì chạy lại lineage (slide chương 5, tr. 31, 32 [@slide-c5]). Việc lần materialize tốn thêm thời gian và có lợi khi K đủ lớn là suy luận của người viết.

**Cấu hình.** orders_5m, `DataFrame.cache()`, 2 worker, mỗi chế độ 3 lần xen kẽ. Truy vấn: q1 doanh thu theo ngày, q2 theo trạng thái, q3 top 10 sản phẩm theo số lượng, q4 số dòng theo phương thức thanh toán, q5 giá trị trung bình theo `line_no`.

Bảng: Tổng thời gian truy vấn không cache và có cache (orders_5m, n = 3) {#tbl:cache-tong}

| Bước | Không cache (s) | Có cache (s) | Không cache / có cache |
|---|---|---|---|
| Materialize (`cache()` + `count()`) | | 8,03 ± 0,66 | |
| Tổng 5 truy vấn | 15,75 ± 1,01 | 2,88 ± 0,09 | 5,48 |
| Tổng gồm materialize | 15,75 ± 1,01 | 10,90 ± 0,59 | 1,44 |

Nguồn: results/metrics/cache/summary.csv; cột tỉ lệ do người viết tính

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

**Nhận xét.**

- Có cache, mỗi truy vấn nhanh hơn 4,4 đến 8,3 lần (@tbl:cache-truy-van, Phụ lục D) vì đọc từ bộ nhớ đệm thay vì đọc lại Parquet trên MinIO và làm lại sort-merge join. Kế hoạch thực thi sau truy vấn đầu tiên có `InMemoryTableScan`, xác nhận dữ liệu được đọc từ cache (`results/metrics/cache/runs/cache/r1/query_bench.json`).
- Chi phí materialize (8,03 giây) được bù lại sau khoảng 3,1 truy vấn, tức từ truy vấn thứ 4 trở đi (@tbl:cache-hoa-von). Với 5 truy vấn, cache tiết kiệm 4,85 giây (khoảng 31% tổng thời gian). Với 1 hoặc 2 truy vấn, cache sẽ làm chậm hơn; theo nhận định của người viết, nên chỉ cache dữ liệu thực sự được dùng lại.
- **Cache tràn một phần ra đĩa nhưng vẫn có lợi.** Cả 3 lần chạy đều cache đủ 8/8 phân vùng (9.024.635 dòng) ở mức "Disk Memory Deserialized 1x Replicated", là mức mặc định MEMORY_AND_DISK_DESER của `DataFrame.cache()` [@pyspark-cache]. Dữ liệu cache chiếm khoảng 216–252 MiB trong bộ nhớ và 20–41 MiB trên đĩa (r1–r3) (`storage_after_materialize` trong `results/metrics/cache/runs/cache/r<k>/query_bench.json`). Với heap mặc định 1 GB, vùng nhớ lưu trữ không chứa hết DataFrame; phần dư được ghi xuống đĩa cục bộ của worker, đọc lại vẫn rẻ hơn đọc lại Parquet và join lại (nhận định của người viết, suy từ số đo ở @tbl:cache-tong).
- Lưu ý công bằng: khi không cache, mỗi truy vấn chỉ đọc các cột cần thiết; khi cache, toàn bộ cột của DataFrame được giữ. Kết quả trên vì vậy đã tính đến chi phí giữ cột thừa.

## 6.10 Thí nghiệm (g): baseline Pandas một máy

**Mục tiêu và giả thuyết.** Viết lại cùng luật làm sạch và ba bảng tổng hợp bằng Pandas, chạy trên một máy, đo theo cùng năm giai đoạn để có điểm so sánh với Spark. Giả thuyết: ở kích thước nhỏ, Pandas có thể nhanh hơn Spark vì không có chi phí phân tán.

**Cấu hình.** orders_500k và orders_1m, mỗi bộ 3 lần, mỗi lần một tiến trình Python mới. Thời gian Spark lấy từ thí nghiệm (a). Mỗi lần chạy Pandas đối chiếu 49 số đếm với manifest và với metrics của Spark; cả 6 lần đều khớp toàn bộ.

Bảng: Thời gian xử lý của Pandas và Spark {#tbl:pandas-spark}

| Bộ | Pandas (s) | Spark (s) | Spark / Pandas | Bộ nhớ đỉnh Pandas (MiB) |
|---|---|---|---|---|
| orders_500k | 3,62 ± 0,27 | 21,90 ± 0,74 | 6,05 | 906 |
| orders_1m | 7,06 ± 0,34 | 27,94 ± 0,36 | 3,95 | 1.682 |

Nguồn: results/metrics/pandas_baseline/comparison_spark.csv; bộ nhớ đỉnh (peak_rss_mib) từ results/metrics/pandas_baseline/summary.csv

![Thời gian xử lý của Pandas (host) và Spark (cụm Docker)](results/figures/pandas_baseline/pandas_vs_spark.png){#fig:pandas}

Nguồn: results/metrics/pandas_baseline/comparison_spark.csv

Thời gian từng giai đoạn của Pandas ở @tbl:pandas-giai-doan (Phụ lục D).

**Nhận xét.**

- Pandas nhanh hơn Spark 6,1 lần ở bộ 500k và 4,0 lần ở bộ 1M (@tbl:pandas-spark). Kết quả phù hợp giả thuyết và được ghi nhận trung thực.
- Hai bên chạy trong **môi trường khác nhau**, nên phép so sánh không hoàn toàn công bằng: Pandas chạy trực tiếp trên host Windows, không bị giới hạn 6 GB của WSL2; Pandas đọc đĩa cục bộ còn Spark đọc MinIO qua mạng Docker; Pandas không có chi phí khởi động JVM, đăng ký ứng dụng và lập lịch task, trong khi Spark vẫn trả chi phí lập lịch trong từng giai đoạn. Ngược lại, Pandas dùng một lõi cho phần lớn thao tác còn Spark dùng 4 lõi executor.
- Bộ 500k và 1M quá nhỏ để kết luận về khả năng mở rộng: ở kích thước này, thời gian Spark bị chi phối bởi chi phí cố định mỗi giai đoạn (mục 6.4). Khoảng cách đang thu hẹp: dữ liệu gấp đôi thì thời gian Pandas tăng 1,95 lần, Spark chỉ tăng 1,28 lần (tính từ bảng).
- Bộ nhớ đỉnh của Pandas tăng gần tỉ lệ với dữ liệu (906 lên 1.682 MiB). Nếu tiếp tục tăng tuyến tính, bộ 5M sẽ cần khoảng 8 GB RAM cho một tiến trình (ngoại suy thô của người viết, **chưa đo**); đó là lúc giới hạn một máy của Pandas trở thành vấn đề. Đồ án không chạy Pandas trên 2,5M và 5M theo phạm vi đã chốt, nên không có số đo kiểm chứng điểm giao nhau.

## 6.11 Tổng hợp kết quả

Bảng: Tóm tắt kết quả bảy thí nghiệm {#tbl:tong-hop}

| Thí nghiệm | Kết quả chính | So với giả thuyết |
|---|---|---|
| (a) Kích thước dữ liệu | Dữ liệu × 10, thời gian × 3,52; thông lượng 96 nghìn lên 274 nghìn dòng/s | Đúng |
| (b) Số worker | S = 1,29, E = 0,64; `dimensions` chậm đi khi có 2 worker | Đúng (1 < S < 2) |
| (c) Định dạng | Parquet nhanh hơn 2,1–2,7 lần, nhỏ hơn 3,6–5,9 lần | Đúng |
| (d) Chiến lược join | Ép sort-merge chậm hơn khoảng 12%; `auto` và `broadcast` cùng kế hoạch | Đúng |
| (e) Lệch khoá | Bộ lệch không chậm hơn rõ rệt (tỉ lệ 0,95–1,09); AQE tách lệch nhưng lợi ích chủ yếu từ gộp phân vùng | Trái giả thuyết |
| (f) Cache | Truy vấn nhanh hơn 4,4–8,3 lần; hoà vốn sau khoảng 3,1 truy vấn | Đúng |
| (g) Pandas | Pandas nhanh hơn 6,1 lần (500k) và 4,0 lần (1M) | Đúng, ở quy mô nhỏ |

Nguồn: tổng hợp từ mục 6.4 đến 6.10 (results/metrics/*/summary.csv và các bảng phụ)

Các ý dưới đây là nhận định của người viết, sẽ được phân tích sâu hơn ở chương Thảo luận:

- **Chi phí cố định chi phối ở quy mô nhỏ.** Mỗi giai đoạn tốn vài giây kể cả khi dữ liệu rất ít, cộng thêm khoảng 23 giây ngoài thời gian xử lý cho mỗi lần chạy. Đây là lý do Spark thua Pandas ở bộ nhỏ và cũng là lý do thông lượng tăng theo kích thước.
- **Một máy giới hạn khả năng mở rộng ngang.** Hai worker chạy trên cùng CPU, cùng ổ đĩa và cùng giới hạn 6 GB, nên efficiency 0,64 phản ánh cả tranh chấp tài nguyên chứ không chỉ phần tuần tự của thuật toán.
- **Kế hoạch thực thi quan trọng hơn cấu hình danh nghĩa.** Kiểm tra event log cho thấy gợi ý broadcast không làm thay đổi kế hoạch so với `auto`; nếu chỉ nhìn thời gian, có thể kết luận sai rằng gợi ý broadcast nhanh hơn.
- **Skew chỉ thành vấn đề khi khoá lệch đi qua shuffle và phân vùng đủ lớn.** Ở cấu hình thực tế (`auto`), broadcast đã tránh được vấn đề.
- **Chất lượng dữ liệu ảnh hưởng trực tiếp đến kết quả phân tích.** Doanh thu tính trên dữ liệu thô cao hơn khoảng 9,6% so với dữ liệu sạch.
- **Độ tin cậy của số đo bị giới hạn** bởi n = 3, áp lực RAM trên host và độ biến thiên: `processing_seconds_total` của các thí nghiệm ETL có CV trên 10% ở hai nhóm, và các truy vấn ngắn của (c), (f) có CV trên 10% ở bảy nhóm (mục 6.2). Các chênh lệch dưới khoảng 5 đến 10% giữa hai cấu hình nên được xem là chưa phân biệt được.

<!-- VERIFY
- Thời gian bộ đo 22:00:54–23:41:37 +07: results/logs/scale_data/runner.log dòng 1; ended_at lớn nhất 2026-11-07T23:41:37 ở results/metrics/pandas_baseline/runs.csv (orders_1m r3).
- CPU, RAM 15,76 GB, ổ, Docker engine 29.9.2, MinIO RELEASE.2026-10-23T20-06-51Z: results/logs/environment.txt.
- 69 lần, status ok, valid True: tất cả runs.csv (12+6+6+9+24+6+6). Riêng format_compare/cache runs.csv có nhiều dòng mỗi lần chạy (theo truy vấn/bước).
- 57/69 dirty: git_dirty True ở mọi runs.csv trừ scale_data; dirty_paths gồm .claude/agent-memory/benchmark-analyst/MEMORY.md và env_limits.md (đã thấy ở skew_shuffle_aqe r1; cần kiểm vài bản ghi khác).
- RAM host 4.168 MiB (74%) trước, 351 MiB (97%) sau lần đầu: results/metrics/scale_data/runs/orders_500k/r1/run_record.json. 400 MiB: scale_data orders_1m r1 trong runs.csv. Khoảng 0,8–1,1 GB: các giá trị host_available_mib khác.
- CV 11,92% = 9,193387/77,141667; CV 12,70% = 16,309134/128,436667. CV truy vấn (c), (f): verify-round1 A3.
- Bảng 6.3: results/samples/orders_5m/summary.csv, quarantine_by_reason.csv; gộp hai bảng cũ, không bỏ số; tổng 19.244.742 / 1.276.733 / 410.030 do người viết cộng; 91,9% = 19.244.742/20.931.505; 38,5% = 376.230/976.840; 1,9 = 376.230/199.956.
- "Khớp số lỗi đã chèn ở cả năm bộ": docs/design/etl.md mục "Kết quả với schema có line_no".
- Bảng (a): scale_data/summary.csv; 273.766 là trung bình theo lần, 271.340 = 20.931.505/77,141667 (verify-round1 mục C); 1,82 = 77,141667/42,429333; 6,4 = 27,344667/4,289333; 23–24 s = wall − processing; r3 87,745, order_items 35,273: scale_data/runs.csv; 4,01 và 3,88: verify-round1 A4.
- Bảng (b): scale_workers/summary.csv; p ≈ 0,45 từ 1/S = 1 − p/2 với S = 1,287569 (người viết tính); 22% = 1 − 82,206/105,846; thời gian khối w1 23:28–23:35, w2 23:35–23:41: scale_workers/runs.csv; 77,14 / 78,65 / 82,21; S ≈ 1,37 = 105,846/77,142.
- Bảng (c): format_compare/summary.csv; sizes.csv; tổng 1.089.695.264 và 226.238.030 byte, tỉ lệ 4,82. q2 2,48 s: runs.csv curated_first r3. 5,46 / 1,75: summary_by_order.csv. Kết quả 3.060.980 / 2.880.698 / 767.333.901,89 / 700.264.598,73: runs.csv cột result; 9,6% = 767.333.901,89/700.264.598,73 − 1.
- Bảng (d): join_strategy/summary.csv, plan_check.csv; 12% = 83,996/74,920 − 1; auto r2 86,178, order_items 31,292: join_strategy/runs.csv. Bốn sort-merge còn lại: suy luận của người viết (plan_check chỉ có số đếm).
- Bảng (e): skew/summary.csv, plan_check.csv, partition_stats_summary.csv; 13% (13,3% và 12,8%); aggregates 23,38→12,90 và 22,16→13,11; dimensions 10,77→6,63 và 11,41→6,36; order_items 34,40 vs 34,85; auto order_items 26,63/22,58 và 28,85/22,17; 10,18 giây = 84,07 − 73,89 (verify-round1 mục C).
- 104 = 64 − 9 + 49: verify-round1 mục C; ảnh 07 và 10.
- Ảnh 07: 49 skewed partition splits; ảnh 09/10: 15,5 MiB / 1,5 MiB / 0,5 s và 1,9 MiB / 0,2 s, 64 và 104 task: results/logs/screenshots/README.md mục "Số đọc được trên ảnh" và chính ảnh.
- AQE gộp phân vùng sau shuffle: Spark SQL Performance Tuning 4.0.0.
- Bảng (f): cache/summary.csv, break_even.csv; tỉ lệ từng truy vấn người viết chia; 31% = 4,849/15,75; 8/8 phân vùng, 9.024.635 dòng, bộ nhớ 215,9/251,9/215,9 MiB, đĩa 41,0/20,5/41,0 MiB: cache/runs/cache/r1..r3/query_bench.json (verify-round1 mục C); InMemoryTableScan trong plan_after_run của r1.
- Mức mặc định của DataFrame.cache() là MEMORY_AND_DISK_DESER: PySpark 4.0.0 (verify-round1 mục C).
- Bảng (g): pandas_baseline/comparison_spark.csv, summary.csv; 49 checks, all_match True: pandas_baseline/runs.csv; 1,95 = 7,064/3,619; 1,28 = 27,936/21,895; ~8 GB ngoại suy = 1.682 × 5 (từ 1M lên 5M), chưa đo.
- Khác biệt môi trường Pandas/Spark: src/experiments/pandas_baseline/README.md.
- Speedup, efficiency (c2 tr. 21), Amdahl (c2 tr. 22), Parquet (c4 tr. 46, c5 tr. 44), broadcast (c5 tr. 51), cache (c5 tr. 31, 32): đã đối chiếu slide (report/review/verify-slides.md). Đã tính lại p ≈ 0,45: 1/1,29 = 0,775; p = 2 × (1 − 0,775).
-->
