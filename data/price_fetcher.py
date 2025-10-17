"""Price data fetcher for downloading adjusted close prices using yfinance."""

from typing import List
import pandas as pd
import yfinance as yf


def fetch_adjusted_prices(tickers: List[str], start: str, end: str) -> pd.DataFrame:
    """
    Fetch adjusted close prices for a list of tickers and date range.
    Args:
        tickers (List[str]): List of ticker symbols.
        start (str): Start date (YYYY-MM-DD).
        end (str): End date (YYYY-MM-DD).
    Returns:
        pd.DataFrame: DataFrame with adjusted close prices and date index.
    Raises:
        ValueError: If no data is returned for the given parameters.
    """
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)  # type: ignore
    if data is None or data.empty:
        raise ValueError("No data returned for the given tickers and date range.")
    if "Adj Close" in data:
        df = data["Adj Close"]
    else:
        df = data["Close"]
    df = df.reset_index()
    return df
