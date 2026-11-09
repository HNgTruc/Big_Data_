# Chương 2. Cơ sở và công nghệ liên quan

Chương này chỉ trình bày những khái niệm đồ án thực sự dùng, lấy từ slide học phần và tài liệu chính thức; phần liên hệ với đồ án dẫn sang các mục sau. Phiên bản và vai trò từng công nghệ ở @tbl:cong-nghe.

## 2.1 Dữ liệu lớn và mô hình 5V

Slide xem dữ liệu là lớn khi công cụ truyền thống không còn xử lý hiệu quả được; dấu hiệu quan trọng là hệ thống phải đổi kiến trúc chứ không chỉ nâng cấp phần cứng (slide chương 1, tr. 10, 11 [@slide-c1]). Học phần dùng mô hình 5V gồm Volume (khối lượng), Velocity (tốc độ), Variety (đa dạng), Veracity (độ tin cậy) và Value (giá trị): bốn V đầu mô tả khó khăn, Value là lý do phải xử lý (slide chương 1, tr. 14 [@slide-c1]). Mục 3.6 nêu ba đặc trưng đồ án thể hiện. Value chỉ thể hiện gián tiếp: doanh thu tính trên dữ liệu thô cao hơn khoảng 9,6% so với dữ liệu sạch (mục 6.6), nên làm sạch tạo ra giá trị cho phân tích (nhận định của người viết).

## 2.2 Pipeline dữ liệu lớn

Pipeline đi từ nguồn, thu nhận, lưu trữ, xử lý, phân tích đến phục vụ và ra quyết định, kèm các lớp xuyên suốt như metadata và chất lượng dữ liệu. Pipeline có thể chạy theo lô, theo luồng hoặc kết hợp (slide chương 1, tr. 33 [@slide-c1]). Đồ án đảm nhận đoạn Storage → Processing, chạy theo lô.

## 2.3 Data Lake, object storage và HDFS

**Data Lake** lưu dữ liệu thô hoặc đã xử lý ở nhiều định dạng trên hạ tầng mở rộng được, nhưng có thể thành data swamp nếu thiếu metadata và quản trị (slide chương 1, tr. 31 [@slide-c1]). Dữ liệu có thể chia theo vùng raw, clean, curated (slide chương 4, tr. 47 [@slide-c4]); cách đồ án áp dụng ở mục 4.2.

**HDFS** là hệ thống file phân tán của Hadoop: file được chia thành block, nhân bản trên các DataNode, NameNode giữ metadata, và framework xử lý có thể tận dụng data locality (slide chương 4, tr. 19, 20 [@slide-c4]).

**Object storage** quản lý dữ liệu theo object key, metadata và API, không cung cấp ngữ nghĩa file POSIX, thường cập nhật theo cả object, và cần lưu ý độ trễ, chi phí request, hành vi rename và listing. S3, GCS, Azure Blob và MinIO thuộc nhóm này. Spark đọc được cả HDFS lẫn object storage, nhưng cơ chế tối ưu I/O khác nhau (slide chương 4, tr. 36, 37 [@slide-c4]). Tài liệu Spark lưu ý object store không thể xem là thay thế trực tiếp cho hệ file cụm như HDFS [@spark-cloud].

Cụm cổ điển đặt tính toán và lưu trữ cùng trên worker; mô hình đám mây có thể tách hai phần để mở rộng độc lập (slide chương 2, tr. 28 [@slide-c2]). Đồ án đi theo hướng tách, nhưng chỉ ở mức dịch vụ trên một máy (mục 4.1).

## 2.4 MinIO và S3A

MinIO là hệ lưu trữ đối tượng tương thích S3 [@minio-docs]. Spark truy cập MinIO qua S3A, connector trong module `hadoop-aws` của Hadoop [@hadoop-s3a]. S3A làm việc được với kho S3 của bên thứ ba nếu kho đáp ứng một số yêu cầu; trang tài liệu này không nêu tên MinIO [@hadoop-s3-third-party]. Đồ án cấu hình `fs.s3a.endpoint=http://minio:9000` và `fs.s3a.path.style.access=true` (`infra/README.md`).

## 2.5 Parquet

Parquet là định dạng file tổ chức dữ liệu theo cột. Truy vấn có thể chỉ đọc những cột cần dùng (column pruning), dữ liệu cùng kiểu nằm gần nhau nên thường nén tốt, và metadata giúp bỏ qua một phần dữ liệu trong nhiều trường hợp (slide chương 4, tr. 46 [@slide-c4]). Định dạng này còn hỗ trợ đẩy điều kiện lọc xuống (predicate pushdown) khi nguồn dữ liệu cho phép (slide chương 5, tr. 44, 48 [@slide-c5]). Thí nghiệm (c) đo lợi ích này (mục 6.6).

## 2.6 Kiến trúc và mô hình thực thi của Spark

Spark là engine xử lý dữ liệu phân tán theo partition (slide chương 5, tr. 8 [@slide-c5]). Kiến trúc có ba thành phần chính (slide chương 5, tr. 13, 17 [@slide-c5]):

- **Driver:** chạy chương trình chính, lập kế hoạch và điều phối task.
- **Executor:** chạy task, giữ dữ liệu cache và shuffle, báo trạng thái về driver.
- **Cluster manager:** phân bổ tài nguyên cho executor, có thể là Standalone, YARN hoặc Kubernetes; đồ án dùng Standalone.

"In-memory" không có nghĩa mọi dữ liệu luôn nằm trong RAM: Spark vẫn có I/O lưu trữ, shuffle và tràn đĩa (slide chương 5, tr. 6 [@slide-c5]). Điều này quan trọng vì executor của đồ án chỉ có heap 1 GB (mục 5.2).

**Lazy evaluation.** Transformation chỉ tạo kế hoạch; action như `count`, `collect` hoặc ghi file mới kích hoạt tính toán (slide chương 5, tr. 19, 30 [@slide-c5]). Vì vậy phép đo phải bao quanh action (nhận định của người viết; cách đo ở mục 6.2).

**DAG.** Spark biểu diễn phụ thuộc giữa các phép biến đổi thành đồ thị có hướng không chu trình. DAGScheduler dùng đồ thị này để chia job thành stage, mỗi stage gồm nhiều task; shuffle thường tạo ranh giới stage. Tối ưu truy vấn của DataFrame và SQL thuộc về Catalyst (slide chương 5, tr. 15, 26 [@slide-c5]).

**Partition.** Đây là đơn vị chia dữ liệu; mỗi task thường xử lý một partition. Quá ít thì không tận dụng hết cụm, quá nhiều thì tốn chi phí lập lịch (slide chương 5, tr. 16 [@slide-c5]). Job mặc định dùng 8 phân vùng shuffle (mục 4.5).

**Shuffle.** Đây là việc phân phối lại dữ liệu giữa các partition để phục vụ grouping, join hoặc repartition. Shuffle tạo I/O mạng giữa executor, có thể tràn ra đĩa cục bộ và dễ tạo straggler khi dữ liệu lệch (slide chương 5, tr. 29 [@slide-c5]).

## 2.7 Các kỹ thuật tối ưu được đánh giá

**Broadcast join.** Bảng nhỏ được gửi tới các executor để join cục bộ; bảng nhỏ vẫn đi qua mạng nhưng có thể tránh shuffle bảng lớn, và Spark SQL có thể tự chọn hoặc dùng hint (slide chương 5, tr. 51 [@slide-c5]). Thí nghiệm (d) so sánh với sort-merge join [@spark-sql-tuning] (mục 6.7).

**AQE (Adaptive Query Execution).** AQE dùng thống kê lúc chạy để gộp partition sau shuffle, đổi chiến lược join và hỗ trợ xử lý lệch (slide chương 5, tr. 48 [@slide-c5]); tính năng này bật mặc định từ Spark 3.2.0 [@spark-sql-tuning]. Điều kiện tách phân vùng lệch ở mục 4.6.

**Data skew.** Lệch dữ liệu xảy ra khi tần suất khoá không đều, tạo điểm nóng ngay cả khi dùng hash partitioning; join và groupBy đặc biệt nhạy (slide chương 2, tr. 18 [@slide-c2]). Biểu hiện điển hình là vài task chạy rất lâu trong khi stage gần xong (slide chương 5, tr. 50 [@slide-c5]). Thí nghiệm (e) đánh giá khái niệm này cùng AQE (mục 6.8).

**Cache.** Cache có lợi khi dataset được dùng lại. Dữ liệu chỉ được materialize ở action đầu tiên, các action sau có thể dùng lại thay vì chạy lại lineage; dữ liệu nằm trong bộ nhớ và/hoặc đĩa tuỳ storage level, và cache sai chỗ có thể làm chậm hơn (slide chương 5, tr. 31, 32 [@slide-c5]). Thí nghiệm (f) đo điểm hoà vốn (mục 6.9).

## 2.8 Speedup, efficiency và định luật Amdahl

Với T(N) là thời gian chạy trên N worker: speedup S(N) = T(1) / T(N), efficiency E(N) = S(N) / N. Efficiency giảm do phần tuần tự, lập lịch, truyền thông, đồng bộ, skew và các chi phí khác (slide chương 2, tr. 21 [@slide-c2]).

Định luật Amdahl cho giới hạn lý thuyết: S = 1 / ((1 − p) + p/N), và dù N tăng vô hạn, S không vượt 1 / (1 − p). Ở đây, thống nhất với mục 6.5, p là phần song song, N là số worker. Slide dùng ký hiệu khác: s là phần tuần tự (s = 1 − p), p là số node (slide chương 2, tr. 22 [@slide-c2]). Thí nghiệm (b) áp dụng các công thức này (mục 6.5).

<!-- VERIFY
- Các số trang slide: đối chiếu report/review/verify-slides.md mục C và văn bản slide. Đã đọc lại văn bản trích khi viết: c1 tr. 10, 11, 14, 31, 33; c2 tr. 18, 21, 22, 28; c4 tr. 19, 20, 36, 37, 46, 47; c5 tr. 6, 8, 13, 15, 16, 17, 19, 26, 29, 30, 31, 32, 44, 48, 50, 51.
- Không trích NIST (chú thích ở c1 tr. 14 không kèm tên tài liệu).
- spark-cloud: câu "cannot be used as a direct replacement for a cluster filesystem such as HDFS" (verify-slides mục D; WebFetch, nên mở trực tiếp để đối chiếu).
- hadoop-s3-third-party: "works well with third-party S3 stores if the following requirements are met", trang không nêu MinIO (verify-slides mục D).
- minio-docs: "S3-compatible object storage" (verify-slides mục D).
- spark-sql-tuning: AQE bật từ 3.2.0; có nêu sort-merge join (verify-slides mục D).
- `fs.s3a.endpoint`, `fs.s3a.path.style.access`: infra/README.md. `hadoop-aws`: [@hadoop-s3a], infra/README.md.
- Công thức viết lại khớp ví dụ slide: p = 0,8, N = 4 cho 1 / (0,2 + 0,2) = 2,5.
- 9,6%: mục 6.6, results/metrics/format_compare/runs.csv cột result.
- Heap 1 GB: mục 5.2. 8 phân vùng: mục 4.5.
- Câu về phép đo phải bao quanh action và về Value: nhận định của người viết.
-->
