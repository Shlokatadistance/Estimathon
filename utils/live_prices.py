import os

import databento
import pandas as pd
import yfinance as yf


class DatabentoClient:
    def __init__(self):
        self.api_key = os.getenv("DB_API_KEY")

    @property
    def historical_client(self):
        """
        Maybe someday i'll have the money for a live
        client.
        """
        client = databento.Historical(key=self.api_key)
        return client

    def get_publishers(self):
        return self.historical_client.metadata.list_publishers()

    def get_datasets(self):
        return self.historical_client.metadata.list_datasets()

    def get_schemas(self, dataset: str):
        return self.historical_client.metadata.list_schemas(dataset=dataset)

    def get_available_fields(self, schema: str, encoding: str = "dbn"):
        """
        dbn is a native databento encoding.
        """
        return self.historical_client.metadata.list_fields(
            schema=schema, encoding=encoding
        )

    def get_schema_unit_prices(self, dataset: str):
        """
        return the price of the dataset per schems ( mbo, mbp, ohlcv)
        """
        return self.historical_client.metadata.list_unit_prices(dataset=dataset)


class FetchMarketData:
    def __init__(self):
        self.query_client = DatabentoClient().historical_client

    def dump_single_price(self, symbol: str, start: str = None, end: str = None) -> None:
        """
        Going with a more default type settings right now.
        2 months of historical data ( January to Februrary 2026 )
        Can pass the symbol

        The way I currently trigger the script is to simply use data csv's,
        so I am thinking of dumping the data to a csv file for now.

        #TODO: Add support for live data streaming

        """
        data = self.query_client.timeseries.get_range(
            symbols=[symbol],
            dataset="EQUS.MINI",
            schema="OHLCV-1m",
            start="2026-04-01T00:00:00",
            end="2026-05-31T00:00:00",
        )

        data = data.to_df()
        data.to_csv(f"data/{symbol}_ohlcv_1m.csv", index=False)


YFINANCE_TICKER_MAP: dict[str, str] = {
    "TSM": "TSM",        # Taiwan Semiconductor (NYSE ADR)
    "ASML": "ASML",      # ASML Holding (NASDAQ)
    "ATD": "ATD.TO",     # Alimentation Couche-Tard (TSX)
    # "CPG": unknown mapping - price ~$32.74 USD doesn't match CPG.TO; skipped
    "CPG": "CPG.TO",     # TODO: verify correct yfinance ticker for this constituent
    "TTE": "TTE",        # TotalEnergies (NYSE ADR)
    "1299": "1299.HK",   # AIA Group (HKEX)
    "AI": "AI.PA",       # Air Liquide (Paris)
    "MRK": "MRK.DE",     # Merck KGaA (Frankfurt)
    "ROG": "RHHBY",      # Roche Holding (OTC ADR; ROG.SW not on Yahoo Finance)
    "AMS": "AMS.SW",     # ams-OSRAM (Swiss)
    "4063": "4063.T",    # Shin-Etsu Chemical (Tokyo)
    "7741": "7741.T",    # Hoya Corp (Tokyo)
    "SGSN": "SGSN.SW",   # Swisscom (Swiss)
    "OR": "OR.PA",       # L'Oreal (Paris)
    "6861": "6861.T",    # Keyence (Tokyo)
    "SIKA": "SIKA.SW",   # Sika AG (Swiss)
    "LONN": "LONN.SW",   # Lonza Group (Swiss)
    "ALC": "ALC",        # Alcon (NYSE)
    # "CLAR": delisted (acquired by SABIC); no Yahoo Finance data available
    "CLAR": "CLAR.SW",   # Clariant (Swiss) - delisted, will produce WARN
    "MC": "MC.PA",       # LVMH (Paris)
    "SAP": "SAP",        # SAP SE (NYSE ADR)
    "EXPN": "EXPN.L",    # Experian (London)
    "ADS": "ADS.DE",     # Adidas (Frankfurt)
    "UMG": "UMG.AS",     # Universal Music Group (Amsterdam)
    "6367": "6367.T",    # Daikin Industries (Tokyo)
    "COLOB": "CLPBY",    # Coloplast (OTC ADR; COLOB.CO has no 1h data on Yahoo Finance)
    "KNEBV": "KNEBV.HE", # Kone (Helsinki)
}


class YFinanceClient:
    def get_ticker(self, symbol: str) -> yf.Ticker:
        return yf.Ticker(symbol)

    def get_info(self, symbol: str) -> dict:
        return self.get_ticker(symbol).info


class FetchYFinanceData:
    def __init__(self):
        self.client = YFinanceClient()

    def dump_single_price(
        self,
        symbol: str,
        start: str,
        end: str,
        interval: str = "1m",
    ) -> None:
        """
        Fetch OHLCV for a single ticker and dump to data/{symbol}_ohlcv_{interval}.csv.

        interval: yfinance interval string, e.g. "1m", "5m", "1h", "1d"
        start/end: ISO date strings, e.g. "2026-04-01"
        """
        ticker = self.client.get_ticker(symbol)
        data: pd.DataFrame = ticker.history(start=start, end=end, interval=interval)
        data.index.name = "timestamp"
        safe_symbol = symbol.replace("/", "-")
        data.to_csv(f"data/{safe_symbol}_ohlcv_{interval}.csv")

    def dump_basket_constituent_prices(
        self,
        basket_path: str,
        start: str,
        end: str,
        interval: str = "1h",
        out_path: str = "data/constituent_prices.csv",
    ) -> None:
        """
        Load a basket JSON, fetch OHLCV for each constituent via yfinance,
        and write a combined CSV with columns: timestamp, symbol, price (Close).
        Uses YFINANCE_TICKER_MAP to translate XLS tickers to Yahoo Finance format.
        """
        import json

        with open(basket_path, encoding="utf-8") as f:
            basket = json.load(f)

        frames: list[pd.DataFrame] = []
        for c in basket["constituents"]:
            xls_symbol = c["symbol"]
            yf_symbol = YFINANCE_TICKER_MAP.get(xls_symbol, xls_symbol)
            try:
                ticker = self.client.get_ticker(yf_symbol)
                data: pd.DataFrame = ticker.history(start=start, end=end, interval=interval)
                if data.empty:
                    print(f"  [WARN] No data for {xls_symbol} ({yf_symbol})")
                    continue
                data.index.name = "timestamp"
                df = data[["Close"]].rename(columns={"Close": "price"}).copy()
                df["symbol"] = xls_symbol
                df = df.reset_index()[["timestamp", "symbol", "price"]]
                frames.append(df)
                print(f"  {xls_symbol} ({yf_symbol}): {len(df)} rows")
            except Exception as e:
                print(f"  [ERROR] {xls_symbol} ({yf_symbol}): {e}")

        if not frames:
            print("No data fetched.")
            return

        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv(out_path, index=False)
        print(f"\nWritten {len(combined)} rows to {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch constituent prices for a basket.")
    parser.add_argument("--basket", required=True, help="Path to basket JSON")
    parser.add_argument("--start", required=True, help="Start date, e.g. 2026-06-29")
    parser.add_argument("--end", required=True, help="End date (exclusive), e.g. 2026-06-30")
    parser.add_argument("--interval", default="1h", help="yfinance interval (default: 1h)")
    parser.add_argument("--out", default="data/constituent_prices.csv")
    args = parser.parse_args()

    fetcher = FetchYFinanceData()
    fetcher.dump_basket_constituent_prices(
        basket_path=args.basket,
        start=args.start,
        end=args.end,
        interval=args.interval,
        out_path=args.out,
    )
