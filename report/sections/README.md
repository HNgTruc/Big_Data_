# report/sections — nội dung báo cáo theo chương

Mỗi chương một tệp Markdown. Báo cáo Word/PDF được script trong `report/build/` sinh tự động từ các tệp này, nên phải giữ đúng quy ước định dạng dưới đây.

## Danh sách tệp và trạng thái

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| `00-bia.md` | Bìa, thông tin sinh viên, bảng phân công | Bản nháp; thiếu lớp, mã lớp, giảng viên, ngày nộp, phân công thực tế |
| `00-tom-tat.md` | Tóm tắt | Bản nháp 1 (2026-11-08), chưa qua vòng kiểm 2 |
| `01-gioi-thieu.md` | Chương 1. Giới thiệu | Bản nháp 1 (2026-11-08), chưa qua vòng kiểm 2 |
| `02-co-so-cong-nghe.md` | Chương 2. Cơ sở và công nghệ liên quan | Bản nháp 1 (2026-11-08), chưa qua vòng kiểm 2 |
| `03-du-lieu-va-yeu-cau.md` | Chương 3. Dữ liệu và yêu cầu | Bản nháp 2 (2026-11-08): đã sửa theo `report/review/verify-round1.md`, chi tiết chuyển sang Phụ lục A |
| `04-thiet-ke-he-thong.md` | Chương 4. Thiết kế hệ thống | Bản nháp 2: đã sửa theo vòng kiểm 1, đã có sơ đồ kiến trúc, chi tiết cờ hợp lệ chuyển sang Phụ lục B |
| `05-cai-dat-va-trien-khai.md` | Chương 5. Cài đặt và triển khai | Bản nháp 2: đã sửa theo vòng kiểm 1, chi tiết chuyển sang Phụ lục C |
| `06-thuc-nghiem-va-danh-gia.md` | Chương 6. Thực nghiệm và đánh giá (7 thí nghiệm) | Bản nháp 2: đã sửa theo vòng kiểm 1, bảng chi tiết chuyển sang Phụ lục D |
| `07-ket-qua-demo.md` | Chương 7. Kết quả demo (6 ảnh, mẫu dữ liệu) | Bản nháp 2: đã sửa theo vòng kiểm 1, 7 ảnh còn lại, mẫu bảng tổng hợp và log chuyển sang Phụ lục E |
| `08-thao-luan.md`, `09-ket-luan.md` | Chương 8, 9 | Bản nháp 1 (2026-11-08), chưa qua vòng kiểm 2 |
| `90-tai-lieu-tham-khao.md` | Danh sách tài liệu tham khảo (IEEE) | Có nguồn của toàn báo cáo, đủ tiêu đề và ngày truy cập URL; slide đã đối chiếu, chỉ thiếu tên giảng viên |
| `95-phu-luc-a-du-lieu.md` | Phụ lục A. Lược đồ và số dòng dữ liệu | Bản nháp 1 (2026-11-08) |
| `95-phu-luc-b-kiem-tra-hop-le.md` | Phụ lục B. Cờ kiểm tra hợp lệ của bộ đo | Bản nháp 1 |
| `95-phu-luc-c-cai-dat.md` | Phụ lục C. Chi tiết cài đặt | Bản nháp 1 |
| `95-phu-luc-d-so-lieu-thuc-nghiem.md` | Phụ lục D. Số liệu chi tiết của các thí nghiệm | Bản nháp 1 |
| `95-phu-luc-e-minh-chung.md` | Phụ lục E. Minh chứng bổ sung | Bản nháp 1 |
| `95-phu-luc-f-huong-dan-chay.md` | Phụ lục F. Hướng dẫn chạy và tái lập | Bản nháp 1 (2026-11-08), chưa qua vòng kiểm 2; còn thiếu lệnh áp dụng `.wslconfig`, xác nhận quyền truy cập kho |
| `95-phu-luc-g-ghi-chu-ai.md` | Phụ lục G. Ghi chú sử dụng AI | Bản nháp 1 (2026-11-08); cập nhật sau vòng kiểm 2; thiếu xác nhận của nhóm |

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

Số liệu chỉ lấy từ `results/`; dữ liệu là dữ liệu mô phỏng; phân biệt kết quả đo, kiến thức từ slide/tài liệu và nhận định của người viết. Xem `.claude/rules/report-format.md` và `.claude/rules/no-fabrication.md`.
