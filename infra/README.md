# infra — hạ tầng chạy thí nghiệm

Docker Compose dựng MinIO (lưu trữ kiểu S3) và Spark standalone (1 master + 2 worker). Máy thí nghiệm: 16 GB RAM, Docker Desktop/WSL2 giới hạn 6 GB.

**Trạng thái: cụm đã chạy và đã kiểm tra kết nối Spark - MinIO (xem mục "Kết quả đã xác nhận").**

Lịch sử kiểm chứng: Đã xác nhận trên máy người dùng (2026-11-06):
- `apache/spark:4.0.0-python3` kéo được; chứa Hadoop **3.4.1** (`hadoop-client-api-3.4.1.jar`) → dùng `hadoop-aws` 3.4.1.
- `minio/minio`, `minio/mc` (Docker Hub) và `quay.io/minio/*` (cả `latest` lẫn tag cố định) **không kéo được** (bị từ chối).
- `cgr.dev/chainguard/minio` và `minio-client` (Chainguard) kéo được; entrypoint là `/usr/bin/minio` và `/usr/bin/mc`; image client **không có shell**.

Vì vậy MinIO lấy từ Chainguard. Nguồn tham khảo: [bài của bex.co](https://bex.co/blog/2026/09/25/minio-docker-hub-removal-quay-repoint) và [bài của Chainguard](https://www.chainguard.dev/unchained/secure-and-free-minio-chainguard-containers). Bản MinIO đã đo ghi ở `results/logs/environment.txt`; thẻ `latest` có thể đổi theo thời gian. Lý do chọn nguồn image này ở mục 5.1 của báo cáo.

## Thành phần

| Service | Vai trò | Cổng |
|---|---|---|
| `minio` | lưu trữ đối tượng, API S3 và console | 9000, 9001 |
| `minio-init` | tạo bucket `MINIO_BUCKET` rồi thoát | — |
| `spark-master` | quản lý cluster, UI | 7077, 8090 |
| `spark-worker-1/2` | chạy executor, mỗi worker `SPARK_WORKER_CORES` lõi, `SPARK_WORKER_MEMORY` RAM | 8091, 8092 |

`data/`, `src/` (chỉ đọc) và `results/` được mount vào `/opt/spark/work-dir/` trong container Spark.

## Chuẩn bị

1. `copy .env.example .env` rồi đổi mật khẩu MinIO (nếu mật khẩu có ký tự đặc biệt phải mã hoá URL vì dùng trong `MC_HOST_local`).
2. `docker pull` ba image trong `.env` (đã kéo được ở mục Trạng thái).

## Chạy

```bash
cd infra
docker compose up -d
docker compose ps          # master, 2 worker, minio phải Up; minio-init thoát mã 0
```

UI: Spark http://localhost:8090 (cổng 8080 trên máy người dùng đã bị chiếm nên đổi; chỉnh bằng `SPARK_MASTER_UI_PORT` trong `.env`) ; MinIO console http://localhost:9001.
Dừng: `docker compose down` (thêm `-v` để xoá dữ liệu MinIO).

## Cần xác nhận sau khi chạy lần đầu

- Worker đăng ký với master (UI http://localhost:8090 thấy 2 worker).
- Job đọc/ghi được `s3a://<bucket>/...` với `hadoop-aws` đúng phiên bản (thêm qua `spark.jars.packages` khi submit). Cấu hình S3A cần `fs.s3a.endpoint=http://minio:9000` và `fs.s3a.path.style.access=true`.
- Tổng RAM Docker Desktop đủ cho 2 worker (WSL2 mặc định có thể thấp hơn 8 GB).

## Kiểm tra Spark - MinIO

Xác nhận (2026-11-06): cụm có 2 worker ALIVE, 4 lõi, 4 GiB (UI master).
Job `src/etl/smoke_s3a.py` ghi rồi đọc lại 1 triệu dòng Parquet qua `s3a://bigdata/smoke/`. Chạy trong thư mục `infra`:

```powershell
docker compose run --rm --no-deps --name smoke-driver spark-master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --conf spark.driver.host=smoke-driver `
  --conf spark.jars.ivy=/tmp/.ivy `
  --packages org.apache.hadoop:hadoop-aws:3.4.1 `
  /opt/spark/work-dir/src/etl/smoke_s3a.py
```

Thành công khi thấy dòng `SMOKE_OK rows_written=1000000 rows_read=1000000`. Lần đầu cần Internet để tải `hadoop-aws` và các phụ thuộc của nó.
Không dùng `docker compose exec` (xem mục "Kết quả đã xác nhận"). Job này đã chạy thành công ngày 2026-11-06 bằng `exec` (driver trong container master); dạng `run` ở trên dùng cùng cách gọi như lệnh ETL (đã chạy nhiều lần), riêng job smoke chưa chạy lại theo dạng này.

## Kết quả đã xác nhận (2026-11-06, máy người dùng: 15,8 GB RAM, Windows, Docker Desktop + WSL2)

- Cụm lên được; UI master (http://localhost:8090) thấy 2 worker ALIVE, 4 lõi, 4 GiB.
- Job `smoke_s3a.py` in `SMOKE_OK rows_written=1000000 rows_read=1000000 path=s3a://bigdata/smoke/range` (Spark 4.0.0, `hadoop-aws:3.4.1`, `awssdk bundle 2.24.6`).
- Chạy job bằng `docker compose run` (không dùng `docker compose exec`, vì exec gặp lỗi `500`/`No such exec instance` khi engine sập).

### Sự cố engine Docker Desktop sập khi chạy job
- Hiện tượng: toàn bộ container `Exited (255)` và engine WSL2 khởi động lại; log Docker Desktop ghi `wsl-bootstrap ... exit status 0xc00000fd` (22:45:11) và client báo `unexpected EOF` (23:05:23).
- Có báo cáo lỗi tương tự (mã `0xc00000fd`, kernel WSL `6.18.54.1`) tại docker/desktop-feedback #767; nguyên nhân chưa được xác nhận ở đó (nghi áp lực bộ nhớ).
- Giới hạn Docker lúc sập là 9,7 GiB trên máy 15,8 GB đang dùng ~72%. Sau khi đặt `C:\Users\<tên>\.wslconfig` với `memory=6GB`, `processors=8` (giới hạn thành 5,79 GiB), job chạy thành công **một lần**. Chưa đủ để khẳng định đây là nguyên nhân; theo dõi tiếp khi chạy job lớn.
- Nếu sập lại: thử tắt Radmin VPN (nghi vấn thứ hai, chưa có bằng chứng), xem Event Viewer của `wslservice.exe`.

### Dung lượng đĩa (2026-11-07)
- Sau 7 lần chạy, `/opt/spark/work` trên mỗi worker chiếm khoảng 4,1 GB: mỗi ứng dụng chép lại các jar của `--packages` vào thư mục riêng và theo mặc định worker chỉ xoá sau 7 ngày. Ổ C còn 2,6 GB vì `docker_data.vhdx` (37,7 GB) nằm trên C.
- Đã xử lý: rút ngắn chu kỳ dọn của worker (`spark.worker.cleanup.*`: mặc định quét 30 phút/lần và giữ 7 ngày, nay quét 10 phút/lần và xoá thư mục của ứng dụng đã kết thúc quá 1 giờ) và ổ đĩa Docker được chuyển sang `D:\Data\DockerDesktopWSL`.
- Hệ quả: log executor (`stderr`) của một lần chạy chỉ còn trên worker khoảng 1 giờ. Log driver vẫn lưu trong `results/logs/`.
- Lưu ý khi chạy cả bộ thí nghiệm: mỗi ứng dụng vẫn chép jar vào thư mục làm việc của worker (bộ đệm Ivy chỉ tránh tải lại ở driver), và thư mục chỉ bị xoá sau 1 giờ, nên trong lúc chạy liên tục dung lượng `/opt/spark/work` sẽ tăng theo số lần chạy trong một giờ. Theo dõi dung lượng ổ D.
- Ổ C và ổ D là hai phân vùng của **cùng một ổ đĩa vật lý** (bộ đếm `PhysicalDisk(0 c: d:)`), nên chuyển sang D chỉ giải quyết dung lượng, không giảm tranh chấp I/O. Trước khi đo chính thức: tạm dừng Windows Update, đóng Chrome/Discord, dừng container không liên quan.

## Đưa dữ liệu thô lên MinIO

Image `minio-client` không có shell nên dùng `compose run` với lệnh `mc` trực tiếp (thư mục `data/` được mount chỉ đọc vào `/data`).
`mc cp --recursive` chép **cả thư mục nguồn** vào đích, nên đích phải là `raw/` (không phải `raw/orders_500k`), nếu không dữ liệu bị lồng thêm một cấp:

```powershell
docker compose run --rm minio-init cp --recursive /data/raw/orders_500k local/bigdata/raw/
docker compose run --rm minio-init ls --recursive --summarize local/bigdata/raw/orders_500k
```

Kết quả đúng: 6 object, đường dẫn dạng `customers.csv`, `orders.csv`... (không có thêm `orders_500k/` phía trước).
Nếu đã lỡ chép lồng (lần đầu 2026-11-06): xoá rồi chép lại bằng `docker compose run --rm minio-init rm --recursive --force local/bigdata/raw/orders_500k`.

## Chạy job ETL

Điều kiện: dữ liệu thô đã có trên MinIO (mục "Đưa dữ liệu thô lên MinIO"). Trong thư mục `infra`:

```powershell
docker compose run --rm --no-deps --name etl-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=etl-driver --conf spark.jars.ivy=/tmp/.ivy --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/etl_job.py --dataset orders_500k 2>&1 | Select-String "ETL_OK|ERROR|Exception|Traceback"
```

- Thành công khi thấy dòng `ETL_OK processing_seconds_total=...`.
- Kết quả: `curated/orders_500k/`, `quarantine/orders_500k/` trong bucket (xem MinIO Console http://localhost:9001) và `results/metrics/orders_500k.json` trên máy.
- Thêm `--join-strategy broadcast|shuffle`, `--run-label <tên>` để chạy thí nghiệm mà không ghi đè kết quả cũ.
- Lệnh này đã chạy cho cả 5 bộ dữ liệu (log `results/logs/etl_<bộ>.log`). Các thí nghiệm trong `src/experiments/` dùng cùng lệnh, thêm `--conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache` để không tải lại jar mỗi lần (xem `data/README.md`).
- Bộ nhớ: worker cho phép tối đa `SPARK_WORKER_MEMORY` (2g), nhưng lệnh không đặt `--executor-memory` nên mỗi executor dùng heap mặc định 1g (`spark.executor.memory`, tài liệu Spark Configuration). Giữ nguyên vì Docker Desktop từng sập dưới giới hạn 6 GB.
