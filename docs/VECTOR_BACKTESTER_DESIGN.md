# Vectorized Backtester — Design & Contract

Status: proposed

This document records the decision to implement a small, deterministic, vectorized backtester inside the repository (rather than integrating an external engine). It defines the contract, algorithms, edge cases, and next steps for a minimal implementation suitable for unit tests and reproducible backtests.

## Motivation
- Keep the codebase lightweight and testable without introducing heavy external dependencies.
- Match the existing `StrategyFactory` output (per-date `weights` DataFrame) with a simple, auditable P&L calculation.
- Prioritize determinism, speed, and reproducibility for analytics and CI testing.

## Contract (inputs / outputs)

- Inputs
  - `price_df: pd.DataFrame` — index = ascending dates, columns = tickers, values = prices (Close or Adj Close).
  - `weights: pd.DataFrame` — index = rebalance dates (subset or same as `price_df.index`), columns = tickers, values = target allocations (floats). Must align to `price_df` index when used.
  - `options` (kwargs):
    - `execution`: "next_close" (default) | "same_close" — determines whether targets at date t apply to returns from t->t+1 or same-day returns.
    - `transaction_cost_bps`: float (default 0.001 == 10 bps).
    - `long_only`: bool (default True).

- Outputs
  - `returns: pd.Series` — portfolio net return per period (aligned to price return periods).
  - `positions: pd.DataFrame` — realized position weights used to generate each period's return.
  - `metrics: dict` — basic performance metrics (cumulative return, annualized return, volatility, max drawdown, total turnover).

## High-level algorithm (vectorized)

1. Compute period returns R_t = price_df.pct_change() (axis=0).
2. Determine execution shift:
   - `next_close`: use targets at date t to capture returns at t+1 (i.e., use R_{t+1}).
   - `same_close`: use targets at date t to capture returns at t (i.e., use R_t).
3. Align `weights` to the return index according to chosen execution semantics.
4. For each period (vectorized):
   - Compute gross_return_t = sum(weights_t * returns_for_period_t) while masking NaNs.
   - Compute turnover_t = sum(abs(weights_t - prev_weights)) across tickers present for that date.
   - Compute transaction_cost_t = turnover_t * transaction_cost_bps.
   - Net return_t = gross_return_t - transaction_cost_t.
5. Aggregate net returns into cumulative P&L and compute metrics.

Notes on vectorization: dot-products, pct_change, and absolute differences will be performed with pandas/numpy operations across the whole DataFrame. Per-period masks are applied by aligning indexes and using DataFrame/Series arithmetic.

## Missing data & NaN handling
- Price NaNs: the ticker-date pair is excluded from that period's return calculation; its weight is treated as zero for the dot product for that period.
- Weight NaNs: treated as zero (no position).
- If all weights are zero or NaNs on a period, portfolio return is zero for that period.

## Transaction costs & turnover
- Turnover is computed on weight changes (L1 norm): turnover_t = sum(abs(w_t - w_{t-1})).
- Transaction cost model (default): cost_t = turnover_t * transaction_cost_bps. This subtracts from net return as a fraction (bps interpreted as decimal fraction).

## Execution semantics and implications
- `next_close` (default): avoids look-ahead; strategy weights computed at close t are filled at the next close t+1 (common in historical backtests when using signals computed from close prices).
- `same_close`: assumes signals are available and tradeable at the same close price; can produce optimistic results (use carefully).

## Edge cases and design choices
- Weight sums not equal to 1: interpreted literally (exposure may be <1 or >1). Optionally rescale in a later API.
- Multi-column feature outputs: the `StrategyFactory` currently uses the first column returned by `compute_indicator`. If features produce multiple columns, mapping rules must be documented and tested.
- Warm-up periods: feature outputs may be NaN for early rows; rebalance should skip until required features exist.
- Shorting and leverage: `long_only` default prevents negative allocations; support for shorts/leverage can be added via config and tests.

## Tests to add
- Deterministic synthetic tests for:
  - Constant single-ticker weight -> returns match price returns.
  - Equal-weight long-only across two tickers with known returns -> net returns and turnover match hand-calculated values.
  - Transaction cost impact on net returns.
  - NaN handling (price and weight NaNs).

## Next implementation steps
1. Add `engine/backtester.py` implementing the vectorized backtester with explicit type hints and small utility helpers.
2. Add `tests/test_backtester.py` with the deterministic cases described above.
3. Add an integration test demonstrating `StrategyFactory` -> `backtester` end-to-end.
4. Iterate on additional sizing/execution models (optional): per-share costs, slippage models, limit/partial fills.

## Rationale summary
- A small in-repo vectorized backtester gives reproducible, testable results and maps directly from the `StrategyFactory` weights output to performance metrics. It avoids a heavy external dependency while being easy to extend and unit test.

---
Last updated: 2025-10-19
