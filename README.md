# Đồ án Nhập môn dữ liệu lớn — Quy trình Storage → Processing (Spark)

Đồ án học phần **Nhập môn dữ liệu lớn** (Trường Đại học Sài Gòn).
Phạm vi: giai đoạn **Storage → Processing** trong pipeline Big Data, dùng Apache Spark/PySpark
để làm sạch, chuẩn hóa, join và tổng hợp dữ liệu thương mại điện tử trên Data Lake (MinIO).

**Tên đề tài:** Đánh giá hiệu năng xử lý phân tán dữ liệu giao dịch thương mại điện tử với PySpark và MinIO

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
| `report/figures/` | Hình vẽ riêng cho báo cáo (sơ đồ kiến trúc) | [report/figures/README.md](report/figures/README.md) |
| `report/review/` | Kết quả các vòng kiểm chứng báo cáo | [report/review/README.md](report/review/README.md) |
| `report/sections/` | Nội dung từng chương báo cáo (Markdown, nguồn để sinh file Word) | [report/sections/README.md](report/sections/README.md) |
| `tests/` | Kiểm thử cho các job | [tests/README.md](tests/README.md) |

## Quy ước
- Ở thư mục gốc chỉ có `README.md` và `.gitignore`; mọi file khác nằm trong thư mục.
- Mỗi thư mục có README mô tả nội dung và đường dẫn tới thư mục con.
- Tài liệu bằng tiếng Việt, mã nguồn bằng tiếng Anh.
- Không bịa số liệu hay trích dẫn: mọi con số trong báo cáo phải truy được về `results/`.
