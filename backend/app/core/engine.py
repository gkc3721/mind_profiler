import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
import json

# Add parent directory to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from zenin_mac2 import process_pipeline
from app.models.config import RunConfig
from app.models.runs import RunResult
from app.core.profiles_manager import get_profile_set

RUNS_DIR = Path(__file__).parent.parent / "data" / "runs"


def _convert_band_thresholds_to_dict(band_thresholds: Dict) -> Dict:
    """Convert Pydantic BandThresholds models to dict format expected by pipeline"""
    if not band_thresholds:
        return None
    
    result = {}
    for band, thresh in band_thresholds.items():
        if hasattr(thresh, 'model_dump'):  # Pydantic model
            result[band] = {
                "yüksek": thresh.yuksek,
                "yüksek orta": thresh.yuksek_orta,
                "orta": thresh.orta,
                "düşük orta": thresh.dusuk_orta
            }
        else:  # Already a dict
            result[band] = thresh
    return result


def generate_profile_summary(log_path: str, output_dir: str, run_id: str) -> Path | None:
    """
    Generate profile summary Excel file from processing log.
    
    Args:
        log_path: Path to the processing log CSV
        output_dir: Directory where summary Excel will be saved
        run_id: Run ID for naming the output file
    
    Returns:
        Path to generated Excel file, or None if generation failed
    """
    try:
        # Import the analyze_processing_log module
        from analyze_processing_log import main as analyze_log_main
        
        # Call the main function with log path, output directory, AND run_id
        # This ensures the summary file is named consistently
        analyze_log_main(log_path, output_dir, run_id_arg=run_id)
        
        # The file should now be created with the correct name
        expected_path = Path(output_dir) / f"profile_summary{run_id}.xlsx"
        
        if expected_path.exists():
            return expected_path
        else:
            print(f"⚠️ Summary file not created at {expected_path}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error generating profile summary: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_batch(config: RunConfig) -> RunResult:
    """Process all CSVs in config.data_root using the selected profile set and constants."""
    if not config.data_root:
        raise ValueError("data_root must be provided for batch processing")
    
    # Generate run_id (timestamp-based)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Get profile CSV path from profile_set_id
    profiles_dir = Path(__file__).parent.parent / "data" / "profiles"
    profile_csv = profiles_dir / f"{config.profile_set_id}.csv"
    
    if not profile_csv.exists():
        raise FileNotFoundError(f"Profile set '{config.profile_set_id}' not found at {profile_csv}")
    
    # Convert band_thresholds
    band_thresh_dict = _convert_band_thresholds_to_dict(config.band_thresholds)
    
    # Call refactored zenin_mac2.process_pipeline() with config params
    try:
        result = process_pipeline(
            csv_root=config.data_root,
            run_id=run_id,
            output_dir=str(run_dir),
            profile_csv_path=str(profile_csv),
            dominance_delta=config.dominance_delta,
            balance_threshold=config.balance_threshold,
            denge_mean_threshold=config.denge_mean_threshold,
            window_secs=config.window_secs,
            window_samples=config.window_samples,
            band_thresholds=band_thresh_dict
        )
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # Move log file to run directory if it's elsewhere
    log_path = Path(result.get("log_path", run_dir / f"processing_log{run_id}.csv"))
    if log_path.parent != run_dir:
        new_log_path = run_dir / log_path.name
        if log_path.exists():
            import shutil
            shutil.move(str(log_path), str(new_log_path))
        log_path = new_log_path
    else:
        log_path = run_dir / f"processing_log{run_id}.csv"
    
    # Generate profile summary Excel
    summary_xlsx_path = None
    if log_path.exists():
        print(f"✅ Generating profile summary from log: {log_path}")
        summary_xlsx_path = generate_profile_summary(
            log_path=str(log_path),
            output_dir=str(run_dir),
            run_id=run_id
        )
        if summary_xlsx_path:
            print(f"✅ Profile summary created: {summary_xlsx_path}")
        else:
            print(f"⚠️ Profile summary generation failed")
    else:
        print(f"⚠️ Log file not found at {log_path}, cannot generate summary")
    
    # Save run metadata
    metadata = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "config": config.model_dump(),
        "processed_files": result.get("processed_files", 0),
        "matched_count": result.get("matched_count", 0),
        "unmatched_count": result.get("unmatched_count", 0)
    }
    metadata_path = run_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Debug logging
    print(f"🔍 DEBUG - Run completed:")
    print(f"  Run ID: {run_id}")
    print(f"  Run dir: {run_dir}")
    print(f"  Log file: {log_path}")
    print(f"  Summary file: {summary_xlsx_path}")
    print(f"  Plots dir: {run_dir / 'graphs'}")
    print(f"  Plots dir exists: {(run_dir / 'graphs').exists()}")
    if (run_dir / 'graphs').exists():
        plots_list = list((run_dir / 'graphs').rglob('*.png'))
        print(f"  Plots count: {len(plots_list)}")
    
    return RunResult(
        run_id=run_id,
        timestamp=metadata["timestamp"],
        config=config,
        processed_files=result.get("processed_files", 0),
        matched_count=result.get("matched_count", 0),
        unmatched_count=result.get("unmatched_count", 0),
        log_file=str(log_path),
        plots_dir=str(run_dir / "graphs"),
        summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
    )


def run_single(config: RunConfig, csv_path: str) -> RunResult:
    """Process exactly one CSV file (by path or uploaded temp file)."""
    # Generate run_id (timestamp-based)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy CSV to run_dir if it's not already there
    csv_path_obj = Path(csv_path)
    if csv_path_obj.parent != run_dir:
        input_csv = run_dir / "input.csv"
        import shutil
        shutil.copy2(csv_path, input_csv)
        csv_path = str(input_csv)
    else:
        csv_path = str(csv_path_obj)
    
    # Get profile CSV path from profile_set_id
    profiles_dir = Path(__file__).parent.parent / "data" / "profiles"
    profile_csv = profiles_dir / f"{config.profile_set_id}.csv"
    
    if not profile_csv.exists():
        raise FileNotFoundError(f"Profile set '{config.profile_set_id}' not found at {profile_csv}")
    
    # Convert band_thresholds
    band_thresh_dict = _convert_band_thresholds_to_dict(config.band_thresholds)
    
    # Create a temporary directory structure for single file processing
    # The pipeline expects a directory to walk, so we'll create a temp structure
    temp_data_dir = run_dir / "temp_data"
    temp_data_dir.mkdir(exist_ok=True)
    
    # Copy the CSV to temp_data_dir
    import shutil
    shutil.copy2(csv_path, temp_data_dir / Path(csv_path).name)
    
    # Call process_pipeline with temp_data_dir as csv_root
    try:
        result = process_pipeline(
            csv_root=str(temp_data_dir),
            run_id=run_id,
            output_dir=str(run_dir),
            profile_csv_path=str(profile_csv),
            dominance_delta=config.dominance_delta,
            balance_threshold=config.balance_threshold,
            denge_mean_threshold=config.denge_mean_threshold,
            window_secs=config.window_secs,
            window_samples=config.window_samples,
            band_thresholds=band_thresh_dict
        )
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # Move log file to run directory
    log_path = Path(result.get("log_path", run_dir / f"processing_log{run_id}.csv"))
    if log_path.parent != run_dir:
        new_log_path = run_dir / log_path.name
        if log_path.exists():
            import shutil
            shutil.move(str(log_path), str(new_log_path))
        log_path = new_log_path
    else:
        log_path = run_dir / f"processing_log{run_id}.csv"
    
    # Generate profile summary Excel
    summary_xlsx_path = None
    if log_path.exists():
        print(f"✅ Generating profile summary from log: {log_path}")
        summary_xlsx_path = generate_profile_summary(
            log_path=str(log_path),
            output_dir=str(run_dir),
            run_id=run_id
        )
        if summary_xlsx_path:
            print(f"✅ Profile summary created: {summary_xlsx_path}")
        else:
            print(f"⚠️ Profile summary generation failed")
    else:
        print(f"⚠️ Log file not found at {log_path}, cannot generate summary")
    
    # Save run metadata
    metadata = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "config": config.model_dump(),
        "processed_files": result.get("processed_files", 0),
        "matched_count": result.get("matched_count", 0),
        "unmatched_count": result.get("unmatched_count", 0),
        "csv_path": csv_path
    }
    metadata_path = run_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Debug logging
    print(f"🔍 DEBUG - Run completed:")
    print(f"  Run ID: {run_id}")
    print(f"  Run dir: {run_dir}")
    print(f"  Log file: {log_path}")
    print(f"  Summary file: {summary_xlsx_path}")
    print(f"  Plots dir: {run_dir / 'graphs'}")
    print(f"  Plots dir exists: {(run_dir / 'graphs').exists()}")
    if (run_dir / 'graphs').exists():
        plots_list = list((run_dir / 'graphs').rglob('*.png'))
        print(f"  Plots count: {len(plots_list)}")
    
    return RunResult(
        run_id=run_id,
        timestamp=metadata["timestamp"],
        config=config,
        processed_files=result.get("processed_files", 0),
        matched_count=result.get("matched_count", 0),
        unmatched_count=result.get("unmatched_count", 0),
        log_file=str(log_path),
        plots_dir=str(run_dir / "graphs"),
        summary_xlsx=summary_xlsx_path.name if summary_xlsx_path and summary_xlsx_path.exists() else None
    )
