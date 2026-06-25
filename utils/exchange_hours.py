from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ExchangeHours:
    exchange_code: str
    timezone: str
    open_time: time
    close_time: time
    trading_days: tuple[int, ...] = (0, 1, 2, 3, 4)

    def is_open(self, timestamp: datetime) -> bool:
        local_timestamp = timestamp.astimezone(ZoneInfo(self.timezone))

        if local_timestamp.weekday() not in self.trading_days:
            return False

        local_time = local_timestamp.time()
        return self.open_time <= local_time < self.close_time


class ExchangeHoursConfig:
    def __init__(self, exchanges: dict[str, ExchangeHours]) -> None:
        self.exchanges = exchanges

    @classmethod
    def from_json(cls, path: str) -> "ExchangeHoursConfig":
        with open(path, encoding="utf-8") as config_file:
            raw_config = json.load(config_file)

        exchanges = {
            exchange_code: ExchangeHours(
                exchange_code=exchange_code,
                timezone=config["timezone"],
                open_time=time.fromisoformat(config["open"]),
                close_time=time.fromisoformat(config["close"]),
                trading_days=tuple(config.get("trading_days", [0, 1, 2, 3, 4])),
            )
            for exchange_code, config in raw_config.items()
        }

        return cls(exchanges)

    def is_open(self, exchange_code: str | None, timestamp: datetime) -> bool:
        if exchange_code is None:
            return False

        exchange = self.exchanges.get(exchange_code)
        if exchange is None:
            return False

        return exchange.is_open(timestamp)
