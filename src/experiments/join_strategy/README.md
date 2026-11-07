# join_strategy — (d) broadcast join so với shuffle (sort-merge) join

**Trạng thái: chưa chạy** (đã smoke test `shuffle_hint` một lần trên orders_500k để kiểm đường ống; không dùng làm số đo).

- **Mục tiêu:** so thời gian ETL khi các join với bảng nhỏ dùng broadcast hash join hay sort-merge join (cần shuffle), trên orders_5m; `auto` làm tham chiếu.
- **Giả thuyết (chưa kiểm chứng):** broadcast nhanh hơn với bảng nhỏ (`products`, tập `customer_id`) vì tránh shuffle bảng lớn (slide chương 5).
- **Biến cố định:** orders_5m, AQE bật, `shuffle.partitions=8`, 2 worker, seed 42.

## Cấu hình

| config | cờ `etl_job.py` | ý nghĩa |
|---|---|---|
| `auto` | `--join-strategy auto` | Spark tự chọn (ngưỡng `autoBroadcastJoinThreshold` mặc định 10 MB) |
| `broadcast` | `--join-strategy broadcast` | gợi ý broadcast cho phía nhỏ của các join có gợi ý |
| `shuffle_hint` | `--join-strategy shuffle` | gợi ý `merge` cho các join có gợi ý; join không gợi ý vẫn có thể broadcast |
| `shuffle_noauto` | `--join-strategy shuffle --no-auto-broadcast` | gợi ý `merge` + tắt broadcast tự động: mọi join thành sort-merge |

Join có gợi ý trong `src/etl/`: `orders ⋈ customers` (làm sạch đơn), `order_items ⋈ products` (làm sạch dòng hàng), và hai join chiều trong `revenue_by_region_category`. Join không gợi ý: `order_items ⋈ orders` (kiểm `no_clean_order`) và `items ⋈ orders` trong tổng hợp doanh thu.

## Xác minh chiến lược thật sự chạy

Mỗi lần chạy ghi event log Spark (`spark.eventLog.compress=false`, `spark.eventLog.rolling.enabled=false`) vào `results/logs/join_strategy/eventlogs/`. `analyze.py` lấy kế hoạch cuối của từng SQL execution (lần cập nhật AQE sau cùng) và đếm `SortMergeJoin`, `BroadcastHashJoin`, `ShuffledHashJoin` → `plan_check.csv`. Như vậy biết được gợi ý `merge` có bị AQE đổi hay không.

Quan sát từ smoke test (orders_500k, 1 lần, **chưa phải kết quả**): với `shuffle_hint`, các join có gợi ý là `SortMergeJoin` trong kế hoạch cuối, còn hai join không gợi ý vẫn là `BroadcastHashJoin`. Vì thế có thêm cấu hình `shuffle_noauto`. Cần kiểm lại trên orders_5m bằng `plan_check.csv`.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.join_strategy.run --dry-run
python -m src.experiments.join_strategy.run                                  # 4 cấu hình × 3 lần
python -m src.experiments.join_strategy.run --configs auto,broadcast,shuffle_noauto
python -m src.experiments.join_strategy.analyze
```

## Đầu ra

`results/metrics/join_strategy/{runs.csv, summary.csv, plan_check.csv}`, `results/figures/join_strategy/join_strategy.png`. Event log không đưa lên git (`.gitignore`).
