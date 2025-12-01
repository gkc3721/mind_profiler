# ✅ Quick Test - Summary Filename Fix

## What Was Fixed

The summary Excel file was being created with filename `profile_summary1022.xlsx` instead of `profile_summary20251201_014614.xlsx`, causing the download button to never appear.

**Root cause:** The `analyze_processing_log.py` script couldn't extract the run_id from the log filename because the regex only matched digits, not timestamps with underscores.

**Fix:** Pass the run_id explicitly to the summary generation function.

---

## How to Test (2 minutes)

### Step 1: Backend Should Auto-Reload ✅

Check your terminal running uvicorn. You should see:
```
INFO:     Shutting down
INFO:     Application startup complete.
```

If not, restart manually:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Step 2: Run a Test Pipeline

1. Open http://localhost:5173
2. Select your sample data folder
3. Click "Run Pipeline"
4. **Watch the backend console carefully**

### Step 3: Look for This in Console ✅

**Before the fix (WRONG):**
```
Özet Excel kaydedildi: .../profile_summary1022.xlsx
⚠️ Summary file not created at .../profile_summary20251201_014614.xlsx
⚠️ Profile summary generation failed
```

**After the fix (CORRECT):**
```
Özet Excel kaydedildi: .../profile_summary20251201_014614.xlsx
✅ Profile summary created: .../profile_summary20251201_014614.xlsx

🔍 DEBUG - Run completed:
  Run ID: 20251201_014614
  Summary file: .../profile_summary20251201_014614.xlsx
```

**Key indicator:** The run_id should be **the same** in both places.

### Step 4: Check Frontend UI ✅

After the run completes:

1. **Look for "Download Excel" button** in the Run Results card
2. **Click it** to download
3. **Verify filename** matches: `profile_summary_{run_id}.xlsx`
4. **Open in Excel** to verify data

---

## Success Criteria

### Backend Console
- ✅ Shows consistent run_id throughout
- ✅ "Özet Excel kaydedildi" shows correct filename
- ✅ "Profile summary created" confirmation
- ❌ NO "Summary file not created" warning
- ❌ NO "Profile summary generation failed" error

### Frontend UI
- ✅ "Download Excel" button appears
- ✅ Clicking downloads the file
- ✅ File opens in Excel with data
- ✅ Plots display (not "No plots available")

### File System
```bash
# Check the file exists with correct name
cd backend/app/data/runs/{run_id}
ls -la profile_summary*.xlsx
# Should show: profile_summary{run_id}.xlsx
```

---

## If It Still Doesn't Work

### Check 1: Console Output

**If you see:**
```
⚠️ Error generating profile summary: ...
```

**Then:** Check the full traceback for the error.

**Common issues:**
- Missing dependencies: `pip install pandas openpyxl`
- Corrupt log file
- Permissions issue

### Check 2: File System

**Check what file was actually created:**
```bash
cd backend/app/data/runs
ls -lt | head -n 1  # Get latest run
cd {latest_run_id}
ls -la profile_summary*
```

**If you see `profile_summary1022.xlsx`:**
- The fix didn't apply (backend didn't reload)
- Restart backend manually

**If you see `profile_summary20251201_014614.xlsx`:**
- File exists! Check why frontend doesn't show button
- Check DevTools Network tab for the API response
- Verify `summary_xlsx` field is not null

### Check 3: API Response

**Open DevTools (F12) → Network tab**

Find the POST request to `/run/upload-batch`

**Check the response JSON:**
```json
{
  "summary_xlsx": "profile_summary20251201_014614.xlsx",  // ← Should match run_id
  "run_id": "20251201_014614",
  ...
}
```

**If `summary_xlsx` is null:**
- Backend didn't find the file
- Check console for errors
- Verify file exists on disk

---

## Quick Verification Command

```bash
# Replace with your actual run_id from the console output
RUN_ID="20251201_014614"

echo "Checking summary file..."
ls -lh backend/app/data/runs/$RUN_ID/profile_summary*.xlsx

echo ""
echo "Expected filename: profile_summary$RUN_ID.xlsx"
echo "If the filename matches, the fix is working! ✅"
```

---

## Expected vs Actual

### Before Fix ❌

**Console:**
```
Özet Excel kaydedildi: .../profile_summary1022.xlsx       ← Wrong number!
⚠️ Summary file not created at .../profile_summary20251201_014614.xlsx
```

**File system:**
```
profile_summary1022.xlsx  ← Wrong filename
```

**Frontend:**
- No download button
- User can't get the summary

### After Fix ✅

**Console:**
```
Özet Excel kaydedildi: .../profile_summary20251201_014614.xlsx  ← Correct!
✅ Profile summary created: .../profile_summary20251201_014614.xlsx
```

**File system:**
```
profile_summary20251201_014614.xlsx  ← Correct filename
```

**Frontend:**
- Download button appears
- Clicking downloads the file
- File opens correctly

---

## Summary

**What changed:**
1. `analyze_processing_log.py` now accepts `run_id_arg` parameter
2. `engine.py` passes `run_id` explicitly when calling summary generation
3. Filename is now consistently based on the run_id

**What didn't change:**
- EEG analysis logic
- Summary content/format
- Excel file structure
- Any other business logic

**Test it now!** Run a pipeline and watch the console for the new consistent filenames. 🎉
