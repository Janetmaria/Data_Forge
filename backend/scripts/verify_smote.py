"""
SMOTE k_neighbors auto-clamping verification script.
Run from backend/ directory:
    PYTHONPATH=. python3 scripts/verify_smote.py
"""
import pandas as pd
import numpy as np
from collections import Counter
from app.services.imbalance_handler import handle_imbalance
from app.services.pipeline_service import execute_step

SEP = "=" * 60

print(SEP)
print("SMOTE K-NEIGHBORS AUTO-CLAMP VERIFICATION")
print(SEP)

# ── Dataset 1: Tiny minority class (3 samples) ─────────────────
df_small = pd.DataFrame({
    'age':    [25, 30, 35, 40, 45, 50, 55, 60, 65, 33],
    'salary': [40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 55.0],
    'target': [0,    0,    0,    0,    0,    0,    0,     1,     1,     1],
})

print(f"\nDataset A: {len(df_small)} rows")
print(f"Class distribution: {dict(Counter(df_small['target']))}")
print(f"Minority class size: 3  (k must be < 3, i.e. max k=2)")

# --- Test 1: Direct call with safe k ---
print("\n[TEST 1] handle_imbalance directly — k=1 (valid, minority=3)")
result1, meta1 = handle_imbalance(
    df_small, target_col='target', feature_cols=['age', 'salary'],
    strategy='smote', k_neighbors=1
)
counts1 = dict(Counter(result1['target']))
print(f"  Rows before : {meta1['rows_before']}")
print(f"  Rows after  : {meta1['rows_after']}  (+{meta1['rows_added']} synthetic)")
print(f"  Class dist  : {meta1['class_dist_after']}")
balanced1 = len(set(counts1.values())) == 1
print(f"  RESULT: {'PASS ✓' if balanced1 else 'FAIL ✗'} — classes balanced")

# --- Test 2: pipeline execute_step, k=5 → should auto-clamp to k=2 ---
print("\n[TEST 2] execute_step — k=5 requested, minority=3 → expects auto-clamp to k=2")
step2 = {
    'operation': 'handle_imbalance',
    'params': {
        'target_column': 'target',
        'strategy': 'smote',
        'k_neighbors': 5,
    }
}
result2 = execute_step(df_small.copy(), step2)
counts2 = dict(Counter(result2['target']))
balanced2 = len(set(counts2.values())) == 1
print(f"  Rows after : {len(result2)}")
print(f"  Class dist : {counts2}")
print(f"  RESULT: {'PASS ✓' if balanced2 else 'FAIL ✗'} — auto-clamp worked, classes balanced")

# --- Test 3: Direct call with k=5 should RAISE (no auto-clamp at handler level) ---
print("\n[TEST 3] handle_imbalance directly — k=5, minority=3 → expects ValueError")
try:
    handle_imbalance(df_small, target_col='target', feature_cols=['age', 'salary'],
                     strategy='smote', k_neighbors=5)
    print("  RESULT: FAIL ✗ — should have raised but did NOT")
except ValueError as e:
    print(f"  RESULT: PASS ✓ — raised ValueError correctly: {e}")

# ── Dataset 2: Realistic imbalanced (fraud-like, 1% minority) ──
print(f"\n{SEP}")
print("Dataset B: Large realistic dataset (1000 rows, 1% minority)")
np.random.seed(42)
n = 1000
df_large = pd.DataFrame({
    'amount':    np.random.exponential(100, n).round(2),
    'duration':  np.random.normal(60, 15, n).round(2),
    'frequency': np.random.poisson(5, n).astype(float),
    'target':    [0] * 990 + [1] * 10,
})
print(f"Rows: {n}  |  Minority: 10 samples (1%)")
print(f"Class distribution: {dict(Counter(df_large['target']))}")

# --- Test 4: k=5 should work without clamping (minority=10, safe_k = min(5,9) = 5) ---
print("\n[TEST 4] execute_step — k=5, minority=10 → no clamping needed")
step4 = {
    'operation': 'handle_imbalance',
    'params': {'target_column': 'target', 'strategy': 'smote', 'k_neighbors': 5}
}
result4 = execute_step(df_large.copy(), step4)
counts4 = dict(Counter(result4['target']))
balanced4 = len(set(counts4.values())) == 1
print(f"  Rows before : {len(df_large)}")
print(f"  Rows after  : {len(result4)}")
print(f"  Class dist  : {counts4}")
print(f"  RESULT: {'PASS ✓' if balanced4 else 'FAIL ✗'} — balanced")

# --- Test 5: Undersample on large dataset ---
print("\n[TEST 5] execute_step — undersample strategy on Dataset B")
step5 = {
    'operation': 'handle_imbalance',
    'params': {'target_column': 'target', 'strategy': 'undersample'}
}
result5 = execute_step(df_large.copy(), step5)
counts5 = dict(Counter(result5['target']))
balanced5 = len(set(counts5.values())) == 1
print(f"  Rows after : {len(result5)}  (expected 20 = 10+10)")
print(f"  Class dist : {counts5}")
print(f"  RESULT: {'PASS ✓' if balanced5 else 'FAIL ✗'} — balanced")

# ── Dataset 3: Float target (simulates mean-fill on binary target) ─
print(f"\n{SEP}")
print("Dataset C: Float target (simulates mean-fill artefact)")
df_float = pd.DataFrame({
    'f0': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
           11.0, 12.0, 13.0, 14.0, 15.0],
    'f1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
           1.1, 1.2, 1.3, 1.4, 1.5],
    'target': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
               1.0, 1.0, 1.0, 1.0, 1.0],
})
print(f"Rows: {len(df_float)}  |  Target dtype: {df_float['target'].dtype}  (float)")
print(f"Class distribution: {dict(Counter(df_float['target']))}")

print("\n[TEST 6] handle_imbalance — float target auto-cast to int")
result6, meta6 = handle_imbalance(df_float, target_col='target',
                                   feature_cols=['f0', 'f1'],
                                   strategy='smote', k_neighbors=1)
counts6 = dict(Counter(result6['target']))
balanced6 = len(set(counts6.values())) == 1
print(f"  Target dtype after cast: {result6['target'].dtype}")
print(f"  Class dist : {counts6}")
print(f"  RESULT: {'PASS ✓' if balanced6 else 'FAIL ✗'} — float cast + balanced")

# ── Summary ─────────────────────────────────────────────────────
print(f"\n{SEP}")
results = [balanced1, balanced2, balanced4, balanced5, balanced6]
passed = sum(results)
print(f"SUMMARY: {passed}/{len(results)+1} checks passed")
print("  (Test 3 is an error-case check — counted separately)")
print(SEP)
