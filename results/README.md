# results — bằng chứng thực nghiệm

Nguồn duy nhất cho mọi số liệu trong báo cáo.

| Thư mục | Nội dung |
|---|---|
| `logs/` | Log chạy job và Spark UI chụp lại, theo từng thí nghiệm |
| `metrics/` | Số đo dạng CSV nhỏ (thời gian, shuffle, dung lượng, số bản ghi) |
| `figures/` | Hình sinh bằng mã từ `metrics/` |
| `samples/` | Mẫu dữ liệu trước/sau xử lý (CSV nhỏ, dữ liệu mô phỏng) do `src/etl/export_samples.py` sinh |

Quy ước: `<loại>/<tên-thí-nghiệm>/`; không sửa tay số đo.
