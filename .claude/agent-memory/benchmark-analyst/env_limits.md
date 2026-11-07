---
name: env-limits
description: Giới hạn môi trường máy đo và trạng thái trước lần đo chính thức 2026-11-07 (RAM host, đĩa, cụm, ivy cache)
metadata:
  type: project
---

Lần đo chính thức đầu tiên bắt đầu 2026-11-07 22:00:54 +07, commit 8164042, cây sạch, `run_all --group all` (69 lần chạy, reps 3, ivy cache bật).

- Trước khi chạy: RAM trống host 4095.9 MB / 16140.4 MB (WSL2 giữ ~6 GB); D trống 345 GB, C trống 58 GB.
- Cụm: 2 worker ALIVE, mỗi worker 2 lõi / 2048 MB, executor 1024 MB; chỉ 4 container `bigdata-*`.
- Trong lúc đo: RAM trống host 351–4168 MiB (memory load 74–97%), phần lớn run chỉ khoảng 0,8–1,1 GB. Sau bộ đo: 6040.1 MB trống; D còn 312 GB (bộ đo làm tốn khoảng 33 GB trên D).
- `data/ivy_cache` đã có jar từ các lần chạy thử, nên lần chạy đầu không cần tải jar.

**Why:** người dùng phải đóng Chrome/Discord, dừng container `xom-nho-*`, tạm dừng Windows Update trước khi đo để giảm nhiễu.
**How to apply:** trước mỗi lần đo lại, kiểm `docker ps` chỉ còn container `bigdata-*`, http://localhost:8090/json/ đủ 2 worker, ghi RAM trống. Không chạy lệnh nặng song song khi đang đo. Xem thêm [[official-run-2026-11-07]].
