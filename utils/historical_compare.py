from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from basket import BasketSnapshot


@dataclass(frozen=True)
class BasketComparison:
    timestamp: datetime
    basket_price: float
    reference_price: float
    difference: float
    percentage_difference: float


def compare_to_reference(
    basket_snapshots: list[BasketSnapshot],
    reference_prices: dict[datetime, float],
) -> list[BasketComparison]:
    """
    Compare estimated basket prices against a historical reference series.

    The reference could be an ETF price, portfolio NAV, or another basket
    calculation you want to benchmark against.
    """
    comparisons: list[BasketComparison] = []

    for snapshot in basket_snapshots:
        if snapshot.timestamp not in reference_prices:
            continue

        reference_price = reference_prices[snapshot.timestamp]
        difference = snapshot.basket_price - reference_price
        percentage_difference = difference / reference_price

        comparisons.append(
            BasketComparison(
                timestamp=snapshot.timestamp,
                basket_price=snapshot.basket_price,
                reference_price=reference_price,
                difference=difference,
                percentage_difference=percentage_difference,
            )
        )

    return comparisons
