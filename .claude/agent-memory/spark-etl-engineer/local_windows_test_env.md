---
name: local-windows-test-env
description: Running tests/test_etl.py on the user's Windows host - what works and what fails (pyspark 4.0.0, JDK 17, no winutils)
metadata:
  type: project
---

As of 2026-11-07 the repo `.venv` (Python 3.12.10) has pyspark 4.0.0 (matches the cluster image apache/spark:4.0.0-python3);
JAVA_HOME = Microsoft JDK 17. Two local blockers, both environmental, not code bugs:
1. Spark's Python worker crashes ("Python worker exited unexpectedly (crashed)", EOFException, no Python traceback even
   with faulthandler on) for ANY task that needs it: `createDataFrame` from Python rows, RDD `map`. Root cause not found.
2. Parquet writes fail: "HADOOP_HOME and hadoop.home.dir are unset" (no winutils.exe).

**Why:** this is why EtlPipelineTest and the DateParsingTest cases using createDataFrame fail locally.

**How to apply:** for unit tests that must run on this host, build inputs JVM-side (`spark.range`, SQL `VALUES` + cast
to the schema) and only `collect()` results; this works (CleanItemsTest passes). The full pipeline test needs either
winutils + a fix for the worker crash, or running pytest inside a Linux container. Ask before installing winutils or
running containers.
