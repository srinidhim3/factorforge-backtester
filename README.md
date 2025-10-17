# FactorForge Backtester

A modular, auditable Python backtesting engine for factor investing strategies. Supports data ingestion, feature engineering, strategy simulation, metrics, reporting, and extensible APIs.

## Features
- Fetches historical price and fundamental data (Yahoo Finance)
- Pluggable strategy interface (momentum, equal weight, etc.)
- Vectorized backtest engine with transaction cost modeling
- Data hygiene, feature store, and provenance logging
- Metrics, attribution, and reporting (CSV/JSON/HTML)
- CLI, FastAPI, and Streamlit dashboard

## Installation

```bash
# Clone the repository
$ git clone https://github.com/srinidhim3/factorforge-backtester.git
$ cd factorforge-backtester

# (Recommended) Create and activate a conda environment
$ conda create -n factorforge python=3.12
$ conda activate factorforge

# Install dependencies
$ pip install -r requirements.txt
```

## Quick Start

```bash
# Run a sample backtest (CLI)
$ python cli/run_backtest.py --tickers AAPL MSFT --start 2022-01-01 --end 2023-01-01

# Launch the Streamlit dashboard
$ streamlit run ui/dashboard.py

# Start the FastAPI server
$ uvicorn api.main:app --reload
```

## Documentation
- [Project Overview](docs/Algorithmic_Backtester_Tasks.md)
- [Design & Tech Docs](docs/Ideation/)
- [API Reference](docs/API_REFERENCE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on bug reports, feature requests, and pull requests.

## License
[MIT License](LICENSE)
