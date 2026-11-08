# report — báo cáo đồ án

Soạn theo `.claude/rules/report-format.md` (cấu trúc mục 6.1 của file yêu cầu). Nộp PDF.
Agent phụ trách: `report-writer`; kiểm chứng: `source-verifier`.

| Mục | Nội dung | Trạng thái |
|---|---|---|
| Bìa và thông tin nhóm | Tên đề tài, lớp, thành viên, phân công | Bản nháp (`sections/00-bia.md`); thiếu lớp, mã lớp, giảng viên, MSSV, ngày nộp |
| Tóm tắt | 150–250 từ | Chưa viết |
| 1–2 | Giới thiệu; Cơ sở và công nghệ liên quan | Chưa viết |
| 3–7 | Dữ liệu và yêu cầu; Thiết kế; Cài đặt; Thực nghiệm; Kết quả demo | Bản nháp 1 (2026-11-08), đã kiểm vòng 1 nhưng chưa sửa theo `review/verify-round1.md`; chương 4 thiếu sơ đồ kiến trúc; cần chuyển chi tiết sang phụ lục |
| 8–9 | Thảo luận; Kết luận | Chưa viết (ý chính đã ghi ở mục 6.11) |
| Tài liệu tham khảo | IEEE | Bản nháp, mới có nguồn của chương 3–7 |
| Phụ lục | Hướng dẫn chạy, cấu hình, schema, bảng phân công, ghi chú dùng AI | Chưa viết |

| Thư mục | Nội dung |
|---|---|
| [`sections/`](sections/README.md) | Nội dung từng chương (Markdown) và quy ước định dạng |
| [`build/`](build/README.md) | Script `build_docx.py` sinh `bao-cao.docx` từ `sections/*.md` (python-docx) |
| [`review/`](review/README.md) | Kết quả từng vòng kiểm chứng của `source-verifier` |
| `bao-cao.docx` | Báo cáo Word sinh tự động; không sửa tay cho tới khi nội dung đã chốt (sửa ở `sections/` rồi sinh lại) |
