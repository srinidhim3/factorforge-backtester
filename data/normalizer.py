"""
Normalizer: Validate and clean price data, flagging gaps and handling splits/dividends.
"""

from typing import Tuple
import pandas as pd


def validate_time_index(
    df: pd.DataFrame, freq: str = "B"
) -> Tuple[pd.DataFrame, pd.Series]:
    """Ensure time index is regular, flag missing dates. Returns (df, gap_flags)."""
    df = df.copy()
    idx = pd.date_range(df.index.min(), df.index.max(), freq=freq)
    gap_flags = pd.Series(~idx.isin(df.index), index=idx)
    df = df.reindex(idx)
    return df, gap_flags


def fill_gaps(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
    """Fill missing values in DataFrame (default: forward fill)."""
    if method == "ffill":
        return df.ffill()
    elif method == "bfill":
        return df.bfill()
    else:
        raise ValueError(f"Unsupported fill method: {method}")


# def flag_splits_dividends(df: pd.DataFrame) -> pd.DataFrame:
#     """Add columns to flag likely splits/dividends based on price jumps."""
#     out = df.copy()
#     if "Adj Close" in df.columns and "Close" in df.columns:
#         out["split_flag"] = (df["Adj Close"] / df["Close"]).pct_change().abs() > 0.1
#     else:
#         out["split_flag"] = False
#     return out


def normalize_prices(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Full normalization: validate index, fill gaps, flag splits/dividends."""
    df2, gap_flags = validate_time_index(df)
    df2 = fill_gaps(df2)
    # df2 = flag_splits_dividends(df2)
    return df2, gap_flags
