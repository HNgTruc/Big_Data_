# Kết quả source-verifier, vòng 3: kiểm đổi nghĩa sau khi viết lại (2026-11-16)

**Trạng thái tệp: HOÀN TẤT.**

Số mục: A 9, B 6, C 1, D 0, E 2.

Phạm vi: so `report/sections/` hiện tại với các câu đã chốt ở `report/review/verify-round2.md` và với nguồn gốc (`results/`, mã, README, `docs/design/`). Không đọc được bản ở commit 340cc5c (không có Bash, đối tượng git nén). Văn bản slide trong scratchpad đã bị xoá. PDF ở `docs/references/slides/` cũng không đọc được vì máy thiếu `pdftoppm`, nên phần slide chỉ đối chiếu theo `report/review/verify-slides.md` và các khối VERIFY.

Ký hiệu `06:58` là `report/sections/06-...md`, dòng 58. `D:93` là `95-phu-luc-d-...md`, dòng 93 (tương tự cho A, B, C, E, F, G).

Ghi chú: nhiều mục dưới đây có thể đã có từ trước lượt viết lại. Không có bản cũ nên không tách được. Dù vậy, chúng đều lệch nguồn và đáng sửa.

## A. Đổi nghĩa (phải sửa)

### A1. 05:29, phạm vi đối chiếu số đếm bị nới rộng (nặng nhất)
- **Câu hiện tại:** "Với cả năm bộ dữ liệu, số dòng thô, số dòng trùng đã bỏ và từng lý do cách ly khớp hoàn toàn với số lỗi đã chèn trong manifest".
- **Vấn đề:** (1) "từng lý do cách ly" gồm cả `no_clean_order`, vốn là hệ quả dây chuyền chứ không phải lỗi đã chèn. Đây đúng là lỗi A2 của vòng 2, nhưng ở chỗ khác: 00:3, 01:12, 03:9, 06:34, 09:5 đã có chữ "trực tiếp", riêng câu này thì không. (2) "Số dòng thô khớp với số lỗi đã chèn" nối sai quan hệ: số dòng thô khớp số dòng ghi trong manifest, không phải khớp số lỗi.
- **Nguồn:** `docs/design/etl.md:60`. Danh sách các lý do được đối chiếu không có `no_clean_order`, và dòng 63 tách riêng `no_clean_order`.
- **Thay bằng:** "Với cả năm bộ dữ liệu, số dòng thô khớp manifest, còn số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp hoàn toàn số lỗi đã chèn (`docs/design/etl.md`)."

### A2. 05:13, "cố định phiên bản image" mâu thuẫn với thẻ `latest`
- **Câu hiện tại:** "... một tệp cấu hình dựng đủ MinIO, master và 2 worker, cố định phiên bản image và giới hạn số lõi, bộ nhớ ..."
- **Vấn đề:** chỉ image Spark cố định phiên bản. MinIO và `mc` dùng thẻ `latest`, và chính 05:11, 08:50, F:37 nói thẻ này có thể đổi.
- **Nguồn:** `infra/.env.example:4-6` (`apache/spark:4.0.0-python3`, `cgr.dev/chainguard/minio:latest`, `minio-client:latest`).
- **Thay bằng:** "... cố định phiên bản image Spark (MinIO dùng thẻ `latest`, xem mục 8.5) và giới hạn số lõi, bộ nhớ ..."

### A3. 05:9, Hadoop 3.4.1 bị biến thành lý do chọn Spark 4.0.0
- **Câu hiện tại:** "Nhóm chọn phiên bản 4.0.0 vì image chính thức kéo được trên máy và chứa sẵn Hadoop 3.4.1, nên `hadoop-aws` phải cùng phiên bản 3.4.1."
- **Vấn đề:** khi gộp câu, "chứa sẵn Hadoop 3.4.1" thành vế thứ hai của "vì". Nguồn chỉ nói image kéo được, còn việc nó chứa Hadoop 3.4.1 là hệ quả và quyết định phiên bản `hadoop-aws`.
- **Nguồn:** `infra/README.md:8` ("`apache/spark:4.0.0-python3` kéo được; chứa Hadoop 3.4.1 → dùng `hadoop-aws` 3.4.1"), `infra/.env.example:2`.
- **Thay bằng:** "Nhóm chọn phiên bản 4.0.0 vì image chính thức `apache/spark:4.0.0-python3` kéo được trên máy. Image này chứa sẵn Hadoop 3.4.1, nên `hadoop-aws` phải cùng phiên bản 3.4.1."

### A4. 06:72, hiệu ứng bộ nhớ viết như đã có
- **Câu hiện tại:** "Phép so sánh cũng nhân đôi bộ nhớ executor (1 lên 2 GB tổng), nên S phản ánh cả hiệu ứng bộ nhớ."
- **Vấn đề:** câu khẳng định mạnh hơn 8.2. Ở 08:26, xu hướng bộ nhớ đẩy S lên là nhận định, và "Đồ án chưa tách được hai hiệu ứng". Không có số đo bộ nhớ hay spill cho (b) (verify-round2, mục "Các ý mới": `scale_workers` không có event log).
- **Thay bằng:** "Phép so sánh cũng nhân đôi tổng heap executor (1 lên 2 GB), nên S có thể gộp cả hiệu ứng bộ nhớ. Đồ án chưa tách được hai hiệu ứng này (mục 8.2)."

### A5. 07:67, mất nhãn nhận định
- **Câu hiện tại:** "Sự trùng khớp này cho thấy phép đo dùng để chọn tham số phản ánh đúng phân vùng lớn nhất khi chạy thật."
- **Vấn đề:** VERIFY của chính chương (07:87) ghi đây là nhận định rút từ sự trùng khớp số, nhưng câu trong thân bài không có nhãn. Hai con số trùng nhau chỉ ở lần r1 (ảnh 09).
- **Thay bằng:** "Theo nhận định của nhóm, sự trùng khớp này (ở lần r1) cho thấy phép đo dùng để chọn tham số phản ánh đúng phân vùng lớn nhất khi chạy thật."

### A6. D:244, mất nhãn nhận định khi chuyển sang phụ lục
- **Câu hiện tại:** "Ở bộ 500k và 1M, chi phí cố định mỗi giai đoạn chi phối thời gian Spark (mục 6.4)."
- **Vấn đề:** mục 6.4 (06:48) chỉ nói "phần lớn là chi phí lập lịch stage, ghi và đọc lại Parquet trên MinIO (nhận định của nhóm)". Câu ở D.14 viết thành khẳng định.
- **Thay bằng:** "Ở bộ 500k và 1M, chi phí cố định mỗi giai đoạn có vẻ chi phối thời gian Spark (nhận định của nhóm, mục 6.4)."

### A7. 04:66, "từng sập dưới giới hạn 6 GB" mâu thuẫn với C.9
- **Câu hiện tại:** "Nhóm giữ giá trị này vì Docker Desktop từng sập dưới giới hạn 6 GB (mục 5.5)."
- **Vấn đề:** C:150 và nguồn ghi rằng lúc sập, giới hạn là 9,7 GiB. Giới hạn 6 GB chỉ được đặt sau sự cố. Câu này chép từ `infra/README.md:108`, vốn cũng mơ hồ như vậy. Mức ưu tiên thấp nếu câu có từ trước.
- **Nguồn:** `infra/README.md:73` ("Giới hạn Docker lúc sập là 9,7 GiB ... Sau khi đặt `.wslconfig` với `memory=6GB` ...").
- **Thay bằng:** "Nhóm giữ giá trị này để cụm nằm trong giới hạn 6 GB của WSL2, giới hạn được đặt sau một lần Docker Desktop sập (mục 5.5)."

### A8. C:154, "sự phụ thuộc vào Internet trong lúc đo" không có nguồn
- **Câu hiện tại:** "Chuyển bộ đệm vào `data/ivy_cache/` trên host (mục C.3) loại bỏ chi phí này và sự phụ thuộc vào Internet trong lúc đo."
- **Vấn đề:** không nguồn nào nói đến Internet. `src/experiments/README.md:49` ghi "jar ... chỉ tải một lần; lần chạy đầu tiên của cả bộ vẫn tải". `infra/README.md:80` ghi bộ đệm "chỉ tránh tải lại ở driver". Như vậy câu hiện tại tuyệt đối hơn nguồn.
- **Thay bằng:** "Chuyển bộ đệm vào `data/ivy_cache/` trên host (mục C.3) giúp jar chỉ tải một lần, lần chạy đầu tiên của cả bộ vẫn tải (`src/experiments/README.md`). Trong bộ đo chính thức, thời gian tải jar chỉ vài chục mili giây mỗi lần (mục C.3)."

### A9. 01:7, "và giải thích vì sao" (tuỳ mức, ưu tiên thấp)
- **Vấn đề:** câu hứa giải thích nguyên nhân, trong khi 06:72, 08:13 và 09:13 nói nguyên nhân speedup thấp phần lớn còn là suy đoán, và 10,18 giây ở (e) chưa giải thích được.
- **Thay bằng:** "... thì thời gian xử lý thay đổi bao nhiêu, và phân tích nguyên nhân có thể."

## B. Gán sai chủ thể

### B1. 00:3, "Nhóm làm 7 thí nghiệm": quay lại lỗi B8 của vòng 2
- **Nguồn:** `src/experiments/README.md:3` ("Người chạy đo chính thức: `benchmark-analyst`"). Vòng 2 đã chốt câu "Đồ án thực hiện 7 thí nghiệm, tổng cộng 69 lần chạy."
- **Thay bằng:** "Đồ án thực hiện 7 thí nghiệm, tổng cộng 69 lần chạy."

### B2. 06:7, "Nhóm chạy bộ đo chính thức ngày 2026-11-07"
- **Vấn đề:** cùng nguồn với B1. Bảng D.6 ghi trung tính.
- **Thay bằng:** "Bộ đo chính thức chạy ngày 2026-11-07, từ 22:00:54 đến 23:41:37 (giờ Việt Nam), ..."

### B3. D:93, "Bộ điều khiển còn đối chiếu số dòng thô của các lần ETL với manifest"
- **Vấn đề:** bước đối chiếu này do bộ phân tích làm, không phải bộ điều khiển. Ở vòng 2 (A3), câu này ở thể bị động ("còn được đối chiếu"). Khi đổi sang chủ động, chủ thể bị gán sai.
- **Nguồn:** `src/experiments/common/analysis.py:30-40` (hàm `run_flags` đặt cờ `raw_rows_mismatch` và cả `workers_changed`). `runner.py:309-324` chỉ ghi `raw_rows_manifest` vào bản ghi. 4:86 và C:37 dùng "bộ điều khiển" theo nghĩa `runner.py`. Phép đối chiếu 49 số đếm do chính job Pandas làm (cột `all_match`).
- **Thay bằng:** "Bước phân tích (`src/experiments/common/analysis.py`) còn đối chiếu số dòng thô của các lần ETL với manifest, còn mỗi lần Pandas tự đối chiếu 49 số đếm."

### B4. G:34, "nhóm so số dòng trùng đã bỏ ... với số lỗi đã chèn"
- **Vấn đề:** việc đối chiếu chạy tự động. Đặt trong phụ lục ghi chú AI, câu này dễ hiểu thành người đã kiểm bằng tay.
- **Nguồn:** `docs/design/etl.md:60` ("Đối chiếu tự động với manifest cho cả 5 bộ").
- **Thay bằng:** "Đối chiếu số đếm: số dòng trùng đã bỏ và các lý do cách ly trực tiếp được đối chiếu tự động với số lỗi đã chèn (`docs/design/etl.md`), baseline Pandas làm 49 phép đối chiếu mỗi lần chạy (mục 5.4)."

### B5. 06:163, "Nhóm viết lại cùng luật làm sạch ... bằng Pandas" (ưu tiên thấp)
- **Vấn đề:** repo không ghi ai viết mã baseline (cùng loại với B7 của vòng 2). G.2 cho thấy mã do các agent viết.
- **Thay bằng:** "Thí nghiệm (g) viết lại cùng luật làm sạch và ba bảng tổng hợp bằng Pandas, ..."

### B6. 04:38, "nhờ đó nhóm đo được thời gian từng giai đoạn độc lập" (ưu tiên thấp)
- **Vấn đề:** người đo là job, không phải nhóm (06:15, B:34: "do job tự đo").
- **Thay bằng:** "..., nhờ đó job đo được thời gian từng giai đoạn độc lập."

## C. Tham chiếu hoặc vị trí bảng, hình sai

### C1. 06:135, dẫn hai hình của chương 7 mà không ghi vị trí (ưu tiên thấp)
- **Câu hiện tại:** "... task lâu nhất giảm từ 0,5 xuống 0,2 giây (@fig:ss-noaqe-tasks, @fig:ss-aqe-tasks)."
- **Vấn đề:** hai hình này nằm ở 7.4. Mọi chỗ dẫn khác trong chương 6 đều ghi "Phụ lục D/E".
- **Thay bằng:** "(@fig:ss-noaqe-tasks, @fig:ss-aqe-tasks, mục 7.4)".

Mọi tham chiếu "mục X.Y", "Phụ lục X", `@tbl:`, `@fig:` khác ở chương 3 đến 8 và phụ lục A đến G đều trỏ đúng nội dung (đã mở từng mục đích).

## D. Mất yêu cầu đề hoặc điểm trung thực

Không có mục nào. Chi tiết:
- **Đề 5.1–5.8** (`docs/requirements/yeu-cau-do-an.md:24-31`): 5.1 ở 3.1, 3.7. 5.2 ở 3.6 (ba V cộng nhu cầu phân tán ở 03:55). 5.3 ở 3.1–3.5. Ví dụ bản ghi thô chỉ còn ở A.1, có câu dẫn ở 03:17, chấp nhận được. 5.4 ở 3.7, 7.3. 5.5 ở 5.1, gồm cả Docker Compose và Pandas. 5.6 ở 4.1 với @fig:kien-truc. 5.7 ở chương 6, 7. 5.8 ở 5.3 và Phụ lục F.
- **Điểm trung thực bắt buộc:** (e) trái giả thuyết ở biến thể ép shuffle (00:3, 06:133, 08:7, 09:9). AQE có tách nhưng skew không thành nút cổ chai (06:135, 06:141, 08:7). S 1,29, E 0,64, nguyên nhân phần lớn là suy đoán (06:70-72, 08:13, 09:13). Pandas nhanh hơn ở bộ nhỏ, trong hai môi trường khác nhau (00:3, 06:174, 08:30, 09:9). RAM host sát (00:3, 06:9, 08:36, 09:13). Cờ dirty 57/69 (06:11, 08:38). (d) khoảng 7–12%, chênh với `auto` trong mức nhiễu (06:110, 06:187, 09:9). Thông lượng chưa xác nhận bão hoà (06:46, 06:184). Đều còn ở thân bài.

## E. Văn phong còn vi phạm (tuỳ chọn)

1. **`report/sections/README.md:45`** còn ghi "nhận định của người viết", trong khi thân bài đã đổi hết thành "nhận định của nhóm". Các khối VERIFY cũng còn "người viết". Đề xuất thống nhất README (vòng 2, H1).
2. **06:116, "Giả thuyết có hai vế":** vế ép shuffle thực ra gồm hai ý: bộ lệch chậm hơn khi tắt AQE, và AQE thu hẹp chênh lệch. Vòng 2 (F2) tính là ba vế. Không đổi nghĩa, chỉ cần thống nhất nếu muốn.

Không còn dấu chấm phẩy trong câu văn thân bài (chỉ còn ở dòng Nguồn). Không còn "không chỉ ... mà còn" (chỉ còn trong VERIFY).

## Đã kiểm đạt

### Sáu điểm report-writer tự nêu
1. **06:72 "Nguyên nhân của speedup thấp phần lớn còn là suy đoán":** ĐẠT. Khớp 08:13 ("Nguyên nhân thì chưa đo trực tiếp") và @tbl:speedup-bang-chung: cả 4 dòng đều có cột "Còn là suy đoán". 09:13 nói cùng ý. Lỗi duy nhất là vế bộ nhớ ở cuối đoạn (A4).
2. **D:204 "(7 thường, 3 có tách lệch)":** ĐÚNG, đã xem tận gốc. Ở cả 3 lần của `skew_shuffle_aqe`, `results/metrics/skew/plan_check.csv:20-22` ghi `SortMergeJoin` = 7 và `SortMergeJoin(skew=true)` = 3. `src/experiments/common/eventlog.py:20-21, 40-52` đếm theo tên nút chính xác, mà AQE đổi tên nút tách lệch thành "SortMergeJoin(skew=true)", nên hai cột không chồng nhau, tổng 10. Các cấu hình ép shuffle khác đều có 10.
3. **02:7 "nâng cấp phần cứng là chưa đủ":** cùng nghĩa với câu cũ "chứ không chỉ nâng cấp phần cứng" (ghi ở VERIFY 02:77). Vòng 2 đã xác nhận c1 tr. 10, 11 đúng ý. Không đọc lại được slide ở vòng này (xem phần dưới).
4. **05:7 câu tóm vai trò Spark, MinIO, S3A, Docker Compose:** ĐẠT. Khớp 4.1 (04:7-11), @tbl:cong-nghe, `infra/.env.example` (`HADOOP_AWS_VERSION=3.4.1`). Bộ sinh và Pandas chạy trên host, không thuộc "cụm", nên "Docker Compose chạy toàn bộ cụm" vẫn đúng.
5. **G:35 "Phần nhóm tự kiểm tra":** câu hiện tại "nhóm xác nhận đã chạy và kiểm tra toàn bộ, kết quả đều bình thường. Đây là xác nhận của nhóm, repo không có bản ghi riêng ..." vẫn giữ đủ hai vế (xác nhận, không có bản ghi). Đổi dấu câu không đổi nghĩa. Không kiểm được nội dung xác nhận.
6. **Số liệu hoặc nguồn mới:** không thấy con số nào thiếu nguồn. Mọi con số trong các mục phụ lục mới (D.6 đến D.14, A.3, A.4, B.4 đến B.6, C.5 đến C.9, E.5, E.6) đều có dòng VERIFY trỏ về `results/` hoặc vòng 1, 2. Đã tính lại: 35,27 và 23,4 (D.8); 4 đến 13% (06:90); 7% (06:74); 1,9 (D.7); 64 − 9 + 49 = 104. Riêng `results/logs/test_clone.log` (F:70, F:110, F:126, G:32) chưa có trong vòng 2, nhưng tệp có thật (chạy 2026-11-09 ở commit 8c0bcf1), và các câu trích đúng nội dung: dừng mã 1 và 2, 69 passed, SHA-256 trùng ở 5 tệp dữ liệu, chỉ hai `plan_check.csv` bị đổi. Ngoại lệ: ý "Internet" ở A8.

### Đổi bị động sang chủ động, gán chủ thể đúng (mẫu đã kiểm)
- "Bộ điều khiển" ở 04:86, B:34, B:45, B:47, F:110, C:70 đúng với `runner.py` và `src/experiments/common/README.md:29`.
- "Bộ phân tích đọc event log" (04:86, B:53) đúng.
- "Job đo riêng ở `stats_seconds`" (04:46), "agent ghi hai tệp này" (06:11) và "Job xuất mẫu đếm lại trực tiếp trên MinIO" (05:29) đều đúng.

### Gộp đoạn, quan hệ nhân quả (đã kiểm, đạt)
- 06:110: "Phần chậm thêm nằm ở ba giai đoạn có join". Khớp @tbl:join: `orders`, `order_items`, `aggregates` tăng, `web_events` gần như bằng nhau.
- 06:139: "`products` được broadcast nên khoá lệch không đi qua shuffle". Khớp ảnh 11 và `results/logs/screenshots/README.md:65`. Khoá lệch chỉ ở `product_id` (`src/data_generation/tables.py:33-38, 63, 81`).
- D:131: "chậm chủ yếu ở `order_items`": chênh 11,9 trên tổng 15,9 giây.
- B:57: "4 MiB nằm giữa hai nhóm". Khớp `src/experiments/skew/README.md:45-46`.
- A:77: `product_id` lệch ở `order_items` và `web_events`, còn `order_id`, `customer_id`, ngày không lệch. Khớp `tables.py`.
- 05:33, 05:35, 05:37: giữ được rào "không khẳng định", "chỉ giải quyết dung lượng", "repo không có ghi nhận".

### Phạm vi và rào đã giữ
"ở biến thể ép shuffle" (06:133, 06:137, 06:188), "lần r1" (06:135, 08:7), "trong mức nhiễu" (06:110), "chưa đo" (03:55, 06:176, 08:36, F:26), "theo mã" (F:110), "suy luận" (06:112, 06:200, D:194), "không đo mức dùng CPU" (06:174, 08:30). 06:46, 06:184 giữ đúng câu B2 của vòng 2. 06:74 giữ đủ bốn mốc 77,14, 77,16, 78,65, 82,21 (C4 vòng 2).

## Không kiểm được, kèm lý do

- **Bản cũ ở commit 340cc5c:** không có Bash, đối tượng git nén nên không đọc được. Không tách được mục nào do lượt viết lại gây ra, mục nào có từ trước.
- **Slide:** thư mục văn bản slide trong scratchpad đã bị xoá. Read không mở được PDF ở `docs/references/slides/` vì máy thiếu `pdftoppm`. Điểm (3) chỉ so với câu cũ (VERIFY 02:77) và kết luận vòng 2, không đọc lại slide c1 tr. 10, 11.
- **Nội dung xác nhận ở G:35:** người dùng cung cấp, repo không có bản ghi.
- **Ai viết mã baseline Pandas, ai chụp ảnh (B5, 07:3, E:3):** repo không ghi người thực hiện. "Nhóm chụp ảnh" không bị xếp là sai.
- **Tài liệu tham khảo:** không mở lại trang web nào ở vòng này. Dựa vào vòng 1, 2.
- **Số lượng và độ dài:** theo yêu cầu, không kiểm lại 603 con số, nhãn, tham chiếu treo và số trang.
