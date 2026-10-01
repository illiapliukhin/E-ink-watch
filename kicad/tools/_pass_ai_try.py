#!/usr/bin/env python3
"""Pass-AI single KEEP attempt. One edit, then the DRC gate.

add_segment (even before the PMID anchor) promoted latent shorts on this
board. The seam edit therefore retargets duplicate 3V3_DISP segments in
place and only moves the existing via.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import fpat, load, save, set_via_at


def rewrite_segment(text, x1, y1, x2, y2, layer, nx1, ny1, nx2, ny2, nlayer, nwidth):
    """Retarget one segment, either endpoint order. Keeps uuid and file order."""
    changed = [0]

    def apply(start_x, start_y, end_x, end_y, body):
        pattern = (
            rf"\t\(segment\n"
            rf"\t\t\(start {fpat(start_x)} {fpat(start_y)}\)\n"
            rf"\t\t\(end {fpat(end_x)} {fpat(end_y)}\)\n"
            rf"\t\t\(width ([^\)]+)\)\n"
            rf"\t\t\(layer \"{layer}\"\)\n"
            rf"\t\t\(net (\d+)\)\n"
            rf"\t\t\(uuid \"([^\"]+)\"\)\n"
            rf"\t\)\n"
        )

        def replacer(match):
            changed[0] += 1
            return (
                f"\t(segment\n"
                f"\t\t(start {nx1} {ny1})\n"
                f"\t\t(end {nx2} {ny2})\n"
                f"\t\t(width {nwidth})\n"
                f"\t\t(layer \"{nlayer}\")\n"
                f"\t\t(net {match.group(2)})\n"
                f"\t\t(uuid \"{match.group(3)}\")\n"
                f"\t)\n"
            )

        return __import__("re").sub(pattern, replacer, body, count=1)

    text = apply(x1, y1, x2, y2, text)
    if changed[0] == 0:
        text = apply(x2, y2, x1, y1, text)
    return text, changed[0]


edit_name = sys.argv[1]
text = load()

if edit_name == "disp_west_seam_inplace":
    # Via (85, 102.75) 0.6/0.3 -> (84.4, 96). Probe edge +0.181 vs EPD_SCK.
    text, via_count = set_via_at(text, 85, 102.75, 84.4, 96)
    print(f"via={via_count}")
    if via_count != 1:
        raise SystemExit("via move failed")
    # Each source is a duplicate. The untouched twin keeps the old copper.
    # F corridor only clears at w<=0.30 (worst +0.335 at 0.25). B clears at 0.45.
    rewrites = [
        (102.25, 82.4, 102.25, 83.15, "F.Cu", 84.45, 98.25, 83.55, 97.4, "F.Cu", 0.25),
        (97.75, 82.4, 97.75, 83.15, "F.Cu", 83.55, 97.4, 83.55, 95.9, "F.Cu", 0.25),
        (94, 87, 94, 82.4, "F.Cu", 83.55, 95.9, 84.4, 96, "F.Cu", 0.25),
        (92, 87, 94, 87, "B.Cu", 84.4, 96, 84.4, 94.2, "B.Cu", 0.45),
        (97, 87.5, 93.5, 87.5, "B.Cu", 84.4, 94.2, 87, 88.4, "B.Cu", 0.45),
        (84.45, 98.25, 83.15, 98.25, "F.Cu", 87, 88.4, 92, 87, "B.Cu", 0.45),
    ]
    for src in rewrites:
        text, count = rewrite_segment(text, *src)
        print(f"rewrite {src[0], src[1]} -> {src[5], src[6]} count={count}")
        if count != 1:
            raise SystemExit(f"rewrite failed {src}")
else:
    raise SystemExit(f"unknown edit {edit_name}")

save(text)
print(f"applied {edit_name}")
