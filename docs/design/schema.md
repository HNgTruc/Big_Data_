# Schema dữ liệu mô phỏng (thương mại điện tử)

Trạng thái: **bộ 5 bảng đã được người dùng duyệt (2026-11-06)**. Kiểu dữ liệu và tập giá trị liệt kê dưới đây là **lựa chọn thiết kế của dự án**
cho dữ liệu mô phỏng, không phải dữ liệu thật; có thể chỉnh khi viết `data-generator`.

| Bảng | Định dạng | Cột | Ghi chú |
|---|---|---|---|
| `orders` | CSV | `order_id` (long), `customer_id` (long), `order_date` (date), `status` (string), `payment_method` (string) | Bảng sự kiện chính |
| `order_items` | CSV | `order_id` (long), `line_no` (int), `product_id` (long), `quantity` (int), `unit_price` (double) | Khóa (`order_id`, `line_no`), `line_no` = 1..k trong mỗi đơn; khóa ngoại tới `orders`, `products` |
| `customers` | CSV | `customer_id` (long), `region` (string), `signup_date` (date) | Dùng cho tổng hợp theo khu vực |
| `products` | Parquet | `product_id` (long), `category` (string), `list_price` (double) | Bảng nhỏ, dùng thử broadcast join |
| `web_events` | JSON lines | `event_id` (string), `event_time` (timestamp), `customer_id` (long), `product_id` (long), `event_type` (string) | Thể hiện Variety |

## Đặc trưng Big Data sẽ nêu (mục 5.2 của đề, cần ≥ 2)
- **Volume:** số dòng lớn, vượt khả năng xử lý thuận tiện bằng Pandas trên một máy (chứng minh bằng thí nghiệm baseline, không khẳng định trước).
- **Variety:** ba định dạng CSV, Parquet, JSON lines.
- **Veracity:** dữ liệu bẩn được chèn có kiểm soát.

## Loại dữ liệu bẩn sẽ chèn (người dùng đã chọn)
- Bản ghi trùng (`order_id`, `event_id`).
- Giá trị thiếu (null).
- Giá trị không hợp lệ: tiền hoặc số lượng âm/bằng 0; khóa ngoại mồ côi.
- Sai định dạng ngày (nhiều định dạng trong cùng cột).

Tỉ lệ: **2% mỗi loại** (người dùng chọn 2026-11-06), là tham số dòng lệnh của generator; tỉ lệ thực tế đã chèn phải được ghi lại cùng dữ liệu.

## Kích thước
- Mức tối đa người dùng chọn: **5 triệu dòng** ở bảng `orders` (Docker/WSL giới hạn 6 GB trên máy 16 GB RAM).
- Các mức cho thí nghiệm mở rộng theo dữ liệu: **0.5M, 1M, 2.5M, 5M** dòng `orders`.
- `order_items`: trung bình khoảng **2 dòng/đơn** (khoảng 10 triệu dòng ở mức 5M).
- **Độ lệch key:** có, bật/tắt bằng tham số; sinh được cả bản cân bằng lẫn bản lệch để so sánh (thí nghiệm skew).
- `customers` ≈ `orders`/10; `products` ≈ max(100, `orders`/250); `web_events` = `orders` (đề xuất của trợ lý, người dùng duyệt "ok rồi thực hiện đi" 2026-11-06; đều ghi đè được bằng tham số).
- Dòng trùng được **thêm vào** (không thay thế), nên số dòng ghi ra lớn hơn khoảng 2%.
- `line_no` được thêm (người dùng duyệt 2026-11-07) vì khi bật skew, các dòng hợp lệ khác nhau trong cùng đơn có thể trùng toàn bộ giá trị; có khóa thì khử trùng theo (`order_id`, `line_no`) chỉ xóa đúng dòng trùng đã chèn. Dòng trùng chèn vào là bản sao đầy đủ (cùng `order_id` và `line_no`); không chèn lỗi vào `line_no`.

## Tập giá trị liệt kê (lựa chọn thiết kế, mô phỏng)
Định nghĩa trong `src/data_generation/config.py`.
- `status`: pending 5%, paid 10%, shipped 15%, delivered 60%, cancelled 10%.
- `payment_method`: cod, card, bank_transfer, e_wallet (đều nhau).
- `event_type`: view 80%, add_to_cart 15%, purchase 5%.
- `region`: north, central, south, highland, mekong, southeast. `category`: 8 giá trị (xem `config.py`).
- `quantity`: 1–5 (50/25/12/8/5%). Ngày đơn 2024-01-01..2025-12-31; ngày đăng ký 2020..2023.
- Skew: `--skew` dồn `hot_share` = 50% lượt chọn sản phẩm vào 10 sản phẩm đầu (tham số chỉnh được).

## Định dạng lỗi ngày được chèn
Ngày: `dd/mm/yyyy`, `yyyymmdd`, `dd-mm-yyyy`. Thời gian: `dd/mm/yyyy HH:MM:SS`, `yyyymmddHHMMSS` (chuẩn là ISO `yyyy-mm-dd`, `yyyy-mm-dd HH:MM:SS`).
Lỗi chèn: orders (customer_id null / mồ côi, sai ngày), order_items (unit_price null, quantity=0, giá âm, product_id mồ côi), customers (region null, sai ngày), web_events (customer_id null, sai thời gian); trùng ở orders, order_items, customers, web_events; `products` sạch.
