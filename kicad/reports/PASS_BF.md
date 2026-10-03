# Pass-BF — BQ25619 WQFN-24 + 3.3 V LDO + display switch

From Pass-BE (shorting 0, unc 3). The YFP BQ25120A stays in the library as a historical symbol. U2 on the board and in `power.kicad_sch` is now the charger below. This pass does not merge.

## Parts

| Ref | Part | Package | Role |
| --- | --- | --- | --- |
| U2 | BQ25619RTWR | WQFN-24 4×4 mm, 0.50 mm, EP 2.6×2.6 | NVDC charger from VBUS. Buck is SYS, not the MCU rail. |
| U3 | MCP1700T-3302E/TT | SOT-23 | Always-on 3.3 V, 250 mA. Pin 1 GND, pin 2 VOUT, pin 3 VIN. Operating Vin 2.3–6.0 V. VIN is SYS. |
| Q1 | DMG2305UX | SOT-23 | P-MOS. Pin 1 gate `DISP_EN`, pin 2 source `3V3`, pin 3 drain `3V3_DISP`. |

SOT-23-5 (TLV75533) was drawn first and then dropped. Its courtyard does not fit beside the WQFN on this Ø40 outline without sitting on existing F.Cu. MCP1700 is always on, so there is no EN pin. SYS at a full charge (~4.2–4.5 V) is inside the 6.0 V operating range. REGN (~4.6–4.8 V, only present on VBUS, ≤50 mA) is not the LDO input and is not the MCU rail. nRF52840 / MDBT50Q VDD absolute max is 3.6 V.

Display gate: `R_LSCTRL` is 100 kΩ from `DISP_EN` to `3V3`, so the P-MOS stays off until firmware drives the gate low. `DISP_EN` is not assigned to a module pad on this pass; an unrouted pad assignment would add another open.

## Pin map, YFP BQ25120A → RTW BQ25619

| Was | BQ25619 pin | Net now |
| --- | --- | --- |
| A2 VBUS | 1 VAC and 24 VBUS | VBUS |
| — | 2 PSEL | PSEL, 10 kΩ to REGN (500 mA input cap; I2C can raise IINDPM) |
| — | 3 PMID_GOOD, 4 STAT | no net (open-drain; pull-ups not fitted) |
| E5 SCL | 5 SCL | SCL |
| E4 SDA | 6 SDA | SDA |
| D2 INT | 7 INT | PMIC_INT |
| E1 / D3 / D4 NC | 8 NC | no net |
| — | 9 /CE | GND (charge enabled) |
| B1 B2 VBAT | 10 BATSNS, 12 /QON, 13 BAT, 14 BAT | VBAT |
| C3 TS | 11 TS | TS. Divider is REGN–TS–GND (103AT on `NTC_BAT`) |
| A3 / B3 / B4 / C4 PMID | 23 PMID | PMID |
| B5 VSYS | 15 SYS, 16 SYS | VSYS. Inductor `L_SYS` still SW–SYS |
| A1 / A5 / D5 GND | 17 GND, 18 GND, 25 EP | GND |
| A4 SW | 19 SW, 20 SW | SW |
| — | 21 BTST | BTST, 47 nF `C_BTST` to SW |
| — | 22 REGN | REGN. `R_VSYS` retasked as the 4.7 µF REGN–GND decouple |
| C5 LS/LDO `3V3_DISP` | none | Q1 drain |
| C1 ISET, C2 ILIM, D1 IPRETERM, E2 CD, E3 LSCTRL | none | resistors left on the old nets; charger no longer uses them |

`R_VSYS` was the only VSYS–3V3 bridge. It is no longer that bridge. The MCU rail is the LDO output.

## Placement

KiCad keeps `(size sx sy)` in world axes. Footprint rotation moves the pad center and does not turn the rectangle. Pad angle does. A scratch board of the official QFN-24 at rotation 270, pad angle 0, shorts pad 1 to pad 2. The same footprint at rotation 0 does not. Rotation 180 with pad angle 0 is also clean. U2 is rotation 0. Q1 is rotation 90 and every pad angle is 90.

U2 could not stay at `(111, 106)`: the 5.2 mm courtyard overlaps `J_STRAP_R`. The old power island at `(107.25, 105.5)` has dozens of F.Cu tracks through the EP. The quiet seat is `(111.00, 91.00)`, east of the module and north of the right FPC, with no F.Cu or via copper on the pads.

| Ref | At | Rot |
| --- | --- | --- |
| U2 | 111.00, 91.00 | 0 |
| U3 | 108.00, 85.75 | 0 |
| Q1 | 88.50, 92.50 | 90 |
| C_BTST | 111.25, 87.50 | 0 |
| L_SYS | 114.75, 91.50 | 90 |
| R_VSYS | 106.75, 93.00 | 90 |
| R_TS | 112.50, 94.25 | 0 |
| NTC_BAT | 114.50, 94.25 | 0 |
| R_ISET | 110.50, 86.00 | 90 |
| R_LSCTRL | 116.25, 93.75 | 90 |

Outward 0.20 mm stubs leave the 0.50 mm pin field (along-row gap is 0.25 mm, so a track cannot pass between pins). Same-net neighbors on the east and north are tied outside the body. Pin 9 (/CE, GND) runs inward to the EP. No new vias: a through via in the stored B GND or In2 3V3 fill is a hole-clearance actual 0.000 even when `shorting_items` stays 0. No track was deleted. `SW_DBG` is still `(90.50, 105.50)`. Nothing puts VBUS on the dock. Existing fat power was not narrowed.

## DRC (KiCad 9.0.9, `--severity-error`)

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Before (Pass-BE board) | 916 | 3 | 0 | 98 |
| After this placement | 865 | 30 | 0 | 98 |

The header total is not the gate. `shorting_items` is 0. The 98 hole-to-zone zeros are the same set as Pass-BE.

A second router then drew 18 more F.Cu segments. DRC went to shorting 1, unc 28: U1 pad 15 GND at `(104.80, 86.35)` against the existing 3V3 track `(97.6, 86.35)–(106.0, 86.35)`, width 0.25. That track is on the Pass-BE board and was not `shorting_items` until the new segments were inserted. Those segments were reverted. The numbers in the table are the board that was kept.

## What is still open (unc 30)

The old three opens (YFP A5, the interior INT ball, the interior TS ball) are gone as balls. The nets are not finished, and the new pads add islands:

- `3V3`: U3 VOUT, Q1 source, and the gate pull-up are not on the module 3V3 copper. The LDO does not yet feed the MCU.
- `VSYS`: U3 VIN is not on U2 SYS. U2 SYS is not on the old SYS copper.
- `3V3_DISP`: Q1 drain is an F.Cu stub. The west display rail on B is a different island. Joining them wants a via, which this pass would not drill through the pour.
- `VBAT`, `VBUS`, `PMID`: stubs only. The south power copper is about 12 mm away, on the other side of the FPC.
- `SCL`, `SDA`, `PMIC_INT`: Pass-BD copper still reaches U1. It does not reach the new U2 pins.
- `TS`: U2 pin 11, `R_TS`, and `NTC_BAT` are three islands, and the old TS track is a fourth.
- `SW`: U2 SW is not on `L_SYS`.
- `GND`: EP and pin 9 are tied; pins 17/18, U3 pin 1, and the moved GND pads are not on the pour.
- `PSEL`, `REGN`, `DISP_EN`: the new passives are not tied to the charger pins (`DISP_EN` is the long gap from the east pull-up to the west FET).

`shorting_items` stays 0. Closing those islands in a later pass has to move the 3V3 track off U1 pad 15 in the same edit, or the latent overlap comes back as a short.
