"""Delete the MinIO outputs written by experiment ETL runs: curated/<exp>_<config>/ and quarantine/<exp>_<config>/.

    python -m src.experiments.cleanup --exps scale_data,join_strategy --dry-run
    python -m src.experiments.cleanup --group spark

Labels come from the default plan of each experiment plus the run records already on disk.
Only these labels are touched (never raw/ or curated/<dataset>/).
Uses `docker compose run --rm --no-deps minio-init rm --recursive --force ...` from infra/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.common import paths, records, registry  # noqa: E402
from src.experiments.common.runner import Runner, RunnerOptions  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--group", choices=sorted(registry.GROUPS), default="spark")
    p.add_argument("--exps", help="comma-separated experiments (overrides --group)")
    p.add_argument("--dry-run", action="store_true", help="print the commands only")
    args = p.parse_args(argv)
    bucket = paths.read_env().get("MINIO_BUCKET", "bigdata")
    for exp in registry.resolve(args.exps, args.group, None):
        run_mod = registry.module(exp, "run")
        # Build the default plan of the experiment to know its labels (no run happens).
        parser = argparse.ArgumentParser()
        run_mod.add_args(parser)
        specs = run_mod.build_specs(parser.parse_args([]))
        runner = Runner(exp, run_mod.TITLE, specs, RunnerOptions(reps=1, dry_run=args.dry_run, bucket=bucket))
        recorded = {r["label"] for r in records.load_records(exp) if r.get("kind") == "etl" and r.get("label")}
        runner.cleanup(sorted(set(runner.labels()) | recorded))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
