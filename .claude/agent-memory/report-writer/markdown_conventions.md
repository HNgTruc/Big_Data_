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
- Không tự điền ngày truy cập URL (không có công cụ web); chỉ ghi ngày khi source-verifier hoặc điều phối viên đã mở trang.
- Phụ lục: tệp `95-phu-luc-<chữ>-<tên>.md`, dòng đầu `# Phụ lục A. Tên`, mục `## A.1 ...`. Thân bài dẫn tới bằng `@tbl:x (Phụ lục D)` hoặc `mục C.3`. Phát hiện và kết luận ở lại thân bài, chỉ bảng chi tiết sang phụ lục. Không tham chiếu `@fig:` trong chú thích hình.
- Phần sau tiền tố của nhãn cũng không trùng giữa `fig` và `tbl`. Tiêu đề nguồn có gạch ngang dài thì viết gạch nối hoặc dấu hai chấm, ghi chú trong VERIFY.
- Trích slide dạng `(slide chương N, tr. X [@slide-cN])`; `[@slide-cN, tr. X]` không khớp regex của script. Ký hiệu Amdahl: p là phần song song, N là số worker; slide dùng s, p khác. Không trích NIST. Tránh viết sát câu slide. Thân bài đã dài, nên dẫn sang mục khác thay vì lặp số. Tệp `00-tom-tat.md` đứng sau bìa theo thứ tự tên file.
- Mỗi khẳng định suy luận ghi rõ "(nhận định của người viết)"; khi chỉ có hướng dẫn mà không có ghi nhận đã làm thì viết đúng như vậy, không khẳng định như sự kiện.

**Why:** điều phối viên giao quy ước này 2026-11-08; báo cáo Word sinh tự động.
**How to apply:** mọi lần viết/sửa trong report/sections. Xem [[chapter-status]].
