from pydantic import BaseModel, Field
from typing import Dict


class BandThresholds(BaseModel):
    yuksek: float
    yuksek_orta: float
    orta: float
    dusuk_orta: float


class RunConfig(BaseModel):
    dominance_delta: float = 29.0
    balance_threshold: float = 22.0
    denge_mean_threshold: float = 46.0
    window_secs: int = 30
    window_samples: int = 5
    data_root: str | None = None
    profile_set_id: str = "meditasyon"
    band_thresholds: Dict[str, BandThresholds] = Field(default_factory=dict)
