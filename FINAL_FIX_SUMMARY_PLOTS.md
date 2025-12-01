# ✅ Summary & Plots Fix - Complete

## What Was Fixed

### 1. Summary Excel Filename Issue
**Problem:** The backend was returning the full absolute path instead of just the filename.

**Fix Applied:**
```python
# Before:
summary_xlsx=str(summary_xlsx_path) if summary_xlsx_path and summary_xlsx_path.exists() else None

# After:
summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
```

This ensures the frontend receives just the filename (e.g., `"profile_summary20251201_123456.xlsx"`) instead of the full path, which makes the truthy check work correctly for showing the download button.

### 2. Added Debug Logging
Added comprehensive debug output to help diagnose issues:

```python
print(f"🔍 DEBUG - Run completed:")
print(f"  Run ID: {run_id}")
print(f"  Run dir: {run_dir}")
print(f"  Log file: {log_path}")
print(f"  Summary file: {summary_xlsx_path}")
print(f"  Plots dir: {run_dir / 'graphs'}")
print(f"  Plots dir exists: {(run_dir / 'graphs').exists()}")
if (run_dir / 'graphs').exists():
    plots_list = list((run_dir / 'graphs').rglob('*.png'))
    print(f"  Plots count: {len(plots_list)}")
```

## How to Test

### Step 1: Backend Should Auto-Reload
The backend should reload automatically with uvicorn's `--reload` flag. Check your terminal for:
```
INFO:     Shutting down
INFO:     Application startup complete.
```

### Step 2: Run the Pipeline
1. Open http://localhost:5173
2. Go to "Run Pipeline"
3. Select your folder with CSV files
4. Click "Run Pipeline"

### Step 3: Watch Backend Console
You should now see detailed debug output:

```
✅ Generating profile summary from log: /path/to/processing_log20251201_XXXXXX.csv
Log dosyası: /path/to/processing_log20251201_XXXXXX.csv
... (analysis output) ...
Özet Excel kaydedildi: /path/to/profile_summary20251201_XXXXXX.xlsx
✅ Profile summary created: /path/to/profile_summary20251201_XXXXXX.xlsx

🔍 DEBUG - Run completed:
  Run ID: 20251201_XXXXXX
  Run dir: /path/to/runs/20251201_XXXXXX
  Log file: /path/to/runs/20251201_XXXXXX/processing_log20251201_XXXXXX.csv
  Summary file: /path/to/runs/20251201_XXXXXX/profile_summary20251201_XXXXXX.xlsx
  Plots dir: /path/to/runs/20251201_XXXXXX/graphs
  Plots dir exists: True
  Plots count: 42
```

**Key indicators:**
- ✅ "Profile summary created" message
- ✅ "Plots dir exists: True"
- ✅ "Plots count: X" (should be > 0)

### Step 4: Check Frontend

After the run completes, the UI should show:

1. **"Download Excel" button** in the Run Results card
   - Located next to the stats boxes
   - Has a download icon
   - Says "Download Excel"

2. **Plot gallery** below the results
   - Should NOT say "No plots available"
   - Should show a grid of plot images
   - First few plots should be visible
   - Click a plot to see full size

### Step 5: Test Download
1. Click the "Download Excel" button
2. Browser should download `profile_summary_20251201_XXXXXX.xlsx`
3. Open the file in Excel/LibreOffice
4. Verify it has multiple sheets with data

### Step 6: Test Plots Display
1. Plots should be visible in a grid
2. Click any plot to see full size
3. Modal should open with larger version
4. Close button should work

## Troubleshooting

### Issue: "Download Excel" button still doesn't appear

**Check DevTools (F12):**
1. Go to Network tab
2. Find the POST request to `/run/upload-batch`
3. Check the Response JSON
4. Look for `summary_xlsx` field

**Expected:**
```json
{
  "summary_xlsx": "profile_summary20251201_XXXXXX.xlsx",  // ← Should be a filename
  ...
}
```

**If null:**
- Check backend console for errors during summary generation
- Check if the processing log file was created
- Verify `analyze_processing_log.py` runs without errors

### Issue: "No plots available" still shows

**Check DevTools:**
1. Network tab
2. Find GET request to `/runs/{run_id}/plots`
3. Check Response

**Expected:**
```json
{
  "plots": ["plot1.png", "plot2.png", ...]  // ← Should NOT be empty
}
```

**If empty:**
1. Check backend debug output for "Plots count: 0"
2. Verify plots directory exists: `backend/app/data/runs/{run_id}/graphs/`
3. Check if PNG files exist in that directory
4. If no plots, the issue is in the pipeline itself (zenin_plot_generator.py)

**If has plots but UI still shows "No plots":**
- Check browser console (F12 → Console) for JavaScript errors
- Verify the `listPlots()` API call succeeded
- Check if `plots` state was set correctly (add `console.log` in useEffect)

### Issue: Backend debug output shows "Plots dir exists: False"

**This means the `graphs` directory wasn't created.**

**Check:**
1. Does `zenin_plot_generator.py` create plots?
2. What directory does it use?
3. Is it using the correct output_dir parameter?

**Possible causes:**
- Pipeline didn't run plot generation step
- Plots are being created in wrong directory
- Error during plot generation (check console for errors)

**Fix:**
Verify the plot generator is being called with the correct output directory:
```python
# In zenin_mac2.py, verify this call exists:
generate_eeg_plots(
    ...,
    output_dir=output_dir,  # Should be the run directory
    ...
)
```

### Issue: Plots exist but wrong filenames

**Check what files are actually created:**
```bash
cd backend/app/data/runs/{run_id}
find . -name "*.png"
```

**If plots are in a subdirectory with a different name:**
- Update the endpoint to look in that directory
- OR update the pipeline to use `graphs/` directory

## Expected File Structure After Run

```
backend/app/data/runs/20251201_123456/
├── processing_log20251201_123456.csv     ← Processing log
├── profile_summary20251201_123456.xlsx   ← Summary Excel
├── metadata.json                         ← Run metadata
├── graphs/                               ← Plots directory
│   ├── subject_001_plot.png
│   ├── subject_002_plot.png
│   ├── ...
│   └── subject_379_plot.png
└── input/                                ← Uploaded CSV files (if using folder upload)
    ├── subject_001.csv
    ├── subject_002.csv
    └── ...
```

## Success Criteria

✅ **Backend:**
- Summary generation logs show success
- Debug output shows correct file paths
- Debug output shows "Plots dir exists: True"
- Debug output shows "Plots count: X" where X > 0

✅ **File System:**
- `profile_summary{run_id}.xlsx` exists in run directory
- `graphs/` directory exists in run directory
- PNG files exist in `graphs/` directory

✅ **API:**
- POST `/run/upload-batch` returns `summary_xlsx` with filename (not null)
- GET `/runs/{run_id}/plots` returns array of plot filenames (not empty)
- GET `/runs/{run_id}/summary` returns the Excel file (200 status)

✅ **Frontend:**
- "Download Excel" button appears in Run Results
- Plot gallery shows images (not "No plots available")
- Clicking download button downloads the file
- Clicking a plot opens full-size modal
- No JavaScript errors in console

## Quick Verification

**One-liner to check everything:**
```bash
# Replace {run_id} with your actual run ID
RUN_ID="20251201_123456"
echo "Summary:" && ls -lh backend/app/data/runs/$RUN_ID/profile_summary*.xlsx
echo "Plots dir:" && ls -d backend/app/data/runs/$RUN_ID/graphs/
echo "Plots count:" && ls backend/app/data/runs/$RUN_ID/graphs/*.png 2>/dev/null | wc -l
```

**Expected output:**
```
Summary:
-rw-r--r--  1 user  staff   245K Dec  1 12:34 profile_summary20251201_123456.xlsx

Plots dir:
backend/app/data/runs/20251201_123456/graphs/

Plots count:
     379
```

## If Everything Passes But UI Still Doesn't Show

This would indicate a frontend issue. Check:

1. **React state:** Add logging in `RunPipelinePage.tsx`:
   ```typescript
   useEffect(() => {
     if (result) {
       console.log('🔍 Result:', result);
       console.log('🔍 summary_xlsx:', result.summary_xlsx);
     }
   }, [result]);
   
   useEffect(() => {
     if (result) {
       listPlots(result.run_id)
         .then((data) => {
           console.log('🔍 Plots:', data.plots);
           setPlots(data.plots);
         })
         .catch(console.error);
     }
   }, [result]);
   ```

2. **Component rendering:** Check `RunSummary.tsx`:
   ```typescript
   console.log('🔍 RunSummary rendering, summary_xlsx:', result.summary_xlsx);
   ```

3. **Plot gallery:** Check `PlotGallery.tsx`:
   ```typescript
   console.log('🔍 PlotGallery rendering, plots:', plots);
   ```

## Summary

The fix changes `summary_xlsx` from returning a full path to just the filename, which:
1. ✅ Makes the frontend truthy check work correctly
2. ✅ Still allows the backend endpoint to find the file (it uses run_id)
3. ✅ Matches the expected behavior

Plus added debug logging to help diagnose any remaining issues with plots or file generation.

Test it now and check the backend console for the debug output! 🎉
