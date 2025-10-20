import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from engine.backtester import (
    backtest_from_weights,
    plot_weights_stack,
    plot_equity_curve,
)


def make_prices_seq() -> pd.DataFrame:
    # 4-day sequence for two tickers with simple returns
    idx = pd.date_range("2024-01-01", periods=4, freq="D")
    a = [100.0, 110.0, 121.0, 121.0]
    b = [200.0, 190.0, 209.0, 218.0]
    return pd.DataFrame({"A": a, "B": b}, index=idx)


def test_next_close_vs_same_close_shift() -> None:
    prices = make_prices_seq()
    # constant full allocation to A only
    weights = pd.DataFrame({"A": 1.0, "B": 0.0}, index=prices.index)

    # same_close should yield returns equal to pct_change (NaN->0 at first)
    returns_same, _, _ = backtest_from_weights(
        prices, weights, execution="same_close", transaction_cost_bps=0.0
    )
    expected_same = prices.pct_change().fillna(0.0)["A"]
    expected_same.name = returns_same.name
    pd.testing.assert_series_equal(returns_same, expected_same)

    # next_close shifts returns up: weights at t apply to returns at t+1
    returns_next, _, _ = backtest_from_weights(
        prices, weights, execution="next_close", transaction_cost_bps=0.0
    )
    # For next_close, the first element should equal the first non-empty pct_change (here 0.1)
    pct = prices.pct_change()["A"]
    assert returns_next.iloc[0] == pytest.approx(pct.iloc[1])


def test_missing_weight_rows_fill_with_zeros() -> None:
    prices = make_prices_seq()
    # provide weights only for the last two dates (subset of index)
    sub_idx = prices.index[2:]
    weights_partial = pd.DataFrame(0.5, index=sub_idx, columns=prices.columns)

    returns, positions, _ = backtest_from_weights(
        prices, weights_partial, execution="same_close", transaction_cost_bps=0.0
    )
    # positions should be full index and have zeros for the first two rows
    assert list(positions.index) == list(prices.index)
    assert positions.iloc[0].sum() == 0.0
    assert positions.iloc[1].sum() == 0.0
    # later rows should reflect the provided 0.5 weights
    assert positions.iloc[2, :].sum() == pytest.approx(1.0)


def test_turnover_and_transaction_costs() -> None:
    prices = pd.DataFrame(
        {
            "A": [100.0, 110.0, 110.0],
            "B": [200.0, 200.0, 220.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )

    # weights: start flat zero, then full A, then split
    w = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    # assign rows with loc to avoid ambiguous typing warnings
    w.loc[prices.index[1]] = pd.Series({"A": 1.0, "B": 0.0})
    w.loc[prices.index[2]] = pd.Series({"A": 0.5, "B": 0.5})

    # use a large transaction cost to make effect visible
    tx_bps = 0.01
    returns, positions, metrics = backtest_from_weights(
        prices, w, execution="same_close", transaction_cost_bps=tx_bps
    )

    # compute expected gross returns manually for day 2 (index 1)
    pct = prices.pct_change().fillna(0.0)
    # gross at day1 = dot(weights_row1, pct_row1)
    gross_day1 = float((w.iloc[1] * pct.iloc[1]).sum())
    turnover_day1 = float((w.iloc[1] - w.iloc[0]).abs().sum())
    expected_net_day1 = gross_day1 - turnover_day1 * tx_bps
    assert returns.iloc[1] == pytest.approx(expected_net_day1)


def test_plot_helpers_write_files(tmp_path) -> None:
    prices = make_prices_seq()
    # positions DataFrame with simple allocations
    positions = pd.DataFrame(0.5, index=prices.index, columns=prices.columns)
    # construct a dummy returns series
    returns = pd.Series(np.random.randn(len(prices)) * 0.01, index=prices.index)

    # write files
    plot_weights_stack(positions, tmp_path)
    plot_equity_curve(returns, tmp_path)

    assert (Path(tmp_path) / "weights_stack.png").exists()
    assert (Path(tmp_path) / "equity_curve.png").exists()
