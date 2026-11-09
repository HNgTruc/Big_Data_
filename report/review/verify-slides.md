# Kiểm chứng trích dẫn slide (chương 1, 2, 4, 5), 2026-11-08

Phạm vi: mọi chỗ trích slide trong `report/sections/`. Tệp này chỉ báo cáo, chưa sửa nội dung báo cáo.

Quy ước:
- **Trang** là số trang PDF, viết "tr.".
- **Đã xem** nghĩa là đã đọc văn bản trích từng trang do điều phối viên cung cấp (hoặc ảnh, nếu ghi rõ). **Suy luận** là kết luận của người kiểm, không phải chữ trên slide.
- "Không thấy" luôn có nghĩa "không thấy trong phần văn bản trích được". Chữ nằm trong hình có thể chưa được trích (danh sách trang nên render ở cuối mục B).

Tổng hợp 12 chỗ trích: **ĐÚNG 5, ĐÚNG MỘT PHẦN 7, KHÔNG THẤY 0**. Có 6 ý nhỏ trong các câu không thấy trên slide được trích (mục B.3).

## A. Thông tin thư mục

| Slide | Tên ở tr. 1 (đã xem) | Khoa, trường, năm ở tr. 1 | Số trang PDF | Chân trang in | Tên giảng viên |
|---|---|---|---|---|---|
| c1 | Chương 1: Giới thiệu dữ liệu lớn | Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, 2026 | 51 | "n/56" | Không có |
| c2 | Chương 2: Tính toán song song và phân tán | Như trên | 53 | "n/53" | Không có |
| c4 | Chương 4: Hệ thống lưu trữ | Như trên | 57 | "n/57" | Không có |
| c5 | Chương 5: Spark và Data Analytics | Như trên | 59 | "n/59" | Không có |

Tên gốc dùng gạch ngang dài sau "Chương N"; bảng trên và mục E viết dấu hai chấm theo quy ước báo cáo. Học phần ở tr. 1: "Nhập môn dữ liệu lớn".

- **Tên giảng viên:** đã xem tr. 1, trang cuối và metadata của cả 4 tệp; tìm thêm các cụm "giảng viên", "TS.", "ThS", "Lecturer", "Instructor" và địa chỉ email: không có kết quả. Metadata author là tổ chức ("Trường Đại học Sài Gòn"). Tr. 1 của cả 4 tệp không có ảnh. Trang cuối của c2, c4, c5 cũng không có ảnh; riêng c1 tr. 51 có 1 ảnh chưa render.
- **Khác biệt so với mô tả nguồn: số trang in không phải lúc nào cũng trùng số trang PDF.** Ở c1, tr. 3 đến tr. 50 trùng nhau, nhưng tr. 51 in "54/56" và mẫu số in là 56 trong khi tệp có 51 trang. Suy luận: bản PDF này có thể đã lược bớt các trang in số 51, 52, 53, 55, 56. Mọi trang c1 đề xuất trích dưới đây đều ≤ 50 nên hai cách đánh số trùng nhau. Tránh trích c1 tr. 51 mà không nói rõ cách đánh số.
- Tiêu đề metadata c4 dài hơn tr. 1 ("Hệ thống lưu trữ dữ liệu lớn"); mục tham khảo nên theo tr. 1, như hiện tại.
- Đã xem ảnh `c1-p42.png` (trang phân cách "Phần 2: Ứng dụng của dữ liệu lớn") và `c4-p27.png` (4 bước khi một DataNode lỗi: bình thường, mất replica, under-replicated, khôi phục).

## B. Từng chỗ trích

### B.1 Bảng kết luận

| Tệp:dòng | Câu trong báo cáo (rút gọn) | Kết luận | Slide, trang (đã xem) | Nhận xét |
|---|---|---|---|---|
| 03:68 | "ba đặc trưng sau, theo khái niệm 5V ở slide chương 1" (Volume, Variety, Veracity) | ĐÚNG | c1 tr. 14; 15-16; 19; 21-22; 26; tr. 7 | Mục Volume không khẳng định "lớn tuyệt đối" khớp c1 tr. 7 (không có ngưỡng GB/TB cố định). Việc áp 3 V vào đồ án là nhận định của người viết. Variety: CSV và Parquet cùng nhóm có cấu trúc, JSON lines bán cấu trúc (c1 tr. 26), nên nói theo mức cấu trúc sẽ sát slide hơn. Value chưa được nhắc. |
| 04:9 | "Lưu trữ đối tượng tách rời lưu trữ khỏi tính toán, khác với HDFS nơi dữ liệu nằm trên chính các nút tính toán (slide chương 4)" | ĐÚNG MỘT PHẦN (sai chương, quá tuyệt đối) | c2 tr. 27, 28, 31, 32; c4 tr. 35, 37; c1 tr. 36 | Trong văn bản c4 không thấy ý tách tính toán khỏi lưu trữ, cũng không thấy câu HDFS đặt dữ liệu trên nút tính toán (chỉ có "data locality": tr. 19, 33, 37). Ý này ở c2 tr. 28, kèm lưu ý: "có thể" tách, và sơ đồ cổ điển không bắt buộc với mọi hệ. Việc MinIO thuộc nhóm object storage có ở c1 tr. 36, c4 tr. 35, 37. "Tương thích S3" không thấy trên slide nào (mục D). Trong đồ án, MinIO và Spark chạy trên cùng một máy (04:7), nên câu không nên hàm ý tách vật lý. |
| 04:32 | "theo tinh thần Data Lake ở slide chương 1: dữ liệu thô giữ nguyên, dữ liệu đã xử lý tách riêng" | ĐÚNG MỘT PHẦN | c1 tr. 31; c4 tr. 47; c5 tr. 52 | c1 tr. 31 chỉ nói Data Lake lưu dữ liệu thô hoặc đã xử lý ở nhiều định dạng. Cách chia vùng (Raw/Landing, Clean/Standardized, Curated/Serving) ở c4 tr. 47. "Giữ nguyên" và vùng `quarantine/` không thấy trên slide; đó là quyết định của đồ án. |
| 04:87 | "Parquet lưu theo cột và nén theo cột, cho phép chỉ đọc những cột cần dùng và đẩy điều kiện lọc xuống tầng đọc (slide chương 4)" | ĐÚNG MỘT PHẦN | c4 tr. 46; c5 tr. 42, 44 | Theo cột, column pruning, nén: c4 tr. 46. Pushdown không thấy trong văn bản c4; c4 chỉ nói metadata/statistics giúp bỏ qua một phần dữ liệu "trong nhiều trường hợp". Predicate pushdown ở c5 tr. 44, kèm lưu ý phụ thuộc khả năng của nguồn dữ liệu (c5 tr. 42). |
| 04:95 | "Bảy thí nghiệm (a) đến (g) ... các kỹ thuật tối ưu học trong slide chương 2 và chương 5" | ĐÚNG MỘT PHẦN | c2 tr. 18, 21; c4 tr. 46; c5 tr. 9, 31, 44, 48, 50, 51 | (b), (d), (e), (f) có khái niệm trực tiếp. (c) có ở c5 tr. 44 và cả c4 tr. 46. (a) mở rộng theo kích thước dữ liệu và (g) so với Pandas không thấy là kỹ thuật trên slide; gần nhất cho (g) là c5 tr. 9 (workload nhỏ thì overhead phân tán có thể lớn hơn lợi ích). |
| 04:116 | "Speedup S = T(1 worker) / T(2 worker); efficiency E = S / 2 (công thức ở slide chương 2)" | ĐÚNG | c2 tr. 21 | Slide: Sp = T1/Tp, Ep = Sp/p, tính theo node. Phân số bị tách dòng khi trích; ví dụ trên slide (100 và 25 phút cho Sp = 4; 4/8 = 50%) xác nhận cách đọc. Áp cho worker với p = 2 là cách dùng của đồ án. |
| 05:25 | "Spark xử lý dữ liệu trong bộ nhớ theo mô hình DAG, có DataFrame và Spark SQL với bộ tối ưu truy vấn, hỗ trợ broadcast join và cache" | ĐÚNG MỘT PHẦN | c5 tr. 6, 8, 9, 26, 31, 42, 51 | DAG, DataFrame, Spark SQL, Catalyst, broadcast, cache: đúng. **"Xử lý trong bộ nhớ" đi ngược lưu ý ở c5 tr. 6:** Spark vẫn có storage I/O, shuffle, disk spill, "in-memory" không có nghĩa mọi dữ liệu luôn ở RAM (thêm c5 tr. 9). c5 tr. 6, 8 cũng không mô tả DAG là mô hình "trong bộ nhớ". Trang tổng quan Spark 4.0.0 cũng không dùng từ "in-memory" (mục D). |
| 06:99 | "Tính speedup S = ... và efficiency E = S / 2" | ĐÚNG | c2 tr. 21 | Lý do chung (phần tuần tự, lập lịch, truyền thông, đồng bộ, skew) ở cùng trang. Ánh xạ sang driver, ghi metadata, MinIO dùng chung là suy luận của người viết; câu hiện đặt trích dẫn trước phần này nên không sai. |
| 06:131 | "Parquet nhanh hơn rõ ở truy vấn dùng ít cột nhờ đọc theo cột và đẩy điều kiện lọc xuống, và nhỏ hơn nhờ nén theo cột" [@slide-c4] | ĐÚNG MỘT PHẦN | c4 tr. 46; c5 tr. 37, 42, 44 | Giống 04:87: pushdown ở c5. Mức "nhanh hơn rõ" là giả thuyết của đồ án, slide không cho mức độ. |
| 06:175 | "broadcast nhanh hơn vì tránh shuffle bảng lớn (slide chương 5)" | ĐÚNG | c5 tr. 27, 40, 43, 51 | c5 tr. 51 nói broadcast "có thể" tránh shuffle bảng lớn và bảng nhỏ vẫn truyền qua mạng. Tên "sort-merge join" không thấy trên slide; "shuffle cả hai phía" có ở tr. 51, nhưng tr. 27 lưu ý không phải mọi join đều buộc như vậy. Nên viết "thường cần". |
| 06:247 | "không cache thì ... làm lại join; có cache thì lần materialize tốn thêm nhưng các truy vấn sau nhanh hơn, có lợi khi K đủ lớn" | ĐÚNG MỘT PHẦN | c5 tr. 6, 31, 32 | Dùng lại dataset, materialize ở action đầu, action sau tái sử dụng: có. "Tốn thêm" và "K đủ lớn" (điểm hoà vốn) không thấy; slide chỉ nói cache có lợi khi dữ liệu thực sự được dùng lại, và cache sai chỗ có thể chậm hơn (tr. 31). |
| 95-e:35 | "Spark chia một job thành các stage tại ranh giới shuffle (nút Exchange), theo mô hình DAG ở slide chương 5" | ĐÚNG | c5 tr. 15, 26, 29, 43 | Slide nói shuffle "thường" tạo ranh giới stage (tr. 26, 29); Exchange là dấu hiệu shuffle trong physical plan (tr. 43). "Skipped" không thấy trên slide; báo cáo đã ghi là nhận định của người viết. |

### B.2 Câu thay thế đề xuất

Cách ghi trang: xem mục E.3. Các câu dưới đây dùng dạng `(slide chương N, tr. X [@slide-cN])`.

- **03:68:** "... theo mô hình 5V ở slide chương 1, tr. 14 [@slide-c1]:". Dòng 71, tuỳ chọn: "**Variety:** dữ liệu có cấu trúc (CSV, Parquet) và bán cấu trúc (JSON lines) trong cùng một job (slide chương 1, tr. 26 [@slide-c1])."
- **04:9:** "**Lớp lưu trữ:** MinIO, một hệ lưu trữ đối tượng tương thích S3 [@minio-docs], giữ dữ liệu thô, dữ liệu sạch và dữ liệu cách ly trong bucket `bigdata`. Object storage được truy cập qua API theo bucket và object key thay vì đường dẫn tệp (slide chương 4, tr. 37 [@slide-c4]). Kiểu cụm cổ điển như HDFS/Hadoop đặt tính toán và lưu trữ cùng trên worker, còn mô hình đám mây có thể tách tính toán khỏi object storage (slide chương 2, tr. 28 [@slide-c2]). Trong đồ án, sự tách này chỉ ở mức dịch vụ vì MinIO và Spark chạy trên cùng một máy."
- **04:32:** "Bucket `bigdata` được chia thành các vùng theo tiền tố đường dẫn. Data Lake có thể lưu cả dữ liệu thô và dữ liệu đã xử lý (slide chương 1, tr. 31 [@slide-c1]), và slide chương 4 minh hoạ cách chia vùng raw, clean, curated (tr. 47 [@slide-c4]). Đồ án áp dụng theo hướng đó: `raw/` giữ nguyên dữ liệu thô, dữ liệu đã xử lý nằm ở `curated/`; vùng `quarantine/` là quyết định riêng của đồ án."
- **04:87:** "**Parquet cho dữ liệu đã xử lý.** Parquet tổ chức dữ liệu theo cột, nhờ đó truy vấn có thể chỉ đọc những cột cần dùng và dữ liệu thường nén hiệu quả (slide chương 4, tr. 46 [@slide-c4]). Định dạng cột còn hỗ trợ đẩy điều kiện lọc xuống, tuỳ khả năng của nguồn dữ liệu (slide chương 5, tr. 42, 44 [@slide-c5]). Thí nghiệm (c) đo trực tiếp lợi ích này (mục 6.6)."
- **04:95:** "Các thí nghiệm (b) đến (f) gắn với các khái niệm trong slide: speedup (slide chương 2, tr. 21 [@slide-c2]), định dạng cột (slide chương 4, tr. 46 [@slide-c4]), broadcast join, data skew, AQE và cache (slide chương 5, tr. 31, 48, 50, 51 [@slide-c5]). Thí nghiệm (a) và (g) là câu hỏi do đồ án đặt ra, để quan sát xu hướng theo kích thước dữ liệu và so sánh với Pandas một máy."
- **04:116:** "... (công thức ở slide chương 2, tr. 21 [@slide-c2])."
- **05:25:** "Spark là engine xử lý dữ liệu phân tán theo partition, dùng DAG để lập lịch job, stage và task, có DataFrame và Spark SQL với bộ tối ưu Catalyst, hỗ trợ broadcast join và cache (slide chương 5, tr. 8, 31, 42, 51 [@slide-c5]). Spark vẫn có I/O lưu trữ, shuffle và tràn đĩa, nên không phải mọi dữ liệu đều nằm trong RAM (tr. 6)."
- **06:99:** "... trên orders_5m (slide chương 2, tr. 21 [@slide-c2])." Phần giả thuyết giữ nguyên.
- **06:131:** "... nhờ đọc theo cột và đẩy điều kiện lọc xuống, và nhỏ hơn nhờ nén theo cột (slide chương 4, tr. 46 [@slide-c4]; slide chương 5, tr. 44 [@slide-c5])."
- **06:175:** "... sort-merge join (thường cần shuffle cả hai phía). Giả thuyết: broadcast nhanh hơn vì có thể tránh shuffle bảng lớn, dù bảng nhỏ vẫn truyền qua mạng (slide chương 5, tr. 51 [@slide-c5])." Nếu cần nguồn cho tên sort-merge join: [@spark-sql-tuning] (mục D).
- **06:247:** "... so không cache với có cache. Giả thuyết: không cache thì mỗi truy vấn đọc lại Parquet và làm lại join; có cache thì action đầu tiên materialize dữ liệu, các action sau có thể dùng lại thay vì chạy lại lineage (slide chương 5, tr. 31, 32 [@slide-c5]). Việc lần materialize tốn thêm thời gian và có lợi khi K đủ lớn là suy luận của người viết."
- **95-e:35:** "... theo mô hình DAG ở slide chương 5, tr. 26, 43 [@slide-c5]." Phần "skipped" giữ là nhận định; có thể bổ sung nguồn hỗ trợ ở mục D, dòng RDD guide.

### B.3 Ý không thấy trên slide được trích

| Ý | Vị trí | Thấy ở đâu | Xử lý theo thứ tự ưu tiên |
|---|---|---|---|
| MinIO tương thích S3 | 04:9, 05:27 | Không thấy trên 4 slide | (a) [@minio-docs], mục D |
| Tách tính toán khỏi lưu trữ; HDFS đặt dữ liệu trên nút tính toán | 04:9 | Không thấy ở c4; có ở c2 tr. 28 | Đổi sang slide chương 2 |
| Đẩy điều kiện lọc xuống của Parquet | 04:87, 06:131 | Không thấy ở c4; có ở c5 tr. 44 | Thêm slide chương 5; có thể thêm tài liệu Spark Parquet |
| Tên "sort-merge join" | 06:175 | Không thấy trên 4 slide | (a) [@spark-sql-tuning] |
| Lần materialize tốn thêm, có lợi khi K đủ lớn | 06:247 | Không thấy | (b) nhận định của người viết |
| Thí nghiệm (a), (g) là kỹ thuật trong slide; `raw/` giữ nguyên; `quarantine/` | 04:95, 04:32 | Không thấy | (b) quyết định hoặc nhận định của đồ án |

### B.4 Chỗ liên quan không có `@slide-c`

- **06:125 (Amdahl):** công thức đang ghi là nhận định của người viết, nhưng có ở c2 tr. 22. Đề xuất: công thức dẫn slide chương 2, tr. 22 [@slide-c2], còn ước lượng p ≈ 0,45 và diễn giải giữ là nhận định. **Ký hiệu khác nhau:** slide dùng s là phần tuần tự, p là số node; báo cáo dùng p là phần song song, N là số worker (p của báo cáo = 1 − s). Đã tính lại: 1/1,29 = 0,775; p = 2 × (1 − 0,775) ≈ 0,45, khớp.
- **05:27:** "MinIO cung cấp API S3" chưa có trích dẫn, nên thêm [@minio-docs]. "Lưu trữ đối tượng của Data Lake" có thể dẫn c4 tr. 48 (data lake dựa trên S3/HDFS).
- **Khối VERIFY và README cần cập nhật khi áp dụng:** 03:122; 04:133-134; 06:358; 95-e:102; 90:21-22; `report/sections/README.md:18` (năm đã có: 2026); `report/review/README.md` chưa có dòng cho tệp này.

### B.5 Trang nên render ảnh

Các trang có hình và liên quan tới kết luận "không thấy", theo thứ tự ưu tiên:

1. c4 tr. 46 và c5 tr. 44 (hình Parquet, có thể có chữ về pushdown).
2. c4 tr. 36 (hình object storage, có thể có ý tách tính toán).
3. c4 tr. 19, 20 (hình HDFS, DataNode có nằm cùng nút tính toán hay không).
4. c5 tr. 6, 26 (hình so sánh MapReduce và Spark, DAG).
5. c2 tr. 21, 22 nếu định chép công thức vào chương 2 (phân số bị tách dòng khi trích; ví dụ số trên slide đã xác nhận cách đọc).

## C. Bảng khái niệm (viết chương 1, 2 và thảo luận)

Tóm tắt là lời của người kiểm, không phải trích nguyên văn. "Tiếng Việt trên slide" chỉ ghi từ đã xem; nhiều thuật ngữ slide để nguyên tiếng Anh.

| Khái niệm | Slide, trang | Slide nói gì | Tiếng Việt trên slide |
|---|---|---|---|
| 5V | c1 tr. 14; chi tiết tr. 15-24; ví dụ tr. 45 | Mô hình "4V + Value" gồm **Volume, Velocity, Variety, Veracity, Value**. 4V mô tả khó khăn, Value là lý do xử lý. Có chú thích NIST xếp khác (Variability thay vào nhóm đặc trưng trực tiếp); học phần dùng 5V này | Khối lượng; Tốc độ; Đa dạng; Độ tin cậy; Giá trị |
| Data Lake | c1 tr. 27, 31; c4 tr. 47, 48; c5 tr. 52 | Lưu dữ liệu thô hoặc đã xử lý, nhiều định dạng, trên hạ tầng mở rộng được, chi phí tương đối thấp; thường schema-on-read; thiếu quản trị dễ thành data swamp; chia vùng raw, clean, curated (c4 tr. 47) | "hồ dữ liệu" (c1 tr. 12); "đầm lầy dữ liệu" (c1 tr. 28, nói về thiếu metadata) |
| Speedup | c2 tr. 21 | Sp = T1/Tp; ví dụ 100 phút và 25 phút cho Sp = 4; có đồ thị lý tưởng so với thực tế | Không dịch |
| Efficiency | c2 tr. 21 | Ep = Sp/p; giảm do phần tuần tự, lập lịch, truyền thông, đồng bộ, skew, overhead khác | Không dịch |
| Định luật Amdahl | c2 tr. 22 | **Sp = 1 / (s + (1 − s)/p)**, s là tỉ lệ tuần tự, p là số node hoặc processor. Ví dụ s = 0,2: S4 = 2,5; p → ∞: Smax = 1/s = 5. Phần tuần tự tạo trần không vượt được bằng cách thêm node | "Định luật Amdahl"; "phần tuần tự"; "trần" |
| Object storage | c4 tr. 8, 36, 37; c1 tr. 26, 36; c2 tr. 27, 28, 32; c5 tr. 49 | Quản lý theo object key/ID, metadata và API; không có POSIX semantics; cập nhật thường cả object; mạnh ở data lake, archive, backup; lưu ý latency, chi phí request và egress, rename/listing. Ví dụ S3, GCS, Azure Blob, MinIO | Không dịch trên slide ("dữ liệu như object"). "Lưu trữ đối tượng" là từ của báo cáo, không thấy trên slide |
| HDFS | c4 tr. 19-28, 33; c2 tr. 28, 31, 32 | Hệ file phân tán của Hadoop, tối ưu file lớn và đọc tuần tự; block lớn; NameNode giữ metadata, DataNode giữ block, data path không qua NameNode; replication, rack awareness; không hợp với file rất nhỏ và point lookup | "hệ thống file phân tán"; "hệ thống file của Hadoop" |
| Parquet, định dạng cột | c4 tr. 35, 39, 46; c5 tr. 37, 44, 48; c1 tr. 26 | Là file format, không phải NoSQL hay table format; đọc đúng cột cần, nén tốt, statistics giúp bỏ qua dữ liệu; column pruning, predicate pushdown; khác wide-column database | "định dạng cột" (c1 tr. 26); "tổ chức dữ liệu theo cột" (c4 tr. 46) |
| DAG | c5 tr. 6, 7, 8, 26; c2 tr. 16 | Đồ thị có hướng không chu trình của các dependency. DAGScheduler chia job thành stage; narrow transformation được pipeline trong cùng stage. Tối ưu truy vấn thuộc Catalyst, không phải DAG scheduler đơn thuần | "DAG tác vụ" (c2 tr. 16) |
| RDD | c5 tr. 21, 22, 35 | Partitioned, distributed, resilient, immutable; API mức thấp, môn nhập môn nên ưu tiên DataFrame | Không dịch; "bất biến" (tr. 22) |
| Lineage | c5 tr. 23, 33; c1 tr. 33 (data lineage) | Mô tả cách dataset được tạo từ dataset cha; là cơ sở tính lại partition bị mất; checkpoint có thể cắt lineage dài (tr. 33) | "phả hệ dữ liệu" (c5 tr. 23) |
| Cache, persist | c5 tr. 6, 31, 32, 48 | Dùng khi dataset được dùng lại; lazy, materialize ở action đầu; dùng memory và/hoặc disk theo storage level; cache sai chỗ có thể chậm hơn; cần unpersist. PySpark DataFrame mặc định MEMORY_AND_DISK_DESER | Không dịch; "cache có chủ đích" (tr. 48) |
| Broadcast join | c5 tr. 27, 40, 43, 51, 56 | Gửi bảng nhỏ tới executor rồi join cục bộ; bảng nhỏ vẫn qua mạng nhưng có thể tránh shuffle bảng lớn; chỉ dùng khi bảng đủ nhỏ; Spark SQL có thể tự chọn hoặc dùng hint; trong plan là BroadcastHashJoin | Không dịch |
| Shuffle | c5 tr. 15, 26, 27, 29, 40, 48, 58; c2 tr. 19 | Phân phối lại dữ liệu giữa partition/task cho grouping, join, repartition; tạo network I/O, có thể tràn đĩa cục bộ, thường tạo ranh giới stage, dễ tạo straggler khi skew | "phân phối lại dữ liệu" (mô tả, không phải tên gọi) |
| AQE | c5 tr. 48; thêm tr. 4, 15, 58 | Mặc định bật trong Spark SQL hiện đại; dựa trên số liệu lúc chạy để gộp partition sau shuffle, đổi chiến lược join, hỗ trợ xử lý skew. Người dùng vẫn cần hiểu shuffle để đọc plan | Không dịch ("Adaptive Query Execution") |
| Driver, executor, cluster manager | c5 tr. 13, 14, 17, 58 | Driver chạy chương trình chính, lập kế hoạch, điều phối task. Executor chạy task, giữ cache/shuffle data, báo trạng thái. Cluster manager cấp tài nguyên cho executor: Standalone, YARN, Kubernetes | Không dịch; "ai cấp tài nguyên?" (tr. 17) |
| Partition | c5 tr. 16, 45; c2 tr. 15 | Đơn vị chia dữ liệu; mỗi task thường xử lý một partition; quá ít thì không tận dụng cụm, quá nhiều thì overhead lập lịch. Các kiểu range, hash, round-robin, không gian/thời gian (c2 tr. 15). `partitionBy` khi ghi là việc khác `repartition` (c5 tr. 45) | "chia dữ liệu" (c2 tr. 15); "phân vùng dữ liệu" (c4 tr. 44). **Dễ nhầm:** "network partition" (c2 tr. 39, 42) là chuyện khác |
| Data skew | c2 tr. 17, 18; c5 tr. 29, 48, 50 | Dữ liệu không đều theo key tạo điểm nóng; hash partitioning vẫn có thể lệch; join, groupBy nhạy với skew; biểu hiện là vài task chạy rất lâu. Giảm bằng salting, repartition, tách hot key, chọn chiến lược join | "dữ liệu lệch"; "lệch tải"; "điểm nóng" |

Thêm cho chương 1, 2: định nghĩa Big Data (c1 tr. 7, 10, 11); pipeline (c1 tr. 33, 40); scale-up, scale-out (c2 tr. 7); data locality (c2 tr. 31, 32); file nhỏ (c4 tr. 28, c5 tr. 49); Catalyst (c5 tr. 42); lazy evaluation (c5 tr. 19, 30). Chú thích NIST ở c1 tr. 14 không kèm tên tài liệu; nếu dùng cần nguồn NIST gốc (chưa kiểm).

## D. Nguồn thay thế đã mở thật

Tất cả mở bằng WebFetch ngày 2026-11-08. WebFetch trả kết quả qua một mô hình tóm tắt, nên các câu dưới đây là câu nó trích lại; nên mở trực tiếp để đối chiếu nguyên văn nếu chép vào báo cáo.

| URL | Tiêu đề trang | Dùng cho | Câu xác nhận |
|---|---|---|---|
| https://raw.githubusercontent.com/minio/minio/master/README.md | MinIO Quickstart Guide | MinIO tương thích S3 (bản mã nguồn mở, đúng dòng sản phẩm đồ án chạy) | "MinIO is a high-performance, S3-compatible object storage solution released under the GNU AGPL v3.0 license." Cùng tệp: "THIS REPOSITORY IS NO LONGER MAINTAINED." |
| https://www.min.io/product/aistor | MinIO AIStor: The Enterprise AI Data Store | Trang hãng; mô tả AIStor, không phải bản đồ án chạy | "enterprise-grade S3-compatible object storage" (mục Objects); chân trang "© 2014-2026 MinIO, Inc." |
| https://docs.min.io/aistor/ | MinIO AIStor Documentation | Tài liệu hãng; yếu hơn | "AIStor natively supports the S3 API for objects, Iceberg for tables, and SFTP for files." Trang không dùng cụm "object storage" hay "S3-compatible" |
| https://spark.apache.org/docs/4.0.0/sql-performance-tuning.html | Performance Tuning - Spark 4.0.0 Documentation | Sort-merge join; AQE | "AQE converts sort-merge join to broadcast hash join when the runtime statistics of any join side are smaller than the adaptive broadcast hash join threshold." AQE "enabled by default since Apache Spark 3.2.0." |
| https://spark.apache.org/docs/4.0.0/sql-data-sources-parquet.html | Parquet Files - Spark 4.0.0 Documentation | Parquet, pushdown (tuỳ chọn) | "Parquet is a columnar format"; `spark.sql.parquet.filterPushdown` mặc định `true` |
| https://parquet.apache.org/docs/overview/ | Overview \| Parquet | Parquet (tuỳ chọn) | "column-oriented data file format designed for efficient data storage and retrieval" |
| https://spark.apache.org/docs/4.0.0/rdd-programming-guide.html | RDD Programming Guide - Spark 4.0.0 Documentation | Hỗ trợ một phần 95-e:35 (dùng lại kết quả shuffle) và 06:247 | "so the shuffle files don't need to be re-created if the lineage is re-computed." Trang không nói về nhãn "skipped" nên phần đó vẫn là nhận định |
| https://spark.apache.org/docs/4.0.0/index.html | Overview - Spark 4.0.0 Documentation | Thay cách nói "trong bộ nhớ" ở 05:25 (tuỳ chọn) | "unified analytics engine for large-scale data processing"; trang không dùng từ "in-memory" |
| https://spark.apache.org/docs/4.0.0/cloud-integration.html | Integration with Cloud Infrastructures - Spark 4.0.0 Documentation | Thảo luận chương 8 về MinIO so với HDFS (tuỳ chọn) | "They cannot be used as a direct replacement for a cluster filesystem such as HDFS"; trang không bàn về data locality |
| https://hadoop.apache.org/docs/r3.4.1/hadoop-aws/tools/hadoop-aws/third_party_stores.html | Working with Third-party S3 Stores | Cơ sở dùng S3A với kho S3 bên thứ ba (tuỳ chọn) | "The S3A connector works well with third-party S3 stores if the following requirements are met:"; trang không nêu tên MinIO |

**Kết quả dò tài liệu MinIO:**
- `docs.min.io`: trang chỉ mục "MinIO Documentation", không có câu về S3.
- `min.io/docs/minio/linux/index.html`: 301 sang `docs.min.io/enterprise/aistor-object-store/`, tiêu đề "MinIO AIStor Documentation", câu duy nhất liên quan là câu "natively supports the S3 API" như trên.
- `docs.min.io/community/minio-object-store/index.html`: cùng tiêu đề, cùng câu.
- `github.com/minio/minio` và `.../blob/master/README.md`: **HTTP 504 ở cả 3 lần thử**, chưa mở được, nên không đề xuất hai URL này. Chỉ `raw.githubusercontent.com` mở được.

**Không mở được:** Hướng dẫn tham khảo IEEE (`journals.ieeeauthorcenter.ieee.org/...IEEE_Reference_Guide.pdf`, 301 sang một Google Doc, nội dung bị cắt, không thấy định dạng cần tìm). Vì vậy mục E dựa theo mẫu đang có trong `90-tai-lieu-tham-khao.md`, **chưa đối chiếu với hướng dẫn IEEE**.

## E. Mục IEEE đề xuất

### E.1 Bốn mục slide

Năm 2026, khoa và số trang đã xem ở mục A. Tên giảng viên giữ `[CHƯA CÓ]` vì slide không có:

```
[@slide-c1]: [CHƯA CÓ: tên giảng viên], "Chương 1: Giới thiệu dữ liệu lớn," bài giảng học phần Nhập môn dữ liệu lớn, Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, 2026, 51 trang.
[@slide-c2]: [CHƯA CÓ: tên giảng viên], "Chương 2: Tính toán song song và phân tán," bài giảng học phần Nhập môn dữ liệu lớn, Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, 2026, 53 trang.
[@slide-c4]: [CHƯA CÓ: tên giảng viên], "Chương 4: Hệ thống lưu trữ," bài giảng học phần Nhập môn dữ liệu lớn, Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, 2026, 57 trang.
[@slide-c5]: [CHƯA CÓ: tên giảng viên], "Chương 5: Spark và Data Analytics," bài giảng học phần Nhập môn dữ liệu lớn, Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, 2026, 59 trang.
```

Phương án nếu người dùng quyết định không ghi tên người: dùng đơn vị làm tác giả, như mẫu "The Apache Software Foundation" đang có trong danh sách:

```
[@slide-c1]: Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn, "Chương 1: Giới thiệu dữ liệu lớn," bài giảng học phần Nhập môn dữ liệu lớn, 2026, 51 trang.
```

Ba mục còn lại làm tương tự với 53, 57 và 59 trang. Khi có tên giảng viên thì điền vào phương án đầu.

### E.2 MinIO

Đề xuất chính (đúng dòng mã nguồn mở mà đồ án chạy, xem `results/logs/environment.txt`: `RELEASE.2026-10-23T20-06-51Z`):

```
[@minio-docs]: MinIO, Inc., "MinIO Quickstart Guide," tệp README, kho minio/minio, GitHub. [Online]. Available: https://raw.githubusercontent.com/minio/minio/master/README.md (truy cập: 2026-11-08).
```

Tên "MinIO, Inc." lấy từ chân trang `www.min.io`; bản thân README không ghi tên này. Liên kết trỏ nhánh `master` nên nội dung có thể đổi.

Phương án trang chính thức của hãng (mô tả AIStor, sản phẩm khác với bản đồ án chạy):

```
[@minio-docs]: MinIO, Inc., "MinIO AIStor: The Enterprise AI Data Store." [Online]. Available: https://www.min.io/product/aistor (truy cập: 2026-11-08).
```

Câu trong báo cáo nên viết "tương thích S3" hoặc "tương thích API S3"; nguồn dùng "S3-compatible" và "S3 API Compatible", không dùng "giao thức S3".

Mục tuỳ chọn cho các nguồn ở mục D, nếu được dùng:

```
[@spark-parquet]: The Apache Software Foundation, "Parquet Files - Spark 4.0.0 Documentation." [Online]. Available: https://spark.apache.org/docs/4.0.0/sql-data-sources-parquet.html (truy cập: 2026-11-08).
[@spark-rdd]: The Apache Software Foundation, "RDD Programming Guide - Spark 4.0.0 Documentation." [Online]. Available: https://spark.apache.org/docs/4.0.0/rdd-programming-guide.html (truy cập: 2026-11-08).
[@spark-cloud]: The Apache Software Foundation, "Integration with Cloud Infrastructures - Spark 4.0.0 Documentation." [Online]. Available: https://spark.apache.org/docs/4.0.0/cloud-integration.html (truy cập: 2026-11-08).
[@hadoop-s3-third-party]: The Apache Software Foundation, "Working with Third-party S3 Stores." [Online]. Available: https://hadoop.apache.org/docs/r3.4.1/hadoop-aws/tools/hadoop-aws/third_party_stores.html (truy cập: 2026-11-08).
```

### E.3 Cách ghi số trang

Đề xuất ghi cả hai, mỗi nơi một việc:
- **Trong danh sách tài liệu:** tổng số trang của tệp PDF, vì một mục dùng cho nhiều chỗ trích. Với c1 ghi 51 (số trang thực của tệp), không ghi 56.
- **Trong thân bài:** trang của từng chỗ trích, vì đây là thứ giúp người đọc kiểm được.

Về cú pháp: `[@slide-c4, tr. 46]` **không khớp** biểu thức trích dẫn ở `report/build/build_docx.py:171-174` (chỉ nhận danh sách khoá). Suy luận từ mã, chưa chạy thử: chuỗi này sẽ không được đánh số. Vì vậy các đề xuất ở mục B dùng dạng `(slide chương 4, tr. 46 [@slide-c4])`, kết xuất thành "(slide chương 4, tr. 46 [3])" và không phải sửa script.
