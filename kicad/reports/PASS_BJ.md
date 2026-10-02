# Pass-BJ — SW onto L_SYS

From Pass-BI (shorting 0, unc 16). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

## What closed

U2 SW and `L_SYS` pin 1 were separate islands. The east stub tips end at x=113.838 (copper edge 113.938). With `L_SYS` at `(114.75, 91.50)` the VSYS pad starts at x=114.15, and the VSYS vertical that feeds it sits at x=114.20. That leaves no 0.15 mm column for SW.

`L_SYS` moved east to `(115.50, 91.50)`, still rotation 90, so the SW pad stays south and the VSYS pad stays north. The north `VSYS` rail still enters the VSYS pad: it stops at y=87.45, steps to x=114.55, drops to y=88.05, then runs at x=114.95 into the pad. The board edge will not hold that column any farther north. At y=87.20 a track center past about x=114.6 is outside the 0.5 mm copper keep-in.

SW then uses the opened column. From the pin-19 stub `(112.25, 88.162)` it runs to y=88.48, south at x=114.58, and into the SW pad at `(115.25, 92.48)`. Checker gaps on the new segments are 0.175 mm or more.

The east VSYS stubs cannot share that column. The copper gap from the stub tips to the SW track is 0.387 mm, and a third 0.15 mm track needs 0.45 mm. Those stubs go south at x=114.20 to y=93.60, east to x=116.42, and north into the VSYS pad at `(115.80, 90.44)`. x=116.42 sits between the inductor (pad east edge 116.10) and the `3V3_DISP` vertical at x=116.85.

New segments were appended after the PMID via `(111.35, 103.85)`. Inserting them before that via promoted a distant `nRESET_POGO` / `3V3` overlap into `shorting_items` on an earlier try; that file was not kept. The `3V3_DISP` via `(115.55, 89.50)` was not moved. Sliding it to `(116.10, 89.50)` put a new hole-clearance actual 0.000 mm on the B.Cu GND zone and split the B.Cu `3V3_DISP` run from the horizontal at y=82.40. That attempt was reverted. Flipping `L_SYS` to rotation 270 was reverted with it.

`EPD_BUSY_L` stays `(90.20, 90.96)`. The Pass-BI `3V3` path to `(93.80, 96.30)` is unchanged. The module `3V3` track still ends at `(98.55, 86.35)`. `PSEL` still owns x=107.81. `SW_DBG` stays `(90.50, 105.50)`. No VBUS on the dock.

## DRC (KiCad 9.0.9, `--severity-error`)

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Before (Pass-BI) | 857 | 16 | 0 | 98 |
| After | 858 | 15 | 0 | 98 |

The header total is not the gate. `shorting_items` is 0. Hole-clearance actual 0.000 mm vs a zone is still 98. No new clearance on the added copper is under 0.15 mm.

The extra violation is two `tracks_crossing` lines on copper this pass did not move, and one clearance line that dropped off the report:

- Existing `TS` at `(107.80, 105.65)` against existing `ILIM` at `(110.30, 105.90)`.
- Existing `EPD_SCK` at `(99.25, 84.90)` against existing `EPD_MOSI` at `(98.75, 85.20)`.

## Still open (unc 15)

- `VBUS` and `PMID` still have no legal front-side exit. West of U2, `EPD_BUSY_R` at x=107.48 and the `PSEL` track at x=107.81 leave 0.165 mm between copper edges. A 0.15 mm track needs 0.30 mm there. North of the chip, `R_ISET` (south edge y=86.08) and the `VSYS` rail at y=86.35 leave room for one track, which `VSYS` already uses. The drops from the SW and BTST stubs into `C_BTST` close the y=87.6 channel. `VBUS` has no vias, so a backside hop needs two new vias and notches in the stored GND fills. The dock is not a VBUS target.
- `SW` now reaches `L_SYS` pin 1. The south via `(115.00, 104.50)` is still its own island.
- `REGN` still does not fit beside `VSYS`. The east side of U2 is now the SW column and the VSYS bypass, so it is not a second REGN corridor.
- `SCL` / `SDA`: `PSEL` still has the only slot at x=107.81.
- `VBAT` pin 10, `PMIC_INT`, the old `TS` stub, and the south B.Cu `VSYS` island are unchanged.

`shorting_items` stays 0.
