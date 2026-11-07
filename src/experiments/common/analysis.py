"""Turn run records into CSV tables (standard library only, so analysis runs without Docker or pandas).

Every row carries `flags` and `valid`. Statistics use only valid runs: status ok and no excluding flag
(worker count changed during the run, raw rows differ from the manifest, pandas counts differ from the
references, MinIO pre-cleanup failed). `foreign_containers` is informational and does not exclude a run.
Summary rows also report the commits used, whether the tree was dirty, whether the group is homogeneous
(one commit, one set of runner options and job parameters) and whether row counts agree across all
valid runs of the same dataset.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from . import paths, stats

ETL_STAGES = ("dimensions", "orders", "order_items", "web_events", "aggregates")
EXCLUDING_FLAGS = ("workers_changed", "raw_rows_mismatch", "pandas_mismatch", "pre_cleanup_failed")
# Runner options that can change a measurement (resume/overwrite/dry-run/reps cannot).
OPTION_KEYS = ("ivy_cache", "cores_per_worker", "hadoop_aws_version", "bucket")


def _sig(obj) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:10]


def run_flags(rec: dict) -> list[str]:
    """Quality flags of one run record (see module docstring for which ones exclude the run)."""
    flags = []
    expected, after = rec.get("workers_expected"), rec.get("cluster_after")
    if expected is not None and (not isinstance(after, dict) or after.get("alive_workers") != expected):
        flags.append("workers_changed")
    manifest_rows = rec.get("raw_rows_manifest") or {}
    tables = ((rec.get("metrics") or {}).get("tables")) or {}
    if rec.get("kind") == "etl" and tables and manifest_rows:
        if any(tables.get(t, {}).get("raw_rows") != n for t, n in manifest_rows.items()):
            flags.append("raw_rows_mismatch")
    if rec.get("kind") == "pandas" and (rec.get("metrics") or {}).get("all_match") is False:
        flags.append("pandas_mismatch")
    pre = rec.get("pre_cleanup")
    if isinstance(pre, dict) and pre.get("exit_code") not in (0, None):
        flags.append("pre_cleanup_failed")
    if (rec.get("host_before") or {}).get("foreign_containers"):
        flags.append("foreign_containers")
    return flags


def counts_signature(rec: dict) -> str | None:
    """Short hash of the row counts (clean/quarantine per reason/duplicates, aggregate rows); None if absent."""
    m = rec.get("metrics") or {}
    if not m.get("tables"):
        return None
    keys = ("raw_rows", "clean_rows", "quarantined_rows", "duplicates_removed", "quarantine_by_reason")
    tables = {t: {k: v.get(k) for k in keys} for t, v in m["tables"].items()}
    return _sig({"tables": tables, "aggregates": m.get("aggregate_rows")})


def provenance(rec: dict) -> dict:
    """Columns describing where and how a run happened, plus its flags and validity."""
    before = rec.get("cluster_before") or {}
    flags = run_flags(rec)
    options = {k: (rec.get("runner_options") or {}).get(k) for k in OPTION_KEYS}
    memory = ((rec.get("host_before") or {}).get("memory")) or {}
    return {"started_at": rec.get("started_at"), "ended_at": rec.get("ended_at"),
            "git_commit": (rec.get("git") or {}).get("commit"), "git_dirty": (rec.get("git") or {}).get("dirty"),
            "alive_workers": before.get("alive_workers"), "total_cores": before.get("total_alive_cores"),
            "host_available_mib": memory["available_bytes"] / 2**20 if memory.get("available_bytes") else None,
            "foreign_containers": ";".join((rec.get("host_before") or {}).get("foreign_containers") or []),
            "seed": rec.get("seed"), "spark_version": rec.get("spark_version"), "app_id": rec.get("app_id"),
            "log_path": rec.get("log_path"),
            "options_sig": _sig(options),
            "params_sig": _sig([rec.get("params"), rec.get("job_args"), rec.get("spark_conf")]),
            "counts_sig": counts_signature(rec),
            "flags": ";".join(flags),
            "valid": rec.get("status") == "ok" and not any(f in EXCLUDING_FLAGS for f in flags)}


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
           "stats_seconds": (rec.get("metrics") or {}).get("stats_seconds"),
           "pre_cleanup_seconds": (rec.get("pre_cleanup") or {}).get("seconds"),
           "raw_rows_total": raw_rows,
           "throughput_rows_per_s": stats.throughput(raw_rows, rec.get("processing_seconds_total"))
           if rec.get("status") == "ok" else None,
           "ivy_download_ms": (rec.get("ivy") or {}).get("download_ms"),
           **provenance(rec)}
    return row


def etl_metric_names() -> list[str]:
    """Metrics summarised for every ETL experiment."""
    return ["processing_seconds_total", "wall_seconds", *[f"stage_{s}" for s in ETL_STAGES],
            "stats_seconds", "throughput_rows_per_s"]


UNITS = {"throughput_rows_per_s": "rows/s"}


def is_valid(row: dict) -> bool:
    """True if the row may enter statistics (works on fresh rows and on rows read back from CSV)."""
    return row.get("valid", row.get("status") == "ok") in (True, "True")


def group_quality(members: Sequence[dict], dataset_sigs: dict) -> dict:
    """Commits, dirty flag, homogeneity and row-count consistency of one summary group."""
    used = [m for m in members if is_valid(m)]
    commits = sorted({str(m.get("git_commit"))[:10] for m in used if m.get("git_commit")})
    homogeneous = (len(commits) <= 1 and len({m.get("options_sig") for m in used}) <= 1
                   and len({m.get("params_sig") for m in used}) <= 1)
    datasets = {m.get("dataset") for m in used}
    sigs = set().union(*(dataset_sigs.get(d, set()) for d in datasets)) if datasets else set()
    flags = sorted({f for m in members for f in str(m.get("flags") or "").split(";") if f})
    return {"git_commits": ";".join(commits),
            "dirty_any": any(m.get("git_dirty") in (True, "True") for m in used),
            "homogeneous": homogeneous,
            "counts_consistent": (len(sigs) <= 1) if sigs else None,
            "flags_seen": ";".join(flags)}


def summary_rows(rows: Sequence[dict], group_keys: Sequence[str], metrics: Sequence[str]) -> list[dict]:
    """Long-format summary: one row per (group, metric) over the valid runs only.

    `n` counts valid runs used; `n_failed` counts runs whose status is not ok; `n_excluded` counts runs
    that finished but carry an excluding flag. Quality columns: see group_quality.
    """
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r.get(k) for k in group_keys), []).append(r)
    dataset_sigs: dict = {}
    for r in rows:
        if is_valid(r) and r.get("counts_sig"):
            dataset_sigs.setdefault(r.get("dataset"), set()).add(r["counts_sig"])
    out = []
    for key, members in groups.items():
        used = [m for m in members if is_valid(m)]
        n_failed = sum(1 for m in members if m.get("status") != "ok")
        quality = group_quality(members, dataset_sigs)
        for metric in metrics:
            s = stats.summarize(m.get(metric) for m in used)
            out.append({**dict(zip(group_keys, key)), "metric": metric, "unit": UNITS.get(metric, "s"),
                        **s, "n_failed": n_failed, "n_excluded": len(members) - len(used) - n_failed, **quality})
    return out


def warn_quality(exp: str, summary: Sequence[dict]) -> list[str]:
    """Print (and return) one warning per group that mixes commits/options, has inconsistent counts
    or excluded runs."""
    seen, warnings = set(), []
    for row in summary:
        key = tuple((k, row.get(k)) for k in ("config", "dataset", "query", "format", "step"))
        if key in seen:
            continue
        seen.add(key)
        problems = []
        if row.get("homogeneous") is False:
            problems.append(f"mixes commits/options/params (commits: {row.get('git_commits')})")
        if row.get("counts_consistent") is False:
            problems.append("row counts differ between valid runs of the same dataset")
        if row.get("n_excluded"):
            problems.append(f"{row['n_excluded']} run(s) excluded ({row.get('flags_seen')})")
        if problems:
            where = {k: v for k, v in key if v is not None}
            msg = f"[{exp}] WARNING {where}: " + "; ".join(problems)
            print(msg)
            warnings.append(msg)
    return warnings


def lookup(summary: Iterable[dict], metric: str, **keys) -> dict | None:
    """First summary row with this metric and these key values, or None."""
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
    """Rows of a CSV file as dicts of strings."""
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
