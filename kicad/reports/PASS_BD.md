# PASS_BD — SDA hops under EPD_RST so I2C meets (2026-10-02)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-BC (`shorting=0`, `unc=4`, `R_SCL` at `(112.00, 107.45)` rot 270)  
**To:** Pass-BD (`shorting=0`, `unc=3`)  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc`. Local edits of the stored `filled_polygon`s. No zone refill.

## Verdict

**KEEP.** SCL already reached U1 pad 29 on F. The SDA tail that finished that route shorted pad 29. SDA now leaves F at `(98.30, 89.20)`, crosses on B, and lands on pad 27 from `(99.00, 87.70)`. Unconnected stays the three balls that cannot take a through via: A5, PMIC_INT, TS. `shorting_items=0`.

`R_SCL` moved to `(112.04, 107.68)` rot 270 so the pull-up sits on SCL and 3V3 without covering the SDA tail. `R_SDA` moved to `(111.10, 109.30)` so its courtyard clears SW2 and its pad 1 meets the jog at x=110.55. `SW_DBG` stays `(90.50, 105.50)`, default OFF. No VBUS on the dock. No microvia and no filled via-in-pad. Power widths were not narrowed.

## Why F alone cannot feed both pads

U1 pad 29 (SCL) and pad 27 (SDA) are 0.40 mm apart at the edges. A 0.15 mm track does not fit between them. The SCL diagonal `(102.60, 92.50)–(98.20, 87.70)` is the wall in front of pad 27, and the BTN3 via `(98.80, 93.95)` sits on pad 27’s x. An F-only search around that wall found no corridor that hits pad 27 and misses pad 29.

The B hop crosses the EPD_RST wall at y=89. That wall moves north between x=97.4 and x=99.8 so the SDA segment can pass.

## Copper

`R_SCL` `Resistor_SMD:R_0402_1005Metric` at `(112.04, 107.68)` rot 270. Pad 1 on the SCL via `(111.90, 107.40)`, pad 2 on the 3V3 rail. Courtyard overlaps U2, the same class as the old seat, and clears `R_SDA` by 0.22 mm.

`R_SDA` at `(111.10, 109.30)` rot 0. SDA comes off E4, up to y=108.30, west to x=110.55, then down into pad 1. 3V3 joins pad 2 from `(112.50, 109.00)`.

SDA, width 0.15, net 27, replacing the three F segments that hit pad 29:

- F `(97.42, 92.43)–(98.30, 89.20)`. Edge gap 0.364 mm.
- Via `(98.30, 89.20)` 0.45/0.20. F copper gap 0.640 mm, hole gap 0.765 mm.
- B `(98.30, 89.20)–(99.00, 87.70)`. Edge gap 0.670 mm.
- Via `(99.00, 87.70)` 0.45/0.20. F copper gap 0.290 mm, hole gap 0.415 mm.
- F `(99.00, 87.70)–(98.85, 87.25)` into pad 27. Edge gap 0.440 mm. Overlap with the pad is 0.055 mm².

EPD_RST, width 0.18, net 10. The straight B run `(104.00, 89.00)–(87.35, 89.00)` becomes:

- `(104.00, 89.00)–(99.80, 89.00)`
- `(99.80, 89.00)–(99.80, 89.85)`
- `(99.80, 89.85)–(97.40, 89.85)`
- `(97.40, 89.85)–(97.40, 89.00)`
- `(97.40, 89.00)–(87.35, 89.00)`

The three new pieces clear other B copper by 0.392 mm, 0.420 mm, and 0.770 mm. The two pieces that stay on y=89 are the old line and still cross `EPD_CS_MAIN` and `EPD_CS_L`, which that line already crossed.

## Keepouts

Every new via is a through via, so it drills B, In1, and In2. The cuts are holes in the stored fill. `(100, 100)` stays inside each pour. The rest of each ring is the original point list. No F.Cu zone was cut.

| Via | B GND | In1 GND | In2 3V3 | Rule |
|-----|-------|---------|---------|------|
| SDA `(98.30, 89.20)` 0.45/0.20 | 0.498 mm | 0.496 mm | 0.496 mm | 0.350 mm |
| SDA `(99.00, 87.70)` 0.45/0.20 | 0.498 mm | 0.490 mm | 0.497 mm | 0.350 mm |

### B.Cu GND — zone `f8a49630-cf63-4392-a480-09453f05d13c`

The existing hole around `(98.4, 89.0)` is a simple loop (indices 2030–2099, no nested bridge). That loop was replaced with the outline of the hole after subtracting a 0.32 mm stadium on `(98.30, 89.20)–(99.00, 87.70)` and 0.50 mm disks on both vias. Area 958.260 → 957.157. Added copper 0. The B track has no sample left in the pour.

### In1.Cu GND — zone `03ba8da5-3329-4248-8d94-a8b4b9831a74`

Via B only needed the existing hole enlarged. The vertices inside the 0.50 mm disk were replaced with the disk arc. Via A is in solid copper, so a 16-point circle r=0.50 was spliced on a 0.111 mm bridge from `(99.534, 87.807)`. Added copper vs a true disk is 0.016 mm² (the flat of the 16-gon). The via still sits 0.490 mm outside.

### In2.Cu 3V3 — zone `885d0b4b-000f-4931-8d0a-8ec2b4bc5458`

Same disk arcs, including the outline bite at via A (the center was 0.349 mm from the pour, 0.001 mm short of the drill rule). Added copper 0.001 mm². No new hole. Rebuilding either ring from a geometry library was not used: a round-trip of the current B fill drops hundreds of mm².

The bowed EPD_RST segments sit in the stored B pour (zone clearance actual 0.000 mm). The straight segment they replaced already did. `shorting_items` does not list them. A refill would push GND off the track; this pass did not refill.

## DRC

`Found 893 violations`, `Found 3 unconnected items`. Before this hop the same tree was 886 violations, 3 unconnected, and 1 short (SDA vs U1 pad 29).

| Check | Before hop | After |
|-------|------------|-------|
| `shorting_items` | 1 (SDA ↔ U1.29 SCL) | 0 |
| unconnected | A5, PMIC_INT, TS | A5, PMIC_INT, TS |
| hole clearance actual 0.000 mm vs a zone | 98 | 98 |
| zone clearance actual 0.000 mm | 184 | 188 |

The two new vias add `drill_out_of_range` (0.20 vs 0.30) and `via_diameter` (0.45 vs 0.60). That is the same class as the SCL vias already on the board. Neither via has a hole-clearance hit. Courtyards stay 23. Solder-mask bridges 28 → 27.

## Still open

A5, PMIC_INT, and TS. A 0.15 mm track does not fit between 0.23 mm balls on a 0.40 mm pitch, and a through via in those pads needs a drill the hole rule does not allow. A microvia or a filled via-in-pad would close them and would make the board harder to build. This pass keeps standard through vias.
