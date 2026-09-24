# PASS_AG — in-place ISET via west (2026-09-20)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AF (`shorting=0`, `unc=10`)  
**To:** Pass-AG (`shorting=0`, `unc=11` after `ts_via_corner`)  
**Tool:** `kicad-cli 9.0.9 pcb drc` + in-place sexpr edits

## Verdict

**Partial.** Hard gates held. ISET via west + TS via on the west B.Cu elbow (`ts_via_corner`). Unconnected 10→11 (C3 island). ILIM/CD/`R_SCL` latents remain. Not production-ready.

## KEEP (DRC-gated)

| Step | Result |
|------|--------|
| `iset_via_west` in-place | Via `(109.5, 106.0)` 0.5/0.25 → `(108.55, 106.0)` 0.35/0.15; F.Cu stub extended. `shorting=0`, `unc=10` |
| `ts_via_corner` in-place | TS via `(110.4, 105.65)` 0.35/0.15 → `(107.8, 105.65)` 0.25/0.15 on existing B.Cu elbow. `shorting=0`, `unc=11`. Sol's `(108.00, 105.65)` `0.35` overlaps VBAT `@x=108.12` and ISET B `@x=108.20`. |

Replay: `python3 tools/_pass_ag_apply_keeps.py` on the Pass-AF board.

In-place `(at …)` / endpoint edits keep KiCad item order. That avoided the Pass-AG delete flake.

## REVERT (shorts)

| Attempt | Short |
|---------|--------|
| `ts_via_off_vbat` (delete TS via cluster) | SCL↔SDA, ILIM↔PMID, CD↔SCL (item-order flake) |
| `cd_erow_del` / `cd_off_erow` | TS↔VBAT via `(110.4, 105.65)` on B1–B2; CD↔3V3/SDA |
| `move_rscl_east` `(112.0, 107.8)` → `(112.5, 107.7)` | 3V3↔SCL (via `112.16, 107.6`); 3V3↔GND (`R_CD` / `C_LDO` pads) |
| `ts_f_retract` | SCL↔SDA; TS↔ILIM (C3 stub vs ILIM F through C3) |
| `ilim_via_slide` `(111.45, 105.8)` → `(110.75, 105.8)` `0.20` | CD↔3V3 (`R_SCL` pad 2); CD↔SCL (E-row). Via-only, no length change. |

## Latent overlaps (still in copper)

These are DRC-quiet until sexpr order changes:

- TS F stubs `x=110.4` still on VBAT F `y=105.6` / C2 ILIM (via itself is now at the west B.Cu elbow)
- ILIM via `(111.45, 105.8)` size 0.5 on PMID B4/C4
- CD F.Cu `y=106.8` through U2 E3/E4/E5
- `R_SCL` pad 1 on SDA vertical `x=111.4`

## Remaining unc=11

Previous islands plus C3 TS (F island after `ts_via_corner`): GND U2 A5↔D5, mid 3V3, west 3V3_DISP ×2, SDA, SCL, PMIC_INT, U2.C3 TS.

## Next

TS via is off VBAT pads. Next **one save**: ILIM via off PMID + CD off E-row + `R_SCL` pad 1 off SDA (no new copper). Do not haul those nets on In1 (GND) / In2 (3V3). See `PASS_AG_SOL.md`.

gpt-6-sol (2026-09-24) first `R_SCL` @(112.70, 108.80) 90° assumed pad 1 at y−0.51; DRC showed pad 1 at y+0.51. Later variants use +Y correctly; Sol's TS park at `(108.00, 105.65)` still overlaps VBAT/ISET.

## Archives

- `tools/_pass_ag_sexpr_lib.py`, `_pass_ag_gate.py`, `_pass_ag_try.py`, `_pass_ag_apply_keeps.py`, `_pass_ag_run.sh`
- `cursor.md` (in-place vs delete)
- `LIVE_LOG.txt`
