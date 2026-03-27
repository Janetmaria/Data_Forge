import pytest
import pandas as pd
import numpy as np
from app.services.encoder import encode_column

def test_encode_column_onehot():
    df = pd.DataFrame({
        'A': ['cat', 'dog', 'cat', 'bird']
    })
    
    result, meta = encode_column(df, column='A', method='one_hot')
    
    # Check that original column is dropped and encoding applied
    assert 'A' not in result.columns
    assert 'A_cat' in result.columns
    assert 'A_dog' in result.columns
    # Check some one-hot values
    assert result['A_cat'].tolist()[0] == 1

def test_encode_column_label():
    df = pd.DataFrame({
        'B': ['low', 'medium', 'high', 'low']
    })
    
    result, meta = encode_column(df, column='B', method='ordinal')
    
    # For label encoding
    assert 'B' in result.columns
    assert len(result['B'].unique()) == 3
    assert result.dtypes['B'] in [np.int64, np.int32, np.float64]

def test_encode_column_invalid_method():
    df = pd.DataFrame({'A': ['x', 'y']})
    with pytest.raises(ValueError):
        encode_column(df, column='A', method='unknown_method')
