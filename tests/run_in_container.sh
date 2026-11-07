#!/usr/bin/env bash
# Run the Spark-dependent tests (ETL, data generation, query bench) inside the Spark image (Linux), deps in /tmp only.
set -eo pipefail
python3 --version
python3 -m pip install -q --disable-pip-version-check --target /tmp/pylib \
  "numpy>=1.26" "pandas>=2.0" "pyarrow>=15" "pytest>=8"
PY4J=$(ls /opt/spark/python/lib/py4j-*.zip)
export PYTHONPATH=/tmp/pylib:/opt/spark/python:$PY4J
export PYSPARK_PYTHON=python3
cd /opt/spark/work-dir
python3 -c 'import numpy, pandas, pyarrow, pyspark; print("versions numpy", numpy.__version__, "pandas", pandas.__version__, "pyarrow", pyarrow.__version__, "pyspark", pyspark.__version__)'
python3 -m pytest -q -p no:cacheprovider tests/test_etl.py tests/test_data_generation.py tests/test_query_bench.py
