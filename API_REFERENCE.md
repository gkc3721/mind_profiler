# API Endpoint Reference

## Base URL
`http://localhost:8000`

## Endpoints

### Configuration
- **GET** `/config/default`
  - Returns: `RunConfig` with default constants

### Profile Sets
- **GET** `/profiles`
  - Returns: List of `ProfileSetSummary`
- **GET** `/profiles/{id}`
  - Returns: Full `ProfileSet` with all profiles
- **POST** `/profiles`
  - Body: `ProfileSet`
  - Returns: Created `ProfileSet`
- **PUT** `/profiles/{id}`
  - Body: `ProfileSet`
  - Returns: Updated `ProfileSet`
- **DELETE** `/profiles/{id}`
  - Returns: `{status: "deleted"}`
  - Note: Cannot delete "meditasyon"

### Pipeline Execution
- **POST** `/run/batch`
  - Body: `RunConfig` with `data_root` set
  - Returns: `RunResult`
  - Purpose: Process all CSVs in folder
- **POST** `/run/single`
  - Body: `RunConfig` + `csv_path` field
  - Returns: `RunResult`
  - Purpose: Process one CSV by path
- **POST** `/run/upload`
  - Content-Type: multipart/form-data
  - Fields: `file` (CSV file), `config` (JSON string of RunConfig)
  - Returns: `RunResult`
  - Purpose: Process uploaded CSV

### Run History
- **GET** `/runs`
  - Returns: List of `RunSummary`
- **GET** `/runs/{run_id}`
  - Returns: Full `RunResult`
- **GET** `/runs/{run_id}/log`
  - Returns: CSV file (download)
- **GET** `/runs/{run_id}/plots`
  - Returns: `{plots: string[]}`
- **GET** `/runs/{run_id}/plots/{filename}`
  - Returns: PNG image file

## Frontend Integration

### API Client
All API calls use Axios client configured in `src/api/client.ts`:
```typescript
baseURL: 'http://localhost:8000'
```

### Example: Running Batch Pipeline

**Frontend call:**
```typescript
import { runBatch } from './api/runsApi';

const result = await runBatch({
  dominance_delta: 29.0,
  balance_threshold: 22.0,
  denge_mean_threshold: 46.0,
  window_secs: 30,
  window_samples: 5,
  data_root: '/Users/umutkaya/Documents/Zenin Mind Reader/aile',
  profile_set_id: 'meditasyon',
  band_thresholds: {...}
});
```

**Actual HTTP request:**
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
    "Delta": {"yuksek": 85, "yuksek_orta": 75, "orta": 50, "dusuk_orta": 40},
    "Theta": {...},
    ...
  }
}
```

**Backend response (success):**
```json
{
  "run_id": "20251130_143022",
  "timestamp": "2025-11-30T14:30:22.123456",
  "config": {...},
  "processed_files": 15,
  "matched_count": 12,
  "unmatched_count": 3,
  "log_file": "/path/to/runs/20251130_143022/processing_log.csv",
  "plots_dir": "/path/to/runs/20251130_143022/graphs",
  "summary_xlsx": "/path/to/runs/20251130_143022/profile_summary.xlsx"
}
```

**Backend response (error):**
```json
{
  "detail": "data_root must be provided for batch processing"
}
```
(HTTP status 500)

## Testing with curl

```bash
# Get default config
curl http://localhost:8000/config/default

# List profile sets
curl http://localhost:8000/profiles

# Run batch (requires config JSON)
curl -X POST http://localhost:8000/run/batch \
  -H "Content-Type: application/json" \
  -d '{
    "dominance_delta": 29.0,
    "balance_threshold": 22.0,
    "denge_mean_threshold": 46.0,
    "window_secs": 30,
    "window_samples": 5,
    "data_root": "/path/to/data",
    "profile_set_id": "meditasyon",
    "band_thresholds": {}
  }'
```
