# Kết quả source-verifier, bản nháp 1 chương 3–7 (2026-11-08) — danh sách việc cần sửa

## A. SAI — phải sửa
1. 90 `[@slide-c5]`: tên đúng là "Chương 5 — Spark và Data Analytics" (tên tệp trên Drive). Ch.1 "Giới thiệu dữ liệu lớn", ch.2 "Tính toán song song và phân tán", ch.4 "Hệ thống lưu trữ" đúng.
2. 05 mục 5.6 "Đầy đĩa": Spark 4.0.0 mặc định `spark.worker.cleanup.enabled=true`, `interval=1800` (30 phút), `appDataTtl=604800` (7 ngày) [@spark-standalone]. Đồ án không "bật" mà RÚT NGẮN: interval 1800→600 s, TTL 604800→3600 s.
3. 06 mục 6.2 và 6.11: "CV vượt 10% ở hai nhóm" chỉ đúng cho `processing_seconds_total` của các thí nghiệm ETL. Truy vấn ngắn cũng có CV > 10%: (c) q1 thô 17,0%, q1 Parquet 19,5%, q2 Parquet 91,5%, q3 Parquet 21,0%; (f) nocache q5 23,3%, cache q3 12,6%, cache q5 15,8%. Giới hạn phạm vi câu. (11,92% và 12,70% đúng.)
4. 06 mục 6.4 ý cuối "kể cả lấy giá trị lớn nhất, tỉ lệ thời gian vẫn dưới 4 lần": 87,745/21,895 = 4,01 (trên 4). Chỉ dưới 4 nếu chia cho max 500k: 87,745/22,631 = 3,88. Nói rõ phép chia hoặc "khoảng 4 lần".
5. 05 mục 5.5: test host là **68 passed in 4.12s** (test_build_docx 12, test_experiments 29, test_experiments_pandas 15, test_data_generation 12), nguồn `results/logs/test_host.log`. Bỏ [CHƯA CÓ], sửa 44→68, thêm dòng test_build_docx.py vào bảng kiểm thử.
6. 90 `[@docker-767]`: issue tồn tại; người tạo M-transferts; mở 21/10/2026; tiêu đề "Docker Desktop 4.95.0 / WSL2: intermittent startup failure (0xc00000fd) and unexplained backend errors"; nguyên nhân chưa xác định. Tác giả IEEE là M-transferts.
7. 05 mục 5.1 trích dẫn đặt sai ý: bài bex.co nói image bị xoá khỏi Docker Hub giữa 9/2026 nhưng KHUYÊN dùng quay.io → không ủng hộ ý "quay.io không kéo được". Đặt `[@bex-minio]` cạnh ý Docker Hub; `[@chainguard-minio]` cạnh ý image miễn phí của Chainguard; ý quay.io ghi là quan sát của đồ án (infra/README.md).

## B. Cần đánh dấu là nhận định của người viết / chưa có nguồn
- 07 mục 7.4 "với heap 1 GB, phép bỏ trùng phải tràn ra đĩa" → thêm "(nhận định của người viết)".
- 06 mục 6.6 "q2 lợi nhiều nhất vì JSON lines phải parse cả dòng" → đánh dấu nhận định.
- 06 mục 6.7 "bốn sort-merge còn lại là join giữa hai bảng lớn (vd order_items với orders)": plan_check chỉ có số đếm → bỏ ví dụ cụ thể hoặc ghi là suy luận.
- 07 mục 7.4 stage 33/37 "skipped vì dùng lại kết quả shuffle": tài liệu không giải thích lý do → ghi là nhận định.
- 05 mục 5.6 "đã đóng ứng dụng nặng, tạm dừng Windows Update" trước khi đo: không có bằng chứng trong repo; chỉ viết được "không có container lạ (cột foreign_containers trống ở mọi lần chạy)". Bỏ hoặc ghi "theo người thực hiện" — KHÔNG khẳng định như có bằng chứng.
- 04 mục 4.1 "MinIO tương thích S3": thêm một nguồn chính thức của MinIO (vd trang tài liệu MinIO) — nếu không có URL đã kiểm thì để [CHƯA CÓ: nguồn MinIO].
- Chú thích ảnh 08, 09, 10, 12: app ID / query ID / stage ID không hiện trên phần ảnh đã cắt; ghi nguồn là `results/logs/screenshots/README.md`.

## C. Cải thiện chính xác
- 06: thông lượng 273.766 rows/s là trung bình thông lượng từng lần (tổng dòng / trung bình thời gian = 271.340). Nêu cách tính.
- 06: "0,95 đến 1,09 ở cả 8 cấu hình" → "ở cả 4 cặp".
- 06 (e): có thể dùng lập luận 104 task = 64 − 9 + 49 lần tách (khớp ảnh 07 và 10).
- 06 (e): phát hiện auto + AQE chậm hơn ở giai đoạn order_items (balanced 26,627 vs 22,581; skew 28,846 vs 22,167) đã xác nhận đúng; 84,07 vs 73,89 (10,18 s) đúng. Giữ, ghi chưa kết luận nguyên nhân với n = 3.
- 06 (f) cache: cả 3 lần 8/8 partition, 9.024.635 dòng, mức "Disk Memory Deserialized 1x Replicated"; bộ nhớ r1 215,9 MiB, r2 251,9 MiB, r3 215,9 MiB; đĩa r1 41,0, r2 20,5, r3 41,0 MiB → viết "khoảng 216–252 MiB trong bộ nhớ, 20–41 MiB trên đĩa (r1–r3)". Mặc định `DataFrame.cache()` là MEMORY_AND_DISK_DESER [@pyspark-cache].
- 05 bảng công nghệ: numpy 2.5.4 / pandas 3.1.1 / pyarrow 26.0.1 / python 3.12.10 là môi trường SINH DỮ LIỆU trên host (manifest). Container dùng numpy 2.2.6 / pandas 2.3.3 / pyarrow 25.0.1, Python 3.10.12 (test_etl.log). matplotlib 3.11.2 chỉ có ở tests/README (không có trong results/) → ghi rõ hoặc bỏ.
- 05: Storage Memory 434,4 MiB = (1024 − 300) × 0,6 khớp công thức ở "Tuning – Spark 4.0.0", https://spark.apache.org/docs/4.0.0/tuning.html → thêm khoá `[@spark-tuning]`.
- 07: mẫu dữ liệu đọc từ đầu ra ETL `app-20261106181012-0003` (lần chạy đầu ngày 06/11, cũng là `results/metrics/orders_5m.json`), không phải từ bộ đo chính thức → thêm một câu.
- 07 ảnh 01: 68 ứng dụng = 63 chính thức (`-0005`…`-0067`, liên tục) + 5 lần chạy thử (`-0000`…`-0004`); ảnh chụp trước `-0068`/`-0069`. Có thể viết cụ thể.
- 07 ảnh 09: Shuffle Write max = 1.059.025 bản ghi, trùng chính xác `rows_max` trong partition_stats (bằng chứng mạnh hơn 1.059.341).
- Nhãn trùng tên giữa fig và tbl (`scale-giai-doan`, `skew`, `cache`, `pandas`) → đổi để nhãn duy nhất.
- 06 mục 6.1: thêm nguồn `results/logs/environment.txt`.

## D. [CHƯA CÓ] lấp được
- 03 mục 3.3 dung lượng thô (tổng 5 bảng, từ `results/metrics/datasets/datasets_summary.csv`): 500k 104.840.158 B ≈ 104,84 MB; 1m 211.124.477 B ≈ 211,12 MB; 2500k 537.773.401 B ≈ 537,77 MB; 5m 1.089.695.264 B; 5m_skew 1.063.216.156 B.
- 03 mục 3.4 lỗi ngày orders_5m: bad_order_date 99.949; bad_event_time 100.375; bad_signup_date 9.847 (datasets_summary.csv).
- 03 mục 3.8 máy: Intel Core i5-14400F, 10 nhân / 16 luồng; RAM 15,76 GB; ổ MAXBY MAX3500 1TB NVMe SSD, một ổ vật lý chia C:/D: (`results/logs/environment.txt`).
- 05 mục 5.1 MinIO: RELEASE.2026-10-23T20-06-51Z; Docker engine 29.9.2 (environment.txt).
- 90 ngày truy cập: 2026-11-08 cho mọi URL. Tiêu đề:
  - spark-config "Configuration - Spark 4.0.0 Documentation"; spark-sql-tuning "Performance Tuning - Spark 4.0.0 Documentation"; spark-ansi "ANSI Compliance - Spark 4.0.0 Documentation"; spark-monitoring "Monitoring and Instrumentation - Spark 4.0.0 Documentation"; spark-standalone "Spark Standalone Mode - Spark 4.0.0 Documentation"; pyspark-cache "pyspark.sql.DataFrame.cache — PySpark 4.0.0 documentation"; hadoop-s3a "Hadoop-AWS module: Integration with Amazon Web Services".
  - chainguard-minio "Secure and Free MinIO Chainguard Containers", M. Moser, D. J. Ledkov, L. Tagliaferri, A. Jain, Chainguard, 27/10/2025.
  - bex-minio "MinIO Vanished From Docker Hub: The One-Line Fix and the Migration You Actually Owe Yourself", D. Noda, 25/09/2026.
  - spark-tuning (mới) "Tuning - Spark 4.0.0 Documentation", https://spark.apache.org/docs/4.0.0/tuning.html.

## E. Slide
Nội dung slide (5V, Data Lake, speedup/Amdahl, object storage, Parquet, DAG, cache, broadcast join…), tên giảng viên, năm: CHƯA KIỂM ĐƯỢC. Người dùng sẽ tải PDF về `docs/references/slides/` để kiểm ở vòng sau. Lần này giữ các trích dẫn slide, thêm `[CHƯA CÓ: số trang slide]` nếu cần, không thêm khẳng định mới gán cho slide.
