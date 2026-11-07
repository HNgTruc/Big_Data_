# tests — kiểm thử

Kiểm thử cho mã trong `src/`, chạy trên dữ liệu rất nhỏ (sinh trong thư mục tạm, không cần MinIO).

| File | Nội dung |
|---|---|
| `test_data_generation.py` | Bộ sinh dữ liệu: schema, tỉ lệ lỗi, khoá `(order_id, line_no)`, manifest (12 test) |
| `test_etl.py` | ETL chạy `local`: quarantine và bỏ trùng khớp manifest, chuẩn hoá ngày, bỏ trùng `order_items` theo khoá (14 test) |
| `run_in_container.sh` | Chạy cả hai file trong image Spark của cụm (Linux) |
| `conftest.py`, `requirements.txt` | Cho phép `import src...`; phụ thuộc của test |

## Cách chạy khuyến nghị: trong container Spark (Linux)

Trong thư mục `infra/` (PowerShell), cụm không cần đang chạy:

```powershell
docker compose run --rm --no-deps -v ${PWD}/../tests:/opt/spark/work-dir/tests:ro --entrypoint bash spark-master /opt/spark/work-dir/tests/run_in_container.sh
```

Script cài `numpy`, `pandas`, `pyarrow`, `pytest` vào `/tmp` của container tạm (cần Internet), rồi chạy `pytest`.
Kết quả 2026-11-07: **26 passed** (Python 3.10.12, pyspark 4.0.0, numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1); log ở `results/logs/test_etl.log`.

## Chạy trực tiếp trên máy

```bash
pip install -r tests/requirements.txt
python -m pytest -q tests/test_data_generation.py
```

- `test_data_generation.py`: 12 passed trên Windows `.venv` (Python 3.12.10, pandas 3.1.1), 2026-11-07.
- `test_etl.py` **không chạy được trên Windows** dù có pyspark 4.0.0 và JDK 17: Python worker của Spark bị crash khi tạo DataFrame từ dữ liệu Python, và ghi Parquet cần `HADOOP_HOME`/`winutils.exe`. Vì vậy dùng cách chạy trong container ở trên.
