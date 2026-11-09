# Phụ lục F. Hướng dẫn chạy và tái lập

Phụ lục này ghi các bước tái lập từ máy trống. Lệnh lấy từ các README trong repo; lệnh đã ghi ở mục C.3 được dẫn sang, không chép lại. Chạy trong PowerShell. Thư mục làm việc ghi ở từng bước: "gốc" là thư mục gốc repo, "`infra`" là thư mục con `infra/`.

Mã nguồn công khai tại `https://github.com/HNgTruc/Big_Data_.git`.

```powershell
git clone https://github.com/HNgTruc/Big_Data_.git
cd Big_Data_
```

Đồ án không cung cấp API dịch vụ; giao diện sử dụng là các tham số dòng lệnh ở mục C.3.

## F.1 Điều kiện cần

- **Docker Desktop trên WSL2.** Máy đã chạy dùng Docker engine 29.9.2 (`results/logs/environment.txt`).
- **Giới hạn WSL2.** Tệp `C:\Users\<tên>\.wslconfig` có `memory=6GB` và `processors=8` trong nhóm `[wsl2]` (`infra/README.md`, `results/logs/environment.txt`). Lý do đặt giới hạn ở mục 5.5. Sau khi sửa tệp, chạy `wsl --shutdown` rồi khởi động lại WSL để thay đổi có hiệu lực [@wsl-config]. Lệnh này tắt mọi bản phân phối WSL 2 đang chạy, nên cần dừng cụm trước (nhận định của nhóm). Repo không ghi nhận lệnh này đã chạy trên máy thí nghiệm.
- **Python trên host.** Máy đã chạy dùng Python 3.12.10; README không nêu phiên bản tối thiểu. Tạo venv từ thư mục gốc (`src/experiments/README.md`):

```powershell
python -m venv .venv-exp
.\.venv-exp\Scripts\Activate.ps1
pip install -r src/experiments/requirements.txt
```

- **Dung lượng đĩa.** Năm bộ dữ liệu thô khoảng 3,0 GB (cộng từ @tbl:kich-thuoc-tong), `data/ivy_cache/` khoảng 1 GB (đo trên máy thí nghiệm). Thư mục làm việc của worker tăng theo số lần chạy trong một giờ (`infra/README.md`; xem thêm mục 5.5): 7 lần chạy chiếm khoảng 4,1 GB trên mỗi worker, và thư mục chỉ bị xoá sau 1 giờ. Bộ đo chính thức chạy 63 ứng dụng Spark trong khoảng 1 giờ 41 phút, nên đỉnh có thể tới vài chục GB (suy luận, chưa đo); cần dự phòng dung lượng.
- **Internet.** Cần khi kéo image, tải `hadoop-aws` lần đầu và cài gói kiểm thử trong container.

## F.2 Cấu hình và dựng cụm

Các lệnh ở mục này chạy trong `infra`. Tạo `infra/.env` rồi đổi mật khẩu MinIO. Mật khẩu có ký tự đặc biệt phải mã hoá URL vì được dùng trong `MC_HOST_local`.

```powershell
copy .env.example .env
```

Kéo ba image ghi trong `.env` bằng `docker pull` (`SPARK_IMAGE`, `MINIO_IMAGE`, `MC_IMAGE`). Thẻ `latest` của MinIO có thể đổi theo thời gian; image đã đo có id `sha256:a692590bc9d7a33c1eb1e52454a02395165392adee65a8ebfa90810b5df0f5e5` (`results/logs/environment.txt`), dùng để đối chiếu. Sau đó dựng cụm (`infra/README.md`):

```bash
docker compose up -d
docker compose ps          # master, 2 worker, minio phải Up; minio-init thoát mã 0
```

Giao diện: Spark Master tại http://localhost:8090, MinIO Console tại http://localhost:9001. Dừng cụm bằng `docker compose down` (thêm `-v` để xoá dữ liệu MinIO).

Tuỳ chọn, kiểm tra kết nối Spark và MinIO. Thành công khi thấy `SMOKE_OK rows_written=1000000 rows_read=1000000`. Lần chạy đã ghi nhận dùng `exec`; dạng `run` dưới đây chưa chạy lại riêng cho job này (`infra/README.md`).

```powershell
docker compose run --rm --no-deps --name smoke-driver spark-master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --conf spark.driver.host=smoke-driver `
  --conf spark.jars.ivy=/tmp/.ivy `
  --packages org.apache.hadoop:hadoop-aws:3.4.1 `
  /opt/spark/work-dir/src/etl/smoke_s3a.py
```

## F.3 Sinh dữ liệu mô phỏng

Chạy từ thư mục gốc (`src/data_generation/README.md`):

```bash
pip install -r src/data_generation/requirements.txt
python -m src.data_generation.generate --orders 500000          # -> data/raw/orders_500k
python -m src.data_generation.generate --orders 5000000 --skew  # -> data/raw/orders_5m_skew
python -m src.data_generation.generate --help
```

README chỉ ghi hai lệnh ví dụ trên và lệnh `--orders 5000000` ở mục C.3. Hai bộ còn lại dùng `--orders 1000000` và `--orders 2500000`, theo trường `params.orders` trong `data/raw/orders_1m/manifest.json` và `data/raw/orders_2500k/manifest.json`. Tham số mặc định: seed 42, chunk 500.000, tỉ lệ lỗi 0,02. Cùng tham số cho cùng nội dung từng byte; đổi `chunk_size` sẽ đổi dữ liệu.

Bản clone đã có `manifest.json` trong `data/raw/<bộ>/`, nên phải thêm `--overwrite`, nếu không bộ sinh báo thư mục không rỗng và dừng. Lệnh này ghi lại `manifest.json`, trong đó `elapsed_seconds` sẽ khác. Đã thử trên một bản clone mới: thiếu `--overwrite` thì dừng với mã 1; có `--overwrite` thì bộ `orders_500k` sinh ra có năm tệp dữ liệu trùng từng byte với dữ liệu đã dùng để đo, so bằng SHA-256 (`results/logs/test_clone.log`).

## F.4 Chép dữ liệu thô lên MinIO

Lệnh `mc cp` ở bước 3 của mục C.3, chạy trong `infra` cho từng bộ, thay `orders_5m` bằng tên bộ. Đích phải là `raw/`, không phải `raw/<bộ>`, nếu không dữ liệu bị lồng thêm một cấp. Kiểm tra (`infra/README.md`):

```powershell
docker compose run --rm minio-init ls --recursive --summarize local/bigdata/raw/orders_500k
```

Kết quả đúng là 6 object, đường dẫn dạng `customers.csv`, `orders.csv`. Nếu đã chép lồng, xoá rồi chép lại:

```powershell
docker compose run --rm minio-init rm --recursive --force local/bigdata/raw/orders_500k
```

## F.5 Chạy job ETL

Chạy trong `infra`, thay tên bộ ở `--dataset`. Lệnh nguyên văn ở `infra/README.md`:

```powershell
docker compose run --rm --no-deps --name etl-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=etl-driver --conf spark.jars.ivy=/tmp/.ivy --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/etl_job.py --dataset orders_500k 2>&1 | Select-String "ETL_OK|ERROR|Exception|Traceback"
```

Để không tải lại jar mỗi lần, đổi `spark.jars.ivy` như mục C.3. Thành công khi thấy `ETL_OK processing_seconds_total=...`. Đầu ra gồm `curated/<bộ>/`, `quarantine/<bộ>/` trên MinIO và `results/metrics/<bộ>.json` trên host. Thêm `--run-label <tên>` để không ghi đè kết quả cũ.

Trước bộ thí nghiệm, chỉ bắt buộc chạy ETL cho `orders_5m`, vì `format_compare` và `cache` cần `curated/orders_5m/`. Baseline Pandas đối chiếu `results/metrics/orders_500k.json`, `orders_1m.json`, đã có sẵn trong kho. Các bộ còn lại chạy để tái lập số đếm ở mục 6.3.

**Dùng `docker compose run`, không dùng `docker compose exec`.** Khi engine Docker sập, `exec` báo lỗi `500` hoặc `No such exec instance`. Dùng `run` thì driver nằm trong container riêng, tách khỏi master, và được xoá sau khi chạy. Chi tiết ở mục C.3.

## F.6 Chạy bộ thí nghiệm

Điều kiện: 2 worker ALIVE tại http://localhost:8090, dữ liệu thô và `curated/orders_5m/` đã có trên MinIO. Hướng dẫn đo yêu cầu đóng ứng dụng nặng và tạm dừng Windows Update trước khi đo. Kích hoạt venv ở F.1 và quay về thư mục gốc, vì F.2, F.4, F.5 chạy trong `infra`. Từ thư mục gốc (`src/experiments/README.md`):

```powershell
python -m src.experiments.run_all --group all --dry-run      # xem trước toàn bộ lệnh, không gọi Docker
python -m src.experiments.run_all --group all                # chạy tất cả theo thứ tự trong common/registry.py
python -m src.experiments.run_all --group spark --resume     # tiếp tục sau khi bị gián đoạn
```

Trên bản clone đã có sẵn 69 bản ghi của bộ đo chính thức, nên lệnh chạy thật phải thêm `--overwrite`: bản ghi và log cũ được đổi tên kèm thời điểm, không bị xoá. `--resume` chỉ dùng khi tiếp tục lần chạy của chính mình; `--group spark` không gồm Pandas, phần đó chạy bằng `--group host`. Đã thử trên bản clone: `--dry-run` chạy được cho cả 7 thí nghiệm; thiếu `--overwrite` thì dừng ở `scale_data` với mã 2 và không đổi tệp nào (`results/logs/test_clone.log`). Lệnh có `--overwrite` cần Docker nên chưa chạy thử trên bản clone (theo mã `src/experiments/common/runner.py`, `registry.py`).

Thứ tự mặc định: `scale_data`, `join_strategy`, `skew`, `format_compare`, `cache`, `scale_workers`, `pandas_baseline`. Bộ đo chính thức kéo dài khoảng 1 giờ 41 phút (mục 6.1).

Thí nghiệm `scale_workers` tự dừng rồi bật lại `spark-worker-2`. Nếu bộ chạy bị dừng đột ngột, kiểm tra Master UI và chạy trong `infra` (`src/experiments/scale_workers/README.md`):

```powershell
docker compose start spark-worker-2
```

Phép đo kích thước phân vùng của thí nghiệm (e) chạy riêng; lệnh ở `src/experiments/skew/README.md`. Mỗi thí nghiệm có `run.py` với `--dry-run` riêng, ghi trong README của thí nghiệm đó.

Khi tái lập, số dòng phải khớp với báo cáo vì dữ liệu và luật làm sạch là xác định, còn thời gian sẽ dao động theo máy và nhiễu (nhận định của nhóm).

## F.7 Phân tích và xuất minh chứng

Dựng lại CSV và hình bằng `analyze_all` ở bước 5 của mục C.3, không cần Docker. Event log không đưa lên git, nên trên bản clone `analyze_all` ghi đè `results/metrics/join_strategy/plan_check.csv` và `results/metrics/skew/plan_check.csv`: số toán tử mất, chỉ còn cột `note` ghi thiếu tệp (`src/experiments/common/analysis.py`, hàm `plan_rows`). Đã thử trên bản clone: đây là hai tệp duy nhất trong `results/` có trên git bị đổi, các CSV và hình khác giữ nguyên (`results/logs/test_clone.log`). Khôi phục bằng `git checkout -- results/metrics/join_strategy/plan_check.csv results/metrics/skew/plan_check.csv`.

Xuất mẫu dữ liệu trước và sau xử lý, trong `infra`, khi ETL của bộ đã có trên MinIO (`results/samples/README.md`):

```powershell
docker compose run --rm --no-deps --name sample-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=sample-driver --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/export_samples.py --dataset orders_5m > ..\results\logs\export_samples_orders_5m.log 2>&1
```

Thành công khi log có `SAMPLES_OK ... mismatches=0`. Cách mở Spark History Server để xem lại kế hoạch thực thi ở `results/logs/screenshots/README.md`. Cần có event log, chỉ có trên máy đã chạy (d), (e).

## F.8 Chạy kiểm thử

Trong container Spark, chạy trong `infra`, cụm không cần đang bật, cần Internet để cài gói (`tests/README.md`):

```powershell
docker compose run --rm --no-deps -v ${PWD}/../tests:/opt/spark/work-dir/tests:ro --entrypoint bash spark-master /opt/spark/work-dir/tests/run_in_container.sh
```

Trên host, từ thư mục gốc (`results/logs/test_host.log`, dòng 2):

```powershell
.venv-exp\Scripts\python.exe -m pytest tests/test_build_docx.py tests/test_experiments.py tests/test_experiments_pandas.py tests/test_data_generation.py -q
```

`test_build_docx.py` cần cài phụ thuộc ở F.9. Thiếu `python-docx` thì tệp này bị bỏ qua. `test_etl.py` không chạy được trên Windows nên phải chạy trong container. Kết quả ở mục 5.4 và @tbl:kiem-thu (Phụ lục C).

## F.9 Dựng báo cáo

Từ thư mục gốc (`report/build/README.md`, `report/figures/README.md`):

```powershell
.\.venv-exp\Scripts\python.exe -m pip install --default-timeout=300 -r report\build\requirements.txt
.\.venv-exp\Scripts\python.exe report\build\draw_architecture.py
.\.venv-exp\Scripts\python.exe report\build\draw_plan_comparison.py
.\.venv-exp\Scripts\python.exe report\build\prepare_screenshots.py
.\.venv-exp\Scripts\python.exe report\build\build_docx.py
```

Mở `report/bao-cao.docx` trong Word, chọn tất cả rồi nhấn F9 để cập nhật mục lục và danh mục. Bản nộp là PDF xuất từ Word.

## F.10 Ghi nhận các lần chạy đã có

Bảng: Nơi lưu ghi nhận các lần chạy {#tbl:ghi-nhan-chay}

| Việc đã chạy | Ghi nhận |
|---|---|
| Sinh dữ liệu | `data/raw/<bộ>/manifest.json` (có trên git; dữ liệu thô thì không); `results/metrics/datasets/datasets_summary.csv` |
| Kiểm tra kết nối | `results/logs/smoke_s3a.log` |
| ETL đầu tiên của năm bộ | `results/logs/etl_<bộ>.log`; `results/metrics/<bộ>.json` |
| Bộ đo chính thức (69 lần) | `results/metrics/<exp>/runs/<config>/r<k>/run_record.json`, `runs.csv`, `summary.csv`; `results/logs/<exp>/<config>_r<k>.log`, `runner.log` |
| Hình kết quả | `results/figures/<exp>/` |
| Event log của (d), (e) | `results/logs/<exp>/eventlogs/` (không đưa lên git) |
| Xuất mẫu | `results/samples/orders_5m/`; `results/logs/export_samples_orders_5m.log` |
| Kiểm thử | `results/logs/test_etl.log`, `results/logs/test_host.log`; các bước không cần Docker trên bản clone: `results/logs/test_clone.log` |
| Môi trường máy | `results/logs/environment.txt` |
| Ảnh chụp giao diện | `results/logs/screenshots/` |

Nguồn: results/logs/README.md, results/README.md, data/README.md, src/experiments/README.md

Bước chép dữ liệu bằng `mc cp` không có log riêng trong `results/`; bằng chứng gián tiếp là @fig:ss-minio-raw và số dòng thô khớp manifest trong các lần chạy.

<!-- VERIFY
- Lệnh F.1 (venv): src/experiments/README.md mục "Cài đặt". F.2: infra/README.md mục "Chuẩn bị", "Chạy", "Kiểm tra Spark - MinIO". F.3: src/data_generation/README.md. F.4: infra/README.md mục "Đưa dữ liệu thô lên MinIO". F.5: infra/README.md mục "Chạy job ETL". F.6: src/experiments/README.md mục "Chạy"; src/experiments/scale_workers/README.md. F.7: results/samples/README.md. F.8: tests/README.md; results/logs/test_host.log dòng 2. F.9: report/build/README.md; report/figures/README.md.
- `docker pull`: README không ghi dạng lệnh đầy đủ, chỉ "`docker pull` ba image trong `.env`"; tên biến lấy từ infra/.env.example.
- `[wsl2]`: results/logs/environment.txt. Tệp `C:\Users\<tên>\.wslconfig`: infra/README.md.
- `--orders 1000000`, `--orders 2500000`: không có trong README; lấy từ params.orders trong data/raw/orders_1m/manifest.json, orders_2500k/manifest.json và default_out_dir trong src/data_generation/generate.py.
- 3,0 GB: 104,84 + 211,12 + 537,77 + 1.089,70 + 1.063,22 = 3.006,65 MB (người viết cộng từ @tbl:kich-thuoc-tong).
- Khoảng 1 giờ 41 phút: 22:00:54 đến 23:41:37, mục 6.1.
- format_compare, cache cần curated/orders_5m: src/experiments/README.md. Pandas đối chiếu results/metrics/<bộ>.json: src/experiments/pandas_baseline/README.md; tệp đã có trên git (verify-round2 E6).
- plan_check.csv khi thiếu event log: src/experiments/common/analysis.py hàm plan_rows; src/experiments/skew/analyze.py dòng 43–44; src/experiments/join_strategy/analyze.py dòng 31–32 (verify-round2 E5). Đã chạy thử trên bản clone: results/logs/test_clone.log.
- `--overwrite` của bộ thí nghiệm: src/experiments/common/runner.py:192-196, 69 run_record.json có trên git; `--group host`: src/experiments/common/registry.py (verify-round2 E1). Đã thử trên bản clone phần dừng khi thiếu cờ; lệnh có cờ cần Docker, chưa thử trên bản clone.
- `--overwrite` của bộ sinh: src/data_generation/generate.py:128-130, 5 manifest.json có trên git (verify-round2 E2, E3). Người dùng quyết định giữ manifest trên git (H3). Đã chạy thử trên bản clone: results/logs/test_clone.log.
- `wsl --shutdown`: [@wsl-config] (verify-round2 E4, trang trả về toàn văn). Việc "cần dừng cụm trước" là nhận định.
- Đỉnh vài chục GB: suy luận từ infra/README.md (4,1 GB sau 7 lần chạy, xoá sau 1 giờ) và 63 ứng dụng trong 1 giờ 41 phút; chưa đo (verify-round2 F8).
- Image id MinIO: results/logs/environment.txt dòng 10 (verify-round2 F9).
- Không có API dịch vụ: nhận xét từ cấu trúc mã; đề mục 6 (verify-round2 G3).
- Dòng 5 (mã nguồn công khai): người dùng xác nhận (2026-11-09). Remote origin: .git/config. Lệnh git clone theo verify-round2 E7, chưa chạy thử.
- Dung lượng ivy_cache: 1.067 MiB, điều phối viên đo trên máy thí nghiệm 2026-11-09; đã sửa ghi chú trong .gitignore cho khớp.
- Lệnh trong C.3 bước 4 dùng ivy_cache và ngắt dòng để trình bày; lệnh F.5 nguyên văn từ infra/README.md dùng /tmp/.ivy. Hai lệnh khác nhau có chủ ý.
-->
