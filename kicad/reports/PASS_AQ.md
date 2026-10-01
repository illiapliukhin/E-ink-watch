# PASS_AQ — clean U2 re-fanout reverted (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` restored to the Pass-AL / Pass-AP file  
**From / to:** `shorting=0`, `unc=7`. No footprint kept. No copper kept.

## Verdict

**No KEEP.** The only seat that joins a net puts `R_SCL` on U2.E5 and DRC then reports `SWDIO_POGO↔3V3`. Ripping the local dogbones does not open a 0.15 mm path from E5 to the existing `R_SCL` pad, because `BTN1` via `(107.50, 110.50)` still blocks that pad and the 3V3 rail, SDA vertical, and LSCTRL seal the south pocket. Full revert. Do not apply VBUS on the dock.

## Footprints

U2 and the passives were not kept at new coordinates.

| Ref | Before and after |
|---|---|
| U2 | `(111.00, 106.00)` rot 0 |
| R_SCL | `(106.50, 110.10)` rot 90 |
| R_SDA | `(111.50, 109.00)` rot 0 |
| R_TS | `(108.00, 107.00)` rot 0 |
| NTC_BAT | `(108.20, 108.15)` rot 0 |
| R_ILIM | `(115.60, 106.60)` rot 0 |
| R_IPRETERM | `(114.80, 102.90)` rot 0 |
| R_CD | `(113.50, 107.75)` rot 90 |
| C_LDO | `(113.50, 106.80)` rot 90 |
| C_VINLS | `(112.50, 104.50)` rot 90 |
| C_PMID | `(112.20, 103.40)` rot 0 |
| R_LSCTRL | `(114.60, 108.25)` rot 90 |

## Steps (each reverted)

| Step | Edit | shorting | unc |
|---|---|---|---|
| Shrink | 3V3 via `(112.16, 107.60)` 0.60/0.30 → 0.25/0.15, in place | 0 | 7 |
| Slide | GND via `(112.40, 106.55)` → `(112.20, 106.49)`, in place, on top of the shrink | 0 | 7 |
| Seat | `R_SCL (112.00, 107.45)` rot 270, pad 1 covers E5 `(111.80, 106.80)`, pad 2 overlaps the 3V3 rail y=108.25 | 1 | 6 |
| Control | `R_ILIM (116.80, 106.60)` rot 0 | 1 | 9 |
| Nudge | `R_SCL (107.50, 110.10)` rot 90 | 2 | 7 |

The seat’s only short is `SWDIO_POGO↔3V3` at SW_DBG pad 6 `(93.45, 104.50)` versus the 3V3 track `(94.90, 101.95)`. Same pair as Pass-AP. The `R_ILIM` short is local `ILIM↔GND` and the nudge short is local `SCL↔BTN1`. Those two do not raise the SW_DBG pair. The shrink and the slide alone do not either. They also do not close an island, so they were reverted with the seat.

After the shrink and the slide, the F.Cu cells at ≥0.15 mm around E5 are only x=111.80–112.40, y=106.80–107.80 (13 cells). They do not reach `R_SCL` pad 1 `(106.50, 110.61)`. The walls are the SDA vertical x=111.40, the 3V3 rail y=108.25, LSCTRL F `(111.00, 106.80)–(110.80, 107.80)`, and the GND dogbone at x=112.80. A west-then-south SCL run at y=107.35 is clear only until x=110.2; the next leg hits the 3V3 rail (`−0.185`) and the hop into the existing SCL pad hits `BTN1` (`−0.331`).

Modest `R_SCL` moves that stay off E5 overlap VBUS, VBAT, `C_BAT`, or `BTN1` (`(106.5, 109.15)` rot 90, `(105.9, 109.4)` rot 90, `(106.5, 108.7)` rot 0, `(108.2, 109.8)` rot 90).

A5 still cannot reach a via that already sits in the B GND fill. North of `(111.80, 105.20)` is PMID and the SW via. East at y=105.20 is `+0.200` versus VSYS, then `3V3_DISP` at y=106.00. C3 and D2 still have no gap between 0.4 mm balls.

## Nets closed

None.

## Next

unc=7, shorting=0. Same seven pairs. No VBUS on the dock.
