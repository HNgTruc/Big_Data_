# report/sections — nội dung báo cáo theo chương

Mỗi chương một tệp Markdown. Báo cáo Word/PDF được script trong `report/build/` sinh tự động từ các tệp này, nên phải giữ đúng quy ước định dạng dưới đây.

## Danh sách tệp và trạng thái

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| `00-bia.md` | Bìa, thông tin sinh viên, bảng phân công | Bản nháp; chỉ còn thiếu ngày nộp |
| `00-tom-tat.md` | Tóm tắt | Bản nháp 3 (2026-11-16): sửa văn phong; nội dung đã kiểm vòng 2 (`report/review/verify-round2.md`) |
| `01-gioi-thieu.md` | Chương 1. Giới thiệu | Bản nháp 3, chỉ sửa văn phong |
| `02-co-so-cong-nghe.md` | Chương 2. Cơ sở và công nghệ liên quan | Bản nháp 3, chỉ sửa văn phong và tham chiếu |
| `03-du-lieu-va-yeu-cau.md` | Chương 3. Dữ liệu và yêu cầu | Bản nháp 3, rút gọn; bảng lỗi chèn, tỉ lệ kích thước, độ lệch khoá sang Phụ lục A (A.2 đến A.4) |
| `04-thiet-ke-he-thong.md` | Chương 4. Thiết kế hệ thống | Bản nháp 3, rút gọn; bảng thành phần, luật làm sạch sang Phụ lục C (C.5, C.6); chỉ số, nhiễu, event log, tham số (e) sang Phụ lục B (B.4 đến B.6) |
| `05-cai-dat-va-trien-khai.md` | Chương 5. Cài đặt và triển khai | Bản nháp 3, rút gọn; bảng công nghệ, nguồn image MinIO, chi tiết sự cố sang Phụ lục C (C.7 đến C.9); giữ lý do chọn Spark, MinIO, Docker Compose, Pandas |
| `06-thuc-nghiem-va-danh-gia.md` | Chương 6. Thực nghiệm và đánh giá (7 thí nghiệm) | Bản nháp 3, rút gọn; mỗi thí nghiệm một bảng hoặc một hình, phần còn lại ở Phụ lục D (D.6 đến D.14) |
| `07-ket-qua-demo.md` | Chương 7. Kết quả demo (2 ảnh chụp, 1 sơ đồ so sánh kế hoạch, 2 bảng mẫu trước/sau) | Bản nháp 3, rút gọn; ảnh Master UI, vùng raw, mẫu bỏ trùng và gán region sang Phụ lục E (E.5, E.6) |
| `08-thao-luan.md`, `09-ket-luan.md` | Chương 8, 9 | Bản nháp 3, chỉ sửa văn phong |
| `90-tai-lieu-tham-khao.md` | Danh sách tài liệu tham khảo (IEEE) | Đủ nguồn của toàn báo cáo, đã kiểm vòng 2; tác giả bốn mục slide do người dùng cung cấp |
| `95-phu-luc-a-du-lieu.md` | Phụ lục A. Lược đồ và số dòng dữ liệu | Bản nháp 3, thêm A.3, A.4 |
| `95-phu-luc-b-kiem-tra-hop-le.md` | Phụ lục B. Thiết kế đo và cờ kiểm tra hợp lệ | Bản nháp 3, đổi tên, thêm B.4 đến B.6 |
| `95-phu-luc-c-cai-dat.md` | Phụ lục C. Chi tiết cài đặt | Bản nháp 3, thêm C.5 đến C.9 |
| `95-phu-luc-d-so-lieu-thuc-nghiem.md` | Phụ lục D. Số liệu chi tiết của các thí nghiệm | Bản nháp 3, thêm D.6 đến D.14 |
| `95-phu-luc-e-minh-chung.md` | Phụ lục E. Minh chứng bổ sung | Bản nháp 3, thêm E.5, E.6 |
| `95-phu-luc-f-huong-dan-chay.md` | Phụ lục F. Hướng dẫn chạy và tái lập | Bản nháp 3, chỉ sửa văn phong; đã kiểm vòng 2 bằng đọc mã, phần lớn lệnh chưa chạy lại trên bản clone |
| `95-phu-luc-g-ghi-chu-ai.md` | Phụ lục G. Ghi chú dùng AI | Bản nháp 3, đổi tên, chỉ sửa văn phong |

Bản nháp 3 (rút thân bài và sửa văn phong, 2026-11-16) chưa qua `source-verifier`. Số liệu, bảng, hình và nhãn chỉ được chuyển chỗ, không viết lại.

## Quy ước định dạng (script sinh Word dựa vào đây)

- Dòng đầu mỗi tệp: `# Chương N. Tên chương` (bìa: `# BÌA`; phụ lục: `# Phụ lục A. Tên phụ lục`). Mục con đánh số tường minh: `## 6.1 ...`, `### 6.2.1 ...`, ở phụ lục `## A.1 ...`; không sâu hơn `####`.
- Văn bản thường, **đậm**, *nghiêng*, `mã`; danh sách `-` hoặc `1.`; khối mã ``` chỉ khi thật cần.
- Hình: một dòng riêng `![Chú thích](đường/dẫn/từ/gốc/repo.png){#fig:nhan}`; dòng ngay sau: `Nguồn: results/...`. Script tự đánh số "Hình N.k" (ở phụ lục "Hình A.k").
- Bảng: dòng `Bảng: Chú thích {#tbl:nhan}` ngay trước bảng pipe; dòng ngay sau bảng: `Nguồn: ...`. Script đánh số "Bảng N.k" (ở phụ lục "Bảng A.k").
- Tham chiếu chéo: `@fig:nhan`, `@tbl:nhan`. Nhãn gồm chữ thường, số, gạch ngang; duy nhất trong toàn báo cáo, phần sau tiền tố cũng không trùng giữa `fig` và `tbl`.
- Trích dẫn: `[@khoa]`; danh sách ở `90-tai-lieu-tham-khao.md`, mỗi mục một dòng `[@khoa]: nội dung IEEE`.
- Chỗ thiếu: `[CHƯA CÓ: lý do]` (script tô vàng). Công thức viết dạng văn bản (S = T1/T2), không LaTeX.
- Khẳng định cần kiểm chứng: khối `<!-- VERIFY ... -->` cuối mỗi tệp (script bỏ qua).
- Không dùng HTML khác, footnote, bảng gộp ô. Không dùng gạch ngang dài trong văn bản.
- Thân bài dẫn tới phụ lục bằng nhãn kèm tên phụ lục, ví dụ `@tbl:partition-stats, Phụ lục D`, hoặc bằng số mục, ví dụ `mục C.3`.

## Nguyên tắc nội dung

Số liệu chỉ lấy từ `results/`; dữ liệu là dữ liệu mô phỏng; phân biệt kết quả đo, kiến thức từ slide/tài liệu và nhận định của nhóm (khối VERIFY còn ghi "người viết" theo cách cũ). Xem `.claude/rules/report-format.md` và `.claude/rules/no-fabrication.md`.
