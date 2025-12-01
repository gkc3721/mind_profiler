from pydantic import BaseModel
from .config import RunConfig


class RunResult(BaseModel):
    run_id: str
    timestamp: str
    config: RunConfig
    processed_files: int
    matched_count: int
    unmatched_count: int
    log_file: str
    plots_dir: str
    summary_xlsx: str | None = None


class RunSummary(BaseModel):
    run_id: str
    timestamp: str
    profile_set_id: str
    processed_files: int
    matched_count: int
    unmatched_count: int
    dominance_delta: float
    balance_threshold: float
    window_secs: int
