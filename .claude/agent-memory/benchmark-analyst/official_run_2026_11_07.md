---
name: official-run-2026-11-07
description: Lần đo chính thức đầy đủ 69 run (2026-11-07 22:00–23:41 +07), phát hiện chính, lỗi analyze cache, cờ dirty do agent
metadata:
  type: project
---

`run_all --group all` chạy 2026-11-07 22:00:54 → 23:41:37 +07, commit 8164042, 69/69 ok, không gián đoạn, không resume. Số liệu nằm ở `results/metrics/<exp>/summary.csv`.

Phát hiện đáng chú ý (quan sát sơ bộ, cần phân tích thêm):
- scale_workers: S_2 = 1.287569, E_2 = 0.643785 (processing_seconds_total).
- skew: bộ lệch KHÔNG chậm hơn bộ cân bằng (ratio_vs_balanced 0.95–1.09); AQE tách join lệch (skewSMJ=3) chỉ ở skew_shuffle_aqe. Ở biến thể shuffle 64 phân vùng, AQE giảm mạnh stage_aggregates ở cả hai bộ: giả thuyết là nhờ gộp phân vùng, không phải xử lý lệch.
- join_strategy: auto và broadcast có cùng kế hoạch (4 SMJ, 6 BHJ), nên chênh thời gian giữa chúng là nhiễu.
- pandas nhanh hơn Spark 4–6 lần ở 0.5M/1M.
- RAM trống của host chỉ 350–1150 MiB trong lúc đo (memory load 93–97%) vì WSL2 chiếm 6 GB: có thể gây nhiễu (giả thuyết).
- CV > 10%: scale_data orders_5m (11.92%), skew balanced_shuffle_noaqe (12.70%), các truy vấn ngắn của format_compare/cache.

Lỗi mã (chưa vá, đã báo): `src/experiments/cache/analyze.py` hàm `plot` lọc `step.startswith("q")` nên bắt cả `queries_seconds_total`, rồi `int("ueries")` gây ValueError → thiếu `cache.png` và `analyze_all` dừng trước scale_workers/pandas_baseline (đã chạy riêng hai analyzer đó).

**Why:** để lần sau biết bộ số nào là chính thức và vì sao có cờ dirty.
**How to apply:** nếu đo lại, chạy sau khi lỗi analyze được sửa; xem [[no-repo-writes-during-runs]] và [[env-limits]].
