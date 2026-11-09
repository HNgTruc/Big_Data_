---
name: chapter-status
description: Trạng thái các tệp báo cáo, số mục và nhãn đã đổi, khoá trích dẫn, các [CHƯA CÓ], điểm chưa chắc (cập nhật 2026-11-08)
metadata:
  type: project
---

2026-11-08: đủ mọi tệp báo cáo. `03`–`07`, `90`, phụ lục A–E là bản nháp 2 đã áp dụng `report/review/verify-round1.md`, `verify-slides.md`. Mới viết bản nháp 1, chưa qua vòng kiểm 2: `00-tom-tat`, `01`, `02`, `08`, `09`, phụ lục F, G. Đồ án làm theo nhóm 4 người; không gán việc cho thành viên.

Số mục chương 5 đã đổi: 5.3 cũ + 5.4 cũ thành 5.3 mới; 5.5 cũ thành 5.4; 5.6 cũ thành 5.5. Chương 7 mất 7.5 (log sang E.4). Mục tiêu đánh số 1–5 ở mục 1.2; chương 9 trả lời theo đúng số này.

Nhãn đã đổi: tbl:scale-giai-doan thành tbl:scale-giai-doan-chi-tiet; tbl:skew thành tbl:skew-cau-hinh; tbl:cache thành tbl:cache-tong và tbl:cache-truy-van; tbl:pandas thành tbl:pandas-spark; tbl:format-truy-van thành tbl:format-thoi-gian; tbl:format-dung-luong thành tbl:format-kich-thuoc và tbl:format-byte-dong. Mới: tbl:kich-thuoc-tong, tbl:co-hop-le, fig:kien-truc, tbl:speedup-bang-chung, tbl:ghi-nhan-chay, tbl:ai-agent. Nhãn ảnh chụp: `fig:ss-*`.

Khoá trích dẫn: slide-c1, slide-c2, slide-c4, slide-c5, minio-docs, spark-cluster, spark-config, spark-sql-tuning, spark-tuning, spark-ansi, spark-monitoring, spark-standalone, pyspark-cache, hadoop-s3a, chainguard-minio, bex-minio, docker-767, spark-cloud, hadoop-s3-third-party.

Còn `[CHƯA CÓ]`: bìa (lớp, mã lớp, giảng viên, ngày nộp, phân công); tên giảng viên trong 90; phụ lục F (lệnh áp dụng `.wslconfig`, xác nhận quyền truy cập kho git); phụ lục G (phần nhóm tự kiểm tra).

Chưa chắc: số test `test_build_docx.py` (log 12, tổng 68; mã và tests/README.md 13, nên chạy lại log sẽ ra 69). Một số README thí nghiệm còn dòng "chưa chạy" đã cũ. C.3 bước 4 dùng ivy_cache, còn infra/README.md dùng /tmp/.ivy. `analyze_all` trên bản clone không có event log có thể ghi đè plan_check.csv (đọc mã, chưa chạy).

Cách đếm từ không có Bash: Grep `\S+` với `-o`, `-n`, `offset` và `head_limit` nhỏ; dò đến dòng `<!-- VERIFY`.

**Why:** để lần sau tiếp tục đúng chỗ.
**How to apply:** kiểm lại file thực tế trong report/sections trước khi viết tiếp. Sau vòng kiểm 2 phải cập nhật phụ lục G. Xem [[markdown-conventions]].
