---
name: no-repo-writes-during-runs
description: Không ghi file nào trong repo (kể cả bộ nhớ agent) khi runner đang đo, vì runner gắn cờ git dirty cho mọi run sau đó
metadata:
  type: feedback
---

Không ghi file vào repo (kể cả `.claude/agent-memory/`) khi bộ đo đang chạy; ghi nhớ trước khi bắt đầu hoặc sau khi xong. Việc tạm để trong scratchpad.

**Why:** lần đo 2026-11-07, tôi ghi hai file bộ nhớ lúc scale_data đang chạy, làm 57/69 run record có `git.dirty=True` (`dirty_paths` chỉ là file bộ nhớ, mã không đổi) và `dirty_any=True` trong summary. `records.py` chỉ loại `results/` khỏi kiểm tra dirty.
**How to apply:** mọi lần chạy `run_all`/`run.py` thật thì đợi đến khi chạy xong mới cập nhật bộ nhớ. Liên quan [[official-run-2026-11-07]].
