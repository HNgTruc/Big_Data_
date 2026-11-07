"""Descriptive statistics and scaling metrics (standard library only)."""
from __future__ import annotations

import math
import statistics
from typing import Iterable, Sequence


def summarize(values: Iterable[float | None]) -> dict:
    """n, mean, sample std (n-1; None when n < 2), min, max of the non-missing values."""
    xs = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not xs:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    return {"n": len(xs), "mean": statistics.fmean(xs), "std": statistics.stdev(xs) if len(xs) > 1 else None,
            "min": min(xs), "max": max(xs)}


def speedup(t_base: float | None, t_new: float | None) -> float | None:
    """S = T_base / T_new (e.g. T(1 worker) / T(2 workers)); None if either value is missing or 0."""
    if not t_base or not t_new:
        return None
    return t_base / t_new


def efficiency(s: float | None, resource_ratio: float) -> float | None:
    """E = S / p, where p is the ratio of resources (2 workers vs 1 -> p = 2)."""
    if s is None or resource_ratio <= 0:
        return None
    return s / resource_ratio


def throughput(rows: float | None, seconds: float | None) -> float | None:
    """Rows per second; None if a value is missing or the time is not positive."""
    if rows is None or not seconds or seconds <= 0:
        return None
    return rows / seconds


def ratio(a: float | None, b: float | None) -> float | None:
    """a / b, or None if a is missing or b is missing/zero."""
    if a is None or not b:
        return None
    return a / b


def relative_to_first(values: Sequence[float | None]) -> list[float | None]:
    """Each value divided by the first one (scale-out tables: data ratio, time ratio)."""
    base = values[0] if values else None
    return [ratio(v, base) for v in values]
