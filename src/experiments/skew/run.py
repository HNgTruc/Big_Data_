"""Experiment skew: balanced vs skewed product keys, each with AQE on and off (4 configurations).

    python -m src.experiments.skew.run [--balanced-dataset orders_5m] [--skew-dataset orders_5m_skew]
                                       [--join-strategy auto] [--dry-run] [--reps 3]

The skewed dataset sends 50% of product picks (order_items, web_events) to 10 products
(`--skew --hot-products 10 --hot-share 0.5` of src/data_generation). Spark event logs are on, so
analyze.py can count AQE skew-join splits.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "skew"
TITLE = "ảnh hưởng của lệch khoá và AQE"


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--balanced-dataset", default="orders_5m")
    p.add_argument("--skew-dataset", default="orders_5m_skew")
    p.add_argument("--join-strategy", choices=("auto", "broadcast", "shuffle"), default="auto",
                   help="join strategy for all 4 configurations (default auto, as decided)")
    p.add_argument("--no-auto-broadcast", action="store_true",
                   help="also set autoBroadcastJoinThreshold=-1 in all 4 configurations")
    p.add_argument("--no-event-log", action="store_true")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    specs = []
    for data_name, dataset in (("balanced", args.balanced_dataset), ("skew", args.skew_dataset)):
        for aqe in (True, False):
            extra = ["--join-strategy", args.join_strategy]
            extra += [] if aqe else ["--no-aqe"]
            extra += ["--no-auto-broadcast"] if args.no_auto_broadcast else []
            specs.append(RunSpec(
                exp=EXP, config=f"{data_name}_{'aqe' if aqe else 'noaqe'}", kind="etl", dataset=dataset,
                workers=2, args=tuple(extra), event_log=not args.no_event_log,
                params={"data": data_name, "aqe": aqe, "join_strategy": args.join_strategy,
                        "auto_broadcast": not args.no_auto_broadcast, "workers": 2, "shuffle_partitions": 8}))
    return specs


def main(argv=None) -> int:
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
