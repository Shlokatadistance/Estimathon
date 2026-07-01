import json

import xlrd

from basket.basket import BasketConstituent, BasketMetadata, ETF

EQUITY_ASSET_CLASS = "FOREIGN STOCK"
CASH_ASSET_CLASSES = {"MONEY MARKET", "NET CASH", "CURRENCY SECURITY"}

# CUSIP -> symbol for rows whose XLS ticker cell is blank
# Slightly dirty right now
CUSIP_SYMBOL_OVERRIDE = {
    "BTMJD19": "ROG",  # Roche Holding AG
}

_DATA_START_ROW = 5  # 0-based row index where holdings begin


def load_xls_basket(path: str) -> ETF:
    """
    Parse a basket XLS file and return an ETF whose constituents are priced
    in USD (close_price = market_value / shares, fx_rate_to_base = 1.0).

    Cash-like rows (MONEY MARKET, NET CASH, CURRENCY SECURITY) are aggregated
    into the basket cash position.
    """
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)

    basket_name = str(sh.cell_value(1, 1)).strip()

    constituents: list[BasketConstituent] = []
    cash = 0.0

    for row_idx in range(_DATA_START_ROW, sh.nrows):
        ticker = str(sh.cell_value(row_idx, 0)).strip()
        cusip = str(sh.cell_value(row_idx, 1)).strip()
        asset_class = str(sh.cell_value(row_idx, 2)).strip()
        shares_val = sh.cell_value(row_idx, 5)
        market_value_val = sh.cell_value(row_idx, 6)

        # Skip blank / footer rows
        if not asset_class or not isinstance(market_value_val, (int, float)):
            continue

        if asset_class in CASH_ASSET_CLASSES:
            cash += float(market_value_val)
            continue

        if asset_class != EQUITY_ASSET_CLASS:
            continue

        if not isinstance(shares_val, (int, float)) or float(shares_val) == 0:
            continue

        # Prefer the XLS ticker; fall back to a CUSIP-based override (e.g. Roche)
        if ticker:
            symbol = ticker
        elif cusip in CUSIP_SYMBOL_OVERRIDE:
            symbol = CUSIP_SYMBOL_OVERRIDE[cusip]
        else:
            continue

        usd_price = float(market_value_val) / float(shares_val)

        constituents.append(BasketConstituent(
            symbol=symbol,
            quantity=float(shares_val),
            currency="USD",
            close_price=round(usd_price, 6),
            fx_rate_to_base=1.0,
        ))

    metadata = BasketMetadata(
        basket_name=basket_name,
        basket_type="PRICING",
        source="xls",
        creation_size=1,
        cash=round(cash, 2),
    )

    return ETF(metadata=metadata, constituents=constituents)


def dump_basket_to_json(etf: ETF, path: str) -> None:
    """
    Serialize an ETF to a JSON file compatible with load_manual_basket_json.
    """
    data = {
        "metadata": {
            "basket_name": etf.metadata.basket_name,
            "basket_type": etf.metadata.basket_type,
            "source": etf.metadata.source,
            "creation_size": str(etf.metadata.creation_size),
            "cash_position": str(etf.metadata.cash),
        },
        "constituents": [
            {
                "symbol": c.symbol,
                "shares": str(c.quantity),
                "currency": c.currency,
                "close_price": str(c.close_price),
                "fx_rate_to_base": str(c.fx_rate_to_base),
            }
            for c in etf.constituents
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load a basket XLS and dump it to JSON.")
    parser.add_argument("--xls", required=True, help="Path to the input basket XLS file")
    parser.add_argument("--out", required=True, help="Path to write the output JSON file")
    args = parser.parse_args()

    etf = load_xls_basket(args.xls)
    dump_basket_to_json(etf, args.out)
    print(f"Basket '{etf.metadata.basket_name}' → {len(etf.constituents)} constituents, cash={etf.metadata.cash}")
    print(f"Written to {args.out}")
