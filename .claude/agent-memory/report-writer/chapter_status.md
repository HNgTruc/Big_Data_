---
name: chapter-status
description: Trạng thái các tệp báo cáo sau lượt rút gọn bản nháp 3 (2026-11-16), số mục và nhãn đã chuyển, khoá trích dẫn, các [CHƯA CÓ], quyết định còn mở
metadata:
  type: project
---

2026-11-16: bản nháp 3. Thân bài rút từ khoảng 50 xuống khoảng 30 trang bằng cách CHUYỂN chi tiết sang phụ lục (người dùng chốt, không xoá nội dung), đồng thời áp bộ quy tắc văn phong (xem [[markdown-conventions]]). Chưa qua source-verifier. Đồ án làm theo nhóm 4 người.

Số mục thân bài KHÔNG đổi (3.1–3.8, 4.1–4.6, 5.1–5.5, 6.1–6.11, 7.1–7.4). Riêng tiêu đề 5.1 đổi thành "Công nghệ và lý do chọn", 2.7 thành "Các kỹ thuật tối ưu đồ án đo".

Phụ lục mới: A.3 lỗi chèn (tbl:loi-chen), A.4 độ lệch khoá; B đổi tên "Thiết kế đo và cờ kiểm tra hợp lệ", thêm B.4 chỉ số và nhiễu, B.5 event log, B.6 tham số ép shuffle; C.5 tbl:thanh-phan, C.6 tbl:luat-lam-sach, C.7 tbl:cong-nghe, C.8 nguồn image MinIO, C.9 chi tiết sự cố (cũ ở 5.5); D.6 tbl:moi-truong + CV truy vấn, D.7 chất lượng, D.8–D.14 cho (a)–(g) (tbl:scale-tong, join-ke-hoach, format-kich-thuoc, cache-hoa-von và 9 hình kết quả); E.5 fig:ss-master, fig:ss-minio-raw; E.6 tbl:mau-trung, tbl:mau-region. G đổi tên "Ghi chú dùng AI".

Chương 6 giữ: fig:scale-thoi-gian (a), tbl:workers, format-thoi-gian, join, skew-cau-hinh, cache-tong, pandas-spark, chat-luong-5m, tong-hop. Chương 7 giữ fig:ke-hoach-so-sanh, ss-noaqe-tasks, ss-aqe-tasks, tbl:mau-ngay, mau-cach-ly.

Đếm 2026-11-16 (token đến dòng VERIFY, gồm bảng): ch3 ~1480, ch4 ~2030, ch5 ~970, ch6 4394, ch7 ~1110. Ch7 có thể hơi vượt 3 trang.

2026-11-16 đã áp `report/review/verify-round3.md` (A1–A9, B1–B6, C1, E1, E2). Điều phối viên chốt:
- Việc đo do `benchmark-analyst` chạy (src/experiments/README.md:3), nên viết "Đồ án thực hiện..." hoặc chủ thể là job, thí nghiệm, bộ đo. Không viết "Nhóm làm/chạy/đo". Đây là ngoại lệ có chủ ý cho từ cấm "thực hiện".
- Số dòng thô khớp manifest. Số trùng và các lý do cách ly TRỰC TIẾP khớp số lỗi đã chèn. Không gộp `no_clean_order`.
- Bước đối chiếu số dòng thô do `analysis.py` (`run_flags`, cờ `raw_rows_mismatch`) làm, không phải bộ điều khiển (`runner.py`).
- Docker sập khi giới hạn là 9,7 GiB. 6 GB đặt sau sự cố.
- Chỉ image Spark cố định phiên bản, MinIO dùng thẻ `latest`.

Quyết định cũ còn hiệu lực: giữ "nhận định của người viết/nhóm"; giữ "Thành phố Hồ Chí Minh"; (d) "khoảng 7–12%". Dòng "Phần nhóm tự kiểm tra" (G.3), dòng F:5, lớp, giảng viên, tác giả slide do người dùng cung cấp, chỉ được sửa dấu câu.

Khoá trích dẫn: slide-c1, slide-c2, slide-c4, slide-c5, minio-docs, spark-cluster, spark-config, spark-sql-tuning, spark-tuning, spark-ansi, spark-monitoring, spark-standalone, pyspark-cache, hadoop-s3a, chainguard-minio, bex-minio, docker-767, spark-cloud, hadoop-s3-third-party, wsl-config. Sau lượt này bex-minio, docker-767, spark-standalone, spark-tuning, pyspark-cache chỉ còn được trích ở phụ lục.

Còn `[CHƯA CÓ]`: bìa (ngày nộp). Lệnh Phụ lục F giữ chữ "theo mã, chưa chạy thử".

Cách đếm từ không có Bash: Grep `\S+` với `-o`, output content, `offset` + `head_limit` 1 để dò dòng của token thứ N, tìm điểm chuyển sang dòng `<!-- VERIFY`. Chế độ count chỉ đếm dòng, không đếm token. Tóm tắt sát trần 250 từ.

**Why:** để lần sau tiếp tục đúng chỗ và không làm lại các quyết định đã chốt.
**How to apply:** kiểm lại file thực tế trong report/sections trước khi viết tiếp; điều phối viên có thể đã sửa vài dòng.
