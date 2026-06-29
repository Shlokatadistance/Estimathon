import csv
from datetime import datetime


def load_basket_prices(path: str) -> dict[datetime, float]:
    """
    Load basket prices from CSV: timestamp,basket_price
    """
    prices: dict[datetime, float] = {}

    with open(path, newline="", encoding="utf-8") as price_file:
        for row in csv.DictReader(price_file):
            prices[datetime.fromisoformat(row["timestamp"])] = float(row["basket_price"])

    return prices


def load_constituent_prices(path: str) -> dict[datetime, dict[str, float]]:
    """
    Load constituent prices from CSV: timestamp,symbol,price
    """
    prices: dict[datetime, dict[str, float]] = {}

    with open(path, newline="", encoding="utf-8") as price_file:
        for row in csv.DictReader(price_file):
            timestamp = datetime.fromisoformat(row["timestamp"])
            prices.setdefault(timestamp, {})[row["symbol"]] = float(row["price"])

    return prices
