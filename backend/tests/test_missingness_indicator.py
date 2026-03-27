import pandas as pd
import numpy as np
from app.services.missingness_indicator import add_missingness_indicator

def test_missingness_indicator_basic():
    df = pd.DataFrame({
        'A': [1, 2, np.nan, 4],
        'B': ['x', None, 'z', 'w']
    })
    
    # Apply to specific columns
    result, meta = add_missingness_indicator(df, columns=['A'])
    
    assert 'A_was_missing' in result.columns
    assert 'B_was_missing' not in result.columns
    assert result['A_was_missing'].tolist() == [0, 0, 1, 0]

def test_missingness_indicator_all_columns():
    df = pd.DataFrame({
        'A': [1, np.nan, 3],
        'B': [np.nan, 'y', 'z']
    })
    
    # Provide both columns
    result, meta = add_missingness_indicator(df, columns=['A', 'B'])
    
    assert 'A_was_missing' in result.columns
    assert 'B_was_missing' in result.columns
    assert result['A_was_missing'].tolist() == [0, 1, 0]
    assert result['B_was_missing'].tolist() == [1, 0, 0]

def test_missingness_indicator_no_missing():
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': ['x', 'y', 'z']
    })
    
    result, meta = add_missingness_indicator(df, columns=['A', 'B'])
    
    # Check that 0 columns were actually affected
    assert meta['rows_affected']['A'] == 0
    assert meta['rows_affected']['B'] == 0
