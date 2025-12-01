# Band Thresholds Editor Implementation Summary

## Changes Made

Added a Band Thresholds editor component to both the Run Pipeline page and Config page, allowing users to configure threshold values for each brain wave band (Delta, Theta, Alpha, Beta, Gamma).

## Files Created

### 1. `frontend/src/components/BandThresholdsEditor.tsx` (NEW)

A reusable React component that displays a table for editing band thresholds.

**Features:**
- Table layout with 5 rows (one per band: Delta, Theta, Alpha, Beta, Gamma)
- 4 columns per row: Yüksek, Yüksek-Orta, Orta, Düşük-Orta
- Number inputs with step="0.1" for precise control
- Responsive design with hover effects
- Turkish labels for threshold levels

**Props:**
```typescript
interface BandThresholdsEditorProps {
  bandThresholds: Record<string, BandThresholds>;
  onChange: (bandThresholds: Record<string, BandThresholds>) => void;
}
```

**Structure:**
```typescript
const BANDS = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'];
const THRESHOLD_KEYS = ['yuksek', 'yuksek_orta', 'orta', 'dusuk_orta'];
const THRESHOLD_LABELS = {
  yuksek: 'Yüksek',
  yuksek_orta: 'Yüksek-Orta',
  orta: 'Orta',
  dusuk_orta: 'Düşük-Orta'
};
```

## Files Modified

### 2. `frontend/src/components/RunConfigForm.tsx`

**Changes:**
- Imported `BandThresholdsEditor` component
- Wrapped the existing form in a `<div className="space-y-6">` container
- Added `<BandThresholdsEditor>` below the pipeline configuration section
- Wired up `onChange` handler to update the `band_thresholds` field in `RunConfig`

**Before:**
```tsx
return (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <h2>Pipeline Configuration</h2>
    {/* fields */}
  </div>
);
```

**After:**
```tsx
return (
  <div className="space-y-6">
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2>Pipeline Configuration</h2>
      {/* fields */}
    </div>
    <BandThresholdsEditor
      bandThresholds={config.band_thresholds}
      onChange={(bandThresholds) => updateField('band_thresholds', bandThresholds)}
    />
  </div>
);
```

## Integration Points

### Run Pipeline Page (`frontend/src/pages/RunPipelinePage.tsx`)

**No changes needed** - The page already uses `RunConfigForm`, which now includes the band thresholds editor.

**Data Flow:**
1. Page loads → calls `getDefaultConfig()` from backend
2. Backend returns `RunConfig` with `band_thresholds` populated (default values)
3. `RunConfigForm` displays both pipeline config fields AND band thresholds table
4. User edits thresholds → `BandThresholdsEditor` calls `onChange` → updates `config` state
5. User clicks "Run Pipeline" → `runBatch()` or `runUpload()` sends full `config` including `band_thresholds`

### Config Page (`frontend/src/pages/ConfigPage.tsx`)

**No changes needed** - The page already uses `RunConfigForm`, which now includes the band thresholds editor.

**Data Flow:**
1. Page loads → calls `getDefaultConfig()` from backend
2. Backend returns default `RunConfig` with default `band_thresholds`
3. `RunConfigForm` displays both pipeline config fields AND band thresholds table
4. User can view/edit defaults (saving to backend is a future feature)

## Default Values

As specified, the backend returns these defaults:

```json
{
  "Delta":  { "yuksek": 85, "yuksek_orta": 75, "orta": 50, "dusuk_orta": 40 },
  "Theta":  { "yuksek": 70, "yuksek_orta": 60, "orta": 40, "dusuk_orta": 30 },
  "Alpha":  { "yuksek": 80, "yuksek_orta": 70, "orta": 50, "dusuk_orta": 40 },
  "Beta":   { "yuksek": 52, "yuksek_orta": 45, "orta": 30, "dusuk_orta": 22 },
  "Gamma":  { "yuksek": 34, "yuksek_orta": 27, "orta": 18, "dusuk_orta": 13 }
}
```

These are defined in `backend/app/core/configs.py` as `DEFAULT_BAND_THRESHOLDS`.

## TypeScript Types

**Already Correctly Defined** in `frontend/src/types/config.ts`:

```typescript
export interface BandThresholds {
  yuksek: number;
  yuksek_orta: number;
  orta: number;
  dusuk_orta: number;
}

export interface RunConfig {
  dominance_delta: number;
  balance_threshold: number;
  denge_mean_threshold: number;
  window_secs: number;
  window_samples: number;
  data_root: string | null;
  profile_set_id: string;
  band_thresholds: Record<string, BandThresholds>; // ✓ Already correct
}
```

## Backend Integration

**Already Correct** - No backend changes needed:

- `backend/app/models/config.py` already defines `BandThresholds` and `RunConfig` with `band_thresholds` field
- `backend/app/core/configs.py` already returns default band thresholds in `get_default_config()`
- `backend/app/routes/run.py` already accepts full `RunConfig` including `band_thresholds`
- `backend/app/core/engine.py` already converts `band_thresholds` and passes them to the pipeline

## API Request Example

When "Run Pipeline" is clicked, the frontend sends:

```
POST http://localhost:8000/run/batch
Content-Type: application/json

{
  "dominance_delta": 29.0,
  "balance_threshold": 22.0,
  "denge_mean_threshold": 46.0,
  "window_secs": 30,
  "window_samples": 5,
  "data_root": "/Users/umutkaya/Documents/Zenin Mind Reader/aile",
  "profile_set_id": "meditasyon",
  "band_thresholds": {
    "Delta": { "yuksek": 85, "yuksek_orta": 75, "orta": 50, "dusuk_orta": 40 },
    "Theta": { "yuksek": 70, "yuksek_orta": 60, "orta": 40, "dusuk_orta": 30 },
    "Alpha": { "yuksek": 80, "yuksek_orta": 70, "orta": 50, "dusuk_orta": 40 },
    "Beta": { "yuksek": 52, "yuksek_orta": 45, "orta": 30, "dusuk_orta": 22 },
    "Gamma": { "yuksek": 34, "yuksek_orta": 27, "orta": 18, "dusuk_orta": 13 }
  }
}
```

## UI Appearance

### Run Pipeline Page
```
┌─────────────────────────────────────────┐
│ Pipeline Configuration                   │
│ ┌─────────────┬─────────────┐           │
│ │ Dom. Delta  │ Balance Thr.│           │
│ └─────────────┴─────────────┘           │
│ ... other fields ...                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Band Thresholds                          │
│ Configure threshold values for each      │
│ brain wave band.                         │
│                                          │
│ ┌──────┬─────────┬────────┬──────┬─────┐│
│ │ Band │ Yüksek  │Yük-Orta│ Orta │Düş. ││
│ ├──────┼─────────┼────────┼──────┼─────┤│
│ │Delta │ [85]    │ [75]   │ [50] │[40] ││
│ │Theta │ [70]    │ [60]   │ [40] │[30] ││
│ │Alpha │ [80]    │ [70]   │ [50] │[40] ││
│ │Beta  │ [52]    │ [45]   │ [30] │[22] ││
│ │Gamma │ [34]    │ [27]   │ [18] │[13] ││
│ └──────┴─────────┴────────┴──────┴─────┘│
└─────────────────────────────────────────┘
```

### Config Page
Same layout as Run Pipeline page, showing default values.

## Testing Checklist

- [x] Created `BandThresholdsEditor.tsx` component
- [x] Updated `RunConfigForm.tsx` to include the editor
- [x] Verified TypeScript types are correct
- [x] Verified backend already returns `band_thresholds`
- [x] Verified backend already accepts `band_thresholds` in POST requests
- [ ] Test editing thresholds in Run Pipeline page
- [ ] Test editing thresholds in Config page
- [ ] Test that edited thresholds are sent in API request
- [ ] Verify no TypeScript errors
- [ ] Verify table renders correctly on both pages

## What Was NOT Changed

- ✅ Backend routes - already correct
- ✅ Backend models - already correct
- ✅ Backend engine - already handles band_thresholds
- ✅ TypeScript types - already correct
- ✅ Single CSV Path removal - completed in previous task
- ✅ Core EEG pipeline logic - unchanged
