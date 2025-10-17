# Selected ideas (Yahoo-feasible MVP)

This document lists the subset of project ideas that are fully feasible using free market data sources such as Yahoo Finance (and common public free datasets). Each idea includes a short description, MVP scope, essential inputs (from Yahoo), limitations, and next steps.

---

## 1) Algorithmic backtester (factor investing) — Fully feasible

Short description
- Backtesting engine for factor-based strategies (momentum, size, basic value proxies) with portfolio-level performance, returns, and risk attribution.

MVP scope
- Price-based backtests (daily), simple factor construction (momentum, size by market cap, value proxies like P/E, P/B from Yahoo), position sizing (equal weight, volatility-scaled), basic transaction-cost model, and summary metrics (CAGR, Sharpe, max drawdown), plus exportable CSV/JSON results.

Essential inputs (Yahoo)
- Historical prices (adjusted close), market cap (or price & shares), basic fundamentals (P/E, P/B where available), dividends and splits.

Limitations
- Advanced fundamental or proprietary factor inputs are limited by Yahoo's fundamentals coverage and freshness; corporate actions/earnings surprises granularity may be imperfect.

Next steps
- Implement FastAPI endpoint for running backtests; add caching and persistence for price histories.

---

## 2) Portfolio optimization (mean-variance, Black–Litterman) — Fully feasible

Short description
- Library to compute portfolio allocations using historical returns (mean-variance) and incorporate views via a Black–Litterman wrapper.

MVP scope
- Historical returns-based optimizer, covariance estimation, constraints (long-only, weight bounds), simple Black–Litterman implementation accepting user views, and output of allocations plus diagnostics (expected return, volatility, weights).

Essential inputs (Yahoo)
- Historical prices (returns), market-cap or benchmark returns for BL priors (can be approximated using broad indices from Yahoo).

Limitations
- Black–Litterman requires a market-cap weighted prior and subjective views; for robust priors, additional factor data helps but is not required for an MVP.

Next steps
- Provide a CLI to compute optimized allocations from a tickers list and date range; persist results for report generation.

---

## 3) Risk dashboard (VaR, drawdowns, scenario analytics) — Fully feasible

Short description
- Dashboard that computes portfolio risk metrics: parametric and historical VaR, expected shortfall, drawdowns, rolling volatility, and simple scenario analysis based on historical shocks.

MVP scope
- Compute historical VaR, parametric VaR, ES, rolling volatility, max drawdown, and simple stress tests using historical worst-day scenarios; interactive time-range filters and CSV export.

Essential inputs (Yahoo)
- Historical prices (returns) and index data for benchmarks; optionally basic fund holdings supplied by user.

Limitations
- Macro-driven scenario libraries and multi-factor stress-tests need extra macro/factor feeds (FRED or paid sources) for richer analysis.

Next steps
- Wire risk endpoints into the backtester outputs and build a Streamlit dashboard for quick visualization.

---

## 4) Automated report generator (performance & attribution PDFs) — Fully feasible

Short description
- Tool to assemble backtest and portfolio analytics into a client-ready HTML/PDF report, including summary tables, charts, and risk metrics.

MVP scope
- Generate templated HTML reports with performance summary, returns charts, drawdown table, basic attribution (period returns vs benchmark), and export to PDF.

Essential inputs (Yahoo)
- Backtest returns and historical prices (from Yahoo) used to compute metrics and charts.

Limitations
- Advanced attribution that requires holdings-level trade logs or external custodial data will need additional inputs; simple returns-based attribution is feasible.

Next steps
- Implement a templating system (Jinja2 or similar) and a small runner that accepts backtest UUID and outputs a report.

---

## 5) CLI: ticker → standardized financial summary & memo — Partially feasible (practical for basic memos)

Short description
- Command-line tool that fetches basic price/fundamental snapshots and renders a concise investment memo (key ratios, price chart, short commentary).

MVP scope
- Fetch current price, 1Y/3Y returns, key ratios (P/E, P/B, market cap) from Yahoo, and produce a markdown memo or short PDF.

Essential inputs (Yahoo)
- Snapshot fundamentals and latest prices.

Limitations
- Deep accounting traceability and qualitative notes are out of scope with Yahoo-only data.

Next steps
- Add a templated memo generator and integrate it with the report generator for consistent outputs.

---

# Combined MVP recommendation (Yahoo-only)

Start with: (1) Algorithmic backtester, (2) Portfolio optimizer, (3) Risk dashboard, and (4) Automated report generator — these four form a consistent workflow (data → backtest/optimize → risk → report) and are fully implementable with Yahoo price/fundamental data.

Quick tech suggestions
- Backend: Python, FastAPI for APIs, pandas/numpy for data, PyPortfolioOpt or custom optimizer; store cached price data in SQLite or lightweight file cache.
- Frontend: Streamlit for rapid dashboards and CLI for quick memos.
- Reporting: Jinja2 + WeasyPrint or wkhtmltopdf for HTML → PDF.

# Next actions
- If you confirm, I'll update the todo list to set the chosen MVP tasks (prototype backtester, optimizer, risk endpoints, report generator) as next in-progress items and scaffold a minimal repo structure and starter files.

---

Updated on {date}.
