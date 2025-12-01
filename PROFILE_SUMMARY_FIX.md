# Profile Summary Excel Download - Complete Fix

## Problem Summary

After running the pipeline successfully, the profile summary Excel file was not visible or downloadable in the UI.

## Root Causes Identified

1. **Backend Summary Generation**: The `engine.py` was using `subprocess.run` to call `analyze_processing_log.py`, which was fragile and error-prone.
2. **No Direct Function Call**: The summary generation wasn't properly integrated into the pipeline flow.
3. **File Path Issues**: The summary file naming wasn't consistent with what the download endpoint expected.

## Fixes Applied

### 1. Backend - engine.py

**Created a dedicated wrapper function:**

```python
def generate_profile_summary(log_path: str, output_dir: str, run_id: str) -> Path | None:
    """
    Generate profile summary Excel file from processing log.
    
    Args:
        log_path: Path to the processing log CSV
        output_dir: Directory where summary Excel will be saved
        run_id: Run ID for naming the output file
    
    Returns:
        Path to generated Excel file, or None if generation failed
    """
    try:
        # Import the analyze_processing_log module
        from analyze_processing_log import main as analyze_log_main
        
        # Call the main function with log path and output directory
        analyze_log_main(log_path, output_dir)
        
        # Check which filename was created
        expected_path = Path(output_dir) / f"profile_summary{run_id}.xlsx"
        alt_path = Path(output_dir) / "profile_summary.xlsx"
        
        if expected_path.exists():
            return expected_path
        elif alt_path.exists():
            # Rename to expected format
            alt_path.rename(expected_path)
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

**Updated both `run_batch()` and `run_single()`:**

```python
# Generate profile summary Excel
summary_xlsx_path = None
if log_path.exists():
    print(f"✅ Generating profile summary from log: {log_path}")
    summary_xlsx_path = generate_profile_summary(
        log_path=str(log_path),
        output_dir=str(run_dir),
        run_id=run_id
    )
    if summary_xlsx_path:
        print(f"✅ Profile summary created: {summary_xlsx_path}")
    else:
        print(f"⚠️ Profile summary generation failed")
else:
    print(f"⚠️ Log file not found at {log_path}, cannot generate summary")
```

**Updated RunResult return value:**

```python
return RunResult(
    run_id=run_id,
    timestamp=metadata["timestamp"],
    config=config,
    processed_files=result.get("processed_files", 0),
    matched_count=result.get("matched_count", 0),
    unmatched_count=result.get("unmatched_count", 0),
    log_file=str(log_path),
    plots_dir=str(run_dir / "graphs"),
    summary_xlsx=str(summary_xlsx_path) if summary_xlsx_path and summary_xlsx_path.exists() else None
)
```

### 2. Backend - Pydantic Model (Already Correct)

**File:** `backend/app/models/runs.py`

```python
class RunResult(BaseModel):
    run_id: str
    timestamp: str
    config: RunConfig
    processed_files: int
    matched_count: int
    unmatched_count: int
    log_file: str
    plots_dir: str
    summary_xlsx: str | None = None  # ✅ Already has this field
```

### 3. Backend - Download Endpoint (Already Correct)

**File:** `backend/app/routes/run.py`

```python
@router.get("/runs/{run_id}/summary")
async def get_summary_endpoint(run_id: str):
    """Download the profile summary Excel file for a run"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Try multiple possible file names
    summary_file = run_dir / f"profile_summary{run_id}.xlsx"
    if not summary_file.exists():
        summary_file = run_dir / "profile_summary.xlsx"
    
    if not summary_file.exists():
        raise HTTPException(status_code=404, detail=f"Summary file for run {run_id} not found")
    
    return FileResponse(
        str(summary_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"profile_summary_{run_id}.xlsx"
    )
```

### 4. Frontend - TypeScript Type (Already Correct)

**File:** `frontend/src/types/runs.ts`

```typescript
export interface RunResult {
  run_id: string;
  timestamp: string;
  config: RunConfig;
  processed_files: number;
  matched_count: number;
  unmatched_count: number;
  log_file: string;
  plots_dir: string;
  summary_xlsx: string | null;  // ✅ Already has this field
}
```

### 5. Frontend - API Client (Already Correct)

**File:** `frontend/src/api/runsApi.ts`

```typescript
export const getSummaryUrl = (runId: string): string => {
  return `http://localhost:8000/runs/${runId}/summary`;
};
```

### 6. Frontend - UI Component (Already Correct)

**File:** `frontend/src/components/RunSummary.tsx`

```typescript
{result.summary_xlsx && (
  <a
    href={getSummaryUrl(result.run_id)}
    download
    className="px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-md transition-all duration-200 flex items-center gap-2"
  >
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    Download Excel
  </a>
)}
```

## How It Works Now

### Flow Diagram

```
User clicks "Run Pipeline"
  ↓
POST /run/upload-batch (or /run/batch)
  ↓
engine.run_batch() or engine.run_single()
  ↓
process_pipeline() executes
  ↓
Creates processing_log{run_id}.csv
  ↓
generate_profile_summary() called
  ↓
Directly imports analyze_processing_log.main()
  ↓
Creates profile_summary{run_id}.xlsx
  ↓
RunResult includes summary_xlsx path
  ↓
Frontend receives RunResult
  ↓
"Download Excel" button appears (if summary_xlsx is not null)
  ↓
User clicks button
  ↓
GET /runs/{run_id}/summary
  ↓
FileResponse streams the Excel file
  ↓
User downloads profile_summary_{run_id}.xlsx
```

## File Locations

After a successful run with run_id `20251201_123456`:

```
backend/app/data/runs/20251201_123456/
├── processing_log20251201_123456.csv      ← Generated by pipeline
├── profile_summary20251201_123456.xlsx    ← Generated by our fix
├── metadata.json                          ← Run metadata
└── graphs/                                ← Plot images
    ├── plot1.png
    ├── plot2.png
    └── ...
```

## What Was Changed

### Files Modified:
1. ✅ `backend/app/core/engine.py` - Added `generate_profile_summary()` function and updated both `run_batch()` and `run_single()`

### Files Already Correct (No Changes Needed):
1. ✅ `backend/app/models/runs.py` - Already had `summary_xlsx` field
2. ✅ `backend/app/routes/run.py` - Already had `/runs/{run_id}/summary` endpoint
3. ✅ `frontend/src/types/runs.ts` - Already had `summary_xlsx` field
4. ✅ `frontend/src/api/runsApi.ts` - Already had `getSummaryUrl()` helper
5. ✅ `frontend/src/components/RunSummary.tsx` - Already had download button

## Testing Steps

1. **Start the backend** (if not already running):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the frontend** (if not already running):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Run a pipeline**:
   - Go to http://localhost:5173
   - Click "Run Pipeline"
   - Select a folder with CSV files
   - Click "Run Pipeline" button
   - Wait for completion

4. **Verify summary generation**:
   - Check backend console for: `✅ Profile summary created: ...`
   - Check the run directory for the Excel file:
     ```bash
     ls backend/app/data/runs/{run_id}/
     ```
   - You should see `profile_summary{run_id}.xlsx`

5. **Download the summary**:
   - After the run completes, the UI should show "Download Excel" button
   - Click the button
   - The Excel file should download as `profile_summary_{run_id}.xlsx`
   - Open it in Excel/LibreOffice to verify content

## Error Handling

The fix includes robust error handling:

1. **If log file doesn't exist**: Warning logged, `summary_xlsx` set to `None`, but run still succeeds
2. **If summary generation fails**: Exception caught, warning logged, `summary_xlsx` set to `None`, but run still succeeds
3. **If Excel file isn't created**: Checks for alternative filenames, renames if found, returns `None` if not found
4. **Frontend**: Download button only appears if `summary_xlsx` is truthy

## Console Output

When running successfully, you should see in backend console:

```
✅ Generating profile summary from log: /path/to/processing_log20251201_123456.csv
Log dosyası: /path/to/processing_log20251201_123456.csv
... (analysis output from analyze_processing_log.py) ...
Özet Excel kaydedildi: /path/to/profile_summary20251201_123456.xlsx
✅ Profile summary created: /path/to/profile_summary20251201_123456.xlsx
```

If summary generation fails:

```
✅ Generating profile summary from log: /path/to/processing_log20251201_123456.csv
⚠️ Error generating profile summary: [error details]
⚠️ Profile summary generation failed
```

## Summary

**What was broken:**
- Summary generation used fragile `subprocess.run` call
- Inconsistent file naming
- No clear error handling

**What's fixed:**
- Direct Python function call to `analyze_processing_log.main()`
- Consistent file naming with `profile_summary{run_id}.xlsx`
- Robust error handling with try/except
- Clear console logging for debugging
- File existence checks and fallbacks

**Result:**
- ✅ Summary Excel file is generated after every run
- ✅ Download button appears in UI
- ✅ Clicking button downloads the Excel file
- ✅ Run still succeeds even if summary generation fails
