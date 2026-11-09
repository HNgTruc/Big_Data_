"""Draw the system architecture diagram used in chapter 4 of the report.

Input: none (the components mirror infra/docker-compose.yml and src/etl/pipeline.py).
Output: a PNG at --output, 16 cm wide at 200 dpi, so font sizes below are the printed sizes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # file output only; must not depend on a display

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "report" / "figures" / "kien-truc.png"

# The axes use centimetres as data units, so layout numbers equal printed distances.
WIDTH_CM = 16.0
HEIGHT_CM = 13.7
DPI = 200
CM_PER_INCH = 2.54

# Both fonts cover Vietnamese; DejaVu Sans ships with matplotlib for machines without Arial.
FONT_FAMILY = ["Arial", "DejaVu Sans"]
TITLE_PT = 9.0
BODY_PT = 8.0

INK = "#111111"
HOST_EDGE = "#444444"
DOCKER_FILL = "#F4F4F4"
SPARK_FILL = "#E8F0FA"
SPARK_EDGE = "#2F5D9B"
MINIO_FILL = "#FCEFDF"
MINIO_EDGE = "#A85E17"


def _frame(ax: Axes, x0: float, y0: float, x1: float, y1: float, *, fill: str, edge: str,
           dashed: bool = False, zorder: int = 1) -> None:
    """Draw a rounded rectangle given its corners, in centimetres."""
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.1",
        facecolor=fill, edgecolor=edge, linewidth=1.0, linestyle="--" if dashed else "-", zorder=zorder,
    ))


def _box(ax: Axes, x0: float, y0: float, x1: float, y1: float, title: str, body: str = "",
         *, edge: str = HOST_EDGE, zorder: int = 3) -> None:
    """Draw a white component box with a bold title and optional body lines, centred."""
    _frame(ax, x0, y0, x1, y1, fill="white", edge=edge, zorder=zorder)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if not body:
        ax.text(cx, cy, title, ha="center", va="center", fontsize=TITLE_PT, fontweight="bold",
                color=INK, zorder=zorder + 1)
        return
    lines = body.count("\n") + 1
    line_cm = 0.36  # one 8 pt line with spacing
    block_top = cy + (0.40 + lines * line_cm) / 2
    ax.text(cx, block_top, title, ha="center", va="top", fontsize=TITLE_PT, fontweight="bold",
            color=INK, zorder=zorder + 1)
    ax.text(cx, block_top - 0.42, body, ha="center", va="top", fontsize=BODY_PT, color=INK,
            linespacing=1.15, zorder=zorder + 1)


def _arrow(ax: Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    """Draw a straight arrow above all frames and boxes."""
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, linewidth=1.1,
                                 color=INK, shrinkA=0, shrinkB=0, zorder=6))


def _label(ax: Axes, x: float, y: float, text: str, *, ha: str = "left", bold: bool = False,
           size: float = BODY_PT) -> None:
    """Place free text (frame title or arrow label)."""
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.1, zorder=7)


def build_figure() -> Figure:
    """Build the architecture diagram: host, then MinIO (storage), Spark (processing), results."""
    plt.rcParams["font.family"] = FONT_FAMILY
    fig = plt.figure(figsize=(WIDTH_CM / CM_PER_INCH, HEIGHT_CM / CM_PER_INCH), dpi=DPI)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, WIDTH_CM)
    ax.set_ylim(0, HEIGHT_CM)
    ax.axis("off")

    # Nested environment frames.
    _frame(ax, 0.06, 0.06, 15.94, 13.64, fill="white", edge=HOST_EDGE)
    _label(ax, 15.7, 13.28, "Máy thí nghiệm (16 GB RAM)", ha="right", bold=True, size=TITLE_PT)
    _frame(ax, 0.35, 1.55, 15.65, 11.45, fill=DOCKER_FILL, edge=HOST_EDGE, dashed=True)
    _label(ax, 15.45, 11.15, "Docker Desktop / WSL2 (giới hạn 6 GB)", ha="right", bold=True, size=TITLE_PT)

    # Host: simulated data generation, then upload.
    _box(ax, 0.3, 12.0, 4.5, 13.4, "Bộ sinh dữ liệu mô phỏng", "src/data_generation\nseed 42")
    _box(ax, 5.15, 12.0, 8.75, 13.4, "data/raw/ trên host", "CSV, Parquet, JSON lines")
    _arrow(ax, (4.5, 12.7), (5.15, 12.7))
    _label(ax, 4.825, 12.92, "ghi", ha="center")
    _arrow(ax, (5.35, 12.0), (5.35, 10.2))
    _label(ax, 5.53, 11.72, "upload bằng mc cp")

    # Storage layer.
    _frame(ax, 0.6, 8.35, 15.4, 10.85, fill=MINIO_FILL, edge=MINIO_EDGE, zorder=2)
    _label(ax, 15.2, 10.53, "MinIO, bucket bigdata (S3 API :9000, console :9001)", ha="right", bold=True,
           size=TITLE_PT)
    _box(ax, 0.9, 8.55, 5.6, 10.2, "raw/", "CSV, Parquet, JSON lines", edge=MINIO_EDGE)
    _box(ax, 5.95, 8.55, 10.45, 10.2, "curated/", "Parquet: bảng sạch\nvà agg_*", edge=MINIO_EDGE)
    _box(ax, 10.8, 8.55, 15.1, 10.2, "quarantine/", "Parquet: bản ghi lỗi\nkèm reject_reason", edge=MINIO_EDGE)

    # Processing layer.
    _frame(ax, 0.6, 1.75, 15.4, 7.35, fill=SPARK_FILL, edge=SPARK_EDGE, zorder=2)
    _label(ax, 0.9, 7.0, "Spark 4.0.0 standalone", bold=True, size=TITLE_PT)
    _frame(ax, 0.9, 4.45, 15.1, 6.6, fill="white", edge=SPARK_EDGE, zorder=3)
    _label(ax, 8.0, 6.28, "Executor đọc raw/, làm sạch, join, tổng hợp, rồi ghi curated/ và quarantine/", ha="center")
    for x0, name in ((1.1, "Worker 1"), (8.15, "Worker 2")):
        _frame(ax, x0, 4.6, x0 + 6.75, 5.95, fill=SPARK_FILL, edge=SPARK_EDGE, zorder=4)
        _label(ax, x0 + 0.2, 5.27, f"{name}\n2 lõi, 2 GB")
        _box(ax, x0 + 2.9, 4.75, x0 + 6.55, 5.8, "Executor", "heap 1 GB", edge=SPARK_EDGE, zorder=5)
    _box(ax, 1.2, 1.95, 6.6, 3.55, "Master", "cụm :7077, UI :8090", edge=SPARK_EDGE)
    _box(ax, 8.6, 1.95, 14.8, 3.55, "Driver",
         "docker compose run\nspark-submit src/etl/etl_job.py", edge=SPARK_EDGE)

    # Data flows between layers: raw is read, curated and quarantine are written.
    _arrow(ax, (5.35, 8.55), (5.35, 6.6))
    _label(ax, 5.53, 7.85, "đọc qua S3A")
    _arrow(ax, (8.2, 6.6), (8.2, 8.55))
    _label(ax, 8.38, 7.85, "ghi qua S3A")
    _arrow(ax, (12.95, 6.6), (12.95, 8.55))
    _label(ax, 13.13, 7.85, "ghi qua S3A")

    # Control flows: the master grants executors, the driver sends them tasks.
    _arrow(ax, (8.6, 2.75), (6.6, 2.75))
    _label(ax, 7.6, 3.15, "nộp ứng dụng\n(:7077)", ha="center")
    _arrow(ax, (3.9, 3.55), (3.9, 4.45))
    _label(ax, 4.08, 4.0, "cấp executor")
    _arrow(ax, (11.7, 3.55), (11.7, 4.45))
    _label(ax, 11.88, 4.0, "giao task")

    # Results reach the host through the bind mount and the captured driver output.
    _box(ax, 8.6, 0.3, 14.8, 1.15, "results/ trên host")
    _arrow(ax, (11.7, 1.95), (11.7, 1.15))
    _label(ax, 11.88, 1.33, "metrics, log")
    return fig


def main() -> None:
    """Parse --output, draw the diagram and save the PNG."""
    parser = argparse.ArgumentParser(description="Draw the report's architecture diagram.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PNG path to write")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    fig.savefig(args.output, dpi=DPI)
    plt.close(fig)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
