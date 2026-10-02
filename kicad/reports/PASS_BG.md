# Pass-BG — BQ25619 fanout

From Pass-BF (shorting 0, unc 30). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

## What closed

The existing `3V3` track `(97.6, 86.35)–(106.0, 86.35)` width 0.25 ran through U1 pad 15 GND. Pass-BF showed that inserting any new segment promoted that overlap into `shorting_items`. The same edit that adds copper now ends that segment at `(98.55, 86.35)`, still on U1 pads 30 and 28, clear of pad 26 and everything east of it.

North of that pad row is the module escape (EPD_MOSI, EPD_DC, EPD_RST, and the GND via at `(104.80, 85.50)`). There is no F.Cu bypass back to `(106.00, 86.35)`. U1 `3V3` joins the inner pour instead:

- Via `(98.30, 85.90)`, 0.45 / 0.20, on the pad-28 side. F.Cu stitch `(98.30, 85.90)–(98.40, 86.35)`.
- B GND and In1 GND each get a 0.42 mm hole bridged from the nearest outline vertex (about 1.1 mm on B, 1.4 mm on In1). The via center sits 0.41 mm outside the copper. `(100, 100)` stays inside the pours. Area removed is the hole only.
- In2 track `(98.30, 85.90)–(98.50, 88.30)` width 0.25 overlaps the stored `3V3` pour. The via is 2.2 mm outside that pour, so it does not add a hole-clearance zero.

Also on F.Cu, in edits that left `shorting_items` at 0:

| Net | Copper |
| --- | --- |
| `3V3` | U3 pin 2 `(107.062, 86.70)` to the existing track at `(106.30, 87.50)` |
| GND | U2 pin 17 `(112.60, 90.25)` into the EP. U3 pin 1 to the via `(104.80, 85.50)`. R_VSYS pin 2 to the via `(106.50, 91.00)`. NTC pin 2 to the track at `(112.70, 95.25)` |
| TS | U2 pin 11 down to y=93.64, east over R_TS, into R_TS pin 2 and on to NTC pin 1 |
| VBAT | U2 pin 12 corner `(112.30, 93.25)–(113.84, 92.25)` onto pins 13 and 14 |

`SW_DBG` stays `(90.50, 105.50)`. No VBUS on the dock. No track was deleted. U2 was not rotated.

## DRC (KiCad 9.0.9, `--severity-error`)

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Before (Pass-BF) | 865 | 30 | 0 | 98 |
| After | 855 | 22 | 0 | 98 |

The header total is not the gate. `shorting_items` is 0. The 98 hole-to-zone zeros are the same set as Pass-BF.

One clearance item appeared that was not in the Pass-BF report: B.Cu `ILIM` `(114.70, 105.20)` against B.Cu `SW` `(111.55, 104.90)`, actual 0.085 mm. Those two tracks were not edited. Inserting the new F.Cu segments is what made the pair show up. It is not a new short.

## Still open (unc 22)

- `VSYS`: U3 pin 3 is not on U2 SYS, and the U2 SYS stub is not on the south B.Cu run. The gap between R_ISET and C_BTST is 0.40 mm; a 0.15 mm track needs 0.45 mm. North of R_ISET the outline is in the way. West of U2, R_VSYS and the EPD_BUSY_R vertical at x=107.60 leave no slot.
- `SCL` / `SDA`: the west stubs end at x=108.16. EPD_BUSY_R occupies x=107.60 from y=89.20 to 92.50. The remaining slot is 0.37 mm, short of the 0.45 mm a minimum track needs. The stub tips and the QFN pads leave no parallel lane either.
- `PMIC_INT`: the new stub is at `(109.75, 93.84)`. Pass-BD copper is on U1 and on the old south stub. `J_STRAP_R` sits between them.
- `3V3` / `3V3_DISP`: the module rail and U3 VOUT are one net. Q1 source, the gate pull-up, and Q1 drain are not. The drain stub is F.Cu; the display rail next to it is B.Cu. A straight F.Cu run hits EPD_BUSY_L at x=90.20. No new via was drilled into the pours for this.
- `VBAT` pin 10 is still its own island (TS occupies the south escape between pins 10 and 12). The south pack copper is on the other side of the FPC.
- `VBUS`, `PMID`, `SW`, `PSEL`, `REGN`, `DISP_EN`: stubs or passives only. `L_SYS` sits on the SW stub escape, and the board edge stops a route around it. `DISP_EN` is still the long gap from R_LSCTRL at `(116.25, 93.75)` to Q1.

`shorting_items` stays 0. Further jogs that would cross those gaps were not written.
