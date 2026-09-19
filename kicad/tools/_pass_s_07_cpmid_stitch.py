#!/usr/bin/env python3
"""Pass-S7 ATTEMPTED / REVERTED: C_PMID via-island → U2 A3 west-of-SW F stitch.

REVERTED: shorting 0→6 (3V3_DISP↔VSYS/PMID, 3V3↔TS, SCL↔TS) despite PMID↔VBUS/SW=0.
Corridor analysis: F west blocked (VBUS@110.6 vs SW via@111.40,104.90 squeeze);
F/B east blocked (VSYS bar@y=104.48, SW B@y=104.90, ILIM B@y=105.35).
Prior S5 full B.Cu east stitch → shorting 12. Leave C_PMID island; do not keep this edit.
"""
raise SystemExit("REVERTED — do not run; see FIX_PASS_SESSION Pass-S")
