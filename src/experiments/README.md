# experiments — thí nghiệm hiệu năng

Mã điều khiển, đo và phân tích các thí nghiệm. Người chạy đo chính thức: `benchmark-analyst`.
**Trạng thái: chưa chạy đo chính thức thí nghiệm nào** (mới kiểm thử mã, dry-run và một lần smoke test, xem cuối trang).

## Cấu trúc

| Đường dẫn | Thí nghiệm | Cấu hình (mỗi cấu hình 3 lần đo) |
|---|---|---|
| `scale_data/` | (a) mở rộng theo kích thước dữ liệu | orders_500k, orders_1m, orders_2500k, orders_5m |
| `scale_workers/` | (b) 1 so với 2 worker | `w1`, `w2` trên orders_5m |
| `format_compare/` | (c) CSV/JSON thô so với Parquet | truy vấn Spark riêng trên orders_5m |
| `join_strategy/` | (d) broadcast so với shuffle join | `auto`, `broadcast`, `shuffle_hint`, `shuffle_noauto` |
| `skew/` | (e) lệch khoá × AQE | `balanced_aqe`, `balanced_noaqe`, `skew_aqe`, `skew_noaqe` |
| `cache/` | (f) cache DataFrame dùng lại | `nocache`, `cache` |
| `pandas_baseline/` | (g) baseline Pandas một máy | orders_500k, orders_1m |
| `common/` | mã dùng chung (Docker, kiểm tra cụm, run record, thống kê, vẽ, job truy vấn) | — |
| `run_all.py` | chạy một nhóm hoặc tất cả thí nghiệm theo thứ tự | — |
| `analyze_all.py` | dựng lại CSV và hình của mọi thí nghiệm (không cần Docker) | — |
| `cleanup.py` | xoá `curated/<exp>_*` và `quarantine/<exp>_*` trên MinIO (tuỳ chọn) | — |
| `requirements.txt` | phụ thuộc phía host | — |

Mỗi thư mục thí nghiệm có `README.md` (mục tiêu, giả thuyết, biến, chỉ số, cách chạy), `run.py` (chạy) và `analyze.py` (phân tích).

## Cài đặt (một lần)

```powershell
# từ thư mục gốc repo; nên dùng venv riêng, không cài vào Python hệ thống
python -m venv .venv-exp
.\.venv-exp\Scripts\Activate.ps1
pip install -r src/experiments/requirements.txt
```

Bộ chạy (`run.py`, `run_all.py`) chỉ cần thư viện chuẩn; `pandas_baseline` cần pandas + pyarrow; `analyze.py` cần matplotlib để vẽ (thiếu thì vẫn ghi CSV).

## Chạy (PowerShell, từ thư mục gốc repo)

Điều kiện: cụm đã `docker compose up -d` trong `infra/`, http://localhost:8090 thấy 2 worker ALIVE, dữ liệu thô đã có trên MinIO, và `curated/orders_5m/` đã có (cho `format_compare`, `cache`). Trước khi đo: đóng ứng dụng nặng, tạm dừng Windows Update (xem `infra/README.md`).

```powershell
python -m src.experiments.run_all --group all --dry-run      # xem trước toàn bộ lệnh, không gọi Docker
python -m src.experiments.run_all --group all                # chạy tất cả theo thứ tự trong common/registry.py
python -m src.experiments.run_all --group spark --resume     # tiếp tục sau khi bị gián đoạn
python -m src.experiments.analyze_all                         # CSV + hình từ run record
```

Thứ tự mặc định: scale_data → join_strategy → skew → format_compare → cache → scale_workers → pandas_baseline (thí nghiệm dừng worker để gần cuối). `run_all` chỉ chuyển tiếp tham số chung; tham số riêng (ví dụ `--datasets`) phải truyền cho `run.py` của thí nghiệm đó.

Tuỳ chọn nên cân nhắc: `--ivy-cache D:\Data\spark-ivy-cache` gắn thư mục host vào `/tmp/.ivy` để không tải lại khoảng 546 MB jar của `--packages` ở mỗi lần chạy (smoke test: tải mất khoảng 65 giây). Mặc định tắt để giữ đúng lệnh trong `infra/README.md`; **chưa kiểm chứng** trên máy này.

## Ước tính số lần chạy (chưa phải số đo)

57 lần chạy: (a) 12, (b) 6, (c) 3, (d) 12, (e) 12, (f) 6, (g) 6. Ước tính thời gian khoảng 2,5–3 giờ nếu không dùng `--ivy-cache`, dựa trên thời gian tham khảo một lần chạy (500k 33 s, 5m 103 s xử lý) cộng khoảng 90 s chi phí khởi động và tải jar mỗi lần (quan sát ở smoke test). Thời gian của (b) 1 worker, (c), (f) chưa có số tham khảo nên chỉ là phỏng đoán.

## Giới hạn môi trường (ghi vào báo cáo)

Máy 16 GB RAM, Docker Desktop/WSL2 giới hạn 6 GB; cụm 1 master + 2 worker × 2 lõi × 2 GB; C: và D: cùng một ổ vật lý. Dữ liệu là dữ liệu mô phỏng sinh bằng script (seed 42).

## Kiểm chứng đã làm (2026-11-07, không phải số đo)

- Unit test: `tests/test_experiments.py`, `tests/test_experiments_pandas.py`.
- Dry-run toàn bộ thí nghiệm.
- Smoke test trên cụm (orders_500k, 1 lần): một lần ETL qua runner (`join_strategy`, `shuffle_hint`) và một lần `query_bench format`; đầu ra đã xoá khỏi `results/` và MinIO.
