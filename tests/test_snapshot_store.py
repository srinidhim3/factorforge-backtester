"""
Unit tests for snapshot_store.py
"""

import shutil
import pandas as pd
import pytest
from data.snapshot_store import save_snapshot, load_snapshot, SNAPSHOT_DIR


def setup_module():
    """Set up a clean snapshot directory before tests."""
    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def teardown_module():
    """Remove snapshot directory after tests."""
    shutil.rmtree(SNAPSHOT_DIR)


def test_save_and_load_parquet():
    """Test saving and loading a DataFrame as parquet."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, index=["x", "y"])
    path = save_snapshot(df, "test1", fmt="parquet")
    assert path.exists()
    df2 = load_snapshot("test1", fmt="parquet")
    pd.testing.assert_frame_equal(df, df2)


def test_save_and_load_csv():
    """Test saving and loading a DataFrame as CSV."""
    df = pd.DataFrame({"a": [5, 6], "b": [7, 8]}, index=["m", "n"])
    path = save_snapshot(df, "test2", fmt="csv")
    assert path.exists()
    df2 = load_snapshot("test2", fmt="csv")
    pd.testing.assert_frame_equal(df, df2)


def test_duplicate_snapshot_raises():
    """Test that saving a duplicate snapshot raises FileExistsError."""
    df = pd.DataFrame({"a": [9]})
    save_snapshot(df, "dup", fmt="parquet")
    with pytest.raises(FileExistsError):
        save_snapshot(df, "dup", fmt="parquet")


def test_load_missing_snapshot_raises():
    """Test that loading a missing snapshot raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_snapshot("doesnotexist")
