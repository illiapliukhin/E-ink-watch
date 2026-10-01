# PASS_AV — VBUS jog cannot open an I2C lane (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AT KEEP)  
**From / to:** `shorting=0`, `unc=6`. No copper moved.  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** Jogging or even deleting the VBUS copper does not open a 0.15 mm lane from the U2 I2C island to U1. The y=102.90 run is a redundant wall. After it is gone, VBAT and ISET still seal the pocket. Full revert (nothing was written).

## What blocks the straight gap

The Pass-AU line from E5 toward the free copper near U1 crosses:

| Copper | Geometry | Role |
|---|---|---|
| VBUS | F `(108.12, 102.90)–(110.60, 102.90)` w=0.40, plus verticals at x=108.12 and x=110.60 up to y=104.50 / 105.20 | Overlaps that far line by 0.260 mm. Already fat (≥0.40). |
| IPRETERM | Via `(110.05, 106.40)` size 0.50 and via `(109.45, 106.70)` size 0.45 | Overlaps the SDA diagonal approach by 0.279 mm. |
| VBAT | F `(108.12, 105.60)–(110.20, 105.60)` w=0.28 | Crosses the closer gap (distance 0). |
| ISET | F `(108.55, 106.00)–(110.20, 106.00)` w=0.15 | Crosses the same closer gap. |

## If VBUS is removed entirely

Treating every VBUS track and via as absent (better than any jog that must keep the net connected and ≥0.40 mm wide):

| Net | Gap that remains to the U1 free region | Connects? |
|---|---|---|
| SDA from `(110.42, 107.45)` | 2.779 mm, nearest free point `(108.74, 105.23)` | No |
| SCL from `(111.80, 106.80)` | 3.436 mm, same free point | No |

That nearer point is the same free component that holds U1 pads 27 and 29. The 2.779 mm that is left is VBAT at y=105.60 (the line crosses it) and ISET at y=106.00 (clearance 0.017 mm). GND at y=105.15–105.20 sits on the south edge of the same stack. Dropping only the y=102.90 VBUS run, or only the two IPRETERM vias, leaves the original ~5.5 mm gap.

Removing the 3V3 net from the obstacle set does connect SDA in this model, but that is a different wall and it is not a VBUS jog. GND together with VBAT also connects. Neither is a local slide of the y=102.90 run.

## Nets closed

None.

## DRC

No new DRC. Board matches Pass-AT: `shorting_items=0`, unconnected 6.

## Next

unc=6, shorting=0. A VBUS jog at y=102.90 cannot yield a ≥0.15 mm I2C lane while VBAT y=105.60 and ISET y=106.00 stay. No VBUS on the dock.
