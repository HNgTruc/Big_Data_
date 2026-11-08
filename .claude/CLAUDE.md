# CLAUDE.md — Đồ án Nhập môn dữ liệu lớn (Storage → Processing)

## Bối cảnh
- Học phần Nhập môn dữ liệu lớn, Trường Đại học Sài Gòn. Giữa kỳ và cuối kỳ được coi là **một đồ án**.
- Quy trình con đã chọn: **Storage → Processing** (Spark/PySpark) trong pipeline
  Sources → Ingestion → Storage → Processing → Analytics → Presentation → Decision/Action.
- Sản phẩm tối thiểu theo đề: job xử lý phân tán; dữ liệu trước/sau xử lý; thống kê chất lượng và thời gian xử lý.

## Quyết định đã chốt (do người dùng xác nhận)
- Miền dữ liệu: thương mại điện tử. Dữ liệu **sinh bằng script** (phải ghi rõ là dữ liệu mô phỏng).
- Lớp lưu trữ nguồn: **MinIO**. Chạy Spark bằng **Docker Compose nhiều worker**.
- Máy thí nghiệm có **16 GB RAM** (15,8 GB khả dụng); Docker Desktop/WSL2 giới hạn **6 GB** qua `.wslconfig`: giới hạn thí nghiệm khoảng 5–10 triệu dòng, tối đa 2 worker. Phải nêu giới hạn này trong báo cáo.
- Ngôn ngữ: tài liệu tiếng Việt, mã nguồn (tên biến, hàm, commit) tiếng Anh.
- Nhóm 4 thành viên: Huỳnh Ngọc Trúc (3123411312), Phạm Trần Minh Khang (3123411143), Tạ Quang Trung (3123411318), Ngô Nguyễn Thành Nhân (3123411205). Phân công thực tế: chưa có.
- Tên đề tài (đã chọn): Đánh giá hiệu năng xử lý phân tán dữ liệu giao dịch thương mại điện tử với PySpark và MinIO.
- Schema: 5 bảng `orders`, `order_items`, `customers` (CSV), `products` (Parquet), `web_events` (JSON lines) — chi tiết ở `docs/design/schema.md`.
- Dữ liệu bẩn sẽ chèn: bản ghi trùng, giá trị thiếu, giá trị không hợp lệ, sai định dạng ngày; **2% mỗi loại**.
- Kích thước `orders`: 0.5M, 1M, 2.5M, 5M dòng. `order_items` khoảng 2 dòng/đơn. Có tham số bật/tắt độ lệch key.
- Lớp học phần cụ thể, phân công thực tế, hạn nộp (chưa cần): **chưa có** — không tự điền.

## Nguồn sự thật (đọc trước khi làm)
1. `docs/requirements/yeu-cau-do-an.md` — tóm tắt file `Yêu cầu đồ án.docx` (đề gốc nằm trên Google Drive của người dùng).
2. `docs/references/README.md` — danh mục slide chương 1–8 và tài liệu, kèm vị trí trên Drive.
3. Thiếu thông tin → quay lại slide/thư mục Tài liệu trên Drive; vẫn thiếu → hỏi người dùng. Không đoán.

## Bản đồ thư mục
Xem `README.md` ở gốc; mỗi thư mục có README riêng. Thư mục gốc chỉ có `README.md` và `.gitignore`.

## Quy trình làm việc
- Giải thích chức năng và lý do trước khi thêm skill, agent, hook mới.
- Cần thông tin để làm bước tiếp theo thì hỏi người dùng; chỉ làm khi đủ thông tin.
- Mỗi thí nghiệm lưu cấu hình, lệnh chạy, log và số đo vào `results/`.
- Số liệu trong báo cáo chỉ lấy từ `results/`. Kết quả không như kỳ vọng vẫn ghi trung thực và phân tích.
- Dùng AI đáng kể thì ghi vào phụ lục (mục 8 của đề): công cụ, mục đích, phần đã kiểm tra.

## Agent và skill
Xem `.claude/README.md`. Giao việc: sinh dữ liệu → `data-generator`; viết job Spark → `spark-etl-engineer`;
soát mã trước khi chạy thí nghiệm → `code-reviewer`;
chạy và đo thí nghiệm → `benchmark-analyst`; viết báo cáo → `report-writer`; kiểm chứng nguồn → `source-verifier`.
