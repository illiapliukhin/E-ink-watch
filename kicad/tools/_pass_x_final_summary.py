#!/usr/bin/env python3
"""Pass-X final state verifier."""
import re, hashlib
from pathlib import Path
from collections import Counter
import pcbnew

BOARD = Path("e-ink-watch.kicad_pcb")
text = Path("reports/drc_after_passx.txt").read_text()
pairs = Counter()
for b in re.split(r"\[shorting_items\]:", text)[1:]:
    m = re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
    if m:
        pairs[tuple(sorted(m.groups()))] += 1
print("shorting", text.count("[shorting_items]"), "unc", text.count("[unconnected_items]"))
print("pairs", dict(pairs) if pairs else "NONE")
b = pcbnew.LoadBoard(str(BOARD))
for ref in ("C_VINLS", "C_SYS", "C_PMID", "C_LDO", "R_SDA"):
    for f in b.GetFootprints():
        if f.GetReference() == ref:
            print(f"{ref} @({f.GetPosition().x/1e6:.2f},{f.GetPosition().y/1e6:.2f})")
print("md5", hashlib.md5(BOARD.read_bytes()).hexdigest())
