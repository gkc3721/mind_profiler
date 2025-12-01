# Quick Test - Profile Summary Viewer

## ✅ What Was Added

**Feature:** View Excel summary directly in the browser as an interactive table

**Before:** Only download button → open Excel manually  
**After:** View inline table + download button

---

## How to Test (1 minute)

### Step 1: Servers Should Auto-Reload ✅

Both backend and frontend should reload automatically.

**Check backend terminal:**
```
INFO:     Application startup complete.
```

**Check frontend terminal:**
```
✓ built in XXXms
```

### Step 2: Run a Pipeline

1. Open http://localhost:5173
2. Select data and run pipeline
3. Wait for completion

### Step 3: Look for Profile Summary Card ✅

After the run completes, you should see **three cards** in this order:

```
1. Run Results Card
   ├─ Processed Files: 379
   ├─ Matched: 350
   └─ Unmatched: 29

2. Profile Summary Card ← NEW!
   ├─ Header: "Profile Summary" + "Download Excel" button
   ├─ Sheet tabs: [Toplam] [Event1] [Event2] ...
   ├─ Data table with columns and rows
   └─ Row count at bottom

3. Plots Gallery
   └─ Grid of plot images
```

### Step 4: Test Sheet Navigation

1. **Click different sheet tabs** (Toplam, Dominance, Band Stats, etc.)
2. **Table content should update** for each sheet
3. **Active tab has gradient background**

### Step 5: Test Download

1. **Click "Download Excel" button** (top-right of Profile Summary card)
2. **File should download:** `profile_summary_{run_id}.xlsx`
3. **Open in Excel** to verify all sheets are present

---

## Success Indicators

### Visual Checks ✅

**Profile Summary Card should have:**
- ✅ Emerald icon (📊) in header
- ✅ "Profile Summary" title
- ✅ "View analysis results by sheet" subtitle
- ✅ "Download Excel" button (gradient: emerald → teal)
- ✅ Sheet tabs below header (gradient for active)
- ✅ Data table with ocean gradient header
- ✅ Zebra striping (alternating row colors)
- ✅ Row count at bottom (e.g., "42 rows")

### Functional Checks ✅

- ✅ Table displays real data (not loading spinner)
- ✅ Clicking tabs changes table content
- ✅ Download button works
- ✅ No console errors (F12 → Console)

---

## Troubleshooting

### Issue: Profile Summary Card Doesn't Appear

**Check 1: Console for errors**
- Open DevTools (F12) → Console tab
- Look for red error messages

**Check 2: Backend console**
- Look for "⚠️ Summary file not created"
- If present, the Excel file wasn't generated

**Check 3: summary_xlsx field**
- In DevTools → Network tab
- Find POST request to `/run/upload-batch`
- Check response: `summary_xlsx` should not be null

**Solution:**
- If `summary_xlsx` is null, the summary generation failed
- Check backend console for errors during summary creation

### Issue: Shows Loading Spinner Forever

**Cause:** API call failed or is hanging

**Check:**
- DevTools → Network tab
- Look for GET request to `/runs/{run_id}/summary`
- Check if it's red (failed) or pending (hanging)

**If failed (404):**
- Summary file doesn't exist on disk
- Check backend console for warnings

**If failed (500):**
- Error reading Excel file
- Check backend console for full error traceback

**Solution:**
```bash
# Manually check if summary file exists
cd backend/app/data/runs/{run_id}
ls -la profile_summary*.xlsx
```

### Issue: Shows "Could not load summary" Error

**This is correct behavior** if:
- Summary file is missing
- Backend is down
- Network error

**Not expected** if:
- Pipeline just completed successfully
- Backend console shows "Profile summary created"

**Solution:**
- Check if file exists (see above)
- Restart backend if needed
- Check for CORS errors in browser console

### Issue: Table is Empty

**Check:**
- Which sheet is active?
- Some sheets may have no data

**Try:**
- Click "Toplam" tab (should always have data)
- If still empty, the Excel file might be corrupt or empty

---

## Expected Output

### Backend Console (After Run)

```
✅ Profile summary created: .../profile_summary20251201_123456.xlsx

🔍 DEBUG - Run completed:
  Run ID: 20251201_123456
  Summary file: .../profile_summary20251201_123456.xlsx
```

### Frontend Display

```
┌─────────────────────────────────────────────────┐
│ 📊 Profile Summary          [Download Excel]   │
│    View analysis results by sheet               │
├─────────────────────────────────────────────────┤
│ [Toplam] [Event1] [Dominance] [Band Stats]     │ ← Tabs
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ Profile    │ 5 Uyumlu │ 4 Uyumlu │ Toplam │ │ ← Header
│ ├────────────┼──────────┼──────────┼────────┤ │
│ │ YARATICI.. │   120    │    45    │   165  │ │
│ │ STRATEJIST │    98    │    32    │   130  │ │
│ │ ...        │   ...    │   ...    │   ...  │ │
│ └─────────────────────────────────────────────┘ │
│                                        25 rows    │
└─────────────────────────────────────────────────┘
```

---

## API Verification

### Test Endpoint Manually

```bash
# Get run_id from a successful run
RUN_ID="20251201_123456"

# Test JSON endpoint
curl http://localhost:8000/runs/$RUN_ID/summary | jq .

# Expected output: JSON with sheets data

# Test download endpoint
curl -o test.xlsx http://localhost:8000/runs/$RUN_ID/summary/download

# Expected output: Excel file downloaded as test.xlsx
```

---

## Quick Checklist

After running a pipeline:

1. [ ] Run Results card appears
2. [ ] Profile Summary card appears below it
3. [ ] Table shows data (not loading)
4. [ ] Multiple sheet tabs visible
5. [ ] Clicking tabs changes table content
6. [ ] Active tab has gradient background
7. [ ] Table header has ocean gradient
8. [ ] Rows have zebra striping
9. [ ] Row count shows at bottom
10. [ ] Download button works
11. [ ] Downloaded Excel file opens correctly
12. [ ] Plots gallery appears below

---

## Summary

**Feature:** View profile summary as interactive table in browser

**Key files:**
- Backend: `backend/app/routes/run.py` (2 new endpoints)
- Frontend: `frontend/src/components/ProfileSummaryViewer.tsx` (new component)

**Testing:** Run pipeline → see table → click tabs → download Excel ✅

If all checks pass, the feature is working perfectly! 🎉
