# report — báo cáo đồ án

Soạn theo `.claude/rules/report-format.md` (cấu trúc mục 6.1 của file yêu cầu). Nộp PDF.
Agent phụ trách: `report-writer`; kiểm chứng: `source-verifier`.

| Mục | Nội dung | Trạng thái |
|---|---|---|
| Bìa và thông tin nhóm | Tên đề tài, khoa, lớp, thành viên, phân công | Bản nháp (`sections/00-bia.md`); chỉ còn thiếu ngày nộp |
| Tóm tắt | 150–250 từ | Đã kiểm vòng 2 và sửa theo `review/verify-round2.md` |
| 1–2 | Giới thiệu; Cơ sở và công nghệ liên quan | Đã kiểm vòng 2 và sửa |
| 3–7 | Dữ liệu và yêu cầu; Thiết kế; Cài đặt; Thực nghiệm; Kết quả demo | Đã kiểm vòng 1, slide và vòng 2 (`review/`), đã sửa; chi tiết đã chuyển sang phụ lục A–E |
| 8–9 | Thảo luận; Kết luận | Đã kiểm vòng 2 và sửa |
| Tài liệu tham khảo | IEEE | Đã kiểm vòng 2 và sửa; định dạng chưa đối chiếu hướng dẫn IEEE gốc |
| Phụ lục | A–E: dữ liệu, cờ hợp lệ, cài đặt, số liệu chi tiết, minh chứng; F–G: hướng dẫn chạy và tái lập, ghi chú dùng AI | A–G: đã kiểm vòng 2 và sửa (`sections/95-phu-luc-*.md`); các lệnh cần Docker ở F chưa chạy lại trên bản clone |

| Thư mục | Nội dung |
|---|---|
| [`sections/`](sections/README.md) | Nội dung từng chương (Markdown) và quy ước định dạng |
| [`build/`](build/README.md) | Script `build_docx.py` sinh `bao-cao.docx` từ `sections/*.md` (python-docx); `draw_architecture.py` vẽ sơ đồ kiến trúc |
| [`figures/`](figures/README.md) | Hình vẽ riêng cho báo cáo, sinh bằng script (sơ đồ kiến trúc) |
| [`review/`](review/README.md) | Kết quả từng vòng kiểm chứng của `source-verifier` |
| `bao-cao.docx` | Báo cáo Word sinh tự động; không sửa tay cho tới khi nội dung đã chốt (sửa ở `sections/` rồi sinh lại) |
