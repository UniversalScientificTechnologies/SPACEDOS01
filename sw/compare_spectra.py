#!/usr/bin/env python3
# %%% Import libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

# %%% Configuration
# List of CSV files to plot
csv_files = [
    'log/SPACEDOS01_20260115_121635_am_test.csv',
    'log/SPACEDOS01_20260115_122537_cs_test.csv',
    'log/SPACEDOS01_20260115_131244_pu_test.csv',
    'log/SPACEDOS01_20260115_143021_co60_test.csv',
    'log/SPACEDOS01_20260115_145011_zn65_test.csv'
]

# Calibration coefficients
# Energy (keV) = a * channel + b
a = 24.995  # keV per channel
b = 337.1   # offset in keV

a = 35
b = 500

# Energy markers (vertical lines) in keV
energy_markers = [
    # (59.54,   'Am-241 γ (59.54 keV)'),
    (661.66,  'Cs-137 γ (661.66 keV)'),
    (1115.5, 'Zn-65 γ (1.1155 MeV)'),
    (1173.23, 'Co-60 γ (1.173 MeV)'),
    (1332.49, 'Co-60 γ (1.332 MeV)'),
    (5486,    'Am-241 α (5.486 MeV)'),
    (5157,    'Pu-239 α (5.157 MeV)'),
]

# %%% Load data
spectra = []
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    df['Energy'] = a * df['Channel'] + b
    label = os.path.splitext(os.path.basename(csv_file))[0]
    spectra.append({'data': df, 'label': label, 'file': csv_file})

# %%% Overlay plot
fig, ax = plt.subplots(figsize=(14, 6))

colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

for i, spectrum in enumerate(spectra):
    df = spectrum['data']
    color = colors[i % len(colors)]
    ax.step(df['Channel'], df['Count'], where='mid', linewidth=1.5, 
            color=color, alpha=0.8, label=spectrum['label'])

ax.set_ylabel('Count')
ax.set_yscale('log')
ax.set_title('Spectral Comparison')
ax.set_xlabel('Channel')
ax.legend()

# Create secondary x-axis for energy (in MeV)
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
ax_energy = ax.twiny()
ax_energy.set_xlim((ax.get_xlim()[0] * a + b) / 1000, (ax.get_xlim()[1] * a + b) / 1000)
ax_energy.set_xlabel(f'Energy (MeV) - E = {a:.3f} × Ch + {b:.1f} keV')
ax_energy.xaxis.set_minor_locator(AutoMinorLocator(5))
ax_energy.grid(True, alpha=0.5, which='major', linewidth=1.0)
ax_energy.grid(True, alpha=0.3, which='minor', linestyle=':', linewidth=0.6)

# Add energy markers
ylim = ax.get_ylim()
y_positions = [0.95, 0.85, 0.75, 0.65]  # Stagger labels vertically
for i, (energy, label) in enumerate(energy_markers):
    channel = (energy - b) / a
    ax.axvline(x=channel, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    y_pos = ylim[0] * (ylim[1]/ylim[0]) ** y_positions[i % len(y_positions)]
    ax.text(channel + 1, y_pos, label, rotation=0, 
            verticalalignment='center', color='red', fontsize=8, 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='red'))

plt.tight_layout()
plt.savefig('log/compare.png', dpi=300, bbox_inches='tight')
print('Graf uložen do: log/compare.png')
plt.show()
