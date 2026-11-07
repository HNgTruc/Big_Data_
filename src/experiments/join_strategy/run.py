"""Experiment join_strategy: broadcast vs shuffle (sort-merge) joins in the ETL, with auto as reference.

    python -m src.experiments.join_strategy.run [--dataset orders_5m] [--dry-run] [--reps 3]

Configurations (etl_job.py flags):
  auto            --join-strategy auto                         (Spark decides; reference)
  broadcast       --join-strategy broadcast                    (broadcast hint on the small join side)
  shuffle_hint    --join-strategy shuffle                      (merge hint on the hinted joins only)
  shuffle_noauto  --join-strategy shuffle --no-auto-broadcast  (merge hint + autoBroadcastJoinThreshold=-1)
Spark event logs are on, so analyze.py can count the join operators that actually ran (after AQE).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "join_strategy"
TITLE = "broadcast join so với shuffle join"
CONFIGS = {
    "auto": ("auto", False),
    "broadcast": ("broadcast", False),
    "shuffle_hint": ("shuffle", False),
    "shuffle_noauto": ("shuffle", True),
}


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dataset", default="orders_5m")
    p.add_argument("--no-event-log", action="store_true", help="do not write Spark event logs")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    specs = []
    for name, (strategy, no_auto) in CONFIGS.items():
        extra = ["--join-strategy", strategy] + (["--no-auto-broadcast"] if no_auto else [])
        specs.append(RunSpec(exp=EXP, config=name, kind="etl", dataset=args.dataset, workers=2, args=tuple(extra),
                             event_log=not args.no_event_log,
                             params={"join_strategy": strategy, "auto_broadcast": not no_auto, "aqe": True,
                                     "workers": 2, "shuffle_partitions": 8}))
    return specs


def main(argv=None) -> int:
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
