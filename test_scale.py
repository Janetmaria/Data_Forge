import pandas as pd
from app.services.pipeline_service import execute_step

def test_scaling():
    # 1. Test data
    df = pd.DataFrame({
        "A": [10, 20, 30, 40, 50],
        "B": [1, 1, 1, 1, 1]
    })
    
    # 2. Test scaling to -1 to 1 bounds
    step_1 = {
        "operation": "normalize",
        "params": {
            "columns": ["A"],
            "feature_min": -1.0,
            "feature_max": 1.0
        }
    }
    
    df_res1 = execute_step(df.copy(), step_1)
    
    print("Testing Custom Bounds (-1 to 1):")
    print(df_res1["A"].values)
    
    # Expected: [-1.0, -0.5, 0.0, 0.5, 1.0]

    # 3. Test scaling default bounds (0 to 1) 
    step_2 = {
        "operation": "normalize",
        "params": {
            "columns": ["A"]
        }
    }
    
    df_res2 = execute_step(df.copy(), step_2)
    
    print("\nTesting Default Bounds (0 to 1):")
    print(df_res2["A"].values)
    
    # Expected: [0.0, 0.25, 0.5, 0.75, 1.0]
    
    # 4. Test zero variance column
    step_3 = {
        "operation": "normalize",
        "params": {
            "columns": ["B"],
            "feature_min": -5.0,
            "feature_max": 5.0
        }
    }

    df_res3 = execute_step(df.copy(), step_3)
    print("\nTesting Constant Column (target bounds -5 to 5):")
    print(df_res3["B"].values)
    
    # Expected: [-5.0, -5.0, -5.0, -5.0, -5.0]
    

if __name__ == "__main__":
    test_scaling()
