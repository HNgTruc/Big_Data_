---
name: reference-sources
description: Nguon da kiem chung duoc cho do an (Drive slide, tai lieu Spark 4.0.0, file results/ chinh) va cach truy cap; dung khi kiem bao cao
metadata:
  type: reference
---

**Google Drive (cong khai, doc duoc danh sach):** dung `https://drive.google.com/embeddedfolderview?id=<folderId>` qua WebFetch de liet ke file kem link.
- Thu muc goc "Du lieu lon - SV": 1C1XIeoK9iBAX2bO2sCNdRCTyi_r5Pyx_; `Slide`: 1s_PLDPpeubudh97-ONYB9_FdL_eDZHXy; `Tai lieu`: 1uP1ljlMSax-5OJScX_G0LpBv1xH6ErdB.
- Ten file slide (2026-11-08): Ch1 "Gioi thieu du lieu lon", Ch2 "Tinh toan song song va phan tan", Ch3 "Lap trinh MapReduce", Ch4 "He thong luu tru", **Ch5 "Spark va Data Analytics"** (khong phai "Apache Spark"), Ch6 "Streaming va xu ly du lieu luong", Ch7 "Clustering va Classification", Ch8 "Graph Computing".
- NOI DUNG slide KHONG doc duoc: PDF > 10 MB vuot gioi han WebFetch; ban tai ve luu .bin, Read khong mo duoc; De cuong la anh scan. Ghi "khong truy cap duoc", dung doan.

**Tai lieu Spark 4.0.0 (da mo, trich duoc):** configuration.html (executor.memory 1g, memory.fraction 0.6, ansi.enabled true), sql-performance-tuning.html (skew factor 5.0, threshold 256MB, phai vuot CA HAI; advisory 64MB; autoBroadcast 10MB), sql-ref-ansi-compliance.html, spark-standalone.html (**worker.cleanup.enabled mac dinh true**, interval 1800 s, appDataTtl 7 ngay; SPARK_DAEMON_MEMORY 1g), monitoring.html, tuning.html (M = (heap-300MiB) x 0.6 -> 434.4 MiB voi heap 1 GiB), web-ui.html (khong giai thich "skipped"), PySpark DataFrame.cache (MEMORY_AND_DISK_DESER; trang dai, can offset 200000).

**Nguon so lieu trong repo:** results/metrics/datasets/datasets_summary.csv (kich thuoc + loi chen tung bo), results/logs/environment.txt (CPU i5-14400F 10 nhan/16 luong, MinIO RELEASE.2026-10-23T20-06-51Z), results/logs/test_host.log (68 passed). App ID Spark chinh thuc lien tuc ...-0005 den ...-0067 (63 ung dung).

Lien quan: [[recurring-errors]]
