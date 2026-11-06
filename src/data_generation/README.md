# data_generation — sinh dữ liệu mô phỏng

Script sinh dữ liệu thương mại điện tử ra `data/raw/`. Agent phụ trách: `data-generator`.

## Chạy (từ thư mục gốc repo)

```bash
pip install -r src/data_generation/requirements.txt
python -m src.data_generation.generate --orders 500000          # -> data/raw/orders_500k
python -m src.data_generation.generate --orders 5000000 --skew  # -> data/raw/orders_5m_skew
python -m src.data_generation.generate --help
```

## Đặc điểm

- Dữ liệu là **mô phỏng** (phân phối do nhóm tự chọn, không phải dữ liệu thật).
- Kết quả là hàm của `Config` (`seed`, `chunk_size`, ...): cùng tham số → cùng byte. Đổi `chunk_size` sẽ đổi dữ liệu.
- Schema 5 bảng: xem [docs/design/schema.md](../../docs/design/schema.md).
- Dữ liệu bẩn: mỗi loại lỗi ~2% số dòng (`--dirty-rate`), các loại lỗi không chồng lên cùng một dòng. Dòng trùng được **thêm vào**, nên `--orders 500000` ghi ra ~510.000 dòng `orders`.
- `manifest.json` trong thư mục đầu ra ghi tham số, phiên bản thư viện, số dòng, số lỗi đã chèn từng loại, kích thước file và thời gian sinh.
- Kích thước mặc định: `customers = orders/10`, `products = max(100, orders/250)`, `web_events = orders`.
- `--skew`: `--hot-share` (mặc định 0.5) số lượt chọn sản phẩm dồn vào `--hot-products` (mặc định 10) sản phẩm đầu.

## Cấu trúc

| File | Vai trò |
|---|---|
| `config.py` | hằng số (giá trị liệt kê, ngày) và `Config` |
| `tables.py` | dựng từng chunk dữ liệu sạch |
| `dirty.py` | chèn lỗi có kiểm soát, trả về số lỗi đã chèn |
| `writer.py` | ghi CSV / JSON lines / Parquet theo chunk |
| `generate.py` | CLI và `generate()` |

## Đã kiểm chứng

- `tests/test_data_generation.py`: 11 test qua trên VM (Python 3.10, pandas 2.3.3, pyarrow 25.0.1).
- Chạy thử 500.000 đơn: ~5 giây, đỉnh RAM ~0,9 GB, ~99 MB (VM, không phải máy người dùng). Các mốc 1M/2.5M/5M chưa chạy.
