# Summary and Plots Display Issue - Diagnosis & Fix

## Current Status

After implementing the summary generation fix, you're still seeing:
- ✅ Run Results card shows basic stats
- ❌ No "Download Excel" button visible
- ❌ "No plots available" message even though pipeline ran

## Root Causes

### 1. Summary Button Already Exists (Just Not Visible?)

The `RunSummary` component already has the download button code:

```typescript
{result.summary_xlsx && (
  <a href={getSummaryUrl(result.run_id)} download>
    Download Excel
  </a>
)}
```

**This means:** If `result.summary_xlsx` is null or undefined, the button won't show.

### 2. Plots Code Already Exists (Just Not Working?)

The `RunPipelinePage` already:
1. Fetches plots: `listPlots(result.run_id)`
2. Sets state: `setPlots(data.plots)`
3. Passes to gallery: `<PlotGallery runId={result.run_id} plots={plots} />`

**This means:** If `data.plots` is empty array, the gallery shows "No plots available".

## Diagnosis Steps

### Step 1: Check Backend Response

After running the pipeline, check the browser DevTools (F12):

1. **Go to Network tab**
2. **Find the POST request** to `/run/upload-batch`
3. **Check the Response** - look for `summary_xlsx` field:

```json
{
  "run_id": "20251201_123456",
  "summary_xlsx": "path/to/file.xlsx",  // ← Should NOT be null
  "plots_dir": "path/to/graphs",
  ...
}
```

**If `summary_xlsx` is null:** The generation failed (check backend console for errors)

### Step 2: Check Plots API Call

Still in Network tab:

1. **Find the GET request** to `/runs/{run_id}/plots`
2. **Check the Response:**

```json
{
  "plots": ["plot1.png", "plot2.png", ...]  // ← Should NOT be empty
}
```

**If `plots` is empty array:** Either:
- Plots weren't generated
- They're in wrong directory
- Directory doesn't exist

### Step 3: Check File System

Verify files actually exist on disk:

```bash
# Replace {run_id} with your actual run ID
cd backend/app/data/runs/{run_id}

# Check for summary
ls -la profile_summary*.xlsx

# Check for plots directory
ls -la graphs/
```

**Expected:**
```
profile_summary20251201_123456.xlsx  ← Should exist
graphs/                              ← Should exist
  graph1.png
  graph2.png
  ...
```

## Most Likely Issues

### Issue 1: Summary File Path is Absolute, Not Relative

The backend is setting:
```python
summary_xlsx=str(summary_xlsx_path) if summary_xlsx_path and summary_xlsx_path.exists() else None
```

This returns the **full absolute path**, but the endpoint expects just the filename.

**Fix:** Change to just the filename:

```python
summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
```

### Issue 2: Plots Directory Named Wrong

The pipeline might be creating plots in:
- `plots/` instead of `graphs/`
- `{run_id}_plots/` 
- Or some other name

**Check:** Look in the run directory for any directory containing PNG files.

**Fix:** Either:
1. Update the endpoint to look in the correct directory
2. Update the pipeline to use `graphs/` directory

### Issue 3: RunResult Not Being Serialized Correctly

The `summary_xlsx` field might not be serializing correctly in the FastAPI response.

**Check:** Backend console should show the RunResult being created with `summary_xlsx` set.

**Fix:** Ensure the Pydantic model serializes the field correctly.

## Quick Fixes

### Fix 1: Update Engine to Return Correct summary_xlsx

The issue is that we're returning the full path, but we should return just the filename or a relative path.

**File:** `backend/app/core/engine.py`

**Change:**
```python
# Before (both run_batch and run_single):
summary_xlsx=str(summary_xlsx_path) if summary_xlsx_path and summary_xlsx_path.exists() else None

# After:
summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
```

Or keep it as is and update the endpoint to handle full paths.

### Fix 2: Add Debug Logging

**File:** `backend/app/core/engine.py`

**Add before return:**
```python
print(f"🔍 DEBUG - Returning RunResult:")
print(f"  summary_xlsx: {summary_xlsx_path.name if summary_xlsx_path else None}")
print(f"  plots_dir: {run_dir / 'graphs'}")
print(f"  plots_dir exists: {(run_dir / 'graphs').exists()}")
if (run_dir / 'graphs').exists():
    plots = list((run_dir / 'graphs').rglob('*.png'))
    print(f"  plots count: {len(plots)}")
```

This will help diagnose what's being returned.

### Fix 3: Verify Plots Directory Name

**Check what zenin_plot_generator creates:**

```bash
# After a run, find the run directory
cd backend/app/data/runs
ls -la  # Find latest directory

cd {latest_run_id}
ls -la  # Look for directories containing plots
```

**If plots are in a different directory:**

Option A: Update engine.py to use correct directory name:
```python
plots_dir=str(run_dir / "actual_directory_name"),
```

Option B: Update the endpoint to look in correct directory:
```python
plots_dir = run_dir / "actual_directory_name"
```

## Testing Procedure

### Test 1: Summary Generation

1. Run pipeline
2. Check backend console for:
   ```
   ✅ Profile summary created: /path/to/profile_summary20251201_XXXXXX.xlsx
   ```
3. Check file exists:
   ```bash
   ls backend/app/data/runs/{run_id}/profile_summary*.xlsx
   ```

**If file exists but button doesn't show:**
- Check DevTools Network tab for the POST response
- Verify `summary_xlsx` field is not null
- Check if it's an absolute path vs filename

### Test 2: Plots Generation

1. Run pipeline
2. Check if plots directory exists:
   ```bash
   ls backend/app/data/runs/{run_id}/graphs/
   ```
3. Count PNG files:
   ```bash
   ls backend/app/data/runs/{run_id}/graphs/*.png | wc -l
   ```
4. Test the endpoint manually:
   ```bash
   curl http://localhost:8000/runs/{run_id}/plots
   ```

**If plots exist but UI shows "No plots available":**
- Check the API response in DevTools
- Verify the `plots` array is not empty
- Check console for JavaScript errors

### Test 3: Frontend State

Add console logging in `RunPipelinePage.tsx`:

```typescript
useEffect(() => {
  if (result) {
    console.log('🔍 Result received:', result);
    console.log('🔍 summary_xlsx:', result.summary_xlsx);
    
    listPlots(result.run_id)
      .then((data) => {
        console.log('🔍 Plots fetched:', data.plots);
        setPlots(data.plots);
      })
      .catch(console.error);
  }
}, [result]);
```

This will show exactly what the frontend is receiving.

## Quick Verification Commands

```bash
# 1. Check if backend is running
curl http://localhost:8000/docs

# 2. After a run, check the response
# (Use the Network tab in DevTools)

# 3. Manually test endpoints
RUN_ID="20251201_XXXXXX"  # Replace with actual ID
curl http://localhost:8000/runs/$RUN_ID/plots
curl http://localhost:8000/runs/$RUN_ID/summary -I  # Check if 404 or 200

# 4. Check file system
ls -la backend/app/data/runs/$RUN_ID/
```

## Most Likely Solution

Based on the code review, the most likely issue is that `summary_xlsx` is being set to the full absolute path, but it should be just the filename. 

**Apply this fix:**

```python
# In engine.py, both run_batch() and run_single(), change:
summary_xlsx=str(summary_xlsx_path) if summary_xlsx_path and summary_xlsx_path.exists() else None

# To:
summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
```

This will make the frontend check work correctly because it just checks if the field is truthy, and the backend endpoint can still find the file using the run_id.

## Next Steps

1. Apply the fix above
2. Run a test pipeline
3. Check DevTools Network tab to verify `summary_xlsx` is not null
4. Check that download button appears
5. Test downloading the file
6. Check plots array in Network tab
7. Verify plots display in UI

If issues persist after these fixes, the problem is likely in the pipeline itself not generating the files, not in the integration code.
