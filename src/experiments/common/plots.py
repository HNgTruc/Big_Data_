"""Matplotlib helpers (imported lazily: the runners must work without matplotlib)."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence


def pyplot():
    """Return matplotlib.pyplot with the non-interactive Agg backend, or None if not installed."""
    try:
        import matplotlib
    except ImportError:
        print("matplotlib is not installed: figures skipped (pip install -r src/experiments/requirements.txt)")
        return None
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _num(v) -> float:
    return float(v) if v not in (None, "") else float("nan")


def bars(plt, ax, labels: Sequence[str], means: Sequence, stds: Sequence, ns: Sequence,
         offset: float = 0.0, width: float = 0.8, label: str | None = None, color=None):
    """Bar chart with std error bars and `n=` written above each bar."""
    xs = [i + offset for i in range(len(labels))]
    m = [_num(v) for v in means]
    s = [0.0 if v in (None, "") else float(v) for v in stds]
    ax.bar(xs, m, width, yerr=s, capsize=4, label=label, color=color)
    for x, mv, sv, n in zip(xs, m, s, ns):
        if mv == mv:  # not NaN
            ax.annotate(f"n={n}", (x, mv + sv), textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=8)
    return xs


def grouped_bars(plt, ax, groups: Sequence[str], series: dict[str, tuple[Sequence, Sequence, Sequence]]):
    """series: name -> (means, stds, ns), each aligned with `groups`."""
    k = max(len(series), 1)
    width = 0.8 / k
    for i, (name, (means, stds, ns)) in enumerate(series.items()):
        bars(plt, ax, groups, means, stds, ns, offset=(i - (k - 1) / 2) * width, width=width, label=name)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.legend()


def save(plt, fig, path: Path, source: str) -> Path:
    """Save the figure with a footnote naming the source CSV."""
    fig.text(0.01, 0.005, f"Nguồn: {source}", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"figure: {path}")
    return path


def _lookup(summary, metric: str, config: str) -> dict:
    for row in summary:
        if row.get("metric") == metric and row.get("config") == config:
            return row
    return {}


def etl_config_figure(summary: Sequence[dict], configs: Sequence[str], path: Path, source: str,
                      title: str, stages: Sequence[str]) -> Path | None:
    """Left: processing time per configuration (mean ± std, n). Right: mean time per stage (stacked)."""
    plt = pyplot()
    if plt is None or not configs:
        return None
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    rows = [_lookup(summary, "processing_seconds_total", c) for c in configs]
    bars(plt, axes[0], configs, [r.get("mean") for r in rows], [r.get("std") for r in rows],
         [r.get("n") for r in rows])
    axes[0].set_xticks(range(len(configs)))
    axes[0].set_xticklabels(configs, rotation=20, ha="right")
    axes[0].set_ylabel("Thời gian xử lý (s)")
    axes[0].set_title(title)
    bottom = [0.0] * len(configs)
    for stage in stages:
        vals = [_lookup(summary, f"stage_{stage}", c).get("mean") or 0.0 for c in configs]
        axes[1].bar(range(len(configs)), vals, bottom=bottom, label=stage)
        bottom = [b + v for b, v in zip(bottom, vals)]
    axes[1].set_xticks(range(len(configs)))
    axes[1].set_xticklabels(configs, rotation=20, ha="right")
    axes[1].set_ylabel("Thời gian trung bình (s)")
    axes[1].set_title("Theo giai đoạn (trung bình)")
    axes[1].legend(fontsize=8)
    return save(plt, fig, path, source)
