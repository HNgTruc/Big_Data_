"""Constants and run configuration for the synthetic data generator."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ORDER_START = date(2024, 1, 1)
ORDER_DAYS = 731  # 2024-01-01 .. 2025-12-31
SIGNUP_START = date(2020, 1, 1)
SIGNUP_DAYS = 1461  # 2020-01-01 .. 2023-12-31

STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]
STATUS_WEIGHTS = [0.05, 0.10, 0.15, 0.60, 0.10]
PAYMENT_METHODS = ["cod", "card", "bank_transfer", "e_wallet"]
EVENT_TYPES = ["view", "add_to_cart", "purchase"]
EVENT_WEIGHTS = [0.80, 0.15, 0.05]
REGIONS = ["north", "central", "south", "highland", "mekong", "southeast"]
CATEGORIES = [
    "electronics", "fashion", "home", "beauty",
    "sports", "books", "toys", "grocery",
]
QUANTITIES = [1, 2, 3, 4, 5]
QUANTITY_WEIGHTS = [0.50, 0.25, 0.12, 0.08, 0.05]

# Bad (non-ISO) formats injected as "wrong date format" defects.
BAD_DATE_FORMATS = ["%d/%m/%Y", "%Y%m%d", "%d-%m-%Y"]
BAD_TIME_FORMATS = ["%d/%m/%Y %H:%M:%S", "%Y%m%d%H%M%S"]

MAX_DIRTY_RATE = 0.25  # three disjoint defect masks per table must fit in [0, 1]


@dataclass(frozen=True)
class Config:
    """Generation parameters. Output is a pure function of this object."""

    orders: int
    seed: int = 42
    chunk_size: int = 500_000
    dirty_rate: float = 0.02
    skew: bool = False
    hot_products: int = 10
    hot_share: float = 0.5
    items_mean: float = 2.0
    items_max: int = 10
    customers: int | None = None
    products: int | None = None
    events: int | None = None

    def __post_init__(self) -> None:
        if self.orders <= 0 or self.chunk_size <= 0:
            raise ValueError("orders and chunk_size must be positive")
        if not 0.0 <= self.dirty_rate <= MAX_DIRTY_RATE:
            raise ValueError(f"dirty_rate must be in [0, {MAX_DIRTY_RATE}]")
        if not 0.0 <= self.hot_share <= 1.0:
            raise ValueError("hot_share must be in [0, 1]")
        if self.items_mean < 1.0 or self.items_max < 1:
            raise ValueError("items_mean and items_max must be >= 1")
        if not 1 <= self.hot_products <= self.n_products:
            raise ValueError("hot_products must be in [1, number of products]")

    @property
    def n_customers(self) -> int:
        return self.customers or max(10, self.orders // 10)

    @property
    def n_products(self) -> int:
        return self.products or max(100, self.orders // 250)

    @property
    def n_events(self) -> int:
        return self.events or self.orders
