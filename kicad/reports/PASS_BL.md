# Pass-BL — charger island re-place, VBUS and PMID still split

From Pass-BK (shorting 0, unc 15). No copper was written. U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

The old north pocket is unchanged. This pass tried the other orientation: rotation 180, so pins 24 and 23 (VBUS and PMID) face south toward `C_IN` and `C_PMID`. Rotation 90 or 270 still shorts adjacent pads, because the pad rectangles do not rotate with the footprint. Rotation 0 leaves VBUS and PMID on the north edge, which Pass-BK already closed.

## Seat that was checked

U2 at `(109.00, 96.00)`, rotation 180, pad angle 0.

- South copper edge y=98.35. Courtyard about x=106.4–111.6, y=93.4–98.6.
- VBUS pin 24 `(110.25, 97.938)`. PMID pin 23 `(109.75, 97.938)`.
- With the old island parts (`L_SYS`, `C_BTST`, `R_ISET`, `R_VSYS`, `R_TS`, `NTC_BAT`) and their stubs ignored, and the two `EPD_BUSY_R` vias at `(109.80, 99.25)` ignored, the worst foreign-pad gap is 0.360 mm.
- Those BUSY vias sit south of the pads. Pad south edge 98.35, via north copper 98.95, gap 0.60 mm. The seat itself does not cover them.
- `R_VSYS` at `(106.75, 93.00)` does overlap the new north-west corner and would have to move with the chip. `Q1` was left at `(88.50, 92.50)`. `SW_DBG` was left at `(90.50, 105.50)`. The `3V3_DISP` via was left at `(115.55, 89.50)`. The PMID via was left at `(111.35, 103.85)`.

West of this seat is the module courtyard (east edge x=105.75). The chip cannot slide further west without landing on it.

## VBUS exits that clear 0.15 mm by themselves

**West run, width 0.18.** `(110.25, 97.938)–(110.25, 98.650)–(108.12, 98.650)–(108.12, 102.400)`, onto the existing bar.

| segment | clearance |
| --- | --- |
| down to y=98.65 | 0.285 mm vs the PMID pad |
| west to x=108.12 | 0.000 mm vs `EPD_BUSY_R` `(107.48, 92.50)–(109.80, 99.25)` |
| south to the bar | 0.210 mm vs the SW pad |

This run does not cross the `EPD_CS_R` horizontal (it starts at x=108.80), the `EPD_BUSY_R` horizontal (it starts at x=109.80), or the GND stitch at y=102.01 (it starts at x=109.20). The only new wall is the BUSY diagonal. A 0.25 mm track does not fit between the pad south edge and that via: the window for the centerline is empty. Width 0.18 at y=98.65 is the fit, at 0.21 mm to the pad and 0.21 mm to the via, and the diagonal still crosses it.

Walking that diagonal east of the short VBUS stub, then back to the via, was checked with `R_VSYS` removed and the old VSYS/SW column east of x=113.8 removed. It still hits the TS track at y=93.64 (0.150 mm at y=93.30), `L_SYS`, the GND tie at y=95.45, `EPD_DC`, `EPD_SCK`, and `EPD_MOSI`. The via `(109.80, 99.25)` sits inside the rectangle the west run closes, so a path from `(107.48, 92.50)` has to cross that run.

**Straight drop, width 0.25.** `(110.25, 97.938)–(110.25, 102.900)`, onto the bar. Clearance 0.250 mm vs the PMID pad, and 0.400 mm if the three walls below are deleted first.

It crosses, in order:

- `EPD_CS_R` `(108.80, 100.25)–(116.85, 100.25)`
- `EPD_BUSY_R` `(109.80, 101.75)–(116.85, 101.75)`
- GND `(109.20, 102.01)–(111.20, 102.01)`

The GND left end at `(109.20, 102.01)` touches no other copper within 0.5 mm, so that segment can be shortened. The two EPD horizontals cannot. With the straight drop in place, a grid search back to the strap pads `(116.85, 100.25)` and `(116.85, 101.75)` found no path (`EPD_CS_R` 792 cells, `EPD_BUSY_R` 491 cells).

## PMID cannot use the same layer

Pin 23 is 0.50 mm west of pin 24. A west VBUS run crosses x=109.75, so the PMID pin is on the north side of that wall. A straight VBUS drop at x=110.25 is a wall on the east. The bar at y=102.90, x=108.12–110.60, is a wall on the south.

With the bar left intact and the straight drop present, a flood from the PMID pin fills x=103.5–110.0, y=97.19–102.44 (368 cells) and does not reach `C_PMID` at `(111.72, 103.40)`.

Gapping the bar does let PMID through. Width 0.18 at x=109.75 from the pin to y=103.42, then east to `(111.72, 103.42)`, measures 0.210 mm against the ISET via `(109.20, 100.99)` and clears the east hop once the dead-end spur `(110.60, 102.90)–(110.60, 105.20)` is out of the way. That spur connects to nothing except the bar. `C_IN` is on the west piece of the bar. A search from the cut end `(109.15, 102.90)` back to the VBUS landing `(110.40, 102.90)`, treating PMID as a wall and VBUS copper as free, found no path: 560 cells on a 0.20 mm grid, 723 cells on a 0.10 mm grid. The south side of the caps is already VBAT, GND, and the PMID island.

So one of the two nets can be made legal on F.Cu. Both cannot. A B.Cu hop was not cut. The only pour opening large enough for a via in this half of the board is the existing via halos, and a track from the BUSY halo `(109.80, 99.25)` to the PMID via `(111.35, 103.85)` is about 5 mm through the GND fill. That is the slit this series does not cut.

## What was not moved

`L_SYS` stays `(115.50, 91.50)` rotation 90. The SW column stays x=114.58. The east VSYS return stays x=116.42. `Q1` stays `(88.50, 92.50)`. `SW_DBG` stays `(90.50, 105.50)`. `EPD_BUSY_L` stays `(90.20, 90.96)`. The module `3V3` track still ends at `(98.55, 86.35)`. `PSEL` still owns x=107.81. No VBUS on the dock. nRF `3V3` is still the LDO, not REGN or raw SYS.

## DRC

The board file is the Pass-BJ board. No new DRC was run.

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Pass-BJ, unchanged | 858 | 15 | 0 | 98 |

`shorting_items` stays 0.

## Still open (unc 15)

- `VBUS`. Two exits clear 0.15 mm alone. The west one crosses the `EPD_BUSY_R` diagonal, and that diagonal has no remaining path to `(109.80, 99.25)`. The straight one crosses `EPD_CS_R` and `EPD_BUSY_R` on the way to the strap, and those two nets then have no F.Cu path around it.
- `PMID`. The pin is between the VBUS drop and the bar. Gapping the bar connects the pin to `C_PMID` and disconnects `C_IN` from the pin, with no second F.Cu bridge.
- South `SW` via `(115.00, 104.50)`, `REGN`, `SCL` / `SDA`, `VBAT` pin 10, `PMIC_INT`, and the old `TS` stub are unchanged.
