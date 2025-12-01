# analytics.py
import os
import math
import re
from typing import Dict
import pandas as pd
import numpy as np

# Log şeman sabit kalsın
HEADERS = [
    "person_name","best_profile","En_Iyi_Profiller", "phone_number",
        "level_delta","level_theta","level_alpha","level_beta","level_gamma",
    "score_delta","score_theta","score_alpha","score_beta","score_gamma",
    "raw_mean_delta","raw_mean_theta","raw_mean_alpha","raw_mean_beta","raw_mean_gamma",
    "raw_mean_delta_window","raw_mean_theta_window","raw_mean_alpha_window","raw_mean_beta_window","raw_mean_gamma_window",
    "pct_delta","pct_theta","pct_alpha","pct_beta","pct_gamma",
    "pct_delta_window","pct_theta_window","pct_alpha_window","pct_beta_window","pct_gamma_window",
    "processed_at_utc","source_file","rows","duration_sec","Dalga_Farki", "Tam_Uyumlu_Profiller", "En_Iyi_Puan"]

# EEG grupları
GROUPS = {
    "Delta": ['Delta_TP9', 'Delta_AF7', 'Delta_AF8', 'Delta_TP10'],
    "Theta": ['Theta_TP9', 'Theta_AF7', 'Theta_AF8', 'Theta_TP10'],
    "Alpha": ['Alpha_TP9', 'Alpha_AF7', 'Alpha_AF8', 'Alpha_TP10'],
    "Beta":  ['Beta_TP9',  'Beta_AF7',  'Beta_AF8',  'Beta_TP10'],
    "Gamma": ['Gamma_TP9', 'Gamma_AF7', 'Gamma_AF8', 'Gamma_TP10']
}

BAND_THRESHOLDS = {
    "Delta": {
        "yüksek": 85,
        "yüksek orta": 75,
        "orta": 50,
        "düşük orta": 40
    },
    "Theta": {
        "yüksek": 70,
        "yüksek orta": 60,
        "orta": 40,
        "düşük orta": 30
    },
    "Alpha": {
        "yüksek": 80,
        "yüksek orta": 70,
        "orta": 50,
        "düşük orta": 40
    },
    "Beta": {
        "yüksek": 52,
        "yüksek orta": 45,
        "orta": 30,
        "düşük orta": 22
    },
    "Gamma": {
        "yüksek": 34,
        "yüksek orta": 27,
        "orta": 18,
        "düşük orta": 13
    }
}

WINDOW_SAMPLES = 5   # outlier temizliği için centered rolling window
WINDOW_SECS    = 30  # 1s resample sonrası rolling

def adjusted_legend_scores(band_means: Dict[str, float], target_min: float = 0.15) -> Dict[str, float]:
    data = {k: float(v) for k, v in band_means.items()
            if v is not None and not math.isnan(float(v)) and not math.isinf(float(v))}
    if not data:
        return {}
    # min'i yukarı çek
    min_val = min(data.values())
    inc = max(0.0, target_min - min_val)
    if inc > 0:
        for k in data:
            data[k] += inc
    # *100
    for k in data:
        data[k] *= 100.0
    # tepeye göre ölçek
    m = max(data.values())
    if m > 120:
        factor = 0.7
    elif 100 <= m <= 120:
        factor = 0.8
    elif 80 <= m < 100:
        factor = 0.9
    else:
        factor = 1.0
    for k in data:
        data[k] *= factor
    # güvenlik eşiği
    if max(data.values()) < 50.0:
        for k in data:
            data[k] += 20.0
    return data

def band_level_text(score: float, band: str, band_thresholds: Dict = None) -> str:
    if score is None or (isinstance(score, float) and (math.isnan(score) or math.isinf(score))):
        return ""
    
    # Use provided thresholds or fall back to defaults
    thresholds_dict = band_thresholds if band_thresholds is not None else BAND_THRESHOLDS
    thresholds = thresholds_dict.get(band, thresholds_dict.get("Alpha", BAND_THRESHOLDS["Alpha"]))
    
    # Handle both dict formats (with Turkish keys or snake_case keys)
    yuksek_key = "yüksek" if "yüksek" in thresholds else "yuksek"
    yuksek_orta_key = "yüksek orta" if "yüksek orta" in thresholds else "yuksek_orta"
    orta_key = "orta"
    dusuk_orta_key = "düşük orta" if "düşük orta" in thresholds else "dusuk_orta"
    
    if score > thresholds.get(yuksek_key, thresholds.get("yuksek", 85)):
        return "-yüksek-"
    elif score > thresholds.get(yuksek_orta_key, thresholds.get("yuksek_orta", 75)):
        return "-yüksek orta-"
    elif score > thresholds.get(orta_key, 50):
        return "-orta-"
    elif score > thresholds.get(dusuk_orta_key, thresholds.get("dusuk_orta", 40)):
        return "-düşük orta-"
    else:
        return "-düşük-"

def compute_mail_csv_metrics(df: pd.DataFrame, band_thresholds: Dict = None, window_secs: int = None, window_samples: int = None) -> Dict[str, float]:
    df = df.copy()
    df.columns = df.columns.str.strip()
    
    # Reusable bands list
    bands = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]

    print(f"🔧 ANALYTICS DEBUG: compute_mail_csv_metrics çağrıldı")
    print(f"🔧 ANALYTICS DEBUG: DataFrame shape: {df.shape}")
    print(f"🔧 ANALYTICS DEBUG: Columns: {list(df.columns)}")

    # TimeStamp & süre
    duration_sec = None
    has_ts = "TimeStamp" in df.columns
    if has_ts:
        df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
        df = df.sort_values("TimeStamp")
        ts_valid = df["TimeStamp"].dropna()
        if not ts_valid.empty:
            duration_sec = float((ts_valid.max() - ts_valid.min()).total_seconds())

    # 1) satır bazlı band avg kolonlarını üret VE DF'DE SAKLA
    for band, cols in GROUPS.items():
        # kolon adlarını case-insensitive yakala
        _lower = {c.lower(): c for c in df.columns}
        avail = [_lower[c.lower()] for c in cols if c.lower() in _lower]
        if not avail:
            continue
        # her kolonu numeric'e çevir, infinity değerleri NaN ile değiştir, sonra satır ortalaması
        num = df[avail].apply(pd.to_numeric, errors="coerce")
        # Replace infinity values with NaN
        num = num.replace([np.inf, -np.inf], np.nan)
        df[f"{band.lower()}_avg"] = num.mean(axis=1, skipna=True)

    avg_cols = [c for c in df.columns if c.endswith("_avg")]
    print(f"🔧 ANALYTICS DEBUG: Oluşturulan avg kolonlar: {avg_cols}")
    
    if not avg_cols:
        return {"rows": int(len(df)), "duration_sec": duration_sec,
                "raw_means": {}, "scores": {}, "levels": {}}

    # Use provided window_samples or default
    win_samples = window_samples if window_samples is not None else WINDOW_SAMPLES
    
    # 2) outlier temizliği (z > 3 → rolling mean ile doldur) VE DF'DE SAKLA
    for c in avg_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        # Replace infinity values with NaN before calculations
        s = s.replace([np.inf, -np.inf], np.nan)
        mu = s.mean()
        sigma = s.std(ddof=0)
        outliers = (abs((s - mu) / sigma) > 3) if sigma and sigma > 0 else pd.Series(False, index=s.index)
        rolling = s.rolling(window=win_samples, min_periods=1, center=True).mean()
        df[c + "_clean"] = np.where(outliers, rolling, s)

    clean_cols = [c for c in df.columns if c.endswith("_avg_clean")] or avg_cols
    print(f"🔧 ANALYTICS DEBUG: Clean kolonlar: {clean_cols}")

    # Use provided window_secs or default
    win_secs = window_secs if window_secs is not None else WINDOW_SECS
    
    # 3) 1s resample + 30s rolling → band ham ortalamaları
    raw_means: Dict[str, float] = {}
    if has_ts and df["TimeStamp"].notna().any():
        tsd = df.set_index("TimeStamp")[clean_cols]
        smooth = tsd.resample("1s").mean().rolling(f"{win_secs}s", min_periods=3).mean()
        for c in smooth.columns:
            series = pd.to_numeric(smooth[c], errors="coerce")
            # Replace infinity values with NaN before dropping
            series = series.replace([np.inf, -np.inf], np.nan).dropna()
            if series.empty:
                continue
            band = c.replace("_avg_clean", "").replace("_avg", "").capitalize()
            raw_means[band] = float(series.mean())
    else:
        for c in clean_cols:
            band = c.replace("_avg_clean", "").replace("_avg", "").capitalize()
            s = pd.to_numeric(df[c], errors="coerce")
            # Replace infinity values with NaN
            s = s.replace([np.inf, -np.inf], np.nan)
            raw_means[band] = float(s.mean())

    print(f"🔧 ANALYTICS DEBUG: Raw means: {raw_means}")

    # 3.5) Window filtering + % computation
    # Identify band columns for each band
    band_cols_map = {}
    for band in ["Delta", "Theta", "Alpha", "Beta", "Gamma"]:
        # Prefer clean version, fallback to avg
        clean_col = f"{band.lower()}_avg_clean"
        avg_col = f"{band.lower()}_avg"
        if clean_col in df.columns:
            band_cols_map[band] = clean_col
        elif avg_col in df.columns:
            band_cols_map[band] = avg_col
        else:
            band_cols_map[band] = None

    # Read HSI columns
    hsi_cols = ["HSI_TP9", "HSI_AF7", "HSI_AF8", "HSI_TP10"]
    available_hsi = [c for c in hsi_cols if c in df.columns]
    
    # Initialize window-filtered means and pct dicts with None (not 0.0)
    raw_means_window: Dict[str, float] = {b: None for b in bands}
    pct_all: Dict[str, float] = {b: None for b in bands}
    pct_window: Dict[str, float] = {b: None for b in bands}

    if band_cols_map:
        # For each row, compute total_power and check quality
        row_band_values = {}
        for band, col in band_cols_map.items():
            if col:
                row_band_values[band] = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
            else:
                row_band_values[band] = pd.Series([np.nan] * len(df))

        # Compute per-row total_power and min_band_value
        band_df = pd.DataFrame(row_band_values)
        
        # Compute total_power: sum of max(band, 0)
        total_power = band_df.apply(lambda row: sum([max(v, 0) if not pd.isna(v) else 0 for v in row]), axis=1)
        
        # Compute min_band_value
        min_band_value = band_df.min(axis=1)

        # Check HSI quality
        hsi_bad = pd.Series([False] * len(df))
        if available_hsi:
            for hsi_col in available_hsi:
                hsi_series = pd.to_numeric(df[hsi_col], errors="coerce")
                hsi_bad = hsi_bad | (hsi_series >= 3)

        # Define low quality windows
        low_quality_window = (
            hsi_bad |
            (total_power < 2.0) |
            (min_band_value < -5.0)
        )

        # High quality mask
        hq = ~low_quality_window

        print(f"🔧 ANALYTICS DEBUG: Total rows: {len(df)}, High-quality rows: {hq.sum()}")

        # Compute window-filtered means
        for band, col in band_cols_map.items():
            if col:
                series = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
                hq_series = series[hq].dropna()
                if not hq_series.empty:
                    raw_means_window[band] = float(hq_series.mean())
                else:
                    raw_means_window[band] = None  # No good windows -> None, not 0
            else:
                raw_means_window[band] = None

        # Compute pct_all: per-row normalized average (skip zero-power rows)
        pct_lists = {b: [] for b in bands}
        
        for idx in range(len(df)):
            vals = {}
            for band in bands:
                col = band_cols_map.get(band)
                if not col:
                    vals[band] = 0.0
                    continue
                v = row_band_values[band].iloc[idx]
                if pd.isna(v) or not np.isfinite(v):
                    vals[band] = 0.0
                else:
                    vals[band] = max(float(v), 0.0)
            
            row_total = sum(vals.values())
            if row_total <= 0:
                # Skip rows with no usable power
                continue
            
            for band in bands:
                pct_lists[band].append(vals[band] / row_total)
        
        # Average the per-row percentages
        for band in bands:
            lst = pct_lists[band]
            if lst:
                pct_all[band] = round(float(np.mean(lst)), 4)  # Keep as 0-1 proportion
            else:
                pct_all[band] = None

        # Compute pct_window: normalize window means
        def _compute_pct_from_means(means_dict):
            vals = {}
            for b in bands:
                v = means_dict.get(b)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    continue
                vals[b] = max(float(v), 0.0)
            
            total = sum(vals.values())
            pct = {b: None for b in bands}
            if total > 0:
                for b in bands:
                    v = vals.get(b)
                    if v is not None:
                        pct[b] = round(v / total, 4)  # 0-1 proportion
            return pct
        
        pct_window = _compute_pct_from_means(raw_means_window)

    print(f"🔧 ANALYTICS DEBUG: Raw means window: {raw_means_window}")
    print(f"🔧 ANALYTICS DEBUG: Pct all: {pct_all}")
    print(f"🔧 ANALYTICS DEBUG: Pct window: {pct_window}")

    # 4) skor + level
    scores = adjusted_legend_scores(raw_means)

    # Dalga farkı hesapla
    valid_scores = []
    for band in ["Delta", "Theta", "Alpha", "Beta", "Gamma"]:
        if band in scores and scores[band] is not None:
            try:
                val = float(scores[band])
                if not math.isnan(val) and not math.isinf(val):
                    valid_scores.append(val)
            except (TypeError, ValueError):
                continue

    dalga_farki = None
    if len(valid_scores) >= 2:
        dalga_farki = round(max(valid_scores) - min(valid_scores), 2)
        print(f"🔧 DEBUG Dalga Farkı: max={max(valid_scores):.2f}, min={min(valid_scores):.2f}, fark={dalga_farki:.2f}")
    else:
        dalga_farki = ""

    levels = {b: band_level_text(scores.get(b), b, band_thresholds) for b in bands}

    return {
        "rows": int(len(df)),
        "duration_sec": None if duration_sec is None else round(duration_sec, 2),
        "raw_means": {k: (None if v is None else round(v, 6)) for k, v in raw_means.items()},
        "raw_means_window": {k: (None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 6)) for k, v in raw_means_window.items()},
        "pct_all": pct_all,  # Keep None, do not coerce to 0.0
        "pct_window": pct_window,  # Keep None, do not coerce to 0.0
        "dalga_farki": dalga_farki,  # Tek anahtar, her yerde aynı
        "scores": {k: (None if scores.get(k) is None else round(scores.get(k), 2))
                  for k in bands},
        "levels": levels,
        "dataframe_with_clean": df
    }

def to_sheet_row(person_name: str, source_file: str, metrics: dict):
    stamp = pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    rm = metrics.get("raw_means", {})
    rmw = metrics.get("raw_means_window", {})
    pct = metrics.get("pct_all", {})
    pctw = metrics.get("pct_window", {})
    sc = metrics.get("scores", {})
    lv = metrics.get("levels", {})
    
    # Helper function to get float value, returns None for missing/invalid
    def _get_float_optional(d, key):
        val = d.get(key)
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Extract best_profile (first profile from comma-separated en_iyi_profiller)
    en_iyi_profiller_str = metrics.get("en_iyi_profiller", "") or ""
    best_profile = ""
    if en_iyi_profiller_str:
        # Remove "(4 uyumlu)" markers and get first profile
        first_profile = en_iyi_profiller_str.split(",")[0].strip()
        # Remove any "(4 uyumlu)" or similar markers
        first_profile = re.sub(r"\s*\(.*?4\s*uyumlu.*?\)", "", first_profile, flags=re.IGNORECASE).strip()
        best_profile = first_profile

    record = {
        "person_name": person_name or "unknown",
        "best_profile": best_profile,
        "phone_number": metrics.get("phone_number", ""),
        "level_delta": lv.get("Delta", ""),
        "level_theta": lv.get("Theta", ""),
        "level_alpha": lv.get("Alpha", ""),
        "level_beta":  lv.get("Beta", ""),
        "level_gamma": lv.get("Gamma", ""),
        "score_delta": sc.get("Delta"),
        "score_theta": sc.get("Theta"),
        "score_alpha": sc.get("Alpha"),
        "score_beta":  sc.get("Beta"),
        "score_gamma": sc.get("Gamma"),
        "raw_mean_delta": rm.get("Delta"),
        "raw_mean_theta": rm.get("Theta"),
        "raw_mean_alpha": rm.get("Alpha"),
        "raw_mean_beta":  rm.get("Beta"),
        "raw_mean_gamma": rm.get("Gamma"),
        "raw_mean_delta_window": _get_float_optional(rmw, "Delta"),
        "raw_mean_theta_window": _get_float_optional(rmw, "Theta"),
        "raw_mean_alpha_window": _get_float_optional(rmw, "Alpha"),
        "raw_mean_beta_window":  _get_float_optional(rmw, "Beta"),
        "raw_mean_gamma_window": _get_float_optional(rmw, "Gamma"),
        "pct_delta": _get_float_optional(pct, "Delta"),
        "pct_theta": _get_float_optional(pct, "Theta"),
        "pct_alpha": _get_float_optional(pct, "Alpha"),
        "pct_beta":  _get_float_optional(pct, "Beta"),
        "pct_gamma": _get_float_optional(pct, "Gamma"),
        "pct_delta_window": _get_float_optional(pctw, "Delta"),
        "pct_theta_window": _get_float_optional(pctw, "Theta"),
        "pct_alpha_window": _get_float_optional(pctw, "Alpha"),
        "pct_beta_window":  _get_float_optional(pctw, "Beta"),
        "pct_gamma_window": _get_float_optional(pctw, "Gamma"),
        "processed_at_utc": stamp,
        "source_file": os.path.basename(source_file),
        "rows": metrics.get("rows"),
        "duration_sec": metrics.get("duration_sec"),
        # PROFİL SÜTUNLARI:
        "Dalga_Farki": metrics.get("dalga_farki", ""),
        "Tam_Uyumlu_Profiller": metrics.get("tam_uyumlu_profiller", ""),  # düzeltildi
        "En_Iyi_Profiller": metrics.get("en_iyi_profiller", ""),          # düzeltildi
        "En_Iyi_Puan": metrics.get("en_iyi_puan", ""),
    }

    # Debug: verify profile assignment
    if record.get("En_Iyi_Profiller") and str(record.get("En_Iyi_Profiller", "")).strip():
        print(f"✅ Profile assigned in to_sheet_row:")
        print(f"   best_profile: '{record.get('best_profile', 'MISSING')}'")
        print(f"   En_Iyi_Profiller: '{record['En_Iyi_Profiller']}'")
    else:
        print(f"⚠️ No profile in to_sheet_row! metrics keys: {list(metrics.keys())}")
        print(f"   en_iyi_profiller from metrics: '{metrics.get('en_iyi_profiller', 'MISSING')}'")
        print(f"   best_profile in record: '{record.get('best_profile', 'MISSING')}'")
        print(f"   En_Iyi_Profiller in record: '{record.get('En_Iyi_Profiller', 'MISSING')}'")

    def _clean(v):
        return "" if v is None or (isinstance(v, float) and math.isnan(v)) else v

    return [_clean(record.get(col)) for col in HEADERS]

