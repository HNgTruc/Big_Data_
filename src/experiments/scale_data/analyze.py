"""Analysis of scale_data (no Docker needed): runs.csv, summary.csv and figures.

    python -m src.experiments.scale_data.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records, stats  # noqa: E402

EXP = "scale_data"


def scaling_columns(summary: list[dict], rows: list[dict]) -> list[str]:
    """Add raw_rows_total, data_ratio, time_ratio to the processing_seconds_total rows.

    Datasets are ordered by raw rows; ratios are relative to the smallest dataset.
    Returns the configs in that order.
    """
    raw = {}
    for r in rows:
        if r.get("raw_rows_total") is not None:
            raw.setdefault(r["config"], r["raw_rows_total"])
    configs = sorted(raw, key=raw.get)
    proc = [A.lookup(summary, "processing_seconds_total", config=c) for c in configs]
    means = [p["mean"] if p else None for p in proc]
    data_ratio = stats.relative_to_first([raw[c] for c in configs])
    time_ratio = stats.relative_to_first(means)
    for p, c, dr, tr in zip(proc, configs, data_ratio, time_ratio):
        if p:
            p.update({"raw_rows_total": raw[c], "data_ratio": dr, "time_ratio": tr})
    return configs


def plot(summary: list[dict], configs: list[str], fig_dir: Path, source: str) -> None:
    plt = plots.pyplot()
    if plt is None or not configs:
        return
    proc = [A.lookup(summary, "processing_seconds_total", config=c) or {} for c in configs]
    xs = [p.get("raw_rows_total", 0) / 1e6 for p in proc]
    means = [p.get("mean") for p in proc]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(xs, [m if m is not None else float("nan") for m in means],
                yerr=[p.get("std") or 0 for p in proc], marker="o", capsize=4, label="Spark (trung bình ± std)")
    for x, p in zip(xs, proc):
        if p.get("mean") is not None:
            ax.annotate(f"n={p['n']}", (x, p["mean"]), textcoords="offset points", xytext=(5, -12), fontsize=8)
    if means and means[0] and xs[0]:
        ax.plot(xs, [means[0] * x / xs[0] for x in xs], "--", color="gray", label="tuyến tính từ bộ nhỏ nhất")
    ax.set_xlabel("Số dòng thô (triệu dòng, tổng 5 bảng)")
    ax.set_ylabel("Thời gian xử lý (s)")
    ax.set_title("Thời gian ETL theo kích thước dữ liệu")
    ax.legend()
    plots.save(plt, fig, fig_dir / "processing_time_vs_rows.png", source)

    thr = [A.lookup(summary, "throughput_rows_per_s", config=c) or {} for c in configs]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    plots.bars(plt, ax, configs, [t.get("mean") for t in thr], [t.get("std") for t in thr],
               [t.get("n") for t in thr])
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels(configs)
    ax.set_ylabel("Thông lượng (dòng thô/s)")
    ax.set_title("Thông lượng ETL theo kích thước dữ liệu")
    plots.save(plt, fig, fig_dir / "throughput.png", source)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bottom = [0.0] * len(configs)
    for stage in A.ETL_STAGES:
        vals = [(A.lookup(summary, f"stage_{stage}", config=c) or {}).get("mean") or 0.0 for c in configs]
        ax.bar(range(len(configs)), vals, bottom=bottom, label=stage)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels(configs)
    ax.set_ylabel("Thời gian trung bình (s)")
    ax.set_title("Thời gian theo giai đoạn (trung bình, n ở summary.csv)")
    ax.legend(fontsize=8)
    plots.save(plt, fig, fig_dir / "stages.png", source)


def analyze(results_root: Path = paths.RESULTS_DIR) -> list[dict]:
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = [A.etl_run_row(r) for r in recs]
    A.write_csv(out_dir / "runs.csv", rows)
    summary = A.summary_rows(rows, ["config", "dataset"], A.etl_metric_names())
    configs = scaling_columns(summary, rows)
    A.write_csv(out_dir / "summary.csv", summary)
    plot(summary, configs, results_root / "figures" / EXP, f"results/metrics/{EXP}/summary.csv")
    print(f"[{EXP}] {len(rows)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
