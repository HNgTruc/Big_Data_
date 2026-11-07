"""Analysis of pandas_baseline, with the Spark times of scale_data (same datasets) when available.

    python -m src.experiments.pandas_baseline.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records, stats  # noqa: E402

EXP = "pandas_baseline"
SPARK_EXP = "scale_data"


def run_row(rec: dict) -> dict:
    m = rec.get("metrics") or {}
    row = A.etl_run_row(rec)
    peak = m.get("peak_rss_bytes")
    row.update({"peak_rss_mib": peak / 2**20 if peak else None, "peak_rss_method": m.get("peak_rss_method"),
                "all_match": m.get("all_match"), "n_checks": m.get("n_checks"), "n_mismatch": m.get("n_mismatch"),
                **{f"read_{s}": (m.get("substep_seconds") or {}).get(s, {}).get("read") for s in A.ETL_STAGES}})
    return row


def spark_comparison(summary: list[dict], spark_summary: Path) -> list[dict]:
    """Mean processing time pandas vs Spark (scale_data) per dataset; ratio = Spark / pandas."""
    if not spark_summary.exists():
        return []
    spark = A.read_csv(spark_summary)
    out = []
    for row in summary:
        if row["metric"] != "processing_seconds_total":
            continue
        sp = next((s for s in spark if s.get("config") == row["config"]
                   and s.get("metric") == "processing_seconds_total"), None)
        sp_mean = float(sp["mean"]) if sp and sp.get("mean") else None
        out.append({"dataset": row["config"], "pandas_mean_s": row["mean"], "pandas_std_s": row["std"],
                    "pandas_n": row["n"], "spark_mean_s": sp_mean,
                    "spark_std_s": float(sp["std"]) if sp and sp.get("std") else None,
                    "spark_n": int(sp["n"]) if sp and sp.get("n") else None,
                    "ratio_spark_over_pandas": stats.ratio(sp_mean, row["mean"]),
                    "spark_source": f"results/metrics/{SPARK_EXP}/summary.csv"})
    return out


def plot(comparison: list[dict], summary: list[dict], fig_dir: Path) -> None:
    plt = plots.pyplot()
    if plt is None:
        return
    rows = comparison or [{"dataset": s["config"], "pandas_mean_s": s["mean"], "pandas_std_s": s["std"],
                           "pandas_n": s["n"]} for s in summary if s["metric"] == "processing_seconds_total"]
    if not rows:
        return
    groups = [r["dataset"] for r in rows]
    series = {"Pandas (host)": ([r["pandas_mean_s"] for r in rows], [r["pandas_std_s"] for r in rows],
                                [r["pandas_n"] for r in rows])}
    if comparison:
        series["Spark (cụm Docker)"] = ([r.get("spark_mean_s") for r in rows], [r.get("spark_std_s") for r in rows],
                                        [r.get("spark_n") for r in rows])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    plots.grouped_bars(plt, ax, groups, series)
    ax.set_ylabel("Thời gian xử lý (s)")
    ax.set_title("Pandas một máy so với Spark (môi trường khác nhau, xem README)")
    plots.save(plt, fig, fig_dir / "pandas_vs_spark.png", f"results/metrics/{EXP}/comparison_spark.csv")


def analyze(results_root: Path = paths.RESULTS_DIR) -> list[dict]:
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = [run_row(r) for r in recs]
    A.write_csv(out_dir / "runs.csv", rows)
    metrics = ["processing_seconds_total", "wall_seconds", *[f"stage_{s}" for s in A.ETL_STAGES],
               "throughput_rows_per_s", "peak_rss_mib"]
    summary = A.summary_rows(rows, ["config", "dataset"], metrics)
    for row in summary:
        if row["metric"] == "peak_rss_mib":
            row["unit"] = "MiB"
    A.write_csv(out_dir / "summary.csv", summary)
    comparison = spark_comparison(summary, results_root / "metrics" / SPARK_EXP / "summary.csv")
    if comparison:
        A.write_csv(out_dir / "comparison_spark.csv", comparison)
    mism = [r for r in rows if r.get("status") == "ok" and not r.get("all_match")]
    if mism:
        print(f"[{EXP}] WARNING: {len(mism)} run(s) with LỆCH row counts; see their metrics JSON 'checks'")
    plot(comparison, summary, results_root / "figures" / EXP)
    print(f"[{EXP}] {len(rows)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
