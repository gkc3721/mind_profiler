import os
import csv
import time
import re
import math
import pandas as pd
import numpy as np
from analytics5 import compute_mail_csv_metrics, to_sheet_row, HEADERS
from profile_analyzer5 import analyze_profiles_from_metrics
from zenin_plot_generator import generate_eeg_plots

# CSV kök dizini: data içindeki etkinlik klasörleri
CSV_ROOT = r"/Users/umutkaya/Documents/Zenin Mind Reader/data"
# Run counter file path
RUN_COUNTER_FILE = os.path.join(CSV_ROOT, "run_counter.txt")
# Unmatched profiles directory (will be set per-run in process_pipeline)
UNMATCHED_DATA_DIR = None  # Will be set dynamically
UNMATCHED_LOG_HEADERS = [
    "event", "person_name", "source_file",
    "en_iyi_profiller", "tam_uyumlu_profiller", "en_iyi_puan",
    "level_delta","level_theta","level_alpha","level_beta","level_gamma",
    "status_delta","status_theta","status_alpha","status_beta","status_gamma",
    "score_delta","score_theta","score_alpha","score_beta","score_gamma",
    "raw_mean_delta","raw_mean_theta","raw_mean_alpha","raw_mean_beta","raw_mean_gamma",
    "dalga_farki","controlled_mean","controlled_label",
    "processed_at_utc"
]
UNMATCHED_KEY_COLS = ("event", "person_name", "source_file")

# DOMINANCE_DELTA sabiti
DOMINANCE_DELTA = 29.0

def _get_and_increment_run_id() -> int:
    """Run ID'yi oku, artır ve kaydet. İlk çalışmada 1005 döner."""
    default_id = 1005
    try:
        if os.path.exists(RUN_COUNTER_FILE):
            with open(RUN_COUNTER_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    current_id = int(content)
                else:
                    current_id = default_id
        else:
            current_id = default_id
    except (ValueError, IOError) as e:
        print(f"⚠️ Run counter okunamadı, varsayılan kullanılıyor: {e}")
        current_id = default_id
    
    # Next ID'yi kaydet
    next_id = current_id + 1
    try:
        os.makedirs(os.path.dirname(RUN_COUNTER_FILE), exist_ok=True)
        with open(RUN_COUNTER_FILE, "w", encoding="utf-8") as f:
            f.write(str(next_id))
    except IOError as e:
        print(f"⚠️ Run counter yazılamadı: {e}")
    
    return current_id

def _norm_tr_simple(s: str) -> str:
    s = s or ""
    s = s.strip().lower()
    # temel TR normalizasyonu
    s = (s.replace("ı", "i")
           .replace("ş", "s").replace("ş", "s")
           .replace("ğ", "g")
           .replace("ö", "o")
           .replace("ç", "c")
           .replace("ü", "u"))
    s = re.sub(r"\s+", " ", s)
    return s

def _append_log_row(row: list, log_path: str):
    """Log CSV'ye satır ekle (header yoksa oluştur). Event sütunu eklendi.
    
    Args:
        row: List of values in order: [event] + HEADERS values from to_sheet_row()
        log_path: Path to the CSV log file
    """
    # LOG_HEADERS = ["event"] + status columns + HEADERS
    # Status columns are computed in zenin_mac2.py and need to be preserved
    status_cols = ["status_delta", "status_theta", "status_alpha", "status_beta", "status_gamma"]
    LOG_HEADERS = ["event"] + status_cols + HEADERS
    
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    write_header = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(LOG_HEADERS)
        # row should be a list: [event, status_delta, status_theta, ..., ...HEADERS values...]
        writer.writerow(row)

def _unmatched_row_key(row: dict):
    """Unmatched log satırları için benzersiz anahtar üret."""
    key = []
    for col in UNMATCHED_KEY_COLS:
        key.append(((row.get(col, "") or "")).strip())
    return tuple(key)

def _append_unmatched_log_row(row: dict, run_id: int, unmatched_dir: str = None):
    """Unmatched profiller için Excel ve CSV log dosyalarına satır ekle."""
    unmatched_data_dir = unmatched_dir if unmatched_dir else UNMATCHED_DATA_DIR
    if unmatched_data_dir is None:
        unmatched_data_dir = os.path.join(CSV_ROOT, "UNMATCHED_DATA")
    os.makedirs(unmatched_data_dir, exist_ok=True)
    log_xlsx = os.path.join(unmatched_data_dir, f"unmatched_profiles_log{run_id}.xlsx")
    log_csv = os.path.join(unmatched_data_dir, f"unmatched_profiles_log{run_id}.csv")
    data_row = {k: row.get(k, "") for k in UNMATCHED_LOG_HEADERS}
    row_key = _unmatched_row_key(data_row)

    # Excel append (read + rewrite to preserve formatting)
    try:
        if os.path.exists(log_xlsx):
            try:
                df_existing = pd.read_excel(log_xlsx, engine="openpyxl")
            except Exception as e:
                print(f"⚠️ Unmatched log (xlsx) okunamadı, CSV denenecek: {e}")
                df_existing = pd.DataFrame(columns=UNMATCHED_LOG_HEADERS)
        elif os.path.exists(log_csv):
            try:
                df_existing = pd.read_csv(log_csv, encoding="utf-8")
            except Exception as e:
                print(f"⚠️ Unmatched log (csv) okunamadı, yeni dosya oluşturulacak: {e}")
                df_existing = pd.DataFrame(columns=UNMATCHED_LOG_HEADERS)
        else:
            df_existing = pd.DataFrame(columns=UNMATCHED_LOG_HEADERS)

        if df_existing.empty:
            existing_keys = set()
        else:
            # ensure missing columns exist
            for col in UNMATCHED_LOG_HEADERS:
                if col not in df_existing.columns:
                    df_existing[col] = ""
            existing_keys = set(
                tuple((str(df_existing.at[idx, col]) if col in df_existing else "").strip()
                      for col in UNMATCHED_KEY_COLS)
                for idx in df_existing.index
            )
        if row_key in existing_keys:
            print(f"ℹ️ Unmatched log satırı zaten mevcut (event={row.get('event')}, person={row.get('person_name')}, file={row.get('source_file')}). Atlanıyor.")
            return

        df_new = pd.DataFrame([data_row])
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(log_xlsx, index=False, engine="openpyxl")
        df_combined.to_csv(log_csv, index=False, encoding="utf-8")
    except Exception as e:
        print(f"❌ Unmatched Excel log yazma hatası: {e}")
        import traceback
        traceback.print_exc()

    print(f"✅ Unmatched profil log'a eklendi: {row.get('person_name', 'unknown')}")

def _build_plot_key(csv_path: str, event: str, csv_root: str = None) -> str:
    """Grafik çıktısı için eşsiz bir isim üretir."""
    root = csv_root if csv_root is not None else CSV_ROOT
    try:
        rel_path = os.path.relpath(csv_path, root)
    except ValueError:
        # If paths are on different drives, use basename
        rel_path = os.path.basename(csv_path)
    safe_event = (event or "root").replace(os.sep, "__")
    safe_rel = re.sub(r"[\\/]+", "__", rel_path)
    return f"{safe_event}__{safe_rel}"

def process_pipeline(
    csv_root: str = None,
    run_id: str = None,
    output_dir: str = None,
    profile_csv_path: str = None,
    dominance_delta: float = None,
    balance_threshold: float = None,
    denge_mean_threshold: float = None,
    window_secs: int = None,
    window_samples: int = None,
    band_thresholds: dict = None
) -> dict:
    """
    Process EEG pipeline with configurable parameters.
    
    Args:
        csv_root: Root directory to scan for CSV files (default: CSV_ROOT)
        run_id: Run identifier (default: auto-generated)
        output_dir: Directory for outputs (default: csv_root)
        profile_csv_path: Path to profile CSV file (default: PROFILES_FILE from profile_analyzer5)
        dominance_delta: Dominance threshold (default: DOMINANCE_DELTA)
        balance_threshold: Balance threshold (default: from profile_analyzer5)
        denge_mean_threshold: Denge mean threshold (default: from profile_analyzer5)
        window_secs: Window seconds for rolling (default: from analytics5)
        window_samples: Window samples for outlier cleaning (default: from analytics5)
        band_thresholds: Band thresholds dict (default: from analytics5)
    
    Returns:
        dict with keys: processed_files, matched_count, unmatched_count, log_path
    """
    # Use provided values or defaults
    root = csv_root if csv_root is not None else CSV_ROOT
    rid = run_id if run_id is not None else str(_get_and_increment_run_id())
    out_dir = output_dir if output_dir is not None else root
    
    # Convert band_thresholds from Pydantic models to dict format if needed
    band_thresh_dict = None
    if band_thresholds:
        band_thresh_dict = {}
        for band, thresh in band_thresholds.items():
            if hasattr(thresh, 'model_dump'):  # Pydantic model
                band_thresh_dict[band] = {
                    "yüksek": thresh.yuksek,
                    "yüksek orta": thresh.yuksek_orta,
                    "orta": thresh.orta,
                    "düşük orta": thresh.dusuk_orta
                }
            else:  # Already a dict
                band_thresh_dict[band] = thresh
    
    print(f"🔄 Run ID: {rid}")
    
    # Set up log paths with run_id
    log_path = os.path.join(out_dir, f"processing_log{rid}.csv")
	
    unmatched_total = 0
    matched_total = 0
    processed_files = set()
    # Walk root and process all csv files under subfolders (skip 'graphs' folders and the log file)
    for walk_root, dirs, files in os.walk(root):
        # prevent descending into graphs/unmatched_data folders altogether
        dirs[:] = [d for d in dirs if d.lower() not in {"graphs", "unmatched_data"}]
        if os.path.basename(walk_root).lower() in {"graphs", "unmatched_data"}:
            continue

        # collect csv files but skip the central log file if present
        csv_files = [f for f in files if f.lower().endswith('.csv') and f != os.path.basename(log_path)]
        if not csv_files:
            continue

        # Determine event name as path relative to root (use "." -> root_event)
        event = os.path.relpath(walk_root, root)
        if event == ".":
            event = "root"

        # prepare event-specific graph output dir
        event_graph_dir = os.path.join(walk_root, "graphs")
        os.makedirs(event_graph_dir, exist_ok=True)

        print(f"Etkinlik: {event} -> bulunan CSV'ler: {csv_files}")

        for csv_file in csv_files:
            csv_path = os.path.join(walk_root, csv_file)
            norm_csv_path = os.path.normpath(os.path.realpath(csv_path))
            if norm_csv_path in processed_files:
                print(f"⏭️  {csv_path} daha önce işlendi, atlanıyor.")
                continue
            print(f"\n--- [{event}] {csv_file} işleniyor ---")
            # read CSV safely
            try:
                df = pd.read_csv(csv_path, encoding="utf-8")
            except Exception:
                try:
                    df = pd.read_csv(csv_path, encoding="cp1254")
                except Exception as e:
                    print(f"❌ CSV okunamadı: {csv_path} -> {e}")
                    continue

            # Replace infinity values with NaN before processing
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            inf_count = 0
            for col in numeric_cols:
                inf_mask = np.isinf(df[col])
                if inf_mask.any():
                    inf_count += inf_mask.sum()
                    df.loc[inf_mask, col] = np.nan
            if inf_count > 0:
                print(f"⚠️ {inf_count} infinity değeri tespit edildi ve NaN ile değiştirildi: {csv_file}")

            # Call compute_mail_csv_metrics with parameters
            metrics = compute_mail_csv_metrics(
                df,
                band_thresholds=band_thresh_dict,
                window_secs=window_secs,
                window_samples=window_samples
            )

            # Debug: metrics içeriğini göster (özellikle scores/levels/raw_means)
            print(f"🔧 METRICS DEBUG for {csv_file}: raw_means={metrics.get('raw_means')}")
            print(f"🔧 METRICS DEBUG for {csv_file}: scores={metrics.get('scores')}")
            print(f"🔧 METRICS DEBUG for {csv_file}: levels={metrics.get('levels')}")

            # safe profile analysis (ensure returns dict with expected keys)
            try:
                profile_data = analyze_profiles_from_metrics(
                    csv_file,
                    metrics,
                    profile_csv_path=profile_csv_path,
                    balance_threshold=balance_threshold,
                    denge_mean_threshold=denge_mean_threshold
                ) or {}
            except Exception as e:
                print(f"⚠️ Profil analiz hatası for {csv_file}: {e}")
                profile_data = {}

            # Debug: analyze sonucu - enhanced
            print(f"🔧 PROFILE ANALYZE DEBUG for {csv_file}:")
            print(f"   profile_data keys: {list(profile_data.keys()) if profile_data else 'EMPTY'}")
            print(f"   profile_data full: {profile_data}")
            print(f"   en_iyi_profiller value: '{profile_data.get('en_iyi_profiller', 'MISSING')}'")
            print(f"   tam_uyumlu_profiller value: '{profile_data.get('tam_uyumlu_profiller', 'MISSING')}'")
            print(f"   en_iyi_puan value: {profile_data.get('en_iyi_puan', 'MISSING')}")

            # merge metrics
            metrics.update(profile_data)

            # Debug: atanan profil(ler)i hemen göster - enhanced
            assigned_profiles = metrics.get('en_iyi_profiller', '')
            if assigned_profiles and assigned_profiles.strip():
                print(f"✅ DEBUG - Assigned profile(s): '{assigned_profiles}'")
            else:
                print(f"⚠️ DEBUG - NO PROFILE ASSIGNED! Value is empty or None: '{assigned_profiles}'")
                print(f"   Available metrics keys: {[k for k in metrics.keys() if 'profil' in k.lower() or 'profile' in k.lower()]}")
            
            # Use provided dominance_delta or default
            dom_delta = dominance_delta if dominance_delta is not None else DOMINANCE_DELTA
            
            # dominance (scores üzerinden) hesapla (sağlam kontrol)
            scores_map = metrics.get("scores", {}) or {}
            vals = []
            for b in ["Delta","Theta","Alpha","Beta","Gamma"]:
                v = scores_map.get(b)
                try:
                    fv = float(v)
                    if not pd.isna(fv) and not math.isinf(fv):
                        vals.append((b, fv))
                except Exception:
                    continue

            dominance = {b: "normal" for b in ["Delta","Theta","Alpha","Beta","Gamma"]}
            if len(vals) >= 2:
                desc = sorted(vals, key=lambda x: x[1], reverse=True)
                top_band, top_val = desc[0]
                second_top_val = desc[1][1]
                if (top_val - second_top_val) >= dom_delta:
                    dominance[top_band] = "Baskın Yüksek"
                asc = sorted(vals, key=lambda x: x[1])
                bot_band, bot_val = asc[0]
                second_bot_val = asc[1][1]
                if (second_bot_val - bot_val) >= dom_delta:
                    dominance[bot_band] = "Baskın Düşük"

            # --- ÖZEL: HUZUR ODAKLI YAŞAYAN -> ZİHİN YOLCUSU BASKIN DÜŞÜK ataması (güçlendirilmiş kontrol) ---

            try:
                current_profiles = metrics.get("en_iyi_profiller", "").strip()
                dom_gamma = dominance.get("Gamma", "")
                
                print(f"🔧 RENAME DEBUG: current_profiles='{current_profiles}'")
                print(f"🔧 RENAME DEBUG: dom_gamma='{dom_gamma}'")
                
                # Gamma "Baskın Düşük" ise ve profilde "HUZUR ODAKLI YAŞAYAN" varsa ama "BASKIN DÜŞÜK" yoksa değiştir
                if (dom_gamma == "Baskın Düşük" and 
                    "HUZUR ODAKLI YAŞAYAN" in current_profiles and 
                    "BASKIN DÜŞÜK" not in current_profiles):
                    
                    new_profiles = current_profiles.replace("HUZUR ODAKLI YAŞAYAN", "ZİHİN YOLCUSU")
                    metrics["en_iyi_profiller"] = new_profiles
                    print(f"✅ RENAME APPLIED: '{current_profiles}' -> '{new_profiles}'")
                else:
                    print(f"ℹ️ RENAME SKIPPED: Koşul sağlanmadı")
                    
            except Exception as e:
                print(f"⚠️ RENAME ERROR: {e}")
			
            # Check if profile match was found (after all profile modifications)
            is_unmatched = not (metrics.get("en_iyi_profiller", "") or "").strip()
            
            if not is_unmatched:
                matched_total += 1
            
            # print metrics for debug
            print("Analiz Sonuçları:")
            for k, v in metrics.items():
                if k != "dataframe_with_clean":
                    print(f"  {k}: {v}")

            # prepare log row using to_sheet_row from analytics5
            person_name = os.path.splitext(csv_file)[0]
            
            # Get properly formatted row from analytics5.to_sheet_row (includes all pct_* columns)
            sheet_row = to_sheet_row(person_name, csv_path, metrics)
            
            # Build status columns list
            status_values = [
                dominance.get("Delta", "normal"),
                dominance.get("Theta", "normal"),
                dominance.get("Alpha", "normal"),
                dominance.get("Beta", "normal"),
                dominance.get("Gamma", "normal")
            ]
            
            # Combine: [event] + [status columns] + [HEADERS values from to_sheet_row]
            log_row = [event] + status_values + sheet_row
            
            # For unmatched profiles, also create a dict version (UNMATCHED_LOG_HEADERS format)
            # Map sheet_row values to a dict using HEADERS order
            sheet_row_dict = dict(zip(HEADERS, sheet_row))
            unmatched_log_row = {
                "event": event,
                "person_name": person_name,
                "source_file": csv_file,
                "en_iyi_profiller": metrics.get("en_iyi_profiller", "") or "",
                "tam_uyumlu_profiller": metrics.get("tam_uyumlu_profiller", ""),
                "en_iyi_puan": metrics.get("en_iyi_puan", ""),
                "level_delta": sheet_row_dict.get("level_delta", ""),
                "level_theta": sheet_row_dict.get("level_theta", ""),
                "level_alpha": sheet_row_dict.get("level_alpha", ""),
                "level_beta": sheet_row_dict.get("level_beta", ""),
                "level_gamma": sheet_row_dict.get("level_gamma", ""),
                "status_delta": status_values[0],
                "status_theta": status_values[1],
                "status_alpha": status_values[2],
                "status_beta": status_values[3],
                "status_gamma": status_values[4],
                "score_delta": sheet_row_dict.get("score_delta", ""),
                "score_theta": sheet_row_dict.get("score_theta", ""),
                "score_alpha": sheet_row_dict.get("score_alpha", ""),
                "score_beta": sheet_row_dict.get("score_beta", ""),
                "score_gamma": sheet_row_dict.get("score_gamma", ""),
                "raw_mean_delta": sheet_row_dict.get("raw_mean_delta", ""),
                "raw_mean_theta": sheet_row_dict.get("raw_mean_theta", ""),
                "raw_mean_alpha": sheet_row_dict.get("raw_mean_alpha", ""),
                "raw_mean_beta": sheet_row_dict.get("raw_mean_beta", ""),
                "raw_mean_gamma": sheet_row_dict.get("raw_mean_gamma", ""),
                "dalga_farki": metrics.get("dalga_farki", ""),
                "controlled_mean": metrics.get("controlled_mean", ""),
                "controlled_label": metrics.get("controlled_label", ""),
                "processed_at_utc": sheet_row_dict.get("processed_at_utc", "")
            }
            
            # Conditional routing based on profile match status
            if is_unmatched:
                unmatched_total += 1
                # Unmatched: route to UNMATCHED_DATA
                print(f"⚠️ Profil eşleşmesi bulunamadı: {csv_file} -> UNMATCHED_DATA'ya yönlendiriliyor")
                
                # Create UNMATCHED_DATA/graphs directory structure
                unmatched_graph_dir = os.path.join(out_dir, "UNMATCHED_DATA", "graphs")
                os.makedirs(unmatched_graph_dir, exist_ok=True)
                
                # Write to unmatched Excel log (uses dict format)
                unmatched_data_dir = os.path.join(out_dir, "UNMATCHED_DATA")
                _append_unmatched_log_row(unmatched_log_row, int(rid) if rid.isdigit() else 1005, unmatched_data_dir)
                
                # Generate plot in UNMATCHED_DATA/graphs
                if "dataframe_with_clean" in metrics:
                    df_for_plot = metrics["dataframe_with_clean"]
                else:
                    df_for_plot = df
                
                plot_key = _build_plot_key(csv_path, event, root)
                try:
                    plot_files = generate_eeg_plots(
                        dfs={plot_key: df_for_plot},
                        metrics_map={plot_key: metrics},
                        balance_diff_map={plot_key: metrics.get("dalga_farki", 0)},
                        best_profile_map={plot_key: metrics.get("en_iyi_profiller", "")},
                        output_dir=unmatched_graph_dir,
                        balance_threshold=balance_threshold,
                        dominance_delta=dom_delta,
                        window_secs=window_secs
                    )
                except Exception as plot_err:
                    print(f"❌ Unmatched grafik üretilemedi ({csv_file}): {plot_err}")
                    import traceback
                    traceback.print_exc()
                    plot_files = []
                print(f"Unmatched grafik(ler) kaydedildi: {plot_files}")
            else:
                # Matched: continue with existing logic
                # Write to main log
                _append_log_row(log_row, log_path)
                
                # Grafik oluştur ve event_graph_dir içine kaydet
                if "dataframe_with_clean" in metrics:
                    df_for_plot = metrics["dataframe_with_clean"]
                else:
                    df_for_plot = df
                
                plot_files = generate_eeg_plots(
                    dfs={csv_file: df_for_plot},
                    metrics_map={csv_file: metrics},
                    balance_diff_map={csv_file: metrics.get("dalga_farki", 0)},
                    best_profile_map={csv_file: metrics.get("en_iyi_profiller", "")},
                    output_dir=event_graph_dir,
                    balance_threshold=balance_threshold,
                    dominance_delta=dom_delta,
                    window_secs=window_secs
                )
                print(f"Oluşan grafik(ler): {plot_files}")

            processed_files.add(norm_csv_path)

    print(f"Toplam eşleşmeyen profil sayısı: {unmatched_total}")
    
    return {
        "processed_files": len(processed_files),
        "matched_count": matched_total,
        "unmatched_count": unmatched_total,
        "log_path": log_path
    }


def main():
    """Original main function - calls process_pipeline with defaults"""
    result = process_pipeline()
    print(f"✅ Pipeline completed: {result}")

if __name__ == "__main__":
    main()
