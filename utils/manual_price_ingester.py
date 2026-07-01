import csv
import json
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


def compute_basket_nav(
    basket_path: str,
    constituent_prices_path: str,
    out_path: str = "data/basket_prices.csv",
) -> None:
    """
    Compute true basket NAV at every constituent-price timestamp and write
    basket_prices.csv (timestamp,basket_price).

    Missing constituents at a given timestamp are forward-filled from the
    most recent known price, seeded from close_price in the basket JSON.
    """
    with open(basket_path, encoding="utf-8") as f:
        basket = json.load(f)

    weights: dict[str, tuple[float, float]] = {
        c["symbol"]: (float(c["shares"]), float(c["fx_rate_to_base"]))
        for c in basket["constituents"]
    }
    cash = float(basket["metadata"]["cash_position"])

    last_prices: dict[str, float] = {
        c["symbol"]: float(c["close_price"])
        for c in basket["constituents"]
    }

    constituent_prices = load_constituent_prices(constituent_prices_path)
    nav_by_time: dict[datetime, float] = {}

    for ts in sorted(constituent_prices.keys()):
        last_prices.update(constituent_prices[ts])
        nav = (
            sum(
                qty * last_prices[sym] * fx
                for sym, (qty, fx) in weights.items()
                if sym in last_prices
            )
            + cash
        )
        nav_by_time[ts] = nav

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "basket_price"])
        for ts, nav in sorted(nav_by_time.items()):
            writer.writerow([ts.isoformat(), round(nav, 4)])

    print(f"Written {len(nav_by_time)} NAV timestamps to {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute true basket NAV from constituent prices.")
    parser.add_argument("--basket", required=True, help="Path to basket JSON")
    parser.add_argument("--constituent-prices", required=True, help="Path to constituent_prices.csv")
    parser.add_argument("--out", default="data/basket_prices.csv", help="Output basket_prices.csv path")
    args = parser.parse_args()

    compute_basket_nav(
        basket_path=args.basket,
        constituent_prices_path=args.constituent_prices,
        out_path=args.out,
    )
