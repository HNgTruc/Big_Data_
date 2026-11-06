# .claude — cấu hình agent của dự án

Thư mục này chứa mọi thứ Claude Code đọc khi làm việc trong repo. Chỉ có **một README này** cho cả
`rules/`, `agents/`, `skills/`: mọi file `.md` trực tiếp trong `rules/` và `agents/` bị coi là rule/agent, còn `skills/` tránh đặt README để phòng rủi ro tương tự (chưa kiểm chứng)
(README đặt ở đó có thể bị nạp nhầm).

| Đường dẫn | Vai trò | Khi nào nạp |
|---|---|---|
| `CLAUDE.md` | Ngữ cảnh và quy ước dự án (dưới 200 dòng) | Mỗi phiên |
| `settings.json` | Khai báo hook | Mỗi phiên |
| `hooks/guard_root.py` | Chặn ghi file lạ ở thư mục gốc | Trước mỗi lần Write/Edit |
| `rules/*.md` | Quy tắc theo chủ đề; một số chỉ áp dụng cho đường dẫn nhất định (`paths`) | Mỗi phiên hoặc khi chạm file khớp |
| `skills/<tên>/SKILL.md` | Quy trình lặp lại gọi bằng `/tên` | Khi gọi hoặc khi liên quan |
| `agents/*.md` | Subagent chuyên trách, mỗi agent có tool riêng | Khi được giao việc |
| `agent-memory/<agent>/MEMORY.md` | Bộ nhớ bền vững của từng agent (`memory: project`) | 200 dòng đầu mỗi lần agent chạy |

## Rules
- `rules/no-fabrication.md` — không bịa thông tin
- `rules/clean-structure.md` — cấu trúc thư mục gọn, README mỗi thư mục
- `rules/code-style.md` — chuẩn mã Python (áp dụng `src/**`, `tests/**`)
- `rules/report-format.md` — chuẩn báo cáo (áp dụng `report/**`)

## Skills
- `/check-requirements` — đối chiếu sản phẩm với file yêu cầu đồ án
- `/new-experiment` — khuôn một thí nghiệm lặp lại được
- `/draft-report-section` — soạn một mục báo cáo từ dữ liệu thật

## Agents
- `data-generator`, `spark-etl-engineer`, `code-reviewer`, `benchmark-analyst`, `report-writer`, `source-verifier`

Nguồn tham chiếu: https://code.claude.com/docs/en/claude-directory và
https://code.claude.com/docs/en/sub-agents
