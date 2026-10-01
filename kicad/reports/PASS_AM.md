# PASS_AM — larger R_SDA / R_SCL placement (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` (Pass-AL KEEP)  
**From / to:** `shorting=0`, `unc=7`. No footprint moved. No copper added.  
**Tool:** KiCad 9.0.9 DRC for the baseline. Placement checked at 0.15 mm pad and track clearance.

## Verdict

**No KEEP.** Unconnected stays 7. Shorting stays 0. Moving `R_SDA` off x=111.4 would open a measured SCL corridor, but no new site for that part has both pad clearance ≥ 0.15 mm and a retie back to U2.E4 and to 3V3. The vertical stays. Do not apply VBUS on the dock.

## Baseline

KiCad 9.0.9 DRC: `shorting_items=0`, `unconnected_items=7`, power pairs empty, pocket pairs empty.

Still open: GND A5, east–west `3V3_DISP`, SDA vs U1.27, SCL `R_SCL` vs the E5 stub, SCL E5 vs U1.29, PMIC_INT, TS.

## Placement (before = after)

| Ref | x, y, rot |
|-----|-----------|
| R_SDA | 111.5, 109.0, 0 |
| R_SCL | 106.5, 110.1, 90 |
| R_CD | 113.5, 107.75, 90 |
| C_LDO | 113.5, 106.8, 90 |
| U2 | 111, 106, 0 |

`R_SDA` pad1 is `(110.99, 109.00)` SDA, pad2 `(112.01, 109.00)` 3V3. The wall is the F.Cu vertical `(111.400, 109.000)–(111.400, 106.800)` w=0.15.

## What opens if that vertical is deleted

With the four `R_SDA` ties ignored and the part's pads ignored, this SCL stitch clears 0.15 mm and stays outside the In2 3V3 fill (r ≈ 13.5 and 14.4 from `(100, 100)`):

- Via 0.25 at `(111.35, 107.30)` on the E5 stub. Worst edge `+0.165` vs the CD B.Cu run. The existing vertical makes this via illegal; that is why the part has to move.
- B.Cu w=0.12 `(111.35, 107.30)–(111.35, 108.80)`, edge `+0.200` vs BTN3 at y=109.15.
- Via 0.25 at `(111.35, 108.80)`, edge `+0.300` vs the 3V3 rail y=108.25.
- F.Cu w=0.15 `(111.35, 108.80)–(111.35, 110.50)`, edge `+0.300`.

The F run stops 2 mm short of the current `R_SCL` pad. BTN1 via `(107.50, 110.50)` blocks the last hop to `(106.50, 110.61)`.

`R_SCL` can meet that run. One clear site is center `(109.20, 110.60)` rot 180: SCL pad `(109.71, 110.60)` edge `+0.63`, 3V3 pad `(108.69, 110.60)` edge `+0.57`. F.Cu from `(111.35, 110.50)` to the SCL pad is edge `+0.547`. A 3V3 drop `(108.69, 110.60)–(108.69, 109.59)` onto the existing rail is edge `+0.630`. Not applied, because the stitch still needs the wall gone. The courtyard would also overlap SW1.

126 `R_SCL` centers in that band have both pads ≥ 0.15 mm. None of them removes the wall.

## Why R_SDA did not move

Pad-clear sites exist (649 on a 0.4 mm grid inside r≈18.5, outside the SCL lane). A legal retie does not.

- On the existing SDA diagonal, the best pad edge is `+0.090` (CD via `(110.60, 106.95)` / LSCTRL via `(110.80, 107.80)` / NTC_BAT). Below 0.15 mm.
- East of the wall, `(112.2, 109.2)` rot 90 has pads ≥ `+0.25` and a 3V3 tie `(112.20, 108.69)–(112.20, 108.25)–(112.50, 108.25)` at `+0.150`. The SDA return to E4 `(111.40, 106.80)` hits the 3V3 via `(112.16, 107.60)` by `−0.335`. There is no 0.15 mm gap between that via and the SCL lane at x=111.35.
- Further east, a bypass at x≈114.4 hits the 3V3 via `(114.30, 107.95)` by `−0.275`, then `R_CD` pad 2. x≈115 hits SW3 pad 1. B.Cu cannot cross BTN3 at y=109.15 (x=103.6–115.7).
- U2 was not translated or rotated. The previous ±0.2–0.4 mm shifts still land SDA on 3V3, and an in-place rotate still overlaps the dogbones.

`R_CD` and `C_LDO` were not spread. Their bodies are not the east-lane blocker; the 3V3 vias `(112.16, 107.60)` and `(114.30, 107.95)` stay if only the 0402s move.

## Next

unc=7, shorting=0. The SCL hop above is the next copper KEEP after a retie that actually removes x=111.4. That retie needs the 3V3 via `(112.16, 107.60)` moved, or another layer hop that does not cross BTN3. A5, `3V3_DISP`, SDA to U1, SCL to U1, PMIC_INT, and TS stay open. No VBUS on the dock.
