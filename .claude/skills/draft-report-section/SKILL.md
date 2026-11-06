---
name: draft-report-section
description: Soạn một mục báo cáo theo cấu trúc 6.1 của file yêu cầu, chỉ dùng dữ liệu có thật trong results/ và nguồn đã xác minh. Dùng khi cần viết hoặc sửa một mục như Thiết kế hệ thống, Thực nghiệm, Thảo luận.
argument-hint: "<số mục hoặc tên mục>"
---

# Soạn một mục báo cáo

## Các bước
1. Xác định mục cần viết theo `.claude/rules/report-format.md` và `docs/requirements/yeu-cau-do-an.md`.
2. Thu thập dữ liệu: đọc `results/` (số đo, log, hình), `src/` (cấu hình, mã), `docs/references/README.md` (nguồn).
3. Lập dàn ý ngắn, rồi viết vào `report/sections/<số>-<tên>.md` (tạo thư mục kèm README nếu chưa có).
4. Mỗi con số, hình, bảng ghi nguồn (đường dẫn trong `results/`). Trích dẫn ngoài theo IEEE.
5. Phân biệt rõ: kết quả đo của đồ án / giải thích của slide hoặc tài liệu / nhận định của người viết.
6. Phần chưa có dữ liệu để dấu `[CHƯA CÓ: lý do]`, không viết thay bằng số giả định.
7. Kết thúc bằng danh sách khẳng định cần `source-verifier` kiểm tra.
