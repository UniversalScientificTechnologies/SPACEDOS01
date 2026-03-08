#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

def parse_log(filepath):
    """Parse SPACEDOS01 log file and sum energy spectrum channels."""
    spectrum = None
    first_timestamp = None
    last_timestamp = None
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) < 10:
                continue
            
            # Process only HKSD messages
            if parts[1] != '$HKSD':
                continue
            
            # Get timestamp from first column
            try:
                timestamp = int(parts[0])
                if first_timestamp is None:
                    first_timestamp = timestamp
                last_timestamp = timestamp
            except ValueError:
                continue
            
            # Channel data starts at index 6
            try:
                channels = [int(x) for x in parts[6:] if x.strip()]
                if not channels:
                    continue
            except ValueError:
                # Skip lines with invalid channel data
                continue
            
            if spectrum is None:
                spectrum = np.array(channels)
            else:
                # Handle cases where channel count might vary
                n = min(len(spectrum), len(channels))
                spectrum[:n] += channels[:n]
    
    duration = None
    if first_timestamp is not None and last_timestamp is not None:
        duration = last_timestamp - first_timestamp
    
    return spectrum, duration

def save_csv(spectrum, output_file, peak_channel):
    """Save spectrum to CSV file with renumbered channels."""
    with open(output_file, 'w') as f:
        f.write('Channel,Count\n')
        for i, count in enumerate(spectrum):
            channel = i - peak_channel
            f.write(f'{channel},{count}\n')
    print(f"CSV uloženo do: {output_file}")

def find_peak_channel(spectrum):
    """Find channel with highest particle count in first 10 channels."""
    peak_channel = np.argmax(spectrum[:10])
    print(f"Kanál s nejvyšším počtem částic (prvních 10): {peak_channel} s {spectrum[peak_channel]} částicemi")
    return peak_channel

def plot_spectrum(spectrum, output_file, peak_channel, duration=None, record_name=None):
    """Plot energy spectrum."""
    
    # Přečíslování kanálů - peak_channel se stane kanálem 0
    channel_numbers = np.arange(len(spectrum)) - peak_channel
    
    plt.figure(figsize=(12, 6))
    
    # Zvýraznit kanál 0 svislou čarou (za sloupečky, na začátku sloupečku 0)
    plt.axvline(x=-0.5, color='red', linestyle='--', linewidth=2, zorder=1)
    
    plt.bar(channel_numbers, spectrum, width=1.0, edgecolor='black', linewidth=0.5, zorder=2)
    
    plt.xlabel('Channel Number')
    plt.ylabel('Particle Count')
    plt.yscale('log')
    
    title = 'Energy Spectrum SPACEDOS01'
    if record_name is not None:
        title += f' - {record_name}'
    if duration is not None:
        title += f' - Expozice: {duration}s ({duration/60:.1f} min)'
    plt.title(title)
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Graf uložen do: {output_file}")
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Použití: python3 plot_spectrum.py <log_soubor> [<log_soubor2> ...]")
        sys.exit(1)
    
    log_files = sys.argv[1:]
    
    combined_spectrum = None
    total_duration = 0
    
    for log_file in log_files:
        print(f"Zpracovávám: {log_file}")
        spectrum, duration = parse_log(log_file)
        
        if spectrum is not None:
            if combined_spectrum is None:
                combined_spectrum = spectrum
            else:
                n = min(len(combined_spectrum), len(spectrum))
                combined_spectrum[:n] += spectrum[:n]
            
            if duration is not None:
                total_duration += duration
    
    if combined_spectrum is not None:
        print(f"\nCelkem načteno {len(log_files)} souborů")
        print(f"Načteno {len(combined_spectrum)} kanálů")
        print(f"Celkový počet částic: {np.sum(combined_spectrum)}")
        if total_duration > 0:
            print(f"Celková délka měření: {total_duration} sekund ({total_duration/60:.1f} minut)")
        
        # Output file names based on first log file
        base_name = os.path.splitext(log_files[0])[0]
        if len(log_files) == 1:
            record_name = os.path.basename(base_name)
        else:
            record_name = f"{os.path.basename(base_name)} + {len(log_files)-1} more"
        
        png_file = f"{base_name}.png"
        csv_file = f"{base_name}.csv"
        
        peak_channel = find_peak_channel(combined_spectrum)
        save_csv(combined_spectrum, csv_file, peak_channel)
        plot_spectrum(combined_spectrum, png_file, peak_channel, total_duration if total_duration > 0 else None, record_name)
    else:
        print("Chyba: Nepodařilo se načíst data z žádného logu")
        sys.exit(1)
