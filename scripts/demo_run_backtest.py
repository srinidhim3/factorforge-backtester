"""End-to-end demo: StrategyFactory -> backtester

This script builds a synthetic price DataFrame, compiles a simple SMA crossover
strategy via `StrategyFactory`, generates weights, runs the vectorized
backtester, and prints prices, features, weights, returns, and metrics.
"""

import importlib.util
import sys
from pathlib import Path
import types

import pandas as pd
import argparse


# helper to load modules by path similarly to tests/demo
def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module {module_name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


repo_root = Path(__file__).resolve().parents[1]

# Register 'features' package shim (so feature_store imports succeed)
pkg = types.ModuleType("features")
pkg.__path__ = [str(repo_root / "features")]
sys.modules["features"] = pkg

# Register 'data' package shim and load price_fetcher
pkg_data = types.ModuleType("data")
pkg_data.__path__ = [str(repo_root / "data")]
sys.modules["data"] = pkg_data
pf_mod = load_module("data.price_fetcher", repo_root / "data" / "price_fetcher.py")
fetch_adjusted_prices = pf_mod.fetch_adjusted_prices

# Load StrategyFactory and feature compute function
sf_mod = load_module(
    "engine.strategy_factory", repo_root / "engine" / "strategy_factory.py"
)
fs_mod = load_module(
    "features.feature_store", repo_root / "features" / "feature_store.py"
)
bt_mod = load_module("engine.backtester", repo_root / "engine" / "backtester.py")

StrategyFactory = sf_mod.StrategyFactory
compute_indicator = fs_mod.compute_indicator
backtest_from_weights = bt_mod.backtest_from_weights


def fetch_price_df(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    # fetch each ticker and combine Close columns into a wide DataFrame
    frames = []
    for t in tickers:
        df = fetch_adjusted_prices(t, start, end)
        # ensure Close column present
        if "Close" not in df.columns:
            raise RuntimeError(f"No Close column for {t}")
        frames.append(df["Close"].rename(t))
    wide = pd.concat(frames, axis=1)
    return wide


def main() -> None:
    # CLI args are parsed to allow real tickers
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tickers", nargs="+", default=["AAPL", "MSFT"]
    )  # default real tickers
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2025-10-20")
    args = parser.parse_args()

    price = fetch_price_df(args.tickers, args.start, args.end)

    cfg = {
        "name": "demo_end_to_end",
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

    # compute features to display
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

    returns, positions, metrics = backtest_from_weights(
        price, weights, execution="next_close", transaction_cost_bps=0.001
    )

    print("Price:\n", price)
    print("\nFeatures (sma3):\n", feats["sma3"])
    print("\nFeatures (sma5):\n", feats["sma5"])
    print("\nWeights:\n", weights)
    print("\nNet returns:\n", returns)
    print("\nMetrics:\n", metrics)


if __name__ == "__main__":
    main()
