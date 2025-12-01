import os
import sys
import re
import pandas as pd

# CSV kök dizini
CSV_ROOT = r"/Users/umutkaya/Documents/Zenin Mind Reader/data"
# Run counter file path
RUN_COUNTER_FILE = os.path.join(CSV_ROOT, "run_counter.txt")

def _get_last_run_id() -> int:
    """Son kullanılan run ID'yi oku. Dosya yoksa veya okunamazsa None döner."""
    try:
        if os.path.exists(RUN_COUNTER_FILE):
            with open(RUN_COUNTER_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    # Counter file contains the NEXT id, so subtract 1 to get last used
                    next_id = int(content)
                    return next_id - 1
    except (ValueError, IOError):
        pass
    return None

def find_log(path_arg=None):
    if path_arg:
        return path_arg if os.path.exists(path_arg) else None
    # Try to find the latest processing log by checking counter file
    run_id = _get_last_run_id()
    if run_id:
        log_path = os.path.join(CSV_ROOT, f"processing_log{run_id}.csv")
        if os.path.exists(log_path):
            return log_path
    return None

def normalize_profile_name(name: str) -> str:
    # remove any "(4 uyumlu)" or similar markers and trim
    name = re.sub(r"\(.*?4\s*uyumlu.*?\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"4\s*uyumlu", "", name, flags=re.IGNORECASE)
    return name.strip()

def aggregate_event(df_event, prof_col="en_iyi_profiller"):
    # returns DataFrame with columns: Profile, 5 Uyumlu, 4 Uyumlu, Toplam, Yüzde
    counts_5 = {}
    counts_4 = {}

    total_occurrences = 0
    for val in df_event[prof_col].fillna("").astype(str):
        if not val:
            continue
        parts = [p.strip() for p in val.split(",") if p.strip()]
        for p in parts:
            is_4 = bool(re.search(r"\(.*?4\s*uyumlu.*?\)", p, flags=re.IGNORECASE) or re.search(r"\b4\s*uyumlu\b", p, flags=re.IGNORECASE))
            base = normalize_profile_name(p)
            if not base:
                continue
            if is_4:
                counts_4[base] = counts_4.get(base, 0) + 1
            else:
                counts_5[base] = counts_5.get(base, 0) + 1
            total_occurrences += 1

    profiles = sorted(set(list(counts_5.keys()) + list(counts_4.keys())))
    rows = []
    total_all = sum(counts_5.values()) + sum(counts_4.values())

    # if no profiles found, return empty DataFrame with expected columns
    if not profiles:
        return pd.DataFrame(columns=["Profile", "5 Uyumlu", "4 Uyumlu", "Toplam", "Yüzde"])

    for prof in profiles:
        c5 = counts_5.get(prof, 0)
        c4 = counts_4.get(prof, 0)
        total = c5 + c4
        pct = round((total / total_all * 100) if total_all > 0 else 0.0, 2)
        rows.append({
            "Profile": prof,
            "5 Uyumlu": c5,
            "4 Uyumlu": c4,
            "Toplam": total,
            "Yüzde": pct
        })
    out = pd.DataFrame(rows)
    # ensure Toplam column exists before sorting
    if "Toplam" in out.columns:
        out = out.sort_values("Toplam", ascending=False).reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)
    return out

def compute_dominance_summary(df_all, prof_col="en_iyi_profiller"):
    """
    Yeni: her profile için satır bazlı sınıflandırma yap.
    Satır sınıflandırması: önce 'Baskın Yüksek' var mı -> oysa yüksek; değilse 'Baskın Düşük' var mı -> düşük; aksi halde Normal.
    Eğer bir satırda profile X görünüyorsa, o profile için ilgili sınıfa 1 eklenir.
    Dönen DataFrame columns: Profile, Baskın Yüksek, Baskın Düşük, Normal
    """
    # status sütunu isimleri beklenen hali
    status_cols = ["status_delta","status_theta","status_alpha","status_beta","status_gamma"]
    # normalize column names to existing ones
    existing_status_cols = [c for c in status_cols if c in df_all.columns]
    if not existing_status_cols:
        # try capitalized variants
        existing_status_cols = [c for c in ["status_Delta","status_Theta","status_Alpha","status_Beta","status_Gamma"] if c in df_all.columns]

    # map profile -> counters
    counts = {}
    for _, row in df_all.iterrows():
        profs_raw = (row.get(prof_col, "") or "")
        if not profs_raw:
            continue
        profs = [p.strip() for p in str(profs_raw).split(",") if p.strip()]
        # determine row class
        row_values = [str(row.get(sc,"") or "").lower() for sc in existing_status_cols]
        is_high = any("baskın yüksek" in rv or "baskin yuksek" in rv or "baskınyüksek" in rv or "baskinyuksek" in rv for rv in row_values)
        is_low = any("baskın düşük" in rv or "baskin dusuk" in rv or "baskındüşük" in rv or "baskindusuk" in rv for rv in row_values)
        if is_high:
            cls = "high"
        elif is_low:
            cls = "low"
        else:
            cls = "normal"
        for p in profs:
            name = normalize_profile_name(p)
            if not name:
                continue
            if name not in counts:
                counts[name] = {"high":0, "low":0, "normal":0}
            counts[name][cls] += 1

    rows = []
    for prof, c in sorted(counts.items(), key=lambda x: sum(x[1].values()), reverse=True):
        rows.append({
            "Profile": prof,
            "Baskın Yüksek": c.get("high", 0),
            "Baskın Düşük": c.get("low", 0),
            "Normal": c.get("normal", 0)
        })
    return pd.DataFrame(rows)

def compute_profile_band_stats(df_all, prof_col="en_iyi_profiller"):
    """
    Compute profile-level band statistics including:
    - Profile name
    - Count of 5-match and 4-match occurrences
    - Average score per band (score_delta, score_theta, etc.)
    - Average pct per band (pct_delta, pct_theta, etc.)
    - Average pct_window per band (pct_delta_window, etc.)
    - Mode (most frequent) of each level (level_delta, level_theta, etc.)
    """
    # Count 5-match and 4-match
    counts_5 = {}
    counts_4 = {}
    
    # Initialize band stats accumulators per profile
    profile_rows = {}  # profile -> list of row indices
    
    bands = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
    
    for idx, row in df_all.iterrows():
        profs_raw = (row.get(prof_col, "") or "")
        if not profs_raw:
            continue
        
        parts = [p.strip() for p in str(profs_raw).split(",") if p.strip()]
        
        for p in parts:
            # Check if 4-match
            is_4 = bool(re.search(r"\(.*?4\s*uyumlu.*?\)", p, flags=re.IGNORECASE) or 
                       re.search(r"\b4\s*uyumlu\b", p, flags=re.IGNORECASE))
            base = normalize_profile_name(p)
            if not base:
                continue
            
            # Count matches
            if is_4:
                counts_4[base] = counts_4.get(base, 0) + 1
            else:
                counts_5[base] = counts_5.get(base, 0) + 1
            
            # Store row index for this profile
            if base not in profile_rows:
                profile_rows[base] = []
            profile_rows[base].append(idx)
    
    # Helper function to safely check if column exists
    def col(name):
        return name if name in df_all.columns else None
    
    # Build robust column mappings
    score_cols = {
        "Delta": col("score_delta"),
        "Theta": col("score_theta"),
        "Alpha": col("score_alpha"),
        "Beta":  col("score_beta"),
        "Gamma": col("score_gamma"),
    }
    
    pct_cols = {
        "Delta": col("pct_delta"),
        "Theta": col("pct_theta"),
        "Alpha": col("pct_alpha"),
        "Beta":  col("pct_beta"),
        "Gamma": col("pct_gamma"),
    }
    
    pct_window_cols = {
        "Delta": col("pct_delta_window"),
        "Theta": col("pct_theta_window"),
        "Alpha": col("pct_alpha_window"),
        "Beta":  col("pct_beta_window"),
        "Gamma": col("pct_gamma_window"),
    }
    
    level_cols = {
        "Delta": col("level_delta"),
        "Theta": col("level_theta"),
        "Alpha": col("level_alpha"),
        "Beta":  col("level_beta"),
        "Gamma": col("level_gamma"),
    }
    
    # Build output DataFrame
    results = []
    profiles = sorted(set(list(counts_5.keys()) + list(counts_4.keys())))
    
    for prof in profiles:
        c5 = counts_5.get(prof, 0)
        c4 = counts_4.get(prof, 0)
        
        row_data = {
            "Profile": prof,
            "5_Uyumlu": c5,
            "4_Uyumlu": c4,
            "Toplam": c5 + c4
        }
        
        # Get subset of rows for this profile
        row_indices = profile_rows.get(prof, [])
        if row_indices:
            sub = df_all.loc[row_indices]
            
            # Drop rows where all pct_* are zero or NaN (no usable percentage data)
            pct_cols_list = [pct_cols[b] for b in bands if pct_cols.get(b)]
            if pct_cols_list:
                pct_block = sub[pct_cols_list].apply(pd.to_numeric, errors="coerce").fillna(0.0)
                pct_sum = pct_block.sum(axis=1)
                sub = sub[pct_sum > 0.0]
            
            # If no valid rows remain, skip averaging
            if sub.empty:
                for b in bands:
                    row_data[f"Avg_Score_{b}"] = None
                    row_data[f"Avg_Pct_{b}"] = None
                    row_data[f"Avg_PctWindow_{b}"] = None
                    row_data[f"Mode_Level_{b}"] = None
            else:
                # Add average scores per band
                for b in bands:
                    c = score_cols.get(b)
                    if c and c in sub.columns:
                        vals = pd.to_numeric(sub[c], errors="coerce")
                        row_data[f"Avg_Score_{b}"] = round(float(vals.mean(skipna=True)), 2) if not vals.isna().all() else None
                    else:
                        row_data[f"Avg_Score_{b}"] = None
                
                # Average global pct per band (ignore zeros and NaN)
                for b in bands:
                    c = pct_cols.get(b)
                    key = f"Avg_Pct_{b}"
                    if c and c in sub.columns:
                        vals = pd.to_numeric(sub[c], errors="coerce")
                        vals = vals[vals > 0]  # ignore 0 and NaN
                        row_data[key] = round(float(vals.mean()), 4) if not vals.empty else None
                    else:
                        row_data[key] = None
                
                # Average window-filtered pct per band (ignore zeros and NaN)
                for b in bands:
                    c = pct_window_cols.get(b)
                    key = f"Avg_PctWindow_{b}"
                    if c and c in sub.columns:
                        vals = pd.to_numeric(sub[c], errors="coerce")
                        vals = vals[vals > 0]  # ignore 0 and NaN
                        row_data[key] = round(float(vals.mean()), 4) if not vals.empty else None
                    else:
                        row_data[key] = None
                
                # Add mode (most frequent level) per band
                for b in bands:
                    c = level_cols.get(b)
                    if c and c in sub.columns:
                        levels = sub[c].dropna().astype(str).str.strip()
                        levels = levels[levels != ""]
                        if not levels.empty:
                            from collections import Counter
                            counter = Counter(levels)
                            most_common = counter.most_common(1)[0][0]
                            row_data[f"Mode_Level_{b}"] = most_common
                        else:
                            row_data[f"Mode_Level_{b}"] = None
                    else:
                        row_data[f"Mode_Level_{b}"] = None
        else:
            # No rows for this profile - set all to None
            for b in bands:
                row_data[f"Avg_Score_{b}"] = None
                row_data[f"Avg_Pct_{b}"] = None
                row_data[f"Avg_PctWindow_{b}"] = None
                row_data[f"Mode_Level_{b}"] = None
        
        results.append(row_data)
    
    df_result = pd.DataFrame(results)
    
    # Sort by total occurrences
    if "Toplam" in df_result.columns:
        df_result = df_result.sort_values("Toplam", ascending=False).reset_index(drop=True)
    
    return df_result


def save_multi_sheet(summary_dict, out_path, dominance_df=None, stats_df=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        # write Toplam sheet first if present
        if "Toplam" in summary_dict:
            df_total = summary_dict.pop("Toplam")
            sheet = "Toplam"[:31]
            df_total.to_excel(writer, sheet_name=sheet or "Toplam", index=False)
        # write dominance summary next (if provided)
        if dominance_df is not None:
            sheet = "Dominance"[:31]
            dominance_df.to_excel(writer, sheet_name=sheet or "Dominance", index=False)
        # write ProfileStats sheet (if provided)
        if stats_df is not None:
            sheet = "ProfileStats"[:31]
            stats_df.to_excel(writer, sheet_name=sheet or "ProfileStats", index=False)
        # then write each event
        for event, df in summary_dict.items():
            sheet = str(event).replace("/", "_").replace("\\", "_")[:31]
            df.to_excel(writer, sheet_name=sheet or "event", index=False)
    return out_path

def main(log_arg=None, out_arg=None, run_id_arg=None):
    log_path = find_log(log_arg)
    if not log_path:
        print("processing_log.csv bulunamadı. Yol verin veya log'u varsayılan konumdaki dosyayı oluşturun.")
        sys.exit(1)
    print(f"Log dosyası: {log_path}")

    df = pd.read_csv(log_path, encoding="utf-8", dtype=str).fillna("")
    # detect column name - prefer En_Iyi_Profiller (preserves 4-match tags), fallback to other variants
    prof_col = None
    for c in ["En_Iyi_Profiller", "en_iyi_profiller", "best_profile", "en_iyi_profiler"]:
        if c in df.columns:
            prof_col = c
            break
    if prof_col is None:
        raise RuntimeError("Log dosyasında 'best_profile' veya 'en_iyi_profiller' sütunu bulunamadı.")

    event_col = "event" if "event" in df.columns else None
    if event_col is None:
        # if no event column, treat entire file as single event named 'Toplam'
        event_groups = {"Toplam": df}
    else:
        event_groups = {ev: grp for ev, grp in df.groupby(event_col)}

    summaries = {}
    # build per-event summaries
    for event, group in event_groups.items():
        summaries[event] = aggregate_event(group, prof_col=prof_col)

    # create total summary across all events (Toplam)
    total_df = aggregate_event(df, prof_col=prof_col)
    # compute dominance summary across all rows (single sheet)
    dominance_df = compute_dominance_summary(df, prof_col=prof_col)
    # compute profile band stats
    stats_df = compute_profile_band_stats(df, prof_col=prof_col)

    # ensure Toplam key exists and will be written first, and include dominance sheet
    summaries = {"Toplam": total_df, **{k: v for k, v in summaries.items() if k != "Toplam"}}

    # Use provided run_id or extract from log filename or use counter file
    run_id = run_id_arg
    if run_id is None:
        log_basename = os.path.basename(log_path)
        # Try to match timestamp format like 20251201_014614 or just digits
        match = re.search(r'processing_log([0-9_]+)\.csv', log_basename)
        if match:
            run_id = match.group(1)
        else:
            run_id = _get_last_run_id()
    
    if run_id is None:
        print("⚠️ Run ID belirlenemedi, varsayılan kullanılıyor: 1005")
        run_id = 1005
    
    out_dir = os.path.dirname(log_path) if out_arg is None else out_arg
    out_path = os.path.join(out_dir, f"profile_summary{run_id}.xlsx")
    save_multi_sheet(summaries, out_path, dominance_df=dominance_df, stats_df=stats_df)
    print(f"Özet Excel kaydedildi: {out_path}")

    # Yeni: hızlı analiz için diagnostic script
    print("\n🔧 Hızlı Analiz:")
    total = len(df)
    print(f"Toplam satır: {total}")

    # Check for profile column with case variations - prefer En_Iyi_Profiller (preserves 4-match tags)
    prof_col_name = None
    for possible_name in ["En_Iyi_Profiller", "en_iyi_profiller", "best_profile", "en_iyi_profiler"]:
        if possible_name in df.columns:
            prof_col_name = possible_name
            break
    
    if prof_col_name is None:
        print("⚠️ 'best_profile' veya 'en_iyi_profiller' sütunu bulunmuyor.")
    else:
        col = df[prof_col_name].fillna("").astype(str)
        empty_cnt = (col.str.strip() == "").sum()
        nan_like_cnt = col.str.strip().str.lower().isin(["nan","none","na"]).sum()
        non_empty_cnt = total - empty_cnt
        print(f"{prof_col_name}: boş/'' = {empty_cnt}, nan-like = {nan_like_cnt}, dolu satır = {non_empty_cnt}")

    if "event" in df.columns:
        print("Event dağılımı (ilk 20):")
        print(df["event"].value_counts().head(20))
    else:
        print("event sütunu yok")

    # Only proceed with diagnostic if profile column exists
    if prof_col_name is not None:
        empty_rows = df[col.str.strip() == ""]
        print(f"{prof_col_name} boş satır sayısı: {len(empty_rows)}. İlk {5} örnek:")
        display_cols = ["event", "person_name", "source_file", prof_col_name]
        available_cols = [c for c in display_cols if c in df.columns]
        if available_cols:
            print(empty_rows.head(5)[available_cols])

        print(f"{prof_col_name} dolu örnekler (ilk {5}):")
        if available_cols:
            print(df[col.str.strip() != ""].head(5)[available_cols])

        # Kontrol: farklı türde NaN/None stringlerinin varlığı
        print(f"{prof_col_name} unique örnekleri (örnek 50):")
        print(df[prof_col_name].dropna().astype(str).unique()[:50])

    return 0

if __name__ == "__main__":
    arg1 = sys.argv[1] if len(sys.argv) > 1 else None
    arg2 = sys.argv[2] if len(sys.argv) > 2 else None
    main(arg1, arg2)

