"""
Comprehensive SMOTE / imbalance-handler test suite.

Covers:
  - Basic SMOTE oversampling
  - Undersample
  - SMOTE then undersample (combined)
  - Float targets that are whole numbers (e.g. 0.0 / 1.0 after mean-fill)
  - Auto k_neighbors clamping via pipeline_service (small minority class)
  - Non-numeric feature rejection
  - Null feature column rejection
  - Missing target column rejection
  - Sentinel / placeholder values don't crash SMOTE
  - Multi-class target
  - Non-feature columns (text/ID) are preserved for original rows
  - handle_imbalance called via pipeline execute_step
"""
import pytest
import pandas as pd
import numpy as np
from app.services.imbalance_handler import handle_imbalance
from app.services.pipeline_service import execute_step


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _make_imbalanced(n_majority=50, n_minority=5, n_features=2, seed=0):
    rng = np.random.default_rng(seed)
    X_maj = rng.normal(0, 1, (n_majority, n_features))
    X_min = rng.normal(5, 1, (n_minority, n_features))
    X = np.vstack([X_maj, X_min])
    y = [0] * n_majority + [1] * n_minority
    cols = {f"f{i}": X[:, i] for i in range(n_features)}
    cols["target"] = y
    return pd.DataFrame(cols)


# ─────────────────────────────────────────────
# 1. Basic SMOTE
# ─────────────────────────────────────────────
def test_smote_basic_oversample():
    df = _make_imbalanced(n_majority=20, n_minority=5)
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="smote", k_neighbors=1)
    counts = result["target"].value_counts()
    assert counts[0] == counts[1], "SMOTE should balance classes"
    assert meta["rows_added"] > 0
    assert meta["strategy"] == "smote"


# ─────────────────────────────────────────────
# 2. Undersample
# ─────────────────────────────────────────────
def test_undersample_basic():
    df = _make_imbalanced(n_majority=30, n_minority=6)
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="undersample")
    counts = result["target"].value_counts()
    assert counts[0] == counts[1], "Undersampling should balance classes"
    assert len(result) < len(df)


# ─────────────────────────────────────────────
# 3. SMOTE then undersample
# ─────────────────────────────────────────────
def test_smote_then_undersample():
    df = _make_imbalanced(n_majority=40, n_minority=5)
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="smote_then_undersample", k_neighbors=1)
    counts = result["target"].value_counts()
    assert counts[0] == counts[1], "Combined strategy should balance classes"


# ─────────────────────────────────────────────
# 4. Float target with whole-number values (auto-cast to int)
# ─────────────────────────────────────────────
def test_float_target_whole_numbers():
    df = _make_imbalanced(n_majority=20, n_minority=5)
    df["target"] = df["target"].astype(float)  # simulate mean-fill converting 0→0.0
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="smote", k_neighbors=1)
    assert result["target"].dtype in (int, np.int64, np.int32)
    counts = result["target"].value_counts()
    assert counts[0] == counts[1]


# ─────────────────────────────────────────────
# 5. Non-numeric feature → should raise
# ─────────────────────────────────────────────
def test_non_numeric_feature_raises():
    df = pd.DataFrame({
        "name": ["alice", "bob", "carol", "dave", "eve", "frank"],
        "score": [1.0, 2.0, 1.5, 2.5, 3.0, 3.5],
        "target": [0, 0, 0, 0, 1, 1],
    })
    with pytest.raises(ValueError, match="not numeric"):
        handle_imbalance(df, target_col="target", feature_cols=["name", "score"],
                         strategy="smote", k_neighbors=1)


# ─────────────────────────────────────────────
# 6. Null in feature column → should raise
# ─────────────────────────────────────────────
def test_null_feature_raises():
    df = pd.DataFrame({
        "f0": [1.0, 2.0, np.nan, 4.0, 5.0, 6.0],
        "target": [0, 0, 0, 0, 1, 1],
    })
    with pytest.raises(ValueError, match="Null values"):
        handle_imbalance(df, target_col="target", feature_cols=["f0"],
                         strategy="smote", k_neighbors=1)


# ─────────────────────────────────────────────
# 7. Missing target column → should raise
# ─────────────────────────────────────────────
def test_missing_target_column_raises():
    df = pd.DataFrame({"f1": [1, 2], "f2": [3, 4]})
    with pytest.raises(ValueError, match="not found"):
        handle_imbalance(df, target_col="label", feature_cols=["f1", "f2"],
                         strategy="smote")


# ─────────────────────────────────────────────
# 8. Unknown strategy → should raise
# ─────────────────────────────────────────────
def test_unknown_strategy_raises():
    df = _make_imbalanced()
    with pytest.raises(ValueError, match="Unknown strategy"):
        handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                         strategy="magic_resample")


# ─────────────────────────────────────────────
# 9. k_neighbors >= minority class size → should raise
# ─────────────────────────────────────────────
def test_k_neighbors_too_large_raises():
    df = pd.DataFrame({
        "f0": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "target": [0, 0, 0, 0, 1, 1],
    })
    with pytest.raises(ValueError, match="k_neighbors"):
        handle_imbalance(df, target_col="target", feature_cols=["f0"],
                         strategy="smote", k_neighbors=5)  # minority=2, k must be <2


# ─────────────────────────────────────────────
# 10. Non-feature columns (text/IDs) are preserved for original rows
# ─────────────────────────────────────────────
def test_non_feature_cols_preserved():
    df = pd.DataFrame({
        "id": [f"EMP-{i:03d}" for i in range(20)],
        "score": list(range(20)),
        "value": [float(i) for i in range(20)],
        "target": [0] * 15 + [1] * 5,
    })
    result, meta = handle_imbalance(df, target_col="target",
                                    feature_cols=["score", "value"],
                                    strategy="smote", k_neighbors=1)
    # Original 20 rows should keep their IDs; synthetic rows get NaN
    original_ids = result["id"].iloc[:20]
    assert original_ids.notna().all(), "Original rows should retain ID values"
    synthetic_ids = result["id"].iloc[20:]
    assert synthetic_ids.isna().all(), "Synthetic rows should have NaN for text columns"


# ─────────────────────────────────────────────
# 11. Multi-class target
# ─────────────────────────────────────────────
def test_multiclass_smote():
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "f0": rng.normal(0, 1, 40),
        "f1": rng.normal(0, 1, 40),
        "target": [0] * 20 + [1] * 15 + [2] * 5,
    })
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="smote", k_neighbors=1)
    counts = result["target"].value_counts()
    # After SMOTE all classes should equal the largest class (20)
    assert counts.min() == counts.max(), "All classes should be balanced"


# ─────────────────────────────────────────────
# 12. Pipeline execute_step integration — auto k_neighbors clamping
# ─────────────────────────────────────────────
def test_pipeline_execute_step_smote_auto_clamp():
    """
    execute_step should auto-clamp k_neighbors when the minority class is small.
    minority size = 3, requested k = 5 → should clamp to k=2 and succeed.
    """
    df = pd.DataFrame({
        "f0": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 1.5, 2.5, 3.5],
        "f1": [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 1.2, 1.8, 2.2],
        "target": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
    })
    step = {
        "operation": "handle_imbalance",
        "params": {
            "target_column": "target",
            "strategy": "smote",
            "k_neighbors": 5,  # too large for minority=3, should auto-clamp to 2
        }
    }
    result = execute_step(df, step)
    counts = result["target"].value_counts()
    assert counts[0] == counts[1], "Pipeline SMOTE step should balance classes"


# ─────────────────────────────────────────────
# 13. Meta-data sanity check
# ─────────────────────────────────────────────
def test_metadata_returned_correctly():
    df = _make_imbalanced(n_majority=20, n_minority=5)
    result, meta = handle_imbalance(df, target_col="target", feature_cols=["f0", "f1"],
                                    strategy="smote", k_neighbors=1)
    assert meta["rows_before"] == 25
    assert meta["rows_after"] == len(result)
    assert meta["rows_added"] == meta["rows_after"] - meta["rows_before"]
    assert "class_dist_before" in meta
    assert "class_dist_after" in meta
    assert meta["strategy"] == "smote"
