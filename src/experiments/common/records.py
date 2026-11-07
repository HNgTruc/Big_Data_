"""Run records: one JSON file per repetition, plus helpers to gather provenance (git, manifest)."""
from __future__ import annotations

import json
import platform
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

from . import paths

RECORD_NAME = "run_record.json"
RECORD_SCHEMA_VERSION = 1
_IVY_RE = re.compile(r"resolution report :: resolve (\d+)ms :: artifacts dl (\d+)ms")


def now_iso() -> str:
    """Local time with UTC offset, second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_info(repo: Path = paths.REPO_ROOT) -> dict:
    """Commit hash and dirty flag. `results/` is excluded: the runner itself writes there."""
    def git(*args: str) -> str | None:
        try:
            res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return res.stdout if res.returncode == 0 else None

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--", ".", ":(exclude)results")
    dirty_paths = [line[3:] for line in (status or "").splitlines() if line.strip()]
    return {"commit": commit.strip() if commit else None,
            "dirty": bool(dirty_paths) if status is not None else None,
            "dirty_paths": dirty_paths[:50]}


def host_info() -> dict:
    """Platform and Python version of the machine running the controller."""
    return {"platform": platform.platform(), "python": platform.python_version(), "machine": platform.machine()}


def load_manifest(dataset: str, raw_dir: Path | None = None) -> dict | None:
    """data/raw/<dataset>/manifest.json as a dict, or None if missing."""
    path = (raw_dir or paths.RAW_DIR) / dataset / "manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_summary(manifest: dict | None) -> dict:
    """Seed and row counts of a generated dataset (None values when the manifest is missing)."""
    if not manifest:
        return {"seed": None, "skew": None, "rows_written": None, "raw_rows_total": None}
    rows = manifest.get("rows_written", {})
    return {"seed": manifest.get("params", {}).get("seed"), "skew": manifest.get("params", {}).get("skew"),
            "rows_written": rows, "raw_rows_total": sum(rows.values()) if rows else None}


def parse_ivy_times(log_text: str) -> dict:
    """Dependency resolution/download time printed by spark-submit --packages (ms), if present."""
    m = _IVY_RE.search(log_text)
    return {"resolve_ms": int(m.group(1)), "download_ms": int(m.group(2))} if m else {}


def write_record(run_dir: Path, record: dict) -> Path:
    """Write run_record.json into `run_dir` (created if needed); returns its path."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / RECORD_NAME
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_record(path: Path) -> dict:
    """Load one run record."""
    return json.loads(path.read_text(encoding="utf-8"))


def find_records(exp: str, metrics_root: Path | None = None) -> list[Path]:
    """All run records of an experiment, sorted by (config, rep)."""
    base = (metrics_root or paths.RESULTS_DIR / "metrics") / exp / "runs"
    found = list(base.glob(f"*/r*/{RECORD_NAME}"))

    def key(p: Path) -> tuple:
        rep = p.parent.name[1:]
        return (p.parent.parent.name, int(rep) if rep.isdigit() else 0)
    return sorted(found, key=key)


def load_records(exp: str, metrics_root: Path | None = None) -> list[dict]:
    """All run records of an experiment, sorted by (config, rep)."""
    return [read_record(p) for p in find_records(exp, metrics_root)]


def ok_records(records: Iterable[dict]) -> list[dict]:
    """Only the records whose status is ok."""
    return [r for r in records if r.get("status") == "ok"]
