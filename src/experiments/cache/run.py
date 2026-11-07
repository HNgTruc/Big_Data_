"""Experiment cache: K repeated aggregate queries on curated orders JOIN order_items, without/with cache().

    python -m src.experiments.cache.run [--dataset orders_5m] [--k 5] [--dry-run] [--reps 3]

Runs src/experiments/common/query_bench.py (subcommand `cache`). With cache, materialisation
(cache + count) is timed separately from the queries; the DataFrame is unpersisted at the end.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "cache"
TITLE = "cache DataFrame dùng lại"


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dataset", default="orders_5m")
    p.add_argument("--curated-label", help="folder under curated/ (default: the dataset name)")
    p.add_argument("--k", type=int, default=5, help="number of queries per run")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    label = args.curated_label or args.dataset
    specs = []
    for mode in ("nocache", "cache"):
        job = ("cache", "--dataset", args.dataset, "--curated-label", label, "--mode", mode, "--k", str(args.k))
        specs.append(RunSpec(exp=EXP, config=mode, kind="query_bench", dataset=args.dataset, workers=2, args=job,
                             params={"mode": mode, "k": args.k, "curated_label": label, "workers": 2,
                                     "shuffle_partitions": 8, "aqe": True}))
    return specs


def main(argv=None) -> int:
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
