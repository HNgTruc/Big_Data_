"""Rebuild runs.csv, summary.csv and figures of every experiment from the run records (no Docker).

    python -m src.experiments.analyze_all [--exps scale_data,cache]

scale_data is analysed before pandas_baseline, which reuses its summary.csv for the comparison.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.common import registry  # noqa: E402


def main(argv=None) -> int:
    """Analyze the selected experiments in registry order; returns 0."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--group", choices=sorted(registry.GROUPS), default="all")
    p.add_argument("--exps", help="comma-separated experiments (overrides --group)")
    args = p.parse_args(argv)
    for exp in registry.resolve(args.exps, args.group, None):
        registry.module(exp, "analyze").analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
