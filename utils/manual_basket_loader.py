from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from basket_definition import (
    BasketMetadata,
    EnrichedBasket,
    EnrichedBasketConstituent,
)


def load_manual_basket_json(path: str) -> EnrichedBasket:
    """
    Load a hand-written basket file for quick experiments.

    Required constituent fields:
        symbol, name, currency, close_price

    Also provide either:
        shares for share-based valuation
        weight for weight-based valuation

    Optional constituent fields:
        exchange, fx_rate_to_base, adjusted_close_price, adjusted_shares,
        weight, constituent_id, constituent_type, isin, cusip, sedol, figi,
        bbg_ticker, close_price_date, extra
    """
    with open(path, encoding="utf-8") as basket_file:
        data = json.load(basket_file)

    metadata = _metadata_from_dict(data["metadata"])
    constituents = tuple(
        _constituent_from_dict(constituent)
        for constituent in data["constituents"]
    )

    return EnrichedBasket(metadata=metadata, constituents=constituents)


def _metadata_from_dict(data: dict[str, Any]) -> BasketMetadata:
    return BasketMetadata(
        basket_name=data["basket_name"],
        basket_type=data.get("basket_type", "PRICING"),
        etf_isin=data.get("etf_isin"),
        fund_type=data.get("fund_type"),
        source=data.get("source", "manual"),
        source_data_date=_to_date(data.get("source_data_date")),
        creation_size=_to_decimal(data.get("creation_size")),
        outstanding_etfs=_to_decimal(data.get("outstanding_etfs")),
        nav_per_etf=_to_decimal(data.get("nav_per_etf")),
        cash_position=_to_decimal(data.get("cash_position")) or Decimal("0"),
        basket_size=_to_decimal(data.get("basket_size")),
        number_of_components=data.get("number_of_components"),
    )


def _constituent_from_dict(data: dict[str, Any]) -> EnrichedBasketConstituent:
    close_price = _to_decimal(data.get("close_price"))
    adjusted_close_price = _to_decimal(data.get("adjusted_close_price"))
    shares = _to_decimal(data.get("shares"))
    weight = _to_decimal(data.get("weight"))

    if close_price is None and adjusted_close_price is None:
        raise ValueError(
            f"Manual constituent {data.get('symbol', data.get('name'))} "
            "needs close_price or adjusted_close_price."
        )

    if shares is None and weight is None:
        raise ValueError(
            f"Manual constituent {data.get('symbol', data.get('name'))} "
            "needs shares or weight."
        )

    return EnrichedBasketConstituent(
        name=data["name"],
        shares=shares or Decimal("0"),
        symbol=data["symbol"],
        currency=data["currency"],
        exchange=data.get("exchange"),
        close_price=close_price,
        adjusted_close_price=adjusted_close_price,
        adjusted_shares=_to_decimal(data.get("adjusted_shares")),
        weight=weight,
        constituent_id=data.get("constituent_id"),
        constituent_type=data.get("constituent_type"),
        isin=data.get("isin"),
        cusip=data.get("cusip"),
        sedol=data.get("sedol"),
        figi=data.get("figi"),
        bbg_ticker=data.get("bbg_ticker"),
        close_price_date=_to_date(data.get("close_price_date")),
        fx_rate_to_base=_to_decimal(data.get("fx_rate_to_base")) or Decimal("1"),
        extra={
            key: str(value)
            for key, value in data.get("extra", {}).items()
        },
    )


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None

    return Decimal(str(value))


def _to_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value

    return date.fromisoformat(str(value))
