# Phụ lục E. Minh chứng bổ sung

Phụ lục này bổ sung cho chương 7: các ảnh chụp còn lại, mẫu bảng tổng hợp và trích đoạn log. Toàn bộ dữ liệu là **dữ liệu mô phỏng**. Ảnh được chụp ngày 2026-11-08, sau bộ đo chính thức.

## E.1 Ảnh chụp MinIO

![MinIO Console: bucket bigdata với các vùng raw, curated, quarantine và smoke](results/logs/screenshots/02_minio_bucket_root.png){#fig:ss-minio-goc}

Nguồn: results/logs/screenshots/02_minio_bucket_root.png

![Vùng curated/orders_5m: năm bảng sạch và ba bảng tổng hợp agg_*](results/logs/screenshots/04_minio_curated_orders_5m.png){#fig:ss-minio-curated}

Nguồn: results/logs/screenshots/04_minio_curated_orders_5m.png

![Vùng quarantine/orders_5m: ba bảng cách ly orders, order_items, web_events](results/logs/screenshots/05_minio_quarantine_orders_5m.png){#fig:ss-minio-quarantine}

Nguồn: results/logs/screenshots/05_minio_quarantine_orders_5m.png

## E.2 Ảnh chụp Spark UI

![Tab Executors của một lần chạy skew_shuffle_aqe: 2 executor trên 2 worker, mỗi executor 2 lõi, Storage Memory 434,4 MiB](results/logs/screenshots/13_executors.png){#fig:ss-executors}

Nguồn: results/logs/screenshots/13_executors.png (ứng dụng app-20261107154233-0032)

Storage Memory 434,4 MiB mỗi executor là vùng nhớ hợp nhất tách ra từ heap 1 GB (mục 5.2).

![Spark History Server: danh sách ứng dụng của thí nghiệm skew dựng lại từ event log](results/logs/screenshots/06_history_app_list.png){#fig:ss-history}

Nguồn: results/logs/screenshots/06_history_app_list.png

![DAG của một job: các stage và ranh giới shuffle (ứng dụng skew_shuffle_aqe)](results/logs/screenshots/12_job_dag.png){#fig:ss-dag}

Nguồn: results/logs/screenshots/12_job_dag.png; mã ứng dụng app-20261107154233-0032 theo results/logs/screenshots/README.md (không hiện trên phần ảnh đã cắt)

@fig:ss-dag minh hoạ cách Spark chia một job thành các stage tại ranh giới shuffle (nút `Exchange`), theo mô hình DAG ở slide chương 5, tr. 26, 43 [@slide-c5]. Hai stage đầu (33 và 37) được đánh dấu "skipped"; chỉ stage 38 (join rồi `WriteFiles`) thực sự chạy. Theo nhận định của người viết, hai stage đó được bỏ qua vì kết quả shuffle của chúng đã có từ job trước và được dùng lại; tài liệu Spark đã kiểm không giải thích lý do này.

![Kế hoạch SQL của skew_shuffle_noaqe, bước ghi order_items sạch: SortMergeJoin không có xử lý lệch](results/logs/screenshots/08_skew_shuffle_noaqe_sql_plan.png){#fig:ss-noaqe-plan}

Nguồn: results/logs/screenshots/08_skew_shuffle_noaqe_sql_plan.png; mã ứng dụng app-20261107154442-0033 và truy vấn SQL số 4 theo results/logs/screenshots/README.md (không hiện trên phần ảnh đã cắt)

## E.3 Mẫu bảng tổng hợp đầu ra

Bảng: Ba dòng đầu của agg_daily_revenue {#tbl:mau-agg-ngay}

| order_date | orders | revenue |
|---|---|---|
| 2024-01-01 | 5507 | 970430.76 |
| 2024-01-02 | 5477 | 987062.4 |
| 2024-01-03 | 5555 | 969962.09 |

Nguồn: results/samples/orders_5m/agg_daily_revenue.csv

Bảng: Ba dòng đầu của agg_revenue_by_region_category {#tbl:mau-agg-khu-vuc}

| region | category | revenue | units |
|---|---|---|---|
| central | beauty | 14376359.5 | 301502 |
| central | books | 14463827.41 | 300801 |
| central | electronics | 14134348.73 | 304495 |

Nguồn: results/samples/orders_5m/agg_revenue_by_region_category.csv

## E.4 Log chạy

Mỗi lần chạy lưu log đầy đủ của driver trong `results/logs/<thí nghiệm>/<cấu hình>_r<k>.log` và nhật ký của bộ điều khiển trong `runner.log`. Một số trích đoạn:

Dòng kết thúc thành công của một lần ETL trên orders_5m (`results/logs/scale_data/orders_5m_r3.log`):

```
ETL_OK processing_seconds_total=87.745 stages={'dimensions': 6.237,
  'orders': 14.288, 'order_items': 35.273, 'web_events': 22.301, 'aggregates': 9.646}
```

Nhật ký bộ điều khiển khi bắt đầu và kết thúc thí nghiệm (a) (`results/logs/scale_data/runner.log`, rút gọn lệnh):

```
[2026-11-07T22:00:54+07:00] [scale_data] start: 12 run(s), reps=3, order=interleaved, git=8164042... dirty=False
[2026-11-07T22:01:42+07:00] [scale_data] orders_500k r1: ok wall=47.429s processing=21.144
[2026-11-07T22:14:12+07:00] [scale_data] done: failures=0 status=0
```

Job xuất mẫu đối chiếu số đếm với metrics (`results/logs/export_samples_orders_5m.log`):

```
SAMPLES_OK out_dir=/opt/spark/work-dir/results/samples/orders_5m files=14 mismatches=0
```

Kiểm thử trong container Spark (`results/logs/test_etl.log`):

```
versions numpy 2.2.6 pandas 2.3.3 pyarrow 25.0.1 pyspark 4.0.0
41 passed in 64.91s (0:01:04)
```

Event log của Spark cho thí nghiệm (d) và (e) được lưu trong `results/logs/<thí nghiệm>/eventlogs/` trên máy đo nhưng không đưa lên git vì dung lượng lớn; các ảnh chụp từ Spark History Server được dựng lại từ các event log này.

<!-- VERIFY
- Ảnh chụp 2026-11-08: results/logs/screenshots/README.md cột Trạng thái.
- Ảnh 04: 8 thư mục (3 agg_* + 5 bảng). Ảnh 02: curated, quarantine, raw, smoke. Ảnh 05: order_items, orders, web_events (đã xem ảnh 2026-11-08). Ảnh 06: 24 ứng dụng từ results/logs/skew/eventlogs (đã xem ảnh 2026-11-08).
- Ảnh 12: stage 33, 37 skipped, stage 38 có WriteFiles (đã xem); lý do skipped là nhận định của người viết (verify-round1 mục B).
- ID ứng dụng, truy vấn của ảnh 08, 12 không hiện trên ảnh đã cắt: verify-round1 mục B; nguồn là results/logs/screenshots/README.md.
- DAG, ranh giới stage: đã đối chiếu slide chương 5, tr. 26, 43 (report/review/verify-slides.md).
- Ảnh 13: Storage Memory 434,4 MiB.
- Bảng agg: results/samples/orders_5m/agg_daily_revenue.csv, agg_revenue_by_region_category.csv.
- Trích log: results/logs/scale_data/orders_5m_r3.log (dòng 2613), runner.log dòng 1, 3, 26, export_samples_orders_5m.log dòng 3199, test_etl.log.
- Event log không đưa lên git: src/experiments/join_strategy/README.md, results/logs/README.md.
-->
