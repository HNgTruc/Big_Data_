# report/sections — nội dung báo cáo theo chương

Mỗi chương một tệp Markdown. Báo cáo Word/PDF được script trong `report/build/` sinh tự động từ các tệp này, nên phải giữ đúng quy ước định dạng dưới đây.

## Danh sách tệp và trạng thái

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| `00-bia.md` | Bìa, thông tin sinh viên, bảng phân công | Bản nháp; thiếu lớp, mã lớp, giảng viên, MSSV, ngày nộp |
| `01-gioi-thieu.md` | Chương 1. Giới thiệu | Chưa viết |
| `02-co-so-cong-nghe.md` | Chương 2. Cơ sở và công nghệ liên quan | Chưa viết |
| `03-du-lieu-va-yeu-cau.md` | Chương 3. Dữ liệu và yêu cầu | Bản nháp 1 (2026-11-08), chờ source-verifier |
| `04-thiet-ke-he-thong.md` | Chương 4. Thiết kế hệ thống | Bản nháp 1, thiếu sơ đồ kiến trúc |
| `05-cai-dat-va-trien-khai.md` | Chương 5. Cài đặt và triển khai | Bản nháp 1, chờ source-verifier |
| `06-thuc-nghiem-va-danh-gia.md` | Chương 6. Thực nghiệm và đánh giá (7 thí nghiệm) | Bản nháp 1, chờ source-verifier |
| `07-ket-qua-demo.md` | Chương 7. Kết quả demo (13 ảnh, mẫu dữ liệu, log) | Bản nháp 1, chờ source-verifier |
| `08-thao-luan.md`, `09-ket-luan.md` | Chương 8, 9 | Chưa viết |
| `90-tai-lieu-tham-khao.md` | Danh sách tài liệu tham khảo (IEEE) | Mới có nguồn của chương 3–7; thiếu ngày truy cập, tên giảng viên |
| Tóm tắt, phụ lục | | Chưa viết |

Tên tệp của các chương chưa viết là dự kiến.

## Quy ước định dạng (script sinh Word dựa vào đây)

- Dòng đầu mỗi tệp: `# Chương N. Tên chương` (bìa: `# BÌA`). Mục con đánh số tường minh: `## 6.1 ...`, `### 6.2.1 ...`; không sâu hơn `####`.
- Văn bản thường, **đậm**, *nghiêng*, `mã`; danh sách `-` hoặc `1.`; khối mã ``` chỉ khi thật cần.
- Hình: một dòng riêng `![Chú thích](đường/dẫn/từ/gốc/repo.png){#fig:nhan}`; dòng ngay sau: `Nguồn: results/...`. Script tự đánh số "Hình N.k".
- Bảng: dòng `Bảng: Chú thích {#tbl:nhan}` ngay trước bảng pipe; dòng ngay sau bảng: `Nguồn: ...`. Script đánh số "Bảng N.k".
- Tham chiếu chéo: `@fig:nhan`, `@tbl:nhan`. Nhãn gồm chữ thường, số, gạch ngang; duy nhất trong toàn báo cáo.
- Trích dẫn: `[@khoa]`; danh sách ở `90-tai-lieu-tham-khao.md`, mỗi mục một dòng `[@khoa]: nội dung IEEE`.
- Chỗ thiếu: `[CHƯA CÓ: lý do]` (script tô vàng). Công thức viết dạng văn bản (S = T1/T2), không LaTeX.
- Khẳng định cần kiểm chứng: khối `<!-- VERIFY ... -->` cuối mỗi tệp (script bỏ qua).
- Không dùng HTML khác, footnote, bảng gộp ô. Không dùng gạch ngang dài trong văn bản.

## Nguyên tắc nội dung

Số liệu chỉ lấy từ `results/`; dữ liệu là dữ liệu mô phỏng; phân biệt kết quả đo, kiến thức từ slide/tài liệu và nhận định của người viết. Xem `.claude/rules/report-format.md` và `.claude/rules/no-fabrication.md`.
