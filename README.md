# Zenin EEG Pipeline - Full-Stack Application

A configurable web application for running EEG analysis pipelines with customizable constants, profile sets, and data sources.

## Architecture

- **Backend**: FastAPI (Python) - Wraps existing EEG analysis pipeline
- **Frontend**: React + TypeScript + Vite - Modern UI for configuration and results

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. The backend will automatically initialize the default profile set (`meditasyon`) from `Zihin_Profilleri_29.csv` on first startup.

3. Start the FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Features

### 1. Run Pipeline Page
- Configure constants (dominance_delta, balance_threshold, window_secs, etc.)
- Select profile set
- Choose data source:
  - Process entire folder
  - Process single CSV by path
  - Upload CSV file
- View results and plots

### 2. Profile Sets Page
- View and edit existing profile sets
- Create new profile sets
- Duplicate profile sets
- Delete profile sets (except default "meditasyon")
- Edit wave levels (yüksek, yüksek orta, orta, düşük orta, düşük)

### 3. Runs History Page
- View all past pipeline runs
- Click on a run to see details
- View plots and download logs
- Download summary Excel files

### 4. Config Page
- View default configuration constants
- (Future: Save defaults to backend)

## API Endpoints

### Config
- `GET /config/default` - Get default configuration

### Profiles
- `GET /profiles` - List all profile sets
- `GET /profiles/{id}` - Get specific profile set
- `POST /profiles` - Create new profile set
- `PUT /profiles/{id}` - Update profile set
- `DELETE /profiles/{id}` - Delete profile set

### Runs
- `POST /run/batch` - Run pipeline on folder
- `POST /run/single` - Run pipeline on single CSV
- `POST /run/upload` - Run pipeline on uploaded file
- `GET /runs` - List all runs
- `GET /runs/{id}` - Get run details
- `GET /runs/{id}/log` - Download log CSV
- `GET /runs/{id}/plots` - List plot files
- `GET /runs/{id}/plots/{filename}` - Serve plot image

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models/              # Pydantic models
│   │   ├── routes/              # API routes
│   │   ├── core/                # Business logic
│   │   └── data/                # Data storage
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── components/          # Reusable components
│   │   ├── api/                 # API client
│   │   └── types/               # TypeScript types
│   └── package.json
├── analytics5.py                # Refactored (parameterized)
├── profile_analyzer5.py         # Refactored (parameterized)
├── zenin_plot_generator.py     # Refactored (parameterized)
└── zenin_mac2.py                # Refactored (wrapped in process_pipeline)
```

## Key Design Decisions

1. **Minimal Refactoring**: Existing Python files were only modified to accept parameters, preserving all business logic
2. **Profile Set Compatibility**: CSV format matches original `Zihin_Profilleri_29.csv` (semicolon-separated)
3. **Run Isolation**: Each run gets its own timestamped folder under `backend/app/data/runs/`
4. **Backward Compatibility**: Original `zenin_mac2.py` main() function still works with defaults

## Notes

- The default profile set "meditasyon" is automatically created from `Zihin_Profilleri_29.csv` on first startup
- All runs are stored in `backend/app/data/runs/{timestamp}/` with logs, plots, and metadata
- Profile sets are stored as CSV files in `backend/app/data/profiles/`
- The frontend communicates with the backend via REST API at `http://localhost:8000`
