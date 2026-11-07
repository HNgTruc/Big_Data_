---
name: export-samples-design
description: Design choices and pitfalls of src/etl/export_samples.py (before/after CSV evidence for section 5.7), incl. broadcast-in-outer-join gotcha and no pandas in the Spark image
metadata:
  type: project
---

`src/etl/export_samples.py` (added 2026-11-08) writes small before/after CSVs into `results/samples/<dataset>/`
from the standard ETL output (`curated/<dataset>/`, not experiment labels); read-only on MinIO.

- CSVs are written on the driver with Python `csv` from `collect()` of already-limited frames, NOT `toPandas()`:
  the `apache/spark:4.0.0-python3` image has no pandas (tests install it into /tmp/pylib only).
- Deterministic selection: sort by table key then limit, or `row_number()` per reason/format ordered by key.
- Outer join gotcha: Spark cannot broadcast the preserved side of an outer join (right join -> only left can be
  built), so a `broadcast()` hint on the small side of `big.join(small, how="right")` is ignored and `big` is
  shuffled. Pattern used: semi-join `big` against `broadcast(small keys)` first, then outer-join the two tiny frames.
- `summary.csv` = direct counts compared with `results/metrics/<dataset>.json`; exit code 3 on any mismatch.
- Run driver as `--name sample-driver` (a `spark-history` container runs on 18080 for the user; leave it alone).

Related: [[spark-cluster-config]]
