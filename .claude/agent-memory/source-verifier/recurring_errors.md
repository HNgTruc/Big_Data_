---
name: recurring-errors
description: Loi hay gap khi kiem ban nhap bao cao (lan kiem 2026-11-08, ch.3-7); kiem lai cac diem nay o lan sau
metadata:
  type: feedback
---

Cac loi da gap o ban nhap 1 (2026-11-08), nen soi lai o moi lan kiem:
- Ten slide lay tu docs/references/README.md thay vi ten that tren Drive (Ch5 sai ten).
- Khang dinh "pham vi" qua rong: "CV > 10% chi o hai nhom" dung cho processing_seconds_total cua ETL, sai neu tinh ca thoi gian truy van (c), (f).
- Lay so tu mot lan lap (r1) roi viet nhu dai dien (cache r2 khac r1/r3).
- So lieu cu tu README trong khi results/ da co log moi (44 vs 68 passed).
- Gan nguon ngoai cho y ma nguon do khong noi (bex.co goi y dung quay.io, khong noi quay.io hong).
- Hanh vi mac dinh Spark 4.0 khac ban cu (worker.cleanup.enabled mac dinh true).
- Ten va dia danh tren bia khong co nguon trong repo; can nguoi dung xac nhan.

**Why:** cac loi nay khong lo ra khi chi so khop tung con so; phai doc cau chu va doi chieu pham vi.
**How to apply:** voi moi khang dinh "chi", "ca", "moi", kiem toan bo tap du lieu; voi moi trich dan ngoai, mo trang va doi chieu dung y duoc gan.

Lien quan: [[reference-sources]]
