"""
Stock Portfolio Analyzer — Streamlit entry point.

Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from data.fetcher import fetch_prices, validate_date_range, BENCHMARK_TICKER
from analysis.metrics import (
    compute_daily_returns,
    compute_portfolio_returns,
    build_summary_metrics,
)
from analysis.charts import (
    chart_cumulative_returns,
    chart_normalized_prices,
    chart_correlation_heatmap,
    chart_allocation_pie,
    chart_drawdown,
)
from utils.export import metrics_to_csv, prices_to_csv


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Stock Portfolio Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Metric card styling */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Tighten sidebar */
    section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
    /* Section dividers */
    hr { border-color: rgba(255,255,255,0.1); margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar — inputs ──────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📈 Portfolio Analyzer")
    st.markdown("---")

    # Ticker input
    st.subheader("Holdings")
    raw_tickers = st.text_input(
        "Tickers (comma-separated)",
        value="AAPL, MSFT, GOOGL, AMZN, META",
        help="Enter valid Yahoo Finance ticker symbols, e.g. AAPL, MSFT, TSLA",
    )
    tickers: list[str] = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

    # Date range
    st.markdown("---")
    st.subheader("Date Range")
    default_end = date.today() - timedelta(days=1)
    default_start = default_end - timedelta(days=3 * 365)

    start_date = st.date_input("Start date", value=default_start, max_value=default_end)
    end_date = st.date_input("End date", value=default_end, max_value=date.today())

    # Weights
    st.markdown("---")
    st.subheader("Portfolio Weights")
    equal_weight = st.toggle("Equal weight", value=True)

    weights: dict[str, float] = {}
    if tickers:
        if equal_weight:
            w = 1.0 / len(tickers)
            weights = {t: w for t in tickers}
            st.caption(f"Each position: {w * 100:.1f}%")
        else:
            st.caption("Drag sliders — they'll be normalized to 100%.")
            raw_weights: dict[str, float] = {}
            for ticker in tickers:
                raw_weights[ticker] = st.slider(
                    ticker,
                    min_value=0,
                    max_value=100,
                    value=int(100 / len(tickers)),
                    step=1,
                    format="%d%%",
                )
            total = sum(raw_weights.values())
            if total == 0:
                st.warning("All weights are zero — using equal weight.")
                w = 1.0 / len(tickers)
                weights = {t: w for t in tickers}
            else:
                weights = {t: v / total for t, v in raw_weights.items()}

    st.markdown("---")
    analyze = st.button("Analyze Portfolio", type="primary", use_container_width=True)


# ── Main content ──────────────────────────────────────────────────────────────

st.title("Stock Portfolio Analyzer")
st.markdown("Analyze historical performance, risk metrics, and correlations for your equity portfolio.")

if not analyze:
    # Landing state
    st.info(
        "Configure your portfolio in the sidebar and click **Analyze Portfolio** to begin. "
        "Default tickers are pre-loaded — you can run immediately.",
        icon="ℹ️",
    )
    st.markdown("""
    **What this tool calculates:**
    | Metric | Description |
    |---|---|
    | Total Return | Cumulative gain/loss over the selected period |
    | Ann. Volatility | Annualized standard deviation of daily returns |
    | Sharpe Ratio | Excess return per unit of risk (risk-free rate: 4.5%) |
    | Max Drawdown | Largest peak-to-trough decline |
    | Correlation | How much stocks move together (lower = better diversification) |
    """)
    st.stop()


# ── Validation ────────────────────────────────────────────────────────────────

if len(tickers) == 0:
    st.error("Please enter at least one ticker symbol.")
    st.stop()

if len(tickers) > 20:
    st.error("Maximum 20 tickers supported at once.")
    st.stop()

date_err = validate_date_range(start_date, end_date)
if date_err:
    st.error(date_err)
    st.stop()


# ── Data fetch ────────────────────────────────────────────────────────────────

with st.spinner("Fetching market data from Yahoo Finance…"):
    prices, invalid_tickers = fetch_prices(tuple(tickers), start_date, end_date)

if invalid_tickers:
    st.warning(
        f"The following tickers returned no data and were skipped: "
        f"**{', '.join(invalid_tickers)}**. "
        "Check that the symbols are valid Yahoo Finance tickers.",
        icon="⚠️",
    )

# Remove invalid tickers from weights
valid_tickers = [t for t in tickers if t not in invalid_tickers and t in prices.columns]
if not valid_tickers:
    st.error("No valid tickers with available data. Please check your inputs.")
    st.stop()

# Renormalize weights to valid tickers only
raw_w = {t: weights[t] for t in valid_tickers}
total_w = sum(raw_w.values())
weights = {t: v / total_w for t, v in raw_w.items()}

if prices.empty or len(prices) < 5:
    st.error("Not enough price history in the selected date range. Try widening the date range.")
    st.stop()


# ── Metrics ───────────────────────────────────────────────────────────────────

daily_returns = compute_daily_returns(prices)
portfolio_ret = compute_portfolio_returns(daily_returns, weights)
summary = build_summary_metrics(prices, weights, BENCHMARK_TICKER)

# Top KPI row
st.markdown("### Portfolio Summary")
col1, col2, col3, col4, col5 = st.columns(5)
p = summary["Portfolio"]

col1.metric(
    "Total Return",
    f"{p['Total Return (%)']:.1f}%",
    delta=f"{p['Total Return (%)'] - summary.get(BENCHMARK_TICKER, pd.Series({'Total Return (%)': 0}))['Total Return (%)']:.1f}% vs SPY",
)
col2.metric("Ann. Return", f"{p['Ann. Return (%)']:.1f}%")
col3.metric("Ann. Volatility", f"{p['Ann. Volatility (%)']:.1f}%")
col4.metric("Sharpe Ratio", f"{p['Sharpe Ratio']:.2f}")
col5.metric("Max Drawdown", f"{p['Max Drawdown (%)']:.1f}%")

st.markdown("---")

# Full metrics table
with st.expander("Full Metrics Table", expanded=False):
    display = summary.T
    display.index.name = "Asset"
    st.dataframe(display.style.format({
        "Total Return (%)": "{:.2f}%",
        "Ann. Return (%)": "{:.2f}%",
        "Ann. Volatility (%)": "{:.2f}%",
        "Sharpe Ratio": "{:.3f}",
        "Max Drawdown (%)": "{:.2f}%",
    }), use_container_width=True)


# ── Charts ───────────────────────────────────────────────────────────────────

st.markdown("### Performance Charts")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Cumulative Return",
    "📊 Stock Comparison",
    "🌡️ Correlation",
    "🥧 Allocation",
    "📉 Drawdown",
])

with tab1:
    fig = chart_cumulative_returns(prices, weights, BENCHMARK_TICKER)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Shows how $1 invested in the portfolio (and SPY benchmark) has grown over time. "
        "Compounding means small daily differences accumulate significantly."
    )

with tab2:
    fig = chart_normalized_prices(prices, valid_tickers)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "All prices normalized to 100 at the start date so you can compare "
        "relative performance regardless of absolute price levels."
    )

with tab3:
    if len(valid_tickers) < 2:
        st.info("Correlation requires at least 2 valid tickers.")
    else:
        fig = chart_correlation_heatmap(prices, valid_tickers)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Values near **+1** mean the stocks move together (less diversification). "
            "Values near **0** or **−1** indicate low or inverse correlation "
            "(better diversification)."
        )

with tab4:
    fig = chart_allocation_pie(weights)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Portfolio weight allocation. Adjust weights using the sliders in the sidebar.")

with tab5:
    fig = chart_drawdown(prices, weights, BENCHMARK_TICKER)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Drawdown shows how far the portfolio has fallen from its previous peak at each point in time. "
        "The maximum drawdown is the deepest trough — a key measure of downside risk."
    )


# ── Export ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Export")

col_a, col_b, _ = st.columns([1, 1, 2])

with col_a:
    st.download_button(
        label="⬇️ Download Metrics (CSV)",
        data=metrics_to_csv(summary),
        file_name=f"portfolio_metrics_{start_date}_{end_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_b:
    portfolio_cols = [t for t in valid_tickers if t in prices.columns]
    if BENCHMARK_TICKER in prices.columns:
        portfolio_cols.append(BENCHMARK_TICKER)
    st.download_button(
        label="⬇️ Download Price History (CSV)",
        data=prices_to_csv(prices[portfolio_cols]),
        file_name=f"portfolio_prices_{start_date}_{end_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("---")
st.caption(
    "Data sourced from Yahoo Finance via yfinance. "
    "Past performance is not indicative of future results. "
    "This tool is for educational purposes only."
)
