import pandas as pd
from app.services.pipeline_service import execute_step

def test_scaling_4_to_5():
    df = pd.DataFrame({
        "A": [0.0, 50.0, 100.0],
    })
    step = {
        "operation": "normalize",
        "params": {
            "columns": ["A"],
            "feature_min": 4,
            "feature_max": 5
        }
    }
    df_res = execute_step(df.copy(), step)
    print("Result bounds 4 to 5 expected [4, 4.5, 5]:")
    print(df_res["A"].values)

if __name__ == "__main__":
    test_scaling_4_to_5()
