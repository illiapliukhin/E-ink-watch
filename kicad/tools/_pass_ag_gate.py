#!/usr/bin/env python3
"""DRC gate for Pass-AG. Usage: python3 tools/_pass_ag_gate.py <label>"""
import re
import sys
import shutil
from pathlib import Path
from collections import Counter

label = sys.argv[1]
text = Path(f"reports/_drc_passag_{label}.txt").read_text()
pairs = Counter()
for block in re.split(r"\[shorting_items\]:", text)[1:]:
    match = re.search(r"nets ([^\s]+) and ([^\s\)]+)", block.split("\n[")[0])
    if match:
        pairs[tuple(sorted(match.groups()))] += 1

shorting_count = text.count("[shorting_items]")
unconnected_count = text.count("[unconnected_items]")
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
    f"power_ok={power_ok} pocket_ok={pocket_ok} pairs={dict(pairs) if pairs else None}"
)

if shorting_count or not power_ok or not pocket_ok:
    shutil.copy("backups/_passag_last_ok.kicad_pcb", "e-ink-watch.kicad_pcb")
    print("REVERT")
    for block in re.split(r"\[shorting_items\]:", text)[1:][:8]:
        print(block.split("\n[")[0][:360])
    sys.exit(1)

shutil.copy("e-ink-watch.kicad_pcb", "backups/_passag_last_ok.kicad_pcb")
print("KEEP")
