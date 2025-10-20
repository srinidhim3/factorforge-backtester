"""Visualize an end-to-end backtest run.

Generates and saves three PNGs under `scripts/output/`:
- backtest_prices_and_wealth.png
- weights_stack.png
- equity_curve.png

Usage:
  conda activate factorforge
  python scripts/visualize_backtest.py --tickers AAPL MSFT --start 2024-01-01 --end 2025-01-01
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import types
import argparse

import pandas as pd


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module {module_name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


repo_root = Path(__file__).resolve().parents[1]

# package shims
pkg = types.ModuleType("features")
pkg.__path__ = [str(repo_root / "features")]
sys.modules["features"] = pkg
pkg2 = types.ModuleType("data")
pkg2.__path__ = [str(repo_root / "data")]
sys.modules["data"] = pkg2

# load modules
sf_mod = load_module(
    "engine.strategy_factory", repo_root / "engine" / "strategy_factory.py"
)
fs_mod = load_module(
    "features.feature_store", repo_root / "features" / "feature_store.py"
)
bt_mod = load_module("engine.backtester", repo_root / "engine" / "backtester.py")
pf_mod = load_module("data.price_fetcher", repo_root / "data" / "price_fetcher.py")

StrategyFactory = sf_mod.StrategyFactory
compute_indicator = fs_mod.compute_indicator
backtest_from_weights = bt_mod.backtest_from_weights
fetch_adjusted_prices = pf_mod.fetch_adjusted_prices
# plotting helpers centralized in engine.backtester
plot_weights_stack = bt_mod.plot_weights_stack
plot_equity_curve = bt_mod.plot_equity_curve


def fetch_price_df(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    frames = []
    for t in tickers:
        df = fetch_adjusted_prices(t, start, end)
        frames.append(df["Close"].rename(t))
    return pd.concat(frames, axis=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tickers", nargs="+", default=["AAPL", "MSFT"]
    )  # default real tickers
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2025-01-01")
    args = parser.parse_args()

    price = fetch_price_df(args.tickers, args.start, args.end)

    cfg = {
        "name": "viz_demo",
        "universe": args.tickers,
        "features": [
            {"id": "sma3", "name": "sma", "params": {"length": 3}},
            {"id": "sma5", "name": "sma", "params": {"length": 5}},
        ],
        "signal": {"type": "boolean_expression", "expression": "sma3 > sma5"},
        "ranking": {"method": "rank", "top_n": 1},
        "sizing": {"method": "equal_weight", "long_only": True},
    }

    sf = StrategyFactory(cfg)
    weights = sf.generate_targets(price)

    # compute features
    feats = {}
    for feat in cfg["features"]:
        fid = feat["id"]
        params = feat.get("params", {})
        out_df = pd.DataFrame(index=price.index)
        for col in price.columns:
            single = pd.DataFrame({"Close": price[col]}, index=price.index)
            ind = compute_indicator(
                single, feat.get("name", feat.get("indicator", fid)).lower(), params
            )
            out_df[col] = ind.iloc[:, 0]
        feats[fid] = out_df

    out_path = Path(__file__).parent / "output"
    out_path.mkdir(parents=True, exist_ok=True)

    # Run backtest and let the backtester produce the aggregate price vs wealth plot
    returns, positions, metrics = backtest_from_weights(
        price,
        weights,
        execution="next_close",
        transaction_cost_bps=0.001,
        plot=True,
        plot_outdir=str(out_path),
    )

    # generate the remaining plots using centralized helpers
    plot_weights_stack(positions, out_path)
    plot_equity_curve(returns, out_path)

    print("Saved plots to:", out_path)
    print("Metrics:", metrics)


if __name__ == "__main__":
    main()
