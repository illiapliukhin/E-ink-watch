# PASS_BC — U2 fanout still cannot escape the 0.4 mm pitch (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-BA KEEP)  
**From / to:** `shorting=0`, `unc=4`. No copper moved. No footprint edit was kept.  
**R_SCL:** `(112.00, 107.45)` rot 270.  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** The BQ25120A land is already the TI YFP0025 pattern: NSMD 0.23 mm rounds on a 0.40 mm pitch. That pitch cannot grow a ≥0.15 mm escape for A5, D2, C3, or E5, and the copper around the north corner has no legal place to move. Unconnected stays 4. `shorting_items` stays 0.

The Pass-AZ SDA hop and the Pass-BA `3V3_DISP` stitch stay, including their keepouts. `R_SCL` was not moved.

## Footprint

Library and board footprint: `EInkWatch:Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm`. Pads are 0.23 mm circles. Ball pitch is 0.40 mm, so the gap between pad edges is 0.17 mm.

A 0.15 mm track with 0.15 mm clearance needs about 0.45 mm between two foreign pad edges. The pitch is 0.40 mm, so that channel does not exist at any pad diameter above zero. Shrinking the lands below the datasheet NSMD size does not open a route between balls.

| Escape | What the rules need | What the 0.40 mm pitch gives |
|--------|---------------------|------------------------------|
| Track between balls | pad gap ≥ 0.45 mm | 0.17 mm with 0.23 mm pads |
| Through via in the pad | drill ≤ 0.07 mm | board minimum through drill is 0.30 mm; the vias already on the board are 0.15–0.30 mm |
| Microvia in the pad | 0.30 / 0.10, the design-rule minimum | copper gap to a 0.23 mm neighbor is 0.135 mm |

A through via centered on a ball sees the next pad edge at 0.285 mm. Hole clearance is 0.25 mm, so the drill radius has to be ≤ 0.035 mm. That is not a via this board can build. The same arithmetic is why D2 and C3, which are interior balls, cannot grow a dogbone.

A microvia is allowed down to 0.30 mm pad and 0.10 mm drill (`min_microvia_diameter` / `min_microvia_drill`), with 0.10 mm annular ring. Against a 0.23 mm neighbor the copper gap is 0.135 mm. Shrinking the two neighbors to 0.20 mm makes copper and hole clearance land on 0.15 mm and 0.25 mm exactly. That was checked for A5 and still does not connect, below.

Pad names and nets already match the YFP ball map (A5 GND, D2 INT, C3 TS, E5 SCL, C5 LS/LDO as `3V3_DISP`). The schematic symbol uses a different pin numbering and was not the blocker. No footprint swap was written.

## A5

A5 is `(111.80, 105.20)`. A1, on the same row, is already on GND: F `(110.20, 105.20)–(109.20, 105.20)` w=0.30 and the via `(109.55, 104.50)`. D5 is tied at `(111.80, 106.40)`. Joining A5 to either of those drops one unconnected item. Neither join fits.

South is B5. The pad edge gap is 0.17 mm, and VSYS F `(111.80, 105.60)–(112.50, 105.60)` w=0.25 leaves 0.160 mm between copper edges. East is `C_VINLS` pad 1, gap 0.275 mm. A 0.15 mm track needs 0.30 mm to pass a foreign pad, so the east slot is a dead end against the cap.

The outside of the package is north. A 0.15 mm GND track `(111.80, 105.20) → (111.80, 104.50) → (112.35, 104.15)` lands on `C_VINLS` pad 2 (GND) and clears every other foreign pad and track by ≥0.200 mm **if two pieces are absent**:

1. SW via `(111.55, 104.55)` size 0.55. Its east edge is x=111.825, so it covers A5's column.
2. PMID F `(112.50, 104.98)–(112.00, 104.98)` w=0.25 and the drop `(112.00, 104.98)–(112.00, 103.85)` w=0.25.

Those two cannot move.

The SW via has to stay near x=111.55 to reach A4 and to stay off the PMID dogbone at x=111.05 w=0.20 (east edge 111.15). The slot between that dogbone and a GND track on x=111.80 is about 0.57 mm of copper. Hole clearance 0.25 mm does not fit a drill in it: for a 0.15 mm drill the allowed center window is empty (PMID side wants x≥111.475, GND side wants x≤111.400). Shrinking the via does not help. Its center is only 0.25 mm west of A5, so the copper still reaches x=111.80 until the radius is ~0.03 mm.

Moving the via north of the dogbone (y<103.85) lands on `C_PMID` / `C_VINLS`. The F run from A4 down that column dead-ends on `C_PMID` pad 1 `(111.44–112.00, 103.09–103.71)`. An east bypass of PMID hits `J_STRAP_R` pad MP, which fills `(113.00–115.00, 104.05–105.25)`, and `C_PMID` pad 2. The PMID dogbone cannot slide west: VBUS F at x=110.60 w=0.40 has its east edge at 110.80, and the dogbone is already against that wall at x=111.05.

A microvia on the A5 pad fails for a different pair of walls. In1 GND covers the center by only 0.021 mm and deepens toward B5 (0.12 mm at the south edge of the pad). The annular ring of a 0.10 mm drill starts at radius 0.05 mm, so the north half of the pad does not touch the fill. The south half, where the fill is deep enough, is the B5 / VSYS side. The north half is the PMID track at y=104.98: a 0.30 mm via there has copper clearance 0.000 mm. In2 is 0.92 mm away and B is 0.66 mm away, so the planes are not the short. The fill simply does not reach a via that also clears VSYS and PMID.

## D2, C3, E5

D2 `(110.60, 106.40)` and C3 `(111.00, 106.00)` are interior balls. With pours ignored, D2's free F pocket is 0.025 mm² (the pad). Deleting the IPRETERM via does not grow it. C3 is not even in free F until the ILIM and PMID tracks are removed, and then the pocket is the pad again. A microvia on either ball would drill In1 GND or In2 3V3. Both are the wrong net. D2's B pocket is 1.32 mm², bounds `(110.44, 105.48)–(112.62, 106.68)`, and it does not reach the PMIC_INT run at x=94.20.

E5's free pocket stays 0.32 mm², bounds about `(111.69, 106.67)–(112.53, 107.42)`, the same seat as Pass-BA. Removing the SDA vertical at x=111.40 grows it and still does not create a drill-legal via. Pass-BA measured the nearest one at 1.87 mm. That vertical is the local E4 dogbone; the SDA hop under VBAT was not touched. `R_SCL` was not moved. 114 seats in Pass-BB already left this pocket unchanged.

## DRC

No new DRC. Nothing was written. The board file matches the Pass-BA KEEP (`f56765f`): 4 unconnected, `shorting_items` absent.

Still open: A5 GND, SCL, PMIC_INT, TS.
