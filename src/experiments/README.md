# experiments — thí nghiệm hiệu năng

Mã điều khiển, đo và phân tích các thí nghiệm. Người chạy đo chính thức: `benchmark-analyst`.
**Trạng thái: chưa chạy đo chính thức thí nghiệm nào** (mới kiểm thử mã, dry-run và vài lần chạy thử; đầu ra chạy thử không để trong `results/`). Bằng chứng duy nhất đã lưu là phép đo kích thước phân vùng của `skew` (`results/metrics/skew/partition_stats*.csv`).

## Cấu trúc

| Đường dẫn | Thí nghiệm | Cấu hình (mỗi cấu hình 3 lần đo) |
|---|---|---|
| `scale_data/` | (a) mở rộng theo kích thước dữ liệu | orders_500k, orders_1m, orders_2500k, orders_5m |
| `scale_workers/` | (b) 1 so với 2 worker | `w1`, `w2` trên orders_5m |
| `format_compare/` | (c) CSV/JSON thô so với Parquet | `raw_first`, `curated_first` (job truy vấn riêng trên orders_5m) |
| `join_strategy/` | (d) broadcast so với shuffle join | `auto`, `broadcast`, `shuffle_noauto` |
| `skew/` | (e) lệch khoá × cách join × AQE | 8 cấu hình `{balanced,skew}_{auto,shuffle}_{aqe,noaqe}` |
| `cache/` | (f) cache DataFrame dùng lại | `nocache`, `cache` |
| `pandas_baseline/` | (g) baseline Pandas một máy | orders_500k, orders_1m |
| `common/` | mã dùng chung (Docker, kiểm tra cụm, run record, thống kê, vẽ, job truy vấn) | — |
| `run_all.py` | chạy một nhóm hoặc tất cả thí nghiệm theo thứ tự | — |
| `analyze_all.py` | dựng lại CSV và hình của mọi thí nghiệm (không cần Docker) | — |
| `cleanup.py` | xoá `curated/<exp>_*/` và `quarantine/<exp>_*/` trên MinIO (tuỳ chọn) | — |
| `requirements.txt` | phụ thuộc phía host | — |

Mỗi thư mục thí nghiệm có `README.md` (mục tiêu, giả thuyết, biến, chỉ số, cách chạy), `run.py` (chạy) và `analyze.py` (phân tích); `skew/` có thêm `partition_stats.py`.

## Cài đặt (một lần)

```powershell
# từ thư mục gốc repo; venv riêng, không cài vào Python hệ thống
python -m venv .venv-exp
.\.venv-exp\Scripts\Activate.ps1
pip install -r src/experiments/requirements.txt
```

Bộ chạy (`run.py`, `run_all.py`) chỉ cần thư viện chuẩn; `pandas_baseline` cần pandas + pyarrow; `analyze.py` cần matplotlib để vẽ (thiếu thì vẫn ghi CSV).

## Chạy (PowerShell, từ thư mục gốc repo)

Điều kiện: cụm đã `docker compose up -d` trong `infra/`, http://localhost:8090 thấy 2 worker ALIVE, dữ liệu thô đã có trên MinIO, và `curated/orders_5m/` đã có (cho `format_compare`, `cache`). Trước khi đo: đóng ứng dụng nặng, tạm dừng Windows Update (xem `infra/README.md`). Container của dự án khác vẫn chạy thì mỗi lần chạy bị gắn cờ `foreign_containers` (không bị loại).

```powershell
python -m src.experiments.run_all --group all --dry-run      # xem trước toàn bộ lệnh, không gọi Docker
python -m src.experiments.run_all --group all                # chạy tất cả theo thứ tự trong common/registry.py
python -m src.experiments.run_all --group spark --resume     # tiếp tục sau khi bị gián đoạn
python -m src.experiments.analyze_all                         # CSV + hình từ run record
```

Thứ tự mặc định: scale_data → join_strategy → skew → format_compare → cache → scale_workers → pandas_baseline (thí nghiệm dừng worker để gần cuối). `run_all` chỉ chuyển tiếp tham số chung; tham số riêng (ví dụ `--datasets`) phải truyền cho `run.py` của thí nghiệm đó.

**Bộ đệm Ivy (mặc định bật):** spark-submit dùng `spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache` (thư mục `data/ivy_cache/` trên máy, đã có trong bind mount `data/`), nên jar của `--packages` chỉ tải một lần; lần chạy đầu tiên của cả bộ vẫn tải. `--no-ivy-cache` quay về `/tmp/.ivy` trong container (tải lại mỗi lần, đúng lệnh trong `infra/README.md`).

## Ước tính (chưa phải số đo)

69 lần chạy: (a) 12, (b) 6, (c) 6, (d) 9, (e) 24, (f) 6, (g) 6. Ước tính thô khoảng 2–3,5 giờ, dựa trên thời gian xử lý tham khảo một lần chạy trong `docs/design/etl.md` (500k khoảng 33 s, 5m khoảng 103 s) cộng chi phí khởi động container/JVM, bước thống kê và tắt Spark mỗi lần (chưa đo chính thức). Chưa có số tham khảo cho (b) 1 worker, (c), (f) và cho biến thể ép shuffle của (e), nên các phần đó chỉ là phỏng đoán.

## Giới hạn môi trường (ghi vào báo cáo)

Máy 16 GB RAM, Docker Desktop/WSL2 giới hạn 6 GB; cụm 1 master + 2 worker, mỗi worker 2 lõi và cho phép tối đa 2 GB, mỗi executor dùng heap mặc định 1 GB (không đặt `spark.executor.memory`; mặc định 1g theo tài liệu Spark Configuration; giữ nguyên vì lịch sử Docker Desktop sập dưới giới hạn 6 GB). C: và D: cùng một ổ vật lý. Dữ liệu là dữ liệu mô phỏng sinh bằng script (seed 42).

## Kiểm chứng đã làm (2026-11-07, không phải số đo)

- Unit test phía host: `tests/test_experiments.py`, `tests/test_experiments_pandas.py`; phía container: `tests/test_query_bench.py` (xem `tests/README.md`).
- Dry-run toàn bộ thí nghiệm.
- Chạy thử trên cụm (đầu ra đã xoá khỏi `results/` và MinIO): ETL qua runner (kiểm bộ đệm Ivy: lần thứ hai không tải jar), `query_bench format`, `skew_shuffle_aqe` trên orders_5m_skew (AQE có tách join lệch; event log không nén đọc được; không thấy mật khẩu MinIO trong event log — Spark che `secret.key`).
