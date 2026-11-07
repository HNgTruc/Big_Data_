# pandas_baseline — (g) baseline Pandas một máy

**Trạng thái: chưa chạy đo chính thức** (đã chạy thử một lần trên orders_500k, đầu ra để ngoài `results/`).

- **Mục tiêu:** cùng luật làm sạch và cùng ba bảng tổng hợp như ETL Spark, viết bằng pandas, chạy trên một máy; đo theo cùng các giai đoạn (`dimensions`, `orders`, `order_items`, `web_events`, `aggregates`) để có điểm so sánh với Spark (mục Volume trong `docs/design/schema.md`).
- **Phạm vi:** chỉ orders_500k và orders_1m (theo quyết định).
- **Giả thuyết (chưa kiểm chứng):** ở các kích thước này pandas có thể nhanh hơn Spark vì không có chi phí phân tán; điều đó không mâu thuẫn với mục tiêu đồ án, nhưng phải phân tích trung thực.

## File

| File | Vai trò |
|---|---|
| `pandas_etl.py` | Luật làm sạch và tổng hợp (bản pandas của `src/etl/cleaning.py`, `aggregates.py`) |
| `baseline.py` | CLI: đọc `data/raw/<bộ>/`, đo từng giai đoạn, ghi Parquet ra thư mục tạm, đối chiếu số dòng |
| `run.py`, `analyze.py` | Lặp 3 lần (mỗi lần một tiến trình Python mới), phân tích và so với `scale_data` |

## Tái hiện luật của Spark

Bỏ trùng theo khoá (`customer_id`, `order_id`, (`order_id`, `line_no`), `event_id`); nhận diện ngày/giờ bằng cùng biểu thức chính quy và định dạng; quarantine theo đúng thứ tự lý do (luật đầu tiên thắng); `no_clean_order`; `region` thiếu → `unknown`; doanh thu chỉ tính `paid`, `shipped`, `delivered`. Kiểu cột tương ứng `src/etl/schemas.py`; như Spark, chỉ chuỗi rỗng là null. `tests/test_experiments_pandas.py` so các hằng số này với mã Spark để phát hiện lệch khi `src/etl/` đổi.

Khác biệt đã biết: làm tròn doanh thu kiểu NumPy (half-to-even) thay vì HALF_UP của Spark (không ảnh hưởng số dòng); pandas giữ bảng sạch trong bộ nhớ thay vì ghi rồi đọc lại; Parquet ghi một file mỗi bảng.

## Đối chiếu

Mỗi lần chạy in `KHỚP`/`LỆCH` cho: số dòng thô, dòng trùng đã bỏ, từng lý do quarantine so với `data/raw/<bộ>/manifest.json`; và mọi số dòng sạch/quarantine/trùng, từng lý do, số dòng bảng tổng hợp so với `results/metrics/<bộ>.json` của Spark. Kết quả ghi trong JSON (`checks`, `all_match`). Có số đếm LỆCH thì `baseline.py` thoát với mã 3: bộ chạy ghi lần đó là `failed` và không đưa vào thống kê (JSON vẫn được ghi để xem nguyên nhân).

## So sánh với Spark: khác biệt môi trường (bắt buộc nêu trong báo cáo)

- Pandas chạy **trực tiếp trên host Windows**, không bị giới hạn 6 GB của Docker/WSL2 (máy 16 GB RAM); nhưng máy ảo WSL2 vẫn giữ bộ nhớ nếu cụm đang bật.
- Pandas đọc **đĩa local** (`data/raw/`), Spark đọc **MinIO qua mạng Docker** (S3A).
- Pandas **không có chi phí khởi động JVM, đăng ký ứng dụng, lập lịch task**; `processing_seconds_total` của cả hai đều không gồm khởi động tiến trình, nhưng Spark vẫn trả chi phí lập lịch trong từng giai đoạn.
- Pandas dùng một lõi cho phần lớn thao tác; Spark dùng 4 lõi executor.
- Bộ nhớ đỉnh: `PeakWorkingSetSize` của tiến trình qua `GetProcessMemoryInfo` (Windows, ctypes; trên Linux dùng `ru_maxrss`), ghi sau mỗi giai đoạn (giá trị đỉnh cộng dồn). Không dùng `tracemalloc` vì làm chậm phép đo.

## Cách chạy (PowerShell, thư mục gốc repo; không cần Docker)

```powershell
python -m src.experiments.pandas_baseline.run --dry-run
python -m src.experiments.pandas_baseline.run                     # orders_500k, orders_1m × 3 lần
python -m src.experiments.pandas_baseline.analyze                 # chạy sau scale_data để có bảng so sánh
# một lần thử, ghi ra ngoài results/:
python -m src.experiments.pandas_baseline.baseline --dataset orders_500k --metrics-out $env:TEMP\pandas_try.json
```

Nên chạy khi cụm Spark không chạy job nào (để hai bên không tranh tài nguyên).

## Đầu ra

`results/metrics/pandas_baseline/{runs.csv, summary.csv, comparison_spark.csv}`, `results/figures/pandas_baseline/pandas_vs_spark.png`.
