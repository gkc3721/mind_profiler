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
  band_thresholds: Record<string, BandThresholds>;
}
