# PASS_AW — VBAT/ISET jog cannot open an I2C lane (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AT KEEP)  
**From / to:** `shorting=0`, `unc=6`. No copper moved.  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** The best short-free change to VBAT and ISET is to take them out of the obstacle set entirely. That still does not join SDA or SCL to the free copper around U1. Minimum remaining gap is **1.207 mm** on SDA, sealed by the 3V3 rail. A real jog cannot do better than deletion, and a jog would also have to keep VBAT connected at about 0.28 mm or wider. Nothing was written.

## What was tested

| Obstacles removed | SDA gap to U1 pad 27 | SCL gap to U1 pad 29 |
|---|---|---|
| None | 5.554 mm, free point `(108.68, 102.18)` | 5.578 mm, same point |
| VBAT | 1.207 mm, free point `(110.78, 108.60)` | 2.181 mm, free point `(112.83, 108.72)` |
| ISET only | 5.554 mm (unchanged) | 5.578 mm (unchanged) |
| VBAT + ISET | 1.207 mm | 2.181 mm |
| VBAT + ISET + IPRETERM | 1.207 mm | 2.181 mm |

Both free points are on the component that contains the U1 pad. VBAT is the useful deletion. ISET and the IPRETERM vias do not move the gap.

## Remaining seal

SDA copper sits near `(110.42, 107.45)`, north of the rail. The opened free point `(110.78, 108.60)` is south of it. Between them:

| Copper | Geometry | On the 1.207 mm line |
|---|---|---|
| 3V3 rail | F `(110.16, 108.25)–(112.16, 108.25)` w=0.25 | crosses (distance 0) |
| 3V3 | F `(110.46, 108.10)–(110.16, 108.25)` w=0.25 | 0.159 mm |
| 3V3 via | `(110.40, 108.25)` size 0.25 | 0.261 mm |

SCL’s 2.181 mm remainder hits the 3V3 via `(112.16, 107.60)` size 0.60 (distance 0.058 mm) and the F tie `(112.51, 107.80)–(112.16, 107.80)` w=0.20, which the line crosses.

The VBAT segment that Pass-AV named, F `(108.12, 105.60)–(110.20, 105.60)` w=0.28, is south of this new entrance. Removing it reveals the entrance. It does not remove the 3V3 rail. ISET F `(108.55, 106.00)–(110.20, 106.00)` w=0.15 is not on the remaining gap.

## Nets closed

None.

## DRC

No new DRC. Board matches Pass-AT: `shorting_items=0`, unconnected 6.

## Next

unc=6, shorting=0. After the best VBAT/ISET removal, SDA is still 1.207 mm short and SCL is still 2.181 mm short, both on 3V3 copper. No VBUS on the dock.
