"""Run several experiments in the default order (see common/registry.py).

    python -m src.experiments.run_all --group all --dry-run
    python -m src.experiments.run_all --exps scale_data,join_strategy --reps 3

Every option not listed below is passed unchanged to each experiment's run.py, so only the shared
runner options (--reps, --dry-run, --order, --resume, --overwrite, --ivy-cache, ...) belong here;
experiment-specific options (e.g. --datasets) must be given to that experiment's run.py directly.
An aborted experiment (cluster in the wrong state) stops the whole sequence.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.common import registry  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--group", choices=sorted(registry.GROUPS), default="all")
    p.add_argument("--exps", help="comma-separated experiments (overrides --group)")
    p.add_argument("--exclude", help="comma-separated experiments to skip")
    args, passthrough = p.parse_known_args(argv)
    exps = registry.resolve(args.exps, args.group, args.exclude)
    print(f"experiments: {exps}; passthrough options: {passthrough}")
    results = {}
    for exp in exps:
        print(f"\n===== {exp} =====")
        status = registry.module(exp, "run").main(list(passthrough))
        results[exp] = status
        if status == 2:
            print(f"{exp} aborted (status 2); remaining experiments not started")
            break
    print("\nstatus per experiment (0 ok, 1 some runs failed, 2 aborted/refused):", results)
    return max(results.values(), default=0)


if __name__ == "__main__":
    raise SystemExit(main())
