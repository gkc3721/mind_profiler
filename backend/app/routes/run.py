from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import json
import sys

from app.core.engine import run_batch, run_single
from app.models.config import RunConfig
from app.models.runs import RunResult, RunSummary

router = APIRouter()

RUNS_DIR = Path(__file__).parent.parent / "data" / "runs"


@router.post("/run/batch", response_model=RunResult)
async def run_batch_endpoint(config: RunConfig):
    """Run pipeline on all CSVs in data_root folder"""
    try:
        return run_batch(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/single", response_model=RunResult)
async def run_single_endpoint(
    config: RunConfig = Body(...),
    csv_path: str = Body(..., embed=True)
):
    """Run pipeline on a single CSV file by path"""
    try:
        return run_single(config, csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/upload", response_model=RunResult)
async def run_upload_endpoint(
    file: UploadFile = File(...),
    config: str = Form(...)
):
    """Run pipeline on an uploaded CSV file"""
    try:
        config_obj = RunConfig.parse_raw(config)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = run_dir / "input.csv"
        with open(csv_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return run_single(config_obj, str(csv_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/upload-batch", response_model=RunResult)
async def run_upload_batch_endpoint(
    files: list[UploadFile] = File(...),
    config: str = Form(...)
):
    """Run pipeline on multiple uploaded CSV files (folder upload)"""
    try:
        config_obj = RunConfig.parse_raw(config)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = RUNS_DIR / run_id
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Save all uploaded CSV files (flatten directory structure)
        csv_count = 0
        for file in files:
            if file.filename and file.filename.lower().endswith('.csv'):
                # Extract only the basename to flatten the directory structure
                # This handles cases where webkitdirectory includes folder names like "sample data/file.csv"
                safe_name = Path(file.filename).name
                file_path = input_dir / safe_name
                
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                csv_count += 1
        
        if csv_count == 0:
            raise ValueError("No CSV files found in uploaded folder")
        
        # Update config to use the input directory as data_root
        config_obj.data_root = str(input_dir)
        
        # Call run_batch with the uploaded files directory
        return run_batch(config_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=list[RunSummary])
async def list_runs_endpoint():
    """List all past runs"""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    
    runs = []
    for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            config_data = metadata.get("config", {})
            runs.append(RunSummary(
                run_id=metadata.get("run_id", run_dir.name),
                timestamp=metadata.get("timestamp", ""),
                profile_set_id=config_data.get("profile_set_id", "meditasyon"),
                processed_files=metadata.get("processed_files", 0),
                matched_count=metadata.get("matched_count", 0),
                unmatched_count=metadata.get("unmatched_count", 0),
                dominance_delta=config_data.get("dominance_delta", 29.0),
                balance_threshold=config_data.get("balance_threshold", 22.0),
                window_secs=config_data.get("window_secs", 30)
            ))
        except Exception as e:
            print(f"⚠️ Error reading run {run_dir.name}: {e}")
            continue
    
    return runs


@router.get("/runs/{run_id}", response_model=RunResult)
async def get_run_endpoint(run_id: str):
    """Get details of a specific run"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail=f"Metadata for run {run_id} not found")
    
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        config = RunConfig(**metadata.get("config", {}))
        
        log_file = run_dir / f"processing_log{run_id}.csv"
        if not log_file.exists():
            # Try alternative name
            log_file = list(run_dir.glob("processing_log*.csv"))
            if log_file:
                log_file = log_file[0]
            else:
                log_file = run_dir / f"processing_log{run_id}.csv"
        
        summary_xlsx = run_dir / f"profile_summary{run_id}.xlsx"
        if not summary_xlsx.exists():
            summary_xlsx = run_dir / "profile_summary.xlsx"
            if not summary_xlsx.exists():
                summary_xlsx = None
        
        return RunResult(
            run_id=metadata.get("run_id", run_id),
            timestamp=metadata.get("timestamp", ""),
            config=config,
            processed_files=metadata.get("processed_files", 0),
            matched_count=metadata.get("matched_count", 0),
            unmatched_count=metadata.get("unmatched_count", 0),
            log_file=str(log_file) if log_file.exists() else "",
            plots_dir=str(run_dir / "graphs"),
            summary_xlsx=str(summary_xlsx) if summary_xlsx and summary_xlsx.exists() else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/log")
async def get_run_log_endpoint(run_id: str):
    """Download the processing log CSV for a run"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    log_file = run_dir / f"processing_log{run_id}.csv"
    if not log_file.exists():
        # Try alternative name
        log_files = list(run_dir.glob("processing_log*.csv"))
        if log_files:
            log_file = log_files[0]
        else:
            raise HTTPException(status_code=404, detail=f"Log file for run {run_id} not found")
    
    return FileResponse(
        str(log_file),
        media_type="text/csv",
        filename=log_file.name
    )


@router.get("/runs/{run_id}/plots")
async def list_plots_endpoint(run_id: str):
    """List all plot files for a run"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    plots_dir = run_dir / "graphs"
    if not plots_dir.exists():
        return {"plots": []}
    
    # Recursively find all PNG files
    plots = []
    for png_file in plots_dir.rglob("*.png"):
        rel_path = png_file.relative_to(plots_dir)
        plots.append(str(rel_path).replace("\\", "/"))  # Normalize path separators
    
    return {"plots": sorted(plots)}


@router.get("/runs/{run_id}/plots/{filename:path}")
async def get_plot_endpoint(run_id: str, filename: str):
    """Serve a plot image file"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    plots_dir = run_dir / "graphs"
    plot_path = plots_dir / filename
    
    # Security: ensure the path is within plots_dir
    try:
        plot_path.resolve().relative_to(plots_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if not plot_path.exists():
        raise HTTPException(status_code=404, detail=f"Plot {filename} not found")
    
    return FileResponse(str(plot_path), media_type="image/png")


@router.get("/runs/{run_id}/summary")
async def get_summary_endpoint(run_id: str):
    """Get the profile summary as JSON for inline viewing"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Try multiple possible file names
    summary_file = run_dir / f"profile_summary{run_id}.xlsx"
    if not summary_file.exists():
        summary_file = run_dir / "profile_summary.xlsx"
    
    if not summary_file.exists():
        raise HTTPException(status_code=404, detail=f"Summary file for run {run_id} not found")
    
    # Helper function to convert DataFrame to JSON-safe dict
    def df_to_json_safe(df: "pd.DataFrame"):
        """Convert DataFrame to JSON-safe dict, handling NaN and Infinity values"""
        import numpy as np
        import pandas as pd
        import math
        
        # Replace inf and -inf with NaN first
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Convert to dict first
        records = df.to_dict(orient="records")
        
        # Now iterate through and replace any NaN/None values
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Check if value is NaN (works for both float NaN and np.nan)
                if isinstance(value, float) and math.isnan(value):
                    cleaned_record[key] = None
                elif value is None or (isinstance(value, float) and math.isinf(value)):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    # Read the Excel file and convert to JSON
    try:
        import pandas as pd
        
        # Read all sheets from the Excel file at once
        sheets = pd.read_excel(str(summary_file), sheet_name=None)
        
        # Convert each sheet to JSON-safe dict
        sheets_json = {
            sheet_name: df_to_json_safe(df)
            for sheet_name, df in sheets.items()
        }
        
        return {
            "run_id": run_id,
            "sheets": sheets_json,
            "download_url": f"/runs/{run_id}/summary/download"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading summary file: {str(e)}")


@router.get("/runs/{run_id}/summary/download")
async def download_summary_endpoint(run_id: str):
    """Download the profile summary Excel file for a run"""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    # Try multiple possible file names
    summary_file = run_dir / f"profile_summary{run_id}.xlsx"
    if not summary_file.exists():
        summary_file = run_dir / "profile_summary.xlsx"
    
    if not summary_file.exists():
        raise HTTPException(status_code=404, detail=f"Summary file for run {run_id} not found")
    
    return FileResponse(
        str(summary_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"profile_summary_{run_id}.xlsx"
    )
