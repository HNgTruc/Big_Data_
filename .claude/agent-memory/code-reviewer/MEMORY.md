# Bộ nhớ của agent code-reviewer

Agent tự cập nhật file này khi làm việc (giữ dưới 200 dòng). Chỉ ghi điều đã xác nhận.

- [Review experiments 2026-11-07](review_experiments_2026-11-07.md) — findings mở của lần soát src/experiments đầu tiên, quyết định người dùng cần tôn trọng
- Môi trường soát: `.venv-exp\Scripts\python.exe -m pytest tests/test_experiments.py tests/test_experiments_pandas.py`; ruff có ở PATH (conda), không có trong venv
