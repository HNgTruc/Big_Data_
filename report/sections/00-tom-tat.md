# Tóm tắt

Đồ án đánh giá hiệu năng của giai đoạn Storage → Processing trên dữ liệu giao dịch thương mại điện tử: làm sạch, chuẩn hoá, kết nối và tổng hợp năm bảng bằng PySpark và MinIO. Dữ liệu là dữ liệu mô phỏng sinh bằng script, từ 0,5 đến 5 triệu đơn hàng (tối đa khoảng 20,9 triệu dòng thô), có chèn 2% lỗi mỗi loại và một biến thể lệch khoá. Hệ thống gồm cụm Spark standalone 2 worker chạy bằng Docker Compose trên một máy, với giới hạn 6 GB RAM cho WSL2. Đồ án thực hiện 7 thí nghiệm, tổng cộng 69 lần chạy. Số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp số lỗi đã chèn. Khi dữ liệu tăng 10 lần, thời gian xử lý tăng 3,52 lần. Hai worker chỉ đạt speedup 1,29 và efficiency 0,64. Parquet nhanh hơn dữ liệu thô 2,1–2,7 lần; cache hoà vốn sau khoảng 3,1 truy vấn. Trái giả thuyết ở biến thể ép shuffle, lệch khoá không làm job chậm rõ rệt (tỉ lệ 0,95–1,09 ở cả 4 cặp) dù AQE có tách join lệch. Pandas nhanh hơn Spark 6,1 lần ở bộ 500k và 4,0 lần ở bộ 1M, trong hai môi trường khác nhau. Hạn chế chính: một máy vật lý, RAM host sát trong lúc đo và mỗi cấu hình chỉ lặp 3 lần, nên kết quả không thể ngoại suy trực tiếp sang cụm thật.

<!-- VERIFY
- 0,5–5 triệu đơn, 20,9 triệu dòng thô (20.931.505): @tbl:kich-thuoc-tong, results/metrics/datasets/datasets_summary.csv.
- 2% mỗi loại, biến thể lệch khoá: mục 3.4, 3.5.
- Cụm 2 worker, 6 GB: mục 3.8, results/logs/environment.txt.
- 7 thí nghiệm, 69 lần chạy: mục 4.6, results/metrics/*/runs.csv.
- Số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp số lỗi đã chèn: mục 5.4, 6.3, docs/design/etl.md. `no_clean_order` là hệ quả dây chuyền, không tính (verify-round2 A2).
- Trái giả thuyết ở biến thể ép shuffle; vế `auto` không bị bác: mục 6.8 (verify-round2 F2).
- 3,52: results/metrics/scale_data/summary.csv. 1,29 và 0,64: results/metrics/scale_workers/summary.csv.
- 2,1–2,7: results/metrics/format_compare/summary.csv. 3,1 truy vấn: results/metrics/cache/break_even.csv (3,12).
- 0,95–1,09: results/metrics/skew/summary.csv. AQE tách join lệch: results/metrics/skew/plan_check.csv.
- 6,1 và 4,0: mục 6.10, 6.11; results/metrics/pandas_baseline/comparison_spark.csv (6,05 và 3,95).
- RAM host sát: mục 6.1.
- Không có bảng, hình, trích dẫn trong thân tóm tắt.
-->
