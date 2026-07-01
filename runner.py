import argparse
import math
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from basket.basket import HistoricalBasketPricer
from utils.load_manual_basket import load_manual_basket_json
from utils.load_xls_basket import load_xls_basket
from utils.manual_price_ingester import (
    load_basket_prices,
    load_constituent_prices,
)


def print_stats(predicted: list[float], actual: list[float]) -> None:
    diffs = [p - a for p, a in zip(predicted, actual)]
    pct_diffs = [abs(d) / a * 100 for d, a in zip(diffs, actual)]
    abs_diffs = [abs(d) for d in diffs]

    mae = sum(abs_diffs) / len(abs_diffs)
    mape = sum(pct_diffs) / len(pct_diffs)
    rmse = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
    max_abs = max(abs_diffs)
    max_pct = max(pct_diffs)
    max_abs_ts_idx = abs_diffs.index(max_abs)
    min_abs = min(abs_diffs)

    print("\n| Metric | Value |")
    print("|---|---|")
    print(f"| MAE | {mae:,.0f} |")
    print(f"| MAPE | {mape:.4f}% |")
    print(f"| RMSE | {rmse:,.0f} |")
    print(f"| Max absolute deviation | {max_abs:,.0f} ({max_pct:.4f}%) |")
    print(f"| Min absolute deviation | {min_abs:,.0f} |")
    print(f"| N timestamps | {len(predicted)} |")


def plot_nav(
    timestamps: list[datetime],
    predicted: list[float],
    actual: list[float],
    out_path: str,
    basket_name: str = "",
) -> None:
    diff = [p - a for p, a in zip(predicted, actual)]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 7), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08},
    )
    fig.patch.set_facecolor("#0f1117")
    for ax in (ax1, ax2):
        ax.set_facecolor("#1a1d27")
        ax.tick_params(colors="#aaaaaa")
        ax.spines[:].set_color("#333344")

    ax1.plot(timestamps, predicted, color="#4fc3f7", linewidth=1.8, label="Kalman predicted")
    ax1.plot(timestamps, actual, color="#81c784", linewidth=1.8, linestyle="--", label="True NAV")
    ax1.fill_between(timestamps, predicted, actual, alpha=0.15, color="#ef9a9a")
    ax1.set_ylabel("Basket NAV", color="#cccccc")
    ax1.legend(facecolor="#1a1d27", labelcolor="#cccccc", framealpha=0.8)
    ax1.set_title(
        f"Kalman Basket Pricer — {basket_name}" if basket_name else "Kalman Basket Pricer",
        color="#eeeeee", pad=10,
    )
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M"))

    ax2.bar(timestamps, diff, color=["#ef5350" if d < 0 else "#66bb6a" for d in diff], width=0.02)
    ax2.axhline(0, color="#555566", linewidth=0.8)
    ax2.set_ylabel("Diff", color="#cccccc")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M"))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator())
    plt.xticks(rotation=30, color="#aaaaaa")

    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Plot saved to {out_path}")


def load_basket(path: str):
    if path.endswith(".xls") or path.endswith(".xlsx"):
        return load_xls_basket(path)
    return load_manual_basket_json(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--basket", default="manual_basket.json")
    parser.add_argument("--basket-prices", required=True)
    parser.add_argument("--constituent-prices", required=True)
    parser.add_argument("--plot", default=None, help="Path to save the NAV plot (e.g. data/nav.png)")
    args = parser.parse_args()

    basket = load_basket(args.basket)
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

    timestamps, predicted_navs, actual_navs = [], [], []

    for snapshot in pricer.run(constituent_prices):
        actual_price = actual_basket_prices.get(snapshot.timestamp)
        difference = (
            snapshot.basket_price - actual_price if actual_price is not None else None
        )

        print(
            snapshot.timestamp.isoformat(),
            f"predicted={snapshot.basket_price:.4f}",
            f"actual={actual_price:.4f}" if actual_price is not None else "actual=NA",
            f"diff={difference:.4f}" if difference is not None else "diff=NA",
        )

        if actual_price is not None:
            timestamps.append(snapshot.timestamp)
            predicted_navs.append(snapshot.basket_price)
            actual_navs.append(actual_price)

    if timestamps:
        print_stats(predicted_navs, actual_navs)

    if args.plot and timestamps:
        plot_nav(
            timestamps=timestamps,
            predicted=predicted_navs,
            actual=actual_navs,
            out_path=args.plot,
            basket_name=basket.metadata.basket_name,
        )


if __name__ == "__main__":
    main()
