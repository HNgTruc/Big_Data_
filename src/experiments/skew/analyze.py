"""Analysis of skew: times for balanced/skewed data with and without AQE, plus AQE skew-join counts.

    python -m src.experiments.skew.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records, stats  # noqa: E402

EXP = "skew"
CONFIG_ORDER = ("balanced_aqe", "balanced_noaqe", "skew_aqe", "skew_noaqe")


def add_ratios(summary: list[dict]) -> None:
    """skew/balanced time ratio (same AQE setting) on the skew_* rows, from the means."""
    for metric in ("processing_seconds_total", *[f"stage_{s}" for s in A.ETL_STAGES]):
        for aqe in ("aqe", "noaqe"):
            bal = A.lookup(summary, metric, config=f"balanced_{aqe}")
            skw = A.lookup(summary, metric, config=f"skew_{aqe}")
            if bal and skw:
                skw["ratio_vs_balanced"] = stats.ratio(skw["mean"], bal["mean"])


def analyze(results_root: Path = paths.RESULTS_DIR, repo_root: Path = paths.REPO_ROOT) -> list[dict]:
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = [A.etl_run_row(r) for r in recs]
    A.write_csv(out_dir / "runs.csv", rows)
    summary = A.summary_rows(rows, ["config", "dataset"], A.etl_metric_names())
    add_ratios(summary)
    A.write_csv(out_dir / "summary.csv", summary)
    plan = A.plan_rows(recs, repo_root)
    A.write_csv(out_dir / "plan_check.csv", plan)
    for row in plan:
        print(f"[{EXP}] plan {row['config']} r{row['rep']}: SMJ={row.get('SortMergeJoin')} "
              f"skewSMJ={row.get('SortMergeJoin(skew=true)')} BHJ={row.get('BroadcastHashJoin')} "
              f"{row.get('note', '')}")
    configs = [c for c in CONFIG_ORDER if any(r["config"] == c for r in rows)]
    plots.etl_config_figure(summary, configs, results_root / "figures" / EXP / "skew.png",
                            f"results/metrics/{EXP}/summary.csv", "Thời gian ETL: lệch khoá × AQE",
                            A.ETL_STAGES)
    print(f"[{EXP}] {len(rows)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
