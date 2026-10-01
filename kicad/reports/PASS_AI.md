# PASS_AI — 3V3_DISP west seam probed, not kept (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb`  
**From / to:** Pass-AH (`shorting=0`, `unc=8`). No copper kept.  
**Tool:** KiCad 9.0.9 `kicad-cli pcb drc`. Probe clearance 0.15 mm. Outline endpoints inside r≈19.2 of (100, 100).

## Verdict

**No KEEP.** The eight unconnected pairs are unchanged. One complete `3V3_DISP` path is probe-clear and would drop unconnected 8→7, but both gated saves promoted existing pairs into `shorting_items`. Each was reverted to `backups/_passah_last_ok.kicad_pcb` before the next edit. Do not apply VBUS on the dock.

The via on the west stub is `(85, 102.75)` uuid `d2999c94-56c5-4a74-a95d-79b127805a81` (net 3, size 0.6/0.3). Uuid `7b923f4d-a456-4460-98a5-c54e1af38dec` is the east via at `(92, 87)`, not the west one.

## Inventory (unc=8, shorting=0)

Same eight pairs as the Pass-AH DRC (`reports/_drc_passah_disp_via_onto_west.txt`):

1. GND F `(111.8, 106.4)` len 0.6 vs U2 pad A5 GND `(111.8, 105.2)`
2. GND F `(111.8, 106.4)` vs west F `(108.71, 108.6)` len 1.19
3. `3V3_DISP` B `(92, 87)` len 2.0 vs F `(84.45, 98.25)` len 0.55
4. SDA F `(109.44, 108.1)` vs U1 pad 27 `(98.8, 87.25)`
5. SCL `R_SCL` pad1 `(106.5, 110.61)` vs E5 F stub `(111.8, 106.8)`
6. SCL E5 stub vs U1 pad 29 `(98.0, 87.25)`
7. PMIC_INT B `(94.2, 90.55)–(94.2, 106.4)` vs F stub `(110.6, 106.4)`
8. TS F `(111.0, 106.0)` vs TS B `(107.8, 105.65)`

West `3V3_DISP` is one island (x 83.15–85, y 98.25–105.5, via at `(85, 102.75)`). Everything else on that net, including vias `(92, 87)`, `(94, 87)`, and `(113, 106)`, is the other island.

## Corridor that does not close

Horizontal B.Cu at y=106.70–106.74, w=0.12, from x=93.3:

- Clears PMIC_INT (ends y=106.4, w=0.18) and GND via `(94.16, 107.25)` size 0.6 through about x=95.7.
- Dies on VBAT via `(96.2, 106.25)` size 0.6 at edge `+0.121` (need 0.15).
- BTN1 B.Cu x=98, y=93.85–110.50, w=0.18 is a wall (edge `−0.150`). BTN2 x=98.5 and BTN3 x=98.8 leave no 0.15 mm slot between them. x≥100.70 (east of EPD_CS_L) is not reachable on this street.
- EPD_SCK B.Cu y=94.5, x=85–115, w=0.18 cannot be crossed. The west end is boxed by the SCK vertical, MOSI x=83, EPD_DC x=82.5, and the outline. The east end is not reachable inside r=19.2. A y-jog around EPD_CS_L (y=91.8) sits north of this wall, so it is not reachable either.
- Off-board F at y=82.4 was not used.

Floods on F.Cu and B.Cu from `(88.54, 102.75)` do not meet `(92, 87)` or `(94, 87)`.

## Probe-clear seam (gated, not kept)

A different seam on the west rim is clear at ≥0.15 mm and inside the outline:

- Move the existing via `(85, 102.75)` 0.6/0.3 → `(84.4, 96)`. Tightest edge `+0.181` vs EPD_SCK via `(85, 96.5)`.
- F.Cu w=0.25: `(84.45, 98.25) → (83.55, 97.4) → (83.55, 95.9) → (84.4, 96)`. Worst `+0.335`. w=0.35 fails (`+0.143` vs GND via `(84.35, 96.8)`).
- B.Cu w=0.45: `(84.4, 96) → (84.4, 94.2) → (87, 88.4) → (92, 87)`. Worst `+0.185` vs EPD_MOSI B y=86.5. The end sits on the east via.

### REVERT `disp_west_seam` (new segments before the PMID via)

`shorting=4`, `unc=7`, power and pocket still 0. Reverted.

Promoted pairs (items that were not the new tracks):

- EPD_MOSI via `(85.35, 97.8)` ↔ EPD_SCK F `(85, 101.25)`
- EPD_SCK F `(85, 101.25)` ↔ existing `3V3_DISP` F `(85, 98.25)` (baseline already calls this a track crossing, not a short)
- 3V3 ↔ SWDIO_POGO pad 6 of SW_DBG (baseline solder-mask bridge)
- 3V3 ↔ SWDCLK_POGO pad 5 of SW_DBG

### REVERT `disp_west_seam_inplace` (no new items)

Same route, built by sliding the via and retargeting one copy of each duplicate segment so file order does not change. F legs narrowed 0.45→0.25. B legs stayed 0.45. The untouched twin keeps the old copper.

`shorting=2`, `unc=7`, power and pocket still 0. Reverted.

- 3V3 F `(97.6, 86.35)` ↔ EPD_MOSI via `(101.6, 86.5)`
- 3V3 F `(94.9, 101.95)` ↔ SWDIO_POGO pad 6

Both pairs are far from the seam. Joining the islands still flipped them into `shorting_items`. Not kept.

## Still blocked (not replayed)

- West GND / A5: F legs hit 3V3 or `R_SDA`; B legs hit 3V3 y=108.55, LSCTRL, or BTN3 y=109.15. A5 north-east overlaps PMID / SW / ILIM. Pass-AH 4-leg scan found no path.
- SCL: BTN3 B y=109.15, BTN1 via, VBUS, 3V3. Do not slide `R_SCL`.
- TS: C3 via `(110.35, 106.05)` shorts ILIM (Pass-AH revert).
- PMIC_INT: B y=106.4 hits VBAT and IPRETERM; jog y=107.85 hits GND vias `(94.16, 107.25)` and `(94.5, 107.5)`.
- Do not park `R_SDA` on SW1/SW2. No In1/In2 hauls. No zone refill. No new via next to C3 `(96, 102.75)`.

## Archives

- `tools/_pass_ai_try.py` (`disp_west_seam_inplace`), `tools/_pass_ai_gate.py`
- Gate reverts unless `shorting==0`, power pairs 0, pocket 0, and unconnected `< backups/_passah_unc.txt`
