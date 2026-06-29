## Core Idea

Think of a composite basket, like VT.US ( Vanguard World ETF ), which has constituents from across the world with disparate trading hours. There are a couple of different ways to price a basket like this, but one interesting idea I thought of is to to almost treat this basket like a moving vehicle, and hence using a Kalman filter to somewhat 'fill' the prices of constituents that do not trade when the rest of the constituents in the baskets do. 

### Running the code
Whats not ideal currently is feeding constituent prices. Because if you want to manually pass prices, need to combine them into one giant constituent_prices.csv file. Would also require some modifications on the filter side
to ingest all that data and predict in parallel and some tuning of the final value.

Run the basket comparison with:

```bash
python3 runner.py --basket-prices basket_prices.csv --constituent-prices constituent_prices.csv
```

`basket_prices.csv`:

```csv
timestamp,basket_price
2026-06-19T09:30:00,800.00
```

`constituent_prices.csv`:

```csv
timestamp,symbol,price
2026-06-19T09:30:00,AAPL US Equity,196.00
2026-06-19T09:30:00,7203 JP Equity,3010.00
```

The basket definition defaults to `manual_basket.json`.
