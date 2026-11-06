---
paths:
  - "src/**"
  - "tests/**"
---

# Chuẩn mã Python

- Python 3, tuân thủ PEP 8, có type hints cho hàm công khai, docstring ngắn nêu đầu vào/đầu ra.
- Tên biến, hàm, lớp, commit bằng tiếng Anh; comment ngắn gọn bằng tiếng Anh, chỉ giải thích "vì sao".
- Mỗi module một trách nhiệm; không để logic trong file chạy trực tiếp (dùng hàm `main()` và `if __name__ == "__main__"`).
- Tham số chạy (đường dẫn, kích thước dữ liệu, số worker, seed) đi qua tham số dòng lệnh hoặc file cấu hình, không viết cứng.
- Job Spark khai báo schema tường minh, không dùng `inferSchema` cho dữ liệu lớn.
- Dùng seed cố định cho dữ liệu sinh để tái lập được kết quả.
- Không in bí mật; thông tin đăng nhập MinIO lấy từ biến môi trường.
- Mỗi job có ít nhất một kiểm thử nhỏ trong `tests/` chạy trên dữ liệu mẫu bé.
