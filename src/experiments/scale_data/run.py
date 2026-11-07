"""Experiment scale_data: ETL time vs data size (default config: auto join, AQE on, 2 workers).

    python -m src.experiments.scale_data.run [--datasets orders_500k,orders_1m,...] [--dry-run] [--reps 3]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "scale_data"
TITLE = "mở rộng theo kích thước dữ liệu"
DEFAULT_DATASETS = "orders_500k,orders_1m,orders_2500k,orders_5m"


def add_args(p: argparse.ArgumentParser) -> None:
    """Add this experiment's own command-line options to `p`."""
    p.add_argument("--datasets", default=DEFAULT_DATASETS, help="comma-separated, smallest first")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    """One RunSpec per configuration of this experiment, from the parsed arguments."""
    return [RunSpec(exp=EXP, config=ds, kind="etl", dataset=ds, workers=2,
                    params={"join_strategy": "auto", "aqe": True, "workers": 2, "shuffle_partitions": 8})
            for ds in cli.split_list(args.datasets)]


def main(argv=None) -> int:
    """Command-line entry point; returns the process exit status."""
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
