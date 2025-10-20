import pandas as pd
from engine.backtester import backtest_from_weights


def make_prices_two() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {"A": [100, 101, 102, 101, 103], "B": [200, 199, 201, 202, 200]}, index=idx
    )


def test_backtester_plot_output(tmp_path) -> None:
    prices = make_prices_two()
    # simple equal-weights
    weights = pd.DataFrame(0.5, index=prices.index, columns=prices.columns)

    outdir = tmp_path / "plots"
    returns, positions, metrics = backtest_from_weights(
        prices,
        weights,
        execution="same_close",
        transaction_cost_bps=0.0,
        plot=True,
        plot_outdir=str(outdir),
    )

    # returns is a pandas Series with same index as prices
    assert isinstance(returns, pd.Series)
    assert list(returns.index) == list(prices.index)

    # positions is a DataFrame aligned to index
    assert isinstance(positions, pd.DataFrame)
    assert list(positions.columns) == list(prices.columns)

    # metrics contains expected keys
    for k in (
        "cumulative_return",
        "annualized_return",
        "annualized_volatility",
        "max_drawdown",
        "total_turnover",
    ):
        assert k in metrics

    # verify file created
    out_file = outdir / "backtest_prices_and_wealth.png"
    assert out_file.exists()
