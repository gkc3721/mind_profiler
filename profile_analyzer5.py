# profile_analyzer.py
import pandas as pd
import math
import unicodedata
import re
from typing import Dict, List, Tuple, Set
import numpy as np
import os

# --- AYARLAR ---
BALANCE_THRESHOLD = 22.0
DENGE_MEAN_THRESHOLD= 46.0
# Sabit profil dosyası yolu (mutlaka bu dosyayı kullan)
PROFILES_FILE = "/Users/umutkaya/Documents/Zenin Mind Reader/zenin_mac/Zihin_Profilleri_28_3.csv"

# --- YENİ: raw_means tabanlı kontrol eşiği ---
CONTROLLED_MEAN_THRESHOLD = 38.0

BANDS = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
TOK5_ASCII = ["dusuk", "dusuk orta", "orta", "yuksek orta", "yuksek"]
ASCII_TO_TR = {
    "dusuk": "düşük",
    "dusuk orta": "düşük orta",
    "orta": "orta",
    "yuksek orta": "yüksek orta",
    "yuksek": "yüksek",
}


#def _norm_tr(s: str) -> str:
 #   """Türkçe metni normalize eder"""
  #  if not isinstance(s, str): 
  #return ""
   # s = s.strip().lower().replace("-", " ").replace("_", " ")
    #s = unicodedata.normalize("NFC", s)
    #s = unicodedata.normalize("NFD", s)
    #s = "".join(ch for ch in s if not unicodedata.combining(ch))
    #s = unicodedata.normalize("NFC", s)
    #s = re.sub(r"\s+", " ", s)
    #return s

def _norm_tr(s: str) -> str:
    """Türkçe metni normalize eder"""
    if not isinstance(s, str):
        return ""
    
    s = s.strip().lower()
    # ❌ ARTIK TİREYİ BURADA ÇEVİRME!
    # s = s.replace("-", " ")  # BU SATIRI KALDIR
    s = s.replace("_", " ")
    
    # Unicode normalizasyonu
    s = unicodedata.normalize("NFC", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = unicodedata.normalize("NFC", s)
    
    # Birden fazla boşluğu teke indir
    s = re.sub(r"\s+", " ", s)
    return s

def canon5(txt: str) -> str:
    """5'li etiketi standart forma dönüştürür"""
    t = _norm_tr(txt)
    t = t.replace("yuksekorta", "yuksek orta").replace("dusukorta", "dusuk orta")
    if t in {"yuksek / orta", "orta / yuksek"}: 
        t = "yuksek orta"
    if t not in TOK5_ASCII:
        if t in {"yuksek", "orta", "dusuk"}:
            return t
    return t


def expand_profile_cell(cell: str) -> Set[str]:
    """Profil hücresini izinli etiket kümesine dönüştürür - gelişmiş parse"""
    TOK5 = set(TOK5_ASCII)
    BASES = {"dusuk", "orta", "yuksek"}
    base_to_idx = {"dusuk": 0, "orta": 2, "yuksek": 4}

    if not isinstance(cell, str):
        return set()

    # Normalize et (TİRE HARİÇ)
    t = _norm_tr(cell)  # Artık tire korunuyor
    if not t:
        return set()

    # ✅ TÜM TİRE VARYASYONLARINI STANDART TİREYE ÇEVİR
    t = t.replace("–", "-")  # En dash
    t = t.replace("—", "-")  # Em dash
    t = t.replace("−", "-")  # Minus sign
    t = t.replace("‐", "-")  # Hyphen
    t = t.replace("‑", "-")  # Non-breaking hyphen
    
    # ✅ BOŞLUKLARI NORMALIZE ET
    t = t.replace("\u00A0", " ")  # Non-breaking space
    t = t.replace("\u3000", " ")  # Full-width space
    t = re.sub(r"\s+", " ", t)     # Multiple spaces → single space
    
    # ✅ TİRE ETRAFINDAKI BOŞLUKLARI KALDIR
    # "orta - dusuk" → "orta-dusuk"
    t = re.sub(r"\s*-\s*", "-", t)
    
    # ✅ AYIRICILARA GÖRE PARÇALA (/, , veya -)
    parts = [p.strip() for p in re.split(r"[\/,\-]+", t) if p.strip()]
    allowed: Set[str] = set()

    for p in parts:
        p = p.replace("yuksekorta", "yuksek orta").replace("dusukorta", "dusuk orta")

        # Base token ise genişlet
        if p in BASES:
            i = base_to_idx[p]
            for j in {max(0, i-1), i, min(4, i+1)}:
                allowed.add(TOK5_ASCII[j])
            continue

        # Tam token ise direkt ekle
        if p in TOK5:
            allowed.add(p)

    return allowed

def load_profiles_table(path: str) -> pd.DataFrame:
    """Profil tablosunu güvenli şekilde yükler — debug ekli"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Profil dosyası bulunamadı: {path}")
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = None
        # try a few encodings
        for enc in ("utf-8-sig", "utf-8", "cp1254"):
            try:
                df = pd.read_csv(path, encoding=enc, sep=',')
                # CSV'nin ilk satırını kontrol ederek doğru ayrılıp ayrılmadığını teyit et
                if len(df.columns) < 2:
                    df = None # Yanlış ayırıcı, denemeye devam et
                    continue
                break
            except Exception:
                df = None
        if df is None:

            df = pd.read_csv(path, sep=';') 

    cols = list(df.columns)
    cols_norm = {c: _norm_tr(c) for c in cols}
    profile_col = None
    for c, cn in cols_norm.items():
        if cn in ("profil adi", "profiladi", "profil adı", "profil", "profil_adı", "profil_ad"):
            profile_col = c
            break
    if not profile_col:
        for c, cn in cols_norm.items():
            if "profil" in cn:
                profile_col = c
                break
    if profile_col:
        if profile_col != "Profil Adı":
            df = df.rename(columns={profile_col: "Profil Adı"})
            print(f"🔧 PROFILE DEBUG: Profil sütunu bulundu ve yeniden adlandırıldı: '{profile_col}' -> 'Profil Adı'")
    else:
        first_col = cols[0] if cols else None
        if first_col:
            df = df.rename(columns={first_col: "Profil Adı"})
            print(f"⚠️ PROFILE WARNING: 'Profil Adı' sütunu otomatik olarak '{first_col}' olarak seçildi. Lütfen profil dosyanızı kontrol edin.")
        else:
            raise ValueError("Profil dosyasında hiçbir sütun bulunamadı.")
    print(f"🔧 PROFILE DEBUG: Yüklendi: {path} -> {len(df)} satır, sütunlar: {list(df.columns)}")
    return df

def compile_profile_rules(df_profiles: pd.DataFrame) -> Dict[str, Dict[str, Set[str]]]:
	"""DataFrame'den profil kurallarını derler — sütun isimlerini normalize edip BANDS ile eşleştirir"""
	# Normalize edilmiş sütun isimleri
	cols = list(df_profiles.columns)
	cols_norm = {c: _norm_tr(c) for c in cols}

	# Map: band -> df sütun adı (varsa)
	band_col_map: Dict[str, str] = {}
	for b in BANDS:
		target = _norm_tr(b)
		found = None
		# Öncelikli tam eşleşme, sonra başlangıç, sonra içerme
		for c, cn in cols_norm.items():
			if cn == target:
				found = c; break
		if not found:
			for c, cn in cols_norm.items():
				if cn.startswith(target):
					found = c; break
		if not found:
			for c, cn in cols_norm.items():
				if target in cn:
					found = c; break
		band_col_map[b] = found  # None ise row.get(...) ile "" dönecek

	print(f"🔧 PROFILE DEBUG: band->column map: {band_col_map}")

	rules: Dict[str, Dict[str, Set[str]]] = {}
	for _, row in df_profiles.iterrows():
		# --- Güvenli profil adı okuma: NaN kontrolü ---
		prof_raw = row.get("Profil Adı", None)
		if pd.isna(prof_raw):
			continue
		prof = str(prof_raw).strip()
		if not prof:
			continue

		band_map = {}
		for b in BANDS:
			colname = band_col_map.get(b)
			# Ham hücre değerini (NaN ya da str) expand_profile_cell'e geçir
			raw_cell = row.get(colname, None) if colname else None
			band_map[b] = expand_profile_cell(raw_cell)
		rules[prof] = band_map

	print(f"🔧 PROFILE DEBUG: Derlenen profil sayısı: {len(rules)}")
	return rules

def extract_profile_cells(df_profiles: pd.DataFrame) -> Dict[str, Dict[str, str]]:
	"""Profil hücrelerinin ham metinlerini çıkarır"""
	cols = list(df_profiles.columns)
	cols_norm = {c: _norm_tr(c) for c in cols}
	band_col_map: Dict[str, str] = {}
	for b in BANDS:
		target = _norm_tr(b)
		found = None
		for c, cn in cols_norm.items():
			if cn == target:
				found = c; break
		if not found:
			for c, cn in cols_norm.items():
				if cn.startswith(target):
					found = c; break
		if not found:
			for c, cn in cols_norm.items():
				if target in cn:
					found = c; break
		band_col_map[b] = found
	cells = {}
	for _, row in df_profiles.iterrows():
		# --- Güvenli profil adı okuma: NaN kontrolü ---
		prof_raw = row.get("Profil Adı", None)
		if pd.isna(prof_raw):
			continue
		prof = str(prof_raw).strip()
		if not prof:
			continue

		# Hücreleri ham halde al; NaN ise boş string yap
		cells[prof] = {}
		for b in BANDS:
			col = band_col_map.get(b)
			if col and not pd.isna(row.get(col)):
				cells[prof][b] = str(row.get(col))
			else:
				cells[prof][b] = ""
	return cells

def is_balance_master(scores: Dict[str, float], threshold: float = BALANCE_THRESHOLD) -> Tuple[bool, float]:
    """Denge Ustası kontrolü - scores dict'ini alır"""
    # Debug çıktısı
    print("\n🔧 BALANCE DEBUG - Gelen scores:")
    print(scores)
    
    # Sadece geçerli değerleri al ve float'a çevir
    valid_scores = []
    for band in ["Delta", "Theta", "Alpha", "Beta", "Gamma"]:
        if band in scores and scores[band] is not None:
            try:
                val = float(scores[band])
                if not math.isnan(val):
                    valid_scores.append(val)
            except (TypeError, ValueError):
                continue
    
    print(f"🔧 BALANCE DEBUG - Geçerli skorlar: {valid_scores}")
    
    # En az 2 geçerli değer yoksa NaN döndür
    if len(valid_scores) < 2:
        print("❌ BALANCE DEBUG - Yetersiz geçerli skor")
        return (False, float("nan"))
    
    # En yüksek ve en düşük değer arasındaki farkı hesapla
    diff = max(valid_scores) - min(valid_scores)
    
    print(f"🔧 BALANCE DEBUG - Hesaplanan fark: {diff:.2f}")
    print(f"🔧 BALANCE DEBUG - Denge Ustası mı? {diff <= threshold}")
    
    return (diff <= threshold, diff)

def count_profile_matches(band_levels: Dict[str, str], rules: Dict[str, Dict[str, Set[str]]]) -> Dict[str, int]:
    """Analytics'ten gelen level'ları kullanır"""
    person = {b: canon5((band_levels.get(b, "") or "").strip("-").strip()) for b in BANDS}  # normalize
    counts: Dict[str, int] = {}
    for prof, cond in rules.items():
        cnt = 0
        for b in BANDS:
            allowed = cond.get(b, set())
            # Eğer profil hücresi tanımsızsa (boş küme), o band için eşleşme sayılmasın
            if not allowed:
                # debug: hangi profilde hangi band tanımsız olduğunu görmek istersen loglayabilirsin
                # print(f"DEBUG: profil '{prof}' için band '{b}' tanımsız -> atlanıyor")
                continue
            if person.get(b, "") in allowed:
                cnt += 1
        counts[prof] = cnt
    return counts

def band_score_for_profile_cell(cell: str, person_level_5: str) -> int:
    """Profil hücresi ve kişi seviyesi için puan hesaplar - gelişmiş parse"""
    if not isinstance(cell, str) or not person_level_5:
        return 0

    person = canon5(person_level_5)

    base_to_allowed = {
        "yuksek": {"yuksek orta", "yuksek"},
        "orta": {"dusuk orta", "orta", "yuksek orta"},
        "dusuk": {"dusuk", "dusuk orta"},
    }
    base_points = {"yuksek": 3, "orta": 1, "dusuk": 2}
    token_points = {"yuksek": 3, "yuksek orta": 3, "orta": 1, "dusuk orta": 2, "dusuk": 2}

    t = _norm_tr(cell)
    if not t:
        return token_points.get(person, 0)

    if "dengeli" in t:
        return token_points.get(person, 0)

    # ✅ TÜM TİRE VARYASYONLARINI NORMALIZE ET
    t = t.replace("–", "-").replace("—", "-").replace("−", "-")
    t = t.replace("‐", "-").replace("‑", "-")
    
    # ✅ BOŞLUKLARI NORMALIZE ET
    t = t.replace("\u00A0", " ").replace("\u3000", " ")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*-\s*", "-", t)  # Tire etrafındaki boşlukları kaldır

    best = 0
    # ✅ AYIRICILARA GÖRE PARÇALA
    for p in [p.strip() for p in re.split(r"[\/,\-]+", t) if p.strip()]:
        #                                         ^^^^ - eklendi
        p = p.replace("yuksekorta", "yuksek orta").replace("dusukorta", "dusuk orta")

        if p in base_to_allowed:
            if person in base_to_allowed[p]:
                best = max(best, base_points[p])
            continue

        if p in token_points and person == p:
            best = max(best, token_points[p])

    return best
# --- ANA FONKSİYON (GÜNCELLENDİ) ---
def analyze_profiles_from_metrics(csv_name: str, metrics: Dict) -> Dict[str, any]:
    try:
        profiles_df = load_profiles_table(PROFILES_FILE)
        PROFILE_RULES = compile_profile_rules(profiles_df)
        PROFILE_CELLS = extract_profile_cells(profiles_df)
        print(f"🔧 PROFILE DEBUG: Derlenen profil sayısı: {len(PROFILE_RULES)}")
    except Exception as e:
        print(f"⚠️  Profil dosyası yüklenemedi veya okunamadı: {e}")
        print("⚠️  Fallback: Basit otomatik profil kuralları oluşturuluyor (dosya yoksa da eşleştirme yapılacak).")
        PROFILE_RULES = {}
        PROFILE_CELLS = {}
        all_tokens = set(TOK5_ASCII)
        for b in BANDS:
            for tok in TOK5_ASCII:
                prof_name = f"{b} {tok}"
                band_map = {bb: ({tok} if bb == b else set(all_tokens)) for bb in BANDS}
                PROFILE_RULES[prof_name] = band_map
                PROFILE_CELLS[prof_name] = {bb: (tok if bb == b else "") for bb in BANDS}
        print(f"🔧 PROFILE DEBUG: Fallback profiller oluşturuldu: {len(PROFILE_RULES)} adet")

    # Dalga farkı ve levels'ı doğrudan metrics'ten al
    raw_dalga = metrics.get("dalga_farki", None)
    dalga_farki = None
    try:
        if raw_dalga is None or raw_dalga == "":
            dalga_farki = None
        else:
            dalga_farki = float(raw_dalga)
    except Exception:
        print(f"⚠️ DEBUG: dalga_farki parse edilemedi: {raw_dalga} (type={type(raw_dalga)})")
        dalga_farki = None

    levels_raw = metrics.get("levels", {}) or {}
    levels_canon = {}
    for b in BANDS:
        v = (levels_raw.get(b, "") or "")
        v_stripped = v.strip().strip("-").strip()
        canon = canon5(v_stripped)
        levels_canon[b] = canon

    # --- YENİ: raw_means ve scores ortalamalarını hesapla (debug & karar için) ---
    raw_means_map = metrics.get("raw_means", {}) or {}
    score_map = metrics.get("scores", {}) or {}

    raw_vals = []
    for v in raw_means_map.values():
        try:
            fv = float(v)
            if not math.isnan(fv):
                raw_vals.append(fv)
        except Exception:
            continue
    mean_raw = None if not raw_vals else float(sum(raw_vals) / len(raw_vals))

    score_vals = []
    for v in score_map.values():
        try:
            fv = float(v)
            if not math.isnan(fv):
                score_vals.append(fv)
        except Exception:
            continue
    mean_score = None if not score_vals else float(sum(score_vals) / len(score_vals))

    print(f"🔧 DEBUG - Dalga Farkı (parsed): {dalga_farki} (raw: {raw_dalga})")
    print(f"🔧 DEBUG - Levels (raw): {levels_raw}")
    print(f"🔧 DEBUG - Levels (canon): {levels_canon}")
    print(f"🔧 DEBUG - PROFILE_RULES count: {len(PROFILE_RULES)}")
    print(f"🔧 DEBUG - mean_raw: {mean_raw}, mean_score(scaled): {mean_score}")

    # Denge Ustası kontrolü
    if dalga_farki is not None:
        try:
            if dalga_farki <= BALANCE_THRESHOLD:
                print(f"✅ DEBUG - Denge Ustası tespit edildi! (Fark: {dalga_farki})")
        # scores ortalamasına göre 'DENGE USTASI YÜKSEK' veya 'DENGE USTASI DÜŞÜK' ata
                scores_map = metrics.get("scores", {}) or {}
                vals = []
                for b in ["Delta", "Theta", "Alpha", "Beta", "Gamma"]:
                    try:
                        v = scores_map.get(b)
                        if v is None:
                            continue
                        fv = float(v)
                        if not math.isnan(fv):
                            vals.append(fv)
                    except Exception:
                        continue
                mean_score = None
                if vals:
                    mean_score = sum(vals) / len(vals)
                # Mean eşik kontrolü: DENGE_MEAN_THRESHOLD sabitini kullan
                if mean_score is None:
                    label = "DENGE USTASI"
                elif mean_score >= DENGE_MEAN_THRESHOLD:
                    label = "YÜKSEK BİLİNÇLİ"
                else:
                    label = "DENGE USTASI"
                return {
                    "dalga_farki": dalga_farki,
                    "tam_uyumlu_profiller": "",
                    "en_iyi_profiller": label,
                    "en_iyi_puan": 0
                }
        except Exception as ex:
            print(f"⚠️ DEBUG - dalga_farki karşılaştırmada hata: {ex}")

    match_counts = count_profile_matches(levels_canon, PROFILE_RULES)
    print(f"🔧 DEBUG - match_counts örnek (ilk 10): {list(match_counts.items())[:10]}")

    perfect = [p for p, c in match_counts.items() if c == 5]
    almost = [p for p, c in match_counts.items() if c == 4]

    print(f"🔧 DEBUG - perfect matches: {perfect}")
    print(f"🔧 DEBUG - almost matches: {almost}")

    # YER: profile_analyzer5.py -> analyze_profiles_from_metrics fonksiyonu


    # ---- YENİ DEBUG BLOĞUNU BURAYA EKLEYİN ----
    print("\n--- DEBUGGING PROFIL EŞLEŞMESİ ---")
    print(f"Kişinin normalize edilmiş seviyeleri (levels_canon): {levels_canon}")
    sorted_matches = sorted(match_counts.items(), key=lambda item: item[1], reverse=True)
    print("En yüksek eşleşme sayıları:")
    for profile, count in sorted_matches[:10]: # En iyi 10 sonucu göster
        if count > 0: # Sadece 0'dan büyükleri göster
            print(f"  - Profil: '{profile}', Eşleşme Sayısı: {count}")
    print(f"Sonuç -> 'perfect' listesi (5 uyumlu) boş mu?: {not perfect}")
    print(f"Sonuç -> 'almost' listesi (4 uyumlu) boş mu?: {not almost}")
    print("--- DEBUGGING SONU ---\n")
    # ---------------------------------------------

    
    # Hiçbir profil eşleşmezse boş döndür (profil ataması yapma)
    if not perfect and not almost:
        print(f"⚠️ DEBUG - Profil eşleşmesi yok. Person levels canonical: {levels_canon}")
        """
        # Eşleşme olmadığında "Eşleşme Yok" yazan eski kod (etkisiz)
        return {
            "dalga_farki": dalga_farki,
            "tam_uyumlu_profiller": "",
            "en_iyi_profiller": "Eşleşme Yok",
            "en_iyi_puan": 0,
            "controlled_mean": mean_score,
            "controlled_label": ""
        }
        """
        # Yeni davranış: Eşleşme yoksa boş döndür
        return {
            "dalga_farki": dalga_farki,
            "tam_uyumlu_profiller": "",
            "en_iyi_profiller": "",
            "en_iyi_puan": 0,
            "controlled_mean": mean_score,
            "controlled_label": ""
        }


    candidate_profiles = perfect if perfect else almost
    candidate_tag = {p: "" for p in perfect} if perfect else {p: " (4 uyumlu)" for p in almost}
    tam_text = ", ".join(perfect) if perfect else ", ".join(f"{p} (4 uyumlu)" for p in almost)

    scored = []
    for prof in candidate_profiles:
        total = 0
        for b in BANDS:
            cell = PROFILE_CELLS.get(prof, {}).get(b, "")
            total += band_score_for_profile_cell(cell, levels_canon.get(b, ""))
        scored.append((prof, total))

    max_score = max((s for _, s in scored), default=0)
    tied = [p for p, s in scored if s == max_score]

    is_almost = (not perfect) and bool(almost)
    if len(tied) > 1 and is_almost:
        def resolve_tie_by_earliest_mismatch(tied_list):
            priority_order = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
            band_to_idx = {b: i for i, b in enumerate(priority_order)}
            mismatched_bands = {}
            for prof in tied_list:
                person_level_map = {b: canon5((levels_canon.get(b, "") or "").strip("-")) for b in BANDS}
                prof_rules = PROFILE_RULES.get(prof, {})
                for band in priority_order:
                    person_level = person_level_map.get(band, "")
                    allowed = prof_rules.get(band, set())
                    if person_level and person_level not in allowed:
                        mismatched_bands[prof] = (band, band_to_idx[band])
                        break
                else:
                    mismatched_bands[prof] = (None, 999)
            print(f"🔧 TIE-BREAK DEBUG: tied={tied_list}, mismatched={mismatched_bands}")
            no_mismatch = [p for p in tied_list if mismatched_bands.get(p, (None, 999))[0] is None]
            if no_mismatch:
                print(f"✅ TIE-BREAK: Uyumsuz dalgası olmayanlar (tam uyum): {no_mismatch}")
                return no_mismatch[:1]
            min_idx = min(mismatched_bands[p][1] for p in tied_list)
            selected = [p for p in tied_list if mismatched_bands.get(p, (None, 999))[1] == min_idx]
            print(f"🔧 TIE-BREAK: min_idx={min_idx} ({priority_order[min_idx] if min_idx < 5 else 'N/A'})")
            print(f"✅ TIE-BREAK: Seçilen profil(ler): {selected}")
            if len(selected) == 1:
                return selected
            else:
                return selected[:1]
        resolved = resolve_tie_by_earliest_mismatch(tied)
        tied = resolved

    top = [f"{p}{candidate_tag.get(p,'')}" for p in tied]
    
    # Atanan profil adını bir string haline getir
    final_profile_str = ", ".join(top)

    # Kontrollü Yaşayan profilini ikiye bölme özelliği kaldırıldı
    # Profil olduğu gibi kullanılacak
    
    return {
        "dalga_farki": dalga_farki,
        "tam_uyumlu_profiller": tam_text,
        "en_iyi_profiller": final_profile_str, # Potansiyel olarak güncellenmiş profil adını kullan
        "en_iyi_puan": max_score,
        # controlled_mean artık adjusted scores ortalamasıyla raporlanıyor
        "controlled_mean": mean_score,
        "controlled_label": ""
    }