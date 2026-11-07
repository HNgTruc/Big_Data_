# skew — (e) lệch khoá × AQE

**Trạng thái: chưa chạy.**

- **Mục tiêu:** so thời gian ETL trên dữ liệu cân bằng (orders_5m) và dữ liệu lệch khoá (orders_5m_skew), mỗi bộ với AQE bật và tắt (`--no-aqe`) → 4 cấu hình.
- **Biến cố định:** `--join-strategy auto` (mặc định, theo quyết định), `shuffle.partitions=8`, 2 worker, seed 42; hai bộ cùng số dòng thô.

## Khoá nào bị lệch

Theo `src/data_generation/tables.py` (`pick_products`) và `docs/design/schema.md`: với `--skew`, 50% lượt chọn sản phẩm (`hot_share=0.5`) rơi vào 10 sản phẩm đầu (`hot_products=10`). Cột bị lệch là **`product_id`** trong `order_items` và `web_events`. `order_id`, `customer_id`, ngày không bị lệch. orders_5m có 20.000 sản phẩm (`orders/250`).

## Điều cần biết khi đọc kết quả

- Trong ETL, `product_id` chỉ là khoá join ở `order_items ⋈ products` và `lines ⋈ products` (tổng hợp theo danh mục). Ở chế độ `auto`, `products` nhỏ nên rất có thể được **broadcast**: khi đó dữ liệu không bị shuffle theo `product_id` và lệch khoá ít ảnh hưởng. Các shuffle lớn (bỏ trùng theo `order_id`, join với `orders`) dùng khoá không lệch. Đây là giả thuyết; `plan_check.csv` cho biết loại join thật sự đã chạy.
- AQE chỉ tách phân vùng lệch của sort-merge join khi phân vùng vượt cả `skewedPartitionFactor` × trung vị và `skewedPartitionThresholdInBytes` (mặc định 5 và 256 MB theo tài liệu Spark SQL Performance Tuning — cần `source-verifier` kiểm chứng cho Spark 4.0). Với khoảng 10 triệu dòng hàng chia 8 phân vùng, có thể không phân vùng nào đạt ngưỡng. `plan_check.csv` đếm `SortMergeJoin(skew=true)`.
- Muốn làm lộ ảnh hưởng của lệch khoá qua shuffle, có thể chạy thêm biến thể `--join-strategy shuffle --no-auto-broadcast` (khác quyết định mặc định; hỏi người dùng trước khi đưa vào báo cáo).
- **Giả thuyết (chưa kiểm chứng):** ở chế độ `auto`, chênh lệch giữa bộ cân bằng và bộ lệch nhỏ; AQE bật nhanh hơn tắt nhờ gộp phân vùng nhỏ (coalesce) hơn là nhờ xử lý lệch.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.skew.run --dry-run
python -m src.experiments.skew.run
python -m src.experiments.skew.analyze
```

## Đầu ra

`results/metrics/skew/{runs.csv, summary.csv (cột ratio_vs_balanced), plan_check.csv}`, `results/figures/skew/skew.png`, event log trong `results/logs/skew/eventlogs/` (không đưa lên git).
