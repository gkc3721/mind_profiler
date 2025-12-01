import json
from pathlib import Path
from typing import Dict
from app.models.config import RunConfig, BandThresholds

# Default BAND_THRESHOLDS from analytics5.py
DEFAULT_BAND_THRESHOLDS = {
    "Delta": {
        "yuksek": 85,
        "yuksek_orta": 75,
        "orta": 50,
        "dusuk_orta": 40
    },
    "Theta": {
        "yuksek": 70,
        "yuksek_orta": 60,
        "orta": 40,
        "dusuk_orta": 30
    },
    "Alpha": {
        "yuksek": 80,
        "yuksek_orta": 70,
        "orta": 50,
        "dusuk_orta": 40
    },
    "Beta": {
        "yuksek": 52,
        "yuksek_orta": 45,
        "orta": 30,
        "dusuk_orta": 22
    },
    "Gamma": {
        "yuksek": 34,
        "yuksek_orta": 27,
        "orta": 18,
        "dusuk_orta": 13
    }
}

CONFIG_FILE = Path(__file__).parent.parent / "data" / "config.json"


def _convert_thresholds_to_model(thresholds_dict: Dict) -> Dict[str, BandThresholds]:
    """Convert dict format to BandThresholds models"""
    return {
        band: BandThresholds(**thresh)
        for band, thresh in thresholds_dict.items()
    }


def get_default_config() -> RunConfig:
    """Load default configuration from config.json or return defaults"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert band_thresholds dict to BandThresholds models
                if "band_thresholds" in data:
                    data["band_thresholds"] = _convert_thresholds_to_model(data["band_thresholds"])
                return RunConfig(**data)
        except Exception as e:
            print(f"⚠️ Error loading config.json: {e}, using defaults")
    
    # Return default config
    return RunConfig(
        dominance_delta=29.0,
        balance_threshold=22.0,
        denge_mean_threshold=46.0,
        window_secs=30,
        window_samples=5,
        profile_set_id="meditasyon",
        band_thresholds=_convert_thresholds_to_model(DEFAULT_BAND_THRESHOLDS)
    )


def save_config(config: RunConfig) -> None:
    """Save configuration to config.json"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict, handling BandThresholds models
    config_dict = config.model_dump()
    # BandThresholds will be serialized as dict automatically
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
