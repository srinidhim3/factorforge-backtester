"""
Feature Store: Compute and persist features with metadata.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Iterable, cast
from pandas.api.types import is_list_like
import pandas as pd
import pandas_ta as ta


FEATURE_DIR = Path("features/store")
FEATURE_DIR.mkdir(parents=True, exist_ok=True)


# Mapping from human-friendly UI label to pandas_ta indicator function name.
# Keep this mapping minimal and explicit so the UI can present readable names
# while compute_indicator receives the correct function identifier.
UI_INDICATOR_MAP: Dict[str, str] = {
    "Simple Moving Average": "sma",
    "Relative Strength Index": "rsi",
    "Moving Average Convergence Divergence": "macd",
    "Exponential Moving Average": "ema",
}


def ui_to_indicator(ui_label: str) -> str:
    """Translate a UI label into the pandas_ta indicator name.

    Raises KeyError if ui_label is unknown.
    """
    try:
        return UI_INDICATOR_MAP[ui_label]
    except KeyError as exc:
        raise KeyError(f"Unknown indicator label: {ui_label}") from exc


def compute_indicator(
    df: pd.DataFrame, indicator: str, params: Dict[str, Any]
) -> pd.DataFrame:
    """Compute a single pandas_ta indicator on df using the provided params.

    Only the requested indicator is computed. The function validates that the
    indicator exists in pandas_ta and returns a DataFrame containing only the
    indicator columns (with the same index as the input).

    Args:
        df: Input price DataFrame.
        indicator: Name of the pandas_ta indicator (e.g., 'sma', 'rsi').
        params: Keyword parameters for the indicator function.

    Returns:
        DataFrame with indicator columns appended or computed.

    Raises:
        AttributeError: If the indicator is not found in pandas_ta.
        TypeError: If params is not a mapping.
    """
    if not isinstance(params, dict):
        raise TypeError("params must be a dict of keyword arguments")

    # pandas_ta exposes a variety of functions under the ta namespace and via
    # the DataFrame accessor df.ta. Prefer the functional API for explicitness.
    func = getattr(ta, indicator, None)
    if func is None or not callable(func):
        # try the dataframe accessor method name (e.g., df.ta.sma)
        accessor = getattr(df.ta, indicator, None)
        if accessor is None or not callable(accessor):
            raise AttributeError(f"Indicator '{indicator}' not found in pandas_ta")

        # Use the accessor which will operate on the DataFrame
        result = accessor(**params)
    else:
        # Some pandas_ta functions expect the Series/array input; pass columns
        # when required. Attempt with the DataFrame first.
        try:
            result = func(df=df, **params)  # type: ignore[arg-type]
        except TypeError:
            # Fallback: try calling with Close series
            if "Close" in df.columns:
                result = func(df["Close"], **params)  # type: ignore[arg-type]
            elif "Adj Close" in df.columns:
                result = func(df["Adj Close"], **params)  # type: ignore[arg-type]
            else:
                # Last resort: call without data and let pandas_ta use defaults
                result = func(**params)  # type: ignore[arg-type]

    # Normalize result into a DataFrame
    if isinstance(result, pd.Series):
        out_df = result.to_frame()
    elif isinstance(result, pd.DataFrame):
        out_df = result
    else:
        # pandas_ta sometimes returns numpy arrays or other array-like objects.
        # Accept only list-like results (length must match df.index).
        if is_list_like(result):
            seq = list(cast(Iterable[Any], result))
            if len(seq) != len(df.index):
                raise ValueError(
                    "Length of indicator result does not match input index"
                )
            out_df = pd.Series(seq, index=df.index).to_frame()
        else:
            raise TypeError("Unsupported result type returned by pandas_ta")

    # Ensure index alignment with input
    out_df.index = df.index
    return out_df


def save_features(
    features: pd.DataFrame, metadata: Dict[str, Any], feature_id: str
) -> None:
    """Save features and metadata as parquet and JSON."""
    fpath = FEATURE_DIR / f"{feature_id}.parquet"
    mpath = FEATURE_DIR / f"{feature_id}_meta.json"
    features.to_parquet(fpath)
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(metadata, f)


def load_features(feature_id: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load features and metadata by ID."""
    fpath = FEATURE_DIR / f"{feature_id}.parquet"
    mpath = FEATURE_DIR / f"{feature_id}_meta.json"
    features = pd.read_parquet(fpath)
    with open(mpath, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return features, metadata
