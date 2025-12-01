# Quick Start Guide - Dark Theme UI + Folder Upload

## 🎨 What's New

### 1. Left Sidebar Navigation (was: Top Horizontal)
```
┌─────────────┐ ┌───────────────────────────────────┐
│   Zenin     │ │                                   │
│    EEG      │ │    Your content here              │
│             │ │                                   │
│ ▓ Run       │ │                                   │
│   Pipeline  │ │                                   │
│             │ │                                   │
│   Profile   │ │                                   │
│   Sets      │ │                                   │
│             │ │                                   │
│   History   │ │                                   │
│             │ │                                   │
│   Config    │ │                                   │
│             │ │                                   │
└─────────────┘ └───────────────────────────────────┘
```

### 2. Dark Ocean Theme (was: Light Ocean)

**Colors:**
- Background: Very dark navy (`#020617`)
- Cards: Dark slate (`#0F172A`, `#1E293B`)
- Text: Light gray/white
- Accent: Ocean gradient (Sky Blue → Teal)
- Highlights: Subtle coral touches

### 3. Folder Upload (was: Text Input)

**Before:**
```
Folder Path: [/Users/username/data/folder_______]
            [Use Folder Button]
```

**After:**
```
┌─────────────────────────────────────────────┐
│           📁                                │
│    Click to select folder                   │
│    All CSV files will be uploaded           │
└─────────────────────────────────────────────┘

╔═══════════════════════════════════════════╗
║ ✓ 15 CSV files selected                   ║
║   Total size: 2.3 MB                       ║
║                                            ║
║   • subject_001.csv                        ║
║   • subject_002.csv                        ║
║   • subject_003.csv                        ║
║   • subject_004.csv                        ║
║   • subject_005.csv                        ║
║   ...and 10 more files                     ║
╚═══════════════════════════════════════════╝

     [Use Folder (15 files) Button]
```

## 🚀 How to Use Folder Upload

### Step 1: Navigate to Run Pipeline
Click "Run Pipeline" in the left sidebar.

### Step 2: Configure Settings
Set your threshold values and select a profile set.

### Step 3: Select Folder
1. Under "Data Source", ensure "Process Folder" tab is active
2. Click the large dashed box that says "Click to select folder"
3. Your OS file picker will open
4. Navigate to and select your EEG data folder
5. Click "Select" or "Open" in the file picker

### Step 4: Verify Selection
You'll see a summary box appear showing:
- Number of CSV files found
- Total size
- List of first few files

### Step 5: Run Pipeline
1. Click "Run Pipeline" button at the bottom
2. Wait for processing (spinner will show)
3. Results, plots, and Excel summary will appear

## 📊 Download Excel Summary

After a successful run:
1. Look for the "Download Excel" button in the "Run Results" section
2. Click to download `profile_summary_{run_id}.xlsx`
3. Open in Excel/LibreOffice/Numbers

## 🎨 Color Reference

### Background Shades
```css
bg-slate-950   /* Main page background */
bg-slate-900   /* Sidebar, cards */
bg-slate-800   /* Inputs, hover states */
bg-slate-700   /* Borders */
```

### Text Colors
```css
text-gray-100  /* Headings */
text-gray-300  /* Body text */
text-gray-400  /* Labels */
text-gray-500  /* Helper text */
```

### Accent Gradients
```css
/* Primary Actions */
from-sky-600 to-teal-500

/* Success States */
from-teal-900/40 to-teal-800/30
text-teal-400, border-teal-700

/* Warning States */
from-amber-900/40 to-amber-800/30
text-amber-400, border-amber-700

/* Error States */
from-rose-900/30 to-rose-800/20
text-rose-400, border-rose-700
```

## 🔧 Technical Details

### Frontend Changes
- **Navigation:** Sidebar component in `App.tsx`
- **Data Source:** `DataSourceSelector.tsx` now uses `<input webkitdirectory>`
- **Theme:** All components use dark Tailwind classes
- **API:** New `runUploadBatch()` function

### Backend Changes
- **New Endpoint:** `POST /run/upload-batch`
- **Accepts:** Multiple files + config
- **Process:** Saves to temp dir, runs batch processing

### Browser Support
- ✅ Chrome
- ✅ Firefox
- ✅ Edge
- ⚠️ Safari (limited folder upload support)
- ❌ Mobile browsers

## 📝 Component Status

| Component | Dark Theme | Folder Upload | Status |
|-----------|-----------|---------------|--------|
| App.tsx | ✅ | N/A | ✅ Complete |
| RunConfigForm | ✅ | N/A | ✅ Complete |
| BandThresholdsEditor | ✅ | N/A | ✅ Complete |
| DataSourceSelector | ✅ | ✅ | ✅ Complete |
| ProfileSetSelector | ✅ | N/A | ✅ Complete |
| RunSummary | ✅ | N/A | ✅ Complete |
| PlotGallery | ✅ | N/A | ✅ Complete |
| RunPipelinePage | ✅ | ✅ | ✅ Complete |
| ConfigPage | ✅ | N/A | ✅ Complete |
| ProfileSetsPage | ⚠️ | N/A | Optional |
| RunsHistoryPage | ⚠️ | N/A | Optional |

## 🐛 Troubleshooting

### Folder Picker Doesn't Open
- **Issue:** Using Safari or unsupported browser
- **Fix:** Switch to Chrome, Firefox, or Edge

### No CSV Files Found
- **Issue:** Selected folder doesn't contain CSV files
- **Fix:** Ensure folder has `.csv` files

### Upload Fails
- **Issue:** Files too large or network error
- **Fix:** Try smaller batch or check backend logs

### Dark Theme Hard to Read
- **Issue:** Monitor brightness/contrast settings
- **Fix:** Adjust display settings or consider light theme variant

## 📦 Files You May Want to Customize

### To adjust colors:
- `frontend/src/App.tsx` (sidebar colors)
- `frontend/src/components/*.tsx` (individual components)

### To change folder upload behavior:
- `frontend/src/components/DataSourceSelector.tsx` (UI)
- `frontend/src/api/runsApi.ts` (API call)
- `backend/app/routes/run.py` (endpoint)

### To modify layout:
- `frontend/src/App.tsx` (sidebar width, main content max-width)

## ✅ What Hasn't Changed

- EEG processing algorithms
- Profile matching logic
- Metrics calculations
- Plot generation
- Existing API endpoints
- Database structure
- File storage format

All core business logic remains identical!
