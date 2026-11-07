# raw

Dữ liệu thô **mô phỏng** đầu vào của job Spark, sinh bằng `src/data_generation` (seed 42, 2% lỗi mỗi loại).
Không đưa lên git (xem `.gitignore`); tạo lại bằng `python -m src.data_generation.generate --orders N [--skew] --overwrite`.

| Thư mục | `orders` | Lệch key |
|---|---|---|
| `orders_500k/` | 500.000 | không |
| `orders_1m/` | 1.000.000 | không |
| `orders_2500k/` | 2.500.000 | không |
| `orders_5m/` | 5.000.000 | không |
| `orders_5m_skew/` | 5.000.000 | có |

Mỗi thư mục có `customers.csv`, `orders.csv`, `order_items.csv`, `products.parquet`, `web_events.jsonl` và `manifest.json`
(tham số sinh, số dòng ghi ra, số lỗi đã chèn theo từng loại; dùng để đối chiếu với `results/metrics/`).
Bản sao trên MinIO: `s3a://bigdata/raw/<thư mục>/` (cách upload ở `infra/README.md`).
