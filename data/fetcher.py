"""
Data fetching module — downloads historical price data from Yahoo Finance.
Uses Streamlit's cache to avoid redundant network calls within a session.
"""

from __future__ import annotations

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date


BENCHMARK_TICKER = "SPY"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(
    tickers: tuple[str, ...],
    start: date,
    end: date,
) -> tuple[pd.DataFrame, list[str]]:
    """Download adjusted closing prices for the given tickers and date range.

    Args:
        tickers: Tuple of uppercase ticker symbols (tuple so it's hashable for caching).
        start: Inclusive start date.
        end: Inclusive end date.

    Returns:
        A tuple of (prices_df, invalid_tickers) where prices_df contains only
        tickers with sufficient data and invalid_tickers lists any that failed.
    """
    all_tickers = list(tickers)
    if BENCHMARK_TICKER not in all_tickers:
        all_tickers.append(BENCHMARK_TICKER)

    raw = yf.download(
        tickers=all_tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if raw.empty:
        return pd.DataFrame(), list(tickers)

    # yfinance returns MultiIndex columns when >1 ticker, flat when exactly 1
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]].rename(columns={"Close": all_tickers[0]})

    prices = prices.dropna(how="all")

    # Identify tickers that returned no usable data
    invalid: list[str] = []
    valid_cols: list[str] = []
    for t in list(tickers) + [BENCHMARK_TICKER]:
        if t not in prices.columns or prices[t].isna().all():
            if t != BENCHMARK_TICKER:
                invalid.append(t)
        else:
            valid_cols.append(t)

    prices = prices[valid_cols].dropna(how="all")

    # Align all series to a common index (trading days present for all tickers)
    prices = prices.dropna()

    return prices, invalid


def validate_date_range(start: date, end: date) -> str | None:
    """Return an error message string if the date range is invalid, else None."""
    if start >= end:
        return "Start date must be before end date."
    if (end - start).days < 30:
        return "Date range must span at least 30 days to compute meaningful metrics."
    if end > date.today():
        return "End date cannot be in the future."
    return None
