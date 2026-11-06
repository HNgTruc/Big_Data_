---
name: new-experiment
description: Tạo khuôn một thí nghiệm lặp lại được (cấu hình, lệnh chạy, nơi lưu log và số đo). Dùng khi thêm thí nghiệm mới như mở rộng theo dữ liệu, theo worker, CSV so với Parquet, broadcast join, skew, cache.
argument-hint: "<tên-thí-nghiệm>"
---

# Tạo thí nghiệm mới

Đầu vào: tên thí nghiệm (chữ thường, gạch ngang). Gọi là `<exp>`.

## Các bước
1. Hỏi người dùng nếu thiếu: giả thuyết, biến thay đổi, biến giữ cố định, chỉ số đo.
2. Tạo `src/experiments/<exp>/` gồm `README.md` (mục tiêu, giả thuyết, cách chạy, kết quả mong đợi để so sánh)
   và `run.py` (nhận tham số dòng lệnh, ghi số đo ra `results/metrics/<exp>/`).
3. Quy ước đầu ra: log vào `results/logs/<exp>/`, số đo dạng CSV nhỏ vào `results/metrics/<exp>/`,
   hình vào `results/figures/<exp>/`. Mỗi thư mục con mới cũng cần README.
4. Mỗi lần chạy ghi lại: ngày giờ, phiên bản Spark, số worker, kích thước dữ liệu, seed, lệnh chạy.
5. Chạy nhiều lần (ít nhất 3) và ghi cả giá trị từng lần, không chỉ trung bình.
6. Số đo thật chỉ được ghi sau khi chạy xong. Chưa chạy thì để trạng thái "chưa chạy".

## Lưu ý
- Giới hạn tài nguyên (Docker/WSL 6 GB trên máy 16 GB): dùng kích thước dữ liệu phù hợp và nêu giới hạn trong README thí nghiệm.
- Không sửa số đo bằng tay; nếu cần loại một lần chạy, ghi lý do.
