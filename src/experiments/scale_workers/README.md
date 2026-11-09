# scale_workers — (b) 1 worker so với 2 worker

**Trạng thái: đã đo chính thức ngày 2026-11-07 (commit 8164042).** Số đo ở `results/metrics/scale_workers/`, hình ở `results/figures/scale_workers/`.

- **Mục tiêu:** tính speedup S = T(1 worker) / T(2 worker) và efficiency E = S / 2 trên orders_5m (công thức ở slide chương 2).
- **Giả thuyết (chưa kiểm chứng):** 1 < S < 2 vì có phần tuần tự (driver, ghi metadata, đọc từ MinIO dùng chung) và chi phí shuffle; đối chiếu định luật Amdahl khi phân tích.
- **Biến thay đổi:** số worker ALIVE (1 hoặc 2). Cả hai cấu hình chạy trong cùng thí nghiệm, không mượn số của `scale_data`.
- **Biến cố định:** orders_5m, auto join, AQE bật, `shuffle.partitions=8`, mỗi worker 2 lõi; worker cho phép tối đa 2 GB (`SPARK_WORKER_MEMORY`) nhưng executor dùng heap mặc định 1 GB vì không đặt `spark.executor.memory` (mặc định 1g theo tài liệu Spark Configuration; giá trị thực ghi ở `resources` trong metrics), seed 42.
- **Chỉ số:** như `scale_data`, cộng `speedup`, `efficiency` (tính từ trung bình) cho tổng thời gian và từng giai đoạn.

## Cách dừng/bật worker

Trước các lần `w1`: `docker compose stop spark-worker-2` (cwd `infra`), chờ đến khi master báo **đúng 1 worker ALIVE** (worker đã dừng có thể vẫn hiện DEAD — chỉ đếm ALIVE). Sau đó **luôn** `docker compose start spark-worker-2` và chờ 2 worker ALIVE, kể cả khi lần chạy lỗi hoặc bị Ctrl+C (`try/finally`). Mặc định `--order blocked` để chỉ dừng/bật một lần. Nếu trước khi dừng mà master không thấy đúng 2 worker ALIVE, thí nghiệm dừng và không đụng vào container.

## Cách chạy (PowerShell, thư mục gốc repo)

```powershell
python -m src.experiments.scale_workers.run --dry-run
python -m src.experiments.scale_workers.run
python -m src.experiments.scale_workers.analyze
```

Nếu bộ chạy bị dừng đột ngột (tắt cửa sổ), kiểm tra http://localhost:8090 và chạy `docker compose start spark-worker-2` trong `infra/` nếu cần.

## Đầu ra

`results/metrics/scale_workers/{runs/, runs.csv, summary.csv}` (cột `speedup`, `efficiency` ở dòng `w2`), `results/figures/scale_workers/speedup.png`.

## Lưu ý

Với 1 worker, cụm chỉ còn 1 executor (2 lõi, heap 1 GB); bộ 5m có thể tràn bộ nhớ ra đĩa nhiều hơn. Nếu lần chạy lỗi vì hết bộ nhớ, ghi lại nguyên nhân (record `status=failed`), không loại bỏ.
