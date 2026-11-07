---
name: review-experiments-2026-11-07
description: First review of src/experiments (commit 1db60b0) before official benchmarks; open findings to re-check next time and agreed constraints
metadata:
  type: project
---

Reviewed 2026-11-07 (commit 1db60b0): src/experiments/*, light pass on src/etl, src/data_generation, tests.
36/36 host tests passed; dry-run printed 57 commands; no blocker found.

Open findings handed to the author (re-check on next review):
- ETL reuses label `<exp>_<config>` across reps; `mode("overwrite")` deletes the previous rep's output INSIDE the timed stages, so r1 differs from r2/r3.
- `wall_seconds - processing_seconds_total` also contains the post-processing stats step (re-reads raw), not only startup.
- Executors run with Spark default 1 GB heap (no executor-memory set) although docs say "2 GB per worker".
- Skew design: 10 hot products hashed into 8 shuffle partitions gives at most ~2x partition imbalance; AQE skew split (factor 5, 256 MB) cannot trigger; in auto mode products is broadcast anyway.
- Analysis does not check run homogeneity (git commit, options), cluster_after worker count, or pandas `all_match`.
- query_bench (Spark job) has no automated test; first measured query pays JVM/codegen warm-up (format q1 raw, cache nocache q1).

**Why:** user decisions recorded by spark-etl-engineer: 3 reps, no warm-up discarded; cache only in query_bench; skew uses auto join; never `docker compose exec`.
**How to apply:** do not ask to change these decisions silently; flag their consequences. Verify the items above were fixed or documented before signing off official runs. Related: [[recurring-issues]].
