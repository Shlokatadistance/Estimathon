from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from kalman import StockKalmanFilter


@dataclass(frozen=True)
class BasketConstituent:
    symbol: str
    quantity: float
    fx_rate: float = 1.0


@dataclass(frozen=True)
class BasketSnapshot:
    timestamp: datetime
    basket_price: float
    estimated_prices: dict[str, float]
    live_symbols: set[str]


class HistoricalBasketPricer:
    """
    Prices a basket through time.

    At each timestamp:
        - live constituents are corrected with their latest market price
        - missing constituents are predicted forward by their own Kalman filter
        - the basket price is the sum of quantity * estimated_price * fx_rate
    """

    def __init__(
        self,
        constituents: list[BasketConstituent],
        initial_prices: dict[str, float],
        price_noise: float = 1.0,
        volatility: float = 0.05,
    ) -> None:
        self.constituents = constituents
        self.filters = {
            constituent.symbol: StockKalmanFilter(
                initial_price=initial_prices[constituent.symbol],
                price_noise=price_noise,
                volatility=volatility,
            )
            for constituent in constituents
        }

    def step(
        self,
        timestamp: datetime,
        live_prices: dict[str, float],
    ) -> BasketSnapshot:
        estimated_prices: dict[str, float] = {}
        live_symbols = set(live_prices)

        for constituent in self.constituents:
            symbol = constituent.symbol
            price_filter = self.filters[symbol]

            if symbol in live_prices:
                _, estimated_price = price_filter.step(live_prices[symbol])
            else:
                estimated_price = price_filter.predict()

            estimated_prices[symbol] = estimated_price

        basket_price = sum(
            constituent.quantity
            * estimated_prices[constituent.symbol]
            * constituent.fx_rate
            for constituent in self.constituents
        )

        return BasketSnapshot(
            timestamp=timestamp,
            basket_price=basket_price,
            estimated_prices=estimated_prices,
            live_symbols=live_symbols,
        )

    def run(self, prices_by_time: dict[datetime, dict[str, float]]) -> list[BasketSnapshot]:
        snapshots: list[BasketSnapshot] = []

        for timestamp in sorted(prices_by_time):
            snapshots.append(self.step(timestamp, prices_by_time[timestamp]))

        return snapshots
