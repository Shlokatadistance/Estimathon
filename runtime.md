# Runtime

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
