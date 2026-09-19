#!/usr/bin/env python3
"""Pass-V1 ATTEMPTED / REVERTED — C_VINLS relocation to clear 3V3_DISP.

Literal Δy=−0.5 (north) worsens pad1↔3V3_DISP overlap (pad1 is south pad).
Δy=+0.5 (south) clears 3V3_DISP but hits R_CD / C_SYS / SW / A5 depending on X.
All variants with fanouts raised shorting or power-priority → REVERTED to Pass-T.
See FIX_PASS_SESSION Pass-V. Do not run.
"""
raise SystemExit("REVERTED — do not run; see FIX_PASS_SESSION Pass-V")
