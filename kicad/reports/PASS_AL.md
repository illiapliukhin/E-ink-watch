# PASS_AL — placement spreads, then one west GND via (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AH / Pass-AJ (`shorting=0`, `unc=8`)  
**To:** Pass-AL (`shorting=0`, `unc=7`)  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc`. Local edit of the existing In2 `filled_polygon`. No zone refill.

## Verdict

**KEEP one copper edit.** Unconnected 8→7. Shorting stays 0. Power-priority pairs and the PMID pocket stay empty.

No footprint moved. Larger spreads of the south 0402s, and a U2 translate or rotate, do not open a 0.15 mm corridor. The west GND island was already reachable on B.Cu once a through via could sit on the F.Cu end without drilling the In2 3V3 fill. That notch is the KEEP.

Do not apply VBUS on the dock. Power islands are still open.

## Placement (before = after)

| Ref | x, y, rot |
|-----|-----------|
| R_SCL | 106.5, 110.1, 90 |
| R_SDA | 111.5, 109.0, 0 |
| R_CD | 113.5, 107.75, 90 |
| C_LDO | 113.5, 106.8, 90 |
| R_LSCTRL | 114.6, 108.25, 90 |
| C_PMID | 112.2, 103.4, 0 |
| R_ILIM | 115.6, 106.6, 0 |
| U2 | 111, 106, 0 |

Nothing was written with `set_fp_at`. Removing passive pads does not open SCL, SDA, PMIC_INT, TS, or GND A5. The blockers are tracks and vias.

- **SCL.** The F.Cu wall is the R_SDA vertical `(111.400, 109.000)–(111.400, 106.800)` w=0.15. Dropping that tie (not the pads alone) lets a flood reach R_SCL pad1. It still does not reach U1 pad 29. No R_SDA site keeps pad edge ≥ 0.15 mm and a legal retie onto the SDA diagonal and a 3V3 rail. Straight F.Cu jogs off x=111.4 hit the 3V3 rail at y=108.25. A B.Cu replacement of the same vertical hits the CD via and BTN3. R_SCL itself has no clear site that touches the E5 stub.
- **U2 translate.** Shifts of ±0.2 to ±0.4 mm, with dogbone endpoints stretched, all have a worst edge ≤ −0.200 mm (SDA into 3V3). Not applied.
- **U2 rotate.** 90/180/270 in place, dogbones left where they are, overlaps 23 pads. Not applied. A rotate only after deleting those stubs was not required: the GND via below did not need it.

## KEEP — In2 notch plus west GND via

The west GND F.Cu track ends at `(108.71, 108.15)`. A 0.25/0.15 through via on that point joins the existing B.Cu GND pour, so unconnected drops without a zone refill. The same point is inside the In2 3V3 fill (about 11.93 mm from `(100, 100)`; the fill radius is 12 mm). Pass-AK put a via at `(108.71, 108.2)`, saw `shorting=0` and `unc=7`, then reverted it: hole clearance to Zone 3V3 on In2 was actual 0.000 mm. A through via drills In2 even when `shorting_items` stays 0.

This pass cut only that spot in the existing filled polygon. Outline vertices that fell inside a 0.45 mm circle were replaced by a clockwise arc of radius 0.45 mm. Fill area 422.581 → 422.211 mm². `(100, 100)` stays inside. All 20 holes stay empty. The via center is 0.449 mm outside the fill, so drill-to-copper is 0.375 mm (rule 0.250 mm). Hole bridges were not rebuilt. A splice that inserts the circle into the ring and drives the polygon area to 0 does **not** clear the plane; that board was discarded.

Via, inserted before the PMID anchor `(111.35, 103.85)`:

- GND `(108.71, 108.15)` size 0.25 drill 0.15, F.Cu–B.Cu, on the existing track end.

DRC (`reports/_drc_passal_gnd_via4.txt`, not committed):

- `shorting_items=0`
- `unconnected_items=8→7` (west GND pair gone)
- power pairs empty; PMID↔VBUS, 3V3_DISP↔PMID, PMID↔SW empty
- the new via is annular width 0.050 mm, drill 0.150 mm vs Power min 0.300 mm, diameter 0.250 mm vs Power min 0.600 mm. Same class as the existing D5 via `(112.4, 106.55)`. It is not hole-clearance 0.000 mm against Zone 3V3.
- one new hole clearance, actual 0.2278 mm: LSCTRL F.Cu `(111.0, 106.8)` length 1.0198 mm vs the CD via `(110.6, 106.95)`. Not a short. Pad E3 vs that via is already 0.2372 mm.

## Still open

1. GND F `(111.8, 106.4)` vs U2 A5 `(111.8, 105.2)`
2. `3V3_DISP` B `(92, 87)` vs west F `(84.45, 98.25)`
3. SDA F `(111.4, 109.0)` vs U1 pad 27 `(98.8, 87.25)`
4. SCL R_SCL pad1 `(106.5, 110.61)` vs E5 stub `(111.8, 106.8)`
5. SCL E5 stub vs U1 pad 29 `(98.0, 87.25)`
6. PMIC_INT B `(94.2, 90.55)` vs F stub `(110.6, 106.4)`
7. TS F `(111.0, 106.0)` vs TS B `(107.8, 105.65)`

4-layer stack, charge path, SW_DBG SWD-only, and pogo nets were not changed. No VBUS on the dock.
