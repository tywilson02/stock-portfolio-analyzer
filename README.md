# AlphaTrack

A Python web app for analyzing equity portfolio performance. Enter a list of tickers, pick a date range, and get returns, risk metrics, and interactive charts — all pulled from live Yahoo Finance data.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red) ![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Market snapshot** — SPY, QQQ, and DIA prices with daily % change, cached and refreshed every 5 minutes
- **Portfolio metrics** — total return, annualized return, volatility, Sharpe ratio, max drawdown, correlation
- **Benchmark comparison** — portfolio return vs. SPY across all charts and the summary table
- **Auto-generated summary** — plain-English performance breakdown built from the actual computed values
- **Best & worst performer** — top and bottom holdings by total return, pulled dynamically
- **Interactive charts** — cumulative return, normalized prices, correlation heatmap, allocation pie, drawdown
- **Custom weights** — equal-weight by default; sliders for manual allocation
- **CSV export** — metrics table and full price history

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/your-username/alphatrack.git
cd alphatrack

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Usage

1. Enter comma-separated tickers in the sidebar (e.g. `AAPL, MSFT, NVDA`)
2. Set a start and end date — defaults to the past year
3. Toggle equal weight off to set custom allocations
4. Click **▶ Analyze Portfolio**
5. Export results as CSV or click **🔄 Reset** to start over

---

## Metrics

| Metric | Formula |
|---|---|
| **Total Return** | `(End Price − Start Price) / Start Price × 100` |
| **Annualized Return** | `(1 + Total Return)^(252/n) − 1` |
| **Annualized Volatility** | `StdDev(daily returns) × √252` |
| **Sharpe Ratio** | `(Ann. Return − Risk-Free Rate) / Ann. Volatility` — above 1 is good, above 2 is strong |
| **Max Drawdown** | Largest peak-to-trough decline over the period |
| **Correlation** | Pearson correlation of daily returns — lower values mean better diversification |

Risk-free rate: **4.5% annualized** (U.S. T-bill approximation).

---

## Project Structure

```
alphatrack/
├── app.py                  # Streamlit UI
├── data/
│   └── fetcher.py          # yfinance data fetching and caching
├── analysis/
│   ├── metrics.py          # Portfolio calculations
│   └── charts.py           # Plotly figures
├── utils/
│   └── export.py           # CSV export
└── requirements.txt
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web dashboard |
| [yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Finance data |
| [pandas](https://pandas.pydata.org) | Data manipulation |
| [NumPy](https://numpy.org) | Numerical calculations |
| [Plotly](https://plotly.com/python/) | Interactive charts |

---

> Data sourced from Yahoo Finance. For educational purposes only — not financial advice.
