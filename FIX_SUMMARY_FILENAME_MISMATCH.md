# Profile Summary Filename Mismatch - FIXED ✅

## Problem

The summary Excel file was being created with the wrong filename, causing the download feature to fail.

### What Was Happening

**Run with ID:** `20251201_014614`

**Expected filename:** `profile_summary20251201_014614.xlsx`  
**Actual filename:** `profile_summary1022.xlsx`

**Log output:**
```
✅ Generating profile summary from log: .../runs/20251201_014614/processing_log20251201_014614.csv
Özet Excel kaydedildi: .../runs/20251201_014614/profile_summary1022.xlsx
...
⚠️ Summary file not created at .../runs/20251201_014614/profile_summary20251201_014614.xlsx
⚠️ Profile summary generation failed
```

**Result:** Frontend never got the download link because the backend couldn't find the file.

## Root Cause

The `analyze_processing_log.py` script was trying to extract the run_id from the log filename using this regex:

```python
match = re.search(r'processing_log(\d+)\.csv', log_basename)
```

This regex pattern **only matches digits**, but our run_id format is `20251201_014614` (includes underscore).

When the regex failed to match:
1. It fell back to `_get_last_run_id()` which reads from a counter file
2. The counter file had `1022` in it
3. Summary was saved as `profile_summary1022.xlsx`
4. Code looked for `profile_summary20251201_014614.xlsx`
5. File not found → "Summary generation failed"

## Solution

### Fix 1: Update `analyze_processing_log.py`

**Added `run_id_arg` parameter to main function:**

```python
def main(log_arg=None, out_arg=None, run_id_arg=None):
    # ... existing code ...
    
    # Use provided run_id or extract from log filename or use counter file
    run_id = run_id_arg  # ← NEW: Use provided run_id first
    if run_id is None:
        log_basename = os.path.basename(log_path)
        # Try to match timestamp format like 20251201_014614 or just digits
        match = re.search(r'processing_log([0-9_]+)\.csv', log_basename)  # ← UPDATED regex
        if match:
            run_id = match.group(1)
        else:
            run_id = _get_last_run_id()
    
    # ... rest of code ...
    out_path = os.path.join(out_dir, f"profile_summary{run_id}.xlsx")
```

**Changes:**
1. Added `run_id_arg=None` parameter
2. Use provided `run_id_arg` first (if given)
3. Updated regex to `r'processing_log([0-9_]+)\.csv'` to match timestamps with underscores
4. Fall back to counter file only if both above methods fail

### Fix 2: Update `engine.py`

**Modified `generate_profile_summary()` to pass run_id:**

```python
def generate_profile_summary(log_path: str, output_dir: str, run_id: str) -> Path | None:
    try:
        from analyze_processing_log import main as analyze_log_main
        
        # Call with run_id_arg to ensure consistent filename
        analyze_log_main(log_path, output_dir, run_id_arg=run_id)  # ← NEW: Pass run_id
        
        # The file should now be created with the correct name
        expected_path = Path(output_dir) / f"profile_summary{run_id}.xlsx"
        
        if expected_path.exists():
            return expected_path
        else:
            print(f"⚠️ Summary file not created at {expected_path}")
            return None
    except Exception as e:
        print(f"⚠️ Error generating profile summary: {e}")
        import traceback
        traceback.print_exc()
        return None
```

**Changes:**
1. Explicitly pass `run_id_arg=run_id` to `analyze_log_main()`
2. Removed fallback logic that checked for alternative filenames
3. Now expects exactly `profile_summary{run_id}.xlsx`

## How It Works Now

### Flow Diagram

```
User runs pipeline with run_id = "20251201_014614"
  ↓
engine.run_batch() or engine.run_single()
  ↓
Calls generate_profile_summary(log_path, output_dir, run_id="20251201_014614")
  ↓
Calls analyze_log_main(log_path, output_dir, run_id_arg="20251201_014614")
  ↓
analyze_processing_log.py uses run_id_arg = "20251201_014614"
  ↓
Creates file: profile_summary20251201_014614.xlsx
  ↓
engine checks for: profile_summary20251201_014614.xlsx
  ↓
✅ File found!
  ↓
Returns: summary_xlsx="profile_summary20251201_014614.xlsx"
  ↓
Frontend shows "Download Excel" button
  ↓
User clicks → Downloads profile_summary_20251201_014614.xlsx
```

## Expected Console Output

After the fix, you should see:

```
✅ Generating profile summary from log: .../runs/20251201_014614/processing_log20251201_014614.csv
Log dosyası: .../runs/20251201_014614/processing_log20251201_014614.csv
... (analysis output) ...
Özet Excel kaydedildi: .../runs/20251201_014614/profile_summary20251201_014614.xlsx
✅ Profile summary created: .../runs/20251201_014614/profile_summary20251201_014614.xlsx

🔍 DEBUG - Run completed:
  Run ID: 20251201_014614
  Run dir: .../runs/20251201_014614
  Summary file: .../runs/20251201_014614/profile_summary20251201_014614.xlsx
  Plots dir exists: True
  Plots count: 42
```

**Key indicators:**
- ✅ Same run_id throughout the process
- ✅ "Özet Excel kaydedildi" shows correct filename
- ✅ "Profile summary created" confirms success
- ✅ No "⚠️ Summary file not created" warning

## Files Modified

1. ✅ `analyze_processing_log.py` - Added `run_id_arg` parameter, updated regex
2. ✅ `backend/app/core/engine.py` - Pass `run_id` to summary generation

## Testing Steps

### Test 1: Run the Pipeline

1. Backend should auto-reload (check terminal)
2. Open http://localhost:5173
3. Run a pipeline with your sample data
4. Watch backend console

### Test 2: Verify Console Output

Look for this pattern:
```
Özet Excel kaydedildi: .../profile_summary{RUN_ID}.xlsx
✅ Profile summary created: .../profile_summary{RUN_ID}.xlsx
```

Where `{RUN_ID}` is the same throughout (e.g., `20251201_014614`).

**Red flags (should NOT see):**
- ❌ `profile_summary1022.xlsx` or any number that doesn't match the run_id
- ❌ `⚠️ Summary file not created at ...`
- ❌ `⚠️ Profile summary generation failed`

### Test 3: Check File System

```bash
# Find the latest run directory
cd backend/app/data/runs
ls -lt | head -n 5

# Check the summary file
cd {latest_run_id}
ls -la profile_summary*.xlsx
```

**Expected:**
```
profile_summary20251201_014614.xlsx  ← Should match the run_id
```

**Should NOT see:**
```
profile_summary1022.xlsx  ← Wrong!
```

### Test 4: Verify Frontend

After a successful run:
1. ✅ "Download Excel" button should appear
2. ✅ Clicking it should download the file
3. ✅ Filename should be `profile_summary_{run_id}.xlsx`
4. ✅ File should open in Excel with data

## Backward Compatibility

The fix maintains backward compatibility:

1. **If `run_id_arg` is provided:** Uses it (new behavior)
2. **If `run_id_arg` is None:** Falls back to extracting from filename (old behavior)
3. **Updated regex:** Now matches both:
   - Old format: `processing_log1022.csv` → run_id = `1022`
   - New format: `processing_log20251201_014614.csv` → run_id = `20251201_014614`

This means:
- ✅ New runs will use timestamp-based run_ids
- ✅ Old runs (if any) will still work with numeric run_ids
- ✅ No breaking changes to existing functionality

## Summary

**Problem:** Filename mismatch due to incorrect run_id extraction  
**Cause:** Regex only matched digits, not timestamp format with underscores  
**Fix:** Pass run_id explicitly + update regex as fallback  
**Result:** Consistent filenames throughout the pipeline  

**Files changed:** 2  
**Lines changed:** ~15  
**Business logic changed:** None (only filename/path handling)

The fix is minimal, focused, and doesn't touch any EEG analysis logic. ✅
