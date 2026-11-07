"""Analysis of scale_workers: speedup S = T(1 worker) / T(2 workers), efficiency E = S / 2.

    python -m src.experiments.scale_workers.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records, stats  # noqa: E402

EXP = "scale_workers"
BASE, SCALED, RESOURCE_RATIO = "w1", "w2", 2.0
TIME_METRICS = ["processing_seconds_total", "wall_seconds", *[f"stage_{s}" for s in A.ETL_STAGES]]


def add_speedup(summary: list[dict]) -> None:
    """Speedup/efficiency on the w2 rows (computed from the means); w1 rows get speedup 1."""
    for metric in TIME_METRICS:
        base = A.lookup(summary, metric, config=BASE)
        scaled = A.lookup(summary, metric, config=SCALED)
        if not base or not scaled:
            continue
        s = stats.speedup(base["mean"], scaled["mean"])
        scaled.update({"speedup": s, "efficiency": stats.efficiency(s, RESOURCE_RATIO)})
        base.update({"speedup": 1.0 if base["mean"] else None, "efficiency": 1.0 if base["mean"] else None})


def plot(summary: list[dict], fig_dir: Path, source: str) -> None:
    """Draw this experiment's figures into results/figures/<exp>/ (skipped without matplotlib)."""
    plt = plots.pyplot()
    if plt is None:
        return
    configs = [c for c in (BASE, SCALED) if A.lookup(summary, "processing_seconds_total", config=c)]
    if not configs:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    rows = [A.lookup(summary, "processing_seconds_total", config=c) for c in configs]
    plots.bars(plt, axes[0], ["1 worker" if c == BASE else "2 worker" for c in configs],
               [r["mean"] for r in rows], [r["std"] for r in rows], [r["n"] for r in rows])
    axes[0].set_xticks(range(len(configs)))
    axes[0].set_xticklabels(["1 worker" if c == BASE else "2 worker" for c in configs])
    axes[0].set_ylabel("Thời gian xử lý (s)")
    axes[0].set_title("Thời gian ETL (trung bình ± std)")
    names, values = [], []
    for metric in TIME_METRICS:
        row = A.lookup(summary, metric, config=SCALED)
        if row and row.get("speedup") is not None:
            names.append(metric.replace("stage_", "").replace("_seconds", ""))
            values.append(row["speedup"])
    axes[1].bar(range(len(names)), values)
    axes[1].axhline(RESOURCE_RATIO, ls="--", color="gray", label="lý tưởng (S = 2)")
    axes[1].axhline(1.0, ls=":", color="black", label="S = 1")
    axes[1].set_xticks(range(len(names)))
    axes[1].set_xticklabels(names, rotation=30, ha="right")
    axes[1].set_ylabel("Speedup T(1)/T(2) (lần)")
    axes[1].set_title("Speedup theo chỉ số (từ trung bình)")
    axes[1].legend(fontsize=8)
    plots.save(plt, fig, fig_dir / "speedup.png", source)


def analyze(results_root: Path = paths.RESULTS_DIR) -> list[dict]:
    """Rebuild runs.csv, summary.csv (and extra tables) and figures from the run records; returns the summary."""
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = [A.etl_run_row(r) for r in recs]
    A.write_csv(out_dir / "runs.csv", rows)
    summary = A.summary_rows(rows, ["config", "dataset"], A.etl_metric_names())
    add_speedup(summary)
    A.write_csv(out_dir / "summary.csv", summary)
    A.warn_quality(EXP, summary)
    plot(summary, results_root / "figures" / EXP, f"results/metrics/{EXP}/summary.csv")
    print(f"[{EXP}] {len(rows)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    """Command-line entry point: analyze the records under results/."""
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
