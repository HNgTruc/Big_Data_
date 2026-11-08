# report/build — dựng file Word báo cáo từ Markdown

Script đọc mọi `report/sections/*.md` (theo thứ tự tên file, bỏ `README.md`) và ghi một file Word
`report/bao-cao.docx` có trang bìa, mục lục, danh mục hình/bảng, đánh số hình/bảng theo chương,
tham chiếu chéo và trích dẫn kiểu IEEE. File `.docx` là bản trung gian; bản nộp là PDF xuất từ Word.

| File | Nội dung |
|---|---|
| `build_docx.py` | Script dựng `.docx` (hai lượt: đánh số rồi dựng); hằng số trình bày ở đầu file |
| `draw_architecture.py` | Vẽ sơ đồ kiến trúc chương 4 bằng matplotlib; mặc định ghi `report/figures/kien-truc.png`, đổi bằng `--output` |
| `requirements.txt` | Phụ thuộc: `python-docx` (kéo theo `lxml`); `pytest` cho kiểm thử |

Kiểm thử: `tests/test_build_docx.py` (xem `tests/README.md`).

## Cài đặt (PowerShell, từ gốc repo)

Dùng venv thí nghiệm của dự án `.venv-exp` (Python 3.12):

```powershell
.\.venv-exp\Scripts\python.exe -m pip install --default-timeout=300 -r report\build\requirements.txt
```

Đã thử 2026-11-08: Python 3.12.10, python-docx 1.2.0, lxml 6.1.3.

## Cách chạy

```powershell
.\.venv-exp\Scripts\python.exe report\build\build_docx.py
```

Tham số (đều có mặc định tương đối gốc repo):

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--root` | gốc repo (suy từ vị trí script) | Đường dẫn ảnh trong Markdown tính từ đây |
| `--sections` | `<root>/report/sections` | Thư mục chứa các file `.md` |
| `--output` | `<root>/report/bao-cao.docx` | File Word đầu ra |
| `--title` | lấy từ bìa | Thuộc tính Title của tài liệu |
| `--author` | Tên 4 thành viên, cách nhau bằng `; ` (`DEFAULT_AUTHOR`) | Thuộc tính Author |
| `--no-update-on-open` | tắt | Không yêu cầu Word cập nhật trường (mục lục, danh mục) khi mở |
| `--strict` | tắt | Thoát mã 1 nếu có cảnh báo |

Cuối khi chạy, script in tóm tắt (số chương, hình, bảng, trích dẫn, cảnh báo) và danh sách cảnh báo
dạng `file.md:dòng: nội dung`. Mã thoát: 0 = đã ghi (kể cả có cảnh báo); 1 = có cảnh báo khi dùng `--strict`;
2 = không có thư mục sections hoặc không có file `.md`; 3 = không ghi được file (thường do file đang mở trong Word).

Sau khi mở `bao-cao.docx` trong Word: chọn tất cả (Ctrl+A) rồi F9, hoặc nhấn chuột phải vào mục lục → Update Field
→ Update entire table, để có số trang trong mục lục và danh mục. Word thường hỏi cập nhật ngay khi mở (script bật
`updateFields`); trước khi cập nhật, mục lục và danh mục hiện dạng danh sách tĩnh không có số trang.

## Quy ước Markdown được hỗ trợ

| Cú pháp | Kết quả |
|---|---|
| `# BÌA` (thường ở `00-bia.md`) | Trang bìa riêng: mỗi dòng một đoạn căn giữa, giữ nguyên chữ, mỗi dòng trống thành một đoạn trống; không số trang, không vào mục lục. Bìa kết thúc ở tiêu đề kế tiếp (mọi cấp). Dòng `![...](logo.png)` trên bìa chèn ảnh căn giữa (cao tối đa 6 cm, không chú thích) |
| Nội dung giữa bìa và `# Chương` đầu tiên (vd `## Thông tin thực hiện` + bảng phân công) | Trang riêng ngay sau bìa, trước mục lục; hình/bảng ở đây đánh số không kèm chương (`Bảng 1`) |
| `# Chương N. …` | Heading 1, sang trang mới; N dùng để đánh số hình/bảng. `# Phụ lục A …` cho số `A.k`; tiêu đề cấp 1 khác (Tóm tắt, Tài liệu tham khảo) đánh số `k` không kèm chương |
| `##`, `###`, `####` | Heading 2, 3, 4 (cấp 5–6 dựng như 4 và cảnh báo). Không tự đánh số tiêu đề |
| `**đậm**`, `*nghiêng*`, `` `mã` `` | Đậm, nghiêng, font Consolas. Dấu `\` thoát ký tự: `` \* \` \_ \[ \] \@ \| \\ `` |
| `- mục`, `1. mục` (lồng 1 cấp bằng 2–4 dấu cách) | Danh sách có ký hiệu `•`/`◦` hoặc số; số bắt đầu từ số của mục đầu. Dòng thụt vào tiếp nối mục trước |
| Khối ```` ``` ```` | Consolas 10, nền xám nhạt, viền mảnh |
| `![chú thích](đường/dẫn/từ/gốc/repo.png){#fig:nhan}` | Ảnh căn giữa, co vừa 16 cm bề rộng và chiều cao trang (giữ tỉ lệ, không phóng to), chú thích dưới ảnh `Hình N.k. chú thích`. Ảnh thiếu/không đọc được → đoạn đỏ `[THIẾU HÌNH: path]` và cảnh báo, vẫn đánh số |
| `Bảng: chú thích {#tbl:nhan}` ngay trước bảng pipe | Chú thích phía trên `Bảng N.k. chú thích`; bảng có viền, hàng tiêu đề đậm và lặp lại khi sang trang, cỡ 11, rộng bằng khổ chữ, cột theo độ dài nội dung, căn cột theo `:---:`/`---:` |
| Bảng pipe không có dòng `Bảng:` | Vẫn dựng, không đánh số, không vào danh mục bảng |
| `Nguồn: …` ngay sau hình/bảng | Đoạn nghiêng cỡ 11 (căn giữa dưới hình, căn trái dưới bảng). Ở chỗ khác là đoạn thường |
| `@fig:nhan`, `@tbl:nhan` | `Hình N.k` / `Bảng N.k`, kể cả khi hình ở phía sau. Nhãn không tồn tại → giữ chữ, tô đỏ, cảnh báo |
| `[@khoa]`, `[@a; @b]` | `[n]`, `[n], [m]`, đánh số theo lần xuất hiện đầu tiên trong toàn báo cáo. Khoá không có trong danh sách → tô đỏ, cảnh báo |
| `[@khoa]: nội dung IEEE` (trong `90-tai-lieu-tham-khao.md`) | Danh sách `[n] nội dung` in tại chỗ dòng khai báo đầu tiên, theo số đã gán; mục không được trích in cuối, cảnh báo. Dòng tiếp theo không trống được nối vào mục |
| `[CHƯA CÓ: …]` | Giữ chữ, tô nền vàng |
| `<!-- … -->` (kể cả nhiều dòng) | Bỏ hoàn toàn |
| Dòng cuối có 2 dấu cách hoặc `\` | Xuống dòng trong cùng đoạn |

## Trình bày trang (mặc định)

A4; lề trái 3 cm, phải 2 cm, trên 2 cm, dưới 2 cm (theo cách trình bày thường dùng cho báo cáo; đổi trong
các hằng số `MARGIN_*_CM` đầu `build_docx.py`). Times New Roman 13 (đặt cả `eastAsia`/`cs` để tiếng Việt hiển thị
đúng), giãn dòng 1,3, căn đều hai bên, thụt đầu dòng 1 cm, cách đoạn 6 pt. Heading Times New Roman đậm, màu đen:
H1 16, H2 14, H3 13, H4 13 nghiêng. Chú thích hình/bảng cỡ 12, nhãn đậm. Số trang ở chân trang, căn giữa,
đếm từ 1 sau bìa. Thuộc tính tài liệu: Title = tên đề tài (dòng `Tên đề tài: …`/`Đề tài: …` trên bìa, nếu không
có thì dòng có chữ đầu tiên của bìa; hoặc `--title`), Author = `--author`.

## Giới hạn đã biết

- Mục lục và danh mục là trường Word (`TOC \o "1-3" \h \z \u`, `TOC \h \z \c "Hình"`, `TOC \h \z \c "Bảng"`):
  số trang chỉ có sau khi Word cập nhật trường (LibreOffice có thể không tự cập nhật).
- Số trong chú thích là trường `SEQ Hình \r k` cố định theo số script đã tính, nên Word cập nhật trường không làm
  sai số theo chương. Tham chiếu `@fig:`/`@tbl:` và `[n]` là chữ tĩnh, không phải liên kết; dựng lại khi thêm hình/bảng.
- Chưa hỗ trợ: trích khối `>`, đường kẻ ngang, liên kết `[chữ](url)` (giữ nguyên chữ), HTML, chú thích cuối trang,
  ô bảng gộp, danh sách lồng quá 1 cấp, ảnh SVG (cảnh báo và chèn chỗ giữ đỏ). Các cú pháp `>`, kẻ ngang, thẻ HTML có cảnh báo.
- Danh sách dựng bằng ký hiệu chữ và thụt lề treo, không dùng kiểu danh sách tự động của Word.
