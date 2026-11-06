"""Chunk-friendly file writers (CSV / JSON lines / Parquet)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def append_csv(df: pd.DataFrame, path: Path, first: bool) -> None:
    df.to_csv(path, mode="w" if first else "a", header=first, index=False, lineterminator="\n")


def append_jsonl(df: pd.DataFrame, path: Path, first: bool) -> None:
    text = df.to_json(orient="records", lines=True).replace("\\/", "/")
    with open(path, "w" if first else "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text.rstrip("\n") + "\n")


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    df.to_parquet(path, index=False)
