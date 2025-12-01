# Quick Test Guide - Profile Summary Fix

## 🧪 Testing the Fix

### Test 1: Verify Backend Auto-Reload

The backend should auto-reload with the changes. Check your terminal running uvicorn:

```
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [xxxxx]
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

If you don't see this, restart the backend manually:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Test 2: Run the Pipeline

1. Open http://localhost:5173
2. Go to "Run Pipeline"
3. Select a folder with CSV files (your "sample data" folder with 379 files)
4. Click "Run Pipeline"

### Test 3: Watch Backend Console

While the pipeline runs, watch for these messages:

```
✅ Generating profile summary from log: /path/to/runs/20251201_XXXXXX/processing_log20251201_XXXXXX.csv
Log dosyası: /path/to/runs/20251201_XXXXXX/processing_log20251201_XXXXXX.csv
... (progress output) ...
Özet Excel kaydedildi: /path/to/runs/20251201_XXXXXX/profile_summary20251201_XXXXXX.xlsx
✅ Profile summary created: /path/to/runs/20251201_XXXXXX/profile_summary20251201_XXXXXX.xlsx
```

### Test 4: Check File System

After the run completes, verify the file exists:

```bash
cd backend/app/data/runs
ls -la  # Find the latest run directory (e.g., 20251201_XXXXXX)
cd 20251201_XXXXXX
ls -la  # You should see profile_summary20251201_XXXXXX.xlsx
```

### Test 5: Check UI

In the browser, after the run completes:

1. **Look for the "Download Excel" button** in the "Run Results" section
2. It should appear next to the stats (Files/Matched/Unmatched)
3. The button should have a download icon and say "Download Excel"

### Test 6: Download the File

1. Click the "Download Excel" button
2. Your browser should download `profile_summary_20251201_XXXXXX.xlsx`
3. Open the file in Excel/LibreOffice
4. Verify it has multiple sheets:
   - Toplam (Total summary)
   - Individual event summaries
   - Dominance summary
   - Band statistics

## ✅ Success Criteria

**Backend:**
- ✅ No errors in console
- ✅ See "✅ Profile summary created" message
- ✅ Excel file exists in run directory

**Frontend:**
- ✅ "Download Excel" button appears after run
- ✅ Button is visible and clickable
- ✅ Clicking button downloads the file

**Downloaded File:**
- ✅ File name: `profile_summary_{run_id}.xlsx`
- ✅ File opens in Excel/LibreOffice
- ✅ Contains multiple sheets with profile data
- ✅ Toplam sheet has Profile, 5 Uyumlu, 4 Uyumlu, Toplam, Yüzde columns
- ✅ Data looks correct (matches your processing log)

## 🐛 Troubleshooting

### Issue: "Download Excel" button doesn't appear

**Check:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for JavaScript errors
4. Check Network tab for the `/run/upload-batch` response
5. Verify that `summary_xlsx` field is not null in the response

**Fix:**
- If `summary_xlsx` is null, check backend console for error messages
- Backend should show either success or error when generating summary

### Issue: Backend says "⚠️ Log file not found"

**Cause:** The processing log wasn't created by the pipeline

**Fix:**
1. Check if `zenin_mac2.process_pipeline()` completed successfully
2. Verify the run directory exists: `backend/app/data/runs/{run_id}/`
3. Check if `processing_log{run_id}.csv` exists in that directory
4. If not, there's an issue with the main pipeline (not our fix)

### Issue: Backend says "⚠️ Profile summary generation failed"

**Cause:** Exception when calling `analyze_processing_log.main()`

**Check backend console for full traceback:**
```
⚠️ Error generating profile summary: [error details]
Traceback (most recent call last):
  ...
```

**Common causes:**
1. Missing pandas/openpyxl dependency: `pip install pandas openpyxl`
2. Corrupt or empty processing log
3. Wrong column names in log

**Fix:**
1. Install missing dependencies: `cd backend && pip install -r requirements.txt`
2. Check the processing log manually to ensure it has data
3. Verify column names match what `analyze_processing_log.py` expects

### Issue: Download button appears but clicking returns 404

**Cause:** File exists in memory but not on disk, or wrong filename

**Check:**
```bash
cd backend/app/data/runs/{run_id}
ls -la profile*
```

**Fix:**
- If file doesn't exist, there's an issue with summary generation
- If filename is different, the endpoint will try fallback names
- Check backend logs when clicking download button

### Issue: Downloaded file is corrupt or won't open

**Cause:** Incomplete file write or transfer issue

**Fix:**
1. Check file size: `ls -lh backend/app/data/runs/{run_id}/profile_summary*.xlsx`
2. If file size is 0 or very small, regeneration failed
3. Try opening directly from the run directory to verify it's valid
4. If valid locally but corrupted when downloaded, it's a transfer issue

## 📊 Expected Output Format

The downloaded Excel should look like:

**Sheet 1: Toplam**
```
| Profile          | 5 Uyumlu | 4 Uyumlu | Toplam | Yüzde |
|------------------|----------|----------|--------|-------|
| YARATICI LIDER   | 120      | 45       | 165    | 15.5  |
| STRATEJIST       | 98       | 32       | 130    | 12.2  |
| ...              | ...      | ...      | ...    | ...   |
```

**Sheet 2-N: Individual Events**
(Same format as Toplam, but for each event separately)

**Sheet: Dominance**
```
| Profile          | Baskın Yüksek | Baskın Düşük | Normal |
|------------------|---------------|--------------|--------|
| YARATICI LIDER   | 45            | 12           | 108    |
| ...              | ...           | ...          | ...    |
```

**Sheet: Band Stats**
```
| Profile          | Delta Mean | Theta Mean | Alpha Mean | ... |
|------------------|------------|------------|------------|-----|
| YARATICI LIDER   | 65.3       | 45.2       | 72.1       | ... |
| ...              | ...        | ...        | ...        | ... |
```

## 🎯 Quick Verification

**One-liner to check if everything worked:**
```bash
# Replace {run_id} with your actual run ID
ls -lh backend/app/data/runs/{run_id}/profile_summary*.xlsx && echo "✅ Summary file exists!"
```

**Check backend logs for the exact file path:**
```bash
# In the terminal running uvicorn, look for:
"✅ Profile summary created: /full/path/to/file.xlsx"
```

## 💡 Tips

1. **Keep backend console visible** during testing to catch issues immediately
2. **Use browser DevTools** to inspect API responses
3. **Check file system** directly if UI doesn't show button
4. **Don't close tabs** - errors might only appear in console
5. **Test with small dataset first** (few CSVs) for faster iteration

## ✨ Success!

If all tests pass:
- ✅ Pipeline runs successfully
- ✅ Backend generates summary
- ✅ UI shows download button
- ✅ Excel file downloads and opens
- ✅ Data looks correct

**You're done!** The profile summary feature is now fully working. 🎉
