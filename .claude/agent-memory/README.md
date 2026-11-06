# agent-memory — bộ nhớ bền vững của từng agent

Mỗi thư mục con tương ứng một agent trong `../agents/` có `memory: project`. Agent đọc 200 dòng đầu
(hoặc 25 KB đầu) của `MEMORY.md` mỗi lần chạy và tự cập nhật khi làm việc.

| Thư mục | Agent | Nội dung nên lưu |
|---|---|---|
| `data-generator/` | sinh dữ liệu | schema đã chốt, tham số đã dùng |
| `spark-etl-engineer/` | job Spark | quyết định thiết kế, lỗi và cách xử lý |
| `code-reviewer/` | soát mã | lỗi hay lặp lại, quy ước đã thống nhất, phần đã soát |
| `benchmark-analyst/` | đo hiệu năng | cấu hình đã đo, phát hiện, giới hạn môi trường |
| `report-writer/` | viết báo cáo | quy ước thuật ngữ, tiến độ từng mục |
| `source-verifier/` | kiểm chứng | nguồn tin cậy, lỗi hay gặp |

Thư mục này được đưa lên git để bộ nhớ đi cùng dự án. Không ghi bí mật hay thông tin cá nhân vào đây.
