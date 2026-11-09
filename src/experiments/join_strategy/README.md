# join_strategy — (d) broadcast join so với shuffle (sort-merge) join

**Trạng thái: đã đo chính thức ngày 2026-11-07 (commit 8164042).** Số đo ở `results/metrics/join_strategy/`, hình ở `results/figures/join_strategy/`.

- **Mục tiêu:** so thời gian ETL khi các join với bảng nhỏ dùng broadcast hash join hay sort-merge join (cần shuffle), trên orders_5m; `auto` làm tham chiếu.
- **Giả thuyết (chưa kiểm chứng):** broadcast nhanh hơn với bảng nhỏ (`products`, tập `customer_id`) vì tránh shuffle bảng lớn (slide chương 5).
- **Biến cố định:** orders_5m, AQE bật, `shuffle.partitions=8`, 2 worker, seed 42.

## Cấu hình (theo quyết định của người dùng: 3 cấu hình)

| config | cờ `etl_job.py` | ý nghĩa |
|---|---|---|
| `auto` | `--join-strategy auto` | Spark tự chọn theo `autoBroadcastJoinThreshold` (10 MB, giá trị ghi trong metrics `conf`) |
| `broadcast` | `--join-strategy broadcast` | gợi ý broadcast cho phía nhỏ của các join có gợi ý |
| `shuffle_noauto` | `--join-strategy shuffle --no-auto-broadcast` | gợi ý `merge` + `autoBroadcastJoinThreshold=-1`: mọi join thành sort-merge |

Join có gợi ý trong `src/etl/`: `orders ⋈ customers` (làm sạch đơn), `order_items ⋈ products` (làm sạch dòng hàng), hai join chiều trong `revenue_by_region_category`. Join không gợi ý: `order_items ⋈ orders` (kiểm `no_clean_order`) và `items ⋈ orders` trong tổng hợp doanh thu. Chỉ dùng gợi ý `merge` thì các join không gợi ý vẫn có thể broadcast theo ngưỡng tự động, nên cấu hình shuffle tắt thêm broadcast tự động.

## Xác minh chiến lược thật sự chạy

Mỗi lần chạy ghi event log Spark (`spark.eventLog.compress=false`, `spark.eventLog.rolling.enabled=false`) vào `results/logs/join_strategy/eventlogs/`. `analyze.py` lấy kế hoạch cuối của từng SQL execution (lần cập nhật AQE sau cùng) và đếm `SortMergeJoin`, `BroadcastHashJoin`, `ShuffledHashJoin` (không đếm lại cây con dưới `ReusedExchange`) → `plan_check.csv`. Kỳ vọng cần kiểm: `shuffle_noauto` không có `BroadcastHashJoin`.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.join_strategy.run --dry-run
python -m src.experiments.join_strategy.run                       # 3 cấu hình × 3 lần, xen kẽ
python -m src.experiments.join_strategy.analyze
```

## Đầu ra

`results/metrics/join_strategy/{runs.csv, summary.csv, plan_check.csv}`, `results/figures/join_strategy/join_strategy.png`. Event log không đưa lên git (`.gitignore`).
