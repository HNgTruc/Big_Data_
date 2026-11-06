# tests — kiểm thử

Kiểm thử cho mã trong `src/`, chạy trên dữ liệu rất nhỏ. Chạy từ thư mục gốc repo:

```bash
pip install -r tests/requirements.txt
python -m pytest -q tests
```

Trạng thái: có `test_data_generation.py` (11 test, qua trên VM). `test_etl.py` (ETL chạy `local` trên dữ liệu sinh nhỏ) **đã viết nhưng chưa chạy được** vì máy soạn không cài được PySpark; cần PySpark, Java 17 (Spark 4) hoặc Java 11 (PySpark 3.5) trên máy chạy test. Đã kiểm chứng ETL trực tiếp trên cụm thay thế.
