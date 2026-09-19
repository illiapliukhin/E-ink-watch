#!/usr/bin/env python3
"""DRC gate for Pass-Z. Usage: _pass_z_gate.py <label>"""
import re, sys, shutil
from pathlib import Path
from collections import Counter

label = sys.argv[1]
text = Path(f"reports/_drc_passz_{label}.txt").read_text()
pairs = Counter()
for b in re.split(r"\[shorting_items\]:", text)[1:]:
    m = re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
    if m:
        pairs[tuple(sorted(m.groups()))] += 1
s, u = text.count("[shorting_items]"), text.count("[unconnected_items]")
POWER = [("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
pok = all(pairs.get(tuple(sorted(p)), 0) == 0 for p in POWER)
pocket = all(pairs.get(k, 0) == 0 for k in [("PMID","VBUS"),("3V3_DISP","PMID"),("PMID","SW")])
print(f"{label}: shorting={s} unc={u} power_ok={pok} pocket_ok={pocket} pairs={dict(pairs) if pairs else None}")
if s or not pok or not pocket:
    shutil.copy("backups/_passz_last_ok.kicad_pcb", "e-ink-watch.kicad_pcb")
    print("REVERT")
    for b in re.split(r"\[shorting_items\]:", text)[1:][:5]:
        print(b.split("\n[")[0][:320])
    sys.exit(1)
shutil.copy("e-ink-watch.kicad_pcb", "backups/_passz_last_ok.kicad_pcb")
print("KEEP")
# stitch check
t = Path("e-ink-watch.kicad_pcb").read_text()
if "111.05" not in t and "111.05 103.85" not in t:
    # soft warn
    if "111.05 105.2" not in t:
        print("WARN: stitch coords may be missing")
