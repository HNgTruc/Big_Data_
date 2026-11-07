# datasets — kích thước và lỗi đã chèn của các bộ dữ liệu mô phỏng

- `datasets_summary.csv`: mỗi dòng một bảng của một bộ dữ liệu (`orders_500k`, `orders_1m`, `orders_2500k`, `orders_5m`, `orders_5m_skew`):
  số dòng đã ghi, dung lượng tệp thô (byte), seed, tỉ lệ lỗi, cờ lệch khoá, số lỗi đã chèn theo loại.
- Nguồn: chép nguyên từ `data/raw/<bộ>/manifest.json` (do `src/data_generation` sinh, được git theo dõi), không tính lại.
  Tạo ngày 2026-11-08 bằng một lệnh Python đọc 5 manifest và ghi CSV (không có script riêng vì chỉ là chép dữ liệu).
- Dữ liệu là dữ liệu mô phỏng.
