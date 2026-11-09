"""Draw the comparison of the three executed plans for the clean order_items step (chapter 7).

Input: none. Plan structure mirrors results/logs/skew/plan_query4.txt (from the Spark event logs).
Numbers are the ones visible on screenshots 07, 09, 10 and 11 in results/logs/screenshots/.
Output: a PNG at --output, 16 cm wide at 200 dpi, in the style of draw_architecture.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from draw_architecture import (BODY_PT, CM_PER_INCH, DPI, FONT_FAMILY, HOST_EDGE, INK, SPARK_EDGE, SPARK_FILL, TITLE_PT,
                               WIDTH_CM, _arrow, _frame, _label)
from matplotlib.axes import Axes
from matplotlib.figure import Figure

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "report" / "figures" / "ke-hoach-so-sanh.png"

HEIGHT_CM = 13.5
COMMON_FILL = "#F4F4F4"
ACCENT_EDGE = "#C25A00"
ACCENT_FILL = "#FCEFDF"
COLUMN_WIDTH = 4.95
COLUMN_LEFT = (0.25, 5.525, 10.8)
COLUMN_TOP, COLUMN_BOTTOM = 11.1, 3.4
BUS_Y = 11.5

# Vertical slots shared by the columns, so the same step lines up across configurations.
EXCHANGE = (7.8, 8.6)
AQE_READ = (6.6, 7.4)
SORT = (5.4, 6.0)
JOIN = (4.0, 4.8)


def _node(ax: Axes, x0: float, x1: float, y: tuple[float, float], title: str, body: str = "",
          *, accent: bool = False) -> None:
    """Draw a plan node; accent marks the node that differs between configurations."""
    fill, edge = (ACCENT_FILL, ACCENT_EDGE) if accent else ("white", SPARK_EDGE)
    _frame(ax, x0, y[0], x1, y[1], fill=fill, edge=edge, zorder=3)
    cx, cy = (x0 + x1) / 2, (y[0] + y[1]) / 2
    weight = "bold" if accent or body else "normal"
    if body:
        ax.text(cx, cy + 0.17, title, ha="center", va="center", fontsize=BODY_PT, fontweight=weight, color=INK, zorder=4)
        ax.text(cx, cy - 0.17, body, ha="center", va="center", fontsize=BODY_PT, color=INK, zorder=4)
    else:
        ax.text(cx, cy, title, ha="center", va="center", fontsize=BODY_PT, fontweight=weight, color=INK,
                linespacing=1.1, zorder=4)


def _column(ax: Axes, left: float, title: str, subtitle: str, facts: tuple[str, str, str]) -> None:
    """Draw one configuration: frame, heading and the values measured for it."""
    _frame(ax, left, COLUMN_BOTTOM, left + COLUMN_WIDTH, COLUMN_TOP, fill=SPARK_FILL, edge=SPARK_EDGE, zorder=2)
    cx = left + COLUMN_WIDTH / 2
    _label(ax, cx, 10.78, title, ha="center", bold=True, size=TITLE_PT)
    _label(ax, cx, 10.42, subtitle, ha="center")
    for y, fact in zip((9.95, 9.6, 9.25), facts):
        _label(ax, cx, y, fact, ha="center")
    _arrow(ax, (cx, JOIN[0]), (cx, 2.95))


def _shuffle_flow(ax: Axes, left: float, *, skew: bool) -> None:
    """Draw the sort-merge join on product_id, with or without AQE's skew handling."""
    main_x0, main_x1 = left + 0.15, left + 3.15
    side_x0, side_x1 = left + 3.35, left + COLUMN_WIDTH - 0.15
    main_cx, side_cx = (main_x0 + main_x1) / 2, (side_x0 + side_x1) / 2

    _node(ax, main_x0, main_x1, EXCHANGE, "Exchange", "64 phân vùng")
    _node(ax, side_x0, side_x1, EXCHANGE, "products")
    if skew:
        _arrow(ax, (main_cx, EXCHANGE[0]), (main_cx, AQE_READ[1]))
        _node(ax, main_x0, main_x1, AQE_READ, "AQEShuffleRead", "skewed, 49 lần tách", accent=True)
        _arrow(ax, (main_cx, AQE_READ[0]), (main_cx, SORT[1]))
    else:
        _arrow(ax, (main_cx, EXCHANGE[0]), (main_cx, SORT[1]))
    _node(ax, main_x0, main_x1, SORT, "Sort")
    _arrow(ax, (side_cx, EXCHANGE[0]), (side_cx, SORT[1]))
    _node(ax, side_x0, side_x1, SORT, "Sort")
    _arrow(ax, (main_cx, SORT[0]), (main_cx, JOIN[1]))
    _arrow(ax, (side_cx, SORT[0]), (side_cx, JOIN[1]))
    title = "SortMergeJoin(skew=true)" if skew else "SortMergeJoin"
    _node(ax, main_x0, side_x1, JOIN, title, "theo product_id", accent=skew)


def _broadcast_flow(ax: Axes, left: float) -> None:
    """Draw the default plan: products is broadcast, so the skewed key is not shuffled."""
    main_x0, main_x1 = left + 0.15, left + 1.8
    side_x0, side_x1 = left + 1.95, left + COLUMN_WIDTH - 0.15
    main_cx, side_cx = (main_x0 + main_x1) / 2, (side_x0 + side_x1) / 2

    _node(ax, side_x0, side_x1, EXCHANGE, "products")
    _arrow(ax, (side_cx, EXCHANGE[0]), (side_cx, AQE_READ[1]))
    _node(ax, side_x0, side_x1, AQE_READ, "BroadcastExchange", accent=True)
    _arrow(ax, (side_cx, AQE_READ[0]), (side_cx, JOIN[1]))
    _arrow(ax, (main_cx, EXCHANGE[1]), (main_cx, JOIN[1]))
    _label(ax, main_cx + 0.1, 6.0, "không\nshuffle")
    _node(ax, main_x0, side_x1, JOIN, "BroadcastHashJoin", "theo product_id", accent=True)


def build_figure() -> Figure:
    """Build the three-column comparison: shared steps above and below, the join in the middle."""
    plt.rcParams["font.family"] = FONT_FAMILY
    fig = plt.figure(figsize=(WIDTH_CM / CM_PER_INCH, HEIGHT_CM / CM_PER_INCH), dpi=DPI)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, WIDTH_CM)
    ax.set_ylim(0, HEIGHT_CM)
    ax.axis("off")

    # Steps before the join on product_id, shared by the three plans.
    _frame(ax, 0.25, 11.9, 15.75, 13.35, fill=COMMON_FILL, edge=HOST_EDGE, dashed=True, zorder=1)
    _label(ax, 0.45, 13.05, "Chung cho cả ba cấu hình", bold=True, size=TITLE_PT)
    _frame(ax, 0.55, 12.1, 15.45, 12.75, fill="white", edge=SPARK_EDGE, zorder=3)
    ax.text(8.0, 12.425, "Scan csv: order_items.csv  →  Bỏ trùng theo (order_id, line_no): HashAggregate",
            ha="center", va="center", fontsize=BODY_PT, color=INK, zorder=4)

    centers = [left + COLUMN_WIDTH / 2 for left in COLUMN_LEFT]
    ax.plot((8.0, 8.0), (11.9, BUS_Y), color=INK, linewidth=1.1, zorder=5)
    ax.plot((centers[0], centers[-1]), (BUS_Y, BUS_Y), color=INK, linewidth=1.1, zorder=5)
    for cx in centers:
        _arrow(ax, (cx, BUS_Y), (cx, COLUMN_TOP))

    _column(ax, COLUMN_LEFT[0], "(a) skew_shuffle_noaqe", "ép shuffle, tắt AQE",
            ("stage đọc shuffle: 64 task", "đọc lớn nhất 15,5 MiB, lâu nhất 0,5 s", "ảnh 09, lần r1"))
    _shuffle_flow(ax, COLUMN_LEFT[0], skew=False)

    _column(ax, COLUMN_LEFT[1], "(b) skew_shuffle_aqe", "ép shuffle, bật AQE",
            ("stage đọc shuffle: 104 task", "đọc lớn nhất 1,9 MiB, lâu nhất 0,2 s", "ảnh 10, lần r1"))
    _shuffle_flow(ax, COLUMN_LEFT[1], skew=True)

    _column(ax, COLUMN_LEFT[2], "(c) skew_auto_aqe", "auto, bật AQE",
            ("join ra 10.000.351 dòng", "bỏ trùng có spill 1312,3 MiB", "ảnh 11, lần r1"))
    _broadcast_flow(ax, COLUMN_LEFT[2])

    # Steps after the join on product_id, shared by the three plans.
    _frame(ax, 0.25, 0.15, 15.75, 2.95, fill=COMMON_FILL, edge=HOST_EDGE, dashed=True, zorder=1)
    _label(ax, 0.45, 2.65, "Chung cho cả ba cấu hình", bold=True, size=TITLE_PT)
    _node(ax, 0.55, 15.45, (1.5, 2.2), "Exchange theo order_id (64 phân vùng ở (a), (b); 8 phân vùng ở (c))  →  Sort")
    _arrow(ax, (8.0, 1.5), (8.0, 1.05))
    _node(ax, 0.55, 15.45, (0.35, 1.05), "SortMergeJoin theo order_id với orders  →  Filter  →  Project  →  WriteFiles: order_items")
    return fig


def main() -> None:
    """Parse --output, draw the diagram and save the PNG."""
    parser = argparse.ArgumentParser(description="Draw the plan comparison for chapter 7.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PNG path to write")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    fig.savefig(args.output, dpi=DPI)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
