# PASS_AR — SW_DBG / pogo move reverted (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AL KEEP)  
**From / to:** `shorting=0`, `unc=7`. `R_SCL` was not seated. No footprint kept.

## Verdict

**No KEEP.** The Pass-AP/AQ short is SW_DBG pad 6 sitting on the 3V3 diagonal, not a pogo-pad hit. Moving the rear pogo does not move that pad. Every SW_DBG translation and 90° rotation that keeps the six signal pads ≥0.15 mm from foreign copper either misses, or lands the slide body on U1. Full revert. Do not apply VBUS on the dock. Do not seat `R_SCL` on E5 until this pad is actually clear.

## Why the short is at the switch

`SW_DBG` stays `(90.50, 105.50)` rot 0. Pad 6 `SWDIO_POGO` is `(93.45, 104.50)`, size 1.2×0.5 mm. The 3V3 F.Cu diagonal `(94.90, 101.95)–(92.00, 105.20)` width 0.25 mm overlaps that pad by **0.123 mm**. Baseline DRC files this as a solder-mask bridge, not `shorting_items`. Seating `R_SCL` on E5 (Pass-AP/AQ) is what promotes the same pair to `shorting_items=1` (`SWDIO_POGO↔3V3`).

A second, separate overlap is the SWDIO_POGO track at y=104.50 crossing the 3V3 vertical at x=94.90. Baseline DRC calls that `tracks_crossing`. It is not the item Pass-AP/AQ reported.

## Coords (unchanged)

| Ref | Coord | Net |
|---|---|---|
| SW_DBG | `(90.50, 105.50)` rot 0 | slide, default OFF (SWDIO/SWDCLK/nRESET not tied to the pogo nets) |
| J_SWD | `(84.00, 108.00)` rot 90 | 1×5 header on y=108: 3V3, SWDIO, SWDCLK, nRESET, GND |
| TP1 | `(93.00, 114.00)` B | VBUS_POGO |
| TP2 | `(96.00, 114.00)` B | GND |
| TP3 | `(99.00, 114.00)` B | SWDIO_POGO |
| TP4 | `(93.00, 111.00)` B | SWDCLK_POGO |
| TP5 | `(96.00, 111.00)` B | nRESET_POGO |
| TP6 | `(108.50, 111.00)` B | OPT |

No case opening moves. The rear 2×3 pogo pitch stays 3.0 mm.

## Search

Pads of SW_DBG (six signals plus four anchors) were tested on a 0.25 mm grid, rotations 0/90/180/270, about ±6–10 mm from the current center. Obstacles were other F.Cu pads (including J_SWD through-holes), foreign tracks and vias, and the 3V3 diagonal. Local SWD/pogo fanout inside 8 mm was ignored, because that copper would be retied.

- Nearby shifts, including rot 90, do not clear pad 6 from the diagonal without hitting the 3V3 horizontal y=105.20, the J_SWD pins, or the outline.
- The only pad-clear pocket is `(95.00–95.25, 98.50–99.00)` rot 0 or 180, minimum gap 0.16–0.25 mm. That courtyard sits on U1 `MDBT50Q` (center `(100.00, 93.50)` rot 180, fab ±5.25 × ±7.75 mm, so the body reaches x=94.75 and y=101.25). Not placed.
- Moving TP1–TP6 does not move pad 6, so it cannot clear this pair.

`R_SCL (112.00, 107.45)` rot 270 was not applied. The known result of that seat, with the switch left where it is, is unc 6 and `shorting_items=1`.

## Nets closed

None.

## DRC

No new DRC. Board file matches Pass-AL: `shorting=0`, unconnected 7.

## Next

unc=7, shorting=0. Same seven pairs. No VBUS on the dock.
