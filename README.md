# Đồ án Nhập môn dữ liệu lớn — Quy trình Storage → Processing (Spark)

Đồ án học phần **Nhập môn dữ liệu lớn** (Trường Đại học Sài Gòn).
Phạm vi: giai đoạn **Storage → Processing** trong pipeline Big Data, dùng Apache Spark/PySpark
để làm sạch, chuẩn hóa, join và tổng hợp dữ liệu thương mại điện tử trên Data Lake (MinIO).

**Tên đề tài:** Đánh giá hiệu năng xử lý phân tán dữ liệu giao dịch thương mại điện tử với PySpark và MinIO

**Lớp:** DCT123C3. **Giảng viên:** Vũ Ngọc Thanh Sang. **Nhóm:** Huỳnh Ngọc Trúc, Phạm Trần Minh Khang, Tạ Quang Trung, Ngô Nguyễn Thành Nhân.

Dữ liệu là **dữ liệu mô phỏng** sinh bằng script (seed 42), không phải dữ liệu thật.

## Chạy thử từ máy trống

Cần Docker Desktop trên WSL2 (máy thí nghiệm giới hạn WSL2 ở 6 GB), Python 3.12, Internet cho lần kéo image và tải jar đầu tiên. Các lệnh dưới đây chạy trong PowerShell, trên bộ nhỏ nhất `orders_500k`.

```powershell
git clone https://github.com/HNgTruc/Big_Data_.git
cd Big_Data_
python -m venv .venv-exp
.\.venv-exp\Scripts\Activate.ps1
pip install -r src/experiments/requirements.txt
pip install -r src/data_generation/requirements.txt

# Sinh dữ liệu. Bắt buộc có --overwrite vì repo đã chứa manifest.json của bộ này
python -m src.data_generation.generate --orders 500000 --overwrite

# Dựng cụm: tạo .env rồi đổi mật khẩu MinIO trước khi chạy tiếp
cd infra
copy .env.example .env
docker compose up -d
docker compose ps

# Chép dữ liệu lên MinIO rồi chạy job ETL; thành công khi thấy dòng ETL_OK
docker compose run --rm minio-init cp --recursive /data/raw/orders_500k local/bigdata/raw/
docker compose run --rm --no-deps --name etl-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=etl-driver --conf spark.jars.ivy=/tmp/.ivy --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/etl_job.py --dataset orders_500k 2>&1 | Select-String "ETL_OK|ERROR|Exception|Traceback"
```

Dùng `docker compose run`, không dùng `docker compose exec` (lý do ở [infra/README.md](infra/README.md)). Giao diện: Spark Master http://localhost:8090, MinIO Console http://localhost:9001. Kết quả: `curated/orders_500k/`, `quarantine/orders_500k/` trên MinIO và `results/metrics/orders_500k.json` trên máy.

Các bước không cần Docker đã được chạy thử trên một bản clone mới (`results/logs/test_clone.log`). Các bước cần Docker đã chạy trên máy thí nghiệm nhưng chưa chạy lại trên bản clone.

Toàn bộ các bước (5 bộ dữ liệu, 7 thí nghiệm, phân tích, kiểm thử, dựng báo cáo) ở Phụ lục F của báo cáo, nguồn tại [report/sections/95-phu-luc-f-huong-dan-chay.md](report/sections/95-phu-luc-f-huong-dan-chay.md). Lưu ý khi chạy lại trên bản clone: `run_all` cần `--overwrite`; `analyze_all` ghi đè hai tệp `plan_check.csv`, khôi phục bằng `git checkout`.

## Bản đồ thư mục

| Thư mục | Nội dung | Đọc README |
|---|---|---|
| `.claude/` | Cấu hình agent: CLAUDE.md, rules, skills, agents, memory, hook | [.claude/README.md](.claude/README.md) |
| `docs/` | Yêu cầu đồ án và tài liệu tham khảo (có nguồn) | [docs/README.md](docs/README.md) |
| `docs/design/` | Schema dữ liệu và thiết kế | [docs/design/README.md](docs/design/README.md) |
| `infra/` | Hạ tầng chạy thí nghiệm (Docker Compose: Spark + MinIO) | [infra/README.md](infra/README.md) |
| `src/` | Mã nguồn: sinh dữ liệu, ETL Spark, thí nghiệm | [src/README.md](src/README.md) |
| `src/experiments/` | Bộ thí nghiệm hiệu năng (a)–(g): chạy, đo, phân tích | [src/experiments/README.md](src/experiments/README.md) |
| `data/` | Dữ liệu thô / đã xử lý / bản ghi lỗi (không đưa lên git) | [data/README.md](data/README.md) |
| `results/` | Log, số đo, hình — bằng chứng thực nghiệm | [results/README.md](results/README.md) |
| `report/` | Báo cáo theo đúng cấu trúc đề yêu cầu | [report/README.md](report/README.md) |
| `report/build/` | Script sinh file Word báo cáo từ Markdown và vẽ sơ đồ kiến trúc | [report/build/README.md](report/build/README.md) |
| `report/figures/` | Hình dùng riêng cho báo cáo: sơ đồ kiến trúc, ảnh chụp đã cắt khung | [report/figures/README.md](report/figures/README.md) |
| `report/review/` | Kết quả các vòng kiểm chứng báo cáo | [report/review/README.md](report/review/README.md) |
| `report/sections/` | Nội dung từng chương báo cáo (Markdown, nguồn để sinh file Word) | [report/sections/README.md](report/sections/README.md) |
| `tests/` | Kiểm thử cho các job | [tests/README.md](tests/README.md) |

## Quy ước
- Ở thư mục gốc chỉ có `README.md` và `.gitignore`; mọi file khác nằm trong thư mục.
- Mỗi thư mục có README mô tả nội dung và đường dẫn tới thư mục con.
- Tài liệu bằng tiếng Việt, mã nguồn bằng tiếng Anh.
- Không bịa số liệu hay trích dẫn: mọi con số trong báo cáo phải truy được về `results/`.
