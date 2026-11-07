---
name: experiments-design
description: Design decisions and Spark 4 pitfalls behind src/experiments (runner, event logs, ivy download, cache/format bench, skew caveat)
metadata:
  type: project
---

Built 2026-11-07 (code + tests only; official runs belong to benchmark-analyst). User decisions: 3 reps per config, no
warm-up discarded; cache measured in a separate query script (no `--cache` in etl_job.py, src/etl must not change);
1-worker runs via `docker compose stop/start spark-worker-2` with try/finally; pandas baseline only on 500k and 1m.

Non-obvious facts found while building it:
- Spark 4.0 event logs default to rolling dir `eventlog_v2_<app>/` + zstd. Host Python 3.12 cannot read zstd, so
  runs pass `spark.eventLog.compress=false` and `spark.eventLog.rolling.enabled=false` (verified in local mode).
- Each spark-submit in a fresh `--rm` container re-downloads ~546 MB of `--packages` jars (smoke: 65 s of a 120 s
  wall clock for 500k, processing 28 s). `--ivy-cache` option exists but is untested and off by default.
- Smoke (500k, `--join-strategy shuffle`): merge hint survives AQE (SMJ in final plans) but unhinted joins stay BHJ,
  hence the extra `shuffle_noauto` config.
- Skew is on `product_id` only; in auto mode `products` is broadcast, so skew may barely touch shuffles. Told the user.
- Pandas baseline matched manifest + Spark metrics on 500k (49/49 checks).

**Why:** these explain choices a reviewer would otherwise question or "fix".
**How to apply:** keep event-log confs, keep record/archival behaviour; re-check smoke observations on 5m before
citing them. Related: [[local-windows-test-env]], [[order-items-key-dedupe]].
