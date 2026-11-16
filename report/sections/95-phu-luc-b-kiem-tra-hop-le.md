# Phụ lục B. Thiết kế đo và cờ kiểm tra hợp lệ

Chi tiết của mục 4.6: bản ghi và cờ của từng lần chạy, chỉ số, kiểm soát nhiễu, xác minh kế hoạch thực thi và tham số biến thể ép shuffle.

## B.1 Bản ghi của mỗi lần chạy

Mỗi lần chạy có một bản ghi `results/metrics/<thí nghiệm>/runs/<cấu hình>/r<k>/run_record.json`, gồm lệnh đầy đủ, commit, cờ cây mã bẩn, số worker trước và sau, RAM trống của host và số đo. Lần chạy lỗi vẫn có bản ghi, với `status` là `failed` hoặc `timeout`.

## B.2 Cờ loại trừ

Thống kê loại một lần chạy nếu trạng thái khác `ok` hoặc lần đó mang một trong các cờ loại trừ ở @tbl:co-hop-le.

Bảng: Các cờ chất lượng của một lần chạy {#tbl:co-hop-le}

| Cờ | Loại khỏi thống kê | Ý nghĩa |
|---|---|---|
| `workers_changed` | Có | Số worker thay đổi trong lúc chạy: số worker ALIVE sau khi chạy khác kỳ vọng |
| `raw_rows_mismatch` | Có | Số dòng thô đọc được khác manifest |
| `pandas_mismatch` | Có | Baseline Pandas cho số đếm lệch |
| `pre_cleanup_failed` | Có | Không xoá được đầu ra cũ trên MinIO trước lần chạy |
| `foreign_containers` | Không, chỉ ghi nhận | Có container ngoài dự án đang chạy |

Nguồn: src/experiments/common/README.md (mục "Phân tích: cờ chất lượng và tính đồng nhất"), src/experiments/common/analysis.py

## B.3 Kiểm tra trên bảng tổng hợp

Ngoài cờ của từng lần, bảng tổng hợp `summary.csv` còn kiểm tra hai tính chất:

- Tính đồng nhất (`homogeneous`): một commit, một bộ tuỳ chọn ảnh hưởng đến phép đo, một bộ tham số job.
- Tính nhất quán của số đếm (`counts_consistent`): số dòng sạch, cách ly theo lý do, trùng và số dòng bảng tổng hợp giống nhau giữa mọi lần hợp lệ của cùng bộ dữ liệu.

## B.4 Chỉ số và kiểm soát nhiễu

`processing_seconds_total` là tổng thời gian năm giai đoạn do job tự đo, không gồm khởi động container, JVM, đăng ký executor và bước thống kê. Bộ điều khiển ghi thời gian cả lệnh Docker (`wall_seconds`) để tham khảo. Mỗi cấu hình chạy 3 lần. Riêng (c) có hai cấu hình đảo thứ tự định dạng, khi phân tích gộp lại thành 6 lần đo cho mỗi cặp truy vấn × định dạng.

Các chỉ số suy ra:

- Thông lượng = tổng số dòng thô năm bảng / `processing_seconds_total` (dòng/giây), tính cho từng lần chạy rồi lấy trung bình.
- Speedup S = T(1 worker) / T(2 worker), efficiency E = S / 2 (công thức ở slide chương 2, tr. 21 [@slide-c2]).
- Số truy vấn hoà vốn của cache n* = M / (u − c), với M là thời gian materialize, u và c là thời gian trung bình một truy vấn khi không cache và có cache.

Các biện pháp kiểm soát nhiễu:

- Thứ tự xen kẽ: lần 1 của mọi cấu hình, rồi lần 2, rồi lần 3, để nhiễu theo thời gian phân bố đều. Riêng (b) chạy theo khối (3 lần 1 worker rồi 3 lần 2 worker) để chỉ phải dừng và bật worker một lần.
- Trước mỗi lần chạy ETL, bộ điều khiển xoá đầu ra cũ của cùng nhãn trên MinIO, ngoài thời gian đo, để mọi lần lặp ghi vào thư mục rỗng như nhau.
- Job truy vấn của (c) và (f) có một bước khởi động không tính giờ trước khi đo.
- Trước mỗi lần chạy Spark, bộ điều khiển kiểm tra cụm có đúng số worker ALIVE, đúng tổng số lõi, không có ứng dụng nào khác đang chạy, sai thì dừng thí nghiệm.

Bảng tổng hợp chỉ dùng các lần có trạng thái `ok` và không mang cờ loại trừ (mục B.2), đồng thời kiểm tra tính đồng nhất và tính nhất quán của số đếm giữa các lần chạy (mục B.3).

## B.5 Xác minh kế hoạch thực thi

Với (d) và (e), mỗi lần chạy ghi event log của Spark. Bộ phân tích đọc kế hoạch cuối cùng (sau lần cập nhật AQE sau cùng) của từng truy vấn SQL và đếm các toán tử `SortMergeJoin`, `BroadcastHashJoin`, `SortMergeJoin(skew=true)`, để biết chiến lược join nào đã chạy thay vì chỉ dựa vào cấu hình [@spark-monitoring].

## B.6 Tham số của biến thể ép shuffle trong (e)

Với 8 phân vùng mặc định, không phân vùng nào của bộ lệch vượt 5 lần trung vị (phân vùng lớn nhất khoảng 34,7 MB). Nhóm chọn ngưỡng 4 MiB dựa trên phép đo kích thước phân vùng thật. Ở 64 phân vùng, 9 phân vùng chứa khoá nóng có kích thước 8,07 đến 16,2 MB, các phân vùng còn lại không quá 1,71 MB, và ở bộ cân bằng phân vùng lớn nhất là 3,47 MB (@tbl:partition-stats, Phụ lục D). Ngưỡng 4 MiB vì vậy nằm giữa hai nhóm, chỉ phân vùng nóng của bộ lệch đạt ngưỡng.

<!-- VERIFY
- Bốn cờ loại trừ và foreign_containers: src/experiments/common/README.md bảng cờ chất lượng, src/experiments/common/analysis.py.
- Nội dung run_record.json và status failed/timeout: src/experiments/common/README.md mục "Run record".
- homogeneous, counts_consistent: src/experiments/common/README.md mục "Phân tích".
- Thông lượng trung bình theo từng lần: verify-round1 mục C; results/metrics/scale_data/summary.csv.
- Thứ tự xen kẽ / scale_workers blocked: src/experiments/common/README.md, src/experiments/scale_workers/README.md, run_record runner_options.order.
- 34,7 MB, 8,07–16,2 MB, ≤1,71 MB, 3,47 MB: src/experiments/skew/README.md và results/metrics/skew/partition_stats_summary.csv (8,07 và 1,71 chỉ có trong partition_stats.csv chi tiết).
- Kiểm tra cụm chỉ áp dụng cho lần chạy Spark: verify-round2 A3.
-->
