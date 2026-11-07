"""Build the `docker compose ...` command lines (lists, no shell syntax).

Only `docker compose run --rm`, `stop`, `start` are ever built here: `docker compose exec`
crashed Docker Desktop on the lab machine (see infra/README.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from . import paths

ETL_SCRIPT = "src/etl/etl_job.py"
QUERY_BENCH_SCRIPT = "src/experiments/common/query_bench.py"
ETL_CONTAINER = "etl-driver"
BENCH_CONTAINER = "bench-driver"
# data/ is bind-mounted read-write, so an Ivy cache there survives the `--rm` driver containers.
IVY_CACHE_HOST = paths.REPO_ROOT / "data" / "ivy_cache"
IVY_CACHE_CONTAINER = str(paths.CONTAINER_ROOT / "data" / "ivy_cache")
IVY_EPHEMERAL = "/tmp/.ivy"


@dataclass(frozen=True)
class SparkSubmitOptions:
    """Cluster-level options shared by every spark-submit of an experiment."""

    master_url: str = "spark://spark-master:7077"
    service: str = "spark-master"
    hadoop_aws_version: str = "3.4.1"
    ivy_dir: str = IVY_CACHE_CONTAINER    # IVY_EPHEMERAL = download the --packages jars on every run
    event_log_dir: str | None = None      # container dir for Spark event logs (None = disabled)
    spark_conf: tuple[str, ...] = ()      # extra "key=value" pairs passed as --conf


def spark_submit(script: str, script_args: Sequence[str], container_name: str,
                 opts: SparkSubmitOptions) -> list[str]:
    """Return the full `docker compose run` command for one spark-submit.

    Input: repo-relative script path, its arguments, the driver container name.
    The driver container name doubles as `spark.driver.host` so executors can reach it.
    """
    cmd = ["docker", "compose", "run", "--rm", "--no-deps", "--name", container_name,
           opts.service, "/opt/spark/bin/spark-submit",
           "--master", opts.master_url,
           "--conf", f"spark.driver.host={container_name}",
           "--conf", f"spark.jars.ivy={opts.ivy_dir}"]
    if opts.event_log_dir:
        # Spark 4 defaults to rolling, zstd-compressed logs; one plain JSON file is readable on the host
        # without extra packages (Python 3.12 has no zstd module).
        cmd += ["--conf", "spark.eventLog.enabled=true",
                "--conf", f"spark.eventLog.dir=file://{opts.event_log_dir}",
                "--conf", "spark.eventLog.compress=false",
                "--conf", "spark.eventLog.rolling.enabled=false"]
    for kv in opts.spark_conf:
        if "=" not in kv:
            raise ValueError(f"spark conf must be key=value, got {kv!r}")
        cmd += ["--conf", kv]
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


def minio_remove(bucket: str, *prefixes: str) -> list[str]:
    """Delete `<bucket>/<prefix>/` recursively for each prefix, in one shell-less `mc rm` call.

    A trailing slash is always added so that `curated/x_aqe/` never matches `curated/x_aqe_shuffle/`.
    """
    if not prefixes:
        raise ValueError("no prefix given")
    targets = []
    for prefix in prefixes:
        clean = prefix.strip("/")
        if not clean or ".." in clean or "/" not in clean:
            raise ValueError(f"refusing to delete suspicious prefix {prefix!r}")
        targets.append(f"local/{bucket}/{clean}/")
    return ["docker", "compose", "run", "--rm", "--no-deps", "minio-init", "rm", "--recursive", "--force", *targets]


def container_exists(name: str) -> list[str]:
    """List containers (running or not) with exactly this name."""
    return ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"]


def running_containers() -> list[str]:
    """Running containers with their compose project label, tab-separated."""
    return ["docker", "ps", "--format", '{{.Names}}\t{{.Label "com.docker.compose.project"}}']


def to_display(cmd: Sequence[str]) -> str:
    """Human-readable command line (for logs and dry runs; not meant to be re-parsed)."""
    return " ".join(f'"{c}"' if (" " in c or not c) else c for c in cmd)
