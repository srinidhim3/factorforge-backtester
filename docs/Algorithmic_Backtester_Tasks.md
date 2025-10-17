# **Project Setup**
- [ ] Set up project repository and folder structure (`repo root`): Initialize Git, create folders for `data`, `engine`, `api`, `ui`, `tests`, and `docs`. Acceptance: All folders exist, Git initialized.
- [ ] Create and commit `requirements.txt` with core dependencies (`repo root`): Add pandas, numpy, yfinance, fastapi, streamlit, pytest, etc. Acceptance: File lists all required packages, installs without error.
- [ ] Configure Python environment and virtualenv (`repo root`): Create and activate virtual environment, install dependencies. Acceptance: `python -m pip list` shows all packages.

# **Data Ingestion & Storage**
- [ ] Implement price data fetcher (`data/price_fetcher.py`): Function to download adjusted prices for tickers using yfinance. Acceptance: Returns DataFrame with correct columns for sample tickers/dates.
- [ ] Build raw snapshot storage (`data/snapshot_store.py`): Save fetched data as immutable parquet/CSV files. Acceptance: Files written/read, reproducible by ID.
- [ ] Add basic data hygiene checks (`data/normalizer.py`): Validate time index, fill/flag gaps, handle splits/dividends. Acceptance: Output DataFrame is clean, gaps flagged.

# **Feature Store & Engineering**
- [ ] Implement feature computation pipeline (`features/feature_store.py`): Calculate returns, moving averages, signals, and save with metadata. Acceptance: Features saved/loaded, metadata present.
- [ ] Add provenance logging for features (`features/provenance.py`): Log source, parameters, and timestamp for each feature. Acceptance: Log file/DB updated per run.

# **Strategy Interface**
- [ ] Create pluggable strategy interface (`engine/strategy.py`): Define base class for strategies, e.g., momentum, equal weight. Acceptance: Strategies accept historical data, emit target weights.
- [ ] Implement sample momentum strategy (`engine/momentum_strategy.py`): Use lookback window to generate weights. Acceptance: Returns expected weights for test data.

# **Backtest Engine**
- [ ] Build vectorized backtest loop (`engine/backtest_engine.py`): Simulate rebalancing, position sizing, transaction costs. Acceptance: Outputs trades, P&L for sample config.
- [ ] Integrate transaction cost & slippage model (`engine/transaction_cost.py`): Apply fixed bps and slippage to trades. Acceptance: Costs reflected in results.

# **Execution Simulator**
- [ ] Simulate order fills and latency (`engine/execution_simulator.py`): Model market/limit fills, lot rounding, partial fills. Acceptance: Simulated fills match expected logic.

# **Metrics & Attribution**
- [ ] Compute performance metrics (`engine/metrics.py`): Calculate returns, drawdowns, turnover, Sharpe, etc. Acceptance: Metrics correct for test runs.
- [ ] Add basic factor attribution (`engine/attribution.py`): Attribute returns to factors for sample strategies. Acceptance: Attribution table generated.

# **Reporting & Exports**
- [ ] Implement CSV/JSON export (`reporting/exporter.py`): Export results, trades, metrics. Acceptance: Files readable, match results.
- [ ] Generate summary charts (`reporting/charts.py`): Create matplotlib/plotly charts for performance. Acceptance: Charts render for sample data.
- [ ] Build HTML report generator (`reporting/html_report.py`): Assemble summary tables, charts, and metrics into HTML. Acceptance: HTML file opens, displays all sections.

# **CLI / API / UI**
- [ ] Create CLI runner for backtests (`cli/run_backtest.py`): Command-line tool to trigger backtest and export results. Acceptance: CLI runs, outputs files.
- [ ] Implement FastAPI endpoint (`api/main.py`): Expose run, inspect, and export endpoints. Acceptance: API responds to requests, returns results.
- [ ] Build Streamlit dashboard (`ui/dashboard.py`): Visualize results, allow user input for tickers/dates. Acceptance: Dashboard loads, displays charts and metrics.

# **Logging & Provenance**
- [ ] Add structured logging (`engine/logger.py`): Log inputs, transforms, and seeds for reproducibility. Acceptance: Log file/DB updated per run.

# **Testing & CI**
- [ ] Write unit tests for core math and edge cases (`tests/test_math.py`): Test feature calculations, engine logic. Acceptance: All tests pass.
- [ ] Add integration smoke test (`tests/test_integration.py`): Run end-to-end backtest with cached data. Acceptance: Test completes, results as expected.
- [ ] Set up GitHub Actions for CI (`.github/workflows/ci.yml`): Run tests on push/PR. Acceptance: CI passes, reports status.
