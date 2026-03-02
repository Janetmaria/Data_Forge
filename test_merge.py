import pandas as pd
from app.services.pipeline_service import execute_step, InvalidColumnTypeError

def test_merges():
    # 1. Base Data
    df_main = pd.DataFrame({
        "id_num": [1, 2, 3],
        "id_str": ["1", "2", "3"],
        "name": ["Alice", "Bob", "Charlie"]
    })
    
    # 2. Secondary Data
    df_secondary = pd.DataFrame({
        "ref_num": [1, 2],
        "ref_str": ["1", "2"],
        "score": [100, 200]
    })
    
    context = {"sec_1": df_secondary}

    print("Test 1: Valid Numeric Merge (id_num -> ref_num)")
    step_valid_num = {
        "operation": "merge",
        "params": {
            "secondary_dataset_id": "sec_1",
            "how": "inner",
            "left_on": "id_num",
            "right_on": "ref_num"
        }
    }
    df_res1 = execute_step(df_main.copy(), step_valid_num, context)
    print("Success. Rows:", len(df_res1))

    print("\nTest 2: Valid String Merge (id_str -> ref_str)")
    step_valid_str = {
        "operation": "merge",
        "params": {
            "secondary_dataset_id": "sec_1",
            "how": "inner",
            "left_on": "id_str",
            "right_on": "ref_str"
        }
    }
    df_res2 = execute_step(df_main.copy(), step_valid_str, context)
    print("Success. Rows:", len(df_res2))
    
    print("\nTest 3: Invalid Cross-Type Merge (id_num -> ref_str)")
    step_invalid = {
        "operation": "merge",
        "params": {
            "secondary_dataset_id": "sec_1",
            "how": "inner",
            "left_on": "id_num",
            "right_on": "ref_str"
        }
    }
    try:
        execute_step(df_main.copy(), step_invalid, context)
        print("FAILED: Did not block invalid merge!")
    except InvalidColumnTypeError as e:
        print("Success! Caught exception:", e)

if __name__ == "__main__":
    test_merges()
