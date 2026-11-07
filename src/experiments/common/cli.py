"""Command-line options shared by every `src/experiments/<exp>/run.py`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Sequence

from . import paths
from .runner import Runner, RunnerOptions, RunSpec


def add_common_args(p: argparse.ArgumentParser, default_order: str = "interleaved") -> None:
    env = paths.read_env()
    port = env.get("SPARK_MASTER_UI_PORT", "8090")
    g = p.add_argument_group("runner")
    g.add_argument("--reps", type=int, default=3, help="repetitions per configuration (default 3, none discarded)")
    g.add_argument("--dry-run", action="store_true", help="print the commands; do not call Docker")
    g.add_argument("--order", choices=("interleaved", "blocked"), default=default_order,
                   help=f"interleaved = r1 of every config, then r2, ...; blocked = all reps of a config "
                        f"in a row (default {default_order})")
    g.add_argument("--configs", help="comma-separated subset of configurations to run")
    g.add_argument("--overwrite", action="store_true", help="re-run reps that already have a record "
                                                            "(old files are renamed, not deleted)")
    g.add_argument("--resume", action="store_true", help="skip reps whose record has status ok")
    g.add_argument("--timeout", type=float, default=3600.0, help="seconds before one run is killed")
    g.add_argument("--stop-on-failure", action="store_true")
    g.add_argument("--master-json-url", default=f"http://localhost:{port}/json/")
    g.add_argument("--cores-per-worker", type=int, default=int(env.get("SPARK_WORKER_CORES", "2")),
                   help="expected cores of each ALIVE worker (0 = do not check)")
    g.add_argument("--ivy-cache", type=Path,
                   help="host folder mounted at /tmp/.ivy so --packages jars are downloaded once "
                        "(default: off, i.e. the same command as infra/README.md)")
    g.add_argument("--cleanup-curated", action="store_true",
                   help="after the runs, delete curated/<exp>_<config> and quarantine/<exp>_<config> on MinIO")
    g.add_argument("--python", default=sys.executable, help="interpreter for host-side (pandas) runs")


def options_from_args(args: argparse.Namespace) -> RunnerOptions:
    env = paths.read_env()
    return RunnerOptions(
        reps=args.reps, dry_run=args.dry_run, order=args.order, overwrite=args.overwrite,
        resume=args.resume, timeout_s=args.timeout, master_url=args.master_json_url,
        cores_per_worker=args.cores_per_worker or None, ivy_cache=args.ivy_cache,
        bucket=env.get("MINIO_BUCKET", "bigdata"), hadoop_aws_version=env.get("HADOOP_AWS_VERSION", "3.4.1"),
        python=args.python, stop_on_failure=args.stop_on_failure, cleanup_curated=args.cleanup_curated)


def select_configs(specs: list[RunSpec], configs: str | None) -> list[RunSpec]:
    if not configs:
        return specs
    wanted = [c.strip() for c in configs.split(",") if c.strip()]
    known = {s.config for s in specs}
    unknown = [c for c in wanted if c not in known]
    if unknown:
        raise SystemExit(f"unknown configuration(s) {unknown}; available: {sorted(known)}")
    return [s for s in specs if s.config in wanted]


def split_list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def run_main(exp: str, title: str, description: str, add_args: Callable[[argparse.ArgumentParser], None],
             build_specs: Callable[[argparse.Namespace], list[RunSpec]], argv: Sequence[str] | None,
             default_order: str = "interleaved") -> int:
    """Parse arguments, build the plan and run it. Returns the runner exit status."""
    p = argparse.ArgumentParser(prog=f"python -m src.experiments.{exp}.run", description=description,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_args(p)
    add_common_args(p, default_order)
    args = p.parse_args(argv)
    specs = select_configs(build_specs(args), args.configs)
    return Runner(exp, title, specs, options_from_args(args)).run()
