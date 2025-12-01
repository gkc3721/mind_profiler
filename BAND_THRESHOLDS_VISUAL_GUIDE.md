# Band Thresholds Editor - Visual Guide

## What You Should See

### Run Pipeline Page

When you navigate to the "Run Pipeline" page, you will now see:

1. **Pipeline Configuration** section (existing - with 5 fields)
2. **NEW: Band Thresholds** section (table with 5 rows × 4 columns)
3. Profile Set selector
4. Data Source selector
5. Run Pipeline button

### Config Page

When you navigate to the "Config" page, you will see the same sections:

1. **Pipeline Configuration** section
2. **NEW: Band Thresholds** section

## Band Thresholds Table

The table has:
- **5 rows** (one per brain wave band)
- **4 columns** (one per threshold level)

```
┌──────────┬──────────┬──────────────┬──────────┬──────────────┐
│   Band   │  Yüksek  │ Yüksek-Orta  │   Orta   │  Düşük-Orta  │
├──────────┼──────────┼──────────────┼──────────┼──────────────┤
│  Delta   │  [  85 ] │   [  75 ]    │ [  50 ]  │   [  40 ]    │
├──────────┼──────────┼──────────────┼──────────┼──────────────┤
│  Theta   │  [  70 ] │   [  60 ]    │ [  40 ]  │   [  30 ]    │
├──────────┼──────────┼──────────────┼──────────┼──────────────┤
│  Alpha   │  [  80 ] │   [  70 ]    │ [  50 ]  │   [  40 ]    │
├──────────┼──────────┼──────────────┼──────────┼──────────────┤
│  Beta    │  [  52 ] │   [  45 ]    │ [  30 ]  │   [  22 ]    │
├──────────┼──────────┼──────────────┼──────────┼──────────────┤
│  Gamma   │  [  34 ] │   [  27 ]    │ [  18 ]  │   [  13 ]    │
└──────────┴──────────┴──────────────┴──────────┴──────────────┘
```

Each `[ number ]` is an editable input field.

## How to Use

### Editing Thresholds

1. Click on any number input field
2. Type a new value (decimals allowed, e.g., 85.5)
3. The value updates immediately in the state
4. When you click "Run Pipeline", the edited values are sent to the backend

### Example: Changing Delta Yüksek Threshold

1. Find the "Delta" row
2. Find the "Yüksek" column
3. Click the input (currently showing 85)
4. Type 90
5. The new value is now stored in the config

### Testing the Integration

1. **Open Browser DevTools** (F12)
2. **Go to Run Pipeline page**
3. **Edit a threshold** (e.g., change Delta > Yüksek from 85 to 90)
4. **Click "Run Pipeline"**
5. **Check Console** - you should see:
   ```
   Running pipeline with config: {
     type: 'folder',
     value: '/path/to/folder',
     config: {
       dominance_delta: 29,
       balance_threshold: 22,
       ...
       band_thresholds: {
         Delta: { yuksek: 90, yuksek_orta: 75, ... },  ← Your edited value!
         Theta: { ... },
         ...
       }
     }
   }
   ```

6. **Check Network tab** - the POST request body should include your edited thresholds

## What Changed vs. Default

### Before (Single CSV Path Visible)
```
Run Pipeline Page:
- Pipeline Configuration
- Profile Set Selector
- Data Source (3 tabs: Folder / Single CSV Path / Upload)  ← Had 3 tabs
- Run Button
```

### After (Band Thresholds Added, Single CSV Removed)
```
Run Pipeline Page:
- Pipeline Configuration
- Band Thresholds (NEW!)  ← Added!
- Profile Set Selector
- Data Source (2 tabs: Folder / Upload)  ← Now only 2 tabs!
- Run Button
```

## Default Values Reference

Band | Yüksek | Yüksek-Orta | Orta | Düşük-Orta
-----|--------|-------------|------|------------
Delta | 85 | 75 | 50 | 40
Theta | 70 | 60 | 40 | 30
Alpha | 80 | 70 | 50 | 40
Beta | 52 | 45 | 30 | 22
Gamma | 34 | 27 | 18 | 13

## Keyboard Shortcuts (Standard HTML Input)

- **Tab** - Move to next field
- **Shift+Tab** - Move to previous field
- **Arrow Up** - Increment value
- **Arrow Down** - Decrement value
- **Enter** - Confirm and move to next (browser default)

## Styling

- **Table borders** - Gray borders around cells
- **Header row** - Light gray background
- **Hover effect** - Light gray background when hovering over a row
- **Focus ring** - Blue ring around input when focused
- **Font** - Band names in medium weight, numbers centered

## Troubleshooting

### If thresholds don't appear:

1. Check browser console for errors
2. Verify `getDefaultConfig()` is returning `band_thresholds` field
3. Check Network tab - GET /config/default should return band_thresholds
4. Try hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### If edited values don't persist across tabs:

This is **expected behavior**. The Run Pipeline page and Config page load their own copies of the config. Edits in one page don't affect the other (unless backend persistence is implemented).

### If backend doesn't receive edited values:

1. Check browser console for the "Running pipeline with config" log
2. Verify the log shows your edited values in `config.band_thresholds`
3. Check Network tab - POST /run/batch request body should include band_thresholds
4. If not, there may be a state update issue - report this
