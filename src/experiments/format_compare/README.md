# format_compare — (c) CSV/JSON thô so với Parquet đã làm sạch

**Trạng thái: chưa chạy** (đã smoke test một lần trên orders_500k để kiểm đường ống; kết quả đó không dùng).

- **Mục tiêu:** cùng một bộ truy vấn Spark trên dữ liệu thô (`raw/<bộ>/`, CSV và JSON lines) và trên Parquet (`curated/<label>/`), đo thời gian từng truy vấn và dung lượng lưu trữ.
- **Giả thuyết (chưa kiểm chứng):** Parquet nhanh hơn rõ ở truy vấn chỉ dùng ít cột nhờ đọc theo cột (column pruning) và đẩy điều kiện lọc xuống (predicate pushdown); dung lượng nhỏ hơn nhờ nén theo cột (slide chương 4).
- **Biến thay đổi:** định dạng nguồn (raw / curated).
- **Biến cố định:** bộ orders_5m (`--dataset`), cùng phiên Spark (cấu hình như ETL), 2 worker.

## Truy vấn (`src/experiments/common/query_bench.py format`)

| Tên | Nội dung | Ý nghĩa |
|---|---|---|
| `q1_filter_count` | `orders` lọc `status = 'delivered'`, đếm | đọc 1 cột, có điều kiện lọc |
| `q2_events_by_type` | `web_events` đếm theo `event_type` | 1/5 cột của bảng lớn nhất; JSON phải phân tích cả dòng |
| `q3_daily_revenue_join` | `order_items ⋈ orders` (trạng thái có doanh thu), tổng `quantity × unit_price` theo ngày | join + tổng hợp |

- Dữ liệu thô đọc bằng `src/etl/pipeline.read_raw` (schema tường minh trong `src/etl/schemas.py`, như ETL); `order_date` thô được chuẩn hoá bằng `cleaning.parse_date` để khoá ngày giống nhau.
- Kết quả thô và curated **khác nhau một chút**: dữ liệu thô còn dòng trùng và dòng lỗi (khoảng 2% mỗi loại). Mục đích là so chi phí đọc theo định dạng; kết quả từng truy vấn được ghi kèm (`result`) để minh bạch.
- Chỉ thời gian `collect()` của truy vấn được đo. Sau mỗi truy vấn, kế hoạch `explain("formatted")` (kế hoạch AQE cuối) được lưu vào JSON và log, làm bằng chứng cho `ReadSchema`/`PushedFilters`.
- Thứ tự: mỗi truy vấn chạy raw trước rồi curated (`--query-order raw-first`, đổi được). Truy vấn đầu tiên của ứng dụng chịu thêm chi phí khởi động (sinh mã, mở kết nối S3A), rơi vào `q1` raw; cần nêu khi phân tích hoặc chạy thêm với `--query-order curated-first`.
- Dung lượng: Hadoop `FileSystem.getContentSummary` trên `s3a://` cho từng file thô và từng thư mục bảng curated (số file gồm cả `_SUCCESS` 0 byte). Bảng curated đã bỏ dòng trùng/lỗi nên nhỏ hơn cả vì có ít dòng hơn.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.format_compare.run --dry-run
python -m src.experiments.format_compare.run                          # orders_5m, curated/orders_5m
python -m src.experiments.format_compare.run --dataset orders_1m      # bộ khác
python -m src.experiments.format_compare.analyze
```

Cần `curated/<label>/` có sẵn (mặc định label = tên bộ, tức đầu ra của lần chạy ETL thường); dùng `--curated-label scale_data_orders_5m` để truy vấn đầu ra của `scale_data`. Thiếu bảng thì job dừng với `QUERY_BENCH_ERROR`.

## Đầu ra

`results/metrics/format_compare/{runs.csv, summary.csv (có ratio_raw_over_curated), sizes.csv}`, `results/figures/format_compare/{query_times_<bộ>,storage_<bộ>}.png`.
