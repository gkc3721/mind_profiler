# Excel Summary Download Integration Summary

## Overview
Integrated the Excel summary file (profile_summary.xlsx) download functionality into the FastAPI + React app. Users can now download the Excel summary after each pipeline run.

## Changes Made

### 1. Backend - New Download Endpoint (`backend/app/routes/run.py`)

**Added:** `GET /runs/{run_id}/summary` endpoint

```python
@router.get("/runs/{run_id}/summary")
async def get_summary_endpoint(run_id: str):
    """Download the profile summary Excel file for a run"""
    # Tries multiple possible file names:
    # - profile_summary{run_id}.xlsx
    # - profile_summary.xlsx
    # Returns 404 if not found
```

**Features:**
- Serves the Excel file with proper MIME type
- Sets download filename to `profile_summary_{run_id}.xlsx`
- Handles missing files with 404 error
- Tries multiple filename patterns for compatibility

**MIME Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 2. Backend - Summary Generation (Already Implemented)

The `backend/app/core/engine.py` already generates the Excel summary:

**In `run_batch()` function:**
```python
# Calls analyze_processing_log.py via subprocess
# Generates profile_summary{run_id}.xlsx in run directory
# Includes in RunResult.summary_xlsx
```

**In `run_single()` function:**
```python
# Same logic as run_batch
# Summary generated even for single CSV uploads
```

**Key behavior:**
- Summary generated automatically after pipeline execution
- Uses existing `analyze_processing_log.py` script
- File path stored in `RunResult.summary_xlsx`
- Returns `None` if generation fails

### 3. TypeScript Types (Already Correct)

**`frontend/src/types/runs.ts`:**
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
  summary_xlsx: string | null;  // ✓ Already present
}
```

### 4. API Client Helper (`frontend/src/api/runsApi.ts`)

**Added:** `getSummaryUrl()` helper function

```typescript
export const getSummaryUrl = (runId: string): string => {
  return `http://localhost:8000/runs/${runId}/summary`;
};
```

**Usage:**
```typescript
import { getSummaryUrl } from '../api/runsApi';
const downloadUrl = getSummaryUrl(result.run_id);
```

### 5. Frontend - Download Button (`frontend/src/components/RunSummary.tsx`)

**Added:** Download button in Run Results card header

**Location:** Top-right of RunSummary component, next to the title

**Appearance:**
- Emerald-to-teal gradient button
- Download icon (document with down arrow)
- Text: "Download Excel Summary"
- Only shows if `result.summary_xlsx` is not null

**Implementation:**
```tsx
{result.summary_xlsx && (
  <a
    href={getSummaryUrl(result.run_id)}
    download
    className="px-4 py-2 rounded-xl font-medium bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-600 hover:to-teal-500 text-white shadow-md transition-all duration-200 flex items-center gap-2"
  >
    <svg>...</svg>
    Download Excel Summary
  </a>
)}
```

## User Experience

### Run Pipeline Page

1. User configures and runs pipeline
2. Pipeline completes successfully
3. **Run Results** card appears with stats
4. **"Download Excel Summary"** button appears in top-right
5. User clicks button → Excel file downloads

### Runs History Page (Future Enhancement)

The download button will be added in a similar way:
- In the run details modal/panel
- Same styling and behavior
- Uses `getSummaryUrl(run.run_id)`

## File Locations

### Backend
```
app/data/runs/{run_id}/
  ├── processing_log{run_id}.csv
  ├── profile_summary{run_id}.xlsx  ← Generated Excel file
  ├── metadata.json
  └── graphs/
      └── *.png
```

### Download URL
```
GET http://localhost:8000/runs/{run_id}/summary
```

### Downloaded Filename
```
profile_summary_{run_id}.xlsx
```

Example: `profile_summary_20251130_143022.xlsx`

## Technical Details

### Summary Generation Process

1. **Pipeline completes** → `process_pipeline()` returns
2. **Log file created** → `processing_log{run_id}.csv`
3. **Engine calls** → `analyze_processing_log.py` via subprocess
4. **Excel generated** → `profile_summary{run_id}.xlsx`
5. **Path stored** → `RunResult.summary_xlsx`
6. **Metadata saved** → `metadata.json`

### Error Handling

**Backend:**
- Returns 404 if run_id doesn't exist
- Returns 404 if summary file not found
- Prints warning if Excel generation fails (but doesn't crash)

**Frontend:**
- Button only appears if `summary_xlsx` is not null
- Browser handles download errors naturally
- No loading state needed (browser manages download)

### Browser Behavior

- `<a download>` attribute triggers download dialog
- Browser downloads file with custom filename
- No page navigation occurs
- Works in all modern browsers

## Testing Checklist

### Backend
- [x] Endpoint added to `routes/run.py`
- [x] FileResponse returns correct MIME type
- [x] Handles missing files with 404
- [x] Tries multiple filename patterns

### Frontend
- [x] TypeScript types updated (already had field)
- [x] API helper function added
- [x] Download button added to RunSummary
- [x] Button only shows when summary_xlsx exists
- [x] Button styled with ocean theme

### Integration
- [ ] Run pipeline with folder path
- [ ] Verify Excel file generates
- [ ] Verify download button appears
- [ ] Click button and verify download
- [ ] Verify Excel content is correct

### Edge Cases
- [ ] Single CSV upload also generates summary
- [ ] Summary works with 1 file
- [ ] Summary works with multiple files
- [ ] No crash if Excel generation fails

## Future Enhancements (Optional)

1. **Add to Runs History Page:**
   - Download button in run details modal
   - Same implementation as RunSummary

2. **Inline Preview:**
   - Show Excel preview in browser
   - Use a library like SheetJS

3. **Multiple Format Options:**
   - CSV export option
   - PDF report option

4. **Progress Indicator:**
   - Show "Generating summary..." message
   - Disable button until ready

5. **Email Option:**
   - Send summary via email
   - Notification when ready

## No Changes to Business Logic

✅ **Preserved:**
- Excel file format unchanged
- Summary calculation logic unchanged
- `analyze_processing_log.py` script unchanged
- Thresholds and metrics unchanged
- Profile matching logic unchanged

✅ **Only Added:**
- Download endpoint
- Frontend UI for download
- API helper function

## Summary Excel Content

The Excel file contains (from `analyze_processing_log.py`):
- Profile distribution summary
- Counts by profile type
- Statistics and aggregations
- Generated in batch format (even for single file)

This format remains identical to the standalone script output.
