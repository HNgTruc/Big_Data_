# samples — mẫu dữ liệu trước/sau xử lý

Minh chứng cho mục 5.7 của đề ("dữ liệu trước/sau xử lý"): các file CSV nhỏ đặt dòng dữ liệu thô cạnh dòng tương ứng sau ETL.
**Toàn bộ là dữ liệu mô phỏng** do `src/data_generation/` sinh (seed cố định), không phải dữ liệu thật.

Sinh bằng job `src/etl/export_samples.py` (Spark): đọc `raw/<bộ>/`, `curated/<bộ>/`, `quarantine/<bộ>/` trên MinIO
(đầu ra của lần ETL chuẩn, không phải nhãn thí nghiệm), chỉ đọc, không ghi gì lên MinIO.

| Thư mục | Nội dung |
|---|---|
| `orders_5m/` | Mẫu của bộ `orders_5m`; ngày chạy, commit, lệnh ở [README](orders_5m/README.md) |

## Các file trong mỗi thư mục `<bộ>/`

Mẫu được chọn **xác định** (sắp theo khoá rồi lấy N dòng đầu, không ngẫu nhiên), nên chạy lại cho cùng nội dung.
Vì lấy khoá nhỏ nhất, mẫu chỉ để minh hoạ cách xử lý, không đại diện thống kê cho cả bộ.
N = `--rows-per-case` (mặc định 5), số dòng bảng tổng hợp = `--agg-rows` (mặc định 10).

| File | Trường hợp | Cột |
|---|---|---|
| `duplicates_orders.csv` | Bản ghi trùng: N khoá `order_id` nhỏ nhất xuất hiện > 1 lần trong thô và còn trong curated | `stage` (`raw`/`curated`) + cột của bảng; mỗi khoá: các dòng thô rồi đúng 1 dòng curated |
| `duplicates_order_items.csv` | Như trên với khoá (`order_id`, `line_no`) | như trên |
| `bad_dates_orders.csv` | Ngày sai định dạng được chuẩn hoá: N dòng cho mỗi định dạng `dd/MM/yyyy`, `yyyyMMdd`, `dd-MM-yyyy` | `order_id`, `raw_order_date`, `raw_format`, `curated_order_date` |
| `bad_times_web_events.csv` | Thời gian sai định dạng: N dòng cho mỗi định dạng `dd/MM/yyyy HH:mm:ss`, `yyyyMMddHHmmss` | `event_id`, `raw_event_time`, `raw_format`, `curated_event_time` |
| `bad_dates_customers.csv` | Ngày đăng ký sai định dạng (3 định dạng như `orders`) | `customer_id`, `raw_signup_date`, `raw_format`, `curated_signup_date` |
| `quarantine_orders.csv`, `quarantine_order_items.csv`, `quarantine_web_events.csv` | Bản ghi bị cách ly: N dòng nhỏ nhất theo khoá cho **mỗi** `reject_reason` có trong quarantine | `reject_reason` + cột thô |
| `missing_region_customers.csv` | Giá trị thiếu được xử lý không cách ly: `region` rỗng trong thô → `unknown` | `customer_id`, `raw_region`, `curated_region`, `raw_signup_date`, `curated_signup_date` |
| `agg_daily_revenue.csv`, `agg_revenue_by_region_category.csv`, `agg_events_daily.csv` | Dòng đầu của 3 bảng tổng hợp, sắp theo khoá (ngày; khu vực, danh mục; ngày, loại sự kiện) | cột của bảng tổng hợp |
| `summary.csv` | Số dòng thô / curated / quarantine của 5 bảng và số dòng 3 bảng tổng hợp | xem dưới |
| `quarantine_by_reason.csv` | Số dòng quarantine theo lý do | `table`, `reject_reason`, `rows`, `metrics_rows`, `matches_metrics` |

- Ô rỗng trong cột `raw_*` hoặc `customer_id`, `unit_price` của file quarantine nghĩa là giá trị thiếu (null) trong dữ liệu thô.
- Quy tắc làm sạch (lý do cách ly, thứ tự ưu tiên, định dạng ngày nhận diện) ở [docs/design/etl.md](../../docs/design/etl.md).
- Chỉ những lý do thực sự có dòng mới xuất hiện trong file quarantine. Với dữ liệu hiện tại không có dòng nào bị loại vì
  `invalid_order_date` hay `invalid_event_time` (mọi định dạng ngày chèn vào đều được nhận diện và chuẩn hoá).

### `summary.csv` và nguồn số liệu

- `raw_rows`, `curated_rows`, `quarantined_rows`: **đếm trực tiếp** bằng `count()` trong chính job này trên MinIO.
- `duplicates_removed` = `raw_rows` − `curated_rows` − `quarantined_rows` (cùng cách tính với `src/etl/pipeline.py`).
- `metrics_*`: đọc từ `results/metrics/<bộ>.json` (metrics của lần ETL đã ghi ra `curated/<bộ>/`).
- `matches_metrics`: `yes` khi mọi giá trị đếm được bằng metrics, `no` khi lệch, `no_metrics` khi không có file metrics.
  Job thoát với mã 3 nếu có dòng `no`. Dòng bảng tổng hợp chỉ có `curated_rows` (so với `aggregate_rows` trong metrics).

## Cách chạy lại

Trong thư mục `infra/`, cụm và MinIO đang chạy, dữ liệu thô và đầu ra ETL của bộ đã có trên MinIO:

```powershell
docker compose run --rm --no-deps --name sample-driver spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=sample-driver --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache --packages org.apache.hadoop:hadoop-aws:3.4.1 /opt/spark/work-dir/src/etl/export_samples.py --dataset orders_5m > ..\results\logs\export_samples_orders_5m.log 2>&1
```

Thành công khi log có `SAMPLES_OK ... mismatches=0`. Tham số khác: `--rows-per-case`, `--agg-rows`, `--out-dir`, `--metrics-file`, `--storage-root`.
Kiểm thử: `tests/test_export_samples.py` (chạy qua `tests/run_in_container.sh`).
