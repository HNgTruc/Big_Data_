"""Experiment names, default execution order and groups (used by run_all, analyze_all, cleanup)."""
from __future__ import annotations

import importlib
from types import ModuleType

# Order: worker stop/start (scale_workers) runs last among the Spark experiments to limit risk;
# the host-only pandas baseline runs at the end.
ORDER = ("scale_data", "join_strategy", "skew", "format_compare", "cache", "scale_workers", "pandas_baseline")
GROUPS = {
    "spark": ORDER[:-1],
    "host": ("pandas_baseline",),
    "all": ORDER,
}


def resolve(exps: str | None, group: str, exclude: str | None) -> list[str]:
    """Experiments to handle, in ORDER. `exps` (comma list) wins over `group`."""
    chosen = [e.strip() for e in exps.split(",") if e.strip()] if exps else list(GROUPS[group])
    unknown = [e for e in chosen if e not in ORDER]
    if unknown:
        raise SystemExit(f"unknown experiment(s) {unknown}; available: {list(ORDER)}")
    skip = {e.strip() for e in (exclude or "").split(",") if e.strip()}
    return [e for e in ORDER if e in chosen and e not in skip]


def module(exp: str, part: str) -> ModuleType:
    """Import src.experiments.<exp>.<part> (part = run | analyze)."""
    return importlib.import_module(f"src.experiments.{exp}.{part}")
