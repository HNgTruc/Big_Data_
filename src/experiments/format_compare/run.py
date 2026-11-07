"""Experiment format_compare: the same Spark queries on raw CSV/JSON and on curated Parquet.

    python -m src.experiments.format_compare.run [--dataset orders_5m] [--curated-label orders_5m]
                                                 [--query-order raw-first] [--dry-run] [--reps 3]

Runs src/experiments/common/query_bench.py (subcommand `format`); also records raw vs curated sizes
measured with the Hadoop FileSystem API (getContentSummary) on s3a://.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import cli  # noqa: E402
from src.experiments.common.runner import RunSpec  # noqa: E402

EXP = "format_compare"
TITLE = "CSV/JSON thô so với Parquet đã làm sạch"


def add_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dataset", default="orders_5m")
    p.add_argument("--curated-label", help="folder under curated/ to query (default: the dataset name, "
                                           "i.e. the output of the plain ETL run)")
    p.add_argument("--query-order", choices=("raw-first", "curated-first"), default="raw-first",
                   help="which format runs first for each query")


def build_specs(args: argparse.Namespace) -> list[RunSpec]:
    label = args.curated_label or args.dataset
    job = ("format", "--dataset", args.dataset, "--curated-label", label, "--order", args.query_order)
    return [RunSpec(exp=EXP, config=args.dataset, kind="query_bench", dataset=args.dataset, workers=2, args=job,
                    params={"curated_label": label, "order": args.query_order, "workers": 2,
                            "shuffle_partitions": 8, "aqe": True})]


def main(argv=None) -> int:
    return cli.run_main(EXP, TITLE, __doc__, add_args, build_specs, argv)


if __name__ == "__main__":
    raise SystemExit(main())
