# skew — (e) lệch khoá × cách join × AQE

**Trạng thái: đã đo chính thức ngày 2026-11-07 (commit 8164042).** Số đo ở `results/metrics/skew/`, hình ở `results/figures/skew/`. Phép đo kích thước phân vùng để chọn tham số: `results/metrics/skew/partition_stats*.csv`, xem dưới.

- **Mục tiêu:** so thời gian ETL trên dữ liệu cân bằng (orders_5m) và lệch khoá (orders_5m_skew), với hai cách join và AQE bật/tắt → **8 cấu hình**, mỗi cấu hình 3 lần.
- **Biến cố định:** 2 worker, seed 42, cùng mã ETL.

## Khoá nào bị lệch

Theo `src/data_generation/tables.py` (`pick_products`) và `docs/design/schema.md`: với `--skew`, 50% lượt chọn sản phẩm (`hot_share=0.5`) rơi vào 10 sản phẩm đầu (`hot_products=10`). Cột bị lệch là **`product_id`** trong `order_items` và `web_events`; `order_id`, `customer_id`, ngày không lệch. Cả hai bộ có 20.000 sản phẩm; số dòng thô gần bằng nhau nhưng không bằng hẳn (`order_items`: 10.201.505 dòng ở orders_5m, 10.200.359 dòng ở orders_5m_skew; bốn bảng còn lại bằng nhau — nguồn `data/raw/<bộ>/manifest.json`).

Trong ETL, `product_id` là khoá join ở `order_items ⋈ products` (làm sạch dòng hàng) và `lines ⋈ products` (tổng hợp theo khu vực × danh mục). Các shuffle lớn khác (bỏ trùng theo `order_id`, join với `orders`) dùng khoá không lệch.

## 8 cấu hình

| config | bộ dữ liệu | cách join | AQE |
|---|---|---|---|
| `balanced_auto_aqe`, `balanced_auto_noaqe` | orders_5m | `auto` | bật / tắt |
| `skew_auto_aqe`, `skew_auto_noaqe` | orders_5m_skew | `auto` | bật / tắt |
| `balanced_shuffle_aqe`, `balanced_shuffle_noaqe` | orders_5m | `shuffle` (ép) | bật / tắt |
| `skew_shuffle_aqe`, `skew_shuffle_noaqe` | orders_5m_skew | `shuffle` (ép) | bật / tắt |

- **`auto`**: cấu hình mặc định của ETL (`--join-strategy auto`, 8 phân vùng shuffle). `products` nhỏ nên thường được broadcast; khi đó dữ liệu không bị shuffle theo `product_id` và lệch khoá ít tác động. Đây là trường hợp "thực tế" của job.
- **`shuffle`** (biến thể ép shuffle — **cài đặt chủ động** để AQE có cơ hội xử lý lệch khoá ở quy mô dữ liệu này):
  `--join-strategy shuffle --no-auto-broadcast --shuffle-partitions 64`
  `--conf spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes=4194304` (4 MiB)
  `--conf spark.sql.adaptive.advisoryPartitionSizeInBytes=2097152` (2 MiB).
  Hai conf này không được `src/etl/session.py` đặt nên giá trị từ spark-submit đến được phiên Spark; metrics JSON của ETL ghi giá trị thực tế (`conf`). Ở cấu hình `noaqe` các conf AQE không có tác dụng; chúng được giữ để hai cấu hình chỉ khác nhau ở AQE.

## Vì sao chọn các tham số của biến thể `shuffle`

Theo tài liệu Spark SQL Performance Tuning (mục Adaptive Query Execution, "Optimizing Skew Join"), AQE chỉ tách một phân vùng của sort-merge join khi phân vùng đó lớn hơn **cả** `skewedPartitionFactor` × trung vị (mặc định 5) **và** `skewedPartitionThresholdInBytes` (mặc định 256 MB). Tài liệu cũng ghi ngưỡng này nên lớn hơn `advisoryPartitionSizeInBytes`. (Các giá trị mặc định lấy từ tài liệu; cần `source-verifier` đối chiếu đúng bản 4.0.)

Kích thước phân vùng thật được đo bằng `partition_stats.py`: `order_items` sau khi bỏ trùng, shuffle `repartition(N, "product_id")` (cùng cách băm như sort-merge join), AQE tắt, đọc số dòng và số byte shuffle của từng tác vụ. Kết quả ở `results/metrics/skew/partition_stats_summary.csv` (chi tiết từng phân vùng: `partition_stats.csv`, log: `results/logs/skew/partition_stats.log`):

| bộ | N | phân vùng lớn nhất / trung vị (byte) | lớn nhất | trung vị | số phân vùng > 5× trung vị |
|---|---|---|---|---|---|
| orders_5m_skew | 8 | 1,77 | 34,7 MB | 19,6 MB | 0 |
| orders_5m_skew | 64 | 10,54 | 16,2 MB | 1,54 MB | 9 |
| orders_5m | 64 | 1,18 | 3,47 MB | 2,94 MB | 0 |

(byte = 10⁶ byte; số chính xác trong CSV.) Suy ra:

1. Với 8 phân vùng (mặc định của ETL) không phân vùng nào vượt 5× trung vị, và phân vùng lớn nhất (34,7 MB) cách xa 256 MB → AQE không thể tách. Vì vậy `auto` và `shuffle` khác nhau cả ở số phân vùng.
2. Với 64 phân vùng, 9 phân vùng chứa khoá nóng có kích thước 8,07–16,2 MB (≥ 5,2× trung vị), các phân vùng còn lại ≤ 1,71 MB. Ngưỡng **4 MiB** nằm giữa hai nhóm: chỉ các phân vùng nóng đạt ngưỡng, và ở bộ cân bằng không phân vùng nào đạt (lớn nhất 3,47 MB, cũng không vượt 5× trung vị).
3. `advisoryPartitionSizeInBytes` = **2 MiB** (< ngưỡng, đúng khuyến nghị) để các phân vùng nóng 8–16 MB được tách thành vài phần; với giá trị mặc định 64 MB, phân vùng nhỏ hơn kích thước mục tiêu sẽ không bị tách.

Số byte đo ở đây là shuffle của riêng `order_items`; trong join tổng hợp, mỗi dòng có thêm cột nên lớn hơn, vẫn trên ngưỡng. Một lần chạy thử `skew_shuffle_aqe` (2026-11-07, ngoài `results/`) đã thấy AQE tách join (`SortMergeJoin(skew=true)` ở bước làm sạch dòng hàng và bước tổng hợp theo danh mục). Kết quả chính thức xem `plan_check.csv` sau khi chạy.

## Giả thuyết (chưa kiểm chứng)

- `auto`: chênh lệch giữa bộ cân bằng và bộ lệch nhỏ, vì join theo `product_id` là broadcast.
- `shuffle`: bộ lệch chậm hơn bộ cân bằng khi AQE tắt (một vài tác vụ xử lý phần lớn dữ liệu); AQE bật thu hẹp chênh lệch nhờ tách phân vùng lệch.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.skew.run --dry-run
python -m src.experiments.skew.run                                  # 8 cấu hình × 3 lần
python -m src.experiments.skew.run --configs skew_shuffle_aqe,skew_shuffle_noaqe
python -m src.experiments.skew.analyze
```

Tham số: `--forced-partitions 64`, `--skew-threshold-bytes 4194304`, `--advisory-bytes 2097152` (ngưỡng phải lớn hơn advisory). Đo lại kích thước phân vùng (không cần cụm, chạy Spark local trong container), trong `infra/`:

```powershell
docker compose run --rm --no-deps spark-master /opt/spark/bin/spark-submit --master "local[2]" /opt/spark/work-dir/src/experiments/skew/partition_stats.py --partitions 8,32,64,128 --out /opt/spark/work-dir/results/metrics/skew/partition_stats.csv
```

## Đầu ra

`results/metrics/skew/{runs.csv, summary.csv (cột ratio_vs_balanced: lệch/cân bằng cùng cách join và AQE), plan_check.csv, partition_stats*.csv}`, `results/figures/skew/skew.png`, event log trong `results/logs/skew/eventlogs/` (không đưa lên git). `plan_check.csv` đếm `SortMergeJoin`, `BroadcastHashJoin`, `SortMergeJoin(skew=true)`, `AQEShuffleRead(skewed)` trong kế hoạch cuối (lần cập nhật AQE sau cùng) của từng SQL execution.
