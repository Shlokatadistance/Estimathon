from __future__ import annotations

import csv
import os


STATE_FIELDNAMES = [
    "timestamp",
    "constituent_key",
    "symbol",
    "exchange",
    "price",
    "trend",
    "price_variance",
    "price_trend_covariance",
    "trend_price_covariance",
    "trend_variance",
]


def append_filter_state_rows(path: str, rows: list[dict[str, str]]) -> None:
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as state_file:
        writer = csv.DictWriter(state_file, fieldnames=STATE_FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)
