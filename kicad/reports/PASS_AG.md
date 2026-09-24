# PASS_AG — in-place ISET via west (2026-09-20)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AF (`shorting=0`, `unc=10`)  
**To:** Pass-AG (`shorting=0`, `unc=16` after `sol_combo_west`)  
**Tool:** `kicad-cli 9.0.9 pcb drc` + in-place sexpr edits

## Verdict

**Partial.** Hard gates held. Combined Sol vision KEEP cleared the four U2 latents in one save. Unconnected 11→16 (islands on C2/C3/E2/E5/`R_SCL`). Reconnect next. Not production-ready.

## KEEP (DRC-gated)

| Step | Result |
|------|--------|
| `iset_via_west` in-place | Via `(109.5, 106.0)` 0.5/0.25 → `(108.55, 106.0)` 0.35/0.15; F.Cu stub extended. `shorting=0`, `unc=10` |
| `ts_via_corner` in-place | TS via `(110.4, 105.65)` 0.35/0.15 → `(107.8, 105.65)` 0.25/0.15 on existing B.Cu elbow. `shorting=0`, `unc=11`. Sol's `(108.00, 105.65)` `0.35` overlaps VBAT `@x=108.12` and ISET B `@x=108.20`. |
| `sol_combo_west` in-place | ILIM via `(111.45, 105.8)` 0.5 → `(110.75, 105.8)` 0.20/0.15; ILIM F stub on C2; CD E-row + vertical retracted; TS F onto C3 stub; `R_SCL` `(108.8, 109.8, 90)`. `shorting=0`, `unc=16`. |

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

## Latent overlaps

The four U2 latents from Pass-AG are **geometrically cleared** by `sol_combo_west` (DRC `shorting=0` after the same save). Remaining work is reconnect, not overlap.

## Remaining unc=16

Previous islands plus C2 ILIM, C3 TS, E2 CD, E5 SCL, `R_SCL` pads (moved west), leftover 3V3 stub at `(112.51, 107.8)`.

## Next

Orthogonal F/B reconnect of TS C3, ILIM C2, CD E2, SCL E5→`R_SCL` pad1, 3V3→`R_SCL` pad2. No In1/In2. No new overlap. Send Sol the after-KEEP pocket images for stub coordinates.

gpt-6-sol vision (2026-09-24): three variants after seeing annotated F/B + 3D. Combined KEEP applied with two corrections: via `(110.75, 105.80)` `0.20` not `(110.80, 0.25)` (PMID F clip); CD vertical `x=112.8` retracted because it crossed 3V3 `y=107.8`.

## Archives

- `tools/_pass_ag_sexpr_lib.py`, `_pass_ag_gate.py`, `_pass_ag_try.py`, `_pass_ag_apply_keeps.py`, `_pass_ag_run.sh`
- `tools/_u2_pocket_render.py`, `_sol_vision_ask.py`
- `reports/sol_views/`
- `reports/PASS_AG_SOL.md`, `reports/PASS_AG_SOL_VISION.md`
- `LIVE_LOG.txt`
