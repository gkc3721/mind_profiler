from pydantic import BaseModel
from typing import List


class ProfileDefinition(BaseModel):
    id: str  # e.g. "YARATICI_LIDER"
    display_name: str  # "YARATICI LİDER"
    delta_level: str  # "yüksek", "orta", etc.
    theta_level: str
    alpha_level: str
    beta_level: str
    gamma_level: str
    notes: str | None = None


class ProfileSet(BaseModel):
    id: str  # "meditasyon"
    name: str  # "Meditasyon Profilleri"
    description: str = ""
    profiles: List[ProfileDefinition]


class ProfileSetSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    profile_count: int
