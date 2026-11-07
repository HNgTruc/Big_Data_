# Chương 3. Dữ liệu và yêu cầu

Chương này mô tả đầu vào của giai đoạn Storage → Processing: nguồn dữ liệu, lược đồ năm bảng, kích thước các bộ dữ liệu, các loại lỗi được chèn có kiểm soát, rồi nêu yêu cầu chức năng, phi chức năng và giới hạn phần cứng của đồ án.

## 3.1 Nguồn dữ liệu

Đồ án dùng **dữ liệu mô phỏng** thuộc miền thương mại điện tử, sinh bằng script Python trong `src/data_generation/`. Đây không phải dữ liệu thật của bất kỳ doanh nghiệp nào; các phân phối (tỉ lệ trạng thái đơn, phương thức thanh toán, loại sự kiện, số lượng mỗi dòng hàng) là lựa chọn thiết kế của đồ án, khai báo trong `src/data_generation/config.py`.

Lý do chọn dữ liệu mô phỏng thay vì một bộ dữ liệu công khai:

- Điều khiển được kích thước (0,5 đến 5 triệu đơn) để đo khả năng mở rộng trong giới hạn phần cứng.
- Biết chính xác số lỗi đã chèn từng loại, nên kiểm chứng được job làm sạch: số dòng bị loại phải khớp đúng số lỗi đã chèn.
- Bật hoặc tắt được độ lệch khoá để làm thí nghiệm skew.

Bộ sinh dùng seed cố định 42 và kích thước khối (chunk) 500.000 dòng. Kết quả là hàm thuần của bộ tham số: cùng tham số cho ra cùng nội dung từng byte (theo `src/data_generation/README.md`). Mỗi bộ dữ liệu có tệp `manifest.json` ghi tham số, phiên bản thư viện, số dòng và số lỗi đã chèn từng loại.

Trong pipeline tổng quát Sources → Ingestion → Storage → Processing → Analytics → Presentation → Decision/Action, bộ sinh đóng vai trò nguồn (Sources). Bước Ingestion được thay bằng lệnh `mc cp` chép thư mục `data/raw/<bộ>/` lên vùng `raw/` của MinIO (mục 5.4). Phạm vi của đồ án bắt đầu từ khi dữ liệu thô đã nằm trên MinIO.

## 3.2 Lược đồ dữ liệu

Bộ dữ liệu gồm năm bảng, dùng ba định dạng khác nhau để thể hiện tính đa dạng (Variety).

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

Quan hệ giữa các bảng: `orders.customer_id` tham chiếu `customers`; `order_items.order_id` tham chiếu `orders`; `order_items.product_id` tham chiếu `products`. Cột `line_no` (số thứ tự dòng hàng 1..k trong mỗi đơn) được thêm vào sau một lần sửa thiết kế; lý do trình bày ở mục 4.5.

Ví dụ bản ghi thô (trích từ mẫu của bộ `orders_5m`, dữ liệu mô phỏng):

```
orders:      30,25619,2024-07-24,paid,e_wallet
order_items: 19,3,17912,2,51.37
customers:   32,,2023-09-21        (region bị thiếu)
```

Nguồn ví dụ: `results/samples/orders_5m/duplicates_orders.csv`, `duplicates_order_items.csv`, `missing_region_customers.csv`.

## 3.3 Kích thước các bộ dữ liệu

Kích thước được điều khiển bằng số đơn hàng. Các bảng còn lại suy ra theo tỉ lệ mặc định: `customers` bằng 1/10 số đơn, `products` bằng max(100, số đơn/250), `web_events` bằng số đơn, `order_items` trung bình khoảng 2 dòng mỗi đơn. Dòng trùng được **thêm vào** chứ không thay thế, nên số dòng ghi ra lớn hơn số dòng gốc khoảng 2%.

Bảng: Số dòng thô của năm bộ dữ liệu (đã gồm dòng trùng chèn thêm) {#tbl:kich-thuoc-bo}

| Bộ dữ liệu | customers | products | orders | order_items | web_events | Tổng |
|---|---|---|---|---|---|---|
| orders_500k | 51.000 | 2.000 | 510.000 | 1.019.960 | 510.000 | 2.092.960 |
| orders_1m | 102.000 | 4.000 | 1.020.000 | 2.038.974 | 1.020.000 | 4.184.974 |
| orders_2500k | 255.000 | 10.000 | 2.550.000 | 5.099.824 | 2.550.000 | 10.464.824 |
| orders_5m | 510.000 | 20.000 | 5.100.000 | 10.201.505 | 5.100.000 | 20.931.505 |
| orders_5m_skew | 510.000 | 20.000 | 5.100.000 | 10.200.359 | 5.100.000 | 20.930.359 |

Nguồn: results/metrics/orders_500k.json, orders_1m.json, orders_2500k.json, orders_5m.json, orders_5m_skew.json (trường `tables.*.raw_rows`); cột Tổng khớp `raw_rows_total` trong results/metrics/scale_data/summary.csv

Dung lượng tệp thô của bộ lớn nhất `orders_5m` (đo bằng Hadoop `FileSystem.getContentSummary` trên MinIO): `customers.csv` 12,90 MB, `orders.csv` 216,90 MB, `order_items.csv` 235,52 MB, `products.parquet` 0,20 MB, `web_events.jsonl` 624,17 MB, tổng khoảng 1,09 GB (1 MB = 10^6 byte; tổng do người viết cộng từ `results/metrics/format_compare/sizes.csv`). Dung lượng tệp thô của các bộ nhỏ hơn hiện chỉ có trong `data/raw/<bộ>/manifest.json`: [CHƯA CÓ: dung lượng tệp thô của orders_500k, orders_1m, orders_2500k chưa được sao vào results/].

## 3.4 Dữ liệu bẩn được chèn có kiểm soát

Để có bài toán làm sạch thực sự và kiểm chứng được kết quả, bộ sinh chèn bốn loại lỗi với tỉ lệ **2% mỗi loại** (tham số `--dirty-rate 0.02`). Các loại lỗi không chồng lên cùng một dòng. Bảng `products` được giữ sạch.

Bảng: Các loại lỗi được chèn theo bảng {#tbl:loi-chen}

| Loại lỗi | Cách chèn | Bảng bị chèn |
|---|---|---|
| Bản ghi trùng | Thêm bản sao đầy đủ của một dòng có sẵn | `orders`, `order_items`, `customers`, `web_events` |
| Giá trị thiếu | Để rỗng `customer_id`, `unit_price`, `region` | `orders`, `order_items`, `customers`, `web_events` |
| Giá trị không hợp lệ | `quantity` = 0, `unit_price` âm, khoá ngoại mồ côi (`customer_id`, `product_id` không tồn tại) | `orders`, `order_items` |
| Sai định dạng ngày | Ngày dạng `dd/mm/yyyy`, `yyyymmdd`, `dd-mm-yyyy`; thời gian dạng `dd/mm/yyyy HH:MM:SS`, `yyyymmddHHMMSS` (chuẩn là ISO) | `orders`, `customers`, `web_events` |

Nguồn: docs/design/schema.md (mục "Định dạng lỗi ngày được chèn"), src/data_generation/README.md

Số lỗi đo được sau ETL trên `orders_5m` cho thấy tỉ lệ thực tế sát 2%: 100.000 dòng trùng trên 5.000.000 đơn gốc của `orders`; 99.579 đơn thiếu `customer_id` và 100.377 đơn có `customer_id` mồ côi; 200.030 dòng trùng trên 10.001.475 dòng hàng gốc của `order_items` (nguồn: `results/metrics/orders_5m.json`; các tỉ lệ do người viết chia). Số dòng sai định dạng ngày đã chèn vào `orders_5m` chỉ ghi trong manifest: [CHƯA CÓ: số dòng `bad_order_date`, `bad_event_time`, `bad_signup_date` của orders_5m chưa có trong results/]. Chi tiết chất lượng dữ liệu trước và sau xử lý ở mục 6.3.

## 3.5 Độ lệch khoá

Bộ `orders_5m_skew` được sinh với cờ `--skew`: 50% số lượt chọn sản phẩm (`hot_share` = 0,5) dồn vào 10 sản phẩm đầu (`hot_products` = 10) trong tổng số 20.000 sản phẩm. Cột bị lệch là `product_id` trong `order_items` và `web_events`; `order_id`, `customer_id` và ngày không bị lệch. Hai bộ `orders_5m` và `orders_5m_skew` có số dòng gần như bằng nhau (@tbl:kich-thuoc-bo), nên khác biệt giữa chúng chủ yếu nằm ở phân bố khoá.

Mức lệch đo được khi băm `order_items` theo `product_id` vào 64 phân vùng: ở bộ lệch, phân vùng lớn nhất gấp 10,54 lần trung vị (16,2 MB so với 1,54 MB) và có 9 phân vùng vượt 5 lần trung vị; ở bộ cân bằng, tỉ số này là 1,18 và không phân vùng nào vượt 5 lần trung vị (nguồn: `results/metrics/skew/partition_stats_summary.csv`). Phép đo này là căn cứ chọn tham số cho thí nghiệm (e) ở mục 4.6 và 6.8.

## 3.6 Đặc trưng dữ liệu lớn

Đề yêu cầu chỉ ra ít nhất hai đặc trưng dữ liệu lớn (mục 5.2 của đề). Đồ án thể hiện ba đặc trưng sau, theo khái niệm 5V ở slide chương 1 [@slide-c1]:

- **Volume:** bộ lớn nhất có khoảng 20,9 triệu dòng thô và 1,09 GB tệp thô. Đây là quy mô khiêm tốn so với hệ thống thực tế, bị chặn bởi phần cứng (mục 3.8); đồ án không khẳng định đây là "dữ liệu lớn" theo nghĩa tuyệt đối mà dùng chuỗi kích thước tăng dần để quan sát xu hướng mở rộng.
- **Variety:** ba định dạng CSV, Parquet và JSON lines trong cùng một job.
- **Veracity:** dữ liệu có lỗi trùng, thiếu, không hợp lệ và sai định dạng ngày, phải làm sạch trước khi dùng.

Velocity không thuộc phạm vi: dữ liệu được xử lý theo lô (batch), không có luồng phát sinh liên tục.

## 3.7 Yêu cầu của giai đoạn Storage → Processing

**Ranh giới.** Giai đoạn bắt đầu khi dữ liệu thô đã có trong `s3a://bigdata/raw/<bộ>/` trên MinIO. Giai đoạn kết thúc khi các bảng sạch, bảng cách ly và ba bảng tổng hợp đã được ghi dưới dạng Parquet vào `curated/` và `quarantine/`, sẵn sàng cho giai đoạn Analytics phía sau. Đầu ra phụ là tệp chỉ số (metrics) JSON cho mỗi lần chạy.

**Yêu cầu chức năng:**

1. Đọc năm bảng thô từ MinIO qua giao thức S3A với lược đồ khai báo tường minh (không suy luận lược đồ).
2. Bỏ bản ghi trùng theo khoá của từng bảng.
3. Chuẩn hoá ngày và thời gian về định dạng ISO.
4. Tách bản ghi lỗi ra vùng cách ly (quarantine), mỗi dòng kèm lý do (`reject_reason`), không xoá im lặng.
5. Kiểm tra toàn vẹn tham chiếu bằng phép kết nối (join) với bảng chiều.
6. Ghi bảng sạch dưới dạng Parquet và tính ba bảng tổng hợp: doanh thu theo ngày, doanh thu theo khu vực × danh mục, số sự kiện theo ngày × loại.
7. Ghi thống kê chất lượng (số dòng thô, sạch, cách ly theo lý do, trùng đã bỏ) và thời gian từng giai đoạn.

**Yêu cầu phi chức năng:**

- Chạy phân tán trên cụm Spark nhiều worker, không phụ thuộc vào một máy đơn.
- Tái lập được: dữ liệu sinh bằng seed cố định; mỗi lần chạy lưu lệnh, cấu hình, commit, log và số đo vào `results/`.
- Đo được: tách thời gian xử lý khỏi thời gian khởi động; có lặp lại để tính độ lệch chuẩn.
- Kiểm chứng được tính đúng: số dòng bị loại phải khớp số lỗi đã chèn.
- Chạy được trong giới hạn bộ nhớ của máy thí nghiệm (mục 3.8).
- Không ghi lộ thông tin đăng nhập MinIO: lấy từ biến môi trường, không viết cứng trong mã.

## 3.8 Giới hạn phần cứng

Toàn bộ thí nghiệm chạy trên **một máy tính cá nhân**:

- RAM 16 GB (15,8 GB khả dụng), Windows 11, Docker Desktop chạy trên WSL2.
- Máy ảo WSL2 bị giới hạn **6 GB** RAM qua tệp `.wslconfig` (`memory=6GB`, `processors=8`); giới hạn này được đặt sau một sự cố engine Docker sập (mục 5.6).
- Cụm Spark gồm 1 master và tối đa 2 worker, mỗi worker 2 lõi; mỗi executor dùng heap mặc định 1 GB.
- Ổ C: và D: là hai phân vùng của cùng một ổ đĩa vật lý, nên MinIO, Spark và hệ điều hành tranh chấp cùng một thiết bị I/O.
- Mẫu CPU của máy: [CHƯA CÓ: tên và số lõi vật lý của CPU chưa được ghi trong repo].

Vì các giới hạn này, kích thước dữ liệu tối đa được chọn là 5 triệu đơn (khoảng 20,9 triệu dòng thô). Mọi kết luận về hiệu năng trong chương 6 chỉ có giá trị trong môi trường này; chúng không thể ngoại suy trực tiếp sang cụm nhiều máy thật.

Nguồn mục 3.8: `.claude/CLAUDE.md`, `infra/README.md`, `src/experiments/README.md` (mục "Giới hạn môi trường").

<!-- VERIFY
- Seed 42, chunk 500.000, dirty-rate 0,02: src/data_generation/config.py (Config: seed=42, chunk_size=500_000, dirty_rate=0.02).
- Tỉ lệ status/payment/event_type/quantity, 731 ngày, ngày đăng ký 2020–2023: src/data_generation/config.py.
- customers = orders/10, products = max(100, orders/250), web_events = orders: config.py (n_customers, n_products, n_events).
- Bảng số dòng thô: results/metrics/orders_*.json, thứ tự trong JSON là customers, products, orders, order_items, web_events; tổng khớp raw_rows_total ở results/metrics/scale_data/summary.csv (500k, 1m, 2500k, 5m) và raw_rows_total 20.930.359 ở results/metrics/skew/runs.csv (skew).
- Dung lượng tệp thô orders_5m và tổng ~1,09 GB (1.089.695.264 byte): results/metrics/format_compare/sizes.csv.
- 99.579 / 100.377 / 100.000 / 200.030: results/metrics/orders_5m.json; 10.001.475 = 10.201.505 − 200.030 (cũng là rows_total ở results/metrics/skew/partition_stats_summary.csv dòng orders_5m).
- Tỉ số 10,54; 16,2 MB; 1,54 MB; 9 phân vùng; 1,18: results/metrics/skew/partition_stats_summary.csv (partitions = 64).
- hot_share 0,5, hot_products 10, 20.000 sản phẩm: config.py, src/experiments/skew/README.md.
- Khái niệm 5V có trong slide chương 1: docs/references/README.md (cần đối chiếu slide thật).
- .wslconfig memory=6GB, processors=8: infra/README.md mục "Sự cố engine Docker Desktop sập".
- C: và D: cùng ổ vật lý: infra/README.md mục "Dung lượng đĩa".
- Bảng lỗi chèn: docs/design/schema.md dòng "Lỗi chèn"; "các loại lỗi không chồng lên cùng một dòng": src/data_generation/README.md.
-->
