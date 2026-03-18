#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backend_tools import ToolBase

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

def load_and_combine(log_files):
    """Load and combine spectra from log files. Returns (spectrum, duration)."""
    combined_spectrum = None
    total_duration = 0
    
    for log_file in log_files:
        print(f"Zpracovávám: {log_file}")
        spectrum, duration = parse_log(log_file)
        
        if spectrum is not None:
            if combined_spectrum is None:
                combined_spectrum = spectrum.copy()
            else:
                n = min(len(combined_spectrum), len(spectrum))
                combined_spectrum[:n] += spectrum[:n]
            
            if duration is not None:
                total_duration += duration
    
    return combined_spectrum, total_duration

def plot_spectrum(spectrum, output_file, peak_channel, duration=None, record_name=None, log_files=None, csv_file=None):
    """Plot energy spectrum with reload button."""
    
    matplotlib.rcParams['toolbar'] = 'toolmanager'
    fig, ax = plt.subplots(figsize=(12, 6))
    
    def draw(spec, pc, dur):
        ax.clear()
        channel_numbers = np.arange(len(spec)) - pc
        ax.axvline(x=-0.5, color='red', linestyle='--', linewidth=2, zorder=1)
        ax.bar(channel_numbers, spec, width=1.0, edgecolor='black', linewidth=0.5, zorder=2)
        ax.set_xlabel('Channel Number')
        ax.set_ylabel('Particle Count')
        ax.set_yscale('log')
        
        title = 'Energy Spectrum SPACEDOS01'
        if record_name is not None:
            title += f' - {record_name}'
        if dur is not None:
            title += f' - Expozice: {dur}s ({dur/60:.1f} min)'
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        fig.canvas.draw_idle()
    
    draw(spectrum, peak_channel, duration)
    
    class ReloadTool(ToolBase):
        default_keymap = 'r'
        description = 'Reload data from log files'
        
        def trigger(self, *args, **kwargs):
            if log_files is None:
                return
            print("\nReload dat...")
            new_spectrum, new_duration = load_and_combine(log_files)
            if new_spectrum is not None:
                new_peak = find_peak_channel(new_spectrum)
                draw(new_spectrum, new_peak, new_duration if new_duration > 0 else None)
                if csv_file is not None:
                    save_csv(new_spectrum, csv_file, new_peak)
                fig.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"Graf uložen do: {output_file}")
            else:
                print("Chyba: Nepodařilo se načíst data")
    
    fig.canvas.manager.toolmanager.add_tool('reload', ReloadTool)
    fig.canvas.manager.toolbar.add_tool('reload', 'io')
    
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Graf uložen do: {output_file}")
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Použití: python3 plot_spectrum.py <log_soubor> [<log_soubor2> ...]")
        sys.exit(1)
    
    log_files = sys.argv[1:]
    
    combined_spectrum, total_duration = load_and_combine(log_files)
    
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
        plot_spectrum(combined_spectrum, png_file, peak_channel, total_duration if total_duration > 0 else None, record_name, log_files, csv_file)
    else:
        print("Chyba: Nepodařilo se načíst data z žádného logu")
        sys.exit(1)
