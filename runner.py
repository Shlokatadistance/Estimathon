import argparse

from basket.basket import HistoricalBasketPricer
from utils.load_manual_basket import load_manual_basket_json
from utils.manual_price_ingester import (
    load_basket_prices,
    load_constituent_prices,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--basket", default="manual_basket.json")
    parser.add_argument("--basket-prices", required=True)
    parser.add_argument("--constituent-prices", required=True)
    args = parser.parse_args()

    basket = load_manual_basket_json(args.basket)
    actual_basket_prices = load_basket_prices(args.basket_prices)
    constituent_prices = load_constituent_prices(args.constituent_prices)

    pricer = HistoricalBasketPricer(
        constituents=basket.constituents,
        initial_prices={
            constituent.symbol: constituent.close_price
            for constituent in basket.constituents
        },
        cash=basket.metadata.cash,
    )

    for snapshot in pricer.run(constituent_prices):
        actual_price = actual_basket_prices.get(snapshot.timestamp)
        difference = (
            snapshot.basket_price - actual_price
            if actual_price is not None
            else None
        )

        print(
            snapshot.timestamp.isoformat(),
            f"predicted={snapshot.basket_price:.4f}",
            f"actual={actual_price:.4f}" if actual_price is not None else "actual=NA",
            f"diff={difference:.4f}" if difference is not None else "diff=NA",
        )


if __name__ == "__main__":
    main()
