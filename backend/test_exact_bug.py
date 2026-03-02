import pandas as pd
from app.services.pipeline_service import execute_pipeline

def test():
    df = pd.DataFrame({
        "age": [30, 40, 50, 60]
    })
    
    steps = [
        {
            "operation": "normalize",
            "params": {
                "columns": ["age"],
                "feature_min": 4,
                "feature_max": 5
            }
        }
    ]
    
    df_res = execute_pipeline(df.copy(), steps)
    print("Result of pipeline:")
    print(df_res["age"].values)

if __name__ == "__main__":
    test()
