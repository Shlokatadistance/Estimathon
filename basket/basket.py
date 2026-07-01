from dataclasses import dataclass
from datetime import datetime

from kalman.kalman import StockKalmanFilter


@dataclass(frozen=True)
class BasketConstituent:
    """
    Represents the individual constituent of a basket
    Previously handle fx conversion separately, now provided in
    fx_rate_to_base.
    """

    symbol: str
    quantity: float
    currency: str
    close_price: float
    fx_rate_to_base: float = 1.0


@dataclass
class BasketMetadata:
    basket_name: str
    basket_type: str
    source: str
    creation_size: int
    cash: float


@dataclass
class ETF:
    metadata: BasketMetadata
    constituents: list[BasketConstituent]


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
        cash: float = 0.0,
        price_noise: float = 1.0,
        volatility: float = 0.05,
    ) -> None:
        self.constituents = constituents
        self.cash = cash
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

        # Core price prediction logic
        # Calculate the price or take the smoothened price if live price is available
        # Use this data to calculate the basket price or the Kalman NAV
        
        for constituent in self.constituents:
            symbol = constituent.symbol
            price_filter = self.filters[symbol]
            # Check which consitutent is actually live and
            # decide whether to use the live price or the predicted price
            if symbol in live_prices:
                _, estimated_price = price_filter.step(live_prices[symbol])
            else:
                estimated_price = price_filter.predict()

            estimated_prices[symbol] = estimated_price

        basket_price = (
            sum(
                constituent.quantity
                * estimated_prices[constituent.symbol]
                * constituent.fx_rate_to_base
                for constituent in self.constituents
            )
            + self.cash
        )

        return BasketSnapshot(
            timestamp=timestamp,
            basket_price=basket_price,
            estimated_prices=estimated_prices,
            live_symbols=live_symbols,
        )

    def run(
        self, prices_by_time: dict[datetime, dict[str, float]]
    ) -> list[BasketSnapshot]:
        snapshots: list[BasketSnapshot] = []

        for timestamp in sorted(prices_by_time):
            snapshots.append(self.step(timestamp, prices_by_time[timestamp]))

        return snapshots
