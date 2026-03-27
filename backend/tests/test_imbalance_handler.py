import pytest
import pandas as pd
from app.services.imbalance_handler import handle_imbalance

def test_handle_imbalance_smote():
    # SMOTE requires at least 6 samples for nearest neighbors by default,
    # but imbalanced-learn adjusts if n_samples < n_neighbors.
    # Provide enough samples to avoid ValueError.
    df = pd.DataFrame({
        'feature1': [1, 2, 1, 2, 1, 2, 8, 9],
        'feature2': [1.1, 2.1, 1.2, 2.2, 1.3, 2.3, 8.1, 9.1],
        'target': [0, 0, 0, 0, 0, 0, 1, 1] # Target '1' is the minority class
    })
    
    result, meta = handle_imbalance(df, target_col='target', feature_cols=['feature1', 'feature2'], strategy='smote', k_neighbors=1)
    
    # Check if the minority class was oversampled to match majority
    counts = result['target'].value_counts()
    assert counts[0] == 6
    assert counts[1] == 6
    assert len(result) == 12

def test_handle_imbalance_undersample():
    df = pd.DataFrame({
        'feature1': [1, 2, 1, 2, 1, 2, 8, 9],
        'target': [0, 0, 0, 0, 0, 0, 1, 1] 
    })
    
    result, meta = handle_imbalance(df, target_col='target', feature_cols=['feature1'], strategy='undersample', k_neighbors=1)
    
    # Check if the majority class was undersampled
    counts = result['target'].value_counts()
    assert counts[0] == 2
    assert counts[1] == 2
    assert len(result) == 4

def test_handle_imbalance_missing_target():
    df = pd.DataFrame({'f1': [1, 2], 'f2': [3, 4]})
    with pytest.raises(ValueError):
        handle_imbalance(df, target_col='target', feature_cols=['f1', 'f2'], strategy='smote')
