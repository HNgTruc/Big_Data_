# metrics

Số đo dạng CSV nhỏ; ghi giá trị từng lần chạy, không chỉ trung bình.

- `<bộ>.json`: metrics của lần chạy ETL đầu tiên từng bộ (một lần, máy chưa sạch; chỉ tham khảo). Bộ thí nghiệm không ghi đè các file này.
- `<exp>/` (tạo khi chạy `src/experiments/<exp>/run.py`, kèm README): `runs/<config>/r<k>/run_record.json` + metrics của job
  cho từng lần lặp (kể cả lần lỗi); `runs.csv`, `summary.csv` và bảng phụ (`plan_check.csv`, `sizes.csv`, `break_even.csv`,
  `comparison_spark.csv`) do `analyze.py` sinh lại được bất cứ lúc nào.

- `skew/partition_stats*.csv`: kích thước phân vùng băm theo `product_id` (bằng chứng chọn tham số của thí nghiệm `skew`, không phải số đo thời gian).

Trạng thái thí nghiệm: chưa chạy.
