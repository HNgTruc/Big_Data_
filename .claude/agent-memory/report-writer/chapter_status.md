---
name: chapter-status
description: Trạng thái các tệp báo cáo sau vòng kiểm 2, số mục và nhãn đã đổi, khoá trích dẫn, các [CHƯA CÓ], quyết định còn mở (cập nhật 2026-11-09)
metadata:
  type: project
---

2026-11-09: đủ mọi tệp báo cáo, đã áp dụng `report/review/verify-round2.md` (mọi nhóm A–F, G3, G4, G5). Trạng thái ở `report/sections/README.md`: bản nháp 2, đã kiểm vòng 2. Đồ án làm theo nhóm 4 người; không gán việc cho thành viên.

Quyết định: giữ "nhận định của người viết" (H1, điều phối viên sẽ hỏi người dùng rồi đổi nếu cần); giữ "Thành phố Hồ Chí Minh"; giữ manifest trên git nên Phụ lục F ghi `--overwrite`; con số chính của (d) là "khoảng 7–12%", mục 6.7 nêu đủ 12%, 7%, 9%.

Số mục chương 5: 5.3 cũ + 5.4 cũ thành 5.3 mới; 5.5 cũ thành 5.4; 5.6 cũ thành 5.5. Chương 7 mất 7.5 (log sang E.4). Mục tiêu đánh số 1–5 ở mục 1.2; chương 9 trả lời theo đúng số này.

Nhãn đã đổi: tbl:scale-giai-doan thành tbl:scale-giai-doan-chi-tiet; tbl:skew thành tbl:skew-cau-hinh; tbl:cache thành tbl:cache-tong và tbl:cache-truy-van; tbl:pandas thành tbl:pandas-spark; tbl:format-truy-van thành tbl:format-thoi-gian; tbl:format-dung-luong thành tbl:format-kich-thuoc và tbl:format-byte-dong. Mới: tbl:kich-thuoc-tong, tbl:co-hop-le, fig:kien-truc, tbl:speedup-bang-chung, tbl:ghi-nhan-chay, tbl:ai-agent. Nhãn ảnh chụp: `fig:ss-*`.

Khoá trích dẫn: slide-c1, slide-c2, slide-c4, slide-c5, minio-docs, spark-cluster, spark-config, spark-sql-tuning, spark-tuning, spark-ansi, spark-monitoring, spark-standalone, pyspark-cache, hadoop-s3a, chainguard-minio, bex-minio, docker-767, spark-cloud, hadoop-s3-third-party, wsl-config.

Còn `[CHƯA CÓ]`: bìa (mã lớp, ngày nộp, phân công, tỉ lệ đóng góp); mục 5.1 (lý do chọn Docker Compose, chờ người dùng). Lớp, giảng viên, tác giả slide, dòng F:5, dòng "Phần nhóm tự kiểm tra" do người dùng cung cấp, không tự sửa. Số test host là 69 passed (13/29/15/12).

Lệnh Phụ lục F chỉ kiểm bằng đọc mã; giữ chữ "theo mã, chưa chạy thử", không viết như đã chạy lại.

Cách đếm từ không có Bash: Grep `\S+` với `-o`, `-n`, `offset` và `head_limit` nhỏ; dò đến dòng `<!-- VERIFY`. Tóm tắt đang sát trần 250 từ, thêm chữ phải bớt chỗ khác.

**Why:** để lần sau tiếp tục đúng chỗ và không làm lại các quyết định đã chốt.
**How to apply:** kiểm lại file thực tế trong report/sections trước khi viết tiếp; điều phối viên có thể đã sửa vài dòng. Xem [[markdown-conventions]].
