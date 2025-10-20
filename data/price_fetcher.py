"""Price data fetcher for downloading adjusted close prices using yfinance."""

import pandas as pd
import yfinance as yf


def fetch_adjusted_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch OHLCV data for a single ticker and date range.
    Args:
        ticker (str): Ticker symbol.
        start (str): Start date (YYYY-MM-DD).
        end (str): End date (YYYY-MM-DD).
    Returns:
        pd.DataFrame: DataFrame with columns [Open, High, Low, Close, Volume] and date index.
    Raises:
        ValueError: If no data is returned for the given parameters.
    """
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=True)  # type: ignore
    if data is None or data.empty:
        raise ValueError("No data returned for the given ticker and date range.")
    columns = ["Open", "High", "Low", "Close", "Volume"]
    df = data[columns].copy()
    df.columns = df.columns.get_level_values(0)
    return df
