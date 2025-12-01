# Bug Fix Summary - 404 "Not Found" Error

## Problem

When clicking "Use Folder" → "Run Pipeline" in the frontend, the application showed a red error box with "Not Found", and the backend logs showed a 404 error.

## Root Cause

**Backend Route Mismatch:**
- The backend routes in `backend/app/routes/run.py` were defined as:
  - `@router.post("/batch")` 
  - `@router.post("/single")`
  - `@router.post("/upload")`
- The router was included in `main.py` with an **empty prefix**: `app.include_router(run.router, prefix="", tags=["run"])`
- This resulted in actual endpoints being:
  - POST `/batch` (NOT `/run/batch`)
  - POST `/single` (NOT `/run/single`)
  - POST `/upload` (NOT `/run/upload`)

**But the frontend was calling:**
- POST `/run/batch` (in `runsApi.ts`)
- POST `/run/single` (in `runsApi.ts`)
- POST `/run/upload` (in `runsApi.ts`)

**Result:** 404 Not Found because `/run/batch` didn't exist!

## Files Modified

### 1. `backend/app/routes/run.py`
**Changed:** Updated route decorators to include the `/run` prefix in the path

**Before:**
```python
@router.post("/batch", response_model=RunResult)
@router.post("/single", response_model=RunResult)
@router.post("/upload", response_model=RunResult)
```

**After:**
```python
@router.post("/run/batch", response_model=RunResult)
@router.post("/run/single", response_model=RunResult)
@router.post("/run/upload", response_model=RunResult)
```

**Why:** This ensures that even with an empty prefix in `main.py`, the endpoints are at `/run/batch`, `/run/single`, and `/run/upload`, matching what the frontend expects.

### 2. `frontend/src/pages/RunPipelinePage.tsx`
**Changed:** Enhanced error handling and added console logging

**Improvements:**
- Added console.log statements to trace the API call flow
- Improved error message extraction from Axios error responses
- Added HTTP status code to error messages (e.g., `[404] Not Found`)
- Added console.error with full error object for debugging
- Added blue info box showing selected data source
- Added "Error:" prefix to error messages for clarity

**Before:**
```typescript
setError(err.response?.data?.detail || err.message || 'Failed to run pipeline');
```

**After:**
```typescript
console.error('Pipeline run failed:', err);
console.error('Error response:', err.response);

let errorMessage = 'Failed to run pipeline';
if (err.response?.data?.detail) {
  errorMessage = err.response.data.detail;
} else if (err.message) {
  errorMessage = err.message;
}

if (err.response?.status) {
  errorMessage = `[${err.response.status}] ${errorMessage}`;
}

setError(errorMessage);
```

## How the Fix Works

### API Call Flow (After Fix)

1. **User clicks "Use Folder":**
   - Component: `DataSourceSelector.tsx`
   - Action: Calls `onSelect('folder', folderPath)`
   - Effect: Updates React state in `RunPipelinePage` → `setDataSource({ type: 'folder', value: '/path/to/folder' })`
   - **NO API CALL MADE** ✓

2. **User clicks "Run Pipeline":**
   - Component: `RunPipelinePage.tsx`
   - Action: Calls `handleRun()`
   - Console logs: `"Running pipeline with config: {type: 'folder', value: '/path/...', config: {...}}"`
   - Calls: `runBatch({ ...config, data_root: '/path/to/folder' })`
   - API Call: `POST http://localhost:8000/run/batch`
   - Request Body:
     ```json
     {
       "dominance_delta": 29.0,
       "balance_threshold": 22.0,
       "denge_mean_threshold": 46.0,
       "window_secs": 30,
       "window_samples": 5,
       "data_root": "/Users/umutkaya/Documents/Zenin Mind Reader/aile",
       "profile_set_id": "meditasyon",
       "band_thresholds": {...}
     }
     ```

3. **Backend receives request:**
   - Endpoint: POST `/run/batch`
   - Handler: `run_batch_endpoint()` in `backend/app/routes/run.py`
   - Calls: `engine.run_batch(config)`
   - Returns: `RunResult` with run_id, processed_files, matched_count, etc.

## Why "Use Folder" Button Doesn't Make API Call

The `DataSourceSelector` component's `handleSubmit()` function only calls the `onSelect` callback prop:

```typescript
const handleSubmit = () => {
  if (activeTab === 'folder' && folderPath) {
    onSelect('folder', folderPath);  // Only updates parent state
  }
};
```

In `RunPipelinePage`, this prop is connected to state update:
```typescript
<DataSourceSelector onSelect={(type, value) => setDataSource({ type, value })} />
```

**No HTTP request is triggered** - it's purely a local state change.

## Debugging Improvements

Now when errors occur, the browser console will show:
```
Running pipeline with config: {type: 'folder', value: '/path/...', config: {...}}
Calling runBatch with data_root: /path/to/folder
Pipeline run failed: AxiosError {...}
Error response: {status: 404, data: {...}}
```

And the UI will show:
```
[404] Not Found
```

Instead of just:
```
Not Found
```

## Testing Checklist

- [x] Backend server restart (to load updated routes)
- [x] Frontend refresh (to load updated error handling)
- [ ] Click "Use Folder" → should see blue info box, NO error
- [ ] Click "Run Pipeline" → should call POST `/run/batch` successfully
- [ ] Check browser DevTools console → should see detailed logs
- [ ] Check backend terminal → should see pipeline processing logs

## Additional Notes

- The frontend API client (`runsApi.ts`) was already correct - no changes needed
- The `DataSourceSelector` component was already correct - no changes needed  
- No changes to business logic (EEG processing, profile matching, etc.)
- The fix only corrects the API routing layer
