export interface ProfileDefinition {
  id: string;
  display_name: string;
  delta_level: string;
  theta_level: string;
  alpha_level: string;
  beta_level: string;
  gamma_level: string;
  notes?: string | null;
}

export interface ProfileSet {
  id: string;
  name: string;
  description: string;
  profiles: ProfileDefinition[];
}

export interface ProfileSetSummary {
  id: string;
  name: string;
  description: string;
  profile_count: number;
}

export const WAVE_LEVELS = ['yüksek', 'yüksek orta', 'orta', 'düşük orta', 'düşük'] as const;
export type WaveLevel = typeof WAVE_LEVELS[number];
