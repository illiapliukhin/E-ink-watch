# PASS_AH — slide orphan 3V3_DISP via onto the west stub (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AG HEAD (`shorting=0`, `unc=9`)  
**To:** Pass-AH (`shorting=0`, `unc=8`)  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc` (lite AppImage). In-place sexpr only.

## Verdict

**Partial.** Hard gates held. One in-place KEEP closed the orphan `3V3_DISP` via against the west F.Cu island. SCL, TS, A5, west GND, SDA, PMIC_INT, and the remaining `3V3_DISP` east B island stay open. Not production-ready. Do not apply VBUS on the dock: power stubs are still unconnected even though `shorting_items=0`.

## Baseline (Pass-AG)

`shorting_items=0`, `unconnected_items=9`, power-priority pairs 0, pocket PMID↔VBUS / 3V3_DISP↔PMID / PMID↔SW = 0.

Open pairs:

- GND A5 vs D5 dogbone `(111.8, 106.4)`
- GND west `(108.71, 108.6)` vs that same D5 island
- `3V3_DISP` west F `(85, 98.25)` vs east B `(92, 87)`
- `3V3_DISP` west F `(85, 102.75)` vs orphan via `(96, 105.2)`
- SDA vs U1.27
- SCL `R_SCL` pad1 `(106.5, 110.61)` vs E5 stub
- SCL E5 vs U1.29
- PMIC_INT B `(94.2, 106.4)` vs F stub `(110.6, 106.4)`
- TS C3 F vs TS B `(107.8, 105.65)`

## KEEP

| Step | Result |
|------|--------|
| `disp_via_onto_west` in-place | Via `(96, 105.2)` 0.6/0.3 → `(85, 102.75)`, same size, no tracks to retarget. Probe overlap=0 (tightest `+0.301` vs 3V3 via `(84.25, 102.25)`). `shorting=0`, `unc=9→8`, power and pocket gates held. |

Replay from the Pass-AG board: `python3 tools/_pass_ah_try.py disp_via_onto_west` then `tools/_pass_ah_run.sh disp_via_onto_west`.

## REVERT (shorting > 0)

| Attempt | Why |
|---------|-----|
| `gnd_b_west_stitch` B.Cu `y=109.35` + via `(112.8, 109.35)` | `shorting=6`: GND↔3V3, GND↔3V3_DISP, GND↔LSCTRL, GND↔CD, GND↔BTN3. LSCTRL vertical and BTN3 `y=109.15` still own that street. |
| `pmic_int_via_b` B haul `y=106.4` to `(94.2, 106.4)` | `unc=8` but PMIC_INT↔VBAT via `(96.2, 106.25)` and PMIC_INT↔IPRETERM via `(110.05, 106.4)`. |
| `pmic_int_b_jog` B `y=107.85` | GND vias `(94.16, 107.25)` and `(94.5, 107.5)` short the west drop. |
| `disp_b_via_stack` / `disp_b_vertical_only` | New via `(96, 102.75)` promoted the latent C3 clearance (GND track `(97.48, 108.8)` vs C3 pad1 3V3) into `shorting_items`. Baseline classifies that pair as clearance (`actual 0.109`) plus solder-mask bridge, not a short. Adding copper reopened it. Reverted. |
| `ts_c3_b_via` | ILIM↔TS on the C2/C3 F stub and on ILIM B `x=110.3`. |
| `gnd_a5_l_dogbone` | GND↔3V3_DISP. The F gap between VSYS `y=105.6` and 3V3_DISP `y=106.0` is ~0.125 mm. East around C_VINLS / C_LDO overlaps PMID and 3V3_DISP. |

## Remaining unc=8

Same list as baseline except the orphan `3V3_DISP` via, which now sits on the west F island. That island is still open versus east B `(92, 87)`.

## Next

Do not add copper that reorders items ahead of the C3 3V3/GND pair until that clearance is opened in the same save (in-place endpoint move, not a delete). A5 still needs a corridor that is not the VSYS/3V3_DISP slot and not the C_VINLS PMID pad. SCL and TS stay blocked by BTN3 B `y=109.15`, the BTN1 via, and the ILIM/CD/VBAT streets. West GND vs east `R_CD` still crosses the 3V3 B stitch at `y=108.55` and LSCTRL B `x=110.8`. No In1/In2 signal hauls. No zone refill. No VBUS on the dock while power islands remain open.

## Archives

- `tools/_pass_ah_try.py`, `_pass_ah_gate.py`, `_pass_ah_run.sh`
- `LIVE_LOG.txt`
