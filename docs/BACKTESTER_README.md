## Vectorized Backtester — Design & Usage

This document describes the simple vectorized backtester implemented in
`engine/backtester.py` (function `backtest_from_weights`). It explains the
input/output contract, execution semantics, algorithm, handling of missing data,
transaction cost model, and common usage patterns.

### Overview

The backtester converts a per-date, per-ticker target `weights` DataFrame into
realized portfolio returns using historical `price_df`. It is intentionally
lightweight, deterministic, and fully vectorized so it is fast and easy to
unit-test.

### Contract

- Inputs
  - `price_df: pd.DataFrame` — index = ascending dates, columns = tickers, values = prices (Close/Adj Close).
  - `weights: pd.DataFrame` — index = rebalance dates (subset or same as `price_df.index`), columns = tickers, values = target allocations.
  - Optional args:
    - `execution`: either `"next_close"` (default) or `"same_close"`.
    - `transaction_cost_bps`: decimal fraction representing cost per unit turnover (default `0.001` = 10 bps).

- Outputs
  - `returns: pd.Series` — net portfolio return per period (aligned to modelled return periods).
  - `positions: pd.DataFrame` — realized position weights used each period (weights aligned to the return index).
  - `metrics: dict` — summary metrics: cumulative return, annualized return, annualized volatility, max drawdown, total turnover.

### Execution semantics

- `same_close`: weights at date `t` are applied to the return observed between `t-1` and `t` (i.e., use `price_df.pct_change()` at the same index). Use with caution — assumes signals are tradeable at the same close.
- `next_close` (recommended default): weights at date `t` are applied to the following period's returns (weights at `t` apply to `t+1` returns). This avoids certain look-ahead assumptions when signals are computed from close prices.

### Algorithm (vectorized)

1. Compute simple returns: `price_returns = price_df.pct_change()`.
2. Align return periods according to `execution`: for `next_close` use `price_returns.shift(-1)` so weights at `t` map to returns at `t+1`.
3. Reindex provided `weights` into the full return index; missing rows or columns are treated as zero exposure.
4. Compute previous-period weights `prev_w = weights.shift(1).fillna(0.0)`.
5. Turnover per period = `sum(abs(weights - prev_w))` (L1 norm across tickers).
6. Gross return per period = elementwise dot of `weights` and returns (treat NaN returns as 0 contribution).
7. Transaction cost per period = `turnover * transaction_cost_bps`.
8. Net return = `gross_return - transaction_cost`.
9. Compute cumulative returns and simple metrics (annualization uses 252 trading days by default).

### Missing data policy

- Price NaNs: treated as zero contribution to that period's return (masked out of the dot product).
- Weight NaNs: treated as zero (no position).
- If all weights are zero for a period, the portfolio return is zero.

This conservative policy avoids using incomplete data to make trading decisions. The repository also provides policies in the `StrategyFactory` for how signals are generated (the default is to mask invalid signals until features are available).

### Transaction costs & turnover

- Turnover is computed on weight changes (L1 norm): `turnover_t = sum(abs(w_t - w_{t-1}))`.
- Transaction cost model (default): `cost_t = turnover_t * transaction_cost_bps`. Costs are subtracted from gross return for the period.

Note: this is a simple notional-based cost model. If you need per-share fees or slippage, extend the backtester to accept a trade ledger or per-ticker trade sizes.

### Metrics produced

- `cumulative_return` — total portfolio return across the run (decimal fraction).
- `annualized_return` — approximate annualized return (uses 252 trading days and geometric scaling).
- `annualized_volatility` — standard deviation of net returns scaled to annual.
- `max_drawdown` — largest peak-to-trough decline in the cumulative series.
- `total_turnover` — sum of period turnover across the run.

### Example usage

Python snippet (in-repo):

```py
from engine.backtester import backtest_from_weights

# price_df and weights are pandas DataFrames built elsewhere
returns, positions, metrics = backtest_from_weights(
    price_df, weights, execution="next_close", transaction_cost_bps=0.001
)

print(metrics)
print(returns.head())
```

### Tests and verification

Unit tests for the backtester live in `tests/test_backtester.py` and cover basic single- and two-ticker scenarios including transaction cost handling. The tests run quickly and are deterministic.

### Next steps / extensions

- Provide a per-trade ledger for more detailed P&L and attribution.
- Add configurable slippage models and per-share fee models.
- Support leverage and margin/borrowing costs explicitly.
- Add integration tests that run `StrategyFactory -> backtester` end-to-end for sample configs.

---
Last updated: 2025-10-20
