# Thiết kế job ETL (Storage → Processing)

Trạng thái: đã chạy trên cụm cả 5 bộ (`orders_500k` đến `orders_5m_skew`) với schema có `line_no` (2026-11-07); số dòng loại bỏ và quarantine khớp hoàn toàn với `manifest.json`. Mã ở `src/etl/`. Quy tắc dưới đây là **lựa chọn thiết kế của dự án** cho dữ liệu mô phỏng.

## Luồng

`s3a://bigdata/raw/<dataset>/` → làm sạch → `s3a://bigdata/curated/<run>/` (+ `quarantine/<run>/`) → tổng hợp → `curated/<run>/agg_*`.
Mỗi bảng sạch được ghi ra Parquet rồi **đọc lại** làm đầu vào cho bước sau (join), nên mỗi bước đo thời gian độc lập.

## Quy tắc làm sạch

| Bảng | Bỏ trùng | Đưa vào quarantine (`reject_reason`) | Sửa tại chỗ |
|---|---|---|---|
| `orders` | theo `order_id` | `null_customer_id`, `invalid_order_date`, `orphan_customer_id` | ngày sai định dạng → `yyyy-MM-dd` |
| `order_items` | theo khoá (`order_id`, `line_no`) | `null_unit_price`, `non_positive_quantity`, `non_positive_price`, `orphan_product_id`, `no_clean_order` | — |
| `customers` | theo `customer_id` | (không có) | `region` null → `unknown`; ngày chuẩn hoá |
| `web_events` | theo `event_id` | `null_customer_id`, `invalid_event_time` | thời gian sai định dạng → timestamp |
| `products` | — | — | — |

- Khi một dòng vi phạm nhiều quy tắc, quy tắc xếp trước trong bảng thắng.
- `no_clean_order`: dòng hàng thuộc đơn không còn trong bảng đơn sạch (đơn bị quarantine hoặc không tồn tại).
- Bốn định dạng ngày và ba định dạng thời gian được nhận diện bằng biểu thức chính quy rồi mới phân tích (xem `cleaning.py`); dữ liệu không khớp mẫu nào ra `NULL`.
- Cấu hình Spark: `spark.sql.ansi.enabled=false` và `spark.sql.legacy.timeParserPolicy=CORRECTED`, vì Spark 4 bật ANSI mặc định (ngày sai sẽ báo lỗi thay vì trả `NULL`).

## Hạn chế đã biết (cần nêu trong báo cáo)

- `order_items` bỏ trùng theo khoá (`order_id`, `line_no`); `line_no` = 1..k trong mỗi đơn và không bị chèn lỗi. Hai dòng hàng hợp lệ giống hệt nhau về sản phẩm, số lượng, giá nhưng khác `line_no` đều được giữ. Phiên bản trước (schema chưa có `line_no`) bỏ trùng theo cả dòng nên đã xoá nhầm các dòng như vậy, rõ nhất ở bộ lệch key; xem các mục kết quả bên dưới.
- Bỏ trùng theo khoá giữ dòng đầu tiên Spark gặp trong mỗi khoá. Điều này đúng vì dòng trùng được chèn là bản sao đầy đủ; nếu hai dòng cùng khoá mà khác nội dung thì một dòng bị bỏ mà không vào quarantine.
- Dòng trùng ở `orders`, `customers`, `web_events` cũng được bỏ theo khoá.
- Sai ngày được **sửa** chứ không loại; chỉ dữ liệu không nhận diện được định dạng mới ra `NULL` (rồi vào quarantine với `orders`).

## Tổng hợp

- `agg_daily_revenue`: số đơn và doanh thu theo ngày.
- `agg_revenue_by_region_category`: doanh thu và số lượng theo khu vực × danh mục (join đủ 4 bảng).
- `agg_events_daily`: số sự kiện theo ngày và loại.
- Doanh thu chỉ tính đơn có trạng thái `paid`, `shipped`, `delivered`; doanh thu = `quantity × unit_price`.

## Chỉ số ghi ra (`results/metrics/<run>.json`)

Cấu hình Spark, thời gian từng giai đoạn và `processing_seconds_total` (không gồm bước thống kê), số dòng thô/sạch/quarantine theo lý do cho từng bảng, số dòng bảng tổng hợp.
Thời gian chỉ có ý nghĩa so sánh khi cùng máy, cùng cấu hình cụm.

## Tham số thí nghiệm

`--join-strategy auto|broadcast|shuffle`, `--shuffle-partitions N`, `--no-aqe`, `--no-auto-broadcast`.

## Kết quả với schema có `line_no` (2026-11-07, cụm 2 worker × 2 lõi, Spark 4.0.0, cấu hình mặc định)

Nguồn: `results/metrics/<bộ>.json`, `results/logs/etl_<bộ>.log`; dữ liệu sinh lại với seed 42 (`data/raw/<bộ>/manifest.json`). Mỗi bộ chạy một lần, máy không ở trạng thái sạch (VS Code, Docker của dự án khác vẫn chạy), nên thời gian chỉ để tham khảo; số đo chính thức lấy từ bộ thí nghiệm có lặp lại.

| Bộ dữ liệu | dimensions | orders | order_items | web_events | aggregates | Tổng (giây) |
|---|---|---|---|---|---|---|
| orders_500k | 7,32 | 7,32 | 6,83 | 5,93 | 5,96 | 33,36 |
| orders_1m | 4,07 | 8,38 | 7,97 | 8,72 | 6,32 | 35,46 |
| orders_2500k | 7,58 | 12,85 | 14,96 | 13,52 | 10,21 | 59,12 |
| orders_5m | 10,70 | 21,41 | 34,39 | 25,39 | 11,46 | 103,36 |
| orders_5m_skew | 8,69 | 18,94 | 31,21 | 24,13 | 11,75 | 94,72 |

Đối chiếu tự động với manifest cho cả 5 bộ: số dòng thô của 5 bảng, số dòng trùng đã bỏ của `customers`, `orders`, `order_items`, `web_events`, và từng lý do quarantine (`null_customer_id`, `orphan_customer_id`, `null_unit_price`↔`zero_quantity`/`negative_unit_price`, `orphan_product_id`) **đều khớp, không lệch dòng nào**. Không có dòng nào bị loại vì ngày/thời gian sai định dạng.

- Với `orders_5m_skew`: `order_items` bỏ đúng 200.008 dòng trùng (schema cũ: 255.378), các lý do quarantine bằng đúng số đã chèn (schema cũ hụt 41 dòng). Thêm khoá đã loại bỏ hoàn toàn sai lệch.
- `no_clean_order` (dòng hàng thuộc đơn bị quarantine): 37.789 / 75.509 / 188.148 / 376.230 / 376.787 cho 5 bộ theo thứ tự trên.
- `orders_5m_skew` chạy nhanh hơn `orders_5m` trong lần này (94,72 so với 103,36 giây). Một lần đo trong điều kiện không sạch không đủ để kết luận về ảnh hưởng của skew.

> Các mục kết quả dưới đây được tạo với **schema cũ** (bỏ trùng `order_items` theo cả dòng, chưa có `line_no`). File metrics tương ứng đã bị ghi đè; bản cũ còn trong commit `993d30b` (`results/metrics/`, `results/logs/`). Giữ lại làm bằng chứng cho hạn chế của cách bỏ trùng theo cả dòng.

## Kết quả chạy đầu tiên (`orders_500k`, cụm 2 worker × 2 lõi, Spark 4.0.0)

Nguồn: `results/metrics/orders_500k.json`. Thời gian một lần chạy, chưa lặp lại, chưa có baseline nên chưa kết luận hiệu năng.

- Tổng thời gian xử lý 24,07 giây (dimensions 4,87; orders 6,22; order_items 4,39; web_events 4,18; aggregates 4,41).
- Số dòng bị loại khớp đúng số lỗi generator đã chèn (`manifest.json`): `orders` null_customer_id 9.837 và orphan_customer_id 10.176; `order_items` null_unit_price 19.871, non_positive_quantity 9.931, non_positive_price 9.967, orphan_product_id 19.769; `web_events` null_customer_id 9.966; dòng trùng `orders` 10.000, `web_events` 10.000, `customers` 1.000.
- `order_items`: bỏ 20.111 dòng trùng trong khi đã chèn 19.999; chênh 112 dòng (≈0,011%) là dòng hàng hợp lệ lặp lại bị xoá nhầm, đúng hạn chế ghi ở trên.
- `no_clean_order` = 37.787 dòng hàng: hệ quả dây chuyền của 20.013 đơn bị quarantine.
- Bảng tổng hợp: 731 ngày, 56 nhóm khu vực × danh mục (6 khu vực + `unknown`, × 8 danh mục), 2.193 nhóm sự kiện (731 ngày × 3 loại).

## Kết quả `orders_1m`, `orders_2500k`, `orders_5m` (cùng cụm, cấu hình mặc định)

Nguồn: `results/metrics/orders_1m.json`, `orders_2500k.json`, `orders_5m.json`; log `results/logs/etl_orders_2500k.log`, `etl_orders_5m.log`. Mỗi bộ chạy một lần, chưa lặp lại.
Lần chạy `orders_5m` diễn ra khi RAM trống của máy chủ chỉ còn khoảng 0,6 GB (VS Code dùng khoảng 1,9 GB), nên chỉ dùng để kiểm tra tính đúng; số đo thời gian chính thức phải chạy lại.

| Bộ dữ liệu | dimensions | orders | order_items | web_events | aggregates | Tổng (giây) |
|---|---|---|---|---|---|---|
| orders_1m | 7,20 | 7,63 | 6,55 | 7,42 | 5,34 | 34,14 |
| orders_2500k | 9,44 | 12,89 | 16,64 | 15,23 | 8,94 | 63,14 |
| orders_5m | 9,30 | 16,85 | 35,16 | 22,79 | 11,79 | 95,90 |

Đối chiếu `orders_5m` với manifest: số dòng thô, các lý do quarantine (`orders` 99.579 + 100.377; `order_items` 200.700 / 99.603 / 99.817 / 200.490; `web_events` 99.937) và dòng trùng theo khoá (`orders` 100.000, `web_events` 100.000, `customers` 10.000) khớp hoàn toàn. `order_items` bỏ 200.143 dòng trùng so với 200.030 đã chèn, chênh 113 dòng (≈0,001%). Không có dòng nào bị loại vì ngày sai định dạng.

## Kết quả `orders_5m_skew` (bật lệch key: 50% lượt chọn sản phẩm rơi vào 10 sản phẩm)

Nguồn: `results/metrics/orders_5m_skew.json`, log `results/logs/etl_orders_5m_skew.log`. Chạy một lần.

| Bộ dữ liệu | dimensions | orders | order_items | web_events | aggregates | Tổng (giây) |
|---|---|---|---|---|---|---|
| orders_5m_skew | 25,07 | 37,44 | 38,80 | 33,18 | 16,66 | 151,14 |

**Không dùng thời gian này để kết luận về skew.** Trong lúc chạy, RAM máy chủ dùng khoảng 95%, đĩa bận 100% và Windows Update (TiWorker) đang cài. Giai đoạn `dimensions` (customers, products) không phụ thuộc skew và có cùng kích thước với `orders_5m`, nhưng mất 25,07 giây so với 9,30 giây. Điều đó cho thấy tải nền đã làm chậm cả job. Thí nghiệm skew phải chạy lại trong điều kiện sạch, có lặp lại.

Đối chiếu với `data/raw/orders_5m_skew/manifest.json`:

- Khớp hoàn toàn: số dòng thô 5 bảng; `orders` null_customer_id 100.446, orphan_customer_id 99.809; `web_events` null_customer_id 99.662; `order_items` orphan_product_id 199.990; dòng trùng `orders` 100.000, `web_events` 100.000, `customers` 10.000.
- `order_items` bỏ 255.378 dòng trùng so với 200.008 dòng đã chèn, thừa 55.370 dòng (≈0,54% của 10.200.359 dòng). Nguyên nhân nằm ở bộ sinh (`src/data_generation/tables.py`): `unit_price` là giá niêm yết cố định theo sản phẩm, `quantity` lấy từ một tập nhỏ, nên khi 50% lượt chọn dồn vào 10 sản phẩm thì hai dòng hàng hợp lệ trong cùng một đơn thường trùng nhau hoàn toàn và bị xoá. Đây là hạn chế bỏ trùng theo cả dòng đã nêu ở trên, lớn hơn khoảng 490 lần so với bộ không lệch (113 dòng).
- Cũng vì thế, quarantine của `order_items` hụt nhẹ so với số lỗi chèn: null_unit_price 200.242/200.267 (−25), non_positive_quantity 100.098/100.109 (−11), non_positive_price 100.049/100.054 (−5). Giải thích hợp lý nhất là hai dòng lỗi khác nhau trở thành giống hệt (cùng đơn, cùng sản phẩm nóng, cùng số lượng, cùng loại lỗi) và bị gộp ở bước bỏ trùng trước khi gắn lý do. Chưa kiểm chứng trực tiếp trên dữ liệu.
- Hướng khắc phục nếu cần: sinh thêm khoá `item_id` (hoặc `line_no`) cho `order_items` và bỏ trùng theo khoá. Chưa thực hiện; cần quyết định có đổi schema hay không. (Cập nhật sau: người dùng đã duyệt, đã thêm `line_no`; xem mục "Quy tắc làm sạch".)

Đối chiếu `orders_2500k` với `data/raw/orders_2500k/manifest.json`:

- Số dòng thô bằng `rows_written` ở cả 5 bảng.
- Quarantine khớp đúng số lỗi đã chèn: `orders` null_customer_id 49.748, orphan_customer_id 50.224; `order_items` null_unit_price 99.823, non_positive_quantity 49.708, non_positive_price 50.188, orphan_product_id 100.342; `web_events` null_customer_id 50.050.
- Dòng trùng: `orders` 50.000, `web_events` 50.000, `customers` 5.000, khớp số đã chèn. `order_items` bỏ 100.100 dòng so với 99.997 dòng đã chèn; chênh 103 dòng (≈0,002% của 5.099.824 dòng) là dòng hàng hợp lệ lặp lại, đúng hạn chế nêu ở trên. Với `orders_1m` con số tương ứng là 40.079 so với 39.980, chênh 99 dòng.
- Ngày sai định dạng (`bad_order_date` 49.978, `bad_event_time` 50.441, `bad_signup_date` 5.052) đều được chuẩn hoá; không có dòng nào bị loại với lý do `invalid_order_date` hoặc `invalid_event_time`.
- `no_clean_order` = 188.145 dòng hàng, là hệ quả dây chuyền của 99.972 đơn bị quarantine.
