# analytics.py
import os
import math
from typing import Dict
import pandas as pd
import numpy as np

# Log şeman sabit kalsın
HEADERS = [
    "person_name","En_Iyi_Profiller", "phone_number",
        "level_delta","level_theta","level_alpha","level_beta","level_gamma",
    "score_delta","score_theta","score_alpha","score_beta","score_gamma",
    "raw_mean_delta","raw_mean_theta","raw_mean_alpha","raw_mean_beta","raw_mean_gamma",
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

def band_level_text(score: float, band: str) -> str:
    if score is None or (isinstance(score, float) and (math.isnan(score) or math.isinf(score))):
        return ""
        
    thresholds = BAND_THRESHOLDS.get(band, BAND_THRESHOLDS["Alpha"])  # Default to Alpha if band not found
    
    if score > thresholds["yüksek"]:
        return "-yüksek-"
    elif score > thresholds["yüksek orta"]:
        return "-yüksek orta-"
    elif score > thresholds["orta"]:
        return "-orta-"
    elif score > thresholds["düşük orta"]:
        return "-düşük orta-"
    else:
        return "-düşük-"

def compute_mail_csv_metrics(df: pd.DataFrame) -> Dict[str, float]:
    df = df.copy()
    df.columns = df.columns.str.strip()

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

    # 2) outlier temizliği (z > 3 → rolling mean ile doldur) VE DF'DE SAKLA
    for c in avg_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        # Replace infinity values with NaN before calculations
        s = s.replace([np.inf, -np.inf], np.nan)
        mu = s.mean()
        sigma = s.std(ddof=0)
        outliers = (abs((s - mu) / sigma) > 3) if sigma and sigma > 0 else pd.Series(False, index=s.index)
        rolling = s.rolling(window=WINDOW_SAMPLES, min_periods=1, center=True).mean()
        df[c + "_clean"] = np.where(outliers, rolling, s)

    clean_cols = [c for c in df.columns if c.endswith("_avg_clean")] or avg_cols
    print(f"🔧 ANALYTICS DEBUG: Clean kolonlar: {clean_cols}")

    # 3) 1s resample + 30s rolling → band ham ortalamaları
    raw_means: Dict[str, float] = {}
    if has_ts and df["TimeStamp"].notna().any():
        tsd = df.set_index("TimeStamp")[clean_cols]
        smooth = tsd.resample("1s").mean().rolling(f"{WINDOW_SECS}s", min_periods=3).mean()
        for c in smooth.columns:
            series = pd.to_numeric(smooth[c], errors="coerce").dropna()
            if series.empty:
                continue
            band = c.replace("_avg_clean", "").replace("_avg", "").capitalize()
            raw_means[band] = float(series.mean())
    else:
        for c in clean_cols:
            band = c.replace("_avg_clean", "").replace("_avg", "").capitalize()
            raw_means[band] = float(pd.to_numeric(df[c], errors="coerce").mean())

    print(f"🔧 ANALYTICS DEBUG: Raw means: {raw_means}")

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

    levels = {b: band_level_text(scores.get(b), b) for b in ["Delta","Theta","Alpha","Beta","Gamma"]}

    return {
        "rows": int(len(df)),
        "duration_sec": None if duration_sec is None else round(duration_sec, 2),
        "raw_means": {k: (None if v is None else round(v, 6)) for k, v in raw_means.items()},
        "dalga_farki": dalga_farki,  # Tek anahtar, her yerde aynı
        "scores": {k: (None if scores.get(k) is None else round(scores.get(k), 2))
                  for k in ["Delta","Theta","Alpha","Beta","Gamma"]},
        "levels": levels,
        "dataframe_with_clean": df
    }

def to_sheet_row(person_name: str, source_file: str, metrics: dict):
    stamp = pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    rm = metrics.get("raw_means", {})
    sc = metrics.get("scores", {})
    lv = metrics.get("levels", {})

    record = {
        "person_name": person_name or "unknown",
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


    def _clean(v):
        return "" if v is None or (isinstance(v, float) and math.isnan(v)) else v

    return [_clean(record.get(col)) for col in HEADERS]

