# Phụ lục B. Cờ kiểm tra hợp lệ của bộ đo

Phụ lục này ghi chi tiết của đoạn "Kiểm tra tính hợp lệ của từng lần chạy" ở mục 4.6.

## B.1 Bản ghi của mỗi lần chạy

Mỗi lần chạy có một bản ghi `results/metrics/<thí nghiệm>/runs/<cấu hình>/r<k>/run_record.json`, gồm lệnh đầy đủ, commit, cờ cây mã bẩn, số worker trước và sau, RAM trống của host và số đo. Lần chạy lỗi vẫn có bản ghi, với `status` là `failed` hoặc `timeout`.

## B.2 Cờ loại trừ

Một lần chạy bị loại khỏi thống kê nếu trạng thái khác `ok` hoặc mang một trong các cờ loại trừ ở @tbl:co-hop-le.

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

- **Tính đồng nhất** (`homogeneous`): một commit, một bộ tuỳ chọn ảnh hưởng đến phép đo, một bộ tham số job.
- **Tính nhất quán của số đếm** (`counts_consistent`): số dòng sạch, cách ly theo lý do, trùng và số dòng bảng tổng hợp giống nhau giữa mọi lần hợp lệ của cùng bộ dữ liệu.

<!-- VERIFY
- Bốn cờ loại trừ và foreign_containers: src/experiments/common/README.md bảng cờ chất lượng, src/experiments/common/analysis.py.
- Nội dung run_record.json và status failed/timeout: src/experiments/common/README.md mục "Run record".
- homogeneous, counts_consistent: src/experiments/common/README.md mục "Phân tích".
-->
