#!/usr/bin/env python3
"""Pass-U1 ATTEMPTED / ALL VARIANTS REVERTED — isolate 3V3_DISP from C_VINLS/VSYS.

Attempts U1a–U1g (VSYS spine pull, B hops, via-on-C5, delete-only, UnFill) all
raised shorting_items above 0 (collateral CD↔PMIC_INT / OPT↔BTN2 / GND↔VSYS /
3V3_DISP↔VSYS). Hard gate: shorting must stay 0 → do not run.
See FIX_PASS_SESSION Pass-U.
"""
raise SystemExit("REVERTED — do not run; see FIX_PASS_SESSION Pass-U")
