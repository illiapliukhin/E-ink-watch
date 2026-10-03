# PASS_BE — no larger-pitch drop-in for U2 (2026-10-02)

**Board:** `e-ink-watch.kicad_pcb` unchanged from Pass-BD  
**From / to:** `shorting=0`, `unc=3`. No symbol, footprint, or copper edit.  
**U2:** BQ25120A, `EInkWatch:Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm`  
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** BQ25120A is sold only in YFP, a 25-ball DSBGA at 0.40 mm pitch. Nothing in that family is a WSON, VQFN, or ≥0.50 mm BGA with the same pins. A function-compatible charger that does use 0.50 mm pitch drops the buck that makes `3V3` and the load-switch/LDO that makes `3V3_DISP`. Putting that charger on the existing nets would feed the MCU from the cell. No footprint was written.

Pass-BD already closed SCL and SDA. This pass does not reopen them. Still open: A5 (PGND), PMIC_INT, TS.

## BQ25120A packages

TI orderable addendum (SLUSDA7 packaging page, 9 Jan 2023) lists four rows, all DSBGA (YFP), 25 pins:

| Orderable | Carrier |
|-----------|---------|
| BQ25120AYFPR / .A | 3000, large reel |
| BQ25120AYFPT / .A | 250, small reel |

Datasheet package outline 4225306/A marks the ball grid **0.4 TYP** in both directions. Ball diameter is 0.25–0.30 mm. Body is 2.50 mm × 2.50 mm. There is no second package table.

The same YFP-25 drawing and the same two orderables are all that BQ25121A lists. It is the higher-current sibling, not a larger pitch.

## What the open balls are

| Ball | Net | Where it sits |
|------|-----|----------------|
| A5 | GND (PGND) | Corner, walled by A4 SW and B5 VSYS |
| D2 | PMIC_INT | Interior |
| C3 | TS | Interior |
| E5 | SCL | Corner. Pass-BD already ties this to U1 pad 29 |

A 0.15 mm track needs about 0.45 mm between foreign pad edges. At 0.40 mm pitch the edge gap is 0.17 mm. Pass-BB and Pass-BC measured that. This pass does not jog those balls again.

A1 and D5 are already on GND, so the die has a ground. The datasheet still asks for PGND (A5) on the buck output cap. That is the remaining ground open.

## Nearest parts, and why they are not a swap

### BQ25155 — still 0.40 mm

YFP-20, body 2.00 mm × 1.60 mm. Outline in the datasheet (4222895/A) is **0.4 TYP** both ways, 20 balls of 0.21–0.25 mm. Orderables are YFPR and YFPT only. It has I2C, TS, INT, a power path, and one LDO (150 mA). It has no SW pin and no second rail. The 3.3 V buck and `3V3_DISP` would leave the chip. The pitch does not open an interior ball.

### BQ25180 — eight edge balls, no MCU rail

YBG-8 only (BQ25180YBGR). Body 1.60 mm × 1.10 mm. Pins: IN, SYS, BAT, GND, SCL, SDA, /INT, TS/MR. All eight sit on the outline of a 4 × 2 grid, so none is an interior ball. TI describes it as not needing an HDI board. It has no SW, no PMID, no ISET, no ILIM, no IPRETERM, no /CD, and no LS/LDO. SYS is the power-path output, not the programmable 1.8 V / 3.3 V buck on BQ25120A. The nRF52840 in the MDBT50Q is specified to 3.6 V. A LiPo on SYS reaches 4.2 V. Connecting SYS to the existing `3V3` net is not a footprint change.

### BQ25619 — 0.50 mm, different power tree

BQ25619RTWR, WQFN (RTW), 24 pins, 4.00 mm × 4.00 mm, pitch **0.50 mm**. I2C, TS, INT, JEITA, ship mode, NVDC power path. The buck is the charger, not a 3.3 V system rail. REGN is about 4.7 V at up to 50 mA for gate drive and the TS divider. Pins are on the perimeter, so SCL, INT, TS, and GND can leave the package outward under a 0.15 mm rule. The pad-to-pad gap on a 0.50 mm pitch is still about 0.25 mm, so a track still does not pass between two pins.

Using it as U2 deletes the inductor path (`SW`), the `3V3` buck, and the `3V3_DISP` load switch, and it deletes the meaning of `R_ISET`, `R_ILIM`, `R_IPRETERM`, `R_CD`, and `R_LSCTRL`. The MCU rail needs a second regulator. That is a new power schematic, not a re-fanout of the four opens. It was not placed.

## DRC

No file changed, so the Pass-BD report still stands.

| | Pass-BD (this tree) |
|--|---------------------|
| `shorting_items` | 0 |
| unconnected | 3: A5, PMIC_INT, TS |
| hole clearance actual 0.000 mm vs a zone | 98 |

`R_SCL` stays `(112.04, 107.68)` rot 270. `R_SDA` stays `(111.10, 109.30)`. The Pass-AZ SDA hop, the Pass-BA `3V3_DISP` stitch, and their keepouts stay.

## What a later pass would have to add

A 0.50 mm charger can close SCL, INT, and TS only after the schematic grows a 3.3 V regulator for the MCU and a switch for `3V3_DISP`, and after `SW` / `PMID` / the programming resistors are redrawn. Until that schematic exists, a new footprint on the current nets is the wrong part.
