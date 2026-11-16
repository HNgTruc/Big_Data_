# Phụ lục A. Lược đồ và số dòng dữ liệu

Chi tiết của mục 3.2 đến 3.5, toàn bộ là dữ liệu mô phỏng.

## A.1 Lược đồ năm bảng

Bảng: Lược đồ năm bảng dữ liệu mô phỏng {#tbl:luoc-do}

| Bảng | Định dạng | Cột (kiểu) | Vai trò |
|---|---|---|---|
| `orders` | CSV | `order_id` (long), `customer_id` (long), `order_date` (date), `status` (string), `payment_method` (string) | Bảng sự kiện chính |
| `order_items` | CSV | `order_id` (long), `line_no` (int), `product_id` (long), `quantity` (int), `unit_price` (double) | Dòng hàng; khoá (`order_id`, `line_no`) |
| `customers` | CSV | `customer_id` (long), `region` (string), `signup_date` (date) | Chiều khách hàng, dùng tổng hợp theo khu vực |
| `products` | Parquet | `product_id` (long), `category` (string), `list_price` (double) | Chiều sản phẩm, bảng nhỏ |
| `web_events` | JSON lines | `event_id` (string), `event_time` (timestamp), `customer_id` (long), `product_id` (long), `event_type` (string) | Sự kiện truy cập web |

Nguồn: docs/design/schema.md, src/etl/schemas.py

Tập giá trị (mô phỏng):

- `status`: pending 5%, paid 10%, shipped 15%, delivered 60%, cancelled 10%.
- `payment_method`: cod, card, bank_transfer, e_wallet chia đều.
- `event_type`: view 80%, add_to_cart 15%, purchase 5%.
- `region` có 6 giá trị, `category` có 8 giá trị, `quantity` từ 1 đến 5.
- Ngày đặt hàng trong 2024-01-01 đến 2025-12-31 (731 ngày), ngày đăng ký khách hàng trong 2020 đến 2023.

Ví dụ bản ghi thô (trích từ mẫu của bộ `orders_5m`, dữ liệu mô phỏng):

```
orders:      30,25619,2024-07-24,paid,e_wallet
order_items: 19,3,17912,2,51.37
customers:   32,,2023-09-21        (region bị thiếu)
```

Nguồn ví dụ: `results/samples/orders_5m/duplicates_orders.csv`, `duplicates_order_items.csv`, `missing_region_customers.csv`.

## A.2 Số dòng thô theo từng bảng

Tỉ lệ mặc định theo số đơn: `customers` bằng 1/10 số đơn, `products` bằng max(100, số đơn/250), `web_events` bằng số đơn, `order_items` trung bình khoảng 2 dòng mỗi đơn. Bộ sinh thêm dòng trùng chứ không thay thế, nên số dòng ghi ra lớn hơn số dòng gốc khoảng 2%.

Bảng: Số dòng thô của năm bộ dữ liệu (đã gồm dòng trùng chèn thêm) {#tbl:kich-thuoc-bo}

| Bộ dữ liệu | customers | products | orders | order_items | web_events | Tổng |
|---|---|---|---|---|---|---|
| orders_500k | 51.000 | 2.000 | 510.000 | 1.019.960 | 510.000 | 2.092.960 |
| orders_1m | 102.000 | 4.000 | 1.020.000 | 2.038.974 | 1.020.000 | 4.184.974 |
| orders_2500k | 255.000 | 10.000 | 2.550.000 | 5.099.824 | 2.550.000 | 10.464.824 |
| orders_5m | 510.000 | 20.000 | 5.100.000 | 10.201.505 | 5.100.000 | 20.931.505 |
| orders_5m_skew | 510.000 | 20.000 | 5.100.000 | 10.200.359 | 5.100.000 | 20.930.359 |

Nguồn: results/metrics/orders_500k.json, orders_1m.json, orders_2500k.json, orders_5m.json, orders_5m_skew.json (trường `tables.*.raw_rows`); cột Tổng khớp `raw_rows_total` trong results/metrics/scale_data/summary.csv

Dung lượng tệp thô của bộ `orders_5m` theo từng bảng là `customers.csv` 12,90 MB, `orders.csv` 216,90 MB, `order_items.csv` 235,52 MB, `products.parquet` 0,20 MB, `web_events.jsonl` 624,17 MB (nguồn: `results/metrics/format_compare/sizes.csv`, đo bằng Hadoop `FileSystem.getContentSummary` trên MinIO, khớp `datasets_summary.csv`).

## A.3 Lỗi được chèn

Bảng: Các loại lỗi được chèn theo bảng {#tbl:loi-chen}

| Loại lỗi | Cách chèn | Bảng bị chèn |
|---|---|---|
| Bản ghi trùng | Thêm bản sao đầy đủ của một dòng có sẵn | `orders`, `order_items`, `customers`, `web_events` |
| Giá trị thiếu | Để rỗng `customer_id`, `unit_price`, `region` | `orders`, `order_items`, `customers`, `web_events` |
| Giá trị không hợp lệ | `quantity` = 0, `unit_price` âm, khoá ngoại mồ côi (`customer_id`, `product_id` không tồn tại) | `orders`, `order_items` |
| Sai định dạng ngày | Ngày dạng `dd/mm/yyyy`, `yyyymmdd`, `dd-mm-yyyy`; thời gian dạng `dd/mm/yyyy HH:MM:SS`, `yyyymmddHHMMSS` (chuẩn là ISO) | `orders`, `customers`, `web_events` |

Nguồn: docs/design/schema.md (mục "Định dạng lỗi ngày được chèn"), src/data_generation/README.md

Số lỗi đo được sau ETL trên `orders_5m` cho thấy tỉ lệ thực tế sát 2% (nguồn: `results/metrics/orders_5m.json`, các tỉ lệ do nhóm chia):

- `orders`: 100.000 dòng trùng trên 5.000.000 đơn gốc, 99.579 đơn thiếu `customer_id`, 100.377 đơn có `customer_id` mồ côi.
- `order_items`: 200.030 dòng trùng trên 10.001.475 dòng hàng gốc.

Bộ sinh chèn vào `orders_5m` 99.949 dòng sai định dạng ở `order_date`, 100.375 ở `event_time` và 9.847 ở `signup_date` (cột `defects_injected`, các trường `bad_order_date`, `bad_event_time`, `bad_signup_date` trong `results/metrics/datasets/datasets_summary.csv`).

## A.4 Độ lệch khoá

Bộ `orders_5m_skew` dùng `hot_share` = 0,5 và `hot_products` = 10 trên tổng số 20.000 sản phẩm. Cột bị lệch là `product_id` trong `order_items` và `web_events`, còn `order_id`, `customer_id` và ngày không bị lệch. Hai bộ `orders_5m` và `orders_5m_skew` có số dòng gần như bằng nhau (@tbl:kich-thuoc-tong), nên khác biệt giữa chúng chủ yếu nằm ở phân bố khoá.

Khi băm `order_items` theo `product_id` vào 64 phân vùng, phân vùng lớn nhất của bộ lệch là 16,2 MB so với trung vị 1,54 MB (gấp 10,54 lần) và có 9 phân vùng vượt 5 lần trung vị. Ở bộ cân bằng, tỉ số là 1,18 và không phân vùng nào vượt 5 lần trung vị (nguồn: `results/metrics/skew/partition_stats_summary.csv`, bảng đầy đủ ở @tbl:partition-stats, Phụ lục D). Nhóm dùng phép đo này làm căn cứ chọn tham số cho thí nghiệm (e) (mục B.6, D.12).

<!-- VERIFY
- Lược đồ: docs/design/schema.md, src/etl/schemas.py.
- Tỉ lệ status/payment/event_type/quantity, 731 ngày, ngày đăng ký 2020–2023: src/data_generation/config.py.
- Ví dụ bản ghi thô: các tệp CSV nêu trong dòng nguồn.
- Bảng số dòng thô: results/metrics/orders_*.json; khớp rows_written trong results/metrics/datasets/datasets_summary.csv; tổng khớp raw_rows_total ở results/metrics/scale_data/summary.csv (500k, 1m, 2500k, 5m) và raw_rows_total 20.930.359 ở results/metrics/skew/runs.csv (skew).
- customers = orders/10, products = max(100, orders/250), web_events = orders: config.py (n_customers, n_products, n_events).
- Dung lượng tệp thô orders_5m từng bảng: results/metrics/format_compare/sizes.csv.
- bad_order_date 99.949; bad_event_time 100.375; bad_signup_date 9.847: results/metrics/datasets/datasets_summary.csv.
- 99.579 / 100.377 / 100.000 / 200.030: results/metrics/orders_5m.json; 10.001.475 = 10.201.505 − 200.030.
- Tỉ số 10,54; 16,2 MB; 1,54 MB; 9 phân vùng; 1,18: results/metrics/skew/partition_stats_summary.csv (partitions = 64).
- hot_share 0,5, hot_products 10, 20.000 sản phẩm: config.py, src/experiments/skew/README.md.
- Bảng lỗi chèn: docs/design/schema.md dòng "Lỗi chèn".
-->
