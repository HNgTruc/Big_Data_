"""Experiment scale_workers: the same ETL with 1 and 2 workers (speedup, efficiency).

    python -m src.experiments.scale_workers.run [--dataset orders_5m] [--dry-run] [--reps 3]

The 1-worker runs stop `spark-worker-2` (docker compose stop), wait until the master reports exactly
1 ALIVE worker, and always start it again afterwards (try/finally), waiting for 2 ALIVE workers.
Default order is blocked (all 1-worker reps in a row) so the worker is stopped/started only once.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "scale_workers"
TITLE = "mở rộng theo số worker (1 so với 2)"


def add_args(p: argparse.ArgumentParser) -> None:
    """Add this experiment's own command-line options to `p`."""
    p.add_argument("--dataset", default="orders_5m")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    """One RunSpec per configuration of this experiment, from the parsed arguments."""
    return [RunSpec(exp=EXP, config=f"w{n}", kind="etl", dataset=args.dataset, workers=n,
                    params={"join_strategy": "auto", "aqe": True, "workers": n, "shuffle_partitions": 8})
            for n in (1, 2)]


def main(argv=None) -> int:
    """Command-line entry point; returns the process exit status."""
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv, default_order="blocked")


if __name__ == "__main__":
    raise SystemExit(main())
