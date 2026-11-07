"""Experiment pandas_baseline: the ETL rules in pandas on one machine (host Windows, no Docker).

    python -m src.experiments.pandas_baseline.run [--datasets orders_500k,orders_1m] [--dry-run] [--reps 3]

Each repetition is a fresh Python process (baseline.py), so the peak memory is per run and the
wall clock includes interpreter start-up and imports.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "pandas_baseline"
TITLE = "baseline Pandas một máy"


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--datasets", default="orders_500k,orders_1m", help="comma-separated (decided: 500k and 1m)")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    return [RunSpec(exp=EXP, config=ds, kind="pandas", dataset=ds, workers=None,
                    params={"engine": "pandas", "reader": "read_csv (C engine) / read_json", "host": "local"})
            for ds in cli.split_list(args.datasets)]


def main(argv=None) -> int:
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
