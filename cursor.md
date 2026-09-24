# cursor.md — agent lessons (E Ink watch / KiCad)

Do not skip these on the next PCB pass.

## Verification

- After every copper edit run `kicad-cli pcb drc` and keep `shorting_items=0` plus power-priority pairs at 0. Revert the board if the gate fails.
- Rebuild KEEP edits from `backups/_passaf_session_base.kicad_pcb` with `tools/_pass_af_apply_keeps.py` before treating a pass as done.
- A clearance probe that only measures endpoints will miss crossing tracks. Include segment–segment intersection and **pads**, not only tracks/vias.

## KiCad pitfalls found

- Copied footprints (SW1/SW2/SW3) reused pad UUIDs. KiCad then reports the wrong ref for unconnected pads. Uniquify duplicate `(uuid …)` before trusting DRC ratsnests.
- Hirose FH12 0.5 mm: middle pins (GND on pad 2) must exit along **+X / cable**, not toward pad 1/3 on the 0.5 mm pitch. A diagonal from pad 2 shorts `3V3_DISP` or `EPD_MOSI`.
- Inserting long B.Cu on the west rim (x≈81.8) shorts existing GND at x≈82.0. West `3V3_DISP` cannot cross the SWD/3V3 forest on F.Cu.
- `pcbnew SaveBoard` after adding copper can promote distant clearance to `shorting_items`. Prefer sexpr insert next to the PMID via `(111.35, 103.85)`.
- **Deleting** copper reorders remaining items and can promote latent overlaps to `shorting_items` (Pass-AG: TS↔VBAT, ILIM↔PMID, CD↔SCL, SCL↔SDA). **In-place** `(at …)` / endpoint edits keep file order. Use `set_via_at` / `set_seg_ends`, not delete-then-add, when opening U2 streets.
- ISET via 0.5 mm @(109.5, 106.0) blocked the west C-row pocket. KEEP: slide to @(108.55, 106.0) and shrink to 0.35/0.15. Do not sit a 0.5 mm via next to VBAT F @x=108.12.
- Do not slide `R_SCL` +0.5 X. Pad 2 (`3V3`) hits `R_CD`/`C_LDO` GND; the E5 SCL stub then clips the 3V3 via @(112.16, 107.6). Need a rotation or a larger move of `R_CD`/`C_LDO` first.
- Latent U2 shorts **cleared** by `sol_combo_west` (one in-place save): ILIM via `(110.75, 105.80)` 0.20; CD E-row + vertical `x=112.8`; TS F onto C3; `R_SCL` `(108.8, 109.8, 90)`. DRC `shorting=0` unc=16. Reconnect next.
- KiCad footprint `90` on 0402 maps pad 1 to **+Y** (clockwise), not −Y. `R_SCL` @(112.7, 109.25) 90 put SCL pad 1 at (112.7, 109.76). A 3V3 stub drawn to +Y shorts SCL.
- `set_seg_ends` on CD still promoted ILIM↔PMID. Only the ISET in-place KEEP (edit *before* the ILIM via in the file, no new overlap) stayed quiet. Fix ILIM↔PMID and TS↔VBAT geometrically before any other copper change.
- Do not store Experiential/`EXPLABS_API_KEY` in the repo or logs. Keys pasted in chat should be rotated.
- gpt-6-sol TS park `(108.00, 105.65)` `0.35` overlaps VBAT F `@x=108.12` w=0.35 and ISET B `@x=108.20`. KEEP: existing TS B.Cu elbow `(107.8, 105.65)` `0.25/0.15` (`ts_via_corner`). The `y=105.65` run under VBAT cannot hold a through via except at that west corner.
- In1 is GND plane and In2 is 3V3 plane. Do not haul CD/SDA on those layers (Sol variant A).
- `set_seg_ends` on TS F (`ts_f_retract`) promoted SCL↔SDA and TS↔ILIM (C3 stub vs ILIM F diagonal through C3). Retract ILIM F off C3/PMID in the same save as any TS F change.
- ILIM via-only slide to `(110.75, 105.80)` `0.20` was overlap-clear of PMID/VBAT but DRC still reported CD↔3V3 and CD↔SCL. File length did not change. Moving the ILIM via promotes the CD E-row latents; clear CD (and R_SCL pad-on-SDA) in the **same** save as the ILIM via.
- Send Sol annotated F.Cu/B.Cu maps plus KiCad 3D of U2. If it is wrong, reply with the overlap numbers and new pictures; do not apply blindly. Vision KEEP `R_SCL (108.8, 109.8, 90)` was F.Cu-clear (TP6 pad is **B.Cu** only). Its ILIM via `0.25@(110.80,105.80)` still clipped PMID F (edge −0.042) — use `0.20@(110.75,105.80)`. CD vertical `x=112.8` crosses 3V3 F `y=107.8`; retract it with the E-row.
- Combined KEEP `sol_combo_west`: ILIM via + ILIM F stub + CD E-row + CD vertical + TS F onto C3 + `R_SCL` rotate-move, one save. `shorting=0`, unc 11→16.
- gpt-6-sol Chat Completions tool loop works on Experiential (`list_dir` / `read_file` / `grep` / `glob` / `read_image` / `inspect_pcb_window` / `probe_clearance`). Do not replace it with a pasted coordinate brief. Deny `*explabs_key*` / `.env`. Round BGA pads as circles in the probe (AABB false-overlaps VBAT B2).
- `inspect_pcb_window` must list **NC** pads. Sol's first self-browse KEEP hauled CD west onto U2.E1 `(110.20, 106.80)` which has no net. CD is E2 only. Reconnect CD toward via `(113.30, 108.41)`, never onto E1.
- ILIM F down to `y=105.80` has probe RISK edge `+0.000` vs VBAT F `y=105.60` w=0.28. Do not drop ILIM onto that street.
- After a correction round, Sol's 3V3 L from `R_SCL` pad2 `(108.80, 109.29)` → `(110.50, 109.29)` → `(110.50, 108.25)` → island `(110.16, 108.25)` DRC-gated as `sol_rscl_3v3`: `shorting=0`, unc 16→15. Add-segment insert still needs the full gate (item-order flake).
- Stepwise with Sol: leftover 3V3 stub `(112.51, 107.80)–(114.60, 107.80)` still fed `R_LSCTRL` pad2 but was an island vs via `(112.16, 107.60)`. One F.Cu tie `(112.51, 107.80)–(112.16, 107.80)` w=0.20 DRC-gated as `sol_3v3_lsctrl_tie`: `shorting=0`, unc 15→14. CD south of E2 still hits the SDA diagonal `(109.44, 108.10)–(111.40, 106.80)` — do not force a CD via there.

## Hard gates (do not relax)

- `shorting_items = 0`
- Power pairs: GND↔VBUS/VBAT/VBUS_POGO/SW/VSYS, 3V3↔GND, 3V3_DISP↔GND, 3V3↔3V3_DISP
- Pocket: PMID↔VBUS, 3V3_DISP↔PMID, PMID↔SW
- Do not apply VBUS on the dock while any power short is possible
