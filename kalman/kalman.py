from dataclasses import dataclass


@dataclass
class StockKalmanFilter:
    """
    Simple Kalman filter for smoothing and predicting a stock price series.

    State:
        price = current price estimate
        trend = hidden price movement per time step
    """

    initial_price: float # Initial price
    initial_trend: float = 0.0 # Initial trend, i.e. initial price change per time step. This is the starting guess
    dt: float = 1.0 # Time step in minutes
    price_noise: float = 1.0 # Tells how much should the live price be trusted or allowed to override the predicted price
    volatility: float = 0.05 # Tells how much the price is expected to change per time step
    initial_uncertainty: float = 10.0 # Tells how much the initial price and trend are expected to be trusted or allowed to override the predicted price and trend

    def __post_init__(self) -> None:
        self.price = float(self.initial_price)
        self.trend = float(self.initial_trend)

        dt2 = self.dt**2
        dt3 = self.dt**3
        dt4 = self.dt**4
        self.process_price_variance = self.volatility * dt4 / 4.0
        self.process_price_trend_covariance = self.volatility * dt3 / 2.0
        self.process_trend_price_covariance = self.process_price_trend_covariance
        self.process_trend_variance = self.volatility * dt2

        self.price_variance = float(self.initial_uncertainty)
        self.price_trend_covariance = 0.0
        self.trend_price_covariance = 0.0
        self.trend_variance = float(self.initial_uncertainty)

    def predict(self) -> float:
        self.price = self.price + self.trend * self.dt

        predicted_price_variance = (
            self.price_variance
            + self.dt * (self.trend_price_covariance + self.price_trend_covariance)
            + self.dt**2 * self.trend_variance
        )
        predicted_price_trend_covariance = (
            self.price_trend_covariance + self.dt * self.trend_variance
        )
        predicted_trend_price_covariance = (
            self.trend_price_covariance + self.dt * self.trend_variance
        )
        predicted_trend_variance = self.trend_variance

        self.price_variance = predicted_price_variance + self.process_price_variance
        self.price_trend_covariance = (
            predicted_price_trend_covariance + self.process_price_trend_covariance
        )
        self.trend_price_covariance = (
            predicted_trend_price_covariance + self.process_trend_price_covariance
        )
        self.trend_variance = predicted_trend_variance + self.process_trend_variance
        return self.price

    def update(self, live_price: float) -> float:
        residual = live_price - self.price
        residual_variance = self.price_variance + self.price_noise

        price_gain = self.price_variance / residual_variance
        trend_gain = self.trend_price_covariance / residual_variance

        self.price = self.price + price_gain * residual
        self.trend = self.trend + trend_gain * residual

        previous_price_variance = self.price_variance
        previous_price_trend_covariance = self.price_trend_covariance
        self.price_variance = (
            self.price_variance - price_gain * previous_price_variance
        )
        self.price_trend_covariance = (
            self.price_trend_covariance
            - price_gain * previous_price_trend_covariance
        )
        self.trend_price_covariance = (
            self.trend_price_covariance - trend_gain * previous_price_variance
        )
        self.trend_variance = (
            self.trend_variance - trend_gain * previous_price_trend_covariance
        )
        return self.price

    def step(self, live_price: float) -> tuple[float, float]:
        predicted_price = self.predict()
        filtered_price = self.update(live_price)
        return predicted_price, filtered_price


if __name__ == "__main__":
    minute_prices = [100.0, 100.3, 100.1, 100.8, 101.2, 101.0, 101.6]
    kf = StockKalmanFilter(
        initial_price=minute_prices[0],
        price_noise=0.25,
        volatility=0.02,
    )

    for price in minute_prices[1:]:
        predicted, filtered = kf.step(price)
        print(
            f"live={price:.2f}, "
            f"predicted={predicted:.2f}, "
            f"filtered={filtered:.2f}"
        )
