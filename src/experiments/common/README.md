# experiments/common — mã dùng chung cho các thí nghiệm

Chạy trên máy host Windows (Python), trừ `query_bench.py` chạy trong container Spark.

| File | Vai trò |
|---|---|
| `paths.py` | Đường dẫn host/container, đọc các khoá không bí mật trong `infra/.env` |
| `commands.py` | Dựng lệnh `docker compose run --rm ...` (spark-submit, có `--conf` thêm), `stop`/`start spark-worker-2`, xoá trên MinIO (tiền tố luôn kết thúc bằng `/`). Không bao giờ dùng `docker compose exec` |
| `cluster.py` | Đọc `http://localhost:8090/json/`, đếm worker `state == "ALIVE"`, chờ đủ worker; `WorkerController` dừng/bật `spark-worker-2` và luôn bật lại (try/finally) |
| `runner.py` | `RunSpec` (một cấu hình), `Runner` (lặp `--reps` lần, kiểm tra cụm và dọn MinIO trước mỗi lần, ghi log và run record, kể cả lần lỗi) |
| `host.py` | RAM trống của máy (`GlobalMemoryStatusEx`) và các container đang chạy không thuộc project `bigdata` |
| `records.py` | Run record JSON, git commit + cờ bẩn, seed từ `manifest.json`, thời gian tải jar của `--packages` |
| `stats.py` | mean, độ lệch chuẩn mẫu, min, max, n; speedup, efficiency, thông lượng |
| `analysis.py` | Run record → `runs.csv`, `summary.csv`: cờ chất lượng, chỉ thống kê lần hợp lệ, kiểm tra tính đồng nhất (xem dưới) |
| `eventlog.py` | Đọc event log Spark, đếm toán tử join và các lần AQE tách join lệch trong kế hoạch thực thi cuối |
| `plots.py` | Vẽ bằng matplotlib (thanh lỗi = std, ghi n, trục có đơn vị, chú thích nguồn) |
| `query_bench.py` | Job Spark truy vấn riêng: `format` (thô so với Parquet) và `cache` (có/không cache); có bước khởi động không tính giờ |
| `cli.py` | Tham số dòng lệnh chung của mọi `run.py` |
| `registry.py` | Danh sách thí nghiệm, thứ tự chạy mặc định, nhóm (`spark`, `host`, `all`) |

## Tham số chung của mọi `run.py`

`--reps 3` · `--dry-run` · `--order interleaved|blocked` · `--configs a,b` · `--resume` · `--overwrite` ·
`--timeout 3600` · `--stop-on-failure` · `--master-json-url` · `--cores-per-worker 2` · `--no-ivy-cache` ·
`--cleanup-curated` · `--python`. Xem `python -m src.experiments.<exp>.run --help`.

## Mỗi lần lặp

1. Kiểm tra cụm: đúng số worker ALIVE theo cấu hình, tổng lõi = số worker × `--cores-per-worker`, không có ứng dụng nào đang chạy, không còn container tên `etl-driver`/`bench-driver`. Sai thì dừng thí nghiệm (mã 2) và ghi lý do vào `runner.log`.
2. Với ETL: xoá `curated/<label>/` và `quarantine/<label>/` trên MinIO **ngoài thời gian đo** (một lệnh `mc rm`; thời gian và mã thoát ghi ở `pre_cleanup`), để mọi lần lặp ghi vào thư mục rỗng như nhau.
3. Ghi RAM trống và container lạ (`host_before`), chạy lệnh, ghi `host_after`, đọc metrics của job.

## Run record

`results/metrics/<exp>/runs/<config>/r<k>/run_record.json`: thời điểm bắt đầu/kết thúc (ISO), git commit và cờ cây bẩn (không tính `results/`), lệnh đầy đủ (kể cả `--conf`), số worker ALIVE/lõi trước và sau, RAM trống và container lạ, bộ dữ liệu, seed, cấu hình, mã thoát, `wall_seconds`, `processing_seconds_total`, `stage_seconds`, `stats_seconds` (từ metrics của job), `pre_cleanup`, đường dẫn log và event log, thời gian phân giải/tải jar.

`wall_seconds` là thời gian cả lệnh docker. Phần `wall_seconds` − `processing_seconds_total` gồm: khởi động container và JVM, phân giải (lần đầu: tải) jar `--packages`, khởi tạo SparkContext và đăng ký executor, bước thống kê sau xử lý (đếm lại bảng thô/curated/quarantine, đo riêng ở `stats_seconds`), ghi metrics, tắt Spark và xoá container. So sánh hiệu năng dùng `processing_seconds_total`.

- Metrics của job nằm cùng thư mục (`<exp>_<config>.json` với ETL, `query_bench.json`, `pandas_baseline.json`); ETL và `query_bench` ghi thêm `resources` (`spark.executor.memory`, `spark.executor.cores`, `spark.driver.memory`, số executor; `null` = không đặt, dùng mặc định của Spark).
- Log: `results/logs/<exp>/<config>_r<k>.log`; nhật ký bộ điều khiển `results/logs/<exp>/runner.log`.
- Lần chạy lỗi vẫn có record (`status` = `failed` hoặc `timeout`). Chạy lại một lần lặp đã có record thì file cũ được đổi tên kèm thời điểm, không bị xoá.
- Run label `<exp>_<config>` giống nhau cho mọi lần lặp; `results/metrics/<bộ>.json` cũ không bị đụng tới.

## Phân tích: cờ chất lượng và tính đồng nhất

Mỗi dòng của `runs.csv` có `flags` và `valid`. Thống kê chỉ dùng lần **hợp lệ**: `status = ok` và không có cờ loại trừ:

| Cờ | Loại khỏi thống kê | Ý nghĩa |
|---|---|---|
| `workers_changed` | có | số worker ALIVE sau khi chạy khác kỳ vọng |
| `raw_rows_mismatch` | có | ETL đọc số dòng thô khác `manifest.json` |
| `pandas_mismatch` | có | baseline Pandas có số đếm LỆCH |
| `pre_cleanup_failed` | có | không xoá được đầu ra cũ trên MinIO trước lần chạy |
| `foreign_containers` | không (chỉ ghi nhận) | có container ngoài project đang chạy |

`summary.csv` có thêm `n` (lần hợp lệ), `n_failed`, `n_excluded`, `git_commits`, `dirty_any`, `homogeneous` (một commit, một bộ tuỳ chọn ảnh hưởng đến phép đo, một bộ tham số job), `counts_consistent` (số dòng sạch/quarantine theo lý do/trùng và số dòng bảng tổng hợp giống nhau giữa mọi lần hợp lệ của cùng bộ dữ liệu), `flags_seen`. `analyze.py` in cảnh báo khi một nhóm không đồng nhất, số đếm lệch hoặc có lần bị loại.
