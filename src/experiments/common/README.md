# experiments/common — mã dùng chung cho các thí nghiệm

Chạy trên máy host Windows (Python), trừ `query_bench.py` chạy trong container Spark.

| File | Vai trò |
|---|---|
| `paths.py` | Đường dẫn host/container, đọc các khoá không bí mật trong `infra/.env` |
| `commands.py` | Dựng lệnh `docker compose run --rm ...` (spark-submit), `stop`/`start spark-worker-2`, xoá trên MinIO. Không bao giờ dùng `docker compose exec` |
| `cluster.py` | Đọc `http://localhost:8090/json/`, đếm worker `state == "ALIVE"`, chờ đủ worker; `WorkerController` dừng/bật `spark-worker-2` và luôn bật lại (try/finally) |
| `runner.py` | `RunSpec` (một cấu hình), `Runner` (lặp `--reps` lần, kiểm tra cụm trước mỗi lần, ghi log và run record, kể cả lần lỗi) |
| `records.py` | Run record JSON, git commit + cờ bẩn, seed từ `manifest.json`, thời gian tải jar của `--packages` |
| `stats.py` | mean, độ lệch chuẩn mẫu, min, max, n; speedup, efficiency, thông lượng |
| `analysis.py` | Run record → `runs.csv`, `summary.csv` (chỉ dùng lần thành công, ghi `n` và `n_failed`) |
| `eventlog.py` | Đọc event log Spark, đếm toán tử join trong kế hoạch thực thi cuối (sau AQE) |
| `plots.py` | Vẽ bằng matplotlib (thanh lỗi = std, ghi n, trục có đơn vị, chú thích nguồn) |
| `query_bench.py` | Job Spark truy vấn riêng: `format` (thô so với Parquet) và `cache` (có/không cache) |
| `cli.py` | Tham số dòng lệnh chung của mọi `run.py` |
| `registry.py` | Danh sách thí nghiệm, thứ tự chạy mặc định, nhóm (`spark`, `host`, `all`) |

## Tham số chung của mọi `run.py`

`--reps 3` · `--dry-run` · `--order interleaved|blocked` · `--configs a,b` · `--resume` · `--overwrite` ·
`--timeout 3600` · `--stop-on-failure` · `--master-json-url` · `--cores-per-worker 2` · `--ivy-cache <thư mục host>` ·
`--cleanup-curated` · `--python`. Xem `python -m src.experiments.<exp>.run --help`.

## Quy ước đầu ra (mỗi lần lặp)

- Run record: `results/metrics/<exp>/runs/<config>/r<k>/run_record.json` — thời điểm bắt đầu/kết thúc (ISO), git commit và cờ cây bẩn (không tính `results/`), lệnh đầy đủ, số worker ALIVE/lõi trước và sau, bộ dữ liệu, seed, cấu hình, mã thoát, `wall_seconds` (cả lệnh docker, gồm khởi động container, JVM, tải jar), `processing_seconds_total` và `stage_seconds` (từ metrics của job), đường dẫn log, thời gian tải jar.
- Metrics của job nằm cùng thư mục (`<exp>_<config>.json` với ETL, `query_bench.json`, `pandas_baseline.json`).
- Log: `results/logs/<exp>/<config>_r<k>.log`; nhật ký bộ điều khiển `results/logs/<exp>/runner.log`.
- Lần chạy lỗi vẫn có record (`status` = `failed` hoặc `timeout`). Chạy lại một lần lặp đã có record thì file cũ được đổi tên kèm thời điểm, không bị xoá.
- Run label `<exp>_<config>` giống nhau cho mọi lần lặp, nên `curated/<label>/` trên MinIO bị ghi đè (đỡ tốn đĩa); `results/metrics/<bộ>.json` cũ không bị đụng tới.

## Kiểm tra trước mỗi lần chạy Spark

Đúng số worker ALIVE theo cấu hình, tổng lõi = số worker × `--cores-per-worker`, không có ứng dụng nào đang chạy, không còn container tên `etl-driver`/`bench-driver`. Sai thì dừng thí nghiệm (mã 2) và ghi lý do vào `runner.log`.
