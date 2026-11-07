import os

import databento
import pandas as pd
import pendulum


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

    @property
    def sm_client(self):
        client = databento.Reference(key=self.api_key)
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
        self.sm_client = DatabentoClient().sm_client

    def get_ohlcv_1m(
        self, symbols: list[str], start: str, end: str, basket_name: str
    ) -> None:
        """
        Going with a more default type settings right now.
        2 months of historical data ( January to Februrary 2026 )
        Can pass the symbol

        The way I currently trigger the script is to simply use data csv's,
        so I am thinking of dumping the data to a csv file for now.

        #TODO: Add support for live data streaming

        Currently not passing any specific market open or close timings to the
        function.

        """

        data = self.query_client.timeseries.get_range(
            symbols=symbols,
            dataset="EQUS.MINI",
            schema="OHLCV-1m",
            start=start,
            end=end,
        )

        data = data.to_df()
        data.to_csv(f"data/{basket_name}_ohlcv_1m.csv", index=False)

    def get_ohlcv_1_day(self, symbols: list[str]) -> pd.DataFrame:
        """
        Get last prices for T-1 business day
        """
        current_date_string = pendulum.today(tz="Asia/Hong_Kong").strftime("%Y-%m-%d")
        ts = pd.Timestamp(current_date_string)
        prev = ts - pd.offsets.BusinessDay(1)
        start = end = prev.strftime("%Y-%m-%d")
        data = self.query_client.timeseries.get_range(
            symbols=symbols,
            dataset="EQUS.MINI",
            schema="OHLCV-1d",
            start=start,
            end=end,
        ).to_df()
        if data.empty:
            print(f"No data returned for {start}")
            return pd.DataFrame()
        return data

    def get_security_master_data(self, symbols: list[str]) -> pd.DataFrame:

        df = self.sm_client.security_master.get_last(symbols=symbols)
        return df


if __name__ == "__main__":
    x = FetchMarketData()
    y = x.get_security_master_data(symbols=["AAPL", "ASML", "2330"])
    print(y.head(5))
