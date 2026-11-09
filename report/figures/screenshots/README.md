# report/figures/screenshots — ảnh chụp đã cắt khung cho báo cáo

13 ảnh dùng ở chương 7 và Phụ lục E, sinh từ ảnh gốc trong `results/logs/screenshots/`. Ảnh gốc mới là bằng chứng; thư mục này chỉ là bản trình bày.

Script `report/build/prepare_screenshots.py` chỉ làm ba việc: cắt bỏ khoảng trống và phần giao diện thừa, thêm viền xám 2 px, đặt bề rộng khi in. Sau khi ghi, script so từng pixel trong vùng cắt với ảnh gốc và dừng nếu có khác biệt. Tên tệp giống ảnh gốc.

Không sửa ảnh ở đây bằng tay. Muốn đổi vùng cắt hoặc bề rộng, sửa bảng `CROPS` trong script rồi sinh lại (PowerShell, từ gốc repo):

```powershell
.\.venv-exp\Scripts\python.exe report\build\prepare_screenshots.py
```

Vùng cắt không được làm mất số liệu mà báo cáo trích từ ảnh; danh sách các số đó ở `results/logs/screenshots/README.md`.
