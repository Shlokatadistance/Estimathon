import os

import databento
import pandas as pd


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

    def stream_single_price(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """
        Going with a more default type settings right now.
        2 months of historical data ( January to Februrary 2026 )
        Can pass the symbol

        """
        data = self.query_client.timeseries.get_range(
            symbols=[symbol],
            dataset="EQUS.MINI",
            schema="OHLCV-1m",
            start="2026-04-01T00:00:00",
            end="2026-05-31T00:00:00",
        )

        data.to_df()
