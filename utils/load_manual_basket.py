import json
from typing import Any
from basket.basket import ETF,BasketConstituent,BasketMetadata



def load_manual_basket_json(path: str) -> ETF:
    """
    Load a hand-written basket file for quick experiments.
    """
    with open(path, encoding="utf-8") as basket_file:
        data = json.load(basket_file)
    metadata = get_basket_metadata(data['metadata'])
    constituents = get_basket_constituents(data['constituents'])

    return ETF(metadata=metadata, constituents=constituents)

def get_basket_metadata(data:dict[str,Any]):
    
    if not data:
        return
    return BasketMetadata(
        basket_name=data['basket_name'],
        basket_type=data['basket_type'],
        source=data['source'],
        creation_size=int(data['creation_size']),
        cash=float(data['cash_position'])
        )

def get_basket_constituents(data:dict[str,Any]):
    consituents = []
    if not data:
        return
    for constituent in data:
        consituents.append(BasketConstituent(
            symbol=constituent['symbol'],
            quantity=float(constituent['shares']),
            currency=constituent['currency'],
            close_price=float(constituent['close_price']),
            fx_rate_to_base=float(constituent['fx_rate_to_base']),
        ))
    return consituents