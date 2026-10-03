# Pass-BN — VBUS and PMID are connected, and the two latent overlaps stay clear

From Pass-BM (shorting 0, unc 15). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

The two overlaps Pass-BM saw promoted into `shorting_items` are real copper overlaps. Baseline DRC listed the `nRESET_POGO` / `3V3` pair as a solder-mask bridge and a track crossing, and it did not list the `EPD_MOSI` / `EPD_SCK` overlap at all. Neither was in `shorting_items` until both blocker families moved. That guess was right.

## What was kept

`VBUS` and `PMID` leave the unconnected list. `shorting_items` stays 0. Unconnected stays 15, because `PSEL` and `EPD_BUSY_R` each open an island and have no legal rebuild. Hole-clearance actual 0.000 vs a zone stays 98.

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Pass-BJ / start of Pass-BN | 858 | 15 | 0 | 98 |
| Pass-BN | 853 | 15 | 0 | 98 |

KiCad 9.0.9, error severity. New segments were inserted after the PMID via `(111.35, 103.85)`.

### The two overlaps

`3V3` `(96.50, 107.75)–(92.00, 105.50)` ran through `SW_DBG` pad 4 (`nRESET_POGO`). There is no F.Cu gap between that pad, the `J_SWD` nRESET pad, and the `SWDCLK_POGO` loop. The diagonal was parked onto the fat vertical as `(96.50, 108.30)–(96.50, 108.60)`. The east island still reaches the west B.Cu spine: a 0.50/0.30 via at `(96.50, 107.75)` sits on the existing F.Cu end and inside the In2 `3V3` pour, which already covers the via at `(92.00, 105.20)`. B.Cu and In1.Cu each got a 0.50 mm circle at that via (bridge 0.527 mm, area drop 0.79 mm²). `SW_DBG` stays at `(90.50, 105.50)`, default off.

`EPD_MOSI` via `(85.35, 97.80)` was 0.60/0.30 and overlapped `EPD_SCK` at x=85.00. It is now 0.50/0.30 in place. The gap is +0.010 mm, so it is a clearance miss and not a short. A 0.15 mm gap does not fit: `3V3_DISP` is colinear with `EPD_SCK` on x=85 from y=98.25, and the GND vias east of the pocket block moving the via.

After both blocker families, the VBUS stubs, and the PMID stub were parked, `shorting_items` stayed 0. Before this separation, that same park raised shorting to 1.

### VBUS and PMID

Width is 0.20 mm on the long runs and 0.18 mm on the four segments that leave the QFN pads. A 0.25 mm track on the pin exits or on the PMID column at x=108.20 drops under 0.16 mm. The existing fat VBUS bar was not narrowed. Vias are 0.45/0.20.

**VBUS**

- F pad tie: `(109.062, 89.750)–(109.45, 89.750)–(109.45, 89.062)–(109.75, 89.062)`
- F down: `(109.75, 89.062)–(109.75, 87.25)`
- B hop: `(109.75, 87.25)–(107.65, 87.25)–(107.65, 87.42)`
- F south: `(107.65, 87.42)–(107.65, 102.20)–(108.12, 102.40)` onto the existing bar

**PMID**, strap kept:

- `(110.25, 89.062)–(110.25, 87.80)–(110.22, 86.75)–(108.20, 86.75)`
- `(108.20, 86.75)–(108.20, 101.55)–(109.30, 101.55)–(109.30, 102.40)`
- `(109.30, 102.40)–(111.15, 102.40)–(111.15, 103.85)–(111.35, 103.85)`

The B hop is inside the GND pours. A r=0.50 spur, the Pass-BM notch, attaches to the relief of the `EPD_CS_R` via `(108.80, 88.00)` 0.60/0.30 and KiCad then reports that via at clearance 0.000 against the zone. That spur was not kept. The kept notch unions a 0.31 mm track stadium and 0.45 mm via circles into the existing hole around that via. Area drop is 2.223 mm² on B and on In1. The `EPD_CS_R` via stays 0.500 mm from the hole edge. Zone clearance on this board is 0.20 mm; the smaller Pass-BM-sized cut left the new vias at 0.179–0.195 mm and was enlarged. In2 does not cover this hop.

GND `(109.20, 102.01)–(111.20, 102.01)` now starts at x=111.70 so the PMID drop at x=111.15 is clear. The SCL and SDA west stubs were parked onto their pads. Both nets were already open.

## What was refused

`PSEL` and `EPD_BUSY_R` were not rebuilt. At a 0.16 mm margin neither net has an F.Cu or B.Cu path from the pin or the west via to the copper that was left in place (the `PSEL` tail from `(107.91, 86.10)`, and `EPD_BUSY_R` via `(109.80, 99.25)`). The pinch between VBUS at x=107.65 and PMID at x=108.20 is about 0.35 mm of edge gap. A 0.15 mm track needs 0.45 mm. No 0.45 mm via fits between PMID and the B.Cu `EPD_CS_R` vertical at x=108.80.

A B.Cu `3V3` hop from a via at `(96.52, 109.30)` back to `(92.00, 105.35)` also connects the diagonal's islands, and a stadium on that hop made existing copper read as clearance 0.000 against a zone. It was not kept. The In2 stitch above does the same job with a short bridge.

U2 was not rotated. Rotation 270 still shorts neighboring pads because the pad rectangles do not rotate. No VBUS was added on the dock. `L_SYS`, `Q1`, `SW_DBG`, `EPD_BUSY_L`, and the `3V3_DISP` via `(115.55, 89.50)` were not moved. nRF `3V3` is still the MCP1700 from SYS. The display switch is still DMG2305UX, gate `DISP_EN`, panel default off.

## Still open

`VBAT` (two islands), `VSYS`, `EPD_BUSY_R`, `SDA`, `SCL`, `PMIC_INT` (two), `TS` (two), `SW`, `PSEL`, `REGN` (three). That is 15. `VBUS` and `PMID` are not on the list.
