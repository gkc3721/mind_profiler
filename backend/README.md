# Backend - Zenin EEG Pipeline API

FastAPI backend that wraps the existing EEG analysis pipeline.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Data Structure

- `app/data/profiles/` - Profile set CSV files
- `app/data/runs/` - Run outputs (logs, plots, metadata)
- `app/data/config.json` - Default configuration (optional)
