import pandas as pd
from app.services.timeseries_features import extract_datetime_components, create_lag_features, create_rolling_features

def test_add_timeseries_lag():
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=5),
        'sales': [10, 20, 30, 40, 50]
    })
    
    result, meta = create_lag_features(df, column='sales', lags=[1], sort_by='date')
    
    assert 'sales_lag_1' in result.columns
    assert pd.isna(result.iloc[0]['sales_lag_1'])
    assert result.iloc[1]['sales_lag_1'] == 10.0

def test_add_timeseries_rolling():
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=5),
        'sales': [10, 20, 30, 40, 50]
    })
    
    result, meta = create_rolling_features(df, column='sales', windows=[2], min_periods=2)
    
    assert 'sales_rolling_2_mean' in result.columns
    assert 'sales_rolling_2_std' in result.columns
    assert pd.isna(result.iloc[0]['sales_rolling_2_mean'])
    assert result.iloc[1]['sales_rolling_2_mean'] == 15.0

def test_add_timeseries_datetime_extraction():
    df = pd.DataFrame({
        'dt': pd.to_datetime(['2023-01-15 14:00:00', '2023-02-14 09:30:00'])
    })
    
    result, meta = extract_datetime_components(df, column='dt', components=['year', 'month', 'hour'])
    
    assert 'dt_year' in result.columns
    assert 'dt_month' in result.columns
    assert 'dt_hour' in result.columns
    assert result.iloc[0]['dt_year'] == 2023
    assert result.iloc[0]['dt_month'] == 1
    assert result.iloc[0]['dt_hour'] == 14
