"""Analysis of join_strategy: times per configuration and join operators found in the event logs.

    python -m src.experiments.join_strategy.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records  # noqa: E402

EXP = "join_strategy"
CONFIG_ORDER = ("auto", "broadcast", "shuffle_noauto")


def analyze(results_root: Path = paths.RESULTS_DIR, repo_root: Path = paths.REPO_ROOT) -> list[dict]:
    """Rebuild runs.csv, summary.csv (and extra tables) and figures from the run records; returns the summary."""
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = [A.etl_run_row(r) for r in recs]
    A.write_csv(out_dir / "runs.csv", rows)
    summary = A.summary_rows(rows, ["config", "dataset"], A.etl_metric_names())
    A.write_csv(out_dir / "summary.csv", summary)
    A.warn_quality(EXP, summary)
    plan = A.plan_rows(recs, repo_root)
    A.write_csv(out_dir / "plan_check.csv", plan)
    for row in plan:
        print(f"[{EXP}] plan {row['config']} r{row['rep']}: SMJ={row.get('SortMergeJoin')} "
              f"BHJ={row.get('BroadcastHashJoin')} SHJ={row.get('ShuffledHashJoin')} {row.get('note', '')}")
    configs = [c for c in CONFIG_ORDER if any(r["config"] == c for r in rows)]
    plots.etl_config_figure(summary, configs, results_root / "figures" / EXP / "join_strategy.png",
                            f"results/metrics/{EXP}/summary.csv", "Thời gian ETL theo chiến lược join",
                            A.ETL_STAGES)
    print(f"[{EXP}] {len(rows)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    """Command-line entry point: analyze the records under results/."""
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
