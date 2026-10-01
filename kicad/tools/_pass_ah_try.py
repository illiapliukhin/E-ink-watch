#!/usr/bin/env python3
"""Pass-AH KEEP edits. Rejected routes are recorded in reports/PASS_AH.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _pass_ag_sexpr_lib import load, save, set_via_at

edit_name = sys.argv[1]
text = load()

if edit_name == "disp_via_onto_west":
    # Orphan 3V3_DISP via (96, 105.2) 0.6 has no tracks. Slide it onto the
    # west F.Cu stub end (85, 102.75). In-place only — no new items.
    text, via_count = set_via_at(text, 96, 105.2, 85, 102.75)
    print(f"disp_via_onto_west via={via_count}")
    if via_count != 1:
        raise SystemExit("disp_via_onto_west failed to match")
else:
    raise SystemExit(f"unknown edit {edit_name}")

save(text)
print(f"applied {edit_name}")
