import os
import re
import pandas as pd
from pathlib import Path
from typing import List, Optional
from app.models.profiles import ProfileSet, ProfileDefinition, ProfileSetSummary

PROFILES_DIR = Path(__file__).parent.parent / "data" / "profiles"
DEFAULT_PROFILE_SOURCE = Path(__file__).parent.parent.parent.parent / "Zihin_Profilleri_29.csv"


def _sanitize_id(name: str) -> str:
    """Convert display name to safe filename (ID)"""
    # Convert to lowercase, replace spaces with underscores, remove special chars
    s = name.lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '_', s)
    return s.strip('_')


def _normalize_level(level: str) -> str:
    """Normalize wave level to standard format"""
    if not level or pd.isna(level):
        return ""
    level = str(level).strip()
    # Convert to lowercase, normalize Turkish characters
    level = level.lower()
    # Handle common variations
    level = level.replace("yüksek", "yüksek").replace("yuksek", "yüksek")
    level = level.replace("düşük", "düşük").replace("dusuk", "düşük")
    level = level.replace("orta", "orta")
    return level


def _profile_name_to_id(display_name: str) -> str:
    """Convert profile display name to ID"""
    return display_name.upper().replace(" ", "_").replace("-", "_").replace("İ", "I")


def initialize_default_profiles():
    """Copy Zihin_Profilleri_29.csv to data/profiles/meditasyon.csv if it doesn't exist"""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    default_path = PROFILES_DIR / "meditasyon.csv"
    
    if not default_path.exists() and DEFAULT_PROFILE_SOURCE.exists():
        import shutil
        shutil.copy2(DEFAULT_PROFILE_SOURCE, default_path)
        print(f"✅ Initialized default profile set: {default_path}")


def list_profile_sets() -> List[ProfileSetSummary]:
    """List all profile sets (CSV files in profiles directory)"""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    
    summaries = []
    for csv_file in PROFILES_DIR.glob("*.csv"):
        profile_set_id = csv_file.stem
        try:
            profile_set = get_profile_set(profile_set_id)
            summaries.append(ProfileSetSummary(
                id=profile_set.id,
                name=profile_set.name,
                description=profile_set.description,
                profile_count=len(profile_set.profiles)
            ))
        except Exception as e:
            print(f"⚠️ Error reading profile set {profile_set_id}: {e}")
            # Still include it with minimal info
            summaries.append(ProfileSetSummary(
                id=profile_set_id,
                name=profile_set_id.replace("_", " ").title(),
                description="",
                profile_count=0
            ))
    
    return summaries


def get_profile_set(profile_set_id: str) -> ProfileSet:
    """Load a profile set from CSV file"""
    csv_path = PROFILES_DIR / f"{profile_set_id}.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Profile set '{profile_set_id}' not found")
    
    # Read CSV (try semicolon first, then comma)
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", sep=';')
    except Exception:
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig", sep=';')
        except Exception:
            df = pd.read_csv(csv_path, encoding="utf-8", sep=',')
    
    # Normalize column names
    cols = list(df.columns)
    cols_norm = {c: c.strip().lower() for c in cols}
    
    # Find profile name column
    profile_col = None
    for c, cn in cols_norm.items():
        if "profil" in cn and "ad" in cn:
            profile_col = c
            break
    
    if not profile_col:
        profile_col = cols[0]  # Fallback to first column
    
    # Find band columns
    bands = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
    band_cols = {}
    for band in bands:
        for c, cn in cols_norm.items():
            if cn.strip().lower() == band.lower():
                band_cols[band] = c
                break
    
    # Build profiles list
    profiles = []
    for _, row in df.iterrows():
        profile_name = str(row.get(profile_col, "")).strip()
        if not profile_name or pd.isna(profile_name):
            continue
        
        profile_id = _profile_name_to_id(profile_name)
        
        # Extract wave levels
        delta_level = _normalize_level(row.get(band_cols.get("Delta", ""), ""))
        theta_level = _normalize_level(row.get(band_cols.get("Theta", ""), ""))
        alpha_level = _normalize_level(row.get(band_cols.get("Alpha", ""), ""))
        beta_level = _normalize_level(row.get(band_cols.get("Beta", ""), ""))
        gamma_level = _normalize_level(row.get(band_cols.get("Gamma", ""), ""))
        
        profiles.append(ProfileDefinition(
            id=profile_id,
            display_name=profile_name,
            delta_level=delta_level,
            theta_level=theta_level,
            alpha_level=alpha_level,
            beta_level=beta_level,
            gamma_level=gamma_level
        ))
    
    # Generate name and description
    name = profile_set_id.replace("_", " ").title()
    if profile_set_id == "meditasyon":
        name = "Meditasyon Profilleri"
    
    return ProfileSet(
        id=profile_set_id,
        name=name,
        description="",
        profiles=profiles
    )


def save_profile_set(profile_set: ProfileSet) -> None:
    """Save a profile set to CSV file"""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = PROFILES_DIR / f"{profile_set.id}.csv"
    
    # Build DataFrame
    rows = []
    for profile in profile_set.profiles:
        rows.append({
            "Profil Adı": profile.display_name,
            "Delta": profile.delta_level,
            "Theta": profile.theta_level,
            "Alpha": profile.alpha_level,
            "Beta": profile.beta_level,
            "Gamma": profile.gamma_level
        })
    
    df = pd.DataFrame(rows)
    
    # Save as semicolon-separated CSV (matching original format)
    df.to_csv(csv_path, index=False, sep=';', encoding="utf-8-sig")
    print(f"✅ Saved profile set: {csv_path}")


def delete_profile_set(profile_set_id: str) -> None:
    """Delete a profile set (CSV file)"""
    if profile_set_id == "meditasyon":
        raise ValueError("Cannot delete default profile set 'meditasyon'")
    
    csv_path = PROFILES_DIR / f"{profile_set_id}.csv"
    if csv_path.exists():
        csv_path.unlink()
        print(f"✅ Deleted profile set: {csv_path}")
    else:
        raise FileNotFoundError(f"Profile set '{profile_set_id}' not found")
