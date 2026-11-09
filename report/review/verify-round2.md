# Kết quả source-verifier, vòng 2, toàn bộ báo cáo (2026-11-08 đến 2026-11-09)

**Trạng thái tệp: HOÀN TẤT.** Đối chiếu với `report/sections/` sau các dòng điều phối viên sửa ngày 2026-11-09 (lớp, giảng viên, tác giả slide, F:5, G:34).

Số mục: A 4, B 10, C 4, D 2, E 8, F 12, G 6, H 5.

Quy ước: "đã xem tận gốc" là đã đọc tệp nguồn hoặc mã; "suy luận" là kết luận của người kiểm. Ký hiệu `03:58` là `report/sections/03-...md`, dòng 58. Không sửa `report/sections/`.

## A. SAI (phải sửa)

### A1. 02:19, trích tài liệu Spark thiếu vế hạn định
- **Câu:** "Tài liệu Spark lưu ý object store không thể xem là thay thế trực tiếp cho hệ file cụm như HDFS [@spark-cloud]."
- **Vấn đề:** nguồn có thêm vế ngoại lệ, câu báo cáo tuyệt đối hơn nguồn. `verify-slides.md` mục D cũng chép thiếu vế này (qua WebFetch).
- **Nguồn (mở 2026-11-08):** https://spark.apache.org/docs/4.0.0/cloud-integration.html: "They cannot be used as a direct replacement for a cluster filesystem such as HDFS *except where this is explicitly stated*."
- **Thay bằng:** "Tài liệu Spark lưu ý object store không thể xem là thay thế trực tiếp cho hệ file cụm như HDFS, trừ khi được nêu rõ [@spark-cloud]."

### A2. 00-tom-tat:3, phạm vi "số dòng bị loại" quá rộng
- **Câu:** "Số dòng bị loại khớp số lỗi đã chèn."
- **Vấn đề:** ở `orders_5m`, tổng dòng bị loại là 1.686.763 (1.276.733 cách ly + 410.030 trùng), trong đó 376.230 dòng `no_clean_order` là hệ quả dây chuyền, không phải lỗi đã chèn. 04:83 và 06:53 đã nói đúng; tóm tắt không khớp hai chỗ đó.
- **Nguồn:** `results/samples/orders_5m/quarantine_by_reason.csv`; `results/metrics/datasets/datasets_summary.csv`.
- **Thay bằng:** "Số dòng trùng đã bỏ và các lý do cách ly trực tiếp khớp số lỗi đã chèn."
- **Áp dụng tương tự, nếu muốn thống nhất:** 03:12, 03:95, G:33 (cùng cụm "số dòng bị loại").

### A3. 06:32 và 04:124, "mọi lần chạy" đều qua kiểm tra cụm và số dòng thô
- **Câu:** 06:32 "mọi lần chạy đều qua kiểm tra trước khi chạy (số worker, số lõi, không có ứng dụng khác) và sau khi chạy (số worker không đổi, số dòng thô khớp manifest)". 04:124 "Trước mỗi lần chạy, bộ điều khiển kiểm tra cụm...".
- **Vấn đề:** 6 lần Pandas không có kiểm tra cụm: `workers_expected: null`, `cluster_before: null` (`results/metrics/pandas_baseline/runs/orders_1m/r1/run_record.json:47-48`; `src/experiments/common/runner.py:237-238`). Cờ `raw_rows_mismatch` chỉ xét `kind == "etl"` (`src/experiments/common/analysis.py:38`), nên không áp dụng cho (c), (f).
- **Thay 06:32 bằng:** "63 lần chạy Spark đều qua kiểm tra trước khi chạy (số worker, số lõi, không có ứng dụng khác) và sau khi chạy (số worker không đổi); các lần ETL còn được đối chiếu số dòng thô với manifest, các lần Pandas đối chiếu 49 số đếm."
- **Thay 04:124:** "Trước mỗi lần chạy Spark, ...".

### A4. 06:330, "khoảng 23 giây ... cho mỗi lần chạy"
- **Vấn đề:** 23,2–23,8 giây chỉ đúng ở (a). Tính từ `wall_seconds` − `processing_seconds_total` trong các `summary.csv`: (b) `w1` 23,0, `w2` 28,5; (d) 25,1–28,0; (e) 25,4–31,6.
- **Thay bằng:** "cộng thêm khoảng 23 đến 24 giây ngoài thời gian xử lý mỗi lần chạy ở (a), và đến khoảng 32 giây ở các thí nghiệm khác".

## B. Thiếu đánh dấu nhận định hoặc thiếu nguồn (gồm các điểm về trung thực)

### B1. 06:205, 06:321, 09:9, "chậm hơn khoảng 12%" chọn mốc thuận lợi nhất
- **Vấn đề:** chính 06:207 nói `auto` và `broadcast` khác nhau là do nhiễu, nhưng 12% chỉ so với `broadcast`, nhóm nhanh nhất. So với `auto`: 83,996/78,645 = 6,8%, và chênh lệch 5,35 giây nhỏ hơn độ lệch chuẩn của `auto` (6,63), tức chưa phân biệt được theo tiêu chí ở 06:33. Gộp `auto` và `broadcast` (trung bình 76,78): 9,4%.
- **Nguồn:** `results/metrics/join_strategy/summary.csv`; phép chia do người kiểm tính.
- **Thay 06:205 bằng:** "Ép sort-merge join cho mọi phép join làm job chậm hơn: 84,00 giây so với 74,92 giây của `broadcast` (khoảng 12%) và 78,65 giây của `auto` (khoảng 7%, trong mức nhiễu). Vì hai cấu hình đó có cùng số toán tử join, lấy trung bình chung thì chênh lệch khoảng 9% (tính từ summary)."
- **06:321, 09:9:** đổi thành "chậm hơn khoảng 7–12%" hoặc "khoảng 9%". Xem H4.

### B2. 06:91, 06:318, "thông lượng bắt đầu chững lại", "Đúng"
- **Vấn đề:** kết luận phụ thuộc lần r3. Thông lượng 5M: r1 289.581, r2 293.167, r3 238.549 dòng/s, so với 246.645 ở 2,5M (`results/metrics/scale_data/runs.csv`, `summary.csv`). Bỏ r3, tỉ lệ thời gian 2,5M lên 5M là 1,69 thay vì 1,82 (suy luận). CV của bộ 5M là 11,92%.
- **Thay vế cuối 06:91 bằng:** "từ 2,5M lên 5M, dữ liệu gấp đôi và thời gian gấp 1,82 lần, nhưng con số này phụ thuộc lần r3 chậm bất thường, nên chưa đủ căn cứ để khẳng định thông lượng đã bão hoà."
- **06:318, cột giả thuyết:** "Đúng về thời gian tăng chậm hơn dữ liệu; chưa xác nhận được bão hoà".

### B3. 06:240, 06:322, "Lợi ích chính của AQE đến từ việc gộp phân vùng"
- **Vấn đề:** đã đo là phần giảm tập trung ở `aggregates`, `dimensions`, và đúng cả ở bộ cân bằng. Không có số đo về số phân vùng sau gộp, nên cơ chế là suy luận. 06:240 có nhãn nhận định ở cuối đoạn, nhưng tiêu đề in đậm và ô bảng 06:322 viết như kết quả đo.
- **Thêm nữa:** chỉ đúng ở biến thể ép shuffle. Ở `auto`, bật AQE không nhanh hơn: 77,16 so với 75,36 và 84,07 so với 73,89 giây.
- **Thay 06:322 bằng:** "AQE tách lệch; ở biến thể ép shuffle, bật AQE nhanh hơn khoảng 13%, người viết cho là chủ yếu nhờ gộp phân vùng".
- **Thay tiêu đề 06:240 bằng:** "**Ở biến thể ép shuffle, phần lợi của AQE không đến từ xử lý lệch.**"

### B4. 06:207, 06:321, 06:332, "cùng kế hoạch"
- **Vấn đề:** `results/metrics/join_strategy/plan_check.csv` chỉ có số đếm toán tử (4 và 6 ở cả hai), không so sánh cây kế hoạch. Không kiểm được cặp bảng của từng join từ tệp này. Đọc được ở `src/experiments/common/eventlog.py:55-65`: chỉ đếm tên nút.
- **Thay bằng:** "có cùng số toán tử join (4 sort-merge, 6 broadcast), nên người viết suy luận gợi ý broadcast không đổi kế hoạch".

### B5. 06:241, "vì thế lệch khoá hầu như không ảnh hưởng"
- **Vấn đề:** câu nguyên nhân chưa đánh dấu nhận định, và cặp `auto` bật AQE lại có tỉ lệ cao nhất trong 4 cặp (1,09; 84,07 so với 77,16, chênh 6,9 giây, lớn hơn cả hai độ lệch chuẩn 2,85 và 5,35). 06:242 chỉ so AQE bật với tắt, chưa nói điểm này. Các giai đoạn không phụ thuộc khoá lệch cũng chậm hơn: `dimensions` 1,13, `orders` 1,13 (`results/metrics/skew/summary.csv`), nên có thể do nhiễu (suy luận).
- **Thay bằng:** "Đây là cấu hình thực tế của job. Tỉ lệ 1,09 ở cặp `auto` bật AQE là cao nhất trong 4 cặp, nhưng `dimensions` và `orders`, hai giai đoạn không phụ thuộc khoá lệch, cũng chậm hơn khoảng 13%, nên người viết cho rằng phần lớn là nhiễu; với n = 3 chưa kết luận được."

### B6. 08:7 và 06:239, số đọc từ ảnh là của một lần chạy
- **Vấn đề:** 15,5 MiB, 1,9 MiB, 0,5 s, 0,2 s đúng với ảnh (đã xem ảnh 09, 10), nhưng chỉ của lần r1: `app-...-0033` stage 19 và `app-...-0032` stage 32 (`results/logs/screenshots/README.md:46-47`). 08:7 viết như đặc trưng chung.
- **Thay 08:7 bằng:** "Ở lần chạy r1 (ảnh chụp), dữ liệu đọc lớn nhất của một task giảm từ 15,5 xuống 1,9 MiB. Nhưng task lâu nhất chỉ giảm từ 0,5 xuống 0,2 giây, và thời gian trung bình của `order_items` gần như không đổi (34,40 so với 34,85 giây)."

### B7. 04:14, "nhóm tự vẽ"
- **Vấn đề:** gán việc cho người mà không có bằng chứng. `report/figures/README.md:3` chỉ ghi "vẽ bằng script". Repo không ghi ai viết script.
- **Thay bằng:** "Nguồn: vẽ bằng script report/build/draw_architecture.py, theo infra/docker-compose.yml và src/etl/pipeline.py".

### B8. 00-tom-tat:3, "Nhóm thực hiện 7 thí nghiệm"
- **Vấn đề:** `src/experiments/README.md:3` ghi người chạy đo chính thức là agent `benchmark-analyst`; `dirty_paths` của 57 bản ghi cũng là tệp bộ nhớ của agent này. Các chương khác dùng "đồ án".
- **Thay bằng:** "Đồ án thực hiện 7 thí nghiệm, tổng cộng 69 lần chạy."

### B9. 06:308, 08:30, "Pandas dùng một lõi cho phần lớn thao tác"
- **Kết luận:** Đúng và có nguồn (`src/experiments/pandas_baseline/README.md:32`). Nhưng đây là mô tả trong README, không có số đo CPU; 06:308 chưa dẫn nguồn này trong câu.
- **Thêm vào cả hai chỗ:** "(theo `src/experiments/pandas_baseline/README.md`, không đo mức dùng CPU)".

### B10. 08:38, "Chênh lệch dưới khoảng 5 đến 10% chưa phân biệt được với nhiễu"
- **Vấn đề:** ở 06:335 ngưỡng này nằm trong danh sách nhận định; 08:38 viết như sự kiện. Xem thêm C2.
- **Thêm:** "(nhận định của người viết)".

## C. Không thống nhất giữa các chương

### C1. 01:28 và 08:3 so với 06:319, 06:324
- **Vấn đề:** 01:28 xếp "speedup thấp, Pandas nhanh hơn Spark ở bộ nhỏ" vào "kết quả không như mong đợi"; 08:3 cũng nói "điểm không như kỳ vọng". Nhưng 6.11 ghi cả hai là "Đúng" so với giả thuyết. Giả thuyết 1 < S < 2 lại rất rộng, nên chữ "Đúng" che mất việc E chỉ 0,64.
- **Thay 01:28 bằng:** "Ghi nhận trung thực các kết quả trái giả thuyết hoặc bất lợi cho Spark: lệch khoá không thành nút cổ chai, speedup thấp, Pandas nhanh hơn Spark ở bộ nhỏ."
- **Thay 06:319, cột giả thuyết:** "Đúng (1 < S < 2), nhưng S thấp, gần 1 hơn 2".

### C2. Hai tiêu chí nhiễu: 06:33 so với 06:335, 08:38
- **Vấn đề:** 06:33 dùng "nhỏ hơn khoảng một độ lệch chuẩn"; 06:335 và 08:38 dùng "dưới khoảng 5 đến 10%". Hai tiêu chí cho kết quả khác nhau: `skew_auto_aqe` so với `balanced_auto_aqe` chênh 9%, trong khoảng 5–10% nhưng lớn hơn một độ lệch chuẩn.
- **Đề xuất, sau câu 06:335:** "Tiêu chí này nới rộng hơn tiêu chí một độ lệch chuẩn ở mục 6.2; một chênh lệch chỉ được coi là rõ khi vượt cả hai."

### C3. 08:36 mất ngữ cảnh "trước các lần chạy"
- **Câu:** "RAM trống giảm từ 4.168 MiB xuống 351 MiB ... sau đó chủ yếu 0,8–1,1 GB, thấp nhất 400 MiB". Cùng câu vừa có 351 lại nói thấp nhất 400. 06:24 viết đúng vì giới hạn "trước các lần chạy Spark còn lại".
- **Thay bằng:** "... sau lần chạy đầu. Đo trước các lần chạy Spark còn lại, RAM trống chủ yếu 0,8–1,1 GB, thấp nhất 400 MiB (mục 6.1)."

### C4. 06:127, 08:22, "ba thí nghiệm" đo cùng cấu hình mặc định
- **Vấn đề:** (e) `balanced_auto_aqe` cũng là orders_5m, `auto`, AQE bật, 8 phân vùng, 2 worker, trung bình 77,16 giây (`results/metrics/skew/summary.csv`). Khoảng dao động không đổi.
- **Thay 06:127 bằng:** "bốn thí nghiệm cho trung bình 77,14 giây ((a)), 77,16 giây ((e), `balanced_auto_aqe`), 78,65 giây ((d), `auto`) và 82,21 giây ((b))". Thêm 77,16 vào 08:22.

## D. Tham chiếu hoặc số mục sai

### D1. F:19, "(mục 5.5)"
- **Vấn đề:** mục 5.5 không nói thư mục làm việc tăng theo số lần chạy trong một giờ; ý này ở `infra/README.md:80`.
- **Thay bằng:** "(`infra/README.md`; xem thêm mục 5.5)".

### D2. 08:37, "(@tbl:co-hop-le, Phụ lục B)"
- **Vấn đề:** bảng này không có dòng `dirty`; kết luận chỉ suy ra được do cờ này vắng mặt.
- **Thay bằng:** "Cờ này không có trong danh sách cờ loại trừ (mục B.2)."

## E. Phụ lục F: lệnh sai hoặc thiếu

### E1. F:97 và C.3 bước 5 (95-c:62), `run_all --group all` dừng ngay trên bản clone
- **Vấn đề (đã đọc mã, chưa chạy thử):** `results/metrics/*/runs/*/*/run_record.json` đã đưa lên git (`.git/index` có `results/metrics/scale_data/runs/orders_5m/r3/run_record.json`). `src/experiments/common/runner.py:191-196`: có bản ghi mà không có `--overwrite` hoặc `--resume` thì in thông báo và trả 2. `src/experiments/run_all.py:36-38`: trạng thái 2 làm dừng cả chuỗi. Thí nghiệm đầu tiên đã dừng, không chạy gì.
- **F:98 cũng cần lưu ý:** với bản clone, `--resume` bỏ qua mọi lần có `status` ok, tức không chạy gì (`runner.py:207-209`). `--group spark` cũng không gồm `pandas_baseline` (`src/experiments/common/registry.py:11-12`), nên nếu bộ chạy dừng giữa chừng, phải chạy thêm `--group host`.
- **Thêm sau khối lệnh F:96-98:** "Trên bản clone đã có sẵn 69 bản ghi của bộ đo chính thức, nên lệnh chạy thật phải thêm `--overwrite`: bản ghi và log cũ được đổi tên kèm thời điểm, không bị xoá. `--resume` chỉ dùng khi tiếp tục lần chạy của chính mình; `--group spark` không gồm Pandas, phần đó chạy bằng `--group host`."
- **C.3 bước 5:** thêm "(thêm `--overwrite` nếu `results/metrics/` đã có bản ghi)".

### E2. F:56-57 và C.3 bước 1 (95-c:48), bộ sinh từ chối chạy trên bản clone
- **Vấn đề (đã đọc mã, chưa chạy thử):** `data/raw/<bộ>/manifest.json` đã đưa lên git (`.gitignore:6` `!data/**/manifest.json`; `.git/index` có đủ 5 tệp). Vì vậy thư mục đầu ra không rỗng, và `src/data_generation/generate.py:128-130` ghi lỗi "pass --overwrite to replace it" rồi trả 1.
- **Thêm sau F:59:** "Bản clone đã có `manifest.json` trong `data/raw/<bộ>/`, nên phải thêm `--overwrite`, nếu không bộ sinh báo thư mục không rỗng và dừng. Lệnh này ghi lại `manifest.json`, trong đó `elapsed_seconds` sẽ khác."

### E3. F:159, "`data/raw/<bộ>/manifest.json` (không đưa lên git)" là SAI
- **Nguồn:** `.gitignore:5-6`; `.git/index`. Nguyên nhân có thể là `data/README.md:10` đã lỗi thời ("chỉ README được giữ").
- **Thay bằng:** "`data/raw/<bộ>/manifest.json` (có trên git; dữ liệu thô thì không)".

### E4. F:10, lấp `[CHƯA CÓ: lệnh áp dụng lại .wslconfig ...]`: ĐÃ XÁC NHẬN từ nguồn chính thức
- **Nguồn (mở 2026-11-08):** https://learn.microsoft.com/en-us/windows/wsl/wsl-config, tiêu đề "Advanced settings configuration in WSL", cập nhật 2026-10-16: "Keep in mind you may need to run `wsl --shutdown` to shut down the WSL 2 VM and then restart your WSL instance for these changes to take effect." và "it will shut down all running distributions, so use wisely."
- **Thay bằng:** "Sau khi sửa tệp, chạy `wsl --shutdown` rồi khởi động lại WSL để thay đổi có hiệu lực [@wsl-config]. Lệnh này tắt mọi bản phân phối WSL 2 đang chạy, nên cần dừng cụm trước (nhận định của người viết). Repo không ghi nhận lệnh này đã chạy trên máy thí nghiệm."
- **Thêm vào 90:**

```
[@wsl-config]: Microsoft, "Advanced settings configuration in WSL," Microsoft Learn, 16/10/2026. [Online]. Available: https://learn.microsoft.com/en-us/windows/wsl/wsl-config (truy cập: 2026-11-08).
```

- Việc phải mở lại Docker Desktop sau lệnh này tài liệu không nói, nên đề xuất không viết.

### E5. F:115, ý về `plan_check.csv`: ĐÚNG, cần nêu đủ tệp
- **Đã xem tận gốc:** `src/experiments/common/analysis.py`, hàm `plan_rows`, dòng 239-242 (`if not path.exists(): row["note"] = f"missing {path.name}"; continue`). `src/experiments/skew/analyze.py:43-44` và `src/experiments/join_strategy/analyze.py:31-32` ghi đè `plan_check.csv` vô điều kiện. `write_csv` dòng 201-206 lấy cột theo khoá thực có, nên tệp mới chỉ còn `config, rep, status, event_log, note`. Event log không lên git (`.gitignore:19`), còn `plan_check.csv` có trên git (`.git/index`).
- **Kết luận:** chắc chắn theo mã, ở cả (d) và (e). Chưa chạy thử. F:115 chỉ nêu `analysis.py`.
- **Thay câu F:115 bằng:** "Theo mã (`src/experiments/common/analysis.py`, hàm `plan_rows`; `analyze.py` của `join_strategy` và `skew`; chưa chạy thử), trên bản clone không có event log, `analyze_all` sẽ ghi đè `results/metrics/join_strategy/plan_check.csv` và `results/metrics/skew/plan_check.csv`: số toán tử mất, chỉ còn cột `note` ghi thiếu tệp. Khôi phục bằng `git checkout -- results/metrics/join_strategy/plan_check.csv results/metrics/skew/plan_check.csv`."

### E6. F:87, "Cần chạy cả năm bộ"
- **Vấn đề:** hai điều kiện được nêu không đòi hỏi cả năm bộ. `format_compare`, `cache` chỉ cần `curated/orders_5m/`; Pandas cần `results/metrics/orders_500k.json`, `orders_1m.json`, đã có trên git (`.git/index`). (e) đọc thô `orders_5m_skew` qua nhãn riêng.
- **Thay bằng:** "Trước bộ thí nghiệm, chỉ bắt buộc chạy ETL cho `orders_5m`, vì `format_compare` và `cache` cần `curated/orders_5m/`. Baseline Pandas đối chiếu `results/metrics/orders_500k.json`, `orders_1m.json`, đã có sẵn trong kho. Các bộ còn lại chạy để tái lập số đếm ở mục 6.3."

### E7. F:3, F:5, nói "từ máy trống" nhưng thiếu bước lấy mã
- **Thêm vào F.1 (hoặc ngay sau F:5):**

```powershell
git clone https://github.com/HNgTruc/Big_Data_.git
cd Big_Data_
```

### E8. F:123, History Server
- **Vấn đề:** event log không có trên bản clone (`results/logs/screenshots/README.md:21`), nên hướng dẫn chỉ dùng được trên máy đã đo hoặc sau khi chạy lại (d), (e).
- **Thêm:** "Cần có event log, chỉ có trên máy đã chạy (d), (e)."

## F. Cải thiện chính xác (tuỳ chọn)

1. **06:95, "trường hợp xấu nhất":** thực sự xấu nhất là lần chậm nhất 5M chia lần nhanh nhất 500k: 87,745/21,144 = 4,15. Thêm số này, hoặc đổi thành "kể cả khi lấy lần chậm nhất của bộ 5M".
2. **Tóm tắt, 06:237, 06:322, 08:7, 09:9, "trái giả thuyết":** giả thuyết (e) có ba vế (06:212). Vế `auto` chênh nhỏ không bị bác; vế ép shuffle bị bác. Đề xuất cho tóm tắt: "Trái giả thuyết ở biến thể ép shuffle, lệch khoá không làm job chậm rõ rệt (tỉ lệ 0,95–1,09 ở cả 4 cặp)".
3. **08:26, "bộ nhớ executor cũng tăng từ 1 lên 2 GB":** dễ hiểu nhầm với heap 1 GB mỗi executor. Viết "tổng heap executor" như 06:126.
4. **01:5, "hai nguồn dữ liệu tiêu biểu":** slide liệt kê sáu nhóm (c1 tr. 9). Viết "là hai trong các nguồn dữ liệu".
5. **02:39:** câu "Điều này quan trọng vì ..." là suy luận chưa đánh dấu.
6. **95-g:20, "chỉ đọc":** đúng theo cấu hình (`.claude/agents/source-verifier.md:4`), nhưng các vòng kiểm vẫn có tệp kết quả trong `report/review/`. Viết "không sửa báo cáo, chỉ báo cáo kết quả".
7. **95-g:28, "AI không tạo số đo":** bảng G.2 ghi `benchmark-analyst` "Chạy thí nghiệm, ghi số đo". Viết: "Số đo do job và bộ điều khiển sinh ra khi chạy thật; AI không tự điền số."
8. **F:19, dung lượng đĩa:** bỏ qua phần lớn nhất. Theo `infra/README.md:77`, 7 lần chạy chiếm 4,1 GB mỗi worker, và thư mục chỉ bị xoá sau 1 giờ. Bộ đo chạy 63 ứng dụng Spark trong khoảng 1 giờ 41 phút, nên đỉnh có thể tới vài chục GB (suy luận, chưa đo). Nên nêu là cần dự phòng.
9. **F:109, 8.5:** có thể ghi image id MinIO đã đo `sha256:a692590b...` (`results/logs/environment.txt:10`) để người tái lập đối chiếu, vì thẻ `latest` thay đổi được.
10. **06:168, 06:171:** tỉ lệ thời gian thô/Parquet cũng gộp hiệu ứng số dòng (thô nhiều hơn khoảng 8%); 06:169 mới nêu điều này cho dung lượng.
11. **F:96-99:** đang kích hoạt venv mới chạy được `python -m`; nên nhắc, vì F.2 đến F.5 chạy trong `infra`.
12. **07:106, 07:110, tên `products` trên ảnh 11:** phần ảnh đã cắt có `BroadcastHashJoin`, `HashAggregate` và spill 1312.3 MiB (đã xem), nhưng không hiện tên bảng. Việc đó là `products` suy từ `src/etl/cleaning.py:89` và `results/logs/screenshots/README.md:65`. Thêm vào dòng Nguồn: "tên bảng theo results/logs/screenshots/README.md (không hiện trên phần ảnh đã cắt)", như đã làm với ảnh 09, 10.

## G. Phần còn thiếu so với đề

1. **Bản PDF** (`rules/report-format.md:13`, đề mục 7): chưa thấy; bản hiện có là `report/bao-cao.docx`.
2. **Bảng phân công, đóng góp:** còn `[CHƯA CÓ]` (đã biết, do người dùng để trống).
3. **Phụ lục "API" (đề mục 6):** không có và không có câu giải thích. Đề xuất thêm vào Phụ lục C hoặc F: "Đồ án không cung cấp API dịch vụ; giao diện sử dụng là các tham số dòng lệnh ở mục C.3."
4. **Lý do chọn công nghệ (đề 5.5):** có cho Spark, MinIO (05:25, 05:27), Parquet (04:87). Thiếu cho Docker Compose và Pandas. Đề xuất viết sau khi nhóm xác nhận lý do; repo không ghi lý do chọn Docker Compose ngoài quyết định trong `.claude/CLAUDE.md`.
5. **"Vì sao cần Big Data" (đề 5.2):** còn mỏng, trong khi 3.6 nói quy mô khiêm tốn và 6.10 cho thấy Pandas nhanh hơn. `docs/design/schema.md:15` từng định chứng minh Volume bằng baseline Pandas, nhưng baseline chỉ chạy ở 500k và 1M nên không chứng minh được. Luận điểm có số: bộ nhớ đỉnh Pandas tăng gần tuyến tính, ngoại suy khoảng 8 GB ở 5M (chưa đo). Nên nêu rõ ở 1.1 hoặc 3.6 là ngoại suy.
6. **Độ dài khoảng 30 trang:** chưa kiểm được (mục cuối).

Đạt: chương 1–9, tóm tắt (khoảng 234 từ, đếm theo khoảng trắng, trong khoảng 150–250), tài liệu tham khảo; hướng dẫn chạy (F), cấu hình (C), schema (A), đường dẫn mã nguồn (F:5); sản phẩm tối thiểu: job phân tán, dữ liệu trước và sau (7.3), thống kê chất lượng (6.3), thời gian xử lý (6.4); các mục 5.1, 5.3, 5.4, 5.6, 5.7, 5.8.

## H. Cần người dùng quyết định

1. **"Nhận định của người viết" so với "của nhóm".** Cụm "người viết" xuất hiện dày, nhất là chương 6 và 8 (49 lần trong 11 tệp, gồm cả khối VERIFY và README). Đồ án có 4 thành viên, số ít ngầm chỉ một người; đề mục 8 đòi quyết định kỹ thuật quan trọng "phải có lập luận của nhóm". Đổi thành "của nhóm" chỉ đúng khi nhóm đã đọc và đồng ý các nhận định đó.
2. **"Thành phố Hồ Chí Minh" trên bìa** (00-bia:29): chưa có nguồn trong repo; VERIFY ghi chờ xác nhận.
3. **Giữ manifest trên git hay không:** giữ thì mọi lệnh sinh dữ liệu trên bản clone cần `--overwrite` (E2).
4. **Con số chính cho (d):** 12%, 7–12% hay khoảng 9% (B1); ảnh hưởng 06:321 và 09:9.
5. **Lý do chọn Docker Compose, Pandas** (G4): nhóm cung cấp.

## Đã kiểm đạt

### Số liệu (đã xem tận gốc)

Đã đối chiếu **khoảng 450 con số** với `results/`, không lấy mẫu mà lấy toàn bộ các bảng dưới đây. Tất cả khớp cả về làm tròn và đơn vị; những chỗ cần sửa chỉ là phạm vi hoặc diễn giải ở nhóm A, B, C.

| Nơi trong báo cáo | Số con số | Tệp gốc |
|---|---|---|
| `tbl:scale-tong`, D.1 | 52 | `scale_data/summary.csv`, `runs.csv` |
| `tbl:workers` | 30 | `scale_workers/summary.csv` |
| `tbl:format-thoi-gian`, `tbl:format-kich-thuoc`, `tbl:format-byte-dong` | 48 | `format_compare/summary.csv`, `sizes.csv`; `samples/orders_5m/summary.csv` |
| `tbl:join`, `tbl:join-ke-hoach` | 30 | `join_strategy/summary.csv`, `plan_check.csv` |
| `tbl:skew-cau-hinh`, `tbl:partition-stats` | 68 | `skew/summary.csv`, `plan_check.csv`, `partition_stats_summary.csv` |
| `tbl:cache-tong`, `tbl:cache-hoa-von`, `tbl:cache-truy-van`; bộ nhớ và đĩa r1–r3 | 36 | `cache/summary.csv`, `break_even.csv`, `runs/cache/r*/query_bench.json` |
| `tbl:pandas-spark`, `tbl:pandas-giai-doan` | 22 | `pandas_baseline/comparison_spark.csv`, `summary.csv`, `runs.csv` |
| `tbl:chat-luong-5m` | 32 | `samples/orders_5m/summary.csv`, `quarantine_by_reason.csv` |
| `tbl:kich-thuoc-tong`, `tbl:kich-thuoc-bo`, số lỗi ở 3.4 | 49 | `datasets/datasets_summary.csv` |
| Số trong câu chữ ở 6.1–6.11, 8 (CV, tỉ số, RAM, kết quả truy vấn) | khoảng 35 | `runs.csv`, `summary_by_order.csv`, `run_record.json` |
| Mẫu 7.3, E.3; trích log E.4 | khoảng 50 | `samples/orders_5m/*.csv`, các tệp log nêu trong E.4 |

Các phép tính lại đạt: 4,01 và 3,88; 1,82; 6,4; 22%; p ≈ 0,45; 1,37; 91,9%; 38,5%; 1,88; 3,2–5,7 lần; 9,6%; 13%; 31%; 1,95; 1,28; 104 = 64 − 9 + 49; 3,0 GB ở F.1; 1 giờ 41 phút. CV: bảy nhóm truy vấn và hai nhóm ETL đúng phạm vi đã nêu ở 6.2. 57/69 bản ghi có `"dirty": true`, và cả 57 có đúng hai đường dẫn trong `.claude/agent-memory/benchmark-analyst/` (grep nhiều dòng trên mọi `run_record.json`).

### Thống nhất giữa các chương (đạt)

3,52 (00, 06, 09); 1,29 và 0,64 (00, 06, 08, 09); 2,1–2,7 (00, 06, 09); 3,1 (00, 06, 09); 0,95–1,09 (00, 06, 08, 09); 6,1 và 4,0 (00, 06, 08, 09); 20.931.505, 19.244.742, 1.276.733, 410.030 (03, 06, 09); 69 (00, 01, 04, 06, 09); 9,6% (02, 06); 10,54 và 16,2 MB (03, 06, 08); 34,40 và 34,85 (06, 08); 77,14, 78,65, 82,21 (06, 08); 4.168 và 351 MiB (06, 08); 11,92% và 12,70% (06, 08); 41 và 69 passed (05, C, G).

### Sau khi chuyển bảng (đạt, trừ D1, D2)

- Toàn bộ tham chiếu "mục X.Y", "Phụ lục X", "chương N" ở chương 1–9 và phụ lục A–G đều trỏ đúng nội dung.
- Mọi nhãn `@fig:`, `@tbl:` đều có định nghĩa, nhãn duy nhất. Việc gộp `tbl:chat-luong-5m` không làm sai số; 06:52, 06:54, 09:18 vẫn trỏ đúng.
- Các câu "dưới đây" (06:328, 07:25, F:39) còn đúng; không còn câu "bảng trên", "bảng dưới đây" nào trỏ sai.
- Chương 7 có 6 ảnh, Phụ lục E có 7 ảnh, khớp `report/sections/README.md:17`.

### Slide (đã xem văn bản trích từng trang, không xem hình)

Mọi trích dẫn ở chương 1, 2, 3, 4, 5, 6, 8 và Phụ lục E đúng ý và đúng trang (ngoại lệ nhỏ: F4 ở nhóm F): c1 tr. 7, 9, 10, 11, 14, 26, 31, 33; c2 tr. 18, 21, 22, 28; c4 tr. 19, 20, 36, 37, 46, 47; c5 tr. 6, 8, 9, 13, 15, 16, 17, 19, 26, 29, 30, 31, 32, 42, 43, 44, 48, 50, 51. Công thức Amdahl đổi ký hiệu ở 2.8 và 6.5 đúng.

### Các ý mới được giao kiểm

- **8.2, (b) không ghi event log: ĐÚNG, đã xem tận gốc.** Cả 6 `results/metrics/scale_workers/runs/*/*/run_record.json` có `"event_logs": []`; `results/logs/scale_workers/` không có `eventlogs/`; `src/experiments/scale_workers/run.py:31-33` không bật `event_log`. Có thể dẫn nguồn này ở 08:24 thay cho `results/logs/README.md`.
- **8.2, bộ nhớ đẩy S lên: đã đánh dấu nhận định.** Không có số đo; `src/experiments/scale_workers/README.md:31` chỉ nói 1 worker "có thể tràn" nhiều hơn. Xem F3 về cách viết.
- **8.3, Pandas giữ bảng sạch trong bộ nhớ: ĐÚNG, có nguồn** (`src/experiments/pandas_baseline/README.md:21`). Một lõi: xem B9.
- **8.5, thẻ `latest`: ĐÚNG, có nguồn** (`infra/.env.example:5-6`, `results/logs/environment.txt:10`; bài Chainguard: "Pull the `cgr.dev/chainguard/minio:latest` image", phiên bản cụ thể dành cho khách hàng). "Chạy lại có thể nhận bản khác" đã đánh dấu nhận định.
- **F.7, `plan_check.csv`:** xem E5.
- **`wsl --shutdown`:** xem E4.

### Phụ lục F (đọc mã và README, không chạy)

F.1 venv, F.2, smoke, F.4 `mc`, F.5, F.6 (trừ E1), F.7 xuất mẫu, F.8 hai lệnh, F.9 khớp nguyên văn README; `--overwrite`, `--resume`, `--dry-run`, `--run-label`, thứ tự thí nghiệm, nhóm `spark`, `host`, `all` khớp mã (`src/experiments/common/cli.py`, `registry.py`, `src/etl/etl_job.py`). `--orders 1000000` và `2500000` cho đúng tên thư mục (`generate.py:42-45`). Dòng 2 của `results/logs/test_host.log` khớp F:136. `pytest` có trong `src/experiments/requirements.txt`; `test_build_docx.py` cần thêm `report/build/requirements.txt`, đúng như F:139.

### Tài liệu tham khảo

- 19 khoá trong 90 đều được trích; mọi khoá được trích đều có mục.
- **Đã mở lại ngày 2026-11-08, tiêu đề khớp:** `spark-cloud`, `hadoop-s3-third-party` (tiêu đề đầy đủ của trang có thêm tiền tố "Apache Hadoop Amazon Web Services support –", mục hiện dùng phần sau, chấp nhận được), `minio-docs` ("MinIO Quickstart Guide", "S3-compatible", "THIS REPOSITORY IS NO LONGER MAINTAINED."), `spark-sql-tuning`, `spark-cluster`, `hadoop-s3a`, `chainguard-minio`.
- **Đã mở lại ngày 2026-11-09, khớp:** `docker-767` (M-transferts, 21/10/2026, nêu `0xc00000fd`, kernel "6.18.54.1-1", "the exact cause has not been established"); `bex-minio` (Dora Noda, 25/09/2026, xoá khỏi Docker Hub 11–14/9, khuyên quay.io).
- **Ngày truy cập:** các mục ghi 2026-11-08; hai mục mở lại ngày 2026-11-09 vẫn còn nội dung, không cần đổi.

### Ảnh (đã xem trong vòng này)

01 (2 Alive, 4 lõi, 4.0 GiB, 68 Completed, 1024.0 MiB), 03 (6 object, `web_events.jsonl` 595.3 MiB), 07, 09, 10, 11, 12, 13 (609 và 637 task, 434.4 MiB, hai địa chỉ), và `report/figures/kien-truc.png` khớp mô tả ở 4.1. Ảnh 09 có Shuffle Write max 1059025, trùng `rows_max` trong `partition_stats_summary.csv`.

### Trung thực

- Kết quả trái giả thuyết của (e) được ghi rõ, không làm nhẹ, ở 00, 06, 08, 09; 10,18 giây được ghi là chưa giải thích được.
- Con số chưa đo được ghi là chưa đo: 8 GB ngoại suy, điểm giao nhau, ảnh hưởng của RAM.
- Không thấy câu viết như đã đo mà chưa đo, ngoài các điểm B3, B4, B5. Không thấy câu nói làm một mình, ngoài cách dùng "người viết" (H1).

## KHÔNG kiểm được, kèm lý do

- **Không chạy lệnh nào:** không có Bash, Docker. E1, E2, E5 và mọi lệnh ở F là kết luận từ đọc mã, chưa chạy thử.
- **Trạng thái git:** chỉ đọc `.git/index` trên máy này, không phải nội dung trên GitHub. Suy luận rằng bản clone cũng có các tệp đó nếu chúng đã được commit và push.
- **Độ dài khoảng 30 trang:** không có công cụ dựng PDF và đếm trang.
- **`data/ivy_cache/`:** `data/README.md:8` ghi khoảng 1 GB, `.gitignore:9` ghi khoảng 0,5 GB; không đo được dung lượng thư mục.
- **Hình trong slide:** chỉ đọc văn bản trích, chưa xem hình trên trang.
- **Mở lại ở vòng này chưa làm:** `spark-config`, `spark-ansi`, `spark-monitoring`, `spark-standalone`, `spark-tuning`, `pyspark-cache`; dựa vào kết quả vòng 1.
- **WebFetch:** các trang Spark, Hadoop, MinIO, GitHub, Chainguard, bex.co đọc qua công cụ tóm tắt, câu trích là do công cụ trả lại. Riêng trang Microsoft trả về toàn văn.
- **Hướng dẫn IEEE gốc:** chưa đối chiếu định dạng mục (như `verify-slides.md` mục D).
- **Các lần chạy `-0000` đến `-0004`:** ảnh 01 chỉ hiện hai dòng đầu; dựa vào vòng 1.
- **Metrics schema cũ ở commit `993d30b`:** không đọc được lịch sử git; 4.5 đối chiếu với `docs/design/etl.md`.
- **Log Docker Desktop lúc sập:** chỉ có mô tả trong `infra/README.md`, không có tệp log trong `results/`.
- **Phân bổ 13/29/15/12:** theo lưu ý của điều phối viên (pytest --co); log chỉ in tổng.
- **95-g:34, xác nhận của nhóm:** không có bản ghi trong repo, và câu đã ghi rõ điều đó. Không kiểm chứng được nội dung xác nhận.
- **Tác giả bốn mục slide, lớp, giảng viên:** thông tin người dùng cung cấp; slide không ghi tên người (`verify-slides.md` mục A), điều phối viên đã báo người dùng đây là giả định nên không kiểm thêm.
- **Ảnh 02, 04, 05, 06, 08:** không xem lại ở vòng này; vòng trước đã xem theo khối VERIFY.
