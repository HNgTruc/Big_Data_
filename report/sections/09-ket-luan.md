# Chương 9. Kết luận

Đồ án đã triển khai đoạn Storage → Processing cho dữ liệu giao dịch thương mại điện tử mô phỏng, dùng PySpark và MinIO. Kết quả theo các mục tiêu ở mục 1.2 như sau.

**Job xử lý và kiểm chứng (mục tiêu 1, 2).** Job đã chạy trên cả năm bộ dữ liệu. Với `orders_5m`, 20.931.505 dòng thô cho 19.244.742 dòng sạch, 1.276.733 dòng cách ly và 410.030 dòng trùng đã bỏ. Số dòng trùng và các lý do cách ly trực tiếp khớp số lỗi đã chèn ở cả năm bộ (mục 6.3).

**Khả năng mở rộng (mục tiêu 3).** Dữ liệu tăng 10 lần thì thời gian xử lý tăng 3,52 lần. Thêm worker từ 1 lên 2 chỉ đạt speedup 1,29, efficiency 0,64 (mục 6.4, 6.5).

**Tối ưu và so sánh (mục tiêu 4).** Parquet nhanh hơn dữ liệu thô 2,1–2,7 lần. Ép sort-merge join chậm hơn khoảng 12% so với `broadcast`. Cache hoà vốn sau khoảng 3,1 truy vấn. Trái giả thuyết, lệch khoá không làm job chậm rõ rệt (tỉ lệ 0,95–1,09), dù AQE có tách join lệch. Pandas nhanh hơn Spark 6,1 lần ở bộ 500k và 4,0 lần ở bộ 1M, trong hai môi trường khác nhau (mục 6.6 đến 6.10).

**Tái lập (mục tiêu 5).** Cả 69 lần chạy đều có bản ghi lệnh, commit và số đo trong `results/`; không lần nào bị loại. Các bước tái lập ở Phụ lục F.

**Hạn chế cốt lõi.** Dữ liệu là dữ liệu mô phỏng. Mọi thí nghiệm chạy trên một máy vật lý, heap executor 1 GB, RAM host sát trong lúc đo, mỗi cấu hình chỉ lặp 3 lần. Nguyên nhân của speedup thấp phần lớn còn là suy đoán (mục 8.2). Kết quả chỉ có giá trị trong môi trường này, không thể ngoại suy trực tiếp sang cụm thật.

**Hướng tiếp theo.** Bước gần nhất là chạy trên nhiều máy thật với nhiều mức worker, ghi thêm số liệu CPU, I/O, spill cho thí nghiệm (b), tăng số lần lặp, và tăng mức lệch để tìm điểm skew thành nút cổ chai (mục 8.6).

<!-- VERIFY
- 20.931.505 / 19.244.742 / 1.276.733 / 410.030: @tbl:chat-luong-5m, results/samples/orders_5m/summary.csv.
- Khớp số lỗi ở cả năm bộ: docs/design/etl.md, mục 6.3.
- 3,52; 1,29; 0,64; 2,1–2,7; 12%; 0,95–1,09; 3,1; 6,1; 4,0: mục 6.4 đến 6.11.
- Không có kết luận ngoài chương 6, 8.
-->
