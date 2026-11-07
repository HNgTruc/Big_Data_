# data — dữ liệu (không đưa lên git)

| Thư mục | Nội dung |
|---|---|
| `raw/` | Dữ liệu thô sinh bởi `src/data_generation/` (CSV/JSON) |
| `curated/` | Bảng Parquet đã làm sạch và tổng hợp |
| `quarantine/` | Bản ghi lỗi kèm lý do bị loại |
| `ivy_cache/` | Bộ đệm Ivy của các jar `spark-submit --packages` (`hadoop-aws` và phụ thuộc, khoảng 1 GB trên đĩa); tạo tự động khi chạy `src/experiments/` |

Tệp dữ liệu bị `.gitignore` loại; chỉ README được giữ. Tái tạo dữ liệu bằng script và seed trong `src/data_generation/`.

## `ivy_cache/`

- Container Spark thấy thư mục này ở `/opt/spark/work-dir/data/ivy_cache` (qua bind mount `../data` trong `infra/docker-compose.yml`). Bộ chạy thí nghiệm truyền `--conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache`, nên container driver `--rm` dùng lại jar đã tải thay vì tải lại ở mỗi lần chạy. Lần chạy thử ngày 2026-11-07: lần thứ hai in `0 artifacts copied, 3 already retrieved`.
- Cả thư mục bị `.gitignore` loại (không có README bên trong vì không đưa lên git). Xoá thư mục thì lần chạy sau sẽ tải lại (cần Internet).
- Tắt bằng `--no-ivy-cache` của `src/experiments/<exp>/run.py`.
