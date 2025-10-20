# UI → Strategy Config

This document describes a practical, auditable way to map UI selections (indicators + parameters) into runtime strategy configuration objects that the backtester can execute.

## Goals
- Keep the UI simple while allowing expressive strategy definitions.
- Produce a deterministic, auditable config that can be saved with backtest results for provenance.
- Compute indicators in a vectorized feature pipeline and map signals → target weights.
- Validate user inputs and prevent look-ahead/data errors.

## Contract
- Input: price / history DataFrame (DatetimeIndex) and a JSON-like strategy config emitted by the UI.
- Output: per-date target weights DataFrame (index: datetime, columns: tickers) or an orders list.
- Error modes: unknown indicator, invalid params, insufficient history, missing data.

## Canonical config schema (example)

```json
{
  "name": "ui_custom_001",
  "universe": ["AAPL", "MSFT", "SPY"],
  "features": [
    {"id": "sma20", "name": "SMA", "params": {"window": 20}},
    {"id": "sma50", "name": "SMA", "params": {"window": 50}},
    {"id": "rsi14", "name": "RSI", "params": {"window": 14}}
  ],
  "signal": {
    "type": "boolean_expression",
    "expression": "sma20 > sma50 and rsi14 < 30"
  },
  "ranking": {"method": "rank", "top_n": 10},
  "sizing": {"method": "equal_weight", "long_only": true},
  "metadata": {"created_by": "ui_user_xyz", "notes": "Quick test"}
}
```

Notes:
- `features` lists the indicator computations required and assigns each an `id` used in expressions.
- `signal` can be a boolean expression (see DSL option) or an aggregator (ranked sum, weighted sum).
- `ranking` and `sizing` map signals into final target weights.

## Minimal supported components (start here)
- Feature functions: SMA, EMA, RSI, returns, volatility (rolling std), momentum (total return over lookback).
- Aggregators: rank (descending), weighted_sum, threshold (signal > x).
- Sizing: equal_weight top-N, volatility-scaling, fixed_weights.

## Implementation pattern (recommended)
1. Parse & validate config. Reject unsupported indicators or invalid params.
2. Resolve required lookback: compute the maximum history needed from all features and ensure data has enough rows.
3. Feature pipeline: compute all requested features once and cache them (in-memory or persisted feature store).
4. Signal evaluation:
   - If `boolean_expression`, compile a safe AST-based evaluator that only allows whitelisted functions/operators and the `id`s from `features`.
   - Else apply aggregator to feature columns to create a numeric signal series per date/ticker.
5. Ranking + sizing: convert per-date signals to target weights using the sizing rules.
6. Return final weights DataFrame and store the original config and feature versioning in provenance metadata.

## Safe expression evaluation (short)
- Use Python's `ast` to parse the expression, walk nodes, and permit only: Compare, BoolOp, Name, Load, Call (to whitelisted feature functions), Numeric constants.
- Replace `Name` nodes that match feature ids with column references into the computed feature DataFrame.
- Do not use `eval` on raw UI strings.

## Validation rules
- Parameter types: windows must be positive integers, RSI window >= 2, etc.
- Lookback check: require data length >= max(feature_lookback) + warmup buffer.
- Universe check: all requested tickers must exist in the price data or be handled by missing-data policy.

## Missing data policy
- Options: `ffill`, `drop`, or `mask` (skip that ticker-date in ranking).
- Recommended default: `mask` then `rank` with `skipna=True` so that missing values don't get misleading ranks.

## Auditing & reproducibility
- Store the exact config JSON, compute environment (package versions), and a feature checksum (hash of the feature computation code + params) with the backtest results.
- Persist the raw feature arrays used for the run (or a pointer to them) so the run can be exactly replayed.

## UX tips for the UI
- Show a human summary of the compiled strategy before running (e.g., "Long top 10 ranked by SMA20>SMA50 and RSI14<30; equal-weight").
- Show estimated required history (e.g., "This config needs 60 trading days of history").
- Validate params client-side (window must be integer > 1) and server-side for safety.

## Example flow (vectorized)
1. UI sends config JSON to the API.
2. Server validates and computes `features` for the full `universe` as DataFrames with shape (dates, tickers).
3. Server computes `signal` per date/ticker (boolean -> cast to float for ranking where needed).
4. Ranking + sizing produces `weights` DataFrame.
5. Backtester runs using `weights` as target allocations at each rebalance date.

## When to consider a DSL
- If users need to author complex boolean logic, allow a restricted DSL with comparison and boolean operators only (no attribute access, no function calls except whitelisted feature ids).
- Implement DSL in the server with AST validation and explicit substitution of feature series.

## Trade-offs
- Parameterized factory approach is simple and safe but less flexible for advanced users.
- DSL gives flexibility but increases validation and security overhead.
- Always prefer computing features first (caching) — it simplifies testing and provenance.

## Next steps (implementation)
- Add a small JSON schema file under `docs/` and a reference implementation plan.
- Implement feature functions in `features/feature_store.py` and a `StrategyFactory` that accepts the config and returns an object with `generate_targets(history) -> DataFrame`.


---
Last updated: 2025-10-19
