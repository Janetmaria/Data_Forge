import pandas as pd
from app.services.pipeline_service import execute_step

def test_scaling_1_to_3():
    print("Starting test...")
    df = pd.DataFrame({
        "A": [0.0, 50.0, 100.0],
    })
    step = {
        "operation": "normalize",
        "params": {
            "columns": ["A"],
            "feature_min": 1,
            "feature_max": 3
        }
    }
    df_res = execute_step(df.copy(), step)
    print("Result bounds 1 to 3 expected [1, 2, 3]:")
    print(df_res["A"].values)

if __name__ == "__main__":
    test_scaling_1_to_3()
