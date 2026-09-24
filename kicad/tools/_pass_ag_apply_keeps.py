#!/usr/bin/env python3
"""Replay Pass-AG KEEP edits (in-place, no sexpr reorder).

Applies any KEEP whose source via is still at the pre-KEEP coordinate.
Safe on a board that already has a prefix of the KEEP list.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import (
    add_segment,
    add_via,
    load,
    netnum,
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

has_rscl_3v3 = (
    "(start 108.8 109.29)" in text
    or "(end 108.8 109.29)" in text
    or "(start 106.5 109.59)" in text
)
if "(at 108.8 109.8 90)" in text and not has_rscl_3v3:
    rail_3v3_net = netnum(text, "3V3")
    text = add_segment(text, 108.8, 109.29, 110.5, 109.29, 0.12, "F.Cu", rail_3v3_net)
    text = add_segment(text, 110.5, 109.29, 110.5, 108.25, 0.12, "F.Cu", rail_3v3_net)
    text = add_segment(text, 110.5, 108.25, 110.16, 108.25, 0.12, "F.Cu", rail_3v3_net)
    applied.append("sol_rscl_3v3")
    has_rscl_3v3 = True

has_lsctrl_tie = "(end 112.16 107.8)" in text or "(start 112.16 107.8)" in text
if "(at 114.6 108.25 90)" in text and not has_lsctrl_tie:
    rail_3v3_net = netnum(text, "3V3")
    text = add_segment(text, 112.51, 107.8, 112.16, 107.8, 0.2, "F.Cu", rail_3v3_net)
    applied.append("sol_3v3_lsctrl_tie")
    has_lsctrl_tie = True

has_cd_e2 = "(at 110.6 106.95)" in text
if has_lsctrl_tie and not has_cd_e2:
    cd_net = netnum(text, "CD")
    text = add_via(text, 110.6, 106.95, 0.25, 0.15, cd_net)
    text = add_segment(text, 110.6, 106.8, 110.6, 106.95, 0.15, "F.Cu", cd_net)
    text = add_segment(text, 110.6, 106.95, 112.65, 106.95, 0.12, "B.Cu", cd_net)
    text = add_segment(text, 112.65, 106.95, 112.65, 108.41, 0.12, "B.Cu", cd_net)
    text = add_segment(text, 112.65, 108.41, 113.3, 108.41, 0.12, "B.Cu", cd_net)
    applied.append("sol_cd_e2_via")
    has_cd_e2 = True

has_ilim_dog = "(start 110.75 106.0)" in text
if has_cd_e2 and not has_ilim_dog:
    ilim_net = netnum(text, "ILIM")
    text = add_segment(text, 110.6, 106.0, 110.75, 106.0, 0.08, "F.Cu", ilim_net)
    text = add_segment(text, 110.75, 106.0, 110.75, 105.8, 0.08, "F.Cu", ilim_net)
    applied.append("sol_ilim_c2_dogbone")
    has_ilim_dog = True

has_rscl_west = "(at 106.5 110.1 90)" in text
if has_ilim_dog and "(at 108.8 109.8 90)" in text and not has_rscl_west:
    text = set_fp_at(text, "R_SCL", "106.5 110.1 90")
    text, n_h = set_seg_ends(
        text, 108.8, 109.29, 110.5, 109.29, 106.5, 109.59, 110.5, 109.59, layer="F.Cu"
    )
    text, n_v = set_seg_ends(
        text, 110.5, 109.29, 110.5, 108.25, 110.5, 109.59, 110.5, 108.25, layer="F.Cu"
    )
    if n_h != 1 or n_v != 1:
        raise SystemExit(f"sol_rscl_west 3V3 follow H={n_h} V={n_v}")
    applied.append("sol_rscl_west")
    has_rscl_west = True

has_gnd_d5 = "(at 112.4 106.55)" in text
has_gnd_d5_tie = "(start 112.8 106.55)" in text or "(end 112.8 106.55)" in text
if has_rscl_west and not has_gnd_d5:
    ground_net = netnum(text, "GND")
    text = add_via(text, 112.4, 106.55, 0.25, 0.15, ground_net)
    text = add_segment(text, 111.8, 106.4, 112.4, 106.4, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 112.4, 106.4, 112.4, 106.55, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 112.4, 106.55, 112.8, 106.55, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 112.8, 106.55, 112.8, 107.24, 0.12, "F.Cu", ground_net)
    applied.append("sol_gnd_d5_via")
    has_gnd_d5 = True
    has_gnd_d5_tie = True
elif has_gnd_d5 and not has_gnd_d5_tie:
    ground_net = netnum(text, "GND")
    text = add_segment(text, 112.4, 106.55, 112.8, 106.55, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 112.8, 106.55, 112.8, 107.24, 0.12, "F.Cu", ground_net)
    applied.append("sol_gnd_d5_tie")
    has_gnd_d5_tie = True

has_3v3_west = "(at 110.4 108.25)" in text
if has_gnd_d5_tie and not has_3v3_west:
    rail_3v3_net = netnum(text, "3V3")
    text = add_via(text, 110.4, 108.25, 0.25, 0.15, rail_3v3_net)
    text = add_segment(text, 110.4, 108.25, 110.4, 108.55, 0.12, "B.Cu", rail_3v3_net)
    text = add_segment(text, 110.4, 108.55, 102.52, 108.55, 0.12, "B.Cu", rail_3v3_net)
    text = add_segment(text, 102.52, 108.55, 102.52, 109.4, 0.12, "B.Cu", rail_3v3_net)
    applied.append("sol_3v3_west_via")
    has_3v3_west = True

has_ntc_west = "(at 103.0 107.2)" in text
if has_3v3_west and not has_ntc_west:
    ts_net = netnum(text, "TS")
    ground_net = netnum(text, "GND")
    text = set_fp_at(text, "NTC_BAT", "103.0 107.2")
    text, n_ts_diag = set_seg_ends(
        text, 108.71, 107.0, 107.69, 108.15, 108.51, 107.0, 108.71, 107.0, layer="F.Cu"
    )
    text, n_ts_stub = set_seg_ends(
        text, 107.69, 108.15, 107.69, 107.55, 108.51, 107.0, 108.51, 107.12, layer="F.Cu"
    )
    text, n_gnd = set_seg_ends(
        text, 108.71, 108.15, 108.71, 108.6, 108.71, 108.6, 109.5, 108.6, layer="F.Cu"
    )
    if n_ts_diag != 1 or n_ts_stub != 1 or n_gnd != 1:
        raise SystemExit(
            f"sol_ntc_west follow TS_diag={n_ts_diag} TS_stub={n_ts_stub} GND={n_gnd}"
        )
    text = add_via(text, 102.49, 107.55, 0.25, 0.15, ts_net)
    text = add_segment(text, 102.49, 107.2, 102.49, 107.55, 0.15, "F.Cu", ts_net)
    text = add_segment(text, 102.49, 107.55, 108.51, 107.55, 0.12, "B.Cu", ts_net)
    text = add_segment(text, 108.51, 107.55, 108.51, 107.0, 0.12, "B.Cu", ts_net)
    text = add_segment(text, 103.51, 107.2, 103.48, 107.2, 0.2, "F.Cu", ground_net)
    text = add_segment(text, 103.48, 107.2, 103.48, 108.8, 0.2, "F.Cu", ground_net)
    applied.append("sol_ntc_west")
    has_ntc_west = True

has_cbat_north = "(at 107.5 108.5)" in text
if has_ntc_west and not has_cbat_north:
    text = set_fp_at(text, "C_BAT", "107.5 108.5")
    text, n_vbat = set_seg_ends(
        text, 107.02, 108.8, 107.02, 106.4, 107.02, 108.5, 107.02, 106.4, layer="F.Cu"
    )
    text, n_gnd_h = set_seg_ends(
        text, 107.98, 108.8, 109.5, 108.8, 107.98, 108.5, 109.5, 108.5, layer="F.Cu"
    )
    text, n_gnd_v = set_seg_ends(
        text, 109.5, 108.8, 109.5, 108.6, 109.5, 108.5, 109.5, 108.6, layer="F.Cu"
    )
    if n_vbat != 1 or n_gnd_h != 1 or n_gnd_v != 1:
        raise SystemExit(
            f"sol_cbat_north follow VBAT={n_vbat} GND_H={n_gnd_h} GND_V={n_gnd_v}"
        )
    applied.append("sol_cbat_north")
    has_cbat_north = True

if not applied:
    if "(at 110.75 105.8)" in text and (
        "(at 108.8 109.8 90)" in text or has_rscl_west
    ):
        extra = ""
        if has_rscl_3v3:
            extra += ", sol_rscl_3v3"
        if has_lsctrl_tie:
            extra += ", sol_3v3_lsctrl_tie"
        if has_cd_e2:
            extra += ", sol_cd_e2_via"
        if has_ilim_dog:
            extra += ", sol_ilim_c2_dogbone"
        if has_rscl_west:
            extra += ", sol_rscl_west"
        if has_gnd_d5:
            extra += ", sol_gnd_d5_via"
        if has_gnd_d5_tie:
            extra += ", sol_gnd_d5_tie"
        if has_3v3_west:
            extra += ", sol_3v3_west_via"
        if has_ntc_west:
            extra += ", sol_ntc_west"
        if has_cbat_north:
            extra += ", sol_cbat_north"
        print(
            "Pass-AG keeps already present: "
            f"iset_via_west, ts_via_corner, sol_combo_west{extra}"
        )
        sys.exit(0)
    raise SystemExit("no Pass-AG KEEP source vias found")

save(text)
print("Pass-AG keeps applied: " + ", ".join(applied))
