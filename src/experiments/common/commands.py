"""Build the `docker compose run --rm ...` command lines (lists, no shell syntax).

Only `docker compose run --rm`, `stop`, `start` are ever built here: `docker compose exec`
crashed Docker Desktop on the lab machine (see infra/README.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import paths

ETL_SCRIPT = "src/etl/etl_job.py"
QUERY_BENCH_SCRIPT = "src/experiments/common/query_bench.py"
ETL_CONTAINER = "etl-driver"
BENCH_CONTAINER = "bench-driver"


@dataclass(frozen=True)
class SparkSubmitOptions:
    """Cluster-level options shared by every spark-submit of an experiment."""

    master_url: str = "spark://spark-master:7077"
    service: str = "spark-master"
    hadoop_aws_version: str = "3.4.1"
    ivy_cache: Path | None = None       # host dir mounted at /tmp/.ivy (None = download jars every run)
    event_log_dir: str | None = None    # container dir for Spark event logs (None = disabled)


def spark_submit(script: str, script_args: Sequence[str], container_name: str,
                 opts: SparkSubmitOptions) -> list[str]:
    """Return the full `docker compose run` command for one spark-submit.

    Input: repo-relative script path, its arguments, the driver container name.
    The driver container name doubles as `spark.driver.host` so executors can reach it.
    """
    cmd = ["docker", "compose", "run", "--rm", "--no-deps", "--name", container_name]
    if opts.ivy_cache is not None:
        cmd += ["-v", f"{opts.ivy_cache.resolve().as_posix()}:/tmp/.ivy"]
    cmd += [opts.service, "/opt/spark/bin/spark-submit",
            "--master", opts.master_url,
            "--conf", f"spark.driver.host={container_name}",
            "--conf", "spark.jars.ivy=/tmp/.ivy"]
    if opts.event_log_dir:
        # Spark 4 defaults to rolling, zstd-compressed logs; one plain JSON file is readable on the host
        # without extra packages (Python 3.12 has no zstd module).
        cmd += ["--conf", "spark.eventLog.enabled=true",
                "--conf", f"spark.eventLog.dir=file://{opts.event_log_dir}",
                "--conf", "spark.eventLog.compress=false",
                "--conf", "spark.eventLog.rolling.enabled=false"]
    cmd += ["--packages", f"org.apache.hadoop:hadoop-aws:{opts.hadoop_aws_version}",
            str(paths.CONTAINER_ROOT / script), *script_args]
    return cmd


def etl_args(dataset: str, label: str, metrics_dir_container: str, extra: Sequence[str] = ()) -> list[str]:
    """Arguments of src/etl/etl_job.py for one experiment run."""
    return ["--dataset", dataset, "--run-label", label, "--metrics-dir", metrics_dir_container, *extra]


def compose_service(action: str, service: str) -> list[str]:
    """`docker compose stop|start <service>` (used only for spark-worker-2 in scale_workers)."""
    if action not in ("stop", "start"):
        raise ValueError(f"unsupported compose action {action!r}")
    return ["docker", "compose", action, service]


def minio_remove(bucket: str, prefix: str) -> list[str]:
    """Delete `<bucket>/<prefix>` recursively with the shell-less mc image (minio-init service)."""
    if not prefix.strip("/") or ".." in prefix:
        raise ValueError(f"refusing to delete suspicious prefix {prefix!r}")
    return ["docker", "compose", "run", "--rm", "--no-deps", "minio-init",
            "rm", "--recursive", "--force", f"local/{bucket}/{prefix.strip('/')}"]


def container_exists(name: str) -> list[str]:
    """List containers (running or not) with exactly this name."""
    return ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"]


def to_display(cmd: Sequence[str]) -> str:
    """Human-readable command line (for logs and dry runs; not meant to be re-parsed)."""
    return " ".join(f'"{c}"' if (" " in c or not c) else c for c in cmd)
