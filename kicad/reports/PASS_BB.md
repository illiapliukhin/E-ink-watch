# PASS_BB — A5 and a R_SCL micro-move cannot drop unc (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-BA KEEP)  
**From / to:** `shorting=0`, `unc=4`. No copper moved.  
**R_SCL:** `(112.00, 107.45)` rot 270, still on E5 and the 3V3 rail.  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** A5 GND has no 0.15 mm exit on F and no via site on B. A pour cut does not help: the walls are pads and tracks, not zone copper. Every `R_SCL` seat that still covers E5 and stays on 3V3 leaves the same F pocket, area 0.266 mm², 23.85 mm from U1 pad 29. PMIC_INT and TS were not retried. A5 copper did not move, and Pass-BA already showed those two fail with the pours ignored. Nothing was written, so there was no DRC to gate. Unconnected stays 4. `shorting_items` stays 0.

The Pass-AZ SDA hop and the Pass-BA `3V3_DISP` stitch stay, including their keepouts. No new keepout was cut.

## A5 GND

U2 A5 is `(111.80, 105.20)`, pad half-size 0.115 mm. D5, the GND ball that is already tied, is `(111.80, 106.40)`, 1.20 mm north. B5 VSYS sits on that column at `(111.80, 105.60)`.

Pours were ignored. Same-net GND was ignored. A 0.12 mm track (extra 0.21 mm) from the A5 center stays inside a 3-cell pocket, bbox x 111.75–111.90, y 105.10–105.25. Farthest reach is 0.112 mm. D5 is in free F and is not reached. A1 is not in free F. Zero other GND copper is hit.

### F, measured from the ball center

| Direction | Distance | What it hits |
|-----------|----------|--------------|
| 0° | 0.400 mm | `C_VINLS` pad 1 PMID. Footprint `(112.5, 104.5)` rot 90 |
| 15° | 0.700 mm | VSYS via `(112.50, 105.60)` size 0.45 |
| 30–75° | 0.300–0.560 mm | VSYS F `(111.80, 105.60)–(112.50, 105.60)` w=0.25 |
| 90° | 0.280 mm | that same VSYS segment |
| 105° | 0.300 mm | U2 B5 VSYS |
| 120–150° | — | PMID w=0.40 at y=105.60 |
| 165–225° | 0.300–0.420 mm | U2 A4 SW and SW F `(111.40, 105.20)–(111.40, 104.55)` w=0.22 |
| 240–270° | 0.440–0.560 mm | SW via `(111.55, 104.55)` size 0.55 |
| 285° | 0.300 mm | PMID F `(112.00, 104.98)–(112.00, 103.85)` w=0.25 |
| 300–345° | 0.180–0.380 mm | PMID F `(112.00, 104.98)–(112.50, 104.98)` w=0.25 |

The tightest F ray is 315°, 0.180 mm from the center. That point is inside the pad (half-size 0.115 mm), so the centerline never leaves the ball.

Edge gaps, which are what a track actually needs:

- North: A5 north edge y=105.315, VSYS south edge y=105.475, gap **0.160 mm**. A 0.15 mm track needs about 0.30 mm between those edges.
- West: A4–A5 ball pitch leaves **0.17 mm** between pad edges. A5–B5 is the same 0.17 mm.

### B, and the via grid

Every ray from 0° to 345° hits ILIM on B, `(110.30, 105.20)–(114.70, 105.20)` w=0.15, at 0.020 mm from the ball center. The track crosses the pad. A through via in the pad shorts ILIM. ILIM is a track. A keepout cannot remove it.

Ignoring ILIM, the next B copper is SW `(111.55, 104.90)–(115.00, 104.90)` w=0.28, 0.160 mm from the center. A 0.15 mm drill needs its center ≥0.325 mm from foreign copper (drill/2 + 0.25 mm hole clearance). 0.160 mm is below that, so the center of the ball is not a via site even with ILIM gone.

A 0.05 mm grid over x=111.0–113.0 and y=104.2–106.2, requiring both layers to clear a 0.15 mm drill by 0.25 mm and a 0.12 mm dogbone back to `(111.80, 105.20)` at edge ≥0.15 mm, found **0 sites**.

## SCL

`R_SCL` was not moved.

The free component that contains E5 `(111.80, 106.80)` is area **0.266 mm²**, bounds `(111.70, 106.74)–(112.52, 107.36)`, **23.846 mm** from U1 pad 29 `(98.00, 87.25)`.

Seats tried: rotations 0/90/180/270, dx −0.8 to +0.8 mm and dy −0.6 to +0.9 mm on a 0.1 mm grid. Pad 1 had to cover the E5 box `(111.685–111.915, 106.685–106.915)`. Pad 2 had to hit 3V3 copper or sit within 1.2 mm of it. **114** seats pass that. Every one has the same pocket: area 0.266 mm², the same bounds, the same 23.85 mm to U1. None reaches U1.

The walls do not move with the resistor while pad 1 still covers E5. They are the SDA vertical at x=111.40, D5 / GND, the 3V3 via `(112.16, 107.60)`, and `R_SCL` pad 2. Pass-BA already measured the nearest drill-legal via at 1.87 mm from E5. A second hop still has no site.

## PMIC_INT and TS

Not routed. The order was to try them only after A5 copper opened an escape. A5 copper was not written. Pass-BA: PMIC_INT's F stub at D2 `(110.60, 106.40)` and the B run at x=94.20 are different free components with the pours ignored. TS's C3 stub is about 1.23 mm from any 0.15 mm corridor, and the B stub is not a legal via start.

## DRC

No new DRC. The board file matches the Pass-BA KEEP (`f56765f`). That run was 902 violations, 4 unconnected, `shorting_items` absent, hole-clearance actual 0.000 mm count 100, zone-clearance actual 0.000 mm count 190.

Still open: A5 GND, SCL (U1 pad 29 vs U2 E5), PMIC_INT, TS.
