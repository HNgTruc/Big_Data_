# quarantine

Thư mục để trống. Job ETL mặc định ghi bản ghi lỗi kèm cột `reject_reason` lên MinIO (`s3a://bigdata/quarantine/`), không ghi vào đây; xem `src/etl/pipeline.py`.
