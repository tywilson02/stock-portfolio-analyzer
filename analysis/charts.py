"""
Chart builders — each function returns a Plotly Figure ready for st.plotly_chart().
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from analysis.metrics import (
    compute_daily_returns,
    compute_portfolio_returns,
    compute_cumulative_returns,
    compute_correlation_matrix,
    compute_drawdown_series,
)


PALETTE = px.colors.qualitative.Set2
BENCHMARK_COLOR = "#636EFA"
PORTFOLIO_COLOR = "#EF553B"


def chart_cumulative_returns(
    prices: pd.DataFrame,
    weights: dict[str, float],
    benchmark_ticker: str = "SPY",
) -> go.Figure:
    """Line chart of portfolio cumulative return vs. the S&P 500 benchmark.

    Args:
        prices: Adjusted closing prices for all tickers including benchmark.
        weights: Portfolio weights keyed by ticker.
        benchmark_ticker: Ticker symbol for the benchmark series.

    Returns:
        Plotly Figure.
    """
    daily_returns = compute_daily_returns(prices)
    portfolio_ret = compute_portfolio_returns(daily_returns, weights)
    portfolio_cum = compute_cumulative_returns(portfolio_ret)

    fig = go.Figure()

    # Benchmark
    if benchmark_ticker in daily_returns.columns:
        bench_cum = compute_cumulative_returns(daily_returns[benchmark_ticker])
        fig.add_trace(go.Scatter(
            x=bench_cum.index,
            y=(bench_cum - 1) * 100,
            name=f"{benchmark_ticker} (Benchmark)",
            line=dict(color=BENCHMARK_COLOR, dash="dash", width=2),
            hovertemplate="%{y:.2f}%<extra>SPY</extra>",
        ))

    # Portfolio
    fig.add_trace(go.Scatter(
        x=portfolio_cum.index,
        y=(portfolio_cum - 1) * 100,
        name="Portfolio",
        line=dict(color=PORTFOLIO_COLOR, width=2.5),
        hovertemplate="%{y:.2f}%<extra>Portfolio</extra>",
    ))

    fig.update_layout(
        title="Portfolio Cumulative Return vs. S&P 500",
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_ticksuffix="%",
        **_layout_defaults(),
    )
    return fig


def chart_normalized_prices(prices: pd.DataFrame, portfolio_tickers: list[str]) -> go.Figure:
    """Line chart of individual stock performance normalized to 100 at the start date.

    Args:
        prices: Adjusted closing prices.
        portfolio_tickers: List of ticker symbols to include (excludes benchmark).

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    available = [t for t in portfolio_tickers if t in prices.columns]

    for i, ticker in enumerate(available):
        series = prices[ticker].dropna()
        normalized = series / series.iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized,
            name=ticker,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            hovertemplate=f"%{{y:.1f}}<extra>{ticker}</extra>",
        ))

    fig.add_hline(y=100, line_dash="dot", line_color="gray", line_width=1)

    fig.update_layout(
        title="Individual Stock Performance (Normalized to 100)",
        xaxis_title="Date",
        yaxis_title="Indexed Price (Start = 100)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **_layout_defaults(),
    )
    return fig


def chart_correlation_heatmap(prices: pd.DataFrame, portfolio_tickers: list[str]) -> go.Figure:
    """Annotated heatmap of pairwise return correlations between portfolio holdings.

    Args:
        prices: Adjusted closing prices.
        portfolio_tickers: Tickers to include (benchmark excluded).

    Returns:
        Plotly Figure.
    """
    available = [t for t in portfolio_tickers if t in prices.columns]
    daily_returns = compute_daily_returns(prices[available])
    corr = compute_correlation_matrix(daily_returns)

    # Build annotation text matrix
    text = corr.round(2).astype(str).values

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        text=text,
        texttemplate="%{text}",
        colorscale="RdBu_r",
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Correlation"),
        hovertemplate="<b>%{y} / %{x}</b><br>Correlation: %{z:.3f}<extra></extra>",
    ))

    fig.update_layout(
        title="Pairwise Return Correlation Matrix",
        xaxis_title="",
        yaxis_title="",
        **_layout_defaults(),
    )
    return fig


def chart_allocation_pie(weights: dict[str, float]) -> go.Figure:
    """Pie chart showing portfolio weight allocation.

    Args:
        weights: Dict of ticker -> weight (should sum to 1.0).

    Returns:
        Plotly Figure.
    """
    labels = list(weights.keys())
    values = [w * 100 for w in weights.values()]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=PALETTE[:len(labels)]),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title="Portfolio Allocation",
        **_layout_defaults(),
    )
    return fig


def chart_drawdown(
    prices: pd.DataFrame,
    weights: dict[str, float],
    benchmark_ticker: str = "SPY",
) -> go.Figure:
    """Area chart showing portfolio drawdown over time vs. benchmark.

    Args:
        prices: Adjusted closing prices.
        weights: Portfolio weights.
        benchmark_ticker: Ticker for the benchmark.

    Returns:
        Plotly Figure.
    """
    daily_returns = compute_daily_returns(prices)
    portfolio_ret = compute_portfolio_returns(daily_returns, weights)
    portfolio_dd = compute_drawdown_series(portfolio_ret) * 100

    fig = go.Figure()

    if benchmark_ticker in daily_returns.columns:
        bench_dd = compute_drawdown_series(daily_returns[benchmark_ticker]) * 100
        fig.add_trace(go.Scatter(
            x=bench_dd.index,
            y=bench_dd,
            name=f"{benchmark_ticker} Drawdown",
            fill="tozeroy",
            line=dict(color=BENCHMARK_COLOR, dash="dash", width=1.5),
            fillcolor="rgba(99,110,250,0.15)",
            hovertemplate="%{y:.2f}%<extra>SPY Drawdown</extra>",
        ))

    fig.add_trace(go.Scatter(
        x=portfolio_dd.index,
        y=portfolio_dd,
        name="Portfolio Drawdown",
        fill="tozeroy",
        line=dict(color=PORTFOLIO_COLOR, width=2),
        fillcolor="rgba(239,85,59,0.2)",
        hovertemplate="%{y:.2f}%<extra>Portfolio Drawdown</extra>",
    ))

    fig.update_layout(
        title="Portfolio Drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_ticksuffix="%",
        **_layout_defaults(),
    )
    return fig


def _layout_defaults() -> dict:
    """Shared Plotly layout settings for a consistent look across all charts."""
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif", size=13),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
