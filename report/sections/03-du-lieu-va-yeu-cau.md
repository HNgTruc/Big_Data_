# Chương 3. Dữ liệu và yêu cầu

Lược đồ đầy đủ, số dòng từng bảng, chi tiết lỗi chèn và độ lệch khoá nằm ở Phụ lục A.

## 3.1 Nguồn dữ liệu

Đồ án dùng dữ liệu mô phỏng thuộc miền thương mại điện tử, sinh bằng script Python trong `src/data_generation/`. Dữ liệu không thuộc bất kỳ doanh nghiệp nào. Các phân phối (tỉ lệ trạng thái đơn, phương thức thanh toán, loại sự kiện, số lượng mỗi dòng hàng) là lựa chọn thiết kế của đồ án, khai báo trong `src/data_generation/config.py`.

Nhóm chọn dữ liệu mô phỏng thay vì bộ dữ liệu công khai để điều khiển kích thước (0,5 đến 5 triệu đơn) trong giới hạn phần cứng và để bật hoặc tắt độ lệch khoá cho thí nghiệm skew. Vì biết chính xác số lỗi đã chèn từng loại, nhóm kiểm chứng được job làm sạch: số dòng trùng đã bỏ và các lý do cách ly trực tiếp phải khớp đúng số lỗi đó.

Bộ sinh dùng seed cố định 42 và kích thước khối (chunk) 500.000 dòng. Cùng tham số cho ra cùng nội dung từng byte (theo `src/data_generation/README.md`). Mỗi bộ dữ liệu có tệp `manifest.json` ghi tham số, phiên bản thư viện, số dòng và số lỗi đã chèn từng loại.

Trong pipeline tổng quát Sources → Ingestion → Storage → Processing → Analytics → Presentation → Decision/Action, bộ sinh đóng vai trò nguồn (Sources). Lệnh `mc cp` thay cho bước Ingestion, chép thư mục `data/raw/<bộ>/` lên vùng `raw/` của MinIO (mục C.3, Phụ lục C). Phạm vi của đồ án bắt đầu từ khi dữ liệu thô đã nằm trên MinIO.

## 3.2 Lược đồ dữ liệu

Bộ dữ liệu gồm năm bảng ở ba định dạng để thể hiện tính đa dạng (Variety): `orders`, `order_items`, `customers` ở dạng CSV, `products` ở dạng Parquet và `web_events` ở dạng JSON lines. `orders` là bảng sự kiện chính, `order_items` chứa các dòng hàng, `customers` và `products` là bảng chiều, `web_events` ghi sự kiện truy cập web. Cột, kiểu dữ liệu, tập giá trị và ví dụ bản ghi thô ở @tbl:luoc-do và mục A.1 (Phụ lục A).

`orders.customer_id` tham chiếu `customers`, `order_items.order_id` tham chiếu `orders`, `order_items.product_id` tham chiếu `products`. Nhóm thêm cột `line_no` (số thứ tự dòng hàng 1..k trong mỗi đơn) sau một lần sửa thiết kế, lý do ở mục 4.5.

## 3.3 Kích thước các bộ dữ liệu

Số đơn hàng điều khiển kích thước, các bảng còn lại suy ra theo tỉ lệ (mục A.2). Số dòng từng bảng của từng bộ ở @tbl:kich-thuoc-bo (Phụ lục A).

Bảng: Tổng số dòng thô và dung lượng tệp thô của năm bộ dữ liệu (MB = 10^6 byte) {#tbl:kich-thuoc-tong}

| Bộ dữ liệu | Tổng số dòng thô | Dung lượng tệp thô (MB) |
|---|---|---|
| orders_500k | 2.092.960 | 104,84 |
| orders_1m | 4.184.974 | 211,12 |
| orders_2500k | 10.464.824 | 537,77 |
| orders_5m | 20.931.505 | 1.089,70 |
| orders_5m_skew | 20.930.359 | 1.063,22 |

Nguồn: results/metrics/datasets/datasets_summary.csv (cột rows_written, bytes; tổng năm bảng do nhóm cộng)

## 3.4 Dữ liệu bẩn được chèn có kiểm soát

Bộ sinh chèn bốn loại lỗi với tỉ lệ 2% mỗi loại (tham số `--dirty-rate 0.02`): bản ghi trùng, giá trị thiếu, giá trị không hợp lệ và sai định dạng ngày. Các loại lỗi không chồng lên cùng một dòng, bảng `products` giữ sạch. Trên `orders_5m`, ETL đo được 100.000 dòng trùng trên 5.000.000 đơn gốc của `orders` (`results/metrics/orders_5m.json`). Cách chèn từng loại và số lỗi đo được ở @tbl:loi-chen và mục A.3, chất lượng trước và sau xử lý ở mục 6.3.

## 3.5 Độ lệch khoá

Bộ `orders_5m_skew` sinh với cờ `--skew` dồn 50% số lượt chọn sản phẩm vào 10 sản phẩm đầu trong 20.000 sản phẩm. Khi băm `order_items` theo `product_id` vào 64 phân vùng, phân vùng lớn nhất của bộ lệch gấp 10,54 lần trung vị, còn ở bộ cân bằng tỉ số là 1,18 (`results/metrics/skew/partition_stats_summary.csv`). Phân tích đầy đủ ở mục A.4.

## 3.6 Đặc trưng dữ liệu lớn

Đề yêu cầu chỉ ra ít nhất hai đặc trưng dữ liệu lớn (mục 5.2 của đề). Đồ án thể hiện ba đặc trưng theo mô hình 5V ở slide chương 1, tr. 14 [@slide-c1]:

- Volume: bộ lớn nhất có khoảng 20,9 triệu dòng thô và 1,09 GB tệp thô. Quy mô này khiêm tốn so với hệ thống thực tế và bị chặn bởi phần cứng (mục 3.8). Đồ án không khẳng định đây là "dữ liệu lớn" theo nghĩa tuyệt đối mà dùng chuỗi kích thước tăng dần để quan sát xu hướng mở rộng.
- Variety: dữ liệu có cấu trúc (CSV, Parquet) và bán cấu trúc (JSON lines) trong cùng một job (slide chương 1, tr. 26 [@slide-c1]).
- Veracity: dữ liệu có lỗi trùng, thiếu, không hợp lệ và sai định dạng ngày, phải làm sạch trước khi dùng.

Velocity không thuộc phạm vi vì job xử lý theo lô (batch), không có luồng phát sinh liên tục.

Về nhu cầu xử lý phân tán, bộ nhớ đỉnh của Pandas tăng gần tỉ lệ với dữ liệu, từ 906 MiB ở bộ 500k lên 1.682 MiB ở bộ 1M (mục 6.10). Nếu tiếp tục tăng tuyến tính, bộ 5M sẽ cần khoảng 8 GB RAM cho một tiến trình (ngoại suy của nhóm, chưa đo), và lúc đó giới hạn một máy trở thành vấn đề.

## 3.7 Yêu cầu của giai đoạn Storage → Processing

Giai đoạn bắt đầu khi dữ liệu thô đã có trong `s3a://bigdata/raw/<bộ>/` trên MinIO. Giai đoạn kết thúc khi job đã ghi các bảng sạch, bảng cách ly và ba bảng tổng hợp dưới dạng Parquet vào `curated/` và `quarantine/`, sẵn sàng cho giai đoạn Analytics phía sau. Đầu ra phụ là tệp chỉ số (metrics) JSON cho mỗi lần chạy.

Yêu cầu chức năng:

1. Đọc năm bảng thô từ MinIO qua connector S3A với lược đồ khai báo tường minh (không suy luận lược đồ).
2. Bỏ bản ghi trùng theo khoá của từng bảng.
3. Chuẩn hoá ngày và thời gian về định dạng ISO.
4. Tách bản ghi lỗi ra vùng cách ly (quarantine), mỗi dòng kèm lý do (`reject_reason`), không xoá im lặng.
5. Kiểm tra toàn vẹn tham chiếu bằng phép kết nối (join) với bảng chiều.
6. Ghi bảng sạch dưới dạng Parquet và tính ba bảng tổng hợp: doanh thu theo ngày, doanh thu theo khu vực × danh mục, số sự kiện theo ngày × loại.
7. Ghi thống kê chất lượng (số dòng thô, sạch, cách ly theo lý do, trùng đã bỏ) và thời gian từng giai đoạn.

Yêu cầu phi chức năng:

- Chạy phân tán trên cụm Spark nhiều worker, không phụ thuộc vào một máy đơn.
- Tái lập được: dữ liệu sinh bằng seed cố định, mỗi lần chạy lưu lệnh, cấu hình, commit, log và số đo vào `results/`.
- Đo được: tách thời gian xử lý khỏi thời gian khởi động, có lặp lại để tính độ lệch chuẩn.
- Kiểm chứng được tính đúng: số dòng trùng đã bỏ và các lý do cách ly trực tiếp phải khớp số lỗi đã chèn.
- Chạy được trong giới hạn bộ nhớ của máy thí nghiệm (mục 3.8).
- Không ghi lộ thông tin đăng nhập MinIO: lấy từ biến môi trường, không viết cứng trong mã.

## 3.8 Giới hạn phần cứng

Toàn bộ thí nghiệm chạy trên một máy tính cá nhân:

- CPU Intel Core i5-14400F, 10 nhân, 16 luồng.
- RAM 16 GB (hệ điều hành báo 15,76 GB), Windows 11, Docker Desktop chạy trên WSL2.
- Máy ảo WSL2 giới hạn 6 GB RAM qua tệp `.wslconfig` (`memory=6GB`, `processors=8`), đặt sau một sự cố engine Docker sập (mục 5.5).
- Cụm Spark gồm 1 master và tối đa 2 worker, mỗi worker 2 lõi, mỗi executor dùng heap mặc định 1 GB.
- Một ổ SSD NVMe duy nhất (MAXBY MAX3500 1TB) chia thành hai phân vùng C: và D:, nên MinIO, Spark và hệ điều hành tranh chấp cùng một thiết bị I/O.

Vì các giới hạn này, nhóm chọn kích thước dữ liệu tối đa 5 triệu đơn (khoảng 20,9 triệu dòng thô). Mọi kết luận về hiệu năng trong chương 6 chỉ có giá trị trong môi trường này, không thể ngoại suy trực tiếp sang cụm nhiều máy thật.

Nguồn mục 3.8: `results/logs/environment.txt`, `.claude/CLAUDE.md`, `infra/README.md`, `src/experiments/README.md` (mục "Giới hạn môi trường").

<!-- VERIFY
- Seed 42, chunk 500.000, dirty-rate 0,02: src/data_generation/config.py (Config: seed=42, chunk_size=500_000, dirty_rate=0.02).
- @tbl:kich-thuoc-tong: tổng rows_written và bytes năm bảng trong results/metrics/datasets/datasets_summary.csv do người viết cộng; byte đã đối chiếu verify-round1 mục D (104.840.158; 211.124.477; 537.773.401; 1.089.695.264; 1.063.216.156). Tổng dòng khớp raw_rows_total ở results/metrics/scale_data/summary.csv và results/metrics/skew/runs.csv (skew). 1.063,22 MB do người viết quy đổi từ 1.063.216.156 byte.
- 100.000 dòng trùng: results/metrics/orders_5m.json. Chi tiết lỗi chèn và các số đo khác: VERIFY Phụ lục A.
- Tỉ số 10,54; 1,18: results/metrics/skew/partition_stats_summary.csv (partitions = 64). hot_share 0,5, hot_products 10, 20.000 sản phẩm: config.py, src/experiments/skew/README.md.
- 906 và 1.682 MiB: results/metrics/pandas_baseline/summary.csv. Khoảng 8 GB = 1.682 × 5, ngoại suy chưa đo: mục 6.10.
- Mô hình 5V, mức cấu trúc dữ liệu: đã đối chiếu slide chương 1, tr. 14, 26 (report/review/verify-slides.md). Việc áp 3 V vào đồ án là nhận định của người viết.
- CPU, RAM 15,76 GB, ổ đĩa, wslconfig: results/logs/environment.txt.
- "Các loại lỗi không chồng lên cùng một dòng": src/data_generation/README.md.
-->
