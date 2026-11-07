---
name: spark-cluster-config
description: How Spark jobs are submitted and tested on this project's Docker cluster (run --rm only, ivy cache, Git Bash path conversion, local-mode tests in container)
metadata:
  type: project
---

- Submit from `infra/` with `docker compose run --rm --no-deps --name <x>-driver spark-master spark-submit
  --master spark://spark-master:7077 --conf spark.driver.host=<x>-driver
  --conf spark.jars.ivy=/opt/spark/work-dir/data/ivy_cache --packages org.apache.hadoop:hadoop-aws:3.4.1 ...`.
  Never `docker compose exec` (engine crash history, see infra/README.md); never stop containers unasked.
- Cluster: 2 workers x 2 cores, executor heap default 1g (Docker/WSL capped at 6 GB) — avoid caching multi-million
  row raw frames; re-reading is safer.
- Git Bash: set `MSYS_NO_PATHCONV=1` and use `$(pwd -W)` for -v host paths, otherwise `/opt/...` is rewritten.
- Spark tests run in local mode inside the image via `tests/run_in_container.sh` (local Spark fails on Windows);
  the run takes several minutes (pip install + three ETL setups).
- Slow network (2026-11-08: ~50 KB/s, pip ReadTimeout in the container): pre-download Linux cp310 wheels to the
  session scratchpad with `pip download --platform manylinux2014_x86_64 --python-version 3.10 --only-binary=:all:`
  (add `exceptiongroup tomli typing_extensions` explicitly: markers are evaluated for the host Python 3.12), then
  `docker compose run -e PIP_NO_INDEX=1 -e PIP_FIND_LINKS=/wheels -v <dir>:/wheels:ro ...` — script unchanged.
  Documented in tests/README.md.
- Spark job driver needs no pandas; collect tiny results and write with the `csv` module.

Related: [[export-samples-design]]
