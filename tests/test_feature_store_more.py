from pathlib import Path
from typing import Any, Dict, cast

import importlib.util
import sys
import types

import pandas as pd
import pytest


def _load_feature_store_module():
    repo_root = Path(__file__).resolve().parents[1]
    mod_path = repo_root / "features" / "feature_store.py"
    # Ensure a 'features' package exists in sys.modules so imports behave
    pkg_name = "features"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(repo_root / "features")]
    sys.modules[pkg_name] = pkg

    full_name = "features.feature_store"
    spec = importlib.util.spec_from_file_location(full_name, str(mod_path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


_FS_MOD = _load_feature_store_module()
compute_indicator = _FS_MOD.compute_indicator
FEATURE_DIR = _FS_MOD.FEATURE_DIR
save_features = _FS_MOD.save_features
load_features = _FS_MOD.load_features


def make_price_df() -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=10, freq="D")
    return pd.DataFrame({"Close": range(10, 20)}, index=idx)


def test_compute_indicator_params_type_check() -> None:
    df = make_price_df()
    with pytest.raises(TypeError):
        # pass a non-dict but silence static type check via Any
        compute_indicator(df, "sma", params=cast(Any, [1, 2, 3]))  # not a dict


def test_compute_indicator_unknown_indicator_raises() -> None:
    df = make_price_df()
    with pytest.raises(AttributeError):
        compute_indicator(df, "nonexistent_indicator", params={})


def test_save_and_load_features_roundtrip(tmp_path: Path) -> None:
    # Use a temporary feature dir so we don't write into repo
    old_dir = FEATURE_DIR
    try:
        # patch FEATURE_DIR on the loaded temp module
        _FS_MOD.FEATURE_DIR = tmp_path
        df = make_price_df()
        feats = compute_indicator(df, "sma", {"length": 3})
        meta: Dict[str, Any] = {"params": {"length": 3}}
        fid = "testfeat"
        save_features(feats, meta, fid)

        loaded_df, loaded_meta = load_features(fid)
        # metadata should match
        assert loaded_meta["params"]["length"] == 3
        # index should be preserved
        assert loaded_df.index.equals(df.index)
        # feature columns should be present
        assert loaded_df.shape[1] >= 1
    finally:
        # restore FEATURE_DIR on the loaded module
        _FS_MOD.FEATURE_DIR = old_dir
