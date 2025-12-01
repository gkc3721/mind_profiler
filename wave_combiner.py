import os
import sys
import re
import pandas as pd
from collections import Counter
from datetime import datetime

# CSV kök dizini
CSV_ROOT = r"/Users/umutkaya/Documents/Zenin Mind Reader/data"
# Run counter file path
RUN_COUNTER_FILE = os.path.join(CSV_ROOT, "run_counter.txt")
# Output directory for Excel file
OUTPUT_DIR = r"/Users/umutkaya/Documents/Zenin Mind Reader/zenin_mac"

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

def find_most_recent_log():
    """En son processing log dosyasını bul ve run_id'yi döndür."""
    # Try to find the latest processing log by checking counter file
    run_id = _get_last_run_id()
    if run_id:
        log_path = os.path.join(CSV_ROOT, f"processing_log{run_id}.csv")
        if os.path.exists(log_path):
            return log_path, run_id
    
    # Fallback: search for all processing_log files and get the most recent
    if os.path.exists(CSV_ROOT):
        log_files = []
        for filename in os.listdir(CSV_ROOT):
            if filename.startswith("processing_log") and filename.endswith(".csv"):
                match = re.search(r'processing_log(\d+)\.csv', filename)
                if match:
                    run_id = int(match.group(1))
                    log_path = os.path.join(CSV_ROOT, filename)
                    log_files.append((run_id, log_path))
        
        if log_files:
            # Sort by run_id descending and return the most recent
            log_files.sort(key=lambda x: x[0], reverse=True)
            return log_files[0][1], log_files[0][0]
    
    return None, None

def analyze_wave_combinations(log_path):
    """5-band level kombinasyonlarını analiz et ve en sık görülenleri döndür."""
    # Read the CSV file
    df = pd.read_csv(log_path, encoding="utf-8", dtype=str)
    
    # Required columns
    level_columns = ["level_delta", "level_theta", "level_alpha", "level_beta", "level_gamma"]
    
    # Check if all required columns exist
    missing_columns = [col for col in level_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Eksik sütunlar: {', '.join(missing_columns)}")
    
    # Filter rows where all level columns have non-empty values
    # Fill NaN and empty strings, then filter
    for col in level_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    
    # Only keep rows where all 5 level columns have non-empty values
    valid_mask = df[level_columns].apply(lambda row: all(val != "" for val in row), axis=1)
    df_valid = df[valid_mask].copy()
    
    if len(df_valid) == 0:
        print("⚠️ Hiç geçerli 5-band kombinasyonu bulunamadı (tüm seviyeler dolu olan satır yok).")
        return []
    
    # Combine the 5 level values into a single string
    # Format: "level_delta-level_theta-level_alpha-level_beta-level_gamma"
    combinations = []
    for _, row in df_valid.iterrows():
        combo = "-".join([str(row[col]) for col in level_columns])
        combinations.append(combo)
    
    # Count frequency of each combination
    combo_counter = Counter(combinations)
    
    # Get top 30 most frequent combinations
    top_30 = combo_counter.most_common(30)
    
    return top_30

def save_to_excel(top_combinations, run_id=None):
    """Sonuçları Excel dosyasına kaydet."""
    if not top_combinations:
        return None
    
    # Create DataFrame
    rows = []
    for rank, (combination, count) in enumerate(top_combinations, 1):
        # Split combination into individual bands
        parts = combination.split("-")
        rows.append({
            "Sıra": rank,
            "Kombinasyon": combination,
            "Delta": parts[0] if len(parts) > 0 else "",
            "Theta": parts[1] if len(parts) > 1 else "",
            "Alpha": parts[2] if len(parts) > 2 else "",
            "Beta": parts[3] if len(parts) > 3 else "",
            "Gamma": parts[4] if len(parts) > 4 else "",
            "Frekans": count
        })
    
    df = pd.DataFrame(rows)
    
    # Generate output filename
    if run_id:
        output_filename = f"wave_combinations_{run_id}.xlsx"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"wave_combinations_{timestamp}.xlsx"
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save to Excel
    df.to_excel(output_path, index=False, engine="openpyxl")
    
    return output_path

def main():
    """Ana fonksiyon: En son log dosyasını bul, analiz et ve sonuçları yazdır."""
    log_path, run_id = find_most_recent_log()
    
    if not log_path:
        print("❌ En son processing log dosyası bulunamadı.")
        print(f"   Arama konumu: {CSV_ROOT}")
        sys.exit(1)
    
    print(f"📊 Analiz edilen log dosyası: {log_path}")
    print("-" * 80)
    
    try:
        top_combinations = analyze_wave_combinations(log_path)
        
        if not top_combinations:
            print("⚠️ Hiç sonuç bulunamadı.")
            return
        
        print(f"\n🏆 En Sık Görülen 30 Adet 5-Band Seviye Kombinasyonu:\n")
        print(f"{'Sıra':<6} {'Kombinasyon':<60} {'Frekans':<10}")
        print("-" * 80)
        
        for rank, (combination, count) in enumerate(top_combinations, 1):
            # Format: delta-theta-alpha-beta-gamma
            print(f"{rank:<6} {combination:<60} {count:<10}")
        
        print("-" * 80)
        print(f"\n✅ Toplam {len(top_combinations)} farklı kombinasyon gösterildi.")
        
        # Save to Excel
        excel_path = save_to_excel(top_combinations, run_id)
        if excel_path:
            print(f"\n💾 Sonuçlar Excel dosyasına kaydedildi: {excel_path}")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
