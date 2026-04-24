# Stock Portfolio Analyzer

An interactive web dashboard for analyzing historical equity portfolio performance. Built with Python, Streamlit, and Plotly — fetches real market data from Yahoo Finance.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red) ![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Live market data** — pulls adjusted closing prices for any Yahoo Finance ticker
- **Portfolio metrics** — returns, volatility, Sharpe ratio, max drawdown, correlation
- **Interactive charts** — cumulative return, normalized price comparison, correlation heatmap, allocation pie, drawdown area chart
- **Benchmark comparison** — portfolio performance measured against SPY (S&P 500 ETF)
- **Custom weights** — equal-weight default with per-ticker sliders
- **CSV export** — download the metrics table and raw price history

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
git clone https://github.com/your-username/stock-portfolio-analyzer.git
cd stock-portfolio-analyzer

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The dashboard opens automatically at `http://localhost:8501`.

---

## How to Use

1. **Enter tickers** — type comma-separated symbols in the sidebar (e.g. `AAPL, MSFT, NVDA`)
2. **Set a date range** — default is the past 3 years
3. **Adjust weights** — toggle equal weight off to set custom allocations with sliders
4. **Click Analyze Portfolio** — all charts and metrics update instantly
5. **Export** — download metrics or raw prices as CSV

---

## Metric Glossary

| Metric | Formula / Explanation |
|---|---|
| **Total Return** | `(End Price − Start Price) / Start Price × 100` — the raw gain or loss over the period |
| **Annualized Return** | `(1 + Total Return)^(252/n) − 1` — total return scaled to a per-year figure using compound growth |
| **Annualized Volatility** | `StdDev(daily returns) × √252` — how much the portfolio fluctuates on an annual basis; higher = more risk |
| **Sharpe Ratio** | `(Ann. Return − Risk-Free Rate) / Ann. Volatility` — return earned per unit of risk taken; >1 is generally considered good, >2 is excellent |
| **Max Drawdown** | The largest percentage drop from any peak to the subsequent trough — measures worst-case loss an investor would have experienced |
| **Correlation** | Pearson correlation of daily returns between two assets; ranges from −1 (perfectly inverse) to +1 (perfectly synchronized) |

Risk-free rate used: **4.5% annualized** (approximate current U.S. T-bill yield).

---

## Project Structure

```
stock-portfolio-analyzer/
├── app.py                  # Streamlit UI — sidebar inputs, layout, tabs
├── data/
│   └── fetcher.py          # yfinance wrapper with Streamlit caching
├── analysis/
│   ├── metrics.py          # All financial calculations (pure functions)
│   └── charts.py           # Plotly figure builders
├── utils/
│   └── export.py           # CSV serialization for download buttons
└── requirements.txt
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web dashboard framework |
| [yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Finance data API |
| [pandas](https://pandas.pydata.org) | Data manipulation and time series |
| [NumPy](https://numpy.org) | Numerical calculations |
| [Plotly](https://plotly.com/python/) | Interactive charts |

---

## Disclaimer

Data is sourced from Yahoo Finance. Past performance is not indicative of future results. This tool is for educational and informational purposes only and does not constitute financial advice.
