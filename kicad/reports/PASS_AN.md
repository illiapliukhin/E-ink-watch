# PASS_AN — larger R_SDA placement, SCL still blocked (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` (Pass-AL KEEP, unchanged)  
**From / to:** `shorting=0`, `unc=7`. No footprint moved. No copper added.  
**Tool:** KiCad 9.0.9 baseline DRC. Placement checked at 0.15 mm pad and track clearance.

## Verdict

**No KEEP.** Unconnected stays 7. Shorting stays 0. Larger moves of `R_SDA`, including a swap that frees `NTC_BAT`, still cannot retie 3V3 at 0.15 mm once the part leaves x=111.4. The SCL hop was not applied. Do not apply VBUS on the dock.

## Baseline

KiCad 9.0.9 DRC (`reports/_drc_passan_baseline.txt`): marker `shorting_items=0`, `unconnected_items=7`. Header count 890 violations.

Still open: GND A5, east–west `3V3_DISP`, SDA vs U1.27, SCL `R_SCL` vs the E5 stub, SCL E5 vs U1.29, PMIC_INT, TS.

## Placement (before = after)

| Ref | x, y, rot |
|-----|-----------|
| R_SDA | 111.5, 109.0, 0 |
| R_SCL | 106.5, 110.1, 90 |
| NTC_BAT | 108.2, 108.15, 0 |
| U2 | 111, 106, 0 |

## Sites tried

1. **Grid, four rotations.** Centers x=104–118, y=102–116, step 0.4 mm, r≤18.6, SCL lane x=111.15–111.80 / y=107.15–110.70 reserved. 483 sites have both pads ≥ 0.15 mm. Zero of them have an F or B retie from the SDA pad to the diagonal `(109.44, 108.10)–(111.40, 106.80)` plus a 3V3 retie. The diagonal's west half (t≤0.55) is locally clear (`+0.22` to `+0.38`), and the free F pocket around it is only about x=108.63–110.58, y=106.98–108.18. That pocket does not reach a 3V3 rail.

2. **East detour of the existing SDA pad**, with the redundant 3V3 via `(112.16, 107.60)` ignored (it has no B.Cu track). A south run at x=112.4–114.5 from y=109.95 to y=107.05 overlaps the 3V3 rail, `R_CD`, the CD via `(113.30, 108.41)`, or `R_LSCTRL`. A west leg at y=106.95–108.00 from x=113.2 to x=111.45 overlaps the SCL stub.

3. **B.Cu portal on the diagonal.** Via 0.25 at `(110.22, 107.58)` is outside In2 (r=12.72, probe `+0.320` vs the LSCTRL via) and **inside the B.Cu GND fill**. A through via there shorts SDA to GND. Two pad sites that can reach it on B are also inside that fill and inside In2:
   - `(107.0, 105.1)` rot 90. SDA via `(107.00, 105.61)`, In2 depth 1.864 mm. 3V3 straight tie `+0.095` vs VBUS F.
   - `(105.0, 108.5)` rot 270. SDA via `(105.00, 107.99)`, In2 depth 2.562 mm. 3V3 straight tie `−0.175` vs GND F.
   BTN3 B at y=109.15 still blocks any south-of-button B run.

4. **Pocket park on the diagonal, NTC_BAT moved away.** `R_SDA (109.60, 107.60)` rot 180 puts SDA pad1 on the diagonal at `(110.11, 107.60)` (pad edge `+0.159` vs the 3V3 spur) and 3V3 pad2 at `(109.09, 107.60)` (edge `+0.195` vs `R_TS`, once `NTC_BAT` is ignored). With `NTC_BAT` left in place that 3V3 pad is `+0.029` vs `NTC_BAT.2`. `NTC_BAT` itself has a legal new site `(108.00, 108.25)` rot 270 (pads and ties ≥ `+0.259` to the TS via and the GND via). The 3V3 pad still cannot reach the rail: the copper gap between the diagonal's west end and GND F y=108.60 is 0.285 mm, too narrow for a 0.12 mm track at 0.15 mm clearance. An east jog at y=108.25 is `−0.015` vs the diagonal. A north-then-east jog is `+0.021` vs the CD via `(110.60, 106.95)` and then `−0.150` vs the diagonal. Not applied.

5. **+0.090 diagonal neighborhoods** from Pass-AM, including `(109.70, 107.50)` rot 180 (min `+0.100` vs `NTC_BAT.2`), stay below 0.15 mm. Not applied.

## SCL hop vs the B GND pour

Probe clearance of the Pass-AM hop ignores zone fills. The B.Cu segment at x=111.35 from y=107.30 to y=108.80 stays outside the B GND fill, but the centerline is only 0.075 mm from it. For w=0.12 that is a 0.015 mm copper gap. x=111.50 gives a 0.165 mm copper gap; x=111.65 gives 0.286 mm. The E5 stub only reaches x≈111.35 at the y that also clears the CD B run (y≥107.34). The hop was not applied.

## Fallback nets

A 0.25 via on U2.C3 `(111.00, 106.00)` is outside In2 (r=12.53) and 0.207 mm from the B GND fill. Probe edge is `+0.000` vs ILIM B y=105.80. The 1.2 mm window around C3 has no via that is outside In2, ≥0.20 mm from that fill, and ≥0.10 mm from foreign copper. PMIC_INT's F stub row y=106.4 sits in the B GND fill. The Pass-AI `3V3_DISP` seam was not replayed.

## Next

unc=7, shorting=0. Same seven pairs. A retie that removes x=111.4 still has to clear the 3V3 rail, the diagonal, and the B GND pour together. No VBUS on the dock.
