# PASS_AT — C3 clearance, 3V3 jog, R_SCL on E5 (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` kept  
**From / to:** `shorting=0`, `unc=7` → `shorting=0`, `unc=6`  
**SW_DBG:** stays `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**KEEP.** The C3 GND track now clears pad 1 by 0.530 mm, the 3V3 run at x=92.00 clears SW_DBG pads 5 and 6 by 0.725 mm, and `R_SCL (112.00, 107.45)` rot 270 covers E5 and the 3V3 rail. DRC `shorting_items=0`, unconnected 6. Helpers (3V3 via shrink, D5 GND slide) were not needed.

## Steps

| Step | Edit | shorting | unc |
|---|---|---|---|
| 1. C3 jog | GND stub extended to `(97.48, 110.55)`; new F w=0.25 to via `(96.95, 112.90)` 0.6/0.3; old diagonal `(97.48, 108.80)–(94.50, 107.50)` removed; nRESET y=111 detoured south to y=113.50 | 1 (pad 6 only) | 7 |
| 2–3. 3V3 west jog | diagonal → `(94.90, 101.95)–(92.00, 101.95)`; vertical → `(92.00, 101.95)–(92.00, 105.20)`; horizontal pulled to `(92.00, 104.40)–(92.00, 105.20)` | 0 | 7 |
| 4. Seat | `R_SCL (112.00, 107.45)` rot 270 | 0 | 6 |

Step 1 alone promotes the existing pad-6 overlap into `shorting_items` (`SWDIO_POGO↔3V3`). C3 itself is not in that list. The west jog removes the overlap, so the two edits are kept together. A straight slide of the old GND diagonal cannot clear pad 1: the 3V3 tie at x=96.50 and the south diagonal share `(96.50, 107.75)`, and SWDCLK at x=95.60 blocks the only F.Cu gap south of the stub. The new via is outside the In2 fill (boundary distance 1.269 mm) and inside the B GND pour (1.170 mm), so it stitches without a zone refill. A via on the stub at y≤111 would drill In2.

## Clearances

| Pair | Gap |
|---|---|
| C3 pad 1 east edge x=96.80 vs GND stub x=97.48 w=0.30 | 0.530 mm |
| SW_DBG pad 6 west edge x=92.85 vs 3V3 x=92.00 w=0.25 | 0.725 mm |
| SW_DBG pad 5 west edge x=92.85 vs the same x=92.00 track | 0.725 mm |
| Anchor pad `(92.65, 103.50)` vs that track | 0.175 mm |
| 3V3 tie `(96.50, 107.75)–(96.50, 108.80)` w=0.45 | unchanged |

## Footprints

| Ref | Before | After |
|---|---|---|
| R_SCL | `(106.50, 110.10)` rot 90 | `(112.00, 107.45)` rot 270 |
| SW_DBG | `(90.50, 105.50)` rot 0 | unchanged |

Pad 1 of `R_SCL` covers E5 `(111.80, 106.80)`. Pad 2 overlaps the 3V3 rail y=108.25. The 3V3 via `(112.16, 107.60)` was left at 0.6/0.3.

## Nets closed

SCL: `R_SCL` pad 1 joined the E5 stub `(111.80, 106.80)–(111.14, 107.60)`. The remaining SCL pair is that stub versus U1 pad 29.

## DRC

`reports/_drc_passat_rscl.txt` (gitignored): `shorting_items=0`, `unconnected_items=6`. Power pairs and the PMID pocket are not in the shorting list.

## Next

unc=6, shorting=0. Still open: A5, east–west `3V3_DISP`, SDA to U1, SCL to U1, PMIC_INT, TS. No VBUS on the dock.
