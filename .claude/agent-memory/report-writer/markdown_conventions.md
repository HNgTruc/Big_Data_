---
name: markdown-conventions
description: Quy ước Markdown bắt buộc cho report/sections (script sinh Word ở report/build dựa vào), thuật ngữ và cách ghi số đã thống nhất
metadata:
  type: feedback
---

Báo cáo được script trong `report/build/` (agent khác viết) chuyển từ `report/sections/*.md` sang Word. Phải giữ đúng cú pháp:
- `# Chương N. Tên` (bìa `# BÌA`), mục `## 6.1 ...`, tối đa `####`.
- Hình: `![chú thích không số](đường/dẫn/từ/gốc/repo.png){#fig:nhan}` + dòng sau `Nguồn: results/...`. Không đặt dòng hình với đường dẫn chưa tồn tại (dùng `[CHƯA CÓ: ...]`), không viết chuỗi `{#fig:...}` trong văn bản thường.
- Bảng: `Bảng: chú thích {#tbl:nhan}` ngay trước bảng pipe, `Nguồn: ...` ngay sau. Không gộp ô.
- Tham chiếu `@fig:x`, `@tbl:x`; trích dẫn `[@khoa]`, danh sách ở `90-tai-lieu-tham-khao.md` dạng `[@khoa]: ...` mỗi dòng một mục.
- `[CHƯA CÓ: lý do]`; khối `<!-- VERIFY ... -->` cuối mỗi tệp; không LaTeX, không footnote, không gạch ngang dài (—) trong văn bản (– chỉ cho khoảng số).
- Số kiểu Việt: 21,90; 20.931.505; ghi rõ MB = 10^6 byte.
- Thuật ngữ: cách ly (quarantine), bỏ trùng, chuẩn hoá, giai đoạn (giữ tên dimensions/orders/order_items/web_events/aggregates), biến thể ép shuffle, gộp phân vùng, tách phân vùng lệch, dữ liệu mô phỏng.
- Không tự điền ngày truy cập URL (không có công cụ web).

**Why:** điều phối viên giao quy ước này 2026-11-08; báo cáo Word sinh tự động.
**How to apply:** mọi lần viết/sửa trong report/sections. Xem [[chapter-status]].
