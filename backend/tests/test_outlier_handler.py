import pytest
import pandas as pd
from app.services.outlier_handler import handle_outliers

def test_outlier_handler_iqr_cap():
    df = pd.DataFrame({
        'A': [10, 12, 11, 15, 13, 11, 12, 1000] # 1000 is an extreme outlier
    })
    
    # Cap outliers
    result, meta = handle_outliers(df, columns=['A'], method='iqr', strategy='cap')
    
    # Check if outlier is capped without dropping the row
    assert len(result) == 8
    assert result['A'].max() < 1000
    assert result['A'].max() > 10 # Should be capped to the upper fence

def test_outlier_handler_iqr_drop():
    df = pd.DataFrame({
        'B': [1, 2, 1, 2, 1, 2, 1, 500] 
    })
    
    result, meta = handle_outliers(df, columns=['B'], method='iqr', strategy='drop')
    
    # The row with 500 should be dropped
    assert len(result) == 7
    assert result['B'].max() == 2

def test_outlier_handler_zscore_cap():
    df = pd.DataFrame({
        'C': [5, 5, 5, 5, 5, 5, 5, 500] 
    })
    
    result, meta = handle_outliers(df, columns=['C'], method='zscore', strategy='cap')
    
    assert len(result) == 8
    assert result['C'].max() < 500 

def test_outlier_handler_invalid_method():
    df = pd.DataFrame({'D': [1, 2, 3]})
    with pytest.raises(ValueError):
        handle_outliers(df, columns=['D'], method='unknown', strategy='cap')
