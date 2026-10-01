# PASS_AS — 3V3 jog off SW_DBG pad 6 reverted (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` restored to the Pass-AL file  
**From / to:** `shorting=0`, `unc=7`. `R_SCL` was not seated. SW_DBG stays `(90.50, 105.50)`.

## Verdict

**No KEEP.** The diagonal can be moved off pad 6 and 3V3 still reaches the via at `(92.00, 105.20)`, but every such edit raises `shorting_items`. The new short is `GND↔3V3` at C3, which baseline only reports as clearance 0.109 mm and a solder-mask bridge. Full revert. Do not apply VBUS on the dock.

## Copper that hits the switch

| Item | Geometry | vs switch |
|---|---|---|
| 3V3 diagonal | F `(94.90, 101.95)–(92.00, 105.20)` w=0.25 | overlaps pad 6 `(93.45, 104.50)` by 0.123 mm |
| 3V3 vertical | F `(94.90, 101.95)–(94.90, 105.20)` w=0.25 | crosses SWDIO_POGO at y=104.50; 0.725 mm from pad 6 |
| 3V3 horizontal | F `(94.90, 105.20)–(92.00, 105.20)` w=0.25 | overlaps pad 5 `(93.45, 105.50)` |

The L (vertical + horizontal) already ties the via `(94.90, 101.95)` to the via `(92.00, 105.20)`, so the diagonal is redundant. The B.Cu 0.45 runs on x=94.9 and from `(92.00, 105.20)` west were left alone.

## Steps (each reverted)

| Step | Edit | shorting | unc |
|---|---|---|---|
| Diagonal only | `(94.90, 101.95)–(92.00, 105.20)` → `(94.90, 101.95)–(92.00, 101.95)` | 2 | 7 |
| West jog | diagonal to that west stub; vertical moved to x=92.00 from y=101.95 to 105.20; horizontal pulled onto `(92.00, 104.40)–(92.00, 105.20)` | 1 | 7 |

Diagonal-only shorts: `GND↔3V3` at C3 pad 1 `(96.52, 108.80)` vs the GND track `(97.48, 108.80)–(94.50, 107.50)`, and `SWDCLK_POGO↔3V3` at pad 5 vs the horizontal that was left in place.

The west jog clears pad 6 (gap 0.725 mm to the x=92.00 track) and clears pad 5. DRC then has one short, the same C3 pair. A straight slide of that GND track from C3 pad 2 `(97.48, 108.80)` to `(94.50, 107.50)` still overlaps pad 1 or the 3V3 tie at x=96.50. That nudge was not written.

`R_SCL (112.00, 107.45)` rot 270 was not applied. With shorting already 1, seating it cannot meet the gate.

## Nets closed

None.

## DRC

No KEEP. Restored board matches Pass-AL: `shorting=0`, unconnected 7.

## Next

unc=7, shorting=0. Same seven pairs. No VBUS on the dock.
