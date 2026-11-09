"""Prepare evidence screenshots for the report: crop, add a uniform border, set the printed width.

Input: results/logs/screenshots/*.png, which stay untouched.
Output: report/figures/screenshots/*.png. Pixels inside the crop are never changed, and every output
is compared with its source region after writing, because these images are experimental evidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageChops, ImageOps

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "results" / "logs" / "screenshots"
DEFAULT_OUTPUT = REPO_ROOT / "report" / "figures" / "screenshots"

BORDER_PX = 2
BORDER_COLOR = (166, 166, 166)
CM_PER_INCH = 2.54
FULL_WIDTH_CM = 16.0  # text block width of the report


class Crop(NamedTuple):
    """Region of the source image to keep, and its width on the printed page."""

    box: tuple[int, int, int, int]  # left, top, right, bottom in source pixels
    width_cm: float = FULL_WIDTH_CM


# Each box only removes UI chrome or empty space; every value quoted in the report stays visible.
CROPS: dict[str, Crop] = {
    "01_spark_master_workers.png": Crop((0, 0, 1556, 624)),
    "02_minio_bucket_root.png": Crop((0, 0, 1550, 470)),
    "03_minio_raw_orders_5m.png": Crop((0, 0, 1554, 530)),
    "04_minio_curated_orders_5m.png": Crop((0, 0, 1552, 610)),
    "05_minio_quarantine_orders_5m.png": Crop((0, 0, 1530, 440)),
    "06_history_app_list.png": Crop((10, 7, 1886, 923)),
    "07_skew_shuffle_aqe_sql_plan.png": Crop((0, 3, 1110, 930)),
    "08_skew_shuffle_noaqe_sql_plan.png": Crop((0, 2, 1275, 929)),
    "09_skew_shuffle_noaqe_stage_tasks.png": Crop((3, 0, 1515, 195)),
    "10_skew_shuffle_aqe_stage_tasks.png": Crop((15, 5, 1515, 205)),
    "11_skew_auto_aqe_sql_plan.png": Crop((0, 0, 443, 612), width_cm=8.5),
    "12_job_dag.png": Crop((3, 0, 690, 495), width_cm=12.0),
    "13_executors.png": Crop((15, 11, 1525, 328)),
}


def prepare(source: Path, target: Path, crop: Crop) -> None:
    """Write one framed copy of source to target, then confirm its pixels match the source crop."""
    original = Image.open(source).convert("RGB")
    region = original.crop(crop.box)
    framed = ImageOps.expand(region, border=BORDER_PX, fill=BORDER_COLOR)
    dpi = framed.width / (crop.width_cm / CM_PER_INCH)
    framed.save(target, dpi=(dpi, dpi), optimize=True)

    written = Image.open(target).convert("RGB")
    inner = written.crop((BORDER_PX, BORDER_PX, written.width - BORDER_PX, written.height - BORDER_PX))
    if ImageChops.difference(inner, region).getbbox() is not None:
        raise RuntimeError(f"{target.name}: pixels differ from the source crop")


def main() -> None:
    """Parse --source and --output, then prepare every screenshot listed in CROPS."""
    parser = argparse.ArgumentParser(description="Crop and frame screenshots for the report.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="folder of original screenshots")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="folder for the framed copies")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, crop in CROPS.items():
        prepare(args.source / name, args.output / name, crop)
        print(f"{name}: crop {crop.box}, printed width {crop.width_cm} cm, pixels match source")


if __name__ == "__main__":
    main()
