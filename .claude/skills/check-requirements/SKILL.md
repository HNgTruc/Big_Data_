---
name: check-requirements
description: Đối chiếu sản phẩm hiện tại với file yêu cầu đồ án (mục 5, 6, 7 và thang điểm) và liệt kê mục còn thiếu. Dùng trước mỗi mốc nộp hoặc khi hỏi "đã đủ chưa".
---

# Kiểm tra yêu cầu đồ án

Nguồn chuẩn: `docs/requirements/yeu-cau-do-an.md`. Nếu nghi ngờ bản tóm tắt, đối chiếu lại file gốc trên Drive.

## Các bước
1. Đọc `docs/requirements/yeu-cau-do-an.md`.
2. Với từng mục bắt buộc 5.1–5.8, tìm bằng chứng trong repo (file, đường dẫn cụ thể):
   quy trình được chọn, bài toán và đặc trưng Big Data (≥ 2), input, output, công nghệ và lý do,
   sơ đồ luồng xử lý, kết quả demo/thực nghiệm, khả năng tái lập.
3. Với từng mục báo cáo 6.1 trong `report/`, ghi trạng thái: chưa có / đang viết / đủ.
4. Đối chiếu minh chứng cần nộp (mục 7): báo cáo PDF, mã nguồn + README chạy, nguồn/script sinh dữ liệu,
   minh chứng demo, bảng phân công, ghi chú dùng AI.
5. Chấm sơ bộ theo 6 tiêu chí của thang điểm, chỉ dựa trên bằng chứng có thật.

## Đầu ra
Bảng: Mục | Trạng thái (Đạt / Thiếu / Chưa kiểm chứng) | Bằng chứng (đường dẫn) | Việc cần làm.
Không đánh "Đạt" khi chưa mở và xác nhận file. Không bịa bằng chứng.
