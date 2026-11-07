# metrics/skew

Số đo của thí nghiệm `skew` (ảnh hưởng của lệch khoá và AQE); tạo bởi `src/experiments/skew/run.py`.

| Đường dẫn | Nội dung |
|---|---|
| `partition_stats.csv`, `partition_stats_summary.csv` | Số dòng và byte shuffle của từng phân vùng băm theo `product_id` (8/32/64/128 phân vùng), đo bằng `src/experiments/skew/partition_stats.py` ngày 2026-11-07 (Spark local trong container, log `results/logs/skew/partition_stats.log`). Là bằng chứng để chọn tham số biến thể `shuffle`, không phải số đo thời gian |
| `runs/<config>/r<k>/run_record.json` | Bản ghi từng lần chạy (kể cả lần lỗi) — chưa có |
| `runs/<config>/r<k>/*.json` | Metrics do job ghi ra — chưa có |
| `runs.csv`, `summary.csv`, `plan_check.csv` | Sinh bởi `analyze.py` từ các run record — chưa có |

Không sửa tay. Bản ghi cũ của cùng một lần lặp được đổi tên kèm thời điểm, không bị xoá.
