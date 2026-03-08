#!/usr/bin/env python3
# %%% Import libraries
import pandas as pd
import plotly.graph_objects as go
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
a = 35
b = 500

# Energy markers (vertical lines) in keV
energy_markers = [
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
    df['Energy_MeV'] = (a * df['Channel'] + b) / 1000
    label = os.path.splitext(os.path.basename(csv_file))[0]
    spectra.append({'data': df, 'label': label, 'file': csv_file})

# %%% Create interactive plot
fig = go.Figure()

colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

for i, spectrum in enumerate(spectra):
    df = spectrum['data']
    color = colors[i % len(colors)]
    
    fig.add_trace(go.Scatter(
        x=df['Energy_MeV'],
        y=df['Count'],
        mode='lines',
        name=spectrum['label'],
        line=dict(color=color, width=1.5, shape='hv'),
        hovertemplate='<b>%{fullData.name}</b><br>Energy: %{x:.3f} MeV<br>Count: %{y}<br>Channel: %{customdata}<extra></extra>',
        customdata=df['Channel']
    ))

# Add energy markers
for energy, label in energy_markers:
    energy_mev = energy / 1000
    fig.add_vline(
        x=energy_mev,
        line_dash="dash",
        line_color="red",
        line_width=1.5,
        opacity=0.7,
        annotation_text=label,
        annotation_position="top left",
        annotation_textangle=0,
        annotation_font=dict(size=9, color="red"),
        annotation_bgcolor="rgba(255,255,255,0.7)",
        annotation_bordercolor="red"
    )

# Update layout
fig.update_layout(
    title=f'Spectral Comparison - E = {a:.3f} × Ch + {b:.1f} keV',
    xaxis_title='Energy (MeV)',
    yaxis_title='Count',
    yaxis_type='log',
    hovermode='closest',
    width=1400,
    height=700,
    template='plotly_white',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99
    )
)

# Update grid
fig.update_xaxes(
    showgrid=True,
    gridwidth=1,
    gridcolor='LightGray',
    minor=dict(
        showgrid=True,
        gridwidth=0.5,
        gridcolor='LightGray',
        griddash='dot',
        nticks=20
    )
)

fig.update_yaxes(
    showgrid=True,
    gridwidth=1,
    gridcolor='LightGray'
)

# %%% Save and show
output_file = 'log/compare_interactive.html'
fig.write_html(output_file)
print(f'Interaktivní graf uložen do: {output_file}')

fig.show()
