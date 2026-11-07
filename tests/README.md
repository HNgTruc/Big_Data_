# tests — kiểm thử

Kiểm thử cho mã trong `src/`, chạy trên dữ liệu rất nhỏ (sinh trong thư mục tạm, không cần MinIO).

| File | Nội dung |
|---|---|
| `test_data_generation.py` | Bộ sinh dữ liệu: schema, tỉ lệ lỗi, khoá `(order_id, line_no)`, manifest (12 test) |
| `test_etl.py` | ETL chạy `local`: quarantine và bỏ trùng khớp manifest, chuẩn hoá ngày, bỏ trùng `order_items` theo khoá (14 test) |
| `test_experiments.py` | Bộ thí nghiệm `src/experiments/`: thống kê, speedup/efficiency, dựng lệnh docker, kiểm tra worker ALIVE, dọn MinIO trước mỗi lần, run record, event log, cờ chất lượng và tính đồng nhất, kế hoạch các thí nghiệm (29 test, không cần Docker/Spark) |
| `test_experiments_pandas.py` | Baseline Pandas: luật làm sạch trên bảng dựng tay, đối chiếu hằng số với `src/etl/`, chạy trọn trên bộ sinh nhỏ, mã thoát 3 khi lệch (15 test) |
| `test_query_bench.py` | Job truy vấn `src/experiments/common/query_bench.py` chạy Spark local: truy vấn `format` cho cùng kết quả trên dữ liệu thô sạch và Parquet, ghi kích thước/thứ tự/khởi động; truy vấn `cache` cùng kết quả có/không cache và `unpersist` giải phóng bộ nhớ đệm (3 test; bị bỏ qua trên Windows) |
| `test_export_samples.py` | Job xuất mẫu `src/etl/export_samples.py`: chọn mẫu xác định trên bảng dựng tay (trùng, ngày sai định dạng, quarantine theo lý do, `region` thiếu, sắp theo khoá kiểu số), so sánh số đếm với metrics, chạy trọn trên bộ sinh nhỏ (12 test; bị bỏ qua trên Windows) |
| `test_build_docx.py` | Script dựng Word `report/build/build_docx.py` trên fixture Markdown nhỏ dựng trong thư mục tạm (kèm PNG tự tạo): đánh số hình/bảng theo chương, tham chiếu tới hình phía sau, trích dẫn theo thứ tự xuất hiện, bỏ chú thích HTML, tô vàng `[CHƯA CÓ: …]`, ảnh thiếu không làm dừng, bìa và trang thông tin không vào đánh số chương, trường TOC/SEQ, mã thoát (12 test; chạy trên host, cần `python-docx`) |
| `run_in_container.sh` | Chạy `test_etl.py`, `test_data_generation.py`, `test_query_bench.py`, `test_export_samples.py` trong image Spark của cụm (Linux) |
| `conftest.py`, `requirements.txt` | Cho phép `import src...`; phụ thuộc của test |

## Cách chạy khuyến nghị: trong container Spark (Linux)

Trong thư mục `infra/` (PowerShell), cụm không cần đang chạy:

```powershell
docker compose run --rm --no-deps -v ${PWD}/../tests:/opt/spark/work-dir/tests:ro --entrypoint bash spark-master /opt/spark/work-dir/tests/run_in_container.sh
```

Script cài `numpy`, `pandas`, `pyarrow`, `pytest` vào `/tmp` của container tạm (cần Internet), rồi chạy `pytest`.
Kết quả 2026-11-08 (sau khi thêm `test_export_samples.py`): **41 passed** (Python 3.10.12, pyspark 4.0.0, numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1, pytest 9.2.0); log ở `results/logs/test_etl.log`. Lần trước (2026-11-07, chưa có test này): 29 passed.

Mạng chậm làm `pip` hết thời gian chờ (lần chạy 2026-11-08 đầu tiên dừng ở bước cài gói). Cách tránh: tải sẵn wheel Linux cp310 vào một thư mục ngoài repo (`pip download --platform manylinux2014_x86_64 --python-version 3.10 --only-binary=:all: -d <dir> numpy==2.2.6 pandas==2.3.3 pyarrow==25.0.1 "pytest>=8" exceptiongroup tomli typing_extensions`) rồi thêm vào lệnh trên `-e PIP_NO_INDEX=1 -e PIP_FIND_LINKS=/wheels -v <dir>:/wheels:ro`. `exceptiongroup`, `tomli` phải ghi rõ vì `pip download` xét điều kiện phụ thuộc theo Python của máy chạy lệnh, không theo `--python-version`.

## Chạy trực tiếp trên máy

```bash
pip install -r tests/requirements.txt
python -m pytest -q tests/test_data_generation.py
```

- `test_data_generation.py`: 12 passed trên Windows `.venv` (Python 3.12.10, pandas 3.1.1), 2026-11-07.
- `test_experiments.py` + `test_experiments_pandas.py`: 44 passed (2026-11-07) trên Windows, cả trong `.venv` của repo (không có matplotlib: bỏ qua vẽ hình) lẫn `.venv-exp` có `src/experiments/requirements.txt` (Python 3.12.10, pandas 3.1.1, pyarrow 26.0.1, matplotlib 3.11.2, pytest 9.2.0). Chạy: `python -m pytest -q tests/test_experiments.py tests/test_experiments_pandas.py`. `test_query_bench.py` bị bỏ qua trên Windows.
- `test_build_docx.py`: 12 passed (2026-11-08) trên Windows `.venv-exp` (Python 3.12.10, python-docx 1.2.0, pytest 9.2.0) sau khi cài `report/build/requirements.txt`. Chạy: `.\.venv-exp\Scripts\python.exe -m pytest -q tests/test_build_docx.py`. Thiếu `python-docx` thì file này bị bỏ qua.
- `test_etl.py` **không chạy được trên Windows** dù có pyspark 4.0.0 và JDK 17: Python worker của Spark bị crash khi tạo DataFrame từ dữ liệu Python, và ghi Parquet cần `HADOOP_HOME`/`winutils.exe`. Vì vậy dùng cách chạy trong container ở trên.
