# PASS_AJ — three new corridors, no KEEP (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` (Pass-AH KEEP only)  
**From / to:** `shorting=0`, `unc=8`. No copper kept.  
**Tool:** KiCad probe at 0.15 mm clearance, endpoints inside r≈19.2 of (100, 100). No DRC candidate was saved, because none of the routes below was clear for the whole path.

## Verdict

**No KEEP.** Unconnected stays 8. Shorting stays 0. The Pass-AI west seam was not replayed. Do not apply VBUS on the dock.

## Inventory (unchanged)

1. GND F `(111.8, 106.4)` vs U2 A5 `(111.8, 105.2)`
2. GND F `(111.8, 106.4)` vs west F `(108.71, 108.6)`
3. `3V3_DISP` B `(92, 87)` vs west F `(84.45, 98.25)`
4. SDA F `(109.44, 108.1)` vs U1 pad 27 `(98.8, 87.25)`
5. SCL `R_SCL` pad1 `(106.5, 110.61)` vs E5 stub `(111.8, 106.8)`
6. SCL E5 stub vs U1 pad 29 `(98.0, 87.25)`
7. PMIC_INT B `(94.2, 90.55)–(94.2, 106.4)` vs F stub `(110.6, 106.4)`
8. TS F `(111.0, 106.0)` vs TS B `(107.8, 105.65)`

## Strategy 1 — PMIC_INT around the BTN wall (not the y=106.72 street)

The B.Cu street at y≈106.72 still dies on the VBAT via `(96.2, 106.25)` (edge `+0.121`). BTN1/2/3 B.Cu verticals at x=98 / 98.5 / 98.8 run from about y=94 to y=110, so no B.Cu line at that band reaches D2.

A different branch uses the existing PMIC_INT vertical, which already spans the north end of those buttons:

- B.Cu w=0.12 `(94.2, 92.7)–(103.15, 92.7)` is clear (tightest `+0.450` vs EPD_SCK).
- Via 0.25 at `(102.7, 92.7)` is clear (`+0.278` vs U1 NC).
- F.Cu south at x=106.9 is clear from y=93.6 to y=102.0, then VBUS F `(105.5, 102.4)–(108.12, 102.4)` and 3V3 F at y=103.35 close it.
- A B.Cu hop across that F.Cu power band is pinched: VSYS B x=106.8 (y=100.3–104.625) and the 3V3 via `(107.5, 102.975)` size 0.6 leave no 0.15 mm slot. East of x=108 the ISET B vertical at x=108.2 takes the next column.

Not applied.

## Strategy 2 — SCL south of `R_SCL`, not east into the BTN1 via

The pad pocket on F.Cu is only about x=106.2–107.1, y=110.3–111.5. A south stub `(106.5, 110.61)–(106.5, 111.2)` is clear, then every eastbound y hits the BTN1 F.Cu vertical x=107.5 (y=110.5–112) or the SW1 pads at y=112. Going under the buttons at y≈113 hits the GND via `(110.9, 113)` and the north run back to E5 hits the 3V3 rail y=108.25 and the SDA diagonal. A slight slide of `R_SCL` stays inside the same pocket. Not applied. `R_SCL` was not moved.

## Strategy 3 — SDA from U1, B.Cu west of the TS elbow

F.Cu from U1 pad 27 reaches `(107.2, 102.05)` (about 890 grid nodes) and stops on VBUS y=102.4. B.Cu x=107.35 from y=104.7 to y=107.5 is clear (`+0.265` vs the TS via). Those two pieces do not meet: the 3V3 via `(107.5, 102.975)` and VSYS B x=106.8 leave no column between them. South of that column, `R_TS` and the TS B elbow block a via onto the SDA stub. Not applied.

## Also checked — `3V3_DISP` by the east rail, not the west seam

F.Cu from the west via `(85, 102.75)` reaches `(114.0, 108.75)`. The nearest east-island copper is B.Cu `(113, 107.4)–(115.55, 107.4)`, 1.35 mm away. The gap is the 3V3 F rail y=107.8 (x=112.51–114.6), the 3V3 via `(114.3, 107.95)`, `R_CD`, `C_LDO`, `R_LSCTRL`, and the ILIM via `(114.7, 106.5)`. Clear vias in that neighborhood sit on the rail at y≈107.0–107.2 and are not on the F.Cu flood. Sliding `R_CD` / `C_LDO` would not move the CD via or the 3V3 via, so that spread does not open the slot. The Pass-AI seam was not repeated.

A5 is still a one-cell F.Cu pocket: C_VINLS PMID pad, VSYS, and the 3V3_DISP rail at y=106 leave no dogbone. West GND still stops on 3V3, `R_SDA`, LSCTRL, and BTN3. TS still stops on the SDA diagonal and the ILIM via.

## Archives

No new copper script was applied. Probe notes are this file.
