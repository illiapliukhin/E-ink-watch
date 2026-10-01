#!/usr/bin/env python3
"""DRC gate for Pass-AI. Usage: python3 tools/_pass_ai_gate.py <label>

KEEP only when shorting==0, power pairs stay 0, pocket stays 0, and
unconnected is strictly below backups/_passah_unc.txt. Otherwise restore
backups/_passah_last_ok.kicad_pcb.
"""
import re
import sys
import shutil
from pathlib import Path
from collections import Counter

label = sys.argv[1]
text = Path(f"reports/_drc_passai_{label}.txt").read_text()
pairs = Counter()
for block in re.split(r"\[shorting_items\]:", text)[1:]:
    match = re.search(r"nets ([^\s]+) and ([^\s\)]+)", block.split("\n[")[0])
    if match:
        pairs[tuple(sorted(match.groups()))] += 1

shorting_count = text.count("[shorting_items]")
unconnected_count = text.count("[unconnected_items]")
previous_path = Path("backups/_passah_unc.txt")
previous_unconnected = int(previous_path.read_text().strip()) if previous_path.exists() else 10**9
unconnected_dropped = unconnected_count < previous_unconnected
power_pairs = [
    ("GND", "VBUS"),
    ("GND", "VBAT"),
    ("GND", "VBUS_POGO"),
    ("3V3", "GND"),
    ("3V3_DISP", "GND"),
    ("GND", "SW"),
    ("3V3", "3V3_DISP"),
    ("GND", "VSYS"),
]
power_ok = all(pairs.get(tuple(sorted(pair)), 0) == 0 for pair in power_pairs)
pocket_pairs = [("PMID", "VBUS"), ("3V3_DISP", "PMID"), ("PMID", "SW")]
pocket_ok = all(pairs.get(tuple(sorted(pair)), 0) == 0 for pair in pocket_pairs)

print(
    f"{label}: shorting={shorting_count} unc={unconnected_count} "
    f"prev_unc={previous_unconnected} power_ok={power_ok} pocket_ok={pocket_ok} "
    f"pairs={dict(pairs) if pairs else None}"
)

if shorting_count or not power_ok or not pocket_ok or not unconnected_dropped:
    shutil.copy("backups/_passah_last_ok.kicad_pcb", "e-ink-watch.kicad_pcb")
    print("REVERT")
    for block in re.split(r"\[shorting_items\]:", text)[1:][:8]:
        print(block.split("\n[")[0][:360])
    sys.exit(1)

shutil.copy("e-ink-watch.kicad_pcb", "backups/_passah_last_ok.kicad_pcb")
previous_path.write_text(f"{unconnected_count}\n")
print("KEEP")
