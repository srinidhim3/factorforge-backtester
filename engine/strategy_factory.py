"""StrategyFactory: build executable strategy objects from UI config.

Minimal implementation supporting:
- feature computation via features.feature_store.compute_indicator
- boolean_expression signals using a safe AST evaluator (vectorized)
- ranking and equal_weight top-N sizing

This file keeps the scope small and well-typed to match project conventions.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd

from features.feature_store import compute_indicator


class UnsafeExpressionError(ValueError):
    pass


def _validate_config(cfg: Dict[str, Any]) -> None:
    if "features" not in cfg:
        raise ValueError("config missing 'features' list")
    if "signal" not in cfg:
        raise ValueError("config missing 'signal' section")


def _require_feature_lookback(feature_cfg: Dict[str, Any]) -> int:
    # simple heuristic: many indicators use 'window' or 'length'
    params = feature_cfg.get("params", {})
    return int(params.get("window", params.get("length", 0)))


def _safe_compile_boolean_expression(expr: str, allowed_names: List[str]) -> ast.AST:
    """Parse and validate a boolean expression AST allowing only simple ops.

    Returns the compiled AST node that can be evaluated with eval(compile()).
    """
    node = ast.parse(expr, mode="eval")

    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.UnaryOp,
        ast.BinOp,
        ast.Compare,
        ast.Name,
        ast.Load,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Gt,
        ast.Lt,
        ast.GtE,
        ast.LtE,
        ast.Eq,
        ast.NotEq,
        ast.Num,
        ast.Constant,
        ast.Call,
    )

    for n in ast.walk(node):
        if not isinstance(n, allowed_nodes):
            raise UnsafeExpressionError(f"Disallowed AST node: {type(n).__name__}")
        if isinstance(n, ast.Name) and n.id not in allowed_names:
            raise UnsafeExpressionError(f"Unknown feature name in expression: {n.id}")
        if isinstance(n, ast.Call):
            # disallow function calls entirely for now
            raise UnsafeExpressionError("Function calls are not allowed in expressions")

    return node


@dataclass
class StrategyFactory:
    config: Dict[str, Any]

    def generate_targets(self, price_history: pd.DataFrame) -> pd.DataFrame:
        """Generate target weights DataFrame indexed by price_history.index.

        price_history: DataFrame with columns for tickers or a single-ticker 'Close' series.
        Returns: weights DataFrame (index dates x columns tickers). For single-ticker
        price inputs, returns a single-column DataFrame named by config.universe[0].
        """
        _validate_config(self.config)

        features_cfg: List[Dict[str, Any]] = self.config.get("features", [])
        universe: List[str] = self.config.get("universe", [])

        # Prepare a container for computed features: mapping id -> DataFrame (dates x tickers)
        computed: Dict[str, pd.DataFrame] = {}

        # If price_history has a single 'Close' column for one ticker, normalize to DataFrame with ticker cols
        # Expect price_history to be either (dates x tickers) numeric or (dates x 1) Close series
        if price_history.shape[1] == 1 and "Close" in price_history.columns:
            # Single series: treat as single ticker named by universe[0] if provided
            if not universe:
                ticker = "TICKER"
            else:
                ticker = universe[0]
            price_df = pd.DataFrame({ticker: price_history["Close"]})
        else:
            price_df = price_history.copy()

        # Compute features for each requested feature id
        for feat in features_cfg:
            fid = feat["id"]
            params = feat.get("params", {})
            # compute_indicator expects a DataFrame with a Close column; compute per-ticker
            out_df = pd.DataFrame(index=price_df.index)
            for col in price_df.columns:
                single = pd.DataFrame({"Close": price_df[col]}, index=price_df.index)
                indicator_name = feat.get(
                    "name", feat.get("indicator", feat.get("id", ""))
                ).lower()
                ind = compute_indicator(single, indicator_name, params)
                # take first column from result and name it by ticker
                out_df[col] = ind.iloc[:, 0]

            computed[fid] = out_df

        # Evaluate signal
        sig_cfg = self.config["signal"]
        sig_type = sig_cfg.get("type")

        if sig_type == "boolean_expression":
            expr: str = sig_cfg["expression"]
            allowed = list(computed.keys())
            _safe_compile_boolean_expression(expr, allowed)

            # Create a local dict mapping names to DataFrames for vectorized evaluation
            local_vars: Dict[str, Any] = {k: v for k, v in computed.items()}

            # Evaluate the expression using pandas operations; replace Name nodes with DataFrames
            # A safe way: build a string that references local_vars keys, then eval with restricted globals
            # The expression is expected to use feature ids as names, which are DataFrame objects.
            try:
                mask = eval(
                    compile(expr, "<expr>", "eval"), {"__builtins__": {}}, local_vars
                )
            except Exception as exc:
                raise UnsafeExpressionError(f"Error evaluating expression: {exc}")

            # mask should be DataFrame-like (dates x tickers) with boolean values
            if isinstance(mask, pd.Series):
                mask = mask.to_frame()
            if not isinstance(mask, pd.DataFrame):
                raise ValueError(
                    "Signal expression must evaluate to a pandas DataFrame or Series"
                )

            # Convert boolean mask to numeric signal (1 for True, 0 for False)
            signal = mask.astype(float)
        else:
            raise NotImplementedError(f"Signal type '{sig_type}' not implemented")

        # Ranking: currently support 'rank' method and top_n
        ranking = self.config.get("ranking", {"method": "rank", "top_n": None})
        top_n = ranking.get("top_n")

        # Sizing: equal_weight
        # sizing currently only supports equal_weight top-N (default)

        # For each date, select tickers where signal > 0, pick top_n by signal value (or all), then equal weight
        weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)

        for dt in signal.index:
            row = signal.loc[dt]
            valid = row.dropna()
            # sort descending
            ranked = valid.sort_values(ascending=False)
            if top_n is not None:
                # prefer only positive signals when selecting top_n
                positives = ranked[ranked > 0]
                if not positives.empty:
                    selected = positives.head(int(top_n))
                else:
                    # no positive signals -> select none
                    selected = ranked.iloc[0:0]
            else:
                selected = ranked[ranked > 0]
            if selected.empty:
                continue
            w = 1.0 / float(len(selected))
            for tick in selected.index:
                weights.at[dt, tick] = w

        return weights
