# PASS_AG — in-place ISET via west (2026-09-20)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AF (`shorting=0`, `unc=10`)  
**To:** Pass-AG (`shorting=0`, `unc=9` after `sol_3v3_west_via`)  
**Tool:** `kicad-cli 9.0.9 pcb drc` + in-place sexpr edits

## Verdict

**Partial.** Hard gates held. Combined Sol vision KEEP cleared the four U2 latents. Sol then browsed the repo: `sol_rscl_3v3` then `sol_3v3_lsctrl_tie` reconnected the west `R_SCL` pad2 and the leftover `R_LSCTRL` 3V3 stub. Independent CD F→B KEEP (`sol_cd_e2_via`) and ILIM C2 dogbone (`sol_ilim_c2_dogbone`) closed E2 and C2 (`unc` 16→12). South 0402 heap spread with `sol_rscl_west` (`R_SCL` to `(106.5, 110.1, 90)`). Independent `sol_gnd_d5_via` + F.Cu tie `sol_gnd_d5_tie` joined D5 onto east `R_CD` GND (`unc` 12→10). Independent `sol_3v3_west_via` joined east 3V3 to west via `(102.52, 109.40)` on B.Cu north of BTN3 (`unc` 10→9). C3 TS and E5 SCL still islands. Not production-ready.

## KEEP (DRC-gated)

| Step | Result |
|------|--------|
| `iset_via_west` in-place | Via `(109.5, 106.0)` 0.5/0.25 → `(108.55, 106.0)` 0.35/0.15; F.Cu stub extended. `shorting=0`, `unc=10` |
| `ts_via_corner` in-place | TS via `(110.4, 105.65)` 0.35/0.15 → `(107.8, 105.65)` 0.25/0.15 on existing B.Cu elbow. `shorting=0`, `unc=11`. Sol's `(108.00, 105.65)` `0.35` overlaps VBAT `@x=108.12` and ISET B `@x=108.20`. |
| `sol_combo_west` in-place | ILIM via `(111.45, 105.8)` 0.5 → `(110.75, 105.8)` 0.20/0.15; ILIM F stub on C2; CD E-row + vertical retracted; TS F onto C3 stub; `R_SCL` `(108.8, 109.8, 90)`. `shorting=0`, `unc=16`. |
| `sol_rscl_3v3` add F.Cu | Orthogonal 3V3 from `R_SCL` pad2 `(108.80, 109.29)` → `(110.50, 109.29)` → `(110.50, 108.25)` → existing island `(110.16, 108.25)`. Sol proposed after browsing the repo; first CD/E1 KEEP rejected. `shorting=0`, `unc=16→15`. |
| `sol_3v3_lsctrl_tie` add F.Cu | One segment `(112.51, 107.80)–(112.16, 107.80)` w=0.20 ties leftover `R_LSCTRL` 3V3 stub onto the via vertical. Sol picked this as the orderly single-item KEEP; CD/TS not KEEP (SDA diagonal / VBAT street). `shorting=0`, `unc=15→14`. |
| `sol_cd_e2_via` add F/B | CD E2 dogbone via `(110.6, 106.95)` `0.25/0.15` + F stub w=0.15 + B.Cu L `y=106.95` / `x=112.65` onto existing CD via `(113.3, 108.41)`. Sol's via-in-pad on E2 and B `x=112.4` rejected (3V3 via OVERLAP `−0.120`). `shorting=0`, `unc=14→13`. |
| `sol_ilim_c2_dogbone` add F.Cu | Orthogonal w=0.08 `(110.6, 106.0)–(110.75, 106.0)–(110.75, 105.8)` onto KEEP ILIM via. Do not drop ILIM on `x=110.6` at `y=105.80` (VBAT RISK `+0.020`). `shorting=0`, `unc=13→12`. |
| `sol_rscl_west` in-place | Spread SCL/TS 0402 heap: `R_SCL (108.8, 109.8, 90)` → `(106.5, 110.1, 90)`; 3V3 L retargeted to pad2 `(106.5, 109.59)` → `(110.5, 109.59)` → `(110.5, 108.25)`. Sol's `R_SDA (111.35, 110.30)` rejected (courtyard onto `SW1`/`SW2`). `shorting=0`, `unc=12`. |
| `sol_gnd_d5_via` add F/via | U2.D5 GND dogbone via `(112.4, 106.55)` `0.25/0.15` + F L `(111.8,106.4)→(112.4,106.4)→(112.4,106.55)` w=0.12. Not VIP. Via does not stitch stale In1 fill. `shorting=0`, `unc=12→11`. |
| `sol_gnd_d5_tie` add F.Cu | Orthogonal F.Cu east-then-south `(112.4,106.55)→(112.8,106.55)→(112.8,107.24)` w=0.12 onto existing `R_CD` GND. Probe overlap=0 (3V3_DISP via `+0.300`, 3V3 via `+0.374`). Vertical-first `(112.4,106.55)–(112.4,107.24)` is only `+0.073` vs 3V3 via — rejected. `shorting=0`, `unc=11→10`. |
| `sol_3v3_west_via` add B/via | Via on existing 3V3 F rail `(110.4, 108.25)` `0.25/0.15` + B.Cu L `(110.4,108.25)→(110.4,108.55)→(102.52,108.55)→(102.52,109.40)` onto west 3V3 via. Sol's F.Cu `(102.52,109.40)–(106.5,109.40)` hits VBUS. Via `(107.0,109.59)` cannot B-drop across BTN3 `y=109.15`. `(110.8,108.25)` overlap LSCTRL B. Probe overlap=0 (LSCTRL B `+0.200`, BTN3 `+0.450`). `shorting=0`, `unc=10→9`. |

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

## Remaining unc=9

GND A5 vs D5, D5/`R_CD` east GND vs west GND `(108.71, 108.60)` (`NTC_BAT`/`C_BAT`), west 3V3_DISP, SDA to U1, SCL E5 vs `R_SCL` pad1 `(106.5, 110.61)`, SCL to U1, PMIC_INT, TS C3 vs TS B via `(107.8, 105.65)`. Pocket CD (E2), ILIM (C2), D5→east GND, and east 3V3→west via are closed. `R_SDA` still sits in the F street at `(111.50, 109.00)`.

## Next

Orthogonal F/B reconnect of TS C3 and SCL E5→`R_SCL` pad1 `(106.5, 110.61)`. Do not park `R_SDA` on `SW1`/`SW2` courtyards. New CD B.Cu at `y=106.95` `x=110.60–112.65` — through vias there short CD. New GND via does not stitch In1 until refill — use F.Cu ties to existing GND copper. No In1/In2 signal hauls. No new overlap. East 0402 column stays (`R_CD`/`C_LDO` x=113.5, `R_LSCTRL` x=114.6, `R_ILIM` x=115.6).

gpt-6-sol now browses with `tools/_sol_repo_explore.py`. NC pads must show in `inspect_pcb_window` / `probe_clearance` or it will haul CD onto E1.

## Archives

- `tools/_pass_ag_sexpr_lib.py`, `_pass_ag_gate.py`, `_pass_ag_try.py`, `_pass_ag_apply_keeps.py`, `_pass_ag_run.sh`
- `tools/_u2_pocket_render.py`, `_sol_vision_ask.py`, `_sol_repo_explore.py`, `_sol_board_query.py`
- `reports/sol_views/`
- `reports/PASS_AG_SOL.md`, `reports/PASS_AG_SOL_VISION.md`, `reports/PASS_AG_SOL_EXPLORE.md`, `reports/PASS_AG_SOL_EXPLORE_FOLLOWUP.md`, `reports/PASS_AG_SOL_STEP.md`, `reports/PASS_AG_SOL_STEP2.md`, `reports/PASS_AG_SOL_STEP3.md`, `reports/PASS_AG_SOL_STEP4.md`, `reports/PASS_AG_SOL_STEP5.md`, `reports/PASS_AG_SOL_STEP6.md`
- `LIVE_LOG.txt`
