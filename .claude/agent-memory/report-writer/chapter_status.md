---
name: chapter-status
description: Chương báo cáo đã viết, chỗ còn [CHƯA CÓ], khoá trích dẫn đã dùng, điểm chưa chắc (2026-11-08)
metadata:
  type: project
---

2026-11-08: bản nháp 1 của `00-bia`, `03`–`07`, `90-tai-lieu-tham-khao` (chỉ nguồn ch.3–7) và `report/sections/README.md`. Chưa viết: tóm tắt, ch.1, 2, 8, 9, phụ lục. Ý thảo luận cho ch.8 ở mục 6.11.

Thiếu dữ liệu (đã đánh `[CHƯA CÓ]`): lớp, mã lớp, giảng viên, MSSV, ngày nộp, khoa; sơ đồ kiến trúc; dung lượng tệp thô bộ 500k/1m/2500k và số dòng sai ngày của orders_5m (chỉ có trong data/raw/*/manifest.json); phiên bản MinIO Chainguard; mẫu CPU; log kiểm thử host (44 passed chỉ ở tests/README.md); tên giảng viên/năm slide; ngày truy cập URL; tiêu đề bài Chainguard, bex.co, issue docker/desktop-feedback #767.

Khoá trích dẫn: slide-c1, slide-c2, slide-c4, slide-c5, spark-config, spark-sql-tuning, spark-ansi, spark-monitoring, spark-standalone, pyspark-cache, hadoop-s3a, chainguard-minio, bex-minio, docker-767. Nhãn ảnh chụp ch.7: `fig:ss-*`.

Chưa chắc: ảnh 01 ghi 68 ứng dụng trong khi app export_samples là ...-0069; storage cache chỉ kiểm r1; numpy 2.5.4 có phải môi trường bộ đo; ảnh 05, 06, 08 chưa mở trực tiếp.

**Why:** để lần sau tiếp tục đúng chỗ.
**How to apply:** kiểm lại file thực tế trong report/sections trước khi viết tiếp. Xem [[markdown-conventions]].
