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


### Setup

For anyone curious, nav.png shows the results for the BNY basket. The test setup is 
1. Hourly constituent data, ordered in time as constituents start to trade. Asian tickers are at the top, European in the middle, and US at the bottom.
2. For constituents which are not trading, use the .predict() method to predict their price. For the rest, use the actual price.
3. Generate a kalman NAV and compare it to the synthetic NAV of the basket. The synthetic NAV is calculated from the formula 
4. Currently I havent account for fx variances ( the base fx rate is all USD and 1:1 ). This would be a good addition to make the model more realistic.
```
NAV = Σ(shares × last_known_price × fx_rate_to_base) + cash
```
For a constituent that is live, use the actual price. For a constituent that is not live, use the price from the basket json.

### Observations

I ran this code for a single basket, BNYM Concentrated International ETF ( got the excel file and then generated the JSON file from it ). I used yfinance data for the start, because I wanted to visualize the results first before actually paying for a live stream. The results are actually quite interesting


- Because the Kalman NAV starts with some initial guess about the error and variance, the first predictions are substantially off. 

- Once more markets start to open and the filter is exposed to more constituent data, the predictions become more accurate. I would compare this to a linear regression approach, where the first predictions would be off as well, but would not improve as much as the Kalman filter once more data is available. ( Though I should put this to the test )


Small table I generated to calculate the error 
```
| Metric | Value |
|---|---|
| Mean Absolute Error | 65,231,443 |
| Mean Absolute Percentage Error | 2.1791% |
| Root Mean Square Error | 135,178,424 |
| N timestamps | 30 |
```

#TODO
The Asian hour spike drags up the average significantly, perhaps I need to modify the skew the starting error and variance to be more conservative.