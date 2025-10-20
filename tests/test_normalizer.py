import pandas as pd
import pytest

from data.normalizer import validate_time_index, fill_gaps, normalize_prices


def make_sample_prices() -> pd.DataFrame:
    # Create business-day prices with a missing day (gap)
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"])  # 4th is missing
    return pd.DataFrame({"Close": [100.0, 101.0, 102.0]}, index=idx)


def test_validate_time_index_flags_missing_business_day() -> None:
    df = make_sample_prices()
    out_df, gap_flags = validate_time_index(df, freq="B")

    # index should now include 2024-01-04
    expected_idx = pd.date_range(df.index.min(), df.index.max(), freq="B")
    assert list(out_df.index) == list(expected_idx)

    # gap_flags should be True for the missing business day (2024-01-04)
    missing_day = pd.to_datetime("2024-01-04")
    assert gap_flags.loc[missing_day]


def test_validate_time_index_daily_freq() -> None:
    df = make_sample_prices()
    out_df, gap_flags = validate_time_index(df, freq="D")
    # daily range from min to max contains 2024-01-04 as missing
    assert pd.to_datetime("2024-01-04") in gap_flags.index
    assert gap_flags.loc[pd.to_datetime("2024-01-04")]


def test_fill_gaps_ffill_and_bfill() -> None:
    idx = pd.date_range("2024-01-01", periods=4, freq="D")
    df = pd.DataFrame({"A": [1.0, None, None, 4.0]}, index=idx)

    ffilled = fill_gaps(df, method="ffill")
    # middle values should be forward-filled to 1.0
    assert ffilled.iloc[1, 0] == 1.0

    bfilled = fill_gaps(df, method="bfill")
    # first NaN forward-filled by bfill should be 4.0 for the two middle
    assert bfilled.iloc[1, 0] == 4.0


def test_fill_gaps_invalid_method_raises() -> None:
    idx = pd.date_range("2024-01-01", periods=2)
    df = pd.DataFrame({"A": [1.0, None]}, index=idx)
    with pytest.raises(ValueError):
        fill_gaps(df, method="unsupported")


def test_normalize_prices_combines_steps() -> None:
    df = make_sample_prices()
    normalized, gap_flags = normalize_prices(df)
    # normalized should have same index as validate_time_index output
    expected_idx = pd.date_range(df.index.min(), df.index.max(), freq="B")
    assert list(normalized.index) == list(expected_idx)
    # the missing business day should be present and filled (ffill)
    missing = pd.to_datetime("2024-01-04")
    assert missing in normalized.index
    # after ffill, the missing day's Close should equal previous day's 101.0
    assert normalized.loc[missing, "Close"] == 101.0
