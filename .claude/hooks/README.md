# hooks — script chạy tự động quanh lệnh của Claude Code

Khai báo trong `../settings.json`. Hook khác với rule: rule chỉ là lời nhắc, hook **bắt buộc** (exit code 2 chặn lệnh).

| File | Sự kiện | Việc làm |
|---|---|---|
| `guard_root.py` | `PreToolUse` (Write, Edit, MultiEdit) | Chặn tạo hoặc sửa file nằm thẳng ở thư mục gốc, trừ `README.md` và `.gitignore` |

Giới hạn: chỉ chặn công cụ ghi file, không chặn file tạo qua lệnh Bash. Cần Python có trong PATH (lệnh `python`).
