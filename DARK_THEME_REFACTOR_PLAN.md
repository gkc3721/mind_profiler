# Dark Ocean Theme + Folder Upload Refactor - Implementation Plan

## Summary of Changes

This document outlines the comprehensive UI/UX refactor with:
1. **Left sidebar navigation** (instead of top horizontal)
2. **Dark ocean theme** with coral accents
3. **Folder upload** functionality (select folder from computer)

## 1. App Layout & Sidebar (✅ DONE)

**File:** `frontend/src/App.tsx`

**Changes:**
- Added left sidebar with vertical navigation
- Dark theme: `bg-slate-950` (main), `bg-slate-900` (sidebar)
- Active route: Ocean gradient with shadow
- Logo at top with subtitle
- Footer with version info
- Main content area: `max-w-5xl mx-auto`

## 2. Component Theme Updates (IN PROGRESS)

### Components to Update with Dark Theme

All components need these color changes:

**Background Colors:**
- Cards: `bg-slate-900` with `border-slate-800`
- Inputs: `bg-slate-800` with `border-slate-700`
- Tables: `bg-slate-900` header, `bg-slate-800/50` rows

**Text Colors:**
- Headings: `text-gray-100`
- Body text: `text-gray-300`
- Muted text: `text-gray-400` / `text-gray-500`
- Labels: `text-gray-400`

**Accent Colors:**
- Primary gradient: `from-sky-600 to-teal-500`
- Focus rings: `focus:ring-sky-500`
- Coral accents: `text-rose-400` / `bg-rose-500` for highlights

**Components List:**
1. ✅ RunConfigForm.tsx
2. ⏳ BandThresholdsEditor.tsx
3. ⏳ DataSourceSelector.tsx (+ folder upload!)
4. ⏳ ProfileSetSelector.tsx
5. ⏳ RunSummary.tsx
6. ⏳ PlotGallery.tsx
7. ⏳ RunPipelinePage.tsx
8. ⏳ ConfigPage.tsx
9. ⏳ ProfileSetsPage.tsx
10. ⏳ RunsHistoryPage.tsx

## 3. Folder Upload Feature

### Frontend Changes

**File:** `frontend/src/components/DataSourceSelector.tsx`

**Current "Process Folder" mode:**
- Text input for folder path
- User types absolute path

**New "Process Folder" mode:**
- Button: "Select Folder"
- Uses `<input type="file" webkitdirectory multiple />`
- Shows summary after selection:
  - Number of CSV files
  - Total size
  - List of filenames (first 5 + "...X more")

**Implementation:**
```tsx
const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
  const files = e.target.files;
  if (files) {
    // Filter to only CSV files
    const csvFiles = Array.from(files).filter(f => f.name.endsWith('.csv'));
    setSelectedFiles(files);
    // Show summary
  }
};

<input 
  type="file" 
  webkitdirectory="true"
  multiple
  onChange={handleFolderSelect}
  className="hidden"
  id="folder-input"
/>
<label htmlFor="folder-input">
  <button type="button">Select Folder</button>
</label>
```

**API Call:**
When user clicks "Run Pipeline":
- Create FormData
- Append all CSV files
- Append config as JSON string
- POST to `/run/upload-batch`

### Backend Changes

**File:** `backend/app/routes/run.py`

**New Endpoint:**
```python
@router.post("/run/upload-batch", response_model=RunResult)
async def run_upload_batch_endpoint(
    files: list[UploadFile] = File(...),
    config: str = Form(...)
):
    """Run pipeline on multiple uploaded CSV files (folder upload)"""
    config_obj = RunConfig.parse_raw(config)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all uploaded files
    for file in files:
        if file.filename.endswith('.csv'):
            file_path = input_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
    
    # Call run_batch with input_dir as data_root
    # This reuses existing batch processing logic
    return run_batch(RunConfig(**{...config_obj.dict(), "data_root": str(input_dir)}))
```

**Integration with Engine:**
- The new endpoint saves files to `{run_dir}/input/`
- Then calls `run_batch()` with that directory as `data_root`
- All existing pipeline logic works unchanged

## 4. Dark Theme Color Reference

### Background Palette
```
bg-slate-950  # Main background (#020617)
bg-slate-900  # Cards, sidebar (#0F172A)
bg-slate-800  # Inputs, hover states (#1E293B)
bg-slate-700  # Borders on inputs (#334155)
```

### Text Palette
```
text-gray-100  # Headings (#F3F4F6)
text-gray-300  # Body text (#D1D5DB)
text-gray-400  # Labels, muted (#9CA3AF)
text-gray-500  # Helper text (#6B7280)
text-gray-600  # Footer, very muted (#4B5563)
```

### Accent Palette
```
# Ocean Gradient (Primary)
from-sky-600 to-teal-500
from-sky-500 to-teal-400

# Coral Accents (Highlights)
text-rose-400 (#FB7185)
bg-rose-500/10 (subtle backgrounds)
border-rose-500 (for emphasis)
```

### State Colors
```
# Success
bg-teal-900/50, text-teal-400, border-teal-700

# Warning
bg-amber-900/50, text-amber-400, border-amber-700

# Error
bg-rose-900/50, text-rose-400, border-rose-700

# Info
bg-sky-900/50, text-sky-400, border-sky-700
```

## 5. Implementation Priority

### Phase 1: Core Components (Essential for usability)
1. ✅ App.tsx (sidebar + dark background)
2. ✅ RunConfigForm.tsx
3. BandThresholdsEditor.tsx
4. DataSourceSelector.tsx (with folder upload)
5. ProfileSetSelector.tsx

### Phase 2: Results & Display
6. RunSummary.tsx
7. PlotGallery.tsx

### Phase 3: Pages
8. RunPipelinePage.tsx (page header, messages)
9. ConfigPage.tsx

### Phase 4: Advanced Features
10. ProfileSetsPage.tsx (table styling)
11. RunsHistoryPage.tsx (table + modal)

### Phase 5: Backend
12. New `/run/upload-batch` endpoint
13. Integration testing

## 6. Testing Checklist

### Visual Tests
- [ ] Sidebar navigation works on all pages
- [ ] Active route is highlighted correctly
- [ ] Dark theme is consistent across all components
- [ ] Text is readable (good contrast)
- [ ] Inputs are visible and focusable
- [ ] Buttons have clear hover states
- [ ] Coral accents are subtle but visible

### Folder Upload Tests
- [ ] Folder selection opens native file picker
- [ ] Only CSV files are processed
- [ ] File summary shows correct info
- [ ] Upload progress is indicated
- [ ] Large folders (100+ files) work
- [ ] Backend receives all files correctly
- [ ] Pipeline processes files as batch
- [ ] Results are displayed normally

### Regression Tests
- [ ] Single file upload still works
- [ ] Profile sets page still works
- [ ] Config changes are saved
- [ ] Plots display correctly
- [ ] Excel download works
- [ ] All existing features intact

## 7. Known Limitations

**Folder Upload:**
- Browser security prevents reading absolute paths
- User must select folder every time (can't remember location)
- Works in Chrome, Firefox, Edge (not Safari)
- Mobile browsers may not support webkitdirectory

**Workaround for Safari:**
- Show message: "Folder upload not supported in this browser. Please use Chrome, Firefox, or Edge."
- Fallback to single file upload mode

## 8. Code Example: Folder Upload Component

```tsx
// DataSourceSelector.tsx excerpt
const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  if (e.target.files) {
    const csvFiles = Array.from(e.target.files).filter(f => 
      f.name.toLowerCase().endsWith('.csv')
    );
    setSelectedFiles(csvFiles);
  }
};

const totalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);
const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};

return (
  <div className="space-y-4">
    <input
      type="file"
      webkitdirectory="true"
      multiple
      onChange={handleFolderChange}
      className="hidden"
      id="folder-upload"
    />
    <label
      htmlFor="folder-upload"
      className="block w-full px-4 py-3 bg-slate-800 border-2 border-dashed border-slate-600 rounded-xl text-center cursor-pointer hover:border-sky-500 hover:bg-slate-700 transition-all"
    >
      <svg className="w-8 h-8 mx-auto mb-2 text-gray-400" />
      <p className="text-sm font-medium text-gray-300">Click to select folder</p>
      <p className="text-xs text-gray-500 mt-1">All CSV files will be processed</p>
    </label>
    
    {selectedFiles.length > 0 && (
      <div className="p-4 bg-teal-900/20 border border-teal-700 rounded-xl">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-teal-400" />
          <span className="font-medium text-teal-400">
            {selectedFiles.length} CSV files selected
          </span>
        </div>
        <p className="text-sm text-gray-400">Total size: {formatSize(totalSize)}</p>
        <div className="mt-2 text-xs text-gray-500">
          {selectedFiles.slice(0, 3).map(f => f.name).join(', ')}
          {selectedFiles.length > 3 && ` ...and ${selectedFiles.length - 3} more`}
        </div>
      </div>
    )}
  </div>
);
```

## 9. Next Steps

1. Complete component theme updates (BandThresholdsEditor next)
2. Implement folder upload in DataSourceSelector
3. Create backend `/run/upload-batch` endpoint
4. Test integration end-to-end
5. Update documentation

## 10. Files Modified Summary

**Frontend:**
- ✅ src/App.tsx
- ✅ src/components/RunConfigForm.tsx
- ⏳ src/components/BandThresholdsEditor.tsx
- ⏳ src/components/DataSourceSelector.tsx
- ⏳ src/components/ProfileSetSelector.tsx
- ⏳ src/components/RunSummary.tsx
- ⏳ src/components/PlotGallery.tsx
- ⏳ src/pages/RunPipelinePage.tsx
- ⏳ src/pages/ConfigPage.tsx
- ⏳ src/pages/ProfileSetsPage.tsx (optional)
- ⏳ src/pages/RunsHistoryPage.tsx (optional)
- ⏳ src/api/runsApi.ts (add runUploadBatch)

**Backend:**
- ⏳ backend/app/routes/run.py (add upload-batch endpoint)

**No Changes:**
- All EEG business logic
- Analytics, profile matching, metrics
- Existing endpoints remain unchanged
