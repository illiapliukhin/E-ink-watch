#!/usr/bin/env python3
"""Replay Pass-AG KEEP edits (in-place, no sexpr reorder).

Applies any KEEP whose source via is still at the pre-KEEP coordinate.
Safe on a board that already has a prefix of the KEEP list.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import (
    load,
    save,
    set_fp_at,
    set_seg_ends,
    set_via_at,
    set_via_size_drill,
)

text = load()
applied = []

text, n_via = set_via_at(text, 109.5, 106.0, 108.55, 106.0)
if n_via == 1:
    text, n_sz = set_via_size_drill(text, 108.55, 106.0, 0.35, 0.15)
    text, n_f = set_seg_ends(
        text, 109.5, 106.0, 110.2, 106.0, 108.55, 106.0, 110.2, 106.0, layer="F.Cu"
    )
    if n_sz != 1 or n_f != 1:
        raise SystemExit(f"iset_via_west partial via={n_via} size={n_sz} F={n_f}")
    applied.append("iset_via_west")

text, n_via = set_via_at(text, 110.4, 105.65, 107.8, 105.65)
if n_via == 1:
    text, n_sz = set_via_size_drill(text, 107.8, 105.65, 0.25, 0.15)
    if n_sz != 1:
        raise SystemExit(f"ts_via_corner size match failed {n_sz}")
    applied.append("ts_via_corner")

text, n_via = set_via_at(text, 111.45, 105.8, 110.75, 105.8)
if n_via == 1:
    text, n_sz = set_via_size_drill(text, 110.75, 105.8, 0.2, 0.15)
    text, n_ilim_f = set_seg_ends(
        text, 110.6, 106.0, 111.45, 105.8, 110.6, 106.0, 110.6, 106.02, layer="F.Cu"
    )
    text, n_cd = set_seg_ends(
        text, 112.8, 106.8, 110.6, 106.8, 110.6, 106.8, 110.63, 106.8, layer="F.Cu"
    )
    text, n_cd_v = set_seg_ends(
        text, 112.8, 108.26, 112.8, 106.8, 112.8, 108.26, 112.8, 108.41, layer="F.Cu"
    )
    text, n_ts_h = set_seg_ends(
        text, 110.4, 106.0, 111.0, 106.0, 111.0, 106.0, 111.0, 106.12, layer="F.Cu"
    )
    text, n_ts_v = set_seg_ends(
        text, 110.4, 105.65, 110.4, 106.0, 111.0, 106.0, 111.0, 106.12, layer="F.Cu"
    )
    text = set_fp_at(text, "R_SCL", "108.8 109.8 90")
    if n_sz != 1 or n_ilim_f != 1 or n_cd != 1 or n_cd_v != 1 or n_ts_h != 1 or n_ts_v != 1:
        raise SystemExit("sol_combo_west partial match")
    applied.append("sol_combo_west")

if not applied:
    if "(at 110.75 105.8)" in text and "(at 108.8 109.8 90)" in text:
        print("Pass-AG keeps already present: iset_via_west, ts_via_corner, sol_combo_west")
        sys.exit(0)
    raise SystemExit("no Pass-AG KEEP source vias found")

save(text)
print("Pass-AG keeps applied: " + ", ".join(applied))
