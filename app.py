"""
AlphaTrack — Streamlit entry point.

Run with: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date, timedelta, datetime

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
    page_title="AlphaTrack",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# ── Global CSS ────────────────────────────────────────────────────────────────
# NOTE: The <style> block is safe to use multi-line — the markdown parser treats
# <style> as a raw HTML block and does not process its contents as markdown.
# All other HTML passed to st.markdown must be compact single-line strings to
# avoid the CommonMark 4-space indentation → code block rule.

st.markdown("""
<style>
/* ── Base ── */
.stApp { background-color: #0a0e1a; color: #e2e8f0; }
[data-testid="stAppViewContainer"] { background-color: #0a0e1a; }
[data-testid="stHeader"] { background-color: #0a0e1a; border-bottom: 1px solid #1a2540; }
[data-testid="stMainBlockContainer"] {
    max-width: 1200px;
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 1.5rem !important;
}

/* ── Sidebar container — no excess scroll ── */
section[data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid rgba(30,144,255,0.2); }
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.7rem;
    padding-bottom: 0 !important;
    overflow-y: auto;
    height: 100%;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-bottom: 0.5rem !important;
}
section[data-testid="stSidebar"] .stMarkdown p { color: #94a3b8; font-size: 0.78rem; }

/* ── Sidebar expander headers ── */
section[data-testid="stSidebar"] .streamlit-expanderHeader,
section[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background-color: #111827 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: 0.82rem;
    font-weight: 600;
}
section[data-testid="stSidebar"] [data-testid="stExpander"] { border: none !important; background: transparent !important; }

/* ── Sidebar compact layout ── */
section[data-testid="stSidebar"] details summary { padding-top: 6px !important; padding-bottom: 6px !important; font-size: 0.8rem !important; min-height: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"] > div > div { padding: 6px 4px !important; gap: 0 !important; }
section[data-testid="stSidebar"] .stTextInput, section[data-testid="stSidebar"] .stDateInput { margin-bottom: 0 !important; }
section[data-testid="stSidebar"] .stTextInput input, section[data-testid="stSidebar"] .stDateInput input { padding: 4px 8px !important; font-size: 0.82rem !important; min-height: 0 !important; }
section[data-testid="stSidebar"] .stTextInput label, section[data-testid="stSidebar"] .stDateInput label { font-size: 0.75rem !important; margin-bottom: 1px !important; padding-bottom: 0 !important; line-height: 1.3 !important; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
section[data-testid="stSidebar"] .stCaption { font-size: 0.67rem !important; margin: 1px 0 3px 0 !important; line-height: 1.3 !important; color: #475569 !important; }
section[data-testid="stSidebar"] .stToggle { margin-top: 3px !important; margin-bottom: 1px !important; }
section[data-testid="stSidebar"] .stToggle > label { font-size: 0.82rem !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin: 0 !important; line-height: 1.2 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="element-container"] { margin-bottom: 2px !important; }

/* ── Analyze button (primary) ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1e90ff, #0066cc);
    border: none; color: white; font-weight: 700; font-size: 0.95rem;
    border-radius: 8px; padding: 0.6rem 1rem; letter-spacing: 0.02em;
    transition: opacity 0.2s, transform 0.1s;
    box-shadow: 0 2px 12px rgba(30,144,255,0.3);
}
.stButton > button[kind="primary"]:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(30,144,255,0.4); }
.stButton > button[kind="primary"]:active { transform: translateY(0); }

/* ── Reset button (secondary) ── */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background-color: transparent;
    border: 1px solid #1e3a5f;
    color: #64748b;
    font-size: 0.8rem;
    border-radius: 6px;
    padding: 4px 10px;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover { background-color: #111827; color: #94a3b8; border-color: #334155; }

/* ── Download buttons ── */
.stDownloadButton > button { background-color: #111827; border: 1px solid rgba(30,144,255,0.4); color: #1e90ff; border-radius: 8px; font-weight: 500; transition: background 0.2s; }
.stDownloadButton > button:hover { background-color: rgba(30,144,255,0.1); }

/* ── Inputs ── */
.stTextInput > div > div > input, .stDateInput > div > div > input { background-color: #111827; border: 1px solid #1e3a5f; color: #e2e8f0; border-radius: 6px; }
.stTextInput > div > div > input:focus, .stDateInput > div > div > input:focus { border-color: #1e90ff; box-shadow: 0 0 0 2px rgba(30,144,255,0.15); }
.stTextInput label, .stDateInput label { color: #94a3b8 !important; font-size: 0.8rem !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background-color: #111827; border-radius: 8px; padding: 4px; gap: 4px; border-bottom: none; }
.stTabs [data-baseweb="tab"] { background-color: transparent; color: #94a3b8; border-radius: 6px; font-weight: 500; padding: 6px 16px; }
.stTabs [aria-selected="true"] { background-color: rgba(30,144,255,0.15) !important; color: #1e90ff !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1rem; }

/* ── Expander (main area) ── */
.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1a2540; border-radius: 8px; color: #94a3b8; }

/* ── Dividers ── */
hr { border: none; border-top: 1px solid #1a2540; margin: 1.5rem 0; }

/* ── Captions ── */
.stCaption, [data-testid="stCaptionContainer"] { color: #64748b !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1a2540; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #1e90ff; }

/* ── Hero header ── */
.hero-container { text-align: center; padding: 1.8rem 0 1rem 0; }
.hero-title { font-size: 2.8rem; font-weight: 800; color: #1e90ff; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 0.35rem; }
.hero-subtitle { font-size: 0.95rem; color: #64748b; margin-bottom: 1.2rem; }
.hero-divider { height: 2px; background: linear-gradient(90deg, transparent, #1e90ff, transparent); border: none; margin: 0 auto; width: 50%; }

/* ── Section headers ── */
.section-header { font-size: 0.68rem; font-weight: 700; color: #1e90ff; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 12px 0; }

/* ── Sidebar footer ── */
.sidebar-footer { font-size: 0.67rem; color: #2d3f52; text-align: center; line-height: 1.6; padding: 8px 0; border-top: 1px solid #1a2540; margin-top: 8px; }

/* ── Market snapshot ── */
.market-bar-label { font-size: 0.67rem; font-weight: 700; color: #1e90ff; text-transform: uppercase; letter-spacing: 0.1em; }
.market-timestamp { font-size: 0.65rem; color: #334155; }
.market-mini-card { background: #0d1117; border: 1px solid #1a2540; border-radius: 10px; padding: 12px 16px; display: flex; align-items: center; gap: 14px; }
.market-ticker { font-size: 0.85rem; font-weight: 700; color: #e2e8f0; min-width: 32px; }
.market-label-name { font-size: 0.72rem; color: #64748b; line-height: 1.2; }
.market-price { font-size: 1rem; font-weight: 600; color: #e2e8f0; font-variant-numeric: tabular-nums; margin-left: auto; text-align: right; }
.market-change { font-size: 0.8rem; font-weight: 600; font-variant-numeric: tabular-nums; min-width: 60px; text-align: right; }

/* ── Summary insight box ── */
.summary-insight { background: rgba(30,144,255,0.06); border-left: 3px solid #1e90ff; border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 4px 0 20px 0; font-size: 0.92rem; color: #cbd5e1; line-height: 1.7; }

/* ── KPI cards ── */
.kpi-card { background: #111827; border: 1px solid rgba(30,144,255,0.25); border-radius: 12px; padding: 18px 20px; display: flex; flex-direction: column; gap: 6px; transition: border-color 0.2s; height: 100%; }
.kpi-card:hover { border-color: rgba(30,144,255,0.55); }
.kpi-icon { font-size: 1.3rem; line-height: 1; }
.kpi-label { font-size: 0.7rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi-delta { font-size: 0.73rem; color: #64748b; margin-top: 2px; }
.kpi-positive { color: #10b981; }
.kpi-negative { color: #ef4444; }
.kpi-neutral  { color: #e2e8f0; }

/* ── Performer cards ── */
.performer-card { background: #111827; border-radius: 12px; padding: 16px 20px; display: flex; flex-direction: column; gap: 6px; height: 100%; }
.performer-card-best  { border: 1px solid rgba(16,185,129,0.35); }
.performer-card-worst { border: 1px solid rgba(239,68,68,0.35); }
.performer-badge { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.performer-badge-best  { color: #10b981; }
.performer-badge-worst { color: #ef4444; }
.performer-ticker { font-size: 1.4rem; font-weight: 800; color: #e2e8f0; letter-spacing: -0.01em; }
.performer-return-best  { font-size: 1rem; font-weight: 600; color: #10b981; }
.performer-return-worst { font-size: 1rem; font-weight: 600; color: #ef4444; }
</style>
""", unsafe_allow_html=True)


# ── Cached helpers ────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_market_snapshot() -> list[dict]:
    """Fetch last two days of closes for SPY, QQQ, DIA. TTL=5 min."""
    _labels = {"SPY": "S&P 500", "QQQ": "Nasdaq 100", "DIA": "Dow Jones"}
    fetched_at = datetime.now().strftime("%I:%M %p").lstrip("0")
    result: list[dict] = []
    try:
        raw = yf.download(
            list(_labels.keys()),
            period="2d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if raw.empty:
            return result
        closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        for ticker, label in _labels.items():
            if ticker not in closes.columns:
                continue
            series = closes[ticker].dropna()
            if len(series) < 2:
                continue
            prev = float(series.iloc[-2])
            curr = float(series.iloc[-1])
            pct  = (curr - prev) / prev * 100
            result.append({
                "ticker":     ticker,
                "label":      label,
                "price":      curr,
                "change":     pct,
                "fetched_at": fetched_at,
            })
    except Exception:
        pass
    return result


# ── Pure UI helpers ───────────────────────────────────────────────────────────

def _color_class(value: float, invert: bool = False) -> str:
    """Return a CSS class name based on the sign of value."""
    if invert:
        return "kpi-positive" if value <= 0 else "kpi-negative"
    return "kpi-positive" if value > 0 else "kpi-negative"


def _kpi_card(icon: str, label: str, value: str, color_class: str, delta: str = "") -> str:
    """Return a compact single-line HTML string for one KPI card.

    Single-line is required: Streamlit's markdown parser treats lines with
    4+ leading spaces as code blocks, which would render as raw HTML text.
    """
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {color_class}">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def _build_summary_text(
    valid_tickers: list[str],
    start: date,
    end: date,
    total_ret: float,
    ann_ret: float,
    vol: float,
    sharpe: float,
    drawdown: float,
    vs_spy: float,
) -> str:
    """Compose a plain-English paragraph summarising portfolio performance."""
    n = len(valid_tickers)
    if n == 1:
        holdings = valid_tickers[0]
    elif n == 2:
        holdings = f"{valid_tickers[0]} and {valid_tickers[1]}"
    else:
        holdings = ", ".join(valid_tickers[:-1]) + f", and {valid_tickers[-1]}"

    start_str = f"{start.strftime('%b')} {start.day}, {start.year}"
    end_str   = f"{end.strftime('%b')} {end.day}, {end.year}"

    vs_spy_str = (
        f"outperforming SPY by {vs_spy:+.1f}%"
        if vs_spy > 0
        else f"underperforming SPY by {abs(vs_spy):.1f}%"
    )

    if sharpe > 2.0:
        sharpe_desc = "exceptional risk-adjusted returns"
    elif sharpe > 1.0:
        sharpe_desc = "strong risk-adjusted returns"
    elif sharpe > 0.0:
        sharpe_desc = "modest risk-adjusted returns"
    else:
        sharpe_desc = "below-average risk-adjusted returns"

    return (
        f"AlphaTrack analyzed your {n}-stock portfolio ({holdings}) "
        f"from {start_str} to {end_str}. "
        f"Your portfolio returned <strong>{total_ret:+.1f}%</strong> "
        f"({ann_ret:+.1f}% annualized), {vs_spy_str}. "
        f"The Sharpe Ratio of <strong>{sharpe:.2f}</strong> indicates {sharpe_desc}. "
        f"Maximum drawdown was <strong>{drawdown:.1f}%</strong>, "
        f"with annualized volatility of {vol:.1f}%."
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo — compact single-line HTML
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
        '<span style="font-size:1.4rem;">📈</span>'
        '<span style="font-size:1.15rem;font-weight:800;color:#1e90ff;letter-spacing:-0.01em;">AlphaTrack</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Analyze button — pinned at top
    if st.button("▶  Analyze Portfolio", type="primary", use_container_width=True):
        st.session_state.analyzed = True

    # Reset button
    if st.button("🔄 Reset", type="secondary", use_container_width=True):
        st.session_state.analyzed = False
        st.rerun()

    st.markdown('<hr style="margin:10px 0;">', unsafe_allow_html=True)

    # Portfolio Settings expander
    with st.expander("⚙️  Portfolio Settings", expanded=True):
        raw_tickers = st.text_input(
            "Tickers (comma-separated)",
            value="AAPL, MSFT, GOOGL, AMZN, META",
        )
        st.caption("Valid Yahoo Finance symbols, e.g. AAPL, NVDA, TSLA")

        tickers: list[str] = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

        equal_weight = st.toggle("Equal weight", value=True)
        st.caption("Split evenly, or set custom allocations below")

        weights: dict[str, float] = {}
        if tickers:
            if equal_weight:
                w = 1.0 / len(tickers)
                weights = {t: w for t in tickers}
            else:
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

    # Date Range expander
    with st.expander("📅  Date Range", expanded=True):
        default_end   = date.today()
        default_start = default_end - timedelta(days=365)

        start_date = st.date_input("Start date", value=default_start, max_value=default_end)
        st.caption("First day of the analysis window")

        end_date = st.date_input("End date", value=default_end, max_value=date.today())
        st.caption("Last day (defaults to today)")

    # Sidebar footer — compact single-line HTML
    st.markdown(
        '<div class="sidebar-footer" style="margin-top:16px;">'
        'Data sourced from Yahoo Finance<br>For educational purposes only'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Hero header — compact single-line HTML ────────────────────────────────────

st.markdown(
    '<div class="hero-container">'
    '<div class="hero-title">AlphaTrack</div>'
    '<div class="hero-subtitle">Real-time portfolio tracking and performance analysis</div>'
    '<hr class="hero-divider">'
    '</div>',
    unsafe_allow_html=True,
)


# ── Market snapshot bar ───────────────────────────────────────────────────────
# Each card is rendered via col.markdown() as a compact single-line string.
# This is intentional: splitting across st.columns avoids Streamlit's markdown
# parser from mangling a large multi-div HTML block.

snapshot = _fetch_market_snapshot()
if snapshot:
    fetched_at = snapshot[0].get("fetched_at", datetime.now().strftime("%I:%M %p").lstrip("0"))
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;">'
        f'<span class="market-bar-label">Markets</span>'
        f'<span class="market-timestamp">&#x1F504; Last updated {fetched_at}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    market_cols = st.columns(len(snapshot))
    for col, m in zip(market_cols, snapshot):
        change_color = "#10b981" if m["change"] >= 0 else "#ef4444"
        arrow = "&#9650;" if m["change"] >= 0 else "&#9660;"
        price_str = f"{m['price']:,.2f}"
        col.markdown(
            f'<div class="market-mini-card">'
            f'<div><div class="market-ticker">{m["ticker"]}</div>'
            f'<div class="market-label-name">{m["label"]}</div></div>'
            f'<div class="market-price">&#36;{price_str}</div>'
            f'<div class="market-change" style="color:{change_color};">'
            f'{arrow}&nbsp;{abs(m["change"]):.2f}%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<hr>', unsafe_allow_html=True)


# ── Landing state ─────────────────────────────────────────────────────────────

if not st.session_state.analyzed:
    st.info(
        "Configure your portfolio in the sidebar and click **▶ Analyze Portfolio** to begin. "
        "Default tickers are pre-loaded — you can run immediately.",
        icon="ℹ️",
    )
    st.markdown("""
**What AlphaTrack calculates:**

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

with st.spinner("Fetching market data..."):
    prices, invalid_tickers = fetch_prices(tuple(tickers), start_date, end_date)

if invalid_tickers:
    st.warning(
        f"The following tickers returned no data and were skipped: "
        f"**{', '.join(invalid_tickers)}**. "
        "Check that the symbols are valid Yahoo Finance tickers.",
        icon="⚠️",
    )

valid_tickers = [t for t in tickers if t not in invalid_tickers and t in prices.columns]
if not valid_tickers:
    st.error("No valid tickers with available data. Please check your inputs.")
    st.stop()

raw_w   = {t: weights[t] for t in valid_tickers}
total_w = sum(raw_w.values())
weights = {t: v / total_w for t, v in raw_w.items()}

if prices.empty or len(prices) < 5:
    st.error("Not enough price history in the selected date range. Try widening the date range.")
    st.stop()


# ── Metrics ───────────────────────────────────────────────────────────────────

daily_returns = compute_daily_returns(prices)
portfolio_ret = compute_portfolio_returns(daily_returns, weights)
summary       = build_summary_metrics(prices, weights, BENCHMARK_TICKER)
p             = summary["Portfolio"]
spy           = summary.get(BENCHMARK_TICKER, pd.Series({"Total Return (%)": 0}))

total_ret = float(p["Total Return (%)"])
ann_ret   = float(p["Ann. Return (%)"])
vol       = float(p["Ann. Volatility (%)"])
sharpe    = float(p["Sharpe Ratio"])
drawdown  = float(p["Max Drawdown (%)"])
spy_ret   = float(spy["Total Return (%)"])
vs_spy    = total_ret - spy_ret


# ── Portfolio summary paragraph ───────────────────────────────────────────────

summary_text = _build_summary_text(
    valid_tickers, start_date, end_date,
    total_ret, ann_ret, vol, sharpe, drawdown, vs_spy,
)
st.markdown(
    f'<div class="summary-insight">{summary_text}</div>',
    unsafe_allow_html=True,
)


# ── KPI cards ────────────────────────────────────────────────────────────────
# Rendered via st.columns so each col.markdown() call receives one compact
# single-line div — avoids the multi-div HTML block parsing issue.

st.markdown('<p class="section-header">Portfolio Metrics</p>', unsafe_allow_html=True)

kpi_cols = st.columns(5)
kpi_data = [
    ("📈", "Total Return",    f"{total_ret:+.1f}%", _color_class(total_ret),            f"{vs_spy:+.1f}% vs SPY"),
    ("📊", "Ann. Return",     f"{ann_ret:+.1f}%",   _color_class(ann_ret),              ""),
    ("⚡", "Ann. Volatility", f"{vol:.1f}%",         "kpi-neutral",                      ""),
    ("🎯", "Sharpe Ratio",    f"{sharpe:.2f}",       _color_class(sharpe),               ""),
    ("📉", "Max Drawdown",    f"{drawdown:.1f}%",    _color_class(drawdown, invert=True), ""),
]
for col, (icon, label, value, css_class, delta) in zip(kpi_cols, kpi_data):
    col.markdown(_kpi_card(icon, label, value, css_class, delta), unsafe_allow_html=True)


# ── Best & Worst performer callouts ──────────────────────────────────────────

stock_returns = {
    t: float(summary[t]["Total Return (%)"])
    for t in valid_tickers
    if t in summary.columns
}

if len(stock_returns) >= 2:
    best_ticker  = max(stock_returns, key=lambda k: stock_returns[k])
    worst_ticker = min(stock_returns, key=lambda k: stock_returns[k])
    best_ret     = stock_returns[best_ticker]
    worst_ret    = stock_returns[worst_ticker]

    col_best, col_worst = st.columns(2)
    col_best.markdown(
        f'<div class="performer-card performer-card-best">'
        f'<div class="performer-badge performer-badge-best">&#127942; Best Performer</div>'
        f'<div class="performer-ticker">{best_ticker}</div>'
        f'<div class="performer-return-best">{best_ret:+.1f}% total return</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    col_worst.markdown(
        f'<div class="performer-card performer-card-worst">'
        f'<div class="performer-badge performer-badge-worst">&#9888; Worst Performer</div>'
        f'<div class="performer-ticker">{worst_ticker}</div>'
        f'<div class="performer-return-worst">{worst_ret:+.1f}% total return</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr>', unsafe_allow_html=True)

with st.expander("Full Metrics Table", expanded=False):
    display = summary.T
    display.index.name = "Asset"
    st.dataframe(display.style.format({
        "Total Return (%)":    "{:.2f}%",
        "Ann. Return (%)":     "{:.2f}%",
        "Ann. Volatility (%)": "{:.2f}%",
        "Sharpe Ratio":        "{:.3f}",
        "Max Drawdown (%)":    "{:.2f}%",
    }), use_container_width=True)


# ── Charts ────────────────────────────────────────────────────────────────────

st.markdown('<hr>', unsafe_allow_html=True)
st.markdown('<p class="section-header">Performance Charts</p>', unsafe_allow_html=True)

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


# ── Export ────────────────────────────────────────────────────────────────────

st.markdown('<hr>', unsafe_allow_html=True)
st.markdown('<p class="section-header">Export</p>', unsafe_allow_html=True)

col_a, col_b, _ = st.columns([1, 1, 2])

with col_a:
    st.download_button(
        label="⬇️ Download Metrics (CSV)",
        data=metrics_to_csv(summary),
        file_name=f"alphatrack_metrics_{start_date}_{end_date}.csv",
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
        file_name=f"alphatrack_prices_{start_date}_{end_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption(
    "AlphaTrack · Data sourced from Yahoo Finance via yfinance · "
    "Past performance is not indicative of future results · "
    "For educational purposes only."
)
