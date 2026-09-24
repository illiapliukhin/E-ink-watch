#!/usr/bin/env python3
"""Apply one named Pass-AF stitch attempt onto the current board."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_af_sexpr_lib import add_segment, add_via, load, netnum, save

edit_name = sys.argv[1]
text = load()
ground_net = netnum(text, "GND")
disp_net = netnum(text, "3V3_DISP")
rail_3v3_net = netnum(text, "3V3")
sda_net = netnum(text, "SDA")
scl_net = netnum(text, "SCL")
pmic_int_net = netnum(text, "PMIC_INT")

if edit_name == "sw3_gnd_bwrap":
    # Merge SW3 pad island (via 117.2,108) with south GND via (113.7,110)
    # on B.Cu south of BTN3/LSCTRL at y=109.15/109.5.
    text = add_segment(text, 117.2, 108.0, 117.2, 111.0, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 117.2, 111.0, 113.7, 111.0, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 113.7, 111.0, 113.7, 110.0, 0.2, "B.Cu", ground_net)
elif edit_name == "sw2_gnd_f":
    # SW2 pad 2 @(116.2,111) to existing GND via @(113.7,110); diagonal was clearance-clear.
    text = add_segment(text, 116.2, 111.0, 113.7, 110.0, 0.25, "F.Cu", ground_net)
elif edit_name == "strap_r_gnd_f":
    # J_STRAP_R pad 2 @(116.85,98.75) to GND via @(114.65,97.8).
    text = add_segment(text, 116.85, 98.75, 114.65, 97.8, 0.2, "F.Cu", ground_net)
elif edit_name == "strap_r_gnd_bwrap":
    # Leave pad 2 east-south so the track does not clip pad 1 (3V3_DISP @ y=98.25).
    text = add_segment(text, 116.85, 98.75, 117.6, 99.4, 0.15, "F.Cu", ground_net)
    text = add_via(text, 117.6, 99.4, 0.5, 0.25, ground_net)
    text = add_segment(text, 117.6, 99.4, 117.6, 99.9, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 117.6, 99.9, 114.65, 99.9, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 114.65, 99.9, 114.65, 97.8, 0.2, "B.Cu", ground_net)
elif edit_name == "strap_r_gnd_east":
    # Exit pad 2 along +X (cable side) between pad 1 and pad 3, then B.Cu to via 114.65,97.8.
    text = add_segment(text, 116.85, 98.75, 118.4, 98.75, 0.15, "F.Cu", ground_net)
    text = add_via(text, 118.4, 98.75, 0.4, 0.2, ground_net)
    text = add_segment(text, 118.4, 98.75, 118.4, 99.9, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 118.4, 99.9, 114.65, 99.9, 0.2, "B.Cu", ground_net)
    text = add_segment(text, 114.65, 99.9, 114.65, 97.8, 0.2, "B.Cu", ground_net)
elif edit_name == "disp_west_f103":
    # West 3V3_DISP island already has F.Cu at x=85 y=102.75..105.5.
    # Horizontal F at y=103.2 was clearance-clear to x=91.2.
    text = add_segment(text, 85.0, 103.2, 91.2, 103.2, 0.15, "F.Cu", disp_net)
elif edit_name == "disp_west_to_via96":
    text = add_segment(text, 85.0, 103.2, 96.0, 103.2, 0.15, "F.Cu", disp_net)
    text = add_segment(text, 96.0, 103.2, 96.0, 105.2, 0.15, "F.Cu", disp_net)
elif edit_name == "disp_west_outer":
    # Outer B.Cu along the west rim, south of the west island, then north to via 92,87.
    # F.Cu across the SWD/3V3 forest is blocked; this path trades edge-clearance DRC
    # (already nonzero) for a shorting-safe island merge.
    text = add_via(text, 82.8, 105.5, 0.45, 0.2, disp_net)
    text = add_segment(text, 84.45, 105.5, 82.8, 105.5, 0.25, "F.Cu", disp_net)
    text = add_segment(text, 82.8, 105.5, 82.8, 108.2, 0.2, "B.Cu", disp_net)
    text = add_segment(text, 82.8, 108.2, 81.8, 108.2, 0.2, "B.Cu", disp_net)
    text = add_segment(text, 81.8, 108.2, 81.8, 87.0, 0.2, "B.Cu", disp_net)
    text = add_segment(text, 81.8, 87.0, 92.0, 87.0, 0.2, "B.Cu", disp_net)
else:
    raise SystemExit(f"unknown edit {edit_name}")

save(text)
print(f"applied {edit_name}")
