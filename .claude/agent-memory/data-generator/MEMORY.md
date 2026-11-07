# Bộ nhớ của agent data-generator

Agent tự cập nhật file này khi làm việc (giữ dưới 200 dòng). Chỉ ghi điều đã xác nhận.

## Quyết định đã được người dùng xác nhận (2026-11-06)
- Miền: thương mại điện tử, dữ liệu mô phỏng sinh bằng script.
- Schema: 5 bảng — chi tiết ở `docs/design/schema.md`.
- Dữ liệu bẩn: bản ghi trùng, giá trị thiếu, giá trị không hợp lệ, sai định dạng ngày.
- Kích thước `orders`: 0.5M, 1M, 2.5M, 5M dòng (Docker/WSL 6 GB, máy 16 GB).
- Dữ liệu bẩn 2% mỗi loại.
- `order_items` trung bình khoảng 2 dòng/đơn.
- Độ lệch key: có, tham số bật/tắt được.

## Đã làm (2026-11-06)
- Generator viết xong ở `src/data_generation/` (README ở đó); 11 test qua trên VM; 500k đơn chạy ~5 giây.
- Người dùng duyệt đề xuất: customers ≈ orders/10, products ≈ max(100, orders/250), web_events = orders, tập giá trị trong `config.py`, skew 50% vào 10 sản phẩm.
- Dữ liệu phụ thuộc `seed` và `chunk_size`; dòng trùng được thêm vào nên số dòng ghi ra ≈ +2%.
- (Đã lỗi thời) Trước đây chưa chạy trên máy người dùng; nay đã chạy đủ 5 bộ, xem mục dưới.

## Cập nhật 2026-11-07
- [order_items có khóa line_no](project_order_items_line_no.md) — cột, lý do, hợp đồng với ETL; 5 bộ đã sinh lại (seed 42, chunk 500k, 0.02).
- Lệnh sinh lại: `.venv\Scripts\python -m src.data_generation.generate --orders N [--skew] --overwrite` (mọi tham số khác mặc định).
- Máy người dùng: 12 test qua; 5M đơn sinh trong ~51 s.
