# PASS_AX — 3V3 rail jog cannot open an I2C lane (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AT KEEP)
**From / to:** `shorting=0`, `unc=6`. No copper moved.
**R_SCL:** `(112.00, 107.45)` rot 270, still on E5 and the 3V3 rail.
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** Jogging the 3V3 rail cannot open a 0.15 mm lane from SDA or SCL to U1. Deleting that copper is a better obstacle result than any jog that has to put it somewhere else, and deletion still does not connect. Nothing was written.

## What was tested

Free space is a 0.15 mm track (half-width + 0.15 mm) on F.Cu. Pads stay in the obstacle set. Distances are component to component. The U1 pad is on the far component in every row.

| 3V3 copper removed | SDA gap | SCL gap |
|---|---|---|
| None | 4.695 mm, free point `(108.51, 102.23)` | 5.486 mm, free point `(108.68, 102.18)` |
| Rail only, F `(110.16, 108.25)–(112.16, 108.25)` w=0.25 | 4.695 mm (unchanged) | 5.486 mm (unchanged) |
| That rail plus via `(112.16, 107.60)` size 0.60 | 4.695 mm | 5.486 mm |
| Every 3V3 track and via in x 109.5–113.2, y 107.4–109.8 | 0.800 mm, `(104.41, 105.80)` to `(104.41, 105.00)` | 0.800 mm, same points |

The last row is the upper bound. It also takes away the rail under `R_SCL` pad 2, which would unseat the pullup. A jog that keeps the seat cannot do better.

## Remaining seal

The 0.800 mm line is vertical at x=104.41. Copper on it:

| Copper | Geometry |
|---|---|
| VBAT | F `(106.20, 105.40)–(100.00, 105.40)` w=0.35 |
| VSYS | `R_VSYS` pad 1 at `(105.00, 104.62)` |

That VBAT run is fat power. It is not the rail this pass was allowed to move.

`R_SCL` pad 2 is at `(112.00, 107.96)`, y 107.69–108.23. The rail copper starts at y=108.125, so the pad overlaps it. Sliding the whole rail off the pad opens the pullup. Keeping the segment, because the east end is the seat, leaves the original 4.695 mm gap.

A via hop at the 0.800 mm site is not a way around. `(104.41, 105.00)` is 1.225 mm inside the B GND pour and 2.316 mm inside the In2 3V3 pour. A through via there shorts GND and drills the 3V3 plane. SDA copper at `(110.42, 107.45)` is already 0.744 mm inside the B pour.

Deleting every 3V3 track on the board does join both nets in this obstacle model. That is the power distribution, not a jog of the rail, and it breaks 3V3 connectivity. It was not applied.

## Nets closed

None.

## DRC

No new DRC. Board matches Pass-AT: `shorting_items=0`, unconnected 6.

## Next

unc=6, shorting=0. Minimum remaining gap after the best short-free change to this rail is **0.800 mm**, on VBAT w=0.35 at y=105.40. Stop. No VBUS on the dock.
