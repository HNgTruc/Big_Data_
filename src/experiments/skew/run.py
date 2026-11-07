"""Experiment skew: {balanced, skewed} data x {auto join, forced shuffle join} x {AQE on, off} = 8 configurations.

    python -m src.experiments.skew.run [--balanced-dataset orders_5m] [--skew-dataset orders_5m_skew] [--dry-run]

The skewed dataset sends 50% of product picks (order_items, web_events) to 10 products
(`--skew --hot-products 10 --hot-share 0.5` of src/data_generation).

`auto` keeps the ETL defaults (auto join, 8 shuffle partitions). `shuffle` deliberately makes the product
joins sort-merge joins with enough partitions for AQE's skew-join split to be able to act at this data
size (see README.md and results/metrics/skew/partition_stats_summary.csv):
  --join-strategy shuffle --no-auto-broadcast --shuffle-partitions 64
  --conf spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes=4194304   (4 MiB, default 256 MB)
  --conf spark.sql.adaptive.advisoryPartitionSizeInBytes=2097152               (2 MiB, default 64 MB)
These confs are not set by src/etl/session.py, so the spark-submit values reach the session; the ETL
metrics JSON records their effective values. Spark event logs are on for plan_check.csv.
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
SKEW_THRESHOLD_KEY = "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes"
ADVISORY_KEY = "spark.sql.adaptive.advisoryPartitionSizeInBytes"


def add_args(p: argparse.ArgumentParser) -> None:
    """Add this experiment's own command-line options to `p`."""
    p.add_argument("--balanced-dataset", default="orders_5m")
    p.add_argument("--skew-dataset", default="orders_5m_skew")
    p.add_argument("--forced-partitions", type=int, default=64, help="shuffle partitions of the `shuffle` variant")
    p.add_argument("--skew-threshold-bytes", type=int, default=4 * 2**20,
                   help="skewedPartitionThresholdInBytes of the `shuffle` variant (must exceed the advisory size)")
    p.add_argument("--advisory-bytes", type=int, default=2 * 2**20,
                   help="advisoryPartitionSizeInBytes of the `shuffle` variant (target size of skew splits)")
    p.add_argument("--no-event-log", action="store_true")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    """One RunSpec per configuration of this experiment, from the parsed arguments."""
    if args.skew_threshold_bytes <= args.advisory_bytes:
        raise SystemExit("--skew-threshold-bytes must be larger than --advisory-bytes (Spark documentation)")
    specs = []
    for join in ("auto", "shuffle"):
        for data_name, dataset in (("balanced", args.balanced_dataset), ("skew", args.skew_dataset)):
            for aqe in (True, False):
                extra = ["--join-strategy", join]
                conf: tuple[str, ...] = ()
                params = {"data": data_name, "join_variant": join, "aqe": aqe, "workers": 2}
                if join == "shuffle":
                    extra = ["--join-strategy", "shuffle", "--no-auto-broadcast",
                             "--shuffle-partitions", str(args.forced_partitions)]
                    conf = (f"{SKEW_THRESHOLD_KEY}={args.skew_threshold_bytes}",
                            f"{ADVISORY_KEY}={args.advisory_bytes}")
                    params.update({"shuffle_partitions": args.forced_partitions, "auto_broadcast": False,
                                   "skew_threshold_bytes": args.skew_threshold_bytes,
                                   "advisory_bytes": args.advisory_bytes})
                else:
                    params.update({"shuffle_partitions": 8, "auto_broadcast": True})
                if not aqe:
                    extra.append("--no-aqe")
                specs.append(RunSpec(exp=EXP, config=f"{data_name}_{join}_{'aqe' if aqe else 'noaqe'}", kind="etl",
                                     dataset=dataset, workers=2, args=tuple(extra), spark_conf=conf,
                                     event_log=not args.no_event_log, params=params))
    return specs


def main(argv=None) -> int:
    """Run the skew experiment (see module docstring)."""
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
