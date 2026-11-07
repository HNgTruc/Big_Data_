"""Turn run records into CSV tables (standard library only, so analysis runs without Docker or pandas)."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

from . import paths, stats

ETL_STAGES = ("dimensions", "orders", "order_items", "web_events", "aggregates")
PROVENANCE = ("started_at", "ended_at", "git_commit", "git_dirty", "alive_workers", "total_cores",
              "seed", "spark_version", "app_id", "log_path")


def provenance(rec: dict) -> dict:
    before = rec.get("cluster_before") or {}
    return {"started_at": rec.get("started_at"), "ended_at": rec.get("ended_at"),
            "git_commit": (rec.get("git") or {}).get("commit"), "git_dirty": (rec.get("git") or {}).get("dirty"),
            "alive_workers": before.get("alive_workers"), "total_cores": before.get("total_alive_cores"),
            "seed": rec.get("seed"), "spark_version": rec.get("spark_version"), "app_id": rec.get("app_id"),
            "log_path": rec.get("log_path")}


def etl_raw_rows(rec: dict) -> int | None:
    """Total raw rows read by the ETL (sum over the 5 tables in the metrics JSON), else from the manifest."""
    tables = ((rec.get("metrics") or {}).get("tables")) or {}
    if tables:
        return sum(int(t.get("raw_rows", 0)) for t in tables.values())
    return rec.get("raw_rows_total_manifest")


def etl_run_row(rec: dict) -> dict:
    """One CSV row per ETL repetition: status, wall clock, processing time, each stage."""
    stages = rec.get("stage_seconds") or {}
    raw_rows = etl_raw_rows(rec)
    row = {"exp": rec.get("exp"), "config": rec.get("config"), "rep": rec.get("rep"),
           "dataset": rec.get("dataset"), "status": rec.get("status"), "exit_code": rec.get("exit_code"),
           "wall_seconds": rec.get("wall_seconds"),
           "processing_seconds_total": rec.get("processing_seconds_total"),
           **{f"stage_{s}": stages.get(s) for s in ETL_STAGES},
           "raw_rows_total": raw_rows,
           "throughput_rows_per_s": stats.throughput(raw_rows, rec.get("processing_seconds_total"))
           if rec.get("status") == "ok" else None,
           "ivy_download_ms": (rec.get("ivy") or {}).get("download_ms"),
           **provenance(rec)}
    return row


def etl_metric_names() -> list[str]:
    return ["processing_seconds_total", "wall_seconds", *[f"stage_{s}" for s in ETL_STAGES],
            "throughput_rows_per_s"]


UNITS = {"throughput_rows_per_s": "rows/s"}


def summary_rows(rows: Sequence[dict], group_keys: Sequence[str], metrics: Sequence[str]) -> list[dict]:
    """Long-format summary: one row per (group, metric) over the successful runs only.

    `n` counts successful runs used; `n_failed` counts runs of the group with another status.
    """
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r.get(k) for k in group_keys), []).append(r)
    out = []
    for key, members in groups.items():
        ok = [m for m in members if m.get("status") == "ok"]
        for metric in metrics:
            s = stats.summarize(m.get(metric) for m in ok)
            out.append({**dict(zip(group_keys, key)), "metric": metric, "unit": UNITS.get(metric, "s"),
                        **s, "n_failed": len(members) - len(ok)})
    return out


def lookup(summary: Iterable[dict], metric: str, **keys) -> dict | None:
    for row in summary:
        if row.get("metric") == metric and all(row.get(k) == v for k, v in keys.items()):
            return row
    return None


def archived_attempts(exp: str, metrics_root: Path | None = None) -> int:
    """Number of renamed earlier attempts (run_record.<timestamp>.json) of this experiment."""
    base = (metrics_root or paths.RESULTS_DIR / "metrics") / exp / "runs"
    return len(list(base.glob("*/r*/run_record.*.json")))


def write_csv(path: Path, rows: Sequence[dict], columns: Sequence[str] | None = None) -> Path:
    """Write rows (dicts) to CSV; columns default to the union of keys in first-seen order."""
    if columns is None:
        columns = []
        for r in rows:
            columns += [k for k in r if k not in columns]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(columns), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r.get(k)) for k in columns})
    return path


def _fmt(v):
    if isinstance(v, float):
        return round(v, 6)
    return "" if v is None else v


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def plan_rows(recs: Sequence[dict], repo_root: Path = paths.REPO_ROOT) -> list[dict]:
    """Join operators in the final executed plans, per run, from the Spark event logs of the record."""
    from . import eventlog

    out = []
    for rec in recs:
        logs = [repo_root / p for p in rec.get("event_logs") or []]
        row = {"config": rec.get("config"), "rep": rec.get("rep"), "status": rec.get("status"),
               "event_log": ";".join(rec.get("event_logs") or [])}
        if not logs:
            row["note"] = "no event log"
        for path in logs:
            if not path.exists():
                row["note"] = f"missing {path.name}"
                continue
            try:
                for k, v in eventlog.summarize_file(path).items():
                    row[k] = row.get(k, 0) + v
            except ValueError as exc:
                row["note"] = str(exc)
        out.append(row)
    return out
