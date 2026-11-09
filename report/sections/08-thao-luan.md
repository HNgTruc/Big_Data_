# Chương 8. Thảo luận

Chương này diễn giải kết quả ở chương 6, tập trung vào các kết quả trái giả thuyết hoặc bất lợi cho Spark và giới hạn của phép đo. Phần không có số đo trực tiếp được ghi là nhận định của nhóm.

## 8.1 Lệch khoá không thành nút cổ chai

Thí nghiệm (e) trái giả thuyết ở biến thể ép shuffle: tỉ lệ lệch/cân bằng là 0,95–1,09 ở cả 4 cặp, kể cả khi ép shuffle và tắt AQE, nên ở quy mô này lệch khoá không thành nút cổ chai (mục 6.8). AQE vẫn tách join lệch. Ở lần chạy r1 (ảnh chụp), dữ liệu đọc lớn nhất của một task giảm từ 15,5 xuống 1,9 MiB. Nhưng task lâu nhất chỉ giảm từ 0,5 xuống 0,2 giây, và thời gian trung bình của `order_items` gần như không đổi (34,40 so với 34,85 giây).

Nhận định của nhóm: giả thuyết coi tỉ lệ lệch là đủ để gây chậm, trong khi kích thước tuyệt đối mới quyết định. Phân vùng lớn nhất gấp 10,54 lần trung vị nhưng chỉ 16,2 MB, nên không xuất hiện cảnh vài task chạy rất lâu (slide chương 5, tr. 50 [@slide-c5]). Ở cấu hình `auto`, `products` còn được broadcast nên khoá lệch không đi qua shuffle. Biến thể ép shuffle được chỉnh chủ động để AQE kích hoạt (mục 4.6), nên thí nghiệm xác nhận cơ chế chứ không chứng minh lợi ích. Kết luận chỉ đúng ở quy mô đã đo; khoản 10,18 giây giữa `skew_auto_aqe` và `skew_auto_noaqe` vẫn chưa giải thích được.

## 8.2 Speedup chỉ đạt 1,29

Đã đo: S = 1,29, E = 0,64, tức gấp đôi tài nguyên chỉ giảm khoảng 22% thời gian (mục 6.5). Nguyên nhân thì chưa được đo trực tiếp; @tbl:speedup-bang-chung tách hai phần này.

Bảng: Nguyên nhân có thể của speedup thấp {#tbl:speedup-bang-chung}

| Nguyên nhân có thể | Đã đo hoặc ghi nhận | Còn là suy đoán |
|---|---|---|
| Chi phí không giảm khi thêm worker | p ≈ 0,45 ước lượng từ S | Tỉ trọng của lập lịch, metadata |
| Tranh chấp trên một máy | Hai worker cùng CPU, cùng ổ với MinIO | Mức tranh chấp (không đo CPU, I/O) |
| Phối hợp khi dữ liệu nhỏ | `dimensions` có S = 0,81 | Cơ chế ((b) không ghi event log) |
| Nhiễu giữa các đợt | 2 worker: 77,14, 77,16, 78,65, 82,21 giây | Nguyên nhân chênh lệch |

Nguồn: mục 3.8, 6.5; results/metrics/scale_workers/summary.csv; `results/metrics/scale_workers/runs/*/*/run_record.json` (`event_logs` rỗng). Cột cuối là nhận định của nhóm

Từ 1 lên 2 worker, tổng heap executor cũng tăng từ 1 lên 2 GB. Theo nhận định của nhóm, hiệu ứng này có xu hướng làm S cao lên, nên speedup thuần theo lõi có thể còn thấp hơn; đồ án chưa tách được hai hiệu ứng.

## 8.3 Pandas nhanh hơn Spark ở bộ nhỏ

Pandas nhanh hơn 6,1 lần ở bộ 500k và 4,0 lần ở bộ 1M (mục 6.10), phù hợp với lưu ý về workload nhỏ (slide chương 5, tr. 9 [@slide-c5]). Đây không phải so sánh tuyệt đối vì môi trường khác nhau: Pandas chạy trên host, đọc đĩa cục bộ, giữ bảng sạch trong bộ nhớ; Spark chạy trong Docker, đọc MinIO qua mạng, ghi rồi đọc lại Parquet giữa các giai đoạn. Ngược lại, Spark dùng 4 lõi executor, Pandas dùng một lõi cho phần lớn thao tác (theo `src/experiments/pandas_baseline/README.md`, không đo mức dùng CPU).

Khi dữ liệu gấp đôi, Pandas tăng 1,95 lần còn Spark 1,28 lần, nhưng điểm giao nhau chưa có số đo. Nhận định của nhóm: dữ liệu vừa bộ nhớ một máy thì Pandas là lựa chọn hợp lý.

## 8.4 Độ tin cậy của số đo

- **RAM host sát.** RAM trống giảm từ 4.168 MiB xuống 351 MiB (97% sử dụng) sau lần chạy đầu. Đo trước các lần chạy Spark còn lại, RAM trống chủ yếu 0,8–1,1 GB, thấp nhất 400 MiB (mục 6.1). Ảnh hưởng lên thời gian chưa được đo.
- **Cờ dirty.** 57/69 bản ghi có cờ này, nhưng `dirty_paths` chỉ gồm hai tệp bộ nhớ của agent đo; `src/` và `tests/` không đổi giữa các lần đó (`results/metrics/*/runs/*/*/run_record.json`, mục 6.1). Cờ này không có trong danh sách cờ loại trừ (mục B.2).
- **Dao động.** Mỗi cấu hình chỉ lặp 3 lần. `orders_5m` có CV 11,92%, `balanced_shuffle_noaqe` có CV 12,70% (mục 6.2). Chênh lệch dưới khoảng 5 đến 10% chưa phân biệt được với nhiễu (mục 6.11; nhận định của nhóm).

## 8.5 Hạn chế

- **Dữ liệu mô phỏng.** Phân phối và loại lỗi do đồ án tự chọn. Số đếm khớp chứng minh job đúng với các lỗi đã biết, không chứng minh xử lý được mọi lỗi thực tế (nhận định của nhóm).
- **Một máy vật lý.** Hai worker tranh chấp tài nguyên; việc tách lưu trữ chỉ ở mức dịch vụ. MinIO và Spark dùng chung một ổ đĩa vật lý (mục 3.8).
- **Heap 1 GB.** Có spill ở bước bỏ trùng (mục 7.4) và cache tràn một phần ra đĩa (mục 6.9); mức bộ nhớ khác chưa được thử.
- **Nguồn MinIO.** README kho `minio/minio` ghi đã ngừng bảo trì [@minio-docs]. Đồ án dùng image Chainguard với thẻ `latest` (mục 5.1), nên chạy lại sau này có thể nhận phiên bản khác (nhận định của nhóm); image id đã đo ghi ở `results/logs/environment.txt` để đối chiếu (mục F.2).

## 8.6 Hướng phát triển

- Chạy trên nhiều máy thật với nhiều mức worker, giữ cố định bộ nhớ để tách hiệu ứng lõi.
- Ghi event log, số liệu CPU, I/O, spill cho (b); đọc event log để giải thích chênh lệch ở `auto` của (e).
- Tăng số lần lặp, chạy xen kẽ `w1` và `w2`.
- Tăng mức lệch hoặc giảm bộ nhớ executor để tìm điểm skew thành nút cổ chai.
- Chạy Pandas trên bộ lớn hơn; so sánh MinIO với HDFS.

<!-- VERIFY
- Mọi số ở 8.1: mục 6.8; results/metrics/skew/summary.csv, plan_check.csv, partition_stats_summary.csv; ảnh 09, 10 trong results/logs/screenshots/.
- Số 15,5, 1,9 MiB, 0,5, 0,2 giây là của lần r1 (verify-round2 B6). Trái giả thuyết ở biến thể ép shuffle (verify-round2 F2).
- 8.2: results/metrics/scale_workers/summary.csv (1,29; 0,64; 0,81); 22%, p ≈ 0,45, 77,14 / 77,16 / 78,65 / 82,21: mục 6.5.
- (b) không ghi event log: 6 run_record.json của scale_workers có "event_logs": []; src/experiments/scale_workers/run.py không bật event_log (verify-round2, đã xem tận gốc).
- "Hiệu ứng bộ nhớ đẩy S lên": nhận định mới của người viết, mở rộng từ ý ở mục 6.5, không có số đo.
- 8.3: 6,1 và 4,0, 1,95 và 1,28: mục 6.10. Khác biệt môi trường và "giữ bảng sạch trong bộ nhớ": src/experiments/pandas_baseline/README.md. Ghi rồi đọc lại Parquet: mục 4.3.
- 8.4: 4.168, 351, 97%, 0,8–1,1 GB, 400 MiB: mục 6.1. 57/69: đã grep 57 run_record.json có "dirty": true, và cả 57 có dirty_paths đúng hai tệp .claude/agent-memory/benchmark-analyst/MEMORY.md, env_limits.md. CV 11,92% và 12,70%: mục 6.2.
- 8.5: spill: ảnh 11, mục 7.4; cache: mục 6.9; "THIS REPOSITORY IS NO LONGER MAINTAINED": verify-slides mục D, README kho minio/minio. MinIO image `latest`: infra/.env.example. Phiên bản đã đo: results/logs/environment.txt.
-->
