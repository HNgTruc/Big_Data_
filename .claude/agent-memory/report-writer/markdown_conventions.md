---
name: markdown-conventions
description: Quy ước Markdown bắt buộc cho report/sections (script sinh Word ở report/build dựa vào), bộ quy tắc văn phong "không rập khuôn" của người dùng, thuật ngữ và cách ghi số
metadata:
  type: feedback
---

Báo cáo được script trong `report/build/` chuyển từ `report/sections/*.md` sang Word. Phải giữ đúng cú pháp:
- `# Chương N. Tên` (bìa `# BÌA`), mục `## 6.1 ...`, tối đa `####`.
- Hình: `![chú thích không số](đường/dẫn.png){#fig:nhan}` + dòng sau `Nguồn: ...`. Bảng: `Bảng: chú thích {#tbl:nhan}` ngay trước bảng pipe, `Nguồn: ...` ngay sau. Không gộp ô.
- Tham chiếu `@fig:x`, `@tbl:x`; trích dẫn `[@khoa]`; trích slide dạng `(slide chương N, tr. X [@slide-cN])`.
- `[CHƯA CÓ: lý do]`; khối `<!-- VERIFY ... -->` cuối mỗi tệp; không LaTeX, footnote, HTML khác.
- Số kiểu Việt: 21,90; 20.931.505; ghi rõ MB = 10^6 byte.
- Thuật ngữ: cách ly (quarantine), bỏ trùng, chuẩn hoá, giai đoạn (dimensions/orders/order_items/web_events/aggregates), biến thể ép shuffle, gộp phân vùng, tách phân vùng lệch, dữ liệu mô phỏng.
- Phụ lục: `# Phụ lục A. Tên`, mục `## A.1`; thêm mục con vào cuối phụ lục, đánh số tiếp. Thân bài dẫn bằng `@tbl:x (Phụ lục D)` hoặc `mục C.3`. Mọi nhãn đã chuyển nên có ít nhất một tham chiếu.

Văn phong (người dùng yêu cầu 2026-11-16, áp cho 00-tom-tat, 01–09, 95-a..g; không áp cho bảng, mã, Nguồn, chú thích, 00-bia, 90, VERIFY):
- Cấm: mở bài chung chung, từ nối đầu câu kiểu "Ngoài ra/Bên cạnh đó/Tóm lại", từ thổi phồng, động từ sáo ("tận dụng", "góp phần", "thúc đẩy"...), ẩn dụ sáo, "một cách + tính từ", "thực sự", "không chỉ... mà còn", "sử dụng/thực hiện/hỗ trợ" (thay dùng/làm/giúp).
- Không dấu ";" và "—" trong văn xuôi, không in đậm giữa câu, ngoặc kép thẳng. Cụm mở đoạn in đậm chỉ dùng như tiêu đề nhỏ, dùng ít.
- Lập luận viết thành đoạn, không gạch đầu dòng; danh sách chỉ cho bước, thông số, tên tệp.
- Viết chủ ngữ thật thay bị động khi biết ai làm ("Job ghi", "Nhóm đo"). Bỏ câu "Chương này trình bày..." nếu không mang thông tin.
- Không xoá nhãn nguồn "nhận định của nhóm", "suy luận", "chưa đo", "theo mã". Ràng buộc số liệu, nhãn, trung thực thắng văn phong.
- Tự rà bằng Grep danh sách từ cấm và `^[^|\-].*[;—]` trước khi bàn giao; dòng `^- ` có ";" phải nằm sau dòng VERIFY.

**Why:** điều phối viên giao quy ước 2026-11-08; người dùng thêm bộ quy tắc văn phong 2026-11-16. Báo cáo Word sinh tự động.
**How to apply:** mọi lần viết/sửa trong report/sections. Xem [[chapter-status]].
