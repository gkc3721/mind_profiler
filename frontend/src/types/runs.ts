import { RunConfig } from './config';

export interface RunResult {
  run_id: string;
  timestamp: string;
  config: RunConfig;
  processed_files: number;
  matched_count: number;
  unmatched_count: number;
  log_file: string;
  plots_dir: string;
  summary_xlsx: string | null;
}

export interface RunSummary {
  run_id: string;
  timestamp: string;
  profile_set_id: string;
  processed_files: number;
  matched_count: number;
  unmatched_count: number;
  dominance_delta: number;
  balance_threshold: number;
  window_secs: number;
}
