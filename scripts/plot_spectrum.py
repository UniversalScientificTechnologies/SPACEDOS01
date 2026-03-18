# %%
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import numpy as np


# %%
# Input log file (timestamp,$MSG,hex,hex,...)
parser = argparse.ArgumentParser(description="Plot SPACEDOS01B spectra from a log file.")
parser.add_argument(
    "log_file",
    nargs="?",
    default=str(Path(__file__).with_name("zaznam.txt")),
    help="Path to log file (default: scripts/zaznam.txt)",
)
parser.add_argument(
    "--mode",
    choices=("avg", "sum"),
    default="avg",
    help="Aggregate HKSD channels using average or sum (default: avg)",
)
parser.add_argument(
    "--log-y",
    action="store_true",
    help="Use logarithmic scale for Y axis",
)
parser.add_argument(
    "--title",
    default="",
    help="Extra text appended to the plot title",
)
args = parser.parse_args()
LOG_PATH = Path(args.log_file)


# %%
def parse_hex(value: str) -> int:
    return int(value, 16)


def parse_line(line: str):
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return None
    try:
        timestamp = int(parts[0])
    except ValueError:
        return None
    return timestamp, parts[1], parts[2:]


hksd_records = []

for raw_line in LOG_PATH.read_text(encoding="utf-8").splitlines():
    if not raw_line or raw_line.lstrip().startswith("#"):
        continue
    parsed = parse_line(raw_line)
    if not parsed:
        continue

    timestamp, msg, fields = parsed
    if msg == "$HKSD" and len(fields) >= 4:
        count = parse_hex(fields[0])
        uptime = parse_hex(fields[1])
        suppress = parse_hex(fields[2])
        base_offset = parse_hex(fields[3])
        channels = [parse_hex(v) for v in fields[4:] if v]
        hksd_records.append(
            {
                "timestamp": timestamp,
                "count": count,
                "uptime": uptime,
                "suppress": suppress,
                "base_offset": base_offset,
                "channels": channels,
            }
        )


# %%
# Plot HKSD (first 50 channels from base_offset)
if not hksd_records:
    raise SystemExit("No $HKSD records found in the log.")


# %%
# Exposure time estimation (prefer HKSD uptime, fallback to log timestamps)
def format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


first_uptime = hksd_records[0]["uptime"]
last_uptime = hksd_records[-1]["uptime"]
timestamp_span = hksd_records[-1]["timestamp"] - hksd_records[0]["timestamp"]
if last_uptime >= first_uptime:
    exposure_seconds = last_uptime - first_uptime
    source = "HKSD uptime"
else:
    exposure_seconds = timestamp_span
    source = "log timestamps"

exposure_label = format_duration(exposure_seconds)
print(f"Estimated exposure time: {exposure_label} ({source})")
print(f"Timestamp span: {format_duration(timestamp_span)} (log timestamps)")


# %%
sum_by_idx: dict[int, int] = defaultdict(int)
count_by_idx: dict[int, int] = defaultdict(int)
base_offsets = []
for rec in hksd_records:
    base_offsets.append(rec["base_offset"])
    for i, value in enumerate(rec["channels"]):
        sum_by_idx[i] += value
        count_by_idx[i] += 1

agg_indices = np.array(sorted(sum_by_idx.keys()))
if args.mode == "sum":
    agg_values = np.array([sum_by_idx[i] for i in agg_indices])
else:
    agg_values = np.array([sum_by_idx[i] / count_by_idx[i] for i in agg_indices])

base_offset_mode = max(set(base_offsets), key=base_offsets.count)
title_suffix = f" | {args.title}" if args.title else ""

plt.figure(figsize=(9, 4))
plt.step(agg_indices, agg_values, where="mid", label=f"HKSD {args.mode}")
plt.axvline(0, color="tab:red", linestyle="--", linewidth=1, label="base_offset start")
plt.title(
    f"SPACEDOS01B - HKSD spectrum (50 channels) | exposure {exposure_label} | base_offset {base_offset_mode}{title_suffix}"
)
plt.xlabel("Channel index (0-49)")
plt.ylabel("Counts")
if args.log_y:
    plt.yscale("log")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
