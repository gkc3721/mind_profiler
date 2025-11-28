import os
import csv
import time
import re
import math
import pandas as pd
import numpy as np
from analytics5 import compute_mail_csv_metrics, to_sheet_row
from profile_analyzer5 import analyze_profiles_from_metrics
from zenin_plot_generator import generate_eeg_plots

# CSV kök dizini: data içindeki etkinlik klasörleri
CSV_ROOT = r"/Users/umutkaya/Documents/Zenin Mind Reader/data"
# Run counter file path
RUN_COUNTER_FILE = os.path.join(CSV_ROOT, "run_counter.txt")
# Unmatched profiles directory
UNMATCHED_DATA_DIR = os.path.join(CSV_ROOT, "UNMATCHED_DATA")
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

def _append_log_row(row: dict, log_path: str):
    """Log CSV'ye satır ekle (header yoksa oluştur). Event sütunu eklendi."""
    headers = [
        "event", "person_name", "en_iyi_profiller",
        "level_delta","level_theta","level_alpha","level_beta","level_gamma",
        "status_delta","status_theta","status_alpha","status_beta","status_gamma",
        "score_delta","score_theta","score_alpha","score_beta","score_gamma",
        "dalga_farki","source_file","processed_at_utc"
    ]
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    write_header = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if write_header:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in headers})

def _unmatched_row_key(row: dict):
    """Unmatched log satırları için benzersiz anahtar üret."""
    key = []
    for col in UNMATCHED_KEY_COLS:
        key.append(((row.get(col, "") or "")).strip())
    return tuple(key)

def _append_unmatched_log_row(row: dict, run_id: int):
    """Unmatched profiller için Excel ve CSV log dosyalarına satır ekle."""
    os.makedirs(UNMATCHED_DATA_DIR, exist_ok=True)
    log_xlsx = os.path.join(UNMATCHED_DATA_DIR, f"unmatched_profiles_log{run_id}.xlsx")
    log_csv = os.path.join(UNMATCHED_DATA_DIR, f"unmatched_profiles_log{run_id}.csv")
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

def _build_plot_key(csv_path: str, event: str) -> str:
    """Grafik çıktısı için eşsiz bir isim üretir."""
    rel_path = os.path.relpath(csv_path, CSV_ROOT)
    safe_event = (event or "root").replace(os.sep, "__")
    safe_rel = re.sub(r"[\\/]+", "__", rel_path)
    return f"{safe_event}__{safe_rel}"

def main():
	# Get and increment run ID at the start
	run_id = _get_and_increment_run_id()
	print(f"🔄 Run ID: {run_id}")
	
	# Set up log paths with run_id
	log_path = os.path.join(CSV_ROOT, f"processing_log{run_id}.csv")
	
	unmatched_total = 0
	processed_files = set()
	# Walk CSV_ROOT and process all csv files under subfolders (skip 'graphs' folders and the log file)
	for root, dirs, files in os.walk(CSV_ROOT):
		# prevent descending into graphs/unmatched_data folders altogether
		dirs[:] = [d for d in dirs if d.lower() not in {"graphs", "unmatched_data"}]
		if os.path.basename(root).lower() in {"graphs", "unmatched_data"}:
			continue

		# collect csv files but skip the central log file if present
		csv_files = [f for f in files if f.lower().endswith('.csv') and f != os.path.basename(log_path)]
		if not csv_files:
			continue

		# Determine event name as path relative to CSV_ROOT (use "." -> root_event)
		event = os.path.relpath(root, CSV_ROOT)
		if event == ".":
			event = "root"

		# prepare event-specific graph output dir
		event_graph_dir = os.path.join(root, "graphs")
		os.makedirs(event_graph_dir, exist_ok=True)

		print(f"Etkinlik: {event} -> bulunan CSV'ler: {csv_files}")

		for csv_file in csv_files:
			csv_path = os.path.join(root, csv_file)
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

			metrics = compute_mail_csv_metrics(df)

			# Debug: metrics içeriğini göster (özellikle scores/levels/raw_means)
			print(f"🔧 METRICS DEBUG for {csv_file}: raw_means={metrics.get('raw_means')}")
			print(f"🔧 METRICS DEBUG for {csv_file}: scores={metrics.get('scores')}")
			print(f"🔧 METRICS DEBUG for {csv_file}: levels={metrics.get('levels')}")

			# safe profile analysis (ensure returns dict with expected keys)
			try:
				profile_data = analyze_profiles_from_metrics(csv_file, metrics) or {}
			except Exception as e:
				print(f"⚠️ Profil analiz hatası for {csv_file}: {e}")
				profile_data = {}

			# Debug: analyze sonucu
			print(f"🔧 PROFILE ANALYZE DEBUG for {csv_file}: profile_data={profile_data}")

			# merge metrics
			metrics.update(profile_data)

			# Debug: atanan profil(ler)i hemen göster
			print(f"🔧 DEBUG - Assigned profile(s): {metrics.get('en_iyi_profiller', '')}")
			
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
				if (top_val - second_top_val) >= DOMINANCE_DELTA:
					dominance[top_band] = "Baskın Yüksek"
				asc = sorted(vals, key=lambda x: x[1])
				bot_band, bot_val = asc[0]
				second_bot_val = asc[1][1]
				if (second_bot_val - bot_val) >= DOMINANCE_DELTA:
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
			
			# print metrics for debug
			print("Analiz Sonuçları:")
			for k, v in metrics.items():
				if k != "dataframe_with_clean":
					print(f"  {k}: {v}")

			# prepare log row (include event) — use consistent key "en_iyi_profiller"
			person_name = os.path.splitext(csv_file)[0]
			levels = metrics.get("levels", {}) or {}
			lvl = {b: ((levels.get(b,"") or "").strip("-")) for b in ["Delta","Theta","Alpha","Beta","Gamma"]}
			sc_map = metrics.get("scores", {}) or {}
			raw_means = metrics.get("raw_means", {}) or {}
			def fmt_score(band):
				v = sc_map.get(band)
				try:
					if v is None or pd.isna(v):
						return ""
					fv = float(v)
					if math.isinf(fv):
						return ""
					return round(fv, 2)
				except Exception:
					return ""
			def fmt_raw(band):
				v = raw_means.get(band)
				try:
					if v is None or pd.isna(v):
						return ""
					fv = float(v)
					if math.isinf(fv):
						return ""
					return round(fv, 6)
				except Exception:
					return ""
			log_row = {
				"event": event,
				"person_name": person_name,
				"en_iyi_profiller": metrics.get("en_iyi_profiller", "") or "",
				"level_delta": lvl.get("Delta",""),
				"level_theta": lvl.get("Theta",""),
				"level_alpha": lvl.get("Alpha",""),
				"level_beta": lvl.get("Beta",""),
				"level_gamma": lvl.get("Gamma",""),
				"status_delta": dominance.get("Delta","normal"),
				"status_theta": dominance.get("Theta","normal"),
				"status_alpha": dominance.get("Alpha","normal"),
				"status_beta": dominance.get("Beta","normal"),
				"status_gamma": dominance.get("Gamma","normal"),
				"score_delta": fmt_score("Delta"),
				"score_theta": fmt_score("Theta"),
				"score_alpha": fmt_score("Alpha"),
				"score_beta": fmt_score("Beta"),
				"score_gamma": fmt_score("Gamma"),
				"dalga_farki": metrics.get("dalga_farki",""),
				"source_file": csv_file,
				"processed_at_utc": pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M:%S')
			}
			log_row.update({
				"tam_uyumlu_profiller": metrics.get("tam_uyumlu_profiller", ""),
				"en_iyi_puan": metrics.get("en_iyi_puan", ""),
				"controlled_mean": metrics.get("controlled_mean", ""),
				"controlled_label": metrics.get("controlled_label", ""),
				"raw_mean_delta": fmt_raw("Delta"),
				"raw_mean_theta": fmt_raw("Theta"),
				"raw_mean_alpha": fmt_raw("Alpha"),
				"raw_mean_beta": fmt_raw("Beta"),
				"raw_mean_gamma": fmt_raw("Gamma")
			})
			
			# Conditional routing based on profile match status
			if is_unmatched:
				unmatched_total += 1
				# Unmatched: route to UNMATCHED_DATA
				print(f"⚠️ Profil eşleşmesi bulunamadı: {csv_file} -> UNMATCHED_DATA'ya yönlendiriliyor")
				
				# Create UNMATCHED_DATA/graphs directory structure
				unmatched_graph_dir = os.path.join(UNMATCHED_DATA_DIR, "graphs")
				os.makedirs(unmatched_graph_dir, exist_ok=True)
				
				# Write to unmatched Excel log
				_append_unmatched_log_row(log_row, run_id)
				
				# Generate plot in UNMATCHED_DATA/graphs
				if "dataframe_with_clean" in metrics:
					df_for_plot = metrics["dataframe_with_clean"]
				else:
					df_for_plot = df
				
				plot_key = _build_plot_key(csv_path, event)
				try:
					plot_files = generate_eeg_plots(
						dfs={plot_key: df_for_plot},
						metrics_map={plot_key: metrics},
						balance_diff_map={plot_key: metrics.get("dalga_farki", 0)},
						best_profile_map={plot_key: metrics.get("en_iyi_profiller", "")},
						output_dir=unmatched_graph_dir
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
					output_dir=event_graph_dir
				)
				print(f"Oluşan grafik(ler): {plot_files}")

			processed_files.add(norm_csv_path)

	print(f"Toplam eşleşmeyen profil sayısı: {unmatched_total}")

if __name__ == "__main__":
	main()
