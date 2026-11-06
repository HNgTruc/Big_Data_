# data — dữ liệu (không đưa lên git)

| Thư mục | Nội dung |
|---|---|
| `raw/` | Dữ liệu thô sinh bởi `src/data_generation/` (CSV/JSON) |
| `curated/` | Bảng Parquet đã làm sạch và tổng hợp |
| `quarantine/` | Bản ghi lỗi kèm lý do bị loại |

Tệp dữ liệu bị `.gitignore` loại; chỉ README được giữ. Tái tạo dữ liệu bằng script và seed trong `src/data_generation/`.
