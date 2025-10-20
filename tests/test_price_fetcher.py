"""
Unit tests for the price_fetcher module.
"""

import pandas as pd
import pytest
from data.price_fetcher import fetch_adjusted_prices


def test_fetch_adjusted_prices_valid():
    """Test fetching adjusted prices for valid tickers and date range."""
    df = fetch_adjusted_prices("MSFT", "2023-01-01", "2023-01-10")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Close" in df.columns


def test_fetch_adjusted_prices_invalid():
    """Test fetching adjusted prices with invalid ticker raises ValueError."""
    with pytest.raises(ValueError):
        fetch_adjusted_prices("INVALIDTICKER", "2023-01-01", "2023-01-10")
