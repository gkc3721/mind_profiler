# UI Changes Summary - Simplified Data Source Selector

## Changes Made

Removed the "Single CSV Path" option from the Data Source selector, simplifying the UI to only support:
1. **Process Folder** - batch process all CSVs in a folder
2. **Upload CSV** - process a single uploaded CSV file

## Files Modified

### 1. `frontend/src/components/DataSourceSelector.tsx`

**Type Definition Updated:**
```typescript
// Before:
export type DataSourceType = 'folder' | 'path' | 'upload';

// After:
export type DataSourceType = 'folder' | 'upload';
```

**Removed State:**
- Removed `csvPath` state variable (no longer needed)

**Removed UI Elements:**
- Removed "Single CSV Path" tab button
- Removed entire "path" tab content section:
  - CSV File Path input field
  - "Use Path" button

**Visual Enhancement:**
- Added `font-semibold` class to active tab for better visual feedback

**Result:** Component now only has 2 tabs instead of 3.

### 2. `frontend/src/pages/RunPipelinePage.tsx`

**Import Updated:**
```typescript
// Before:
import { runBatch, runSingle, runUpload, listPlots } from '../api/runsApi';

// After:
import { runBatch, runUpload, listPlots } from '../api/runsApi';
```

**Simplified Pipeline Execution Logic:**
```typescript
// Before:
if (dataSource.type === 'folder') {
  runResult = await runBatch({ ...config, data_root: dataSource.value as string });
} else if (dataSource.type === 'path') {
  runResult = await runSingle(config, dataSource.value as string);
} else {
  runResult = await runUpload(config, dataSource.value as File);
}

// After:
if (dataSource.type === 'folder') {
  runResult = await runBatch({ ...config, data_root: dataSource.value as string });
} else {
  // dataSource.type === 'upload'
  runResult = await runUpload(config, dataSource.value as File);
}
```

**Simplified Data Source Display:**
```typescript
// Before:
{dataSource.type === 'folder' ? `Folder: ${dataSource.value}` : 
  dataSource.type === 'path' ? `CSV: ${dataSource.value}` : 
  `Upload: ${(dataSource.value as File).name}`}

// After:
{dataSource.type === 'folder' 
  ? `Folder: ${dataSource.value}` 
  : `Upload: ${(dataSource.value as File).name}`}
```

## What Was NOT Changed

### Backend Remains Intact
- **POST /run/single** endpoint still exists in the backend
- The `runSingle` function still exists in `frontend/src/api/runsApi.ts`
- Backend can still process single CSV files by path if needed

### Why Keep Backend Endpoint?
- May be useful for future features
- May be called programmatically or via API
- No harm in keeping it available

## How the UI Works Now

### Process Folder Flow
1. User clicks "Process Folder" tab
2. User enters folder path (e.g., `/Users/umutkaya/Documents/Zenin Mind Reader/aile`)
3. User clicks "Use Folder" → blue info box shows "Data source selected: Folder: /path/to/folder"
4. User clicks "Run Pipeline"
5. Frontend calls `POST /run/batch` with `data_root` set to the folder path
6. Backend processes all CSV files in that folder

### Upload CSV Flow
1. User clicks "Upload CSV" tab
2. User selects a CSV file from their computer
3. User clicks "Use Upload" → blue info box shows "Data source selected: Upload: filename.csv"
4. User clicks "Run Pipeline"
5. Frontend calls `POST /run/upload` with the file as multipart/form-data
6. Backend saves the file temporarily and processes it

## Benefits of This Change

1. **Simpler UX** - Two options instead of three
2. **Less Confusion** - "Single CSV Path" and "Upload CSV" were redundant (both process one file)
3. **Cleaner Code** - Less branching logic in `RunPipelinePage`
4. **Better TypeScript Types** - `DataSourceType` now only has 2 valid values
5. **Reduced Maintenance** - One less UI path to maintain and test

## Testing Checklist

- [x] DataSourceSelector component updated
- [x] RunPipelinePage updated
- [x] TypeScript types updated
- [ ] Test "Process Folder" → "Run Pipeline" flow
- [ ] Test "Upload CSV" → "Run Pipeline" flow
- [ ] Verify no TypeScript errors
- [ ] Verify UI renders correctly with only 2 tabs
- [ ] Verify blue info box shows correct data source
- [ ] Verify error handling still works for both modes
