# Phụ lục A. Lược đồ và số dòng dữ liệu

Phụ lục này ghi chi tiết của mục 3.2 và 3.3: lược đồ năm bảng, tập giá trị, ví dụ bản ghi thô và số dòng từng bảng. Toàn bộ là **dữ liệu mô phỏng**.

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

Một số tập giá trị (mô phỏng): `status` gồm pending 5%, paid 10%, shipped 15%, delivered 60%, cancelled 10%; `payment_method` gồm cod, card, bank_transfer, e_wallet chia đều; `event_type` gồm view 80%, add_to_cart 15%, purchase 5%; `region` có 6 giá trị; `category` có 8 giá trị; `quantity` từ 1 đến 5. Ngày đặt hàng nằm trong 2024-01-01 đến 2025-12-31 (731 ngày); ngày đăng ký khách hàng nằm trong 2020 đến 2023.

Ví dụ bản ghi thô (trích từ mẫu của bộ `orders_5m`, dữ liệu mô phỏng):

```
orders:      30,25619,2024-07-24,paid,e_wallet
order_items: 19,3,17912,2,51.37
customers:   32,,2023-09-21        (region bị thiếu)
```

Nguồn ví dụ: `results/samples/orders_5m/duplicates_orders.csv`, `duplicates_order_items.csv`, `missing_region_customers.csv`.

## A.2 Số dòng thô theo từng bảng

Bảng: Số dòng thô của năm bộ dữ liệu (đã gồm dòng trùng chèn thêm) {#tbl:kich-thuoc-bo}

| Bộ dữ liệu | customers | products | orders | order_items | web_events | Tổng |
|---|---|---|---|---|---|---|
| orders_500k | 51.000 | 2.000 | 510.000 | 1.019.960 | 510.000 | 2.092.960 |
| orders_1m | 102.000 | 4.000 | 1.020.000 | 2.038.974 | 1.020.000 | 4.184.974 |
| orders_2500k | 255.000 | 10.000 | 2.550.000 | 5.099.824 | 2.550.000 | 10.464.824 |
| orders_5m | 510.000 | 20.000 | 5.100.000 | 10.201.505 | 5.100.000 | 20.931.505 |
| orders_5m_skew | 510.000 | 20.000 | 5.100.000 | 10.200.359 | 5.100.000 | 20.930.359 |

Nguồn: results/metrics/orders_500k.json, orders_1m.json, orders_2500k.json, orders_5m.json, orders_5m_skew.json (trường `tables.*.raw_rows`); cột Tổng khớp `raw_rows_total` trong results/metrics/scale_data/summary.csv

<!-- VERIFY
- Lược đồ: docs/design/schema.md, src/etl/schemas.py.
- Tỉ lệ status/payment/event_type/quantity, 731 ngày, ngày đăng ký 2020–2023: src/data_generation/config.py.
- Ví dụ bản ghi thô: các tệp CSV nêu trong dòng nguồn.
- Bảng số dòng thô: results/metrics/orders_*.json; khớp rows_written trong results/metrics/datasets/datasets_summary.csv; tổng khớp raw_rows_total ở results/metrics/scale_data/summary.csv (500k, 1m, 2500k, 5m) và raw_rows_total 20.930.359 ở results/metrics/skew/runs.csv (skew).
-->
