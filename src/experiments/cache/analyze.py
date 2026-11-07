"""Analysis of cache: per-query times, materialisation cost and totals for nocache vs cache.

    python -m src.experiments.cache.analyze
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records  # noqa: E402

EXP = "cache"
TOTALS = ("materialize_seconds", "queries_seconds_total", "total_seconds")


def step_rows(recs: list[dict]) -> list[dict]:
    """Long format: one row per (run, step); steps are `materialize` and `q<index>_<query>`."""
    out = []
    for rec in recs:
        m = rec.get("metrics") or {}
        base = {"config": rec.get("config"), "rep": rec.get("rep"), "dataset": rec.get("dataset"),
                "status": rec.get("status"), "k": m.get("k"), "storage_level": m.get("storage_level"),
                "warmup_seconds": m.get("warmup_seconds"), **A.provenance(rec)}
        if rec.get("status") != "ok":
            out.append({**base, "step": None, "seconds": None})
            continue
        if m.get("materialize_seconds") is not None:
            out.append({**base, "step": "materialize", "index": 0, "seconds": m["materialize_seconds"]})
        for q in m.get("measurements", []):
            out.append({**base, "step": f"q{q['index']}_{q['query']}", "index": q["index"], "seconds": q["seconds"]})
        for key in TOTALS:
            out.append({**base, "step": key, "index": None, "seconds": m.get(key)})
    return out


def summarize_steps(rows: list[dict]) -> list[dict]:
    """Per (config, step) over valid runs (quality columns from analysis.summary_rows)."""
    measured = [r for r in rows if r.get("step")]
    summary = A.summary_rows(measured, ["config", "dataset", "step"], ["seconds"])
    failed = [r for r in rows if not r.get("step")]
    for row in summary:
        row["n_failed"] = sum(1 for r in failed if r.get("config") == row["config"])
    return sorted(summary, key=lambda r: (r["config"], r["step"]))


def break_even(summary: list[dict], k: int | None) -> dict:
    """Number of queries n* after which caching is cheaper, from the means.

    Cost of n queries of the measured mix: without cache n*u, with cache M + n*c, where u and c are the mean
    per-query times (queries_seconds_total / k) and M the materialisation (cache + count). Hence
    n* = M / (u - c), valid only when u > c. Both benchmarks run an untimed warm-up first, so neither the
    first nocache query nor the materialisation pays JVM/executor start-up.
    """
    def mean(config: str, step: str):
        row = next((s for s in summary if s["config"] == config and s["step"] == step), None)
        return row["mean"] if row else None
    no_q, c_q = mean("nocache", "queries_seconds_total"), mean("cache", "queries_seconds_total")
    mat = mean("cache", "materialize_seconds")
    if not k or no_q is None or c_q is None or mat is None:
        return {"k": k, "break_even_queries": None}
    u, c = no_q / k, c_q / k
    n_star = mat / (u - c) if u > c else None
    return {"k": k, "per_query_nocache_mean": u, "per_query_cache_mean": c, "materialize_mean": mat,
            "per_query_saving": u - c, "break_even_queries": n_star,
            "break_even_queries_ceil": math.ceil(n_star) if n_star is not None else None,
            "saving_at_k": no_q - (mat + c_q),
            "formula": "n* = M / (u - c); u, c = mean per-query time without/with cache; M = materialize",
            "note": "từ trung bình; None nếu cache không làm truy vấn nhanh hơn"}


def plot(summary: list[dict], fig_dir: Path) -> None:
    """Draw this experiment's figures into results/figures/<exp>/ (skipped without matplotlib)."""
    plt = plots.pyplot()
    if plt is None or not summary:
        return
    steps = sorted({s["step"] for s in summary if s["step"].startswith("q")},
                   key=lambda x: int(x.split("_")[0][1:]))
    series = {}
    for config in ("nocache", "cache"):
        vals = [next((s for s in summary if s["config"] == config and s["step"] == st), {}) for st in steps]
        series[config] = ([v.get("mean") for v in vals], [v.get("std") for v in vals], [v.get("n") for v in vals])
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    plots.grouped_bars(plt, axes[0], [s.split("_")[0] for s in steps], series)
    axes[0].set_ylabel("Thời gian truy vấn (s)")
    axes[0].set_title("Từng truy vấn (trung bình ± std)")
    labels, means, stds, ns = [], [], [], []
    for config, step in (("nocache", "total_seconds"), ("cache", "materialize_seconds"),
                         ("cache", "queries_seconds_total"), ("cache", "total_seconds")):
        row = next((s for s in summary if s["config"] == config and s["step"] == step), None)
        if row:
            labels.append(f"{config}\n{step.replace('_seconds', '').replace('_total', '')}")
            means.append(row["mean"])
            stds.append(row["std"])
            ns.append(row["n"])
    plots.bars(plt, axes[1], labels, means, stds, ns)
    axes[1].set_xticks(range(len(labels)))
    axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel("Thời gian (s)")
    axes[1].set_title("Tổng thời gian và chi phí materialize")
    plots.save(plt, fig, fig_dir / "cache.png", f"results/metrics/{EXP}/summary.csv")


def analyze(results_root: Path = paths.RESULTS_DIR) -> list[dict]:
    """Rebuild runs.csv, summary.csv (and extra tables) and figures from the run records; returns the summary."""
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = step_rows(recs)
    A.write_csv(out_dir / "runs.csv", rows)
    summary = summarize_steps(rows)
    A.write_csv(out_dir / "summary.csv", summary)
    A.warn_quality(EXP, summary)
    ks = {r.get("k") for r in rows if r.get("k")}
    A.write_csv(out_dir / "break_even.csv", [break_even(summary, ks.pop() if len(ks) == 1 else None)])
    plot(summary, results_root / "figures" / EXP)
    print(f"[{EXP}] {len(recs)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    """Command-line entry point: analyze the records under results/."""
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
