# Phụ lục G. Ghi chú sử dụng AI

Phụ lục này thực hiện yêu cầu ở mục 8 của đề: nêu công cụ AI, mục đích và phần đã kiểm tra.

## G.1 Công cụ

Đồ án dùng Claude Code. Cấu hình của dự án nằm trong `.claude/`, gồm quy tắc, skill và sáu agent chuyên trách (`.claude/README.md`).

## G.2 Mục đích

Bảng: Các agent đã cấu hình và mục đích {#tbl:ai-agent}

| Agent | Mục đích |
|---|---|
| `data-generator` | Viết bộ sinh dữ liệu mô phỏng |
| `spark-etl-engineer` | Viết job Spark |
| `code-reviewer` | Soát mã trước khi chạy thí nghiệm |
| `benchmark-analyst` | Chạy thí nghiệm, ghi số đo, phân tích |
| `report-writer` | Soạn nháp báo cáo |
| `source-verifier` | Kiểm chứng khẳng định với nguồn; không sửa báo cáo, chỉ báo cáo kết quả |

Nguồn: .claude/README.md, .claude/CLAUDE.md, .claude/agents/

Các quyết định chính của đồ án (miền dữ liệu, MinIO, Docker Compose, lược đồ, tỉ lệ lỗi, kích thước dữ liệu) được người dùng công cụ xác nhận và ghi trong `.claude/CLAUDE.md`. Theo mục 8 của đề, nhóm chịu trách nhiệm hoàn toàn về sản phẩm và phải giải thích được hệ thống.

## G.3 Phần đã kiểm tra

- **Số liệu.** Số đo do job và bộ điều khiển sinh ra khi chạy thật; AI không tự điền số. Số được ghi vào `results/` trên máy thí nghiệm, mỗi lần chạy có `run_record.json` và log.
- **Vòng kiểm chứng 1.** `report/review/verify-round1.md` kiểm bìa, chương 3–7 và tài liệu tham khảo của bản nháp 1. Các điểm phát hiện đã được áp dụng vào `report/sections/`.
- **Trích dẫn slide.** `report/review/verify-slides.md` kiểm 12 chỗ trích: 5 đúng, 7 đúng một phần, không chỗ nào không thấy trên slide. Các chỗ đúng một phần đã được sửa.
- **Vòng kiểm chứng 2.** `report/review/verify-round2.md` kiểm toàn bộ báo cáo. Khoảng 450 con số đối chiếu với `results/` đều khớp; các lỗi tìm thấy nằm ở phạm vi câu chữ, diễn giải và lệnh tái lập, đã được sửa.
- **Tái lập trên bản clone.** Các bước không cần Docker đã chạy thử trên một bản clone mới: 69 test qua, dữ liệu `orders_500k` sinh lại trùng từng byte, phân tích và dựng báo cáo chạy được (`results/logs/test_clone.log`). Các bước cần Docker (dựng cụm, ETL, đo) chưa chạy lại trên bản clone; chúng đã chạy trên máy thí nghiệm theo log trong `results/logs/`.
- **Bộ kiểm thử.** Các test trong `tests/` cho 41 passed trong container và 69 passed trên host (mục 5.4, @tbl:kiem-thu, Phụ lục C).
- **Đối chiếu số đếm.** Số dòng trùng đã bỏ và các lý do cách ly trực tiếp được so với số lỗi đã chèn; baseline Pandas thực hiện 49 phép đối chiếu mỗi lần chạy (mục 5.4).
- **Phần nhóm tự kiểm tra.** Nhóm xác nhận đã chạy và kiểm tra toàn bộ, kết quả đều bình thường. Đây là xác nhận của nhóm; repo không có bản ghi riêng cho lần kiểm tra này.

## G.4 Giới hạn

AI có thể sai, nên nội dung do AI hỗ trợ đã được đối chiếu như ở G.3. Ví dụ đã xảy ra: bản nháp 1 từng khẳng định đã đóng ứng dụng nặng trước khi đo trong khi repo không có bằng chứng; có chỗ mô tả Spark là "xử lý trong bộ nhớ" trái với lưu ý ở slide; và lệnh ở Phụ lục F từng thiếu `--overwrite` trên bản clone. Các điểm này đã được sửa. Bản thân `source-verifier` cũng là AI, và một số trang web được đọc qua công cụ tóm tắt, nên kiểm chứng này không thay thế việc nhóm tự kiểm tra (`report/review/verify-slides.md`, mục D; `report/review/verify-round2.md`, mục "KHÔNG kiểm được").

<!-- VERIFY
- Sáu agent, cấu trúc .claude: .claude/README.md; mục đích: .claude/CLAUDE.md mục "Agent và skill" và phần mô tả trong .claude/agents/*.md.
- "Quyết định ... xác nhận": .claude/CLAUDE.md mục "Quyết định đã chốt (do người dùng xác nhận)".
- verify-round1: phạm vi và trạng thái theo report/review/README.md. verify-slides: tổng hợp 12 chỗ (5 đúng, 7 đúng một phần, 0 không thấy).
- Ví dụ AI sai: report/review/verify-round1.md mục B (05 mục 5.6 "đã đóng ứng dụng nặng"); report/review/verify-slides.md mục B.1 (05:25 "xử lý trong bộ nhớ").
- WebFetch trả kết quả qua mô hình tóm tắt: verify-slides.md mục D.
- 41, 69, 49: mục 5.4. Không nêu mô hình cụ thể (không có nguồn).
- Vòng 2: report/review/verify-round2.md mục "Đã kiểm đạt" (khoảng 450 con số), mục E (lệnh Phụ lục F), mục "KHÔNG kiểm được" (không chạy lệnh nào).
- Dòng "Phần nhóm tự kiểm tra": người dùng xác nhận (2026-11-09); repo không có bản ghi riêng.
-->
