# PASS_AP — U2 zone re-layout reverted (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` restored to the Pass-AL file  
**From / to:** `shorting=0`, `unc=7`. No footprint kept. No copper kept.

## Verdict

**No KEEP.** A real move of `R_SCL` onto U2.E5 joins the local SCL island (`unc` 7→6) and then DRC reports `SWDIO_POGO↔3V3` at `SW_DBG`. That pair is not in the PMIC zone. The trial was fully reverted. Rigid shifts of the whole PMIC island by 1–2 mm overlap foreign copper. U2 stays at `(111, 106)` rot 0. Do not apply VBUS on the dock.

## Baseline

Still open: GND A5, east–west `3V3_DISP`, SDA vs U1.27, SCL `R_SCL` vs E5, SCL E5 vs U1.29, PMIC_INT, TS. Pass-AN markers were `shorting_items=0`, `unconnected_items=7`. This pass ends on that same board.

## Footprints tried

| Ref | Before | Trial | After (reverted) |
|---|---|---|---|
| U2 | `(111.00, 106.00)` rot 0 | not moved | same |
| R_SCL | `(106.50, 110.10)` rot 90 | `(112.05, 107.55)` rot 270 | `(106.50, 110.10)` rot 90 |
| R_SDA | `(111.50, 109.00)` rot 0 | not moved | same |
| R_TS | `(108.00, 107.00)` rot 0 | not moved | same |
| NTC_BAT | `(108.20, 108.15)` rot 0 | not moved | same |
| R_ILIM | `(115.60, 106.60)` rot 0 | not moved | same |
| R_IPRETERM | `(114.80, 102.90)` rot 0 | not moved | same |
| R_CD | `(113.50, 107.75)` rot 90 | not moved | same |
| C_LDO | `(113.50, 106.80)` rot 90 | not moved | same |
| C_VINLS | `(112.50, 104.50)` rot 90 | not moved | same |
| C_PMID | `(112.20, 103.40)` rot 0 | not moved | same |
| R_LSCTRL | `(114.60, 108.25)` rot 90 | not moved | same |

`R_SCL` rot 270 puts pad 1 (SCL) at `(112.05, 107.04)`, rectangle x=111.73–112.37, y=106.77–107.31. That rectangle covers U2.E5 `(111.80, 106.80)`. Pad 2 (3V3) is x=111.73–112.37, y=107.79–108.33 and overlaps the 3V3 rail at y=108.25. Pad-edge clearance vs foreign copper is at least `+0.162` once the D5 GND via leaves `(112.40, 106.55)`. The 0.60 via at `(112.16, 107.60)` still overlaps the SCL pad unless it is shrunk.

## Why the island cannot slide

Cluster checked together: U2, R_SDA, R_SCL, R_TS, NTC_BAT, R_ILIM, R_IPRETERM, R_CD, C_LDO, C_VINLS, C_PMID, R_LSCTRL. Every rigid shift of ±1.0, ±1.5, or ±2.0 mm overlaps foreign copper. Worst gaps are `−0.567` to `−0.709` (strap test pad, SW vias, BTN vias, CD, 3V3). Not written.

U2 alone, dogbone ends stretched, passives left put: the least-bad ≥1 mm step is `(−1.0, +1.0)` at `+0.167` vs `NTC_BAT` pad 2. That is only a pad screen. Moving the dogbones with the balls is the cluster check above, and it does not clear. Rotating U2 onto the existing dogbones still overlaps 23 pads (Pass-AL). Not applied.

Inner balls do not gain an exit by moving the package. Pitch is 0.4 mm and the pads are 0.23 mm circles. A track at 0.15 mm clearance does not fit between them. C3 (TS) and D2 (PMIC_INT) stay caged. A through via on those pads lands in the B GND fill.

## DRC of the R_SCL seat

All of these were reverted.

| Trial | shorting | unc | What DRC named |
|---|---|---|---|
| `R_SCL` only | 2 | 6 | SCL↔3V3 on the new pad vs the 0.60 via `(112.16, 107.60)`; SWDIO_POGO↔3V3 at SW_DBG pad 6 `(93.45, 104.50)` |
| `R_SCL` + in-place shrink of that via to 0.25/0.15 + GND via `(112.40, 106.55)` → `(112.20, 106.49)` | 1 | 6 | SWDIO_POGO↔3V3 only. Header 897 violations. Local SCL island closed |
| Same seat, 3V3 spine moved to x=112.40, via moved to `(114.55, 108.00)` size 0.35 | 2 | 6 | C3 GND↔3V3 at `(97.48, 108.80)` plus SWDIO_POGO↔3V3 |
| Same seat, 3V3 via deleted | 3 | 6 | those two plus nRESET_POGO↔3V3 |
| Via shrink + GND slide, `R_SCL` left at `(106.50, 110.10)` | 0 | 7 | no island closed, so not kept |

The local SCL pair (`R_SCL` pad 1 vs U2.E5) is the one that dropped. E5 vs U1.29 stayed open. A5, `3V3_DISP`, SDA, PMIC_INT, and TS stayed open.

Deleting the 3V3 via, or hauling it across the pocket, is what wakes the C3 and nRESET pairs. An in-place shrink without the footprint move does not. The footprint move itself is what wakes SWDIO_POGO↔3V3. Shorting must stay 0, so the seat was not kept.

## Nets closed

None. The board file matches the pre-pass copy `backups/_passap_base.kicad_pcb`.

## Next

unc=7, shorting=0. Same seven pairs. No VBUS on the dock.
