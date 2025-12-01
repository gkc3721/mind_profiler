# plot_generator2.py

import os
import numpy as np
import pandas as pd
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from analytics5 import BAND_THRESHOLDS

    # Parametreler (defaults, can be overridden)
WINDOW_SECS = 30
BALANCE_THRESHOLD = 22.0 # Bu değeri profile_analyzer2.py ile aynı yapın
DOMINANCE_DELTA = 29.0   # Grafik için skor bazlı baskın eşik (puan cinsinden)

BAND_COLORS = {
    "Delta": "red", "Theta": "purple", "Alpha": "blue", 
    "Beta": "green", "Gamma": "orange"
}

# --- ANA FONKSİYONU GÜNCELLE ---
def generate_eeg_plots(dfs, metrics_map=None, balance_diff_map=None, best_profile_map=None, output_dir="eeg_plots", balance_threshold=None, dominance_delta=None, window_secs=None):
    print(f"🔧 PLOT DEBUG: generate_eeg_plots çağrıldı")
    
    # Use provided parameters or defaults
    win_secs = window_secs if window_secs is not None else WINDOW_SECS
    bal_thresh = balance_threshold if balance_threshold is not None else BALANCE_THRESHOLD
    dom_delta = dominance_delta if dominance_delta is not None else DOMINANCE_DELTA
    
    os.makedirs(output_dir, exist_ok=True)
    plot_files = []
    
    # Varsayılan boş sözlükler
    if metrics_map is None: metrics_map = {}
    if balance_diff_map is None: balance_diff_map = {}
    if best_profile_map is None: best_profile_map = {}
    
    for name, df in dfs.items():
        print(f"🔧 PLOT DEBUG: {name} işleniyor...")
        
        try:
            if df is None or df.empty:
                print(f"❌ PLOT DEBUG: {name} DataFrame boş")
                continue
                
            # İlgili CSV için analytics metriklerini al
            current_metrics = metrics_map.get(name, {})
            scores = current_metrics.get("scores", {}) or {}
            levels = current_metrics.get("levels", {}) or {}

            # --- YENİ: scores'tan baskın tespiti (sadece görsel; metrikleri değiştirme) ---
            dominance = {}
            vals = []
            # scores genelde 0-100 aralığında, None/NaN olabilir
            for b, v in scores.items():
                try:
                    fv = float(v)
                    if not (math.isnan(fv) or math.isinf(fv)):
                        vals.append((b, fv))
                except Exception:
                    continue

            # DEBUG: scores ve toplanan vals
            print(f"🔧 DEBUG dominance (scores): scores={scores}")
            print(f"🔧 DEBUG dominance (scores): vals(before sort)={vals}")

            if len(vals) >= 2:
                desc = sorted(vals, key=lambda x: x[1], reverse=True)
                print(f"🔧 DEBUG dominance (scores): desc={desc}")
                top_band, top_val = desc[0]
                second_top_val = desc[1][1]
                top_diff = top_val - second_top_val
                print(f"🔧 DEBUG dominance (scores): top={top_band}({top_val}), second={second_top_val}, diff={top_diff}")
                if top_diff >= dom_delta:
                    dominance[top_band] = "Baskın Yüksek"

                asc = sorted(vals, key=lambda x: x[1])
                print(f"🔧 DEBUG dominance (scores): asc={asc}")
                bot_band, bot_val = asc[0]
                second_bot_val = asc[1][1]
                bot_diff = second_bot_val - bot_val
                print(f"🔧 DEBUG dominance (scores): bot={bot_band}({bot_val}), second={second_bot_val}, diff={bot_diff}")
                if bot_diff >= dom_delta:
                    dominance[bot_band] = "Baskın Düşük"

            # DEBUG: final dominance
            print(f"🔧 DEBUG dominance (scores): computed dominance={dominance}")

            # --- YENİ: output içindeki alt klasörleri hazırla (dominant / normal) ---
            dominant_dir = os.path.join(output_dir, "dominant")
            normal_dir = os.path.join(output_dir, "normal")
            os.makedirs(dominant_dir, exist_ok=True)
            os.makedirs(normal_dir, exist_ok=True)
            
            if "TimeStamp" not in df.columns:
                print(f"❌ PLOT DEBUG: {name} TimeStamp sütunu yok")
                continue

            df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")
            df = df.dropna(subset=["TimeStamp"]).sort_values("TimeStamp")
            
            if df.empty:
                print(f"❌ PLOT DEBUG: {name} geçerli TimeStamp yok")
                continue

            bands = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
            avg_cols = [f"{b.lower()}_avg_clean" for b in bands if f"{b.lower()}_avg_clean" in df.columns]
            if not avg_cols:
                avg_cols = [f"{b.lower()}_avg" for b in bands if f"{b.lower()}_avg" in df.columns]

            if not avg_cols:
                print(f"❌ PLOT DEBUG: {name} hiçbir EEG band sütunu bulunamadı")
                continue

            ts = df.set_index("TimeStamp")[avg_cols]
            smooth = ts.resample("1s").mean().rolling(f"{win_secs}s", min_periods=1).mean()

            fig, ax = plt.subplots(figsize=(15, 7))

            # Grafik çizgilerini çiz
            for col_name in smooth.columns:
                band_name = col_name.replace("_avg_clean", "").replace("_avg", "").capitalize()
                series = smooth[col_name].dropna()
                if series.empty: continue
                ax.plot(series.index, series, label=band_name, color=BAND_COLORS.get(band_name, "black"), linewidth=1.5)

            # --- Y-ekseni: raw -> score etiketleme ---
            # scores ve raw_means metrics'ten alınır (scores: band -> puan, raw_means: band -> μV ort)
            raw_means = current_metrics.get("raw_means", {}) or {}
            scores_map = current_metrics.get("scores", {}) or {}
            # collect numeric raw and score pairs for bands that exist
            pairs = []
            for b in ["Delta","Theta","Alpha","Beta","Gamma"]:
                r = raw_means.get(b)
                s = scores_map.get(b)
                try:
                    if r is not None and s is not None:
                        rr = float(r)
                        ss = float(s)
                        if not (math.isnan(rr) or math.isnan(ss) or math.isinf(rr) or math.isinf(ss)):
                            pairs.append((b, rr, ss))
                except Exception:
                    continue

            # Debug
            print(f"🔧 Y-AXIS DEBUG: pairs(raw_mean,score)={pairs}")

            if pairs:
                raw_vals = [p[1] for p in pairs]
                score_vals = [p[2] for p in pairs]
                raw_min, raw_max = min(raw_vals), max(raw_vals)
                score_min, score_max = min(score_vals), max(score_vals)
                mapped_ok = False
                if raw_max != raw_min and score_max != score_min:
                    a = (score_max - score_min) / (raw_max - raw_min)
                    b = score_min - a * raw_min
                    # mevcut y-tick'leri al, map et, set et
                    yticks = ax.get_yticks()
                    # ensure ticks are explicitly set before set_yticklabels to avoid matplotlib warning
                    ax.set_yticks(yticks)
                    ylabels = [f"{(a * y + b):.1f}" for y in yticks]
                    ax.set_yticklabels(ylabels)
                    ax.set_ylabel("Score", fontsize=10)
                    mapped_ok = True
                    print(f"🔧 Y-AXIS DEBUG: linear map a={a:.6f}, b={b:.6f}, yticks_raw={list(yticks)}, yticks_score={ylabels}")

                if not mapped_ok:
                    # fallback: tick'leri band raw_mean değerlerine koy ve label olarak score ver
                    ticks = []
                    labels = []
                    for (band, rr, ss) in pairs:
                        ticks.append(rr)
                        labels.append(f"{band}: {ss:.1f}")
                    # sıralı yerleştir
                    ticks_labels = sorted(zip(ticks, labels), key=lambda x: x[0])
                    if ticks_labels:
                        ticks_s, labels_s = zip(*ticks_labels)
                        ax.set_yticks(list(ticks_s))
                        ax.set_yticklabels(list(labels_s))
                        ax.set_ylabel("Score (band means)", fontsize=10)
                        print(f"🔧 Y-AXIS DEBUG: fallback ticks={ticks_s}, labels={labels_s}")

            # Legend'ı oluştur
            handles, labels = ax.get_legend_handles_labels()
            new_labels = []

            # Dalga etiketlerini skor ve seviyelerle güncelle
            for band in labels:
                score = scores.get(band)
                level = (levels.get(band, "") or "").strip("-") # "-yüksek-" -> "yüksek"
                dom = dominance.get(band, "")
                dom_suffix = f" [{dom}]" if dom else ""
                if score is not None and level:
                    new_labels.append(f"{band}: {score:.2f} ({level}){dom_suffix}")
                else:
                    new_labels.append(f"{band}{dom_suffix}") # Eğer skor yoksa sadece dalga adını yaz

            # Analiz sonuçlarını ekle
            handles.append(Line2D([], [], linestyle="none"))
            new_labels.append("") # Boşluk

            bal_diff = balance_diff_map.get(name)
            if bal_diff is not None and not pd.isna(bal_diff):
                handles.append(Line2D([], [], linestyle="none"))
                diff_text = f"Dalga Farkı: {bal_diff:.2f}"
                if bal_diff <= bal_thresh:
                    diff_text += " (Denge Ustası)"
                new_labels.append(diff_text)
            
            best_profile = best_profile_map.get(name, "")
            if best_profile:
                handles.append(Line2D([], [], linestyle="none"))
                new_labels.append(f"Profil: {best_profile}")
            
            # Grafik ayarları
            plot_title = os.path.splitext(os.path.basename(name))[0]
            ax.set_title(f"EEG Dalga Eğilimleri: {plot_title}", fontsize=14, pad=15)
            ax.set_xlabel("Zaman", fontsize=10)
            ax.set_ylabel("Genlik (μV)", fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend(handles, new_labels, loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True, fontsize=9, title="Analiz Sonuçları")
            fig.tight_layout(rect=[0, 0, 0.85, 1])

            # Kaydetme
            # Eğer herhangi bir band için dominance tespit edildiyse "dominant" klasörüne, aksi halde "normal" klasörüne kaydet
            is_dominant = bool(dominance)
            if is_dominant:
                save_path = os.path.join(dominant_dir, f"{plot_title}.png")
            else:
                save_path = os.path.join(normal_dir, f"{plot_title}.png")
            
            print(f"🔧 PLOT DEBUG: Kaydediliyor -> {'dominant' if is_dominant else 'normal'} : {save_path}")

            fig.savefig(save_path, dpi=150, facecolor="white", edgecolor="none")
            plt.close(fig)
            
            plot_files.append(save_path)
            print(f"✅ PLOT DEBUG: {name} grafiği kaydedildi → {save_path}")

        except Exception as e:
            print(f"❌ PLOT DEBUG: {name} grafik hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    print(f"🔧 PLOT DEBUG: Toplam {len(plot_files)} grafik oluşturuldu")
    return plot_files
