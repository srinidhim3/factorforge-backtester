import pandas as pd

from engine.strategy_factory import StrategyFactory


def make_price_df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=20, freq="D")
    # create two tickers with different trends
    a = list(range(20, 40))
    b = list(range(40, 20, -1))
    return pd.DataFrame({"A": a, "B": b}, index=idx)


def test_strategy_factory_boolean_sma_topn() -> None:
    price = make_price_df()
    cfg = {
        "name": "test1",
        "universe": ["A", "B"],
        "features": [
            {"id": "sma3", "name": "sma", "params": {"length": 3}},
            {"id": "sma6", "name": "sma", "params": {"length": 6}},
        ],
        "signal": {"type": "boolean_expression", "expression": "sma3 > sma6"},
        "ranking": {"method": "rank", "top_n": 1},
        "sizing": {"method": "equal_weight", "long_only": True},
    }

    sf = StrategyFactory(cfg)
    weights = sf.generate_targets(price)

    # weights should be DataFrame with same index and columns
    assert isinstance(weights, pd.DataFrame)
    assert weights.index.equals(price.index)
    assert list(weights.columns) == ["A", "B"]

    # Each row should sum to either 0.0 or 1.0 (top_n=1 -> weight 1 on selected ticker)
    row_sums = weights.sum(axis=1)
    assert all((row_sums == 0) | (row_sums == 1))
