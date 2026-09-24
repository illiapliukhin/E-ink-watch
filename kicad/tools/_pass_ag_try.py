#!/usr/bin/env python3
"""Named Pass-AG edits: move parts and reroute to open U2 east/south corridors."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import (
    add_segment,
    add_via,
    del_segments_at,
    del_via,
    load,
    netnum,
    save,
    set_fp_at,
    set_seg_ends,
    set_via_at,
    set_via_size_drill,
)

edit_name = sys.argv[1]
text = load()
ground_net = netnum(text, "GND")
disp_net = netnum(text, "3V3_DISP")
vsys_net = netnum(text, "VSYS")
cd_net = netnum(text, "CD")
sda_net = netnum(text, "SDA")
scl_net = netnum(text, "SCL")
pmic_int_net = netnum(text, "PMIC_INT")
rail_3v3_net = netnum(text, "3V3")
ts_net = netnum(text, "TS")
ilim_net = netnum(text, "ILIM")

if edit_name == "iset_via_west":
    # In-place: slide ISET via off the C1 pocket so ILIM/TS can use 109.5,106 later.
    # Shrink 0.5→0.35 so it does not clip VBAT @x=108.12.
    text, n_via = set_via_at(text, 109.5, 106.0, 108.55, 106.0)
    text, n_sz = set_via_size_drill(text, 108.55, 106.0, 0.35, 0.15)
    text, n_f = set_seg_ends(
        text, 109.5, 106.0, 110.2, 106.0, 108.55, 106.0, 110.2, 106.0, layer="F.Cu"
    )
    print(f"iset_via_west via={n_via} size={n_sz} F={n_f}")
    if n_via != 1 or n_f != 1:
        raise SystemExit("iset_via_west failed to match")

elif edit_name == "ilim_via_west":
    # In-place + one PMID-insert jog: inner ILIM via off PMID B4/C4.
    # Lands in the hole left by iset_via_west.
    text, n_via = set_via_at(text, 111.45, 105.8, 109.5, 105.9)
    text, n_sz = set_via_size_drill(text, 109.5, 105.9, 0.32, 0.15)
    text, n_f = set_seg_ends(
        text, 110.6, 106.0, 111.45, 105.8, 110.6, 105.9, 109.5, 105.9, layer="F.Cu"
    )
    text, n_b = set_seg_ends(
        text, 111.45, 105.8, 110.3, 105.8, 109.5, 105.9, 110.3, 105.9, layer="B.Cu"
    )
    text = add_segment(text, 110.6, 106.0, 110.6, 105.9, 0.08, "F.Cu", ilim_net)
    print(f"ilim_via_west via={n_via} size={n_sz} F={n_f} B={n_b}")
    if n_via != 1 or n_f != 1 or n_b != 1:
        raise SystemExit("ilim_via_west failed to match")

elif edit_name == "cd_stub_south":
    # In-place only: turn the E-row CD haul into a short south stub on E2.
    # Clears E3/E4/E5 without inserting copper (avoids sexpr-order flake).
    text, n1 = set_seg_ends(
        text, 112.8, 106.8, 110.6, 106.8, 110.6, 106.8, 110.6, 107.15, layer="F.Cu"
    )
    print(f"cd_stub_south n1={n1}")
    if n1 != 1:
        raise SystemExit("cd_stub_south failed to match")

elif edit_name == "rotate_rscl_90":
    # KiCad 0402 rot 90 maps pad 1 to +Y (clockwise), pad 2 to -Y.
    # gpt-6-sol proposed (112.70, 108.80) 90 with pad1 at y-0.51 — that is pad 2.
    # Origin south of 3V3 y=108.25 so the E5 stub does not cross that rail.
    text = set_fp_at(text, "R_SCL", "112.7 109.25 90")
    text, n_scl = set_seg_ends(
        text, 111.8, 106.8, 111.14, 107.6, 111.8, 106.8, 111.8, 107.15, layer="F.Cu"
    )
    text = add_segment(text, 111.8, 107.15, 112.7, 107.15, 0.12, "F.Cu", scl_net)
    text = add_segment(text, 112.7, 107.15, 112.7, 108.74, 0.12, "F.Cu", scl_net)
    text = add_segment(text, 112.7, 109.76, 112.5, 109.76, 0.15, "F.Cu", rail_3v3_net)
    text = add_segment(text, 112.5, 109.76, 112.5, 109.0, 0.15, "F.Cu", rail_3v3_net)
    print(f"rotate_rscl_90 scl={n_scl}")
    if n_scl != 1:
        raise SystemExit("rotate_rscl_90 SCL stub not matched")

elif edit_name == "move_rscl_east":
    # R_SCL pad 1 sits on SDA vertical x=111.4. Slide +0.50 X.
    text = set_fp_at(text, "R_SCL", "112.5 107.7")
    text, n_scl = set_seg_ends(
        text, 111.8, 106.8, 111.14, 107.6, 111.8, 106.8, 111.99, 107.7, layer="F.Cu"
    )
    text, n_3v3 = set_seg_ends(
        text, 112.51, 107.8, 114.6, 107.8, 113.01, 107.7, 114.6, 107.8, layer="F.Cu"
    )
    print(f"move_rscl_east scl={n_scl} 3v3={n_3v3}")
    if n_scl != 1:
        raise SystemExit("move_rscl_east SCL stub not matched")

elif edit_name == "nudge_cd_south":
    # In-place: CD E-row y=106.8 → 108.05, off E3/E4/E5. Stub E2 south (PMID insert).
    text, n1 = set_seg_ends(
        text, 112.8, 106.8, 110.6, 106.8, 112.8, 108.05, 110.45, 108.05, layer="F.Cu"
    )
    text, n2 = set_seg_ends(
        text, 112.8, 108.26, 112.8, 106.8, 112.8, 108.26, 112.8, 108.05, layer="F.Cu"
    )
    text = add_segment(text, 110.6, 106.8, 110.45, 107.2, 0.1, "F.Cu", cd_net)
    text = add_segment(text, 110.45, 107.2, 110.45, 108.05, 0.1, "F.Cu", cd_net)
    print(f"nudge_cd_south n1={n1} n2={n2}")
    if n1 != 1 or n2 != 1:
        raise SystemExit("nudge_cd_south failed to match")

elif edit_name == "sol_combo_west":
    # gpt-6-sol vision KEEP, geometrically corrected:
    # - ILIM via 0.25@(110.80,105.80) still clips PMID F; use 0.20@(110.75,105.80).
    # - R_SCL (108.8,109.8,90) is F.Cu-clear (TP6 pad is B.Cu only).
    # - Also retract CD vertical x=112.8 which crosses 3V3 F y=107.8.
    text, n_via = set_via_at(text, 111.45, 105.8, 110.75, 105.8)
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
    print(
        f"sol_combo_west via={n_via} sz={n_sz} ilimF={n_ilim_f} "
        f"cd={n_cd} cdV={n_cd_v} ts={n_ts_h,n_ts_v}"
    )
    if n_via != 1 or n_ilim_f != 1 or n_cd != 1 or n_cd_v != 1 or n_ts_h != 1 or n_ts_v != 1:
        raise SystemExit("sol_combo_west failed to match")

elif edit_name == "ts_via_corner":
    # gpt-6-sol first KEEP was (108.00, 105.65) 0.35 — that overlaps VBAT F @x=108.12
    # w=0.35 and ISET B @x=108.20. Park on the existing TS B.Cu elbow instead.
    # In-place only: via already sits on (107.8, 105.65)-(110.4, 105.65).
    text, n_via = set_via_at(text, 110.4, 105.65, 107.8, 105.65)
    text, n_sz = set_via_size_drill(text, 107.8, 105.65, 0.25, 0.15)
    print(f"ts_via_corner via={n_via} size={n_sz}")
    if n_via != 1 or n_sz != 1:
        raise SystemExit("ts_via_corner failed to match")

elif edit_name == "ts_f_retract":
    # After ts_via_corner: F stubs (110.4,105.65)-(110.4,106.0)-(111.0,106.0)
    # still overlap VBAT y=105.6 and run through C2 ILIM. Collapse onto the
    # existing C3 stub (111.0,106.0)-(111.0,106.12). C3 stays an island until
    # a later orthogonal escape. No new copper.
    text, n1 = set_seg_ends(
        text, 110.4, 105.65, 110.4, 106.0, 111.0, 106.0, 111.0, 106.12, layer="F.Cu"
    )
    text, n2 = set_seg_ends(
        text, 110.4, 106.0, 111.0, 106.0, 111.0, 106.0, 111.0, 106.12, layer="F.Cu"
    )
    print(f"ts_f_retract n1={n1} n2={n2}")
    if n1 != 1 or n2 != 1:
        raise SystemExit("ts_f_retract failed to match")

elif edit_name == "ilim_via_slide":
    # Via-only, on existing ILIM B.Cu y=105.80. Scan after ts_via_corner:
    # (110.75, 105.80) size 0.20 is overlap-clear of PMID/VBAT/TS; 0.22 also
    # clear. Do not set_seg_ends (ts_f_retract flake: SCL↔SDA + TS↔ILIM).
    # F stub still ends at 111.45,105.8 on PMID — later retract.
    text, n_via = set_via_at(text, 111.45, 105.8, 110.75, 105.8)
    text, n_sz = set_via_size_drill(text, 110.75, 105.8, 0.2, 0.15)
    print(f"ilim_via_slide via={n_via} size={n_sz}")
    if n_via != 1 or n_sz != 1:
        raise SystemExit("ilim_via_slide failed to match")

elif edit_name == "ilim_via_park":
    # Sol temp park (109.65, 106.30) 0.30 is overlap-clear of pads, but the
    # one-segment F diagonal C2→park clips C1 ISET. Do not run as-is.
    text, n_via = set_via_at(text, 111.45, 105.8, 109.65, 106.3)
    text, n_sz = set_via_size_drill(text, 109.65, 106.3, 0.3, 0.15)
    text, n_f = set_seg_ends(
        text, 110.6, 106.0, 111.45, 105.8, 110.6, 106.0, 109.65, 106.3, layer="F.Cu"
    )
    text, n_b = set_seg_ends(
        text, 111.45, 105.8, 110.3, 105.8, 109.65, 106.3, 110.3, 105.8, layer="B.Cu"
    )
    print(f"ilim_via_park via={n_via} size={n_sz} F={n_f} B={n_b}")
    if n_via != 1 or n_f != 1 or n_b != 1:
        raise SystemExit("ilim_via_park failed to match")

elif edit_name == "nudge_ts_via":
    # In-place: TS via off VBAT row, south of C3 after CD is off E-row.
    text, n_via = set_via_at(text, 110.4, 105.65, 111.18, 107.18)
    text, n_sz = set_via_size_drill(text, 111.18, 107.18, 0.25, 0.15)
    text, n_f1 = set_seg_ends(
        text, 110.4, 105.65, 110.4, 106.0, 111.18, 107.18, 111.18, 106.14, layer="F.Cu"
    )
    text, n_f2 = set_seg_ends(
        text, 110.4, 106.0, 111.0, 106.0, 111.18, 106.14, 111.0, 106.0, layer="F.Cu"
    )
    text, n_b1 = set_seg_ends(
        text, 107.8, 105.65, 110.4, 105.65, 108.51, 107.18, 111.18, 107.18, layer="B.Cu"
    )
    text, n_b2 = set_seg_ends(
        text, 107.8, 107.0, 107.8, 105.65, 108.51, 107.0, 108.51, 107.18, layer="B.Cu"
    )
    print(
        f"nudge_ts_via via={n_via} size={n_sz} F={n_f1,n_f2} B={n_b1,n_b2}"
    )
    if n_via != 1 or n_f1 != 1 or n_f2 != 1 or n_b1 != 1:
        raise SystemExit("nudge_ts_via failed to match")

elif edit_name == "ts_via_off_vbat":
    # Latent short: TS via @(110.4,105.65) size 0.35 sits on VBAT B1–B2 F @y=105.6.
    # F.Cu (110.4,106)-(111,106) also runs through U2.C2 ILIM. B.Cu y=105.65
    # crosses ISET/ILIM/IPRETERM. Delete the cluster; C3 reconnects later.
    text, n_via = del_via(text, 110.4, 105.65, net=ts_net)
    text, n1 = del_segments_at(text, 110.4, 105.65, 110.4, 106.0, layer="F.Cu")
    text, n2 = del_segments_at(text, 110.4, 106.0, 111.0, 106.0, layer="F.Cu")
    text, n3 = del_segments_at(text, 107.8, 105.65, 110.4, 105.65, layer="B.Cu")
    text, n4 = del_segments_at(text, 107.8, 107.0, 107.8, 105.65, layer="B.Cu")
    text, n5 = del_segments_at(text, 108.51, 107.0, 107.8, 107.0, layer="B.Cu")
    deleted = n_via + n1 + n2 + n3 + n4 + n5
    print(f"ts_via_off_vbat via={n_via} segs={n1,n2,n3,n4,n5} total={deleted}")
    if n_via < 1 or deleted < 4:
        raise SystemExit("ts_via_off_vbat deleted too little")

elif edit_name == "sda_diag_del":
    # Incomplete SDA haul E4→west blocks the south of U2 and crosses CD/LSCTRL.
    # Keep the vertical E4 → R_SDA.
    text, n1 = del_segments_at(text, 109.44, 108.1, 111.4, 106.8, layer="F.Cu")
    print(f"sda_diag_del n1={n1}")
    if n1 < 1:
        raise SystemExit("sda_diag_del deleted nothing")

elif edit_name == "cd_erow_del":
    # Delete-only: stop CD from running through U2 E3/E4/E5.
    text, n1 = del_segments_at(text, 112.8, 106.8, 110.6, 106.8, layer="F.Cu")
    text, n2 = del_segments_at(text, 112.8, 108.26, 112.8, 106.8, layer="F.Cu")
    print(f"deleted cd e-row segs n1={n1} n2={n2}")
    if n1 + n2 < 1:
        raise SystemExit("cd_erow_del deleted nothing")

elif edit_name == "cd_off_erow":
    # CD F.Cu at y=106.8 runs through U2 E3/E4/E5 (LSCTRL/SDA/SCL).
    # Keep the pad stub on E2 and send CD south-east around the E-row.
    text, n1 = del_segments_at(text, 112.8, 106.8, 110.6, 106.8, layer="F.Cu")
    text, n2 = del_segments_at(text, 112.8, 108.26, 112.8, 106.8, layer="F.Cu")
    if n1 + n2 < 1:
        raise SystemExit(f"cd_off_erow deleted nothing n1={n1} n2={n2}")
    # E2 @(110.6,106.8) south then east to existing CD via @(113.30,108.41)
    text = add_segment(text, 110.6, 106.8, 110.15, 107.55, 0.12, "F.Cu", cd_net)
    text = add_segment(text, 110.15, 107.55, 110.15, 108.41, 0.12, "F.Cu", cd_net)
    text = add_segment(text, 110.15, 108.41, 113.3, 108.41, 0.12, "F.Cu", cd_net)

elif edit_name == "move_cldo_ne":
    # Slide C_LDO off the U2 east column so A5/D5 can fan out.
    # Old (113.5, 106.8, 90) → (114.3, 105.15, 90)
    text = set_fp_at(text, "C_LDO", "114.3 105.15 90")
    text, _ = del_segments_at(text, 113.5, 106.0, 113.5, 106.32, layer="F.Cu")
    text, _ = del_segments_at(text, 111.8, 106.0, 113.5, 106.0, layer="F.Cu")
    # pad2 3V3_DISP @(114.3, 105.63); pad1 GND @(114.3, 104.67)
    text = add_segment(text, 111.8, 106.0, 113.0, 106.0, 0.25, "F.Cu", disp_net)
    text = add_segment(text, 113.0, 106.0, 114.3, 105.63, 0.2, "F.Cu", disp_net)
    text = add_segment(text, 114.3, 104.67, 114.3, 104.02, 0.2, "F.Cu", ground_net)
    text = add_segment(text, 114.3, 104.02, 112.5, 104.02, 0.2, "F.Cu", ground_net)

elif edit_name == "vsys_via_east":
    # VSYS via @(112.50,105.60) blocks A5-D5 east. Shift east, keep B5 dogbone.
    text, n = del_via(text, 112.5, 105.6, net=vsys_net)
    if not n:
        raise SystemExit("VSYS via 112.5,105.6 not found")
    text, _ = del_segments_at(text, 112.05, 105.6, 112.5, 105.6, layer="F.Cu")
    text, _ = del_segments_at(text, 112.5, 105.6, 117.4, 105.6, layer="B.Cu")
    text = add_via(text, 113.35, 105.6, 0.45, 0.2, vsys_net)
    text = add_segment(text, 112.05, 105.6, 113.35, 105.6, 0.25, "F.Cu", vsys_net)
    text = add_segment(text, 113.35, 105.6, 117.4, 105.6, 0.25, "B.Cu", vsys_net)

elif edit_name == "gnd_a5_d5_east":
    # After east column is clearer: dogbone vias east of A5/D5, stitch on B.Cu.
    text = add_via(text, 112.22, 105.2, 0.35, 0.15, ground_net)
    text = add_via(text, 112.22, 106.4, 0.35, 0.15, ground_net)
    text = add_segment(text, 111.8, 105.2, 112.22, 105.2, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 111.8, 106.4, 112.22, 106.4, 0.12, "F.Cu", ground_net)
    text = add_segment(text, 112.22, 105.2, 112.22, 106.4, 0.15, "B.Cu", ground_net)

elif edit_name == "disp_via_east":
    # 3V3_DISP via @(113.00,106.00) sits between A5 and D5 east. Nudge east.
    text, n = del_via(text, 113.0, 106.0, net=disp_net)
    if not n:
        raise SystemExit("3V3_DISP via 113,106 not found")
    text, _ = del_segments_at(text, 111.8, 106.0, 113.0, 106.0, layer="F.Cu")
    text, _ = del_segments_at(text, 113.0, 106.0, 113.0, 107.4, layer="B.Cu")
    text, _ = del_segments_at(text, 116.85, 106.0, 113.0, 106.0, layer="B.Cu")
    text = add_via(text, 113.7, 106.0, 0.45, 0.2, disp_net)
    text = add_segment(text, 111.8, 106.0, 113.7, 106.0, 0.25, "F.Cu", disp_net)
    text = add_segment(text, 113.7, 106.0, 113.7, 107.4, 0.25, "B.Cu", disp_net)
    text = add_segment(text, 113.7, 107.4, 115.55, 107.4, 0.25, "B.Cu", disp_net)
    text = add_segment(text, 116.85, 106.0, 113.7, 106.0, 0.25, "B.Cu", disp_net)

elif edit_name == "ts_south_via":
    # After CD E-row is gone: via south of C3/D3 street, B.Cu west to R_TS via.
    # Avoid E3/E4/SDA vertical and SCL diagonal.
    text = add_via(text, 111.18, 107.18, 0.25, 0.15, ts_net)
    text = add_segment(text, 111.0, 106.0, 111.18, 106.14, 0.08, "F.Cu", ts_net)
    text = add_segment(text, 111.18, 106.14, 111.18, 107.18, 0.08, "F.Cu", ts_net)
    text = add_segment(text, 111.18, 107.18, 108.51, 107.18, 0.12, "B.Cu", ts_net)
    text = add_segment(text, 108.51, 107.18, 108.51, 107.0, 0.12, "B.Cu", ts_net)

elif edit_name == "cd_jog_south":
    # After E-row delete: E2 south then east at y=108.48 (between 3V3 y=108.25 and GND y=108.6).
    text = add_segment(text, 110.6, 106.8, 110.45, 107.2, 0.1, "F.Cu", cd_net)
    text = add_segment(text, 110.45, 107.2, 110.45, 108.48, 0.1, "F.Cu", cd_net)
    text = add_segment(text, 110.45, 108.48, 113.3, 108.48, 0.1, "F.Cu", cd_net)
    text = add_segment(text, 113.3, 108.48, 113.3, 108.41, 0.1, "F.Cu", cd_net)

elif edit_name == "ilim_via_out":
    # Inner ILIM via @(111.45,105.80) size 0.5 overlaps PMID B4/C4. Move east of C5.
    text, n = del_via(text, 111.45, 105.8, net=ilim_net)
    if not n:
        raise SystemExit("ILIM via 111.45,105.8 not found")
    text, n1 = del_segments_at(text, 110.6, 106.0, 111.45, 105.8, layer="F.Cu")
    text, n2 = del_segments_at(text, 111.45, 105.8, 110.3, 105.8, layer="B.Cu")
    print(f"ilim_via_out del via segs F={n1} B={n2}")
    # Dogbone C2 west-south of BGA to via west of ISET, then B to existing ILIM B @x=110.3.
    text = add_via(text, 109.15, 105.85, 0.3, 0.15, ilim_net)
    text = add_segment(text, 110.6, 106.0, 110.6, 105.85, 0.08, "F.Cu", ilim_net)
    text = add_segment(text, 110.6, 105.85, 109.15, 105.85, 0.08, "F.Cu", ilim_net)
    text = add_segment(text, 109.15, 105.85, 109.15, 105.35, 0.12, "B.Cu", ilim_net)
    text = add_segment(text, 109.15, 105.35, 110.3, 105.35, 0.12, "B.Cu", ilim_net)

elif edit_name == "sol_rscl_3v3":
    # gpt-6-sol repo-explore follow-up KEEP: reconnect R_SCL pad2 (3V3)
    # at (108.80,109.29) to the existing 3V3 island at y=108.25.
    # Orthogonal F.Cu only. Combined CD/E1 KEEP was rejected (E1 is NC).
    text = add_segment(text, 108.8, 109.29, 110.5, 109.29, 0.12, "F.Cu", rail_3v3_net)
    text = add_segment(text, 110.5, 109.29, 110.5, 108.25, 0.12, "F.Cu", rail_3v3_net)
    text = add_segment(text, 110.5, 108.25, 110.16, 108.25, 0.12, "F.Cu", rail_3v3_net)
    print("sol_rscl_3v3 added 3 F.Cu 3V3 segments")

elif edit_name == "sol_3v3_lsctrl_tie":
    # gpt-6-sol stepwise KEEP: leftover 3V3 stub that still feeds R_LSCTRL pad2
    # (112.51,107.80)-(114.60,107.80) is an island vs via (112.16,107.60).
    # One orthogonal F.Cu tie onto the existing 3V3 vertical x=112.16.
    text = add_segment(text, 112.51, 107.8, 112.16, 107.8, 0.2, "F.Cu", rail_3v3_net)
    print("sol_3v3_lsctrl_tie added F.Cu 3V3 (112.51,107.8)-(112.16,107.8)")

elif edit_name == "sol_cd_e2_via":
    # Sol variant 2 (CD F→B→existing CD via). Independent probe, not VIP.
    # Rejected: via-in-pad on E2 (110.6,106.8) and B vertical x=112.4
    # (OVERLAP −0.120 vs 3V3 via 0.6@(112.16,107.60)).
    # KEEP: dogbone south of E2, then B.Cu L at y=106.95 / x=112.65.
    text = add_via(text, 110.6, 106.95, 0.25, 0.15, cd_net)
    text = add_segment(text, 110.6, 106.8, 110.6, 106.95, 0.15, "F.Cu", cd_net)
    text = add_segment(text, 110.6, 106.95, 112.65, 106.95, 0.12, "B.Cu", cd_net)
    text = add_segment(text, 112.65, 106.95, 112.65, 108.41, 0.12, "B.Cu", cd_net)
    text = add_segment(text, 112.65, 108.41, 113.3, 108.41, 0.12, "B.Cu", cd_net)
    print("sol_cd_e2_via via (110.6,106.95) 0.25 + F stub + B L x=112.65")

elif edit_name == "sol_ilim_c2_dogbone":
    # Orthogonal F.Cu C2 → KEEP ILIM via (110.75,105.80). Do not drop
    # ILIM onto x=110.6 / y=105.80 (VBAT RISK +0.020). w=0.08 keeps
    # VBAT +0.070 and PMID +0.080 on the via vertical.
    text = add_segment(text, 110.6, 106.0, 110.75, 106.0, 0.08, "F.Cu", ilim_net)
    text = add_segment(text, 110.75, 106.0, 110.75, 105.8, 0.08, "F.Cu", ilim_net)
    print("sol_ilim_c2_dogbone F L (110.6,106.0)->(110.75,106.0)->(110.75,105.8)")

elif edit_name == "sol_rscl_west":
    # Spread the untouched SCL/TS 0402 heap. Sol STEP4 wanted R_SDA at
    # (111.35,110.30,0) — F.Cu vs SW2.1 is +0.220 but courtyards overlap
    # SW1 (−1.18) and SW2 (−1.42); that piles onto the buttons, not a spread.
    # KEEP: R_SCL (108.8,109.8,90) → (106.5,110.1,90). pad1 SCL +Y
    # (106.5,110.61), pad2 3V3 (106.5,109.59). Retarget the existing 3V3 L
    # onto pad2 in the same save. y=110.1 keeps pad2 sepY +0.21 vs C_BAT.1
    # VBAT; x=106.5 keeps VBUS F x=105.7 w=0.35 at +0.305. probe_via RISK
    # vs BTN3 B y=109.15 is F-only 0402 (ignore).
    text = set_fp_at(text, "R_SCL", "106.5 110.1 90")
    text, n_h = set_seg_ends(
        text, 108.8, 109.29, 110.5, 109.29, 106.5, 109.59, 110.5, 109.59, layer="F.Cu"
    )
    text, n_v = set_seg_ends(
        text, 110.5, 109.29, 110.5, 108.25, 110.5, 109.59, 110.5, 108.25, layer="F.Cu"
    )
    print(f"sol_rscl_west fp R_SCL (106.5,110.1,90) 3V3 H={n_h} V={n_v}")
    if n_h != 1 or n_v != 1:
        raise SystemExit("sol_rscl_west failed to match 3V3 follow")

else:
    raise SystemExit(f"unknown edit {edit_name}")

save(text)
print(f"applied {edit_name}")
