"""Analysis of format_compare: query times raw vs curated, and storage sizes.

    python -m src.experiments.format_compare.analyze
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.experiments.common import analysis as A  # noqa: E402
from src.experiments.common import paths, plots, records, stats  # noqa: E402

EXP = "format_compare"
# raw file -> curated table with the same content (before cleaning)
TABLE_FILES = {"customers": "customers.csv", "orders": "orders.csv", "order_items": "order_items.csv",
               "products": "products.parquet", "web_events": "web_events.jsonl"}


def query_rows(recs: list[dict]) -> list[dict]:
    """Long format: one row per (run, query, format). Failed runs give one row with status only."""
    out = []
    for rec in recs:
        base = {"config": rec.get("config"), "rep": rec.get("rep"), "dataset": rec.get("dataset"),
                "status": rec.get("status"), "wall_seconds": rec.get("wall_seconds"), **A.provenance(rec)}
        ms = ((rec.get("metrics") or {}).get("measurements")) or []
        if rec.get("status") != "ok" or not ms:
            out.append({**base, "query": None, "format": None, "seconds": None})
            continue
        for m in ms:
            out.append({**base, "query": m["query"], "format": m["format"], "seq": m.get("seq"),
                        "seconds": m["seconds"], "result": m.get("result")})
    return out


def summarize_queries(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[float]] = {}
    for r in rows:
        if r.get("status") == "ok" and r.get("query"):
            groups.setdefault((r["config"], r["query"], r["format"]), []).append(r["seconds"])
    summary = [{"config": c, "query": q, "format": f, "metric": "seconds", "unit": "s", **stats.summarize(v)}
               for (c, q, f), v in sorted(groups.items())]
    for row in summary:
        if row["format"] == "raw":
            cur = next((s for s in summary if s["config"] == row["config"] and s["query"] == row["query"]
                        and s["format"] == "curated"), None)
            row["ratio_raw_over_curated"] = stats.ratio(row["mean"], cur["mean"]) if cur else None
    return summary


def size_rows(recs: list[dict]) -> list[dict]:
    """Raw vs curated bytes per table, from every successful run (they should be identical)."""
    out = []
    for rec in records.ok_records(recs):
        sizes = (rec.get("metrics") or {}).get("sizes") or {}
        for table, raw_file in TABLE_FILES.items():
            raw = (sizes.get("raw") or {}).get(raw_file) or {}
            cur = (sizes.get("curated") or {}).get(table) or {}
            out.append({"config": rec["config"], "rep": rec["rep"], "table": table, "raw_file": raw_file,
                        "raw_bytes": raw.get("bytes"), "curated_bytes": cur.get("bytes"),
                        "curated_files": cur.get("files"),
                        "ratio_raw_over_curated": stats.ratio(raw.get("bytes"), cur.get("bytes")),
                        "measured_with": "Hadoop FileSystem.getContentSummary (s3a)"})
    return out


def plot(summary: list[dict], sizes: list[dict], fig_dir: Path) -> None:
    plt = plots.pyplot()
    if plt is None or not summary:
        return
    for config in sorted({s["config"] for s in summary}):
        part = [s for s in summary if s["config"] == config]
        queries = sorted({s["query"] for s in part})
        series = {}
        for fmt in ("raw", "curated"):
            vals = [next((s for s in part if s["query"] == q and s["format"] == fmt), {}) for q in queries]
            series[fmt] = ([v.get("mean") for v in vals], [v.get("std") for v in vals], [v.get("n") for v in vals])
        fig, ax = plt.subplots(figsize=(8, 4.5))
        plots.grouped_bars(plt, ax, queries, series)
        ax.set_ylabel("Thời gian truy vấn (s)")
        ax.set_title(f"CSV/JSON thô so với Parquet ({config})")
        plots.save(plt, fig, fig_dir / f"query_times_{config}.png", f"results/metrics/{EXP}/summary.csv")
    first = {}
    for s in sizes:
        first.setdefault((s["config"], s["table"]), s)
    for config in sorted({c for c, _ in first}):
        rows = [v for (c, _), v in first.items() if c == config]
        tables = [r["table"] for r in rows]
        mb = lambda v: (v or 0) / 2**20  # noqa: E731
        series = {"raw": ([mb(r["raw_bytes"]) for r in rows], [None] * len(rows), [1] * len(rows)),
                  "curated": ([mb(r["curated_bytes"]) for r in rows], [None] * len(rows), [1] * len(rows))}
        fig, ax = plt.subplots(figsize=(8, 4.5))
        plots.grouped_bars(plt, ax, tables, series)
        ax.set_ylabel("Dung lượng (MiB)")
        ax.set_title(f"Dung lượng thô so với Parquet đã làm sạch ({config})")
        plots.save(plt, fig, fig_dir / f"storage_{config}.png", f"results/metrics/{EXP}/sizes.csv")


def analyze(results_root: Path = paths.RESULTS_DIR) -> list[dict]:
    recs = records.load_records(EXP, results_root / "metrics")
    if not recs:
        print(f"[{EXP}] no run records under {results_root / 'metrics' / EXP}")
        return []
    out_dir = results_root / "metrics" / EXP
    rows = query_rows(recs)
    A.write_csv(out_dir / "runs.csv", rows)
    summary = summarize_queries(rows)
    A.write_csv(out_dir / "summary.csv", summary)
    sizes = size_rows(recs)
    A.write_csv(out_dir / "sizes.csv", sizes)
    plot(summary, sizes, results_root / "figures" / EXP)
    print(f"[{EXP}] {len(recs)} run(s), {len(records.ok_records(recs))} ok -> {out_dir}")
    return summary


def main() -> int:
    analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
