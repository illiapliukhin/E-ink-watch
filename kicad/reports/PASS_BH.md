# Pass-BH — VSYS, PSEL, and the display switch

From Pass-BG (shorting 0, unc 22). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

## What closed

`C_BTST` moved from `(111.25, 87.50)` to `(111.25, 86.95)`. `R_ISET` moved from `(110.50, 86.00)` to `(110.50, 85.30)`, still rotation 90. The gap between those pads opened from 0.40 mm to 0.55 mm, which is enough for one 0.15 mm track. `VSYS` uses it:

- U3 pin 3 `(108.938, 85.75)` east to `(109.20, 86.35)`, across to `(112.45, 86.35)`, then out to `(114.20, 87.20)` and south into `L_SYS` pin 2.
- Short extensions put the moved cap back on the existing BTST and SW tracks.

That joins U3 VIN to the U2 SYS island. The south B.Cu VSYS run is still its own island.

`EPD_BUSY_R` on F.Cu moved from x=107.60 to x=107.48 (the vertical, the diagonal that leaves it, and the horizontal that feeds it). The slot between that wall and the west stub tips is now wide enough for one 0.15 mm track, centered at x=107.81. `PSEL` takes that slot, runs north of U3, and lands in `R_ISET` pin 2. A second track does not fit beside it.

`R_LSCTRL` moved from `(116.25, 93.75)` to `(86.30, 93.438)`, still rotation 90, beside Q1. Its old stubs were retargeted, not deleted:

- `DISP_EN` ties the resistor to Q1 pin 1.
- `3V3` walks west of the resistor, south of Q1, and into Q1 pin 2. Those two islands are now one net. They are still not on the module rail.
- Q1 pin 3 walks around to the existing `3V3_DISP` via `(89.20, 89.55)`.

The module `3V3` track still ends at `(98.55, 86.35)`. U1 pad 15 is not on it. `SW_DBG` stays `(90.50, 105.50)`. No VBUS on the dock. U2 was not rotated. The PMID via `(111.35, 103.85)` was not moved. No track was deleted.

A round-cap checker that only sampled centerlines had called a REGN route legal. KiCad measured 0.051 mm to the BTST track at `(111.01, 87.82)` and a crossing of the new VSYS run. That REGN copper was not kept.

## DRC (KiCad 9.0.9, `--severity-error`)

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Before (Pass-BG) | 855 | 22 | 0 | 98 |
| After | 857 | 17 | 0 | 98 |

The header total is not the gate. `shorting_items` is 0. The 98 hole-to-zone zeros are the same set as Pass-BG. Courtyard overlaps did not change. No new copper-edge clearance.

Two clearance lines appeared that were not in the Pass-BG report, and one line dropped. None of them is copper this pass added:

- U1 pad 39 `PMIC_INT` against the existing `nRESET` track `(96.25, 90.15)`, actual 0.100 mm. Pass-BG reported the same track against U1 pad 41, also 0.100 mm.
- An existing `SDA` track `(109.44, 108.10)` against the `CD` via `(110.60, 106.95)`, actual 0.102 mm.

The `EPD_BUSY_R` / `3V3` crossing at `(106.30, 89.20)` is the same pair as before. The BUSY segment is shorter (2.95 mm to 2.83 mm) because its east end moved to x=107.48.

## Still open (unc 17)

- `SCL` / `SDA`: the opened slot holds one track, and `PSEL` has it. From the north end of that slot, SCL does not reach the existing SCL copper west of U1. The south end is the BUSY diagonal to `(109.80, 99.25)`. Pulling BUSY off the lane left no F.Cu path back to that via.
- `REGN`: U2 pin 22, `R_ISET` pin 1, `R_TS`, and `R_VSYS` are still separate. The channel `VSYS` uses is 0.55 mm. A second 0.15 mm track needs about 0.75 mm. The north stub tips and the BTST copper block the other ways out.
- `VBUS`, `PMID`, `SW`: still the stub versus the south island. `L_SYS` and the board edge block SW. No legal F.Cu path turned up at 0.15 mm clearance.
- `3V3`: Q1 pin 2 and `R_LSCTRL` are joined to each other, not to the module rail. `EPD_BUSY_L` at x=90.20 still sits in that gap.
- `VBAT` pin 10, `PMIC_INT`, and the old `TS` stub versus the new resistor chain are unchanged.
- `VSYS` on B.Cu south of U2 is still separate from the F.Cu island that now includes U3 and `L_SYS`.

`shorting_items` stays 0. Routes that would have crossed those gaps were not written.
