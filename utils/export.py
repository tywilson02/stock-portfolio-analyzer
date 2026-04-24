"""
Export utilities — convert in-memory DataFrames to downloadable byte buffers.
"""

from __future__ import annotations

import io
import pandas as pd


def metrics_to_csv(summary_df: pd.DataFrame) -> bytes:
    """Serialize the metrics summary DataFrame to CSV bytes for st.download_button.

    Args:
        summary_df: DataFrame with metrics as rows and tickers + portfolio as columns.

    Returns:
        UTF-8 encoded CSV as bytes.
    """
    buffer = io.StringIO()
    summary_df.to_csv(buffer)
    return buffer.getvalue().encode("utf-8")


def prices_to_csv(prices: pd.DataFrame) -> bytes:
    """Serialize the raw price history to CSV bytes.

    Args:
        prices: Adjusted closing prices indexed by date.

    Returns:
        UTF-8 encoded CSV as bytes.
    """
    buffer = io.StringIO()
    prices.to_csv(buffer)
    return buffer.getvalue().encode("utf-8")
