# report — báo cáo đồ án

Soạn theo `.claude/rules/report-format.md` (cấu trúc mục 6.1 của file yêu cầu). Nộp PDF.
Agent phụ trách: `report-writer`; kiểm chứng: `source-verifier`.

| Mục | Nội dung | Trạng thái |
|---|---|---|
| Bìa và thông tin nhóm | Tên đề tài, khoa, lớp, thành viên, phân công | Bản nháp (`sections/00-bia.md`); thiếu lớp, mã lớp, giảng viên, ngày nộp, phân công thực tế |
| Tóm tắt | 150–250 từ | Chưa viết |
| 1–2 | Giới thiệu; Cơ sở và công nghệ liên quan | Chưa viết |
| 3–7 | Dữ liệu và yêu cầu; Thiết kế; Cài đặt; Thực nghiệm; Kết quả demo | Bản nháp 2 (2026-11-08): đã sửa theo `review/verify-round1.md`, đã chèn sơ đồ kiến trúc, chi tiết đã chuyển sang phụ lục A–E; nội dung slide chưa kiểm |
| 8–9 | Thảo luận; Kết luận | Chưa viết (ý chính đã ghi ở mục 6.11) |
| Tài liệu tham khảo | IEEE | Bản nháp, mới có nguồn của chương 3–7; thiếu tên giảng viên, năm và số trang slide, thiếu nguồn MinIO |
| Phụ lục | A–E: dữ liệu, cờ hợp lệ, cài đặt, số liệu chi tiết, minh chứng; F–G: hướng dẫn chạy và tái lập, ghi chú dùng AI | A–E: bản nháp (`sections/95-phu-luc-*.md`); F–G chưa viết |

| Thư mục | Nội dung |
|---|---|
| [`sections/`](sections/README.md) | Nội dung từng chương (Markdown) và quy ước định dạng |
| [`build/`](build/README.md) | Script `build_docx.py` sinh `bao-cao.docx` từ `sections/*.md` (python-docx); `draw_architecture.py` vẽ sơ đồ kiến trúc |
| [`figures/`](figures/README.md) | Hình vẽ riêng cho báo cáo, sinh bằng script (sơ đồ kiến trúc) |
| [`review/`](review/README.md) | Kết quả từng vòng kiểm chứng của `source-verifier` |
| `bao-cao.docx` | Báo cáo Word sinh tự động; không sửa tay cho tới khi nội dung đã chốt (sửa ở `sections/` rồi sinh lại) |
