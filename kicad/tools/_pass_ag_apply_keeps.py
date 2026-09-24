#!/usr/bin/env python3
"""Replay Pass-AG KEEP edits onto the Pass-AF board (in-place, no sexpr reorder)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import save, set_seg_ends, set_via_at, set_via_size_drill, load

text = load()
text, n_via = set_via_at(text, 109.5, 106.0, 108.55, 106.0)
text, n_sz = set_via_size_drill(text, 108.55, 106.0, 0.35, 0.15)
text, n_f = set_seg_ends(
    text, 109.5, 106.0, 110.2, 106.0, 108.55, 106.0, 110.2, 106.0, layer="F.Cu"
)
if n_via != 1 or n_sz != 1 or n_f != 1:
    raise SystemExit(f"Pass-AG keep match failed via={n_via} size={n_sz} F={n_f}")
save(text)
print("Pass-AG keeps applied: iset_via_west")
