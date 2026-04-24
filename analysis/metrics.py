"""
Portfolio metrics module — all financial calculations live here.

Assumes prices are daily adjusted closing prices as a pd.DataFrame
with tickers as columns and dates as the index.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
RISK_FREE_RATE_ANNUAL = 0.045  # 4.5% annualized


def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute simple daily percentage returns from price series.

    Args:
        prices: DataFrame of adjusted closing prices.

    Returns:
        DataFrame of daily returns (NaN on first row dropped).
    """
    return prices.pct_change().dropna()


def compute_portfolio_returns(
    daily_returns: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    """Compute weighted portfolio daily returns.

    Args:
        daily_returns: Per-ticker daily returns (columns = tickers).
        weights: Dict mapping ticker -> weight (must sum to 1.0).

    Returns:
        Series of daily portfolio returns.
    """
    tickers = [t for t in weights if t in daily_returns.columns]
    w = np.array([weights[t] for t in tickers])
    return daily_returns[tickers].dot(w).rename("Portfolio")


def compute_cumulative_returns(returns: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Convert daily returns to cumulative growth index (starts at 1.0).

    Args:
        returns: Daily returns as Series or DataFrame.

    Returns:
        Cumulative return index of the same shape.
    """
    return (1 + returns).cumprod()


def compute_total_return(prices: pd.DataFrame) -> pd.Series:
    """Compute total percentage return from first to last price for each ticker.

    Args:
        prices: DataFrame of adjusted closing prices.

    Returns:
        Series of total returns indexed by ticker.
    """
    return ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100).rename("Total Return (%)")


def compute_annualized_volatility(daily_returns: pd.DataFrame | pd.Series) -> pd.Series | float:
    """Annualize daily return standard deviation.

    Multiplies daily std by sqrt(252) — the square-root-of-time rule.

    Args:
        daily_returns: Daily returns as Series or DataFrame.

    Returns:
        Annualized volatility as a float (Series) or scalar.
    """
    return daily_returns.std() * np.sqrt(TRADING_DAYS)


def compute_sharpe_ratio(
    daily_returns: pd.Series | pd.DataFrame,
    risk_free_rate: float = RISK_FREE_RATE_ANNUAL,
) -> float | pd.Series:
    """Compute the annualized Sharpe ratio.

    Sharpe = (annualized_return - risk_free_rate) / annualized_volatility

    Args:
        daily_returns: Daily returns for a portfolio (Series) or individual stocks (DataFrame).
        risk_free_rate: Annual risk-free rate as a decimal (default 4.5%).

    Returns:
        Sharpe ratio as float or per-ticker Series.
    """
    daily_rf = risk_free_rate / TRADING_DAYS
    excess = daily_returns - daily_rf
    annualized_excess = excess.mean() * TRADING_DAYS
    annualized_vol = excess.std() * np.sqrt(TRADING_DAYS)
    return annualized_excess / annualized_vol


def compute_max_drawdown(returns: pd.Series) -> float:
    """Compute the maximum drawdown for a return series.

    Max drawdown = the largest peak-to-trough decline in the cumulative
    return curve, expressed as a percentage.

    Args:
        returns: Daily return series (e.g. portfolio or single stock).

    Returns:
        Max drawdown as a negative float (e.g. -0.35 means -35%).
    """
    cum = compute_cumulative_returns(returns)
    rolling_peak = cum.cummax()
    drawdown = (cum - rolling_peak) / rolling_peak
    return float(drawdown.min())


def compute_drawdown_series(returns: pd.Series) -> pd.Series:
    """Return the full drawdown time series (used for plotting).

    Args:
        returns: Daily return series.

    Returns:
        Series of drawdown values (0 to negative).
    """
    cum = compute_cumulative_returns(returns)
    rolling_peak = cum.cummax()
    return (cum - rolling_peak) / rolling_peak


def compute_correlation_matrix(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """Compute the Pearson correlation matrix between ticker returns.

    Args:
        daily_returns: Daily returns DataFrame with tickers as columns.

    Returns:
        Correlation matrix as a DataFrame.
    """
    return daily_returns.corr()


def compute_annualized_return(daily_returns: pd.Series | pd.DataFrame) -> float | pd.Series:
    """Compute compound annual growth rate from daily returns.

    Args:
        daily_returns: Daily return series or DataFrame.

    Returns:
        CAGR as a decimal.
    """
    n = len(daily_returns)
    total = (1 + daily_returns).prod()
    return total ** (TRADING_DAYS / n) - 1


def build_summary_metrics(
    prices: pd.DataFrame,
    weights: dict[str, float],
    benchmark_ticker: str = "SPY",
) -> pd.DataFrame:
    """Assemble the full metrics table shown in the dashboard summary card.

    Args:
        prices: Adjusted closing prices including all tickers and benchmark.
        weights: Portfolio weights (benchmark excluded).
        benchmark_ticker: Ticker symbol for the benchmark.

    Returns:
        DataFrame with one row per metric and columns for the portfolio,
        benchmark, and each individual stock.
    """
    portfolio_tickers = [t for t in weights]
    daily_returns = compute_daily_returns(prices)

    portfolio_ret = compute_portfolio_returns(daily_returns, weights)
    benchmark_ret = daily_returns[benchmark_ticker] if benchmark_ticker in daily_returns.columns else None

    columns: dict[str, dict] = {}

    # Portfolio column
    columns["Portfolio"] = {
        "Total Return (%)": round(float(compute_annualized_return(portfolio_ret) * 100 * len(portfolio_ret) / TRADING_DAYS), 2),
        "Ann. Return (%)": round(float(compute_annualized_return(portfolio_ret) * 100), 2),
        "Ann. Volatility (%)": round(float(compute_annualized_volatility(portfolio_ret) * 100), 2),
        "Sharpe Ratio": round(float(compute_sharpe_ratio(portfolio_ret)), 3),
        "Max Drawdown (%)": round(float(compute_max_drawdown(portfolio_ret) * 100), 2),
    }

    # Benchmark column
    if benchmark_ret is not None:
        columns[benchmark_ticker] = {
            "Total Return (%)": round(float(compute_annualized_return(benchmark_ret) * 100 * len(benchmark_ret) / TRADING_DAYS), 2),
            "Ann. Return (%)": round(float(compute_annualized_return(benchmark_ret) * 100), 2),
            "Ann. Volatility (%)": round(float(compute_annualized_volatility(benchmark_ret) * 100), 2),
            "Sharpe Ratio": round(float(compute_sharpe_ratio(benchmark_ret)), 3),
            "Max Drawdown (%)": round(float(compute_max_drawdown(benchmark_ret) * 100), 2),
        }

    # Per-stock columns
    for ticker in portfolio_tickers:
        if ticker in daily_returns.columns:
            ret = daily_returns[ticker]
            columns[ticker] = {
                "Total Return (%)": round(float(compute_annualized_return(ret) * 100 * len(ret) / TRADING_DAYS), 2),
                "Ann. Return (%)": round(float(compute_annualized_return(ret) * 100), 2),
                "Ann. Volatility (%)": round(float(compute_annualized_volatility(ret) * 100), 2),
                "Sharpe Ratio": round(float(compute_sharpe_ratio(ret)), 3),
                "Max Drawdown (%)": round(float(compute_max_drawdown(ret) * 100), 2),
            }

    return pd.DataFrame(columns)
