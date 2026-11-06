"""CLI: generate the synthetic e-commerce dataset into data/raw/.

Run from the repository root:
    python -m src.data_generation.generate --orders 500000
"""
from __future__ import annotations

import argparse
import json
import logging
import platform
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import pyarrow

from . import dirty, tables, writer
from .config import Config

LOG = logging.getLogger("data_generation")
REPO_ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "products": "products.parquet",
    "web_events": "web_events.jsonl",
}


def _chunks(total: int, size: int) -> Iterator[tuple[int, int]]:
    """Yield (first_row_index, rows) pairs covering `total` rows."""
    for start in range(0, total, size):
        yield start, min(size, total - start)


def default_out_dir(cfg: Config) -> Path:
    n = cfg.orders
    label = f"{n // 1_000_000}m" if n % 1_000_000 == 0 else f"{n // 1000}k" if n % 1000 == 0 else str(n)
    return REPO_ROOT / "data" / "raw" / f"orders_{label}{'_skew' if cfg.skew else ''}"


def generate(cfg: Config, out_dir: Path) -> dict:
    """Write all tables under `out_dir` and return the manifest (also saved as manifest.json)."""
    start = time.perf_counter()
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg.seed)
    rows: Counter = Counter()
    defects: dict[str, Counter] = {t: Counter() for t in FILES}

    def emit(table: str, df: pd.DataFrame, injected: dict, first: bool) -> None:
        path = out_dir / FILES[table]
        if table == "web_events":
            writer.append_jsonl(df, path, first)
        else:
            writer.append_csv(df, path, first)
        rows[table] += len(df)
        defects[table].update(injected)

    products = tables.build_products(rng, cfg)
    writer.write_parquet(products, out_dir / FILES["products"])
    rows["products"] = len(products)

    customers, injected = dirty.dirty_customers(tables.build_customers(rng, cfg), rng, cfg)
    emit("customers", customers, injected, first=True)

    prices = products["list_price"].to_numpy()
    for i, (first_row, n) in enumerate(_chunks(cfg.orders, cfg.chunk_size)):
        clean_orders = tables.build_orders_chunk(rng, cfg, first_row + 1, n)
        clean_items = tables.build_items_chunk(rng, cfg, clean_orders["order_id"].to_numpy(), prices)
        orders, o_inj = dirty.dirty_orders(clean_orders, rng, cfg)
        items, i_inj = dirty.dirty_items(clean_items, rng, cfg)
        emit("orders", orders, o_inj, first=i == 0)
        emit("order_items", items, i_inj, first=i == 0)
        LOG.info("orders chunk %d: %d orders, %d items", i, n, len(clean_items))

    for i, (first_row, n) in enumerate(_chunks(cfg.n_events, cfg.chunk_size)):
        events, injected = dirty.dirty_events(tables.build_events_chunk(rng, cfg, first_row + 1, n), rng, cfg)
        emit("web_events", events, injected, first=i == 0)
        LOG.info("events chunk %d: %d events", i, n)

    manifest = {
        "params": {**asdict(cfg), "n_customers": cfg.n_customers, "n_products": cfg.n_products,
                   "n_events": cfg.n_events},
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "pyarrow": pyarrow.__version__},
        "rows_written": dict(rows),
        "defects_injected": {t: dict(c) for t, c in defects.items()},
        "bytes": {t: (out_dir / f).stat().st_size for t, f in FILES.items()},
        "elapsed_seconds": round(time.perf_counter() - start, 2),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--orders", type=int, required=True, help="number of orders (0.5M/1M/2.5M/5M planned)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--chunk-size", type=int, default=500_000, help="orders (or events) per in-memory chunk")
    p.add_argument("--dirty-rate", type=float, default=0.02, help="share of rows per defect type")
    p.add_argument("--skew", action="store_true", help="concentrate product picks on a few hot products")
    p.add_argument("--hot-products", type=int, default=10)
    p.add_argument("--hot-share", type=float, default=0.5)
    p.add_argument("--items-mean", type=float, default=2.0)
    p.add_argument("--items-max", type=int, default=10)
    p.add_argument("--customers", type=int, help="default: orders // 10")
    p.add_argument("--products", type=int, help="default: max(100, orders // 250)")
    p.add_argument("--events", type=int, help="default: same as orders")
    p.add_argument("--out", type=Path, help="output dir (default: data/raw/orders_<size>[_skew])")
    p.add_argument("--overwrite", action="store_true", help="allow writing into a non-empty output dir")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    cfg = Config(orders=args.orders, seed=args.seed, chunk_size=args.chunk_size,
                 dirty_rate=args.dirty_rate, skew=args.skew, hot_products=args.hot_products,
                 hot_share=args.hot_share, items_mean=args.items_mean, items_max=args.items_max,
                 customers=args.customers, products=args.products, events=args.events)
    out_dir = args.out or default_out_dir(cfg)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite:
        LOG.error("%s is not empty; pass --overwrite to replace it", out_dir)
        return 1
    manifest = generate(cfg, out_dir)
    LOG.info("done in %.1fs -> %s rows=%s", manifest["elapsed_seconds"], out_dir, manifest["rows_written"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
