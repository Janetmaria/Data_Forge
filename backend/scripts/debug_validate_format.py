"""
Diagnostic script: reproduce the exact screenshot scenario and identify the bug.
Run: PYTHONPATH=. python3 scripts/debug_validate_format.py
"""
import pandas as pd
import numpy as np
import re
from app.services.pipeline_service import execute_step, execute_pipeline

SEP = "=" * 65

# ── Reproduce the exact dataset from the screenshot ────────────────
df = pd.DataFrame({
    'id':         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    'name':       ['John Doe','JANE SMITH','alice jones','Bob Brown','Charlie','Dave','Eve','Frank','Grace','Heidi',
                   'Ivan','Judy','Mallory','Niaj','Olivia','Peggy','Rupert','Sybil','Ted','Victor'],
    'age':        [25, 30, None, None, 50, 22, 28, 35, 40, None,
                   60, 18, 90, 24, 33, 29, 31, 27, 44, 38],
    'salary':     [50000, 60000, 75000, 45000, 80000, 45000, 55000, 65000, 70000, 72000,
                   120000, 30000, 40000, 40000, 62000, 50000, 61000, 53000, 80000, 76000],
    'department': ['HR','IT','IT','Finance','HR','Marketing','IT','Finance','Marketing','HR',
                   'IT','IT','Finance','Marketing','HR','IT','Finance','Marketing','HR','IT'],
    'join_date':  ['2020-01-01','2019-05-15','2021-03-10','invalid_date','2018-11-20','2022-01-01','2020-02-01',
                   '2020-03-01','2020-04-01','2020-05-01','2020-06-01','2020-07-01','2020-08-01','2020-09-01',
                   '2020-10-01','2020-11-01','2020-12-01','2021-01-01','2021-02-01','2021-03-01'],
    'score_str':  ['100','95','88','70','60','50','40','30','20','10',
                   '99','85','75','65','55','45','35','25','15','5'],
    'email':      [f'user{i}@example.com' for i in range(20)],
})

print(SEP)
print("VALIDATE_FORMAT BUG DIAGNOSIS")
print(SEP)
print(f"\nOriginal dataset: {len(df)} rows")
print(f"join_date values: {df['join_date'].tolist()}")
print(f"\nRow with 'invalid_date': row index {df[df['join_date']=='invalid_date'].index.tolist()}")

# ── TEST A: validate_format in isolation ───────────────────────────
print(f"\n{SEP}")
print("TEST A: validate_format drop_invalid on join_date — STANDALONE")
print(SEP)

date_pattern = r"^\s*(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\s*(?:T| )?(?:\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[\+-]\d{2}:\d{2})?)?\s*$"

is_valid = df['join_date'].astype(str).str.match(date_pattern, na=False)
print(f"\nstr.match results for each join_date value:")
for val, valid in zip(df['join_date'], is_valid):
    status = "VALID ✓" if valid else "INVALID ✗"
    print(f"  {str(val):<20} → {status}")

print(f"\nRows that would be DROPPED: {df[~is_valid]['join_date'].tolist()}")

step_validate = {
    'operation': 'validate_format',
    'params': {
        'columns': ['join_date'],
        'format_type': 'date',
        'action': 'drop_invalid',
    }
}
result_a = execute_step(df.copy(), step_validate)
print(f"\nexecute_step result: {len(result_a)} rows (from {len(df)})")
still_has_invalid = 'invalid_date' in result_a['join_date'].values
print(f"'invalid_date' still present: {'YES — BUG ✗' if still_has_invalid else 'NO — correct ✓'}")

# ── TEST B: Pipeline with handle_imbalance BEFORE validate_format ──
print(f"\n{SEP}")
print("TEST B: Pipeline — handle_imbalance → drop_missing → validate_format")
print("(Reproducing screenshot scenario)")
print(SEP)

steps = [
    {
        'operation': 'handle_imbalance',
        'params': {
            'target_column': 'department',
            'strategy': 'smote',
            'k_neighbors': 5,
            # score_str is a string column — will be filtered out by numeric check
            'feature_columns': ['id', 'age', 'salary', 'score_str'],
        }
    },
    {
        'operation': 'drop_missing',
        'params': {}
    },
    {
        'operation': 'validate_format',
        'params': {
            'columns': ['join_date'],
            'format_type': 'date',
            'action': 'drop_invalid',
        }
    }
]

print("\nExecuting pipeline step by step to find where it breaks:")
df_step = df.copy()
for i, step in enumerate(steps):
    try:
        df_step = execute_step(df_step, step)
        print(f"  Step {i+1} ({step['operation']}): OK — {len(df_step)} rows")
    except Exception as e:
        print(f"  Step {i+1} ({step['operation']}): FAILED ✗ — {e}")
        print(f"  Pipeline stops here! Remaining steps NEVER run.")
        break

still_invalid_pipeline = 'invalid_date' in df_step['join_date'].values
print(f"\nFinal result: {len(df_step)} rows")
print(f"'invalid_date' present: {'YES — BUG (pipeline broke early) ✗' if still_invalid_pipeline else 'NO — correct ✓'}")

# ── TEST C: Null handling — NaN join_date rows ─────────────────────
print(f"\n{SEP}")
print("TEST C: How NaN join_date values behave with na=False")
print(SEP)

df_nulldate = df.copy()
df_nulldate.loc[3, 'join_date'] = None  # replace invalid_date with NaN
is_valid_null = df_nulldate['join_date'].astype(str).str.match(date_pattern, na=False)
print(f"\nNaN → astype(str) gives: '{str(df_nulldate['join_date'].iloc[3])}'")
print(f"'None' string matches date regex: {bool(re.match(date_pattern, 'None'))}")
print(f"NaN treated as invalid (na=False): {not is_valid_null.iloc[3]}")

# ── TEST D: Confirm regex directly ────────────────────────────────
print(f"\n{SEP}")
print("TEST D: Raw regex check on 'invalid_date'")
print(SEP)

test_vals = ["2020-01-01", "invalid_date", "01/15/2021", "2020-1-1", "None", "NaT", "not-a-date"]
for v in test_vals:
    match = bool(re.match(date_pattern, v))
    print(f"  '{v}': {('VALID ✓' if match else 'INVALID ✗')}")

print(f"\n{SEP}")
print("DIAGNOSIS COMPLETE")
print(SEP)
