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
- Latent U2 shorts still in copper (DRC-quiet until item order changes): TS F stubs `x=110.4` on VBAT/C2 (via KEEP at `(107.8, 105.65)`); ILIM via @(111.45, 105.8) on PMID B4/C4; CD F @y=106.8 through E3/E4/E5; `R_SCL` pad 1 on SDA x=111.4.
- KiCad footprint `90` on 0402 maps pad 1 to **+Y** (clockwise), not −Y. `R_SCL` @(112.7, 109.25) 90 put SCL pad 1 at (112.7, 109.76). A 3V3 stub drawn to +Y shorts SCL.
- `set_seg_ends` on CD still promoted ILIM↔PMID. Only the ISET in-place KEEP (edit *before* the ILIM via in the file, no new overlap) stayed quiet. Fix ILIM↔PMID and TS↔VBAT geometrically before any other copper change.
- Do not store Experiential/`EXPLABS_API_KEY` in the repo or logs. Keys pasted in chat should be rotated.
- gpt-6-sol TS park `(108.00, 105.65)` `0.35` overlaps VBAT F `@x=108.12` w=0.35 and ISET B `@x=108.20`. KEEP: existing TS B.Cu elbow `(107.8, 105.65)` `0.25/0.15` (`ts_via_corner`). The `y=105.65` run under VBAT cannot hold a through via except at that west corner.
- In1 is GND plane and In2 is 3V3 plane. Do not haul CD/SDA on those layers (Sol variant A).
- `set_seg_ends` on TS F (`ts_f_retract`) promoted SCL↔SDA and TS↔ILIM (C3 stub vs ILIM F diagonal through C3). Retract ILIM F off C3/PMID in the same save as any TS F change.
- ILIM via-only slide to `(110.75, 105.80)` `0.20` was overlap-clear of PMID/VBAT but DRC still reported CD↔3V3 and CD↔SCL. File length did not change. Moving the ILIM via promotes the CD E-row latents; clear CD (and R_SCL pad-on-SDA) in the **same** save as the ILIM via.

## Hard gates (do not relax)

- `shorting_items = 0`
- Power pairs: GND↔VBUS/VBAT/VBUS_POGO/SW/VSYS, 3V3↔GND, 3V3_DISP↔GND, 3V3↔3V3_DISP
- Pocket: PMID↔VBUS, 3V3_DISP↔PMID, PMID↔SW
- Do not apply VBUS on the dock while any power short is possible
