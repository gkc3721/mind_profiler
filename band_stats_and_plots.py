"""
EEG Band Power Statistics and Distribution Plot Generator

This script loads all CSV files from a specified root directory,
extracts EEG band power columns, computes descriptive statistics,
and generates a 5×4 grid of distribution plots.
"""

import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# Root directory for CSV files
CSV_ROOT = r"/Users/umutkaya/Documents/Zenin Mind Reader/data"

# Expected band power columns (5 bands × 4 channels = 20 columns)
BAND_COLUMNS = [
    "Delta_TP9", "Delta_AF7", "Delta_AF8", "Delta_TP10",
    "Theta_TP9", "Theta_AF7", "Theta_AF8", "Theta_TP10",
    "Alpha_TP9", "Alpha_AF7", "Alpha_AF8", "Alpha_TP10",
    "Beta_TP9",  "Beta_AF7",  "Beta_AF8",  "Beta_TP10",
    "Gamma_TP9", "Gamma_AF7", "Gamma_AF8", "Gamma_TP10"
]


def load_data(csv_root: str) -> pd.DataFrame:
    """
    Load all CSV files from the root directory and merge them.
    
    Args:
        csv_root: Root directory path to search for CSV files
        
    Returns:
        Combined DataFrame with band power columns
    """
    print(f"Searching for CSV files under: {csv_root}")
    
    # Check if root directory exists
    if not os.path.exists(csv_root):
        print(f"Warning: Directory '{csv_root}' does not exist.")
        print("Returning empty DataFrame.")
        return pd.DataFrame()
    
    # Find all CSV files recursively
    csv_pattern = os.path.join(csv_root, "**", "*.csv")
    csv_files = glob.glob(csv_pattern, recursive=True)
    
    # Also check directly in root directory
    csv_files_direct = glob.glob(os.path.join(csv_root, "*.csv"))
    csv_files = list(set(csv_files + csv_files_direct))  # Remove duplicates
    
    if not csv_files:
        print(f"No CSV files found in '{csv_root}'")
        return pd.DataFrame()
    
    print(f"Found {len(csv_files)} CSV file(s)")
    
    # Load each CSV file
    dataframes = []
    for csv_file in csv_files:
        try:
            # Try different separators
            df = pd.read_csv(csv_file, sep=';', encoding='utf-8', low_memory=False)
            if df.empty or len(df.columns) < 2:
                # Try comma separator
                df = pd.read_csv(csv_file, sep=',', encoding='utf-8', low_memory=False)
            
            if not df.empty:
                dataframes.append(df)
                print(f"  Loaded: {os.path.basename(csv_file)} ({len(df)} rows)")
        except Exception as e:
            print(f"  Warning: Could not load {os.path.basename(csv_file)}: {e}")
            continue
    
    if not dataframes:
        print("No valid CSV files could be loaded.")
        return pd.DataFrame()
    
    # Concatenate all DataFrames
    print(f"Concatenating {len(dataframes)} DataFrames...")
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Find which band columns actually exist
    available_columns = [col for col in BAND_COLUMNS if col in combined_df.columns]
    
    if not available_columns:
        print("Warning: No band power columns found in any CSV files.")
        print(f"Expected columns: {BAND_COLUMNS}")
        print(f"Available columns in data: {list(combined_df.columns)[:10]}...")
        return pd.DataFrame()
    
    print(f"Available band columns: {available_columns}")
    
    # Extract only the band columns that exist
    band_df = combined_df[available_columns].copy()
    
    # Convert to numeric, coercing errors to NaN
    for col in available_columns:
        band_df[col] = pd.to_numeric(band_df[col], errors='coerce')
        # Replace infinite values with NaN
        band_df[col] = band_df[col].replace([np.inf, -np.inf], np.nan)
    
    # Remove rows where all band columns are NaN
    band_df = band_df.dropna(how='all')
    
    if band_df.empty:
        print("Warning: After converting to numeric, no valid data remains.")
        return pd.DataFrame()
    
    print(f"Final dataset: {len(band_df)} rows, {len(available_columns)} band columns")
    
    return band_df


def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute descriptive statistics for band power columns.
    
    Args:
        df: DataFrame with band power columns
        
    Returns:
        DataFrame with statistics (transposed describe())
    """
    if df.empty:
        print("Cannot compute statistics: DataFrame is empty.")
        return pd.DataFrame()
    
    # Get available band columns from the DataFrame
    available_columns = [col for col in BAND_COLUMNS if col in df.columns]
    
    if not available_columns:
        print("No band columns available for statistics.")
        return pd.DataFrame()
    
    print(f"\nComputing statistics for {len(available_columns)} columns...")
    
    # Compute descriptive statistics
    stats = df[available_columns].describe().T
    
    # Add column name as index name for clarity
    stats.index.name = 'Column'
    
    return stats


def plot_distributions(df: pd.DataFrame, output_path: str) -> None:
    """
    Create a 5×4 grid of distribution plots for band power columns.
    
    Args:
        df: DataFrame with band power columns
        output_path: Path to save the figure
    """
    if df.empty:
        print("Cannot create plots: DataFrame is empty.")
        return
    
    # Create figure with 5 rows × 4 columns
    fig, axes = plt.subplots(nrows=5, ncols=4, figsize=(20, 20))
    
    # Flatten axes array for easier indexing
    axes_flat = axes.flatten()
    
    # Define band order and channel order
    bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
    channels = ['TP9', 'AF7', 'AF8', 'TP10']
    
    print("\nGenerating distribution plots...")
    
    # Plot each subplot
    for row_idx, band in enumerate(bands):
        for col_idx, channel in enumerate(channels):
            # Calculate flat index: row * 4 + col
            flat_idx = row_idx * 4 + col_idx
            
            ax = axes_flat[flat_idx]
            column_name = f"{band}_{channel}"
            
            if column_name in df.columns:
                # Get data for this column, removing NaN and infinite values
                data = df[column_name].dropna()
                # Filter out infinite values
                data = data[np.isfinite(data)]
                
                if len(data) > 0:
                    # Plot histogram
                    ax.hist(data, bins=30, edgecolor='black', alpha=0.7)
                    ax.set_title(column_name, fontsize=10, fontweight='bold')
                    ax.set_xlabel('Value', fontsize=8)
                    ax.set_ylabel('Frequency', fontsize=8)
                    ax.grid(True, alpha=0.3)
                else:
                    # Column exists but has no valid data
                    ax.set_title(f"{column_name}\n(no data)", fontsize=10, 
                               color='gray', style='italic')
                    ax.text(0.5, 0.5, 'No data', ha='center', va='center', 
                           transform=ax.transAxes, fontsize=12, color='gray')
            else:
                # Column does not exist
                ax.set_title(f"{column_name}\n(missing)", fontsize=10, 
                           color='red', style='italic')
                ax.text(0.5, 0.5, 'Column not found', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color='red')
            
            # Remove ticks for empty subplots
            if column_name not in df.columns or (column_name in df.columns and len(df[column_name].dropna()) == 0):
                ax.set_xticks([])
                ax.set_yticks([])
    
    # Add overall title
    fig.suptitle('EEG Band Power Distributions (5×4 Grid)', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    
    # Save figure
    print(f"Saving distribution plot to {output_path}")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Plot saved successfully.")


def main():
    """Main function to orchestrate the analysis."""
    print("=" * 60)
    print("EEG Band Power Statistics and Distribution Analysis")
    print("=" * 60)
    print(f"\nRoot directory: {CSV_ROOT}\n")
    
    # Load data
    df = load_data(CSV_ROOT)
    
    if df.empty:
        print("\nExiting: No data available for analysis.")
        return
    
    # Compute statistics
    stats = compute_stats(df)
    
    if stats.empty:
        print("\nExiting: Could not compute statistics.")
        return
    
    # Print statistics preview
    print("\n" + "=" * 60)
    print("Statistical Summary Preview:")
    print("=" * 60)
    print(stats.head(20))  # Print all rows (max 20)
    print("\n" + "=" * 60)
    
    # Save statistics to Excel
    excel_path = "band_stats_summary.xlsx"
    print(f"\nSaving Excel summary to {excel_path}")
    try:
        stats.to_excel(excel_path, sheet_name='Band Statistics', index=True)
        print("Excel file saved successfully.")
    except Exception as e:
        print(f"Error saving Excel file: {e}")
    
    # Create and save distribution plots
    plot_path = "band_distributions_5x4.png"
    plot_distributions(df, plot_path)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print(f"Output files:")
    print(f"  - {excel_path}")
    print(f"  - {plot_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
