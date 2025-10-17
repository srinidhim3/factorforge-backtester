"""
Snapshot Store: Save and load immutable raw price data snapshots.
"""

from pathlib import Path
from typing import Optional
import pandas as pd

SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_snapshot(df: pd.DataFrame, snapshot_id: str, fmt: str = "parquet") -> Path:
    """Save DataFrame as immutable snapshot. Returns file path."""
    if fmt not in ("parquet", "csv"):
        raise ValueError("Format must be 'parquet' or 'csv'")
    path = SNAPSHOT_DIR / f"{snapshot_id}.{fmt}"
    if path.exists():
        raise FileExistsError(f"Snapshot {path} already exists.")
    if fmt == "parquet":
        df.to_parquet(path)
    else:
        df.to_csv(path, index=True)

    return path


def load_snapshot(snapshot_id: str, fmt: Optional[str] = None) -> pd.DataFrame:
    """Load snapshot by ID. Auto-detects format if not given."""
    for ext in ("parquet", "csv") if fmt is None else (fmt,):
        path = SNAPSHOT_DIR / f"{snapshot_id}.{ext}"
        if path.exists():
            if ext == "parquet":
                return pd.read_parquet(path)
            return pd.read_csv(path, index_col=0)
    raise FileNotFoundError(f"Snapshot {snapshot_id} not found.")
