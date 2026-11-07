---
name: experiments-design
description: Design decisions and verified Spark 4 facts behind src/experiments (runner, ivy cache, event logs, skew parameters, pipeline metrics)
metadata:
  type: project
---

Built and revised 2026-11-07 (code + tests; official runs belong to benchmark-analyst). User decisions: 3 reps per
config, no warm-up run discarded (an untimed warm-up ACTION inside query_bench is fine); cache only in query_bench;
1-worker runs via `docker compose stop/start spark-worker-2` with try/finally; pandas baseline only 500k and 1m;
(d) only auto/broadcast/shuffle_noauto; (e) 8 configs incl. a forced-shuffle variant; ivy cache on by default in
data/ivy_cache; executor memory stays at Spark default 1g (Docker crash history), src/etl only metrics may change.

Verified facts (2026-11-07):
- Spark 4.0 event logs default to rolling + zstd; runs pass `spark.eventLog.compress=false`,
  `spark.eventLog.rolling.enabled=false` -> single plain JSON file (checked on the cluster). Spark redacts
  `fs.s3a.secret.key`; MinIO password/user absent from event logs and run logs.
- `--conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache` works through the existing data/ bind mount; 2nd run
  "0 artifacts copied" (download 59 ms vs 56 s). Cache is ~1.1 GB.
- Skew: only product_id is skewed. With 8 partitions the hottest partition is 1.77x median (no AQE split possible);
  with 64 it is 10.5x and 9 hot partitions are 8-16 MB vs <=1.7 MB others (results/metrics/skew/partition_stats*).
  Chosen: 64 partitions, skewedPartitionThresholdInBytes=4 MiB, advisoryPartitionSizeInBytes=2 MiB; a test run of
  skew_shuffle_aqe produced 3 SortMergeJoin(skew=true) (items x products writes and region/category aggregate).
- `mc rm` on a missing prefix exits 0; always pass a trailing slash (labels share prefixes, e.g. *_aqe vs *_aqe_x).

**Why:** these explain choices a reviewer would otherwise question or "fix".
**How to apply:** keep these confs/flags; re-derive skew parameters with partition_stats.py if data size changes.
Related: [[local-windows-test-env]], [[order-items-key-dedupe]].
