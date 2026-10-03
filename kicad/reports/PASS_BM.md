# Pass-BM — VBUS and PMID have a legal pair of routes; the keep raises shorting

From Pass-BL (shorting 0, unc 15). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. The copper that was tried was restored. This pass does not merge.

The user decision was to rip the `PSEL` and `EPD_BUSY_R` tracks that close the north pocket, then route both `VBUS` and `PMID`. Both routes clear the 0.15 mm rule. They cannot be kept: clearing those blockers together promotes existing overlaps into `shorting_items`.

## Routes that cleared a 0.16 mm centerline check

`VBUS` cannot share the west F.Cu lane with `PMID`. Both pins are east of that lane, so two westbound F.Cu runs cross. `VBUS` hops to B.Cu in the gap between `EPD_MOSI` at y=86.50 and `EPD_CS_R` at y=88.00. `PMID` stays on F.Cu.

Width of every new track is 0.15 mm. Existing fat `VBUS` was not narrowed.

**VBUS**

- F pad tie: `(109.062, 89.750)–(109.45, 89.750)–(109.45, 89.062)–(109.75, 89.062)`
- F down: `(109.75, 89.062)–(109.75, 87.25)`
- Vias 0.45/0.20 at `(109.75, 87.25)` and `(107.65, 87.42)`, net VBUS
- B: `(109.75, 87.25)–(107.65, 87.25)–(107.65, 87.42)`
- F south: `(107.65, 87.42)–(107.65, 102.20)–(108.12, 102.40)` onto the existing bar

The west via is not at y=87.50. That site is 0.138 mm from the 3V3 corner at `(107.06, 87.50)`. At `(107.65, 87.42)` the gaps are 0.195 mm to U3 pin 2, 0.238 mm to the 3V3 tracks, and 0.265 mm to `EPD_CS_R` on B.Cu.

**PMID**, with the `EPD_BUSY_R` strap kept (`(109.80, 99.25)–(109.80, 101.75)–(116.85, 101.75)`):

`(110.25, 89.062)–(110.25, 87.80)–(110.22, 87.80)–(110.22, 86.75)–(108.20, 86.75)–(108.20, 101.55)–(109.30, 101.55)–(109.30, 102.40)–(111.15, 102.40)–(111.15, 103.85)–(111.35, 103.85)`

The east jog is at y=102.40, under the strap and north of the fat VBUS bar at y=102.90. A jog at y=100.50 toward x=108.70 hits `EPD_CS_R` `(108.80, 100.25)–(116.85, 100.25)`. The column at x=108.20 cannot continue through the VBUS spur `(108.12, 102.40)–(108.12, 102.90)` w=0.40. GND `(109.20, 102.01)–(111.20, 102.01)` was shortened to start at x=111.70 so the drop at x=111.15 is clear. The spur and the bar stay.

## What had to move, and what could not be rebuilt

Out of the corridor, in the trial only:

- `PSEL` from the pin through `(108.11, 86.30)`. The tail from `(107.91, 86.10)` to `R_ISET` pin 2 was left, so the resistor side stayed one piece and the pin became the other.
- `EPD_BUSY_R` `(104.65, 89.20)–(107.48, 89.20)`, the wall at x=107.48, and the diagonal to `(109.80, 99.25)`. The strap and the U1 fanout to via `(105.50, 91.75)` stayed. Those two islands no longer meet.
- SCL and SDA west stubs, pulled back onto their pads. They still do not reach U1.
- The dangling GND end at `(109.20, 102.01)`.

`PSEL` has no third F.Cu lane. After the two power lanes, the pinch around y=91.6–92.5 is about 0.90 mm, which holds two 0.15 mm tracks. An A* from pin 2 dies in the pad shadow. A B.Cu hop from the pin to `R_ISET` would have to cross the EPD ladder. The rungs are too close to pass between, and going around `EPD_MOSI` (it runs to x=117.50) is a long slit. Not cut.

`EPD_BUSY_R` on F.Cu, with the power walls reserved, floods only to x=107.2 and y=102.0. The VBUS column and the bar close the west island. A 0.45 mm via does not fit between PMID at x=108.20 and the B.Cu `EPD_CS_R` vertical at x=108.80 (copper gap about 0.43 mm; the via needs 0.75 mm). The existing vias `(105.50, 91.75)` and `(109.80, 99.25)` are 8.6 mm apart. That B.Cu slit was not cut.

`REGN` from pin 22 toward `R_ISET` pin 1 is a 46-cell pocket. East of `C_BTST` is the BTST and SW stubs and the VSYS riser at x=112.45. SCL, SDA, and the south SW via `(115.00, 104.50)` do not gain a path from this corridor. The east side of the chip is still the SW column.

Unc arithmetic if the copper had stayed: VBUS −1, PMID −1, PSEL +1, BUSY +1. Unc stays 15. Below 15 needs one of those two nets rebuilt, or another open net closed. Neither happened.

## DRC on the trial, then the revert

KiCad 9.0.9, error severity. New segments were inserted after the PMID via `(111.35, 103.85)`. B.Cu and In1.Cu each got one spur: nearest boundary vertex 0.316 mm from an r=0.50 stadium on the B.Cu hop. Fill area dropped 2.74 mm² on each. In2 is outside those vias (the In2 outline is r=12).

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Pass-BJ / Pass-BL, kept | 858 | 15 | 0 | 98 |
| Trial, with the notch | 863 | 15 | 2 | 98 |
| Same copper, notch removed | 867 | 15 | 2 | 102 |

`VBUS` and `PMID` were absent from `[unconnected_items]`. `PSEL` and `EPD_BUSY_R` were present. The two `shorting_items` are existing overlaps, reclassified:

- `nRESET_POGO` pad 4 of `SW_DBG` `(93.45, 106.50)` against `3V3` `(96.50, 107.75)–(92.00, 105.50)`
- `EPD_MOSI` via `(85.35, 97.80)` against `EPD_SCK` `(85.00, 101.25)–(85.00, 96.50)`

Moving only the VBUS stubs, or only `PSEL`, or only the BUSY wall, leaves `shorting_items` at 0. Moving the VBUS stubs together with both `PSEL` and the BUSY wall raises it to 1 (the nRESET pair). Deleting those blockers instead of parking them does the same. The full route adds the MOSI/SCK pair. Without the notch, the two new vias add four hole-clearance actual 0.000 mm hits against a zone (98 → 102).

The board file was restored from the pre-edit copy. `shorting_items` is 0 again. Unc is 15. U2 stays rotation 0. `L_SYS` stays `(115.50, 91.50)` rotation 90. The SW column stays x=114.58. `SW_DBG` stays `(90.50, 105.50)`. `EPD_BUSY_L` stays `(90.20, 90.96)`. The `3V3_DISP` via stays `(115.55, 89.50)`. No VBUS on the dock. nRF `3V3` is still the LDO.

## Still open (unc 15)

- `VBUS` and `PMID`. The pair of routes above is legal on its own and was not kept, because the corridor clear raises `shorting_items`.
- `PSEL` still owns the slot at x=107.81. `EPD_BUSY_R` still owns x=107.48 and the diagonal.
- South `SW` via `(115.00, 104.50)`, `REGN`, `SCL` / `SDA`, `VBAT` pin 10, `PMIC_INT`, and the old `TS` stub are unchanged.
