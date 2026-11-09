# report/figures — hình vẽ riêng cho báo cáo

Hình dùng riêng cho báo cáo, sinh bằng script. Biểu đồ số đo nằm ở `results/figures/`, ảnh chụp gốc nằm ở `results/logs/screenshots/`.

| File hoặc thư mục | Nội dung | Sinh bằng |
|---|---|---|
| `kien-truc.png` | Sơ đồ kiến trúc hệ thống (chương 4), 16 × 13,7 cm, 200 dpi | `report/build/draw_architecture.py` |
| `ke-hoach-so-sanh.png` | So sánh ba kế hoạch đã chạy của bước ghi `order_items` sạch (mục 7.4), 16 × 13,5 cm, 200 dpi; cấu trúc theo `results/logs/skew/plan_query4.txt`, số liệu theo ảnh chụp 07, 09, 10, 11 | `report/build/draw_plan_comparison.py` |
| [`screenshots/`](screenshots/README.md) | Bản cắt khung và thêm viền của 13 ảnh chụp minh chứng | `report/build/prepare_screenshots.py` |

## Cách dùng

Không sửa ảnh bằng tay; sửa script rồi sinh lại (PowerShell, từ gốc repo):

```powershell
.\.venv-exp\Scripts\python.exe report\build\draw_architecture.py
.\.venv-exp\Scripts\python.exe report\build\draw_plan_comparison.py
.\.venv-exp\Scripts\python.exe report\build\prepare_screenshots.py
```

Chèn vào Markdown theo quy ước ở `report/sections/README.md`. Sinh lại `bao-cao.docx` sau khi đổi ảnh.
