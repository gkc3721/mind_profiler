# Quick Test - JSON NaN/Infinity Fix

## ✅ What Was Fixed

**Problem:** `/runs/{run_id}/summary` endpoint failing with:
```
ValueError: Out of range float values are not JSON compliant: nan
```

**Solution:** Replace `inf`/`-inf` with `NaN`, then convert all `NaN` to `null` before JSON serialization

---

## How to Test (30 seconds)

### Step 1: Backend Should Auto-Reload ✅

**Check backend terminal:**
```
INFO:     Application startup complete.
```

If you see this, the fix is loaded.

### Step 2: Run a Pipeline

1. Open http://localhost:5173
2. Select data and run pipeline
3. Wait for completion

### Step 3: Look for Profile Summary Card ✅

**Expected result:**

```
✅ Run Results Card
   ├─ Processed Files: 379
   ├─ Matched: 350
   └─ Unmatched: 29

✅ Profile Summary Card ← Should appear WITHOUT errors
   ├─ Sheet tabs: [Toplam] [Event1] [ProfileStats] [Dominance] ...
   └─ Data table with rows

✅ Plots Gallery
   └─ Grid of plots
```

### Step 4: Check Backend Console ✅

**Before fix (error):**
```
ERROR: Exception in ASGI application
ValueError: Out of range float values are not JSON compliant
```

**After fix (success):**
```
INFO: 127.0.0.1:xxxxx - "GET /runs/20251201_123456/summary HTTP/1.1" 200 OK
```

### Step 5: Check Frontend Console ✅

Open DevTools (F12) → Console tab

**Expected:** No errors related to summary loading

**If you see:**
```
✅ (no errors)
```
→ Fix is working!

---

## Success Indicators

### Backend ✅
- No `ValueError` about JSON compliance
- HTTP 200 OK for `/runs/{run_id}/summary`
- Response body is valid JSON

### Frontend ✅
- Profile Summary card appears
- Table displays data
- Cells with NaN/inf show as `-`
- No loading spinner stuck
- No error messages

---

## Manual API Test (Optional)

```bash
# Get a run_id from a completed run
RUN_ID="20251201_123456"

# Test the summary endpoint
curl http://localhost:8000/runs/$RUN_ID/summary | jq .
```

**Expected output:**
```json
{
  "run_id": "20251201_123456",
  "sheets": {
    "Toplam": [...],
    "ProfileStats": [
      {
        "Profile": "YARATICI LIDER",
        "Avg_PctWindow_Delta": 42.5,
        "Avg_PctWindow_Theta": null,  ← null (was inf)
        "Count": 150
      }
    ]
  },
  "download_url": "/runs/20251201_123456/summary/download"
}
```

**All values should be valid JSON:**
- ✅ No `NaN` strings
- ✅ No `Infinity` strings
- ✅ Only `null`, numbers, or strings

---

## What to Look For

### In Profile Summary Table

**Cells with statistical calculations may show `-`:**

| Profile | Avg Delta | Avg Theta | Avg Alpha | Count |
|---------|-----------|-----------|-----------|-------|
| YARATICI | 42.5 | - | 38.2 | 150 |
| STRATEJIST | 35.1 | - | - | 120 |

**`-` means the cell had `NaN` or `inf` in Excel** (now `null` in JSON)

### ProfileStats Sheet

This sheet is most likely to have NaN/inf values because it contains:
- Averages (can be NaN if no data)
- Percentages (can be inf if division by zero)
- Standard deviations (can be NaN if single value)

**Click "ProfileStats" tab** and verify:
- Table loads
- Some cells may show `-`
- No errors

---

## Troubleshooting

### Issue: Profile Summary Card Still Doesn't Appear

**Check 1:** Backend console for other errors
```
# Look for:
✅ "Profile summary created: .../profile_summary{run_id}.xlsx"
❌ "⚠️ Profile summary generation failed"
```

**If summary generation failed:**
- This is a different issue (not the JSON fix)
- Check earlier in this conversation for summary generation fixes

**Check 2:** Frontend console (F12 → Console)
```
# Look for:
❌ Failed to load resource: /runs/{run_id}/summary (404)
❌ Could not load summary: ...
```

**If 404:**
- Summary file doesn't exist
- Check backend console for generation errors

**If 500:**
- Different error reading file
- Check backend console for full traceback

### Issue: Still Getting JSON Error

**This shouldn't happen** after the fix, but if it does:

**Check 1:** Is the fix actually loaded?
```bash
# In backend terminal, look for:
INFO:     Application startup complete.
```

**Check 2:** Is there a syntax error in run.py?
```bash
# In backend terminal, look for:
ERROR: SyntaxError: ...
```

**Solution:** Restart backend manually
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Issue: Table Shows All Dashes (All `-`)

**This is expected** if the Excel sheet has:
- All NaN values
- All inf values
- Empty sheet

**Not a bug**, just means no valid data in that sheet.

**Try:**
- Click "Toplam" tab (should have data)
- Click different sheets to find ones with valid data

---

## Before/After Comparison

### Before Fix

```
1. Run pipeline
2. Pipeline completes successfully
3. Profile Summary card tries to load
4. ❌ Backend error: ValueError (JSON compliance)
5. ❌ Frontend shows error: "Could not load summary"
```

### After Fix

```
1. Run pipeline
2. Pipeline completes successfully
3. Profile Summary card loads
4. ✅ Backend returns 200 OK
5. ✅ Frontend shows table with data
6. Cells with NaN/inf show as `-`
```

---

## Technical Details

### What the Fix Does

**For every DataFrame in the Excel file:**

1. **Find infinity values:**
   ```python
   df.replace([np.inf, -np.inf], pd.NA)
   ```
   - `inf` → `NA`
   - `-inf` → `NA`

2. **Convert NaN to None:**
   ```python
   df.where(pd.notna(df), None)
   ```
   - `NaN` → `None`
   - `NA` → `None`

3. **Convert to dict:**
   ```python
   df.to_dict(orient="records")
   ```
   - `None` → JSON `null` ✅

**Result:** JSON-compliant output with `null` instead of `NaN`/`inf`

---

## Summary

**Fix:** Replace inf with NaN, then NaN with None, before JSON serialization

**Changes:**
- ✅ Modified `/runs/{run_id}/summary` endpoint
- ✅ Added `df_to_json_safe()` helper function
- ✅ Applied to all sheets

**Testing:**
- ✅ Run pipeline
- ✅ Profile Summary card appears
- ✅ No JSON errors
- ✅ Table displays with some cells as `-`

**Expected time:** Backend auto-reloads (5s) → Test (30s) → Done! ✅

If the Profile Summary card appears and displays data without errors, the fix is working perfectly! 🎉
