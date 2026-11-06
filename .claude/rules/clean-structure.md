# Cấu trúc thư mục gọn

- Thư mục gốc chỉ có `README.md` và `.gitignore`. Mọi file khác phải nằm trong một thư mục cụ thể.
- Mỗi thư mục mới phải có `README.md` nêu: nội dung, file/thư mục con, cách dùng.
- Ngoại lệ: `.claude/rules/` và `.claude/agents/` không đặt README (file `.md` ở đó bị coi là rule/agent);
  `.claude/skills/` cũng không đặt README để tránh rủi ro tương tự (chưa kiểm chứng hành vi). Bản đồ của chúng nằm ở `.claude/README.md`.
- Thêm hoặc đổi tên thư mục thì cập nhật README của thư mục cha và README gốc trong cùng lần thay đổi.
- Không để file tạm, bản sao `_old`, `_final` hay ghi chú rời trong repo; việc tạm dùng thư mục scratchpad của phiên.
- Tên file và thư mục: chữ thường, dấu gạch ngang hoặc gạch dưới, không dấu tiếng Việt, không khoảng trắng.
