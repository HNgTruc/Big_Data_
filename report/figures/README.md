# report/figures — hình vẽ riêng cho báo cáo

Hình minh hoạ vẽ bằng script, không phải kết quả đo. Biểu đồ số đo nằm ở `results/figures/`, ảnh chụp minh chứng nằm ở `results/logs/screenshots/`.

| File | Nội dung | Sinh bằng |
|---|---|---|
| `kien-truc.png` | Sơ đồ kiến trúc hệ thống (chương 4), 16 × 13,7 cm, 200 dpi | `report/build/draw_architecture.py` |

## Cách dùng

Không sửa ảnh bằng tay; sửa script rồi sinh lại (PowerShell, từ gốc repo):

```powershell
.\.venv-exp\Scripts\python.exe report\build\draw_architecture.py
```

Chèn vào Markdown theo quy ước ở `report/sections/README.md`. Sinh lại `bao-cao.docx` sau khi đổi ảnh.
