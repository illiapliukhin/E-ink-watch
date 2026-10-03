# PASS_AZ — pour keepouts and an SDA layer hop (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AT / Pass-AY (`shorting=0`, `unc=6`, `R_SCL` at `(112, 107.45)` rot 270)  
**To:** Pass-AZ (`shorting=0`, `unc=5`)  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc`. Local edits of the stored `filled_polygon`s. No zone refill.

## Verdict

**KEEP.** SDA now reaches U1 pad 27. Unconnected 6→5. `shorting_items=0`. The VBAT bar stays `(100.00, 105.40)–(106.20, 105.40)` width 0.35. `R_SCL` stays seated. `SW_DBG` stays `(90.50, 105.50)` default OFF. No VBUS was added on the dock.

SCL is still open (U1 pad 29 vs the E5 stub). The seat on `R_SCL` is the remaining SCL wall. Closing it would unseat the pullup.

## Why the hop can leave the VBAT bar in place

With the 3V3 knot slid off x=110.2–110.6, `(103.25, 105.90)` is in the SDA free component and `(103.25, 104.85)` is in the U1 free component. The bar copper is y=105.225–105.575. The south via copper ends at y=105.775 (gap 0.200 mm). The north via copper starts at y=104.975 (gap 0.250 mm). Both are ≥0.15 mm, so the bar does not have to break and does not have to be retied.

A straight F run at x=103.25 cannot do this. It would have to cross the bar. The hop is on B between the two vias.

## Keepouts

Every cut is a hole in the stored fill. `(100, 100)` stays inside each pour. Existing pad-clearance holes stay empty. No F.Cu zone was cut. There is no F pour on this board.

Drill-to-copper after the cuts, measured on the written rings:

| Via | Drill gap B GND | In1 GND | In2 3V3 | Rule |
|-----|-----------------|---------|---------|------|
| SDA `(103.25, 105.90)` 0.25/0.15 | 0.424 mm | 0.424 mm | 0.423 mm | 0.250 mm |
| SDA `(103.25, 104.85)` 0.25/0.15 | 0.424 mm | 0.424 mm | 0.423 mm | 0.250 mm |
| 3V3 `(106.40, 108.55)` 0.25/0.15 | 0.375 mm | 0.375 mm | already  outside | 0.250 mm |
| 3V3 `(111.80, 108.25)` 0.25/0.15 | 0.450 mm | 0.375 mm | already outside | 0.250 mm |

### B.Cu GND — zone `f8a49630-cf63-4392-a480-09453f05d13c`

1. **Stadium**, centerline `(103.25, 104.85)–(103.25, 105.90)`, radius **0.50 mm** (shapely buffer, 12 steps per quadrant, written into the fractured ring).  
   **Reason:** the SDA B track width 0.15 and both through-vias sit inside the pour (south via was 2.125 mm deep, north via 1.075 mm deep). Two separate circles leave a 0.05 mm neck of GND on the track. The stadium removes that neck. Copper clearance from the 0.15 track to the remaining pour is about 0.42 mm.

2. **Circle**, center `(106.40, 108.55)`, radius **0.45 mm**.  
   **Reason:** the west 3V3 via moved onto the existing B run. Without the circle the drill is inside B GND.

3. **Circle**, center `(111.80, 108.25)`, radius **0.45 mm**.  
   **Reason:** the east 3V3 via moved onto the shortened rail. Same drill clearance.

### In1.Cu GND — zone `03ba8da5-3329-4248-8d94-a8b4b9831a74`

4. **Circle**, center `(103.25, 105.90)`, radius **0.50 mm**.  
5. **Circle**, center `(103.25, 104.85)`, radius **0.50 mm**.  
   **Reason:** a through via drills In1 even though the B track does not. The track-only stadium is not required here.

6. **Circle**, center `(106.40, 108.55)`, radius **0.45 mm**.  
7. **Circle**, center `(111.80, 108.25)`, radius **0.45 mm**.  
   **Reason:** the two relocated 3V3 vias drill In1.

### In2.Cu 3V3 — zone `885d0b4b-000f-4931-8d0a-8ec2b4bc5458`

8. **Circle**, center `(103.25, 105.90)`, radius **0.50 mm**, 32 points, clockwise. Spliced into the original ring on a 1.394 mm bridge from `(101.943, 104.529)`.  
9. **Circle**, center `(103.25, 104.85)`, radius **0.50 mm**, 32 points, clockwise. Spliced on a 1.884 mm bridge from `(103.193, 102.466)`.  
   **Reason:** the SDA vias drill the 3V3 plane. Rebuilding the whole In2 ring from a geometry library moves about 0.05 mm² even with no cutter, so these two holes were inserted into the original point list. The bridges attach only to vertices that were already in that list, so they do not pinch the first hole. The 3V3 vias at `(106.40, 108.55)` and `(111.80, 108.25)` are already outside this pour (about 1 mm), so In2 was not cut there.

## Copper

`R_SCL`, `R_SDA`, U1, U2, `SW_DBG`, and C3 did not move.

3V3 knot, in place, so both ends still reach the existing B run `(110.40, 108.55)–(102.52, 108.55)`:

- F rail `(110.16, 108.25)–(112.16, 108.25)` w=0.25 becomes `(111.80, 108.25)–(112.16, 108.25)`. The west cap clears the SDA vertical at x=111.40 by 0.200 mm and still overlaps `R_SCL` pad 2.
- West horiz ends at `(106.40, 109.59)`. Vertical `(106.40, 109.59)–(106.40, 108.55)` w=0.12. New via `(106.40, 108.55)` 0.25/0.15. The spur and the old y=108.25 tie are parked on that vertical so they leave the SDA corridor. x=109.90 is not usable: GND F `(108.71, 108.60)–(109.90, 108.60)` w=0.25 ends on a zero-length GND dot `(109.90, 108.60)` w=0.45.
- East via `(110.40, 108.25)` moves to `(111.80, 108.25)`. B drop `(111.80, 108.25)–(111.80, 108.55)` plus `(111.80, 108.55)–(110.40, 108.55)` w=0.12 joins the old run.

SDA, width 0.15, net 27:

- F `(110.42, 107.45)` on the existing diagonal, then `(110.25, 108.00)`, `(110.50, 109.25)`, `(108.25, 113.00)`, `(106.00, 113.25)`, `(105.00, 112.25)`, `(103.50, 106.25)`, `(103.25, 106.00)`, `(103.25, 105.90)`.
- Via `(103.25, 105.90)` 0.25/0.15.
- B `(103.25, 105.90)–(103.25, 104.85)`.
- Via `(103.25, 104.85)` 0.25/0.15.
- F `(103.25, 104.85)`, `(103.25, 104.75)`, `(102.965, 102.785)`, `(102.215, 102.035)`, `(102.75, 91.75)`, `(99.75, 88.75)`, `(98.80, 87.25)` on U1 pad 27.

Tightest F edge gaps in the circle-pad model are 0.152 mm (SW1.1, the pad is 0.9×1.7 so the real rectangle is looser) and 0.154 mm (FB1.1). Real via clearances on the route are 0.161 mm and up. VBAT gaps are 0.200 mm and 0.250 mm.

## DRC

`shorting_items=0`. `unconnected_items=5` (was 6). SDA is gone from the list. Still open: A5 GND, east–west `3V3_DISP`, SCL, PMIC_INT, TS.

Hole-clearance actual 0.000 mm vs a zone: 102 → 100. Zone-clearance actual 0.000 mm: 192 → 190. The old via `(110.40, 108.25)` was one of those overlaps; the notches remove it and the new vias do not add one. The new vias are annular width 0.050 mm, drill 0.150 mm, diameter 0.250 mm, same class as the existing D5 via. Not a short.

Power-pair shorts stay empty because `shorting_items` is empty. PMID via `(111.35, 103.85)` is still the insert anchor.
