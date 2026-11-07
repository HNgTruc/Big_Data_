# metrics/scale_data

Số đo của thí nghiệm `scale_data` (mở rộng theo kích thước dữ liệu); tạo bởi `src/experiments/scale_data/run.py`.

| Đường dẫn | Nội dung |
|---|---|
| `runs/<config>/r<k>/run_record.json` | Bản ghi từng lần chạy (kể cả lần lỗi) |
| `runs/<config>/r<k>/*.json` | Metrics do job ghi ra |
| `runs.csv`, `summary.csv`, ... | Sinh bởi `analyze.py` từ các run record |

Không sửa tay. Bản ghi cũ của cùng một lần lặp được đổi tên kèm thời điểm, không bị xoá.
