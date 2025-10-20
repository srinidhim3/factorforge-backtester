"""Demo: build synthetic price DataFrame, run StrategyFactory, and print prices & weights.

Run: python scripts/demo_show_weights.py
"""

import importlib.util
import sys
from pathlib import Path
import types
import pandas as pd

# Load StrategyFactory module directly by file path to avoid package import issues in scripts
repo_root = Path(__file__).resolve().parents[1]
spec_path = repo_root / "engine" / "strategy_factory.py"
spec = importlib.util.spec_from_file_location("engine.strategy_factory", str(spec_path))
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load module from {spec_path}")
mod = importlib.util.module_from_spec(spec)
# Ensure a 'features' package exists in sys.modules so imports inside the module resolve

pkg_name = "features"
pkg = types.ModuleType(pkg_name)
pkg.__path__ = [str(repo_root / "features")]
sys.modules[pkg_name] = pkg

sys.modules["engine.strategy_factory"] = mod
spec.loader.exec_module(mod)
StrategyFactory = mod.StrategyFactory

# Load features.feature_store module so we can compute and display the raw feature columns
feat_spec_path = repo_root / "features" / "feature_store.py"
feat_spec = importlib.util.spec_from_file_location(
    "features.feature_store", str(feat_spec_path)
)
if feat_spec is None or feat_spec.loader is None:
    raise RuntimeError(f"Cannot load features module from {feat_spec_path}")
feat_mod = importlib.util.module_from_spec(feat_spec)
sys.modules["features.feature_store"] = feat_mod
feat_spec.loader.exec_module(feat_mod)
compute_indicator = feat_mod.compute_indicator


def make_price_df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=10, freq="D")
    # simple linear trends for two tickers
    a = [100 + i for i in range(len(idx))]
    b = [200 - 0.5 * i for i in range(len(idx))]
    return pd.DataFrame({"A": a, "B": b}, index=idx)


def main() -> None:
    price = make_price_df()

    cfg = {
        "name": "demo",
        "universe": ["A", "B"],
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

    # Compute and print SMA features used by the strategy
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

    print("Price DataFrame:\n", price)
    print("\nComputed feature: sma3\n", feats["sma3"])  # full table for clarity
    print("\nComputed feature: sma5\n", feats["sma5"])  # full table for clarity
    print("\nGenerated Weights DataFrame:\n", weights)


if __name__ == "__main__":
    main()
