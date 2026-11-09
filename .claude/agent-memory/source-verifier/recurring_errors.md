---
name: recurring-errors
description: Loi hay gap khi kiem ban nhap bao cao (vong 1 ch.3-7 va vong 2 toan bo, 2026-11-08/09); kiem lai cac diem nay o lan sau
metadata:
  type: feedback
---

Cac loi da gap o ban nhap 1 (2026-11-08), nen soi lai o moi lan kiem:
- Ten slide lay tu docs/references/README.md thay vi ten that tren Drive (Ch5 sai ten).
- Khang dinh "pham vi" qua rong: "CV > 10% chi o hai nhom" dung cho processing_seconds_total cua ETL, sai neu tinh ca thoi gian truy van (c), (f).
- Lay so tu mot lan lap (r1) roi viet nhu dai dien (cache r2 khac r1/r3; so doc tu anh chup cung la r1).
- So lieu cu tu README trong khi results/ da co log moi (44 vs 68 passed).
- Gan nguon ngoai cho y ma nguon do khong noi (bex.co goi y dung quay.io, khong noi quay.io hong).
- Hanh vi mac dinh Spark 4.0 khac ban cu (worker.cleanup.enabled mac dinh true).
- Ten va dia danh tren bia khong co nguon trong repo; can nguoi dung xac nhan.

Them tu vong 2 (2026-11-09):
- Bang so gan nhu luon khop; loi nam o cau chu: "moi lan chay", "cho moi lan chay", "so dong bi loai" (gom ca no_clean_order), kiem tra cum khong ap dung cho Pandas.
- Chon moc thuan loi: "cham hon 12%" chi so voi nhom nhanh nhat, trong khi bao cao tu noi hai nhom la nhieu (so voi auto chi 6,8%).
- Nhan "Dung" o bang tong hop che ket qua bat loi khi gia thuyet qua rong (1 < S < 2).
- Cau trich WebFetch de mat ve han dinh ("except where this is explicitly stated").
- Huong dan tai lap viet tu README ma khong xet ban clone: tep da tren git lam lenh dung ngay (run_record.json lam run_all tra 2; manifest.json lam generate tra 1). Luon doc ma va doi chieu .gitignore, .git/index.
- README trong repo co the loi thoi so voi .gitignore (data/README.md noi chi giu README, thuc te giu ca manifest.json).

**Why:** cac loi nay khong lo ra khi chi so khop tung con so; phai doc cau chu va doi chieu pham vi.
**How to apply:** voi moi khang dinh "chi", "ca", "moi", kiem toan bo tap du lieu; voi moi trich dan ngoai, mo trang va doi chieu dung y duoc gan; voi moi lenh tai lap, doc ma xu ly tep da ton tai.

Lien quan: [[reference-sources]]
