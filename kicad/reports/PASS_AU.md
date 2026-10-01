# PASS_AU — next island still blocked (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AT KEEP)  
**From / to:** `shorting=0`, `unc=6`. No copper, no footprint move.  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** None of the six open islands has a 0.15 mm path that closes the pair. The Pass-AT seat put `R_SCL` on E5, but that pocket does not reach U1. Full pass left the board as Pass-AT.

## Steps

| Island | What was measured | Result |
|---|---|---|
| 1. SCL → U1 | F escape from E5 `(111.80, 106.80)` and from the pad east side | 0.50 mm, then U2.E4. 5.571 mm of foreign copper remains before the free region that holds U1 pad 29 `(98.00, 87.25)`. Along that gap the worst hit is VBUS F y=102.90, overlap 0.260 mm. |
| 2. SDA → U1 | F escape from the diagonal midpoint `(110.42, 107.45)` | 1.25 mm, then `R_TS` pad 2. Gap to the U1 free region is 5.532 mm. Worst hits: IPRETERM via `(110.05, 106.40)` overlap 0.279 mm, then the same VBUS rail. A 0402 cannot bridge 5.5 mm, so moving `R_SDA` does not close it. |
| 3. PMIC_INT | D2 `(110.60, 106.40)` is an interior ball | Copper gap between 0.23 mm balls on a 0.40 mm pitch is 0.170 mm. A 0.12 mm track needs 0.420 mm. A 0.25 via on the pad clears the neighbor balls by only 0.160 mm (hole clearance about 0.210 mm vs 0.250 mm) and sits 0.025 mm outside the B GND fill, so the via copper enters that pour. |
| 3. TS | C3 stub `(111.00, 106.00)` and B end `(110.40, 105.65)` | Via at the B end overlaps VBAT F by 0.215 mm and ILIM B by 0.100 mm, and that point is inside In2. Via `(111.00, 106.05)` is only +0.078 mm vs PMID F and +0.050 mm vs ILIM B. |
| 4. A5 | Pad `(111.80, 105.20)` | North and east steps overlap PMID. Best earlier edge vs the VSYS via `(112.50, 105.60)` is still about −0.120 mm. The pad is 0.660 mm outside the B fill, with no exit. |
| 4. 3V3_DISP E–W | West F via `(85.00, 102.75)`, east B `(92.00, 87.00)` | West F reaches `(87.81, 101.12)` and stops +0.035 mm from EPD_CS_L y=100.75 (14.73 mm still left). East B reaches `(87.54, 88.62)` and stops +0.079 mm from EPD_RST y=89.00 (14.35 mm still left). The Pass-AI seam was not replayed. |

`R_SCL` stays `(112.00, 107.45)` rot 270. The 3V3 via `(112.16, 107.60)` was not shrunk: Pass-AQ already showed that only opens a pocket about 0.6 mm by 1.0 mm, which is the same pocket the SCL march dies in.

## Nets closed

None.

## DRC

No new DRC. Board matches the Pass-AT report: `shorting_items=0`, unconnected 6.

## Next

unc=6, shorting=0. Same six pairs: A5, east–west `3V3_DISP`, SDA to U1, SCL to U1, PMIC_INT, TS. Closing SCL or SDA needs a path through the VBUS / IPRETERM wall, not another local jog at E5. No VBUS on the dock.
