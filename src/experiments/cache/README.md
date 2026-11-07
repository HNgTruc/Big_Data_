# cache — (f) cache DataFrame dùng lại

**Trạng thái: chưa chạy.** Đo trong job truy vấn riêng (`src/experiments/common/query_bench.py cache`), không đo trong ETL (theo quyết định của người dùng; `etl_job.py` không có cờ `--cache`).

- **Mục tiêu:** chạy K truy vấn tổng hợp trên cùng DataFrame `order_items ⋈ orders` (đọc từ `curated/<label>/`), so không cache với có cache.
- **Giả thuyết (chưa kiểm chứng):** không cache thì mỗi truy vấn đọc lại Parquet và làm lại join (shuffle); có cache thì lần materialize tốn thêm nhưng các truy vấn sau nhanh hơn, có lợi khi K đủ lớn (slide chương 5: chỉ cache dữ liệu thực sự dùng lại).
- **Biến thay đổi:** `nocache` / `cache` (`DataFrame.cache()`, mức lưu trữ được ghi vào JSON).
- **Biến cố định:** orders_5m, K = 5 (`--k`), cùng thứ tự truy vấn, 2 worker, cấu hình phiên như ETL.

## Đo gì

- `cache`: thời gian materialize (`cache()` + `count()`) đo riêng; sau đó thời gian từng truy vấn; cuối cùng `unpersist(blocking=True)`. Dung lượng cache (bộ nhớ/đĩa, số phân vùng) lấy từ `SparkContext.getRDDStorageInfo` ngay sau materialize.
- `nocache`: thời gian từng truy vấn.
- Truy vấn (lặp vòng nếu K > 5): doanh thu theo ngày, theo trạng thái, top 10 sản phẩm theo số lượng, số dòng theo phương thức thanh toán, giá trị trung bình theo `line_no`.
- Kế hoạch sau truy vấn đầu tiên được lưu (thấy `InMemoryTableScan` khi có cache).
- `analyze.py` tính tổng mỗi chế độ và số truy vấn hoà vốn = materialize / (thời gian tiết kiệm mỗi truy vấn), từ các trung bình.

Lưu ý công bằng: khi không cache, mỗi truy vấn chỉ đọc các cột nó cần (column pruning); khi cache, toàn bộ cột của DataFrame được giữ. Bộ nhớ lưu trữ của executor có hạn (worker 2 GB), phần không vừa sẽ ghi ra đĩa — xem `storage_after_materialize`.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.cache.run --dry-run
python -m src.experiments.cache.run                    # nocache và cache, xen kẽ, 3 lần mỗi chế độ
python -m src.experiments.cache.run --k 10
python -m src.experiments.cache.analyze
```

## Đầu ra

`results/metrics/cache/{runs.csv, summary.csv, break_even.csv}`, `results/figures/cache/cache.png`.
