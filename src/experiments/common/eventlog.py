"""Read Spark event logs and count the join operators of the plans that actually ran.

For every SQL execution the last plan reported wins: the plan at execution start, replaced by
each AQE update (`SparkListenerSQLAdaptiveExecutionUpdate`). The structured `sparkPlanInfo`
tree is used (not the text plan), so the AQE "Initial Plan" section is not double counted.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable

START = "org.apache.spark.sql.execution.ui.SparkListenerSQLExecutionStart"
AQE_UPDATE = "org.apache.spark.sql.execution.ui.SparkListenerSQLAdaptiveExecutionUpdate"
JOIN_NODES = ("SortMergeJoin", "BroadcastHashJoin", "ShuffledHashJoin", "BroadcastNestedLoopJoin",
              "CartesianProduct")


def final_plans(lines: Iterable[str]) -> dict[int, dict]:
    """executionId -> last sparkPlanInfo seen in the event log lines."""
    plans: dict[int, dict] = {}
    for line in lines:
        if START not in line and AQE_UPDATE not in line:
            continue  # cheap pre-filter: task events are the bulk of the file
        try:
            ev = json.loads(line)
        except ValueError:
            continue  # a truncated last line of an .inprogress log
        if ev.get("Event") in (START, AQE_UPDATE) and "sparkPlanInfo" in ev:
            plans[int(ev["executionId"])] = ev["sparkPlanInfo"]
    return plans


def count_nodes(plan: dict) -> Counter:
    """Count node names in a sparkPlanInfo tree (children are walked iteratively)."""
    counts: Counter = Counter()
    stack = [plan]
    while stack:
        node = stack.pop()
        name = str(node.get("nodeName", ""))
        counts[name] += 1
        if name == "AQEShuffleRead" and "skewed" in str(node.get("simpleString", "")):
            counts["AQEShuffleRead(skewed)"] += 1
        stack.extend(node.get("children") or [])
    return counts


def join_summary(plans: dict[int, dict]) -> dict:
    """Join operator counts over all executions. `SortMergeJoin(skew=true)` is AQE's skew-join split."""
    total: Counter = Counter()
    for plan in plans.values():
        total.update(count_nodes(plan))
    out = {name: total.get(name, 0) for name in JOIN_NODES}
    out["SortMergeJoin(skew=true)"] = total.get("SortMergeJoin(skew=true)", 0)
    out["AQEShuffleRead(skewed)"] = total.get("AQEShuffleRead(skewed)", 0)
    out["executions"] = len(plans)
    return out


def _part_index(path: Path) -> int:
    pieces = path.name.split("_")
    return int(pieces[1]) if len(pieces) > 1 and pieces[1].isdigit() else 0


def event_files(path: Path) -> list[Path]:
    """The plain-text event files of one application: the file itself, or the parts of a rolling
    log directory (eventlog_v2_<app>/events_<n>_<app>) in order. Compressed parts are rejected."""
    if path.is_dir():
        parts = sorted(path.glob("events_*"), key=_part_index)
    else:
        parts = [path]
    compressed = [p.name for p in parts if p.suffix in (".zstd", ".lz4", ".snappy", ".lzf")]
    if compressed:
        raise ValueError(f"compressed event log {compressed}; runs must use spark.eventLog.compress=false")
    return parts


def summarize_file(path: Path) -> dict:
    """Join summary of one application's event log (single file or rolling directory)."""
    def lines():
        for part in event_files(path):
            with part.open(encoding="utf-8", errors="replace") as fh:
                yield from fh
    return join_summary(final_plans(lines()))
