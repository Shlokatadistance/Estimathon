import re

import xlrd

from basket.basket import BasketConstituent, BasketMetadata, ETF

EQUITY_ASSET_CLASS = "FOREIGN STOCK"
CASH_ASSET_CLASSES = {"MONEY MARKET", "NET CASH", "CURRENCY SECURITY"}

# CUSIP -> symbol for rows whose XLS ticker cell is blank
CUSIP_SYMBOL_OVERRIDE = {
    "BTMJD19": "ROG",  # Roche Holding AG
}

_DATA_START_ROW = 5  # 0-based row index where holdings begin


def load_xls_basket(path: str) -> ETF:
    """
    Parse a BNY basket XLS file and return an ETF whose constituents are priced
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
