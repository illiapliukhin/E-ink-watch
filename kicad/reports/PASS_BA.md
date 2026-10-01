# PASS_BA — east–west 3V3_DISP stitch (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AZ (`shorting=0`, `unc=5`, SDA on U1 pad 27, `R_SCL` at `(112, 107.45)` rot 270)  
**To:** Pass-BA (`shorting=0`, `unc=4`)  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc`. Local edits of the stored `filled_polygon`s. No zone refill.

## Verdict

**KEEP.** East and west `3V3_DISP` are one net. Unconnected 5→4. `shorting_items=0`. The Pass-AZ SDA hop and its keepouts stay. `R_SCL` stays at `(112.00, 107.45)` rot 270. `SW_DBG` stays `(90.50, 105.50)` default OFF. No VBUS was added on the dock.

SCL, PMIC_INT, TS, and A5 GND are still open. SCL was tried first. It does not have a 0.15 mm exit from the `R_SCL` seat, so the first route that clears is this `3V3_DISP` stitch.

## Why SCL, PMIC_INT, TS, and A5 stayed open

SCL's free pocket on F is 0.26 mm², bounds `(111.70, 106.74)–(112.52, 107.35)`. It has no via site: the nearest point that clears a 0.25/0.15 drill by 0.25 mm is 1.87 mm away. The west wall is the SDA vertical at x=111.40 (edge gap to the SCL pad is 0.205 mm; a 0.15 mm track needs about 0.30 mm between those edges). The south wall is `R_SCL` pad 2. Deleting the 3V3 via `(112.16, 107.60)` only pushes the pocket to y=107.475. Sliding the SDA vertical to x=110.95 grows the pocket to y=108.72 and still leaves no via site, because CD on B at y=106.95 and 3V3 on B at y=108.55 fill that band. Shifting `R_SCL` does not open E5: the ball stays between SDA, D5, and the via.

PMIC_INT's F stub at D2 `(110.60, 106.40)` and the B run at x=94.20 are different free components even when the pours are ignored. TS's C3 stub `(111.00, 106.12)` is 1.23 mm from any 0.15 mm track corridor. A5 `(111.80, 105.20)` is 0.91 mm from free F copper; B5 VSYS sits on `(111.80, 105.60)` between A5 and D5.

## Route

Width 0.28 mm, net `3V3_DISP`. Four vias, 0.45 / 0.20, layers F.Cu–B.Cu. This is the same via class already used on this net at `(113.00, 106.00)`. It is not the Pass-AI west rim: nothing here goes west of x=85.

- F `(85.00, 102.75)` on the existing west via → `(88.60, 101.25)`.
- Via `(88.60, 101.25)`.
- B `(88.60, 101.25)` → `(91.90, 102.05)` → `(92.20, 101.55)` → `(92.20, 96.75)`.
- Via `(92.20, 96.75)`.
- F `(92.20, 96.75)` → `(90.70, 92.25)`. This is the hop across EPD_SCK, which is on B at y=94.5.
- Via `(90.70, 92.25)`.
- B `(90.70, 92.25)` → `(88.60, 90.15)` → `(89.20, 89.55)`.
- Via `(89.20, 89.55)`.
- F `(89.20, 89.55)` → `(91.00, 87.40)` → `(92.00, 87.00)` on the existing east via.

Tightest edge gaps: F 0.250 mm, B 0.190 mm, via annulus 0.165 mm at `(88.60, 101.25)` against the F track at x=89.08. All are ≥0.15 mm. Hole clearance to foreign copper is ≥0.290 mm.

## Keepouts

Every cut is a hole or a boundary bite in the stored fill. `(100, 100)` stays inside each pour. The SDA vias `(103.25, 105.90)` and `(103.25, 104.85)` stay outside. No F.Cu zone was cut. There is no F pour.

Drill-to-copper after the cuts, measured on the written rings. A 0.45/0.20 via needs 0.250 mm from the drill edge, so the center must sit ≥0.350 mm outside the fill.

| Via | B GND | In1 GND | In2 3V3 |
|-----|-------|---------|---------|
| `(88.60, 101.25)` | 0.499 mm | 0.499 mm | 0.498 mm |
| `(92.20, 96.75)` | 0.499 mm | 0.499 mm | 0.498 mm |
| `(90.70, 92.25)` | 0.499 mm | 0.499 mm | 0.499 mm |
| `(89.20, 89.55)` | 0.499 mm | 0.499 mm | already 3.034 mm outside |

### B.Cu GND — zone `f8a49630-cf63-4392-a480-09453f05d13c`

1. **Stadium**, radius **0.50 mm**, centerline `(88.60, 101.25)–(91.90, 102.05)–(92.20, 101.55)–(92.20, 96.75)`.  
2. **Stadium**, radius **0.50 mm**, centerline `(90.70, 92.25)–(88.60, 90.15)–(89.20, 89.55)`.  
   **Reason:** the B tracks are width 0.28 and the four through-vias sit inside the pour (depths before the cut were 1.411, 0.499, 0.209, and 1.709 mm). The stadium removes the GND neck a pair of circles would leave on the track. Written by fracturing the differenced ring. The fracture drops an extra 0.077 mm² of pour, as two slivers near `(105.97, 103.22)` and `(102.98, 103.81)`. That is removed copper, not a filled hole. Area 991.59 → about 977.6.

### In1.Cu GND — zone `03ba8da5-3329-4248-8d94-a8b4b9831a74`

3. **Circle** `(88.60, 101.25)` r=0.50.  
4. **Circle** `(92.20, 96.75)` r=0.50.  
5. **Circle** `(90.70, 92.25)` r=0.50.  
6. **Circle** `(89.20, 89.55)` r=0.50.  
   **Reason:** a through via drills In1. The B track does not. Fracture round-trip of this cut is symmetric-difference 0.000 mm². Area drop 3.14 mm².

### In2.Cu 3V3 — zone `885d0b4b-000f-4931-8d0a-8ec2b4bc5458`

7. **Circle** `(88.60, 101.25)` r=0.50, 32 points, clockwise. Spliced on a **0.053 mm** bridge to the original outline vertex near `(88.058, 101.174)`.  
8. **Circle** `(92.20, 96.75)` r=0.50, 32 points, clockwise. Spliced on a **0.072 mm** bridge to the original outline near `(91.666, 96.557)`.  
   **Reason:** both vias are about 0.50 mm inside the 3V3 plane. A long slit (the first automatic bridge was 6.38 mm) pinches the pour. The short bridge to the nearby outline does not: each circle drops 0.78 mm², which is the disk.  
9. **Boundary bite**, center `(90.70, 92.25)`, radius **0.50 mm**.  
   **Reason:** the center is 0.110 mm outside the pour, so a 0.20 mm drill would clear the copper by about 0.010 mm. The bite pulls the outline off the drill. Symmetric difference of this step is 0.000 mm². The via `(89.20, 89.55)` is already 3.034 mm outside, so In2 was not cut there.

In2 area 420.65 → 418.68.

## DRC

`shorting_items=0`. `unconnected_items=4` (was 5). `3V3_DISP` is gone from the list. Still open: A5 GND, SCL (U1 pad 29 vs U2 E5), PMIC_INT, TS.

Hole-clearance actual 0.000 mm vs a zone stays 100. Zone-clearance actual 0.000 mm stays 190. The new vias are annular width 0.125 mm, drill 0.200 mm, diameter 0.450 mm, the same class as the existing `3V3_DISP` via at `(113.00, 106.00)`. Not a short.

Power-pair shorts stay empty because `shorting_items` is empty. PMID via `(111.35, 103.85)` is still the insert anchor. `R_SCL` and `SW_DBG` did not move.
