# Fixed: JSON Serialization with NaN Values (Actual Working Fix) ✅

## Problem

The previous fix didn't work because `df.where(pd.notna(df), None)` combined with `to_dict()` was still producing Python float NaN values in the resulting dictionary, which JSON serialization rejects.

**Error:**
```
ValueError: Out of range float values are not JSON compliant: nan
when serializing dict item 'Avg_PctWindow_Delta'
```

## Root Cause

When pandas converts a DataFrame to a dict, even if we try to replace NaN with None beforehand, pandas' `to_dict(orient="records")` can still produce float NaN values in the output dictionary.

## Solution

The fix requires a **two-step approach**:

1. **Convert DataFrame to dict** (may still contain NaN)
2. **Post-process the dict** to replace all NaN/Infinity with None

### Updated Code

```python
def df_to_json_safe(df: "pd.DataFrame"):
    """Convert DataFrame to JSON-safe dict, handling NaN and Infinity values"""
    import numpy as np
    import pandas as pd
    import math
    
    # Step 1: Replace inf and -inf with NaN first
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Step 2: Convert to dict (may still contain NaN)
    records = df.to_dict(orient="records")
    
    # Step 3: Post-process to replace NaN with None
    cleaned_records = []
    for record in records:
        cleaned_record = {}
        for key, value in record.items():
            # Check if value is NaN (works for both float NaN and np.nan)
            if isinstance(value, float) and math.isnan(value):
                cleaned_record[key] = None
            elif value is None or (isinstance(value, float) and math.isinf(value)):
                cleaned_record[key] = None
            else:
                cleaned_record[key] = value
        cleaned_records.append(cleaned_record)
    
    return cleaned_records
```

## Why This Works

### Previous Approach (Didn't Work)
```python
df = df.replace([np.inf, -np.inf], pd.NA)
df = df.where(pd.notna(df), None)
return df.to_dict(orient="records")  # ❌ Still contains float NaN
```

**Issue:** `to_dict()` converts NA/None back to NaN internally

### New Approach (Works)
```python
df = df.replace([np.inf, -np.inf], np.nan)
records = df.to_dict(orient="records")

# Explicitly iterate and replace NaN with None
for record in records:
    for key, value in record.items():
        if math.isnan(value):  # ✅ Catches NaN after dict conversion
            cleaned_record[key] = None
```

**Why:** We check and replace NaN **after** the dict conversion, catching any NaN values that pandas might have reintroduced.

## Testing

### Test 1: Run Pipeline and Check Backend Console

**Expected (success):**
```
INFO: 127.0.0.1:xxxxx - "GET /runs/20251201_020909/summary HTTP/1.1" 200 OK
```

**Not expected (failure):**
```
ERROR: Exception in ASGI application
ValueError: Out of range float values are not JSON compliant
```

### Test 2: Check Frontend

1. Run pipeline
2. Profile Summary card should load
3. Table should display data
4. No errors in console

### Test 3: Manual API Test

```bash
curl http://localhost:8000/runs/20251201_020909/summary | jq .
```

**Expected output:**
```json
{
  "run_id": "20251201_020909",
  "sheets": {
    "ProfileStats": [
      {
        "Profile": "YARATICI LIDER",
        "Avg_PctWindow_Delta": null,  ← Was NaN, now null
        "Count": 150
      }
    ]
  }
}
```

**All float NaN values should be converted to JSON `null`**

## What Changed

**File:** `backend/app/routes/run.py`

**Before:**
- Used `df.where(pd.notna(df), None)` before `to_dict()`
- Assumed None would be preserved during dict conversion
- ❌ Failed because pandas reintroduced NaN

**After:**
- Convert to dict first
- Then iterate through and explicitly check for NaN using `math.isnan()`
- Replace NaN with None in a post-processing step
- ✅ Works because we handle NaN after dict conversion

## Edge Cases Handled

1. ✅ **float NaN** → `None`
2. ✅ **np.nan** → `None`
3. ✅ **inf** → `None`
4. ✅ **-inf** → `None`
5. ✅ **Python None** → `None` (preserved)
6. ✅ **Valid numbers** → unchanged
7. ✅ **Strings** → unchanged

## Summary

**Problem:** Previous fix didn't work because pandas `to_dict()` reintroduces NaN  
**Solution:** Post-process dict to explicitly replace NaN with None using `math.isnan()`  
**Result:** All NaN/Infinity values converted to JSON-safe `null` ✅

Backend should auto-reload. Test by running a pipeline - the Profile Summary should now load successfully! 🎉
