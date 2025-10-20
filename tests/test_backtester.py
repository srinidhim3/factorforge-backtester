import pandas as pd

from engine.backtester import backtest_from_weights


def make_prices_single() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=4, freq="D")
    # simple increasing prices -> positive returns
    return pd.DataFrame({"A": [100, 101, 102, 103]}, index=idx)


def test_single_ticker_pass_through() -> None:
    prices = make_prices_single()
    # weights always 1 on A
    weights = pd.DataFrame(1.0, index=prices.index, columns=prices.columns)
    returns, positions, metrics = backtest_from_weights(
        prices, weights, execution="same_close", transaction_cost_bps=0.0
    )

    # returns should equal price pct_change with NaN replaced by 0 for first period
    expected = prices.pct_change().fillna(0.0)["A"]
    # align name
    returns.name = expected.name
    pd.testing.assert_series_equal(returns, expected)


def test_two_ticker_equal_weight_and_costs() -> None:
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"A": [100, 110, 121], "B": [200, 198, 198]}, index=idx)
    # equal weight across two tickers from start
    weights = pd.DataFrame(0.5, index=idx, columns=["A", "B"])

    returns, positions, metrics = backtest_from_weights(
        prices, weights, execution="same_close", transaction_cost_bps=0.01
    )

    # gross returns for 2024-01-02: ((110/100-1)*0.5 + (198/200-1)*0.5)
    r1 = (0.1 * 0.5) + ((198 / 200 - 1) * 0.5)
    # initial turnover cost is applied on the first index; returns.iloc[1] equals gross return
    assert abs(returns.iloc[1] - r1) < 1e-9
