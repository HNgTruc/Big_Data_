# Chương 1. Giới thiệu

## 1.1 Bối cảnh và vấn đề

Giao dịch thương mại điện tử và hành vi trên web là hai nguồn dữ liệu tiêu biểu (slide chương 1, tr. 9 [@slide-c1]). Theo slide, bài toán trở thành dữ liệu lớn khi kích thước, tốc độ, độ đa dạng hoặc độ phức tạp khiến cách làm truyền thống không còn phù hợp, và không có ngưỡng dung lượng cố định (slide chương 1, tr. 7 [@slide-c1]).

Spark phù hợp với ETL và làm sạch dữ liệu lớn, nhưng ở workload nhỏ, chi phí phân tán có thể lớn hơn lợi ích (slide chương 5, tr. 9 [@slide-c5]). Đồ án định lượng điều đó trên một cụm nhỏ: thêm dữ liệu, thêm worker, đổi định dạng, đổi chiến lược join, dùng cache hay gặp dữ liệu lệch khoá thì thời gian xử lý thay đổi bao nhiêu, và vì sao.

## 1.2 Mục tiêu

1. Xây dựng job PySpark đọc năm bảng từ MinIO, làm sạch, chuẩn hoá, kết nối, tổng hợp, ghi Parquet và tách bản ghi lỗi kèm lý do.
2. Kiểm chứng job bằng cách đối chiếu số dòng bị loại với số lỗi đã chèn.
3. Đo khả năng mở rộng theo kích thước dữ liệu và số worker.
4. Đo tác động của định dạng lưu trữ, chiến lược join, lệch khoá kết hợp AQE và cache; so sánh với Pandas một máy.
5. Bảo đảm tái lập được: lưu mã nguồn, cấu hình, lệnh chạy, log và số đo.

## 1.3 Phạm vi

- **Quy trình con:** Storage → Processing, ranh giới nêu ở mục 3.7. Bộ sinh dữ liệu và lệnh `mc cp` chỉ tạo đầu vào; Analytics và Presentation không thuộc phạm vi.
- **Dữ liệu:** dữ liệu mô phỏng sinh bằng script, xử lý theo lô.
- **Giới hạn máy:** một máy 16 GB RAM, Docker Desktop trên WSL2 giới hạn 6 GB, tối đa 2 worker và 5 triệu đơn (mục 3.8). Kết quả chỉ có giá trị trong môi trường này.

## 1.4 Đóng góp của đồ án

- Job ETL có vùng cách ly và thống kê chất lượng đối chiếu được với số lỗi đã chèn.
- Bộ bảy thí nghiệm, 69 lần chạy, mỗi lần có bản ghi lệnh, commit, cờ hợp lệ và số đo.
- Phân tích join và lệch khoá dựa trên kế hoạch thực thi đọc từ event log, không chỉ dựa vào cấu hình.
- Ghi nhận trung thực các kết quả không như mong đợi: lệch khoá không thành nút cổ chai, speedup thấp, Pandas nhanh hơn Spark ở bộ nhỏ.

## 1.5 Cấu trúc báo cáo

Chương 2 trình bày cơ sở và công nghệ; chương 3 mô tả dữ liệu và yêu cầu; chương 4, 5 trình bày thiết kế và cài đặt; chương 6 báo cáo kết quả đo; chương 7 là minh chứng demo; chương 8 thảo luận; chương 9 kết luận. Phụ lục A đến E chứa chi tiết, Phụ lục F hướng dẫn tái lập, Phụ lục G ghi chú việc dùng AI.

<!-- VERIFY
- Nguồn giao dịch, web/clickstream: slide chương 1, tr. 9.
- Định nghĩa theo kích thước, tốc độ, độ đa dạng, độ phức tạp; không có ngưỡng cố định: slide chương 1, tr. 7.
- Spark phù hợp ETL; workload nhỏ thì overhead lớn hơn lợi ích: slide chương 5, tr. 9.
- Giới hạn máy: mục 3.8, results/logs/environment.txt, .claude/CLAUDE.md.
- 69 lần chạy, bản ghi lần chạy: mục 4.6, Phụ lục B.
- Event log chỉ có ở thí nghiệm (d), (e): results/logs/README.md.
-->
