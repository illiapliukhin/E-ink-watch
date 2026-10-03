# Pass-BK — VBUS and PMID still blocked

From Pass-BJ (shorting 0, unc 15). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. No copper was written. This pass does not merge.

## What was tried

The charge path is still two islands. `VBUS` has no vias. The north stubs sit in a closed F.Cu pocket, and the south island is the copper around `C_IN` at about y=102.4–105.2. `PMID` is the same shape: the pin-23 stub is in that north pocket, and the south via `(111.35, 103.85)` was not moved.

A 0.20 mm flood of the `VBUS` pocket, treating foreign F.Cu as a wall at 0.15 mm plus a 0.075 mm half-width, covers x=108.2–110.6 and y=86.3–89.9 (149 cells) and does not reach `(108.12, 102.40)`. The walls are:

- `EPD_CS_R` via `(108.80, 88.00)`, size 0.6
- `PSEL` at x=108.11 (y=86.30–88.40) and x=107.81 (y=88.70–90.25), then the horizontal at y=90.25 back to pin 2
- `C_BTST` pad at `(110.74, 86.95)` and the BTST drop into it
- the `PMID` stub `(110.25, 89.062)–(110.25, 88.162)`
- the `VSYS` rail `(109.20, 86.35)–(112.45, 86.35)` and the drop into U3 pin 3
- the QFN body and the exposed pad

Removing the `C_BTST`, `R_ISET`, and `R_VSYS` pads from that flood does not open a path. Removing the `PSEL` and `EPD_BUSY_R` F.Cu tracks does. The path that appears runs west to about x=107.75 and south to y=100.5. Reserving that corridor and searching for a new `PSEL` route from pin 2 to `R_ISET` dies in 9 cells at the pin. On F.Cu the west slot cannot carry both nets, and `EPD_BUSY_R` still has to reach its via `(109.80, 99.25)`, so its diagonal crosses the same slot.

The copper gap that slot would have to use is still 0.165 mm: `EPD_BUSY_R` center x=107.48, width 0.18, east edge 107.57; `PSEL` center x=107.81, width 0.15, west edge 107.735. A 0.15 mm track needs 0.45 mm between those edges. Moving `R_VSYS` west to x=106.25 and parking `EPD_BUSY_R` at x=107.08 widens it enough for one track at x=107.45 (checker 0.205 mm) from y=90.4 to y=92.3. The diagonal to `(109.80, 99.25)` then crosses that track. A 0.45 mm via does not fit in the widened slot: the slot is about 0.56 mm and the via needs 0.75 mm.

A layer hop does not fit either. A search for a via pair, each 0.45 mm and at least 0.16 mm clear on both F.Cu and B.Cu, with a B.Cu segment under 3.5 mm between them, found no pair in the window around the pocket. Dropping the B.Cu `EPD_CS_MAIN` vertical at x=107.50 still found none. B.Cu under the pocket is a ladder: `EPD_MOSI` y=86.50, `EPD_CS_R` y=88.00 and x=108.80, `EPD_DC` y=88.50, `EPD_RST` y=89.00, `EPD_CS_MAIN` y=90.15 and x=107.50, `EPD_BUSY_L` y=90.80. The gaps that can hold a via are about y=87.25 and y=89.55, and those rows are not clear of F.Cu once the via is 0.45 mm.

New through-vias also have nowhere to sit outside the stored pours. A 0.25 mm grid from x=104–118 and y=84–110 found one point at least 0.40 mm outside B.Cu, In1.Cu, and In2.Cu with 0.05 mm of room to an existing via: `(111.00, 104.25)`, 0.057 mm from the PMID via `(111.35, 103.85)`. That is the same south island, not a second hop. Sites at least 0.42 mm outside B and In1 with 0.10 mm of via room: none. `(113.6, 98.5)` is 0.404 mm outside B and In1, but it is inside the `EPD_DC` via halo at `(113.50, 98.50)`. A notch long enough to walk `VBUS` from y=88 to y=102 would be a pour slit on the order of 14 mm. That was not cut.

`PMID` is a smaller pocket, x=108.5–110.5 and y=86.5–89.25 (41 cells). Its extra walls are the `VBUS` stub at x=109.75 and the `REGN` stub at x=110.75. A flood that ignores `PSEL` and `EPD_BUSY_R` still does not reach `(111.35, 103.85)`. The east side is the Pass-BJ SW column and the VSYS bypass, which this pass did not move.

`L_SYS` stays `(115.50, 91.50)` rotation 90. The SW column stays x=114.58. VSYS still steps east only after y=88.05 and the east stubs still return at x=116.42. The `3V3_DISP` via stays `(115.55, 89.50)`. `EPD_BUSY_L` stays `(90.20, 90.96)`. The Pass-BI `3V3` land stays `(93.80, 96.30)`. `PSEL` still owns x=107.81. `SW_DBG` stays `(90.50, 105.50)`. The module `3V3` track still ends at `(98.55, 86.35)`. No VBUS on the dock. The PMID via was not moved.

## DRC

The board file is the Pass-BJ board. No new DRC was run.

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Pass-BJ, unchanged | 858 | 15 | 0 | 98 |

`shorting_items` stays 0.

## Still open (unc 15)

- `VBUS`. F.Cu pocket x=108.2–110.6, y=86.3–89.9. The only corridor that reaches the south island requires deleting both the `PSEL` wall and the `EPD_BUSY_R` diagonal, and `PSEL` then has no remaining F.Cu path to `R_ISET`. No legal via pair on F and B. No pour opening for a new via.
- `PMID`. F.Cu pocket x=108.5–110.5, y=86.5–89.25. Still separate from via `(111.35, 103.85)` after the same track deletion. The east exit is the SW column at x=114.58 and the VSYS return at x=116.42.
- South `SW` via `(115.00, 104.50)` is still separate from `L_SYS` pin 1. The VSYS bypass at y=93.60 covers the pad's x range (114.20–116.42). East of x=116.42 the gap to the `3V3_DISP` vertical at x=116.85 is 0.230 mm. A west jog at y=90.2 meets the GND stubs at x=113.84. Not routed, because a `VBUS` route that cleared 0.15 mm was the gate for any new copper.
- `REGN` still has to share the one-track channel between `R_ISET` and the `VSYS` rail at y=86.35, and the east side is now the SW column.
- `SCL` / `SDA` still need a second west corridor. x=107.81 stays `PSEL`.
- `VBAT` pin 10, `PMIC_INT`, the old `TS` stub, and the south B.Cu `VSYS` island are unchanged.
