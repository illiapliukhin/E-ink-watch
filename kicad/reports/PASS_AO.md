# PASS_AO — other open islands, no KEEP (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` (unchanged)  
**From / to:** `shorting=0`, `unc=7`. No footprint moved. No copper added.  
`R_SDA` and the Pass-AM SCL hop were not retried.

## Verdict

**No KEEP.** Unconnected stays 7. Shorting stays 0. PMIC_INT, TS, east–west `3V3_DISP`, and A5 each fail a 0.15 mm stitch. The blockers are U2 balls, chip dogbones, the B GND fill, and the EPD_SCK back-side wall. Moving the nearby 0402s does not move those. Do not apply VBUS on the dock.

## Baseline

Still open: GND A5, east–west `3V3_DISP`, SDA vs U1.27, both SCL islands, PMIC_INT, TS. Pass-AN baseline DRC markers were `shorting_items=0`, `unconnected_items=7`. This pass did not write a trial, so that board is still the file.

## 1. PMIC_INT

Islands: B.Cu `(94.200, 90.550)–(94.200, 106.400)` w=0.18, via `(94.2, 89.75)`, and U1.39 `(95.35, 89.75)`. The other end is the F stub `(110.600, 106.400)–(110.550, 106.400)` on U2.D2.

Every 0.40 mm ray off D2 `(110.60, 106.40)` is under 0.15 mm. Best is `+0.025` (pad E2 / pad C2). The west rays hit the IPRETERM via `(110.05, 106.40)` size 0.50 by `−0.025` to `−0.175`. `R_IPRETERM` sits at `(114.80, 102.90)`. Moving it leaves that via on D1.

A 0.25 via on D2 is outside In2 (r=12.38) with pad edge `+0.160` vs D1, and 0.025 mm from the B GND fill, so the ring overlaps the pour. A 1 mm grid from x=94 to x=111, y=90 to y=107 has one B cell that clears both the pour and foreign copper (`(96, 105)`). There is no B corridor to the west vertical. Not applied.

## 2. TS

Islands: F stub `(111.000, 106.000)–(111.000, 106.120)` on U2.C3, and B `(107.800, 105.650)–(110.400, 105.650)` plus `R_TS` / `NTC_BAT`.

F rays off C3 top out at `+0.000` (pads D2 and D4). Moving `R_TS` `(108.00, 107.00)` or `NTC_BAT` `(108.20, 108.15)` does not move those balls.

The B end `(110.40, 105.65)` is 0.10 mm from ILIM B x=110.30 (edge `−0.035` for a w=0.12 extension). Going around the east end of ILIM at x=111.80 enters the B GND fill. A via search around C3, even with the ILIM segment y=105.8 and via `(110.75, 105.80)` ignored, best edge is `+0.078` at `(111.00, 106.05)` vs PMID F, and the B fill is 0.196 mm from that point (ring gap 0.071 mm). `R_ILIM` is at `(115.60, 106.60)`; its body is not this dogbone. Not applied.

## 3. East–west 3V3_DISP

West island: x=83.15–85.00, y=98.25–105.50, pads `J_STRAP_L` 1 and 10, via `(85.00, 102.75)`.  
East island: x=92–119, including U2.C5 and `C_LDO`. Westernmost copper is B `(92.00, 87.00)–(94.00, 87.00)` w=0.45.

Closest copper gap is 12.85 mm, from F `(85.00, 98.25)` to that B run. EPD_SCK B `(85.0, 94.5)–(115.0, 94.5)` w=0.18 blocks every southern crossing inside the outline. The only way past it is west of x=85, which is the Pass-AI seam (DRC shorting 4, then 2). Not replayed. No 0402 in that gap owns the EPD_SCK track.

## 4. A5

U2.A5 `(111.80, 105.20)` vs the D5 dogbone at `(111.80, 106.40)`. Best F ray is `+0.008` vs the VSYS via `(112.50, 105.60)`. East to x=112.6 hits `C_VINLS` pad 1 PMID `(112.50, 104.98)` by `−0.190`. With that capacitor ignored, VSYS F y=105.60 w=0.25 still leaves 0.16 mm between A5 copper and the track, short of a 0.12 mm trace at 0.15 mm clearance. `C_VINLS` is `(112.50, 104.50)` rot 90. Moving it does not move the VSYS dogbone.

A 0.25 GND via on the pad is 0.660 mm from the B GND fill (in the ILIM clearance hole, so it would not join the pour) and overlaps ILIM B y=105.20 by `−0.200`. Not applied.

## Next

unc=7, shorting=0. Same seven pairs. No VBUS on the dock.
