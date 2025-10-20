import pandas as pd

from features.feature_store import compute_indicator


def test_compute_sma_preserves_index_and_columns() -> None:
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    df = pd.DataFrame({"Close": [1, 2, 3, 4, 5]}, index=idx)

    out = compute_indicator(df, "sma", {"length": 3})
    print(out)
    # SMA with length=3 produces a column named 'SMA_3' (pandas_ta naming)
    assert len(out) == len(df)
    assert out.index.equals(df.index)
    assert out.shape[1] >= 1
