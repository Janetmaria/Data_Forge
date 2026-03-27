import pytest
import pandas as pd
from app.services.binner import bin_column

def test_bin_column_quantile():
    df = pd.DataFrame({
        'salary': [10000, 20000, 50000, 100000, 250000]
    })
    
    # 4 quantiles = quartiles
    result, meta = bin_column(df, column='salary', strategy='equal_frequency', n_bins=4)
    
    # Output should be categorical replacing the original or appending
    assert 'salary_binned' in result.columns
    assert len(result['salary_binned'].unique()) == 4

def test_bin_column_equal_width():
    df = pd.DataFrame({
        'age': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    })
    
    result, meta = bin_column(df, column='age', strategy='equal_width', n_bins=5)
    
    # 5 bins of width 18-20ish
    assert 'age_binned' in result.columns
    assert len(result['age_binned'].unique()) == 5
    
def test_bin_column_missing_col():
    df = pd.DataFrame({'other': [1, 2]})
    with pytest.raises(ValueError):
        bin_column(df, column='missing', strategy='equal_frequency', n_bins=4)
