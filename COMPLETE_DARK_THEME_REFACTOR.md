# Complete Dark Ocean Theme + Folder Upload Refactor Summary

## 🎨 UI/UX Transformation Overview

### What Changed
1. **Navigation**: Horizontal top tabs → Vertical left sidebar
2. **Theme**: Light ocean → Dark ocean with coral accents
3. **Data Source**: Text input for folder path → Folder picker (webkitdirectory)
4. **New Feature**: Batch folder upload endpoint

## 1. Navigation - Left Sidebar

### Before
- Horizontal navigation bar at top
- Tabs with underline for active state
- Logo and nav items in same row

### After
- Fixed left sidebar (264px wide)
- Vertical menu with icons
- Active state: Ocean gradient pill with shadow
- Logo at top with subtitle
- Footer with version info

**File:** `frontend/src/App.tsx`

**Key Features:**
- Sticky sidebar, full height
- Dark slate background (`bg-slate-900`)
- Gradient active indicator
- Icon + label for each nav item
- Smooth transitions on hover/active

## 2. Dark Ocean Theme

### Color Palette

**Background:**
- Main: `bg-slate-950` (#020617)
- Sidebar: `bg-slate-900` (#0F172A)
- Cards: `bg-slate-900` with `border-slate-800`
- Inputs: `bg-slate-800` with `border-slate-700`

**Text:**
- Headings: `text-gray-100` (#F3F4F6)
- Body: `text-gray-300` (#D1D5DB)
- Labels: `text-gray-400` (#9CA3AF)
- Muted: `text-gray-500` (#6B7280)

**Accents:**
- Primary: `from-sky-600 to-teal-500`
- Success: `text-teal-400`, `border-teal-700`
- Warning: `text-amber-400`, `border-amber-700`
- Error: `text-rose-400`, `border-rose-700`
- Info: `text-sky-400`, `border-sky-700`

**Coral (Subtle):**
- Used sparingly in hover states
- Focus rings can use coral
- Alternative gradient: `from-rose-500 to-coral-400`

### Components Updated

**All components now use:**
- Dark card backgrounds
- Light text colors
- Dark inputs with light borders
- Ocean gradient for primary actions
- Subtle shadows and transitions

## 3. Folder Upload Feature

### User Experience

**Before:**
```
[Text Input: /path/to/folder]
[Use Folder Button]
```

User had to:
- Know the absolute path
- Type it manually
- Risk typos

**After:**
```
┌────────────────────────────────────┐
│  📁 Click to select folder         │
│  All CSV files will be uploaded    │
└────────────────────────────────────┘

✓ 15 CSV files selected
  Total size: 2.3 MB
  • file1.csv
  • file2.csv
  • file3.csv
  • file4.csv
  • file5.csv
  ...and 10 more files

[Use Folder (15 files) Button]
```

User now:
- Clicks to open native file picker
- Selects folder visually
- Sees file count and size
- All CSVs uploaded together

### Technical Implementation

**Frontend:** `frontend/src/components/DataSourceSelector.tsx`

```typescript
<input
  type="file"
  webkitdirectory="true"
  multiple
  onChange={handleFolderSelect}
  className="hidden"
  id="folder-upload"
/>
```

**Features:**
- Filters to only CSV files
- Shows file count and total size
- Lists first 5 files + "...X more"
- Validates selection before enabling button

**Backend:** `backend/app/routes/run.py`

**New Endpoint:** `POST /run/upload-batch`

```python
@router.post("/run/upload-batch", response_model=RunResult)
async def run_upload_batch_endpoint(
    files: list[UploadFile] = File(...),
    config: str = Form(...)
):
    # Save all files to {run_dir}/input/
    # Set data_root to input directory
    # Call run_batch() to process all files
```

**Process:**
1. Receives multiple files + config
2. Creates `{run_id}/input/` directory
3. Saves all CSV files there
4. Calls existing `run_batch()` with that directory
5. Returns standard `RunResult`

## 4. Files Modified

### Frontend (9 files)

1. **src/App.tsx**
   - Added sidebar layout
   - Dark theme background
   - Navigation component inline

2. **src/components/RunConfigForm.tsx**
   - Dark card background
   - Dark inputs with light text
   - Helper text in gray-500

3. **src/components/BandThresholdsEditor.tsx**
   - Dark table with ocean gradient header
   - Zebra striping in dark colors
   - Dark inputs

4. **src/components/DataSourceSelector.tsx**
   - Folder picker with webkitdirectory
   - File summary display
   - Dark theme styling
   - Changed signature: now returns `File[]` instead of `string | File`

5. **src/components/ProfileSetSelector.tsx**
   - Dark card and input styling
   - Dark select dropdown

6. **src/components/RunSummary.tsx**
   - Dark cards with gradient stats
   - Download button for Excel summary

7. **src/components/PlotGallery.tsx**
   - Dark plot cards
   - Dark modal with blur backdrop

8. **src/pages/RunPipelinePage.tsx**
   - Updated to handle File[] from DataSourceSelector
   - Calls `runUploadBatch()` for folder mode
   - Dark theme page layout

9. **src/pages/ConfigPage.tsx**
   - Dark theme styling
   - Updated messages and info boxes

10. **src/api/runsApi.ts**
    - Added `runUploadBatch()` function
    - Added `getSummaryUrl()` helper

### Backend (1 file)

11. **backend/app/routes/run.py**
    - Added `POST /run/upload-batch` endpoint
    - Added `GET /runs/{run_id}/summary` endpoint

## 5. API Changes

### New Endpoints

**1. POST /run/upload-batch**
- **Purpose:** Process multiple uploaded CSV files (folder upload)
- **Body:** `multipart/form-data`
  - `files`: Multiple CSV files
  - `config`: JSON string of RunConfig
- **Returns:** `RunResult`

**2. GET /runs/{run_id}/summary**
- **Purpose:** Download Excel summary file
- **Returns:** Excel file (`.xlsx`)
- **Filename:** `profile_summary_{run_id}.xlsx`

### Modified API Calls

**Frontend folder upload flow:**
```
User selects folder
  ↓
Frontend filters CSV files
  ↓
User clicks "Run Pipeline"
  ↓
POST /run/upload-batch with files + config
  ↓
Backend saves files to {run_id}/input/
  ↓
Backend calls run_batch() with input dir
  ↓
Pipeline processes all files
  ↓
Returns RunResult
```

**Frontend single file upload flow:**
```
User selects single CSV
  ↓
User clicks "Run Pipeline"
  ↓
POST /run/upload (existing endpoint)
  ↓
Backend processes single file
  ↓
Returns RunResult
```

## 6. Key Design Decisions

### Why webkitdirectory?
- Provides native folder picker UI
- Works in Chrome, Firefox, Edge
- Users don't need to know absolute paths
- More intuitive for non-technical users

### Why Upload Files Instead of Path?
- Browser security prevents reading local file system
- Can't directly access arbitrary paths from JS
- Upload is the only secure way to get folder contents

### Why Keep /run/batch Endpoint?
- Still useful for server-side folder processing
- API users can still use it
- Internal testing
- Not removed, just not used by UI

### Why Batch Upload Creates temp input directory?
- Pipeline expects a directory to scan
- Reuses existing `run_batch()` logic
- No need to refactor core pipeline
- Clean separation of concerns

## 7. Browser Compatibility

**webkitdirectory Support:**
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Edge
- ❌ Safari (limited)
- ❌ Mobile browsers

**Fallback for unsupported browsers:**
- User can still use "Upload CSV" for single files
- Could add detection and show warning message

## 8. Visual Comparison

### Before (Light Ocean)
```
┌─────────────── Zenin EEG ──────────────┐
│  [Run] [Profiles] [History] [Config]   │ ← Top tabs
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  White cards with blue accents          │
│  Light backgrounds                      │
│  Bright colors                          │
└─────────────────────────────────────────┘
```

### After (Dark Ocean)
```
┌─────┐ ┌───────────────────────────────┐
│ ⚡  │ │ Dark background               │
│Zenin│ │ with subtle gradients         │
│ EEG │ │                               │
├─────┤ │ ┌───────────────────────────┐ │
│▓Run │ │ │ Dark cards                │ │
│ Pro │ │ │ Ocean gradients           │ │
│ His │ │ │ Light text                │ │
│ Con │ │ └───────────────────────────┘ │
└─────┘ └───────────────────────────────┘
  ↑           ↑
Sidebar    Main content (centered)
```

## 9. Testing Checklist

### Visual Tests
- [ ] Sidebar displays correctly
- [ ] Active route is highlighted
- [ ] All text is readable
- [ ] Inputs are visible and focusable
- [ ] Buttons have clear hover states
- [ ] Gradients render smoothly
- [ ] Shadows are subtle

### Folder Upload Tests
- [ ] Folder picker opens (Chrome/Firefox/Edge)
- [ ] Only CSV files are counted
- [ ] File summary shows correctly
- [ ] Large folders work (100+ files)
- [ ] Upload progress is indicated
- [ ] Backend receives all files
- [ ] Pipeline processes all files
- [ ] Results display normally

### Excel Download Tests
- [ ] Download button appears after run
- [ ] Button only shows when summary exists
- [ ] Clicking downloads Excel file
- [ ] Filename includes run ID
- [ ] Excel content is correct

### Regression Tests
- [ ] Single file upload still works
- [ ] Profile sets page works
- [ ] Config changes work
- [ ] Plots display correctly
- [ ] All navigation works
- [ ] No console errors

## 10. Performance Considerations

**Large Folder Uploads:**
- Browser may take time to read all files
- Consider adding progress indicator
- May hit browser memory limits (1000+ files)
- Backend handles files sequentially

**Optimization Opportunities:**
1. Add upload progress bar
2. Compress files before upload
3. Stream processing on backend
4. Chunk large uploads

## 11. Next Steps (Optional Enhancements)

1. **Add ProfileSetsPage dark theme** (if needed)
2. **Add RunsHistoryPage dark theme** (if needed)
3. **Add upload progress indicator**
4. **Add browser compatibility warning**
5. **Add coral accent touches** (currently minimal)
6. **Add folder name display** (show selected folder name)

## 12. Summary of Major Changes

**Navigation:**
- ✅ Left sidebar with vertical menu
- ✅ Icon + label navigation items
- ✅ Gradient active indicator

**Theme:**
- ✅ Dark navy backgrounds
- ✅ Light text for contrast
- ✅ Ocean gradients (blue → teal)
- ✅ Subtle coral touches available
- ✅ All components themed consistently

**Folder Upload:**
- ✅ Native folder picker
- ✅ File count and size display
- ✅ CSV filtering
- ✅ New backend endpoint
- ✅ Batch upload processing

**Excel Download:**
- ✅ Download button in results
- ✅ Backend endpoint
- ✅ Proper MIME type
- ✅ Custom filename

**No Changes:**
- ✅ EEG processing logic
- ✅ Profile matching
- ✅ Metrics calculations
- ✅ Plot generation
- ✅ Existing endpoints still work
