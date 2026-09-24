# PASS_AG — in-place ISET via west (2026-09-20)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AF (`shorting=0`, `unc=10`)  
**To:** Pass-AG (`shorting=0`, `unc=10`)  
**Tool:** `kicad-cli 9.0.9 pcb drc` + in-place sexpr edits

## Verdict

**Partial.** Hard gates held. Moved the ISET via off the U2 west C-row pocket without promoting shorts. Unconnected count unchanged. Not production-ready. Session paused after a requested stop.

## KEEP (DRC-gated)

| Step | Result |
|------|--------|
| `iset_via_west` in-place | Via `(109.5, 106.0)` 0.5/0.25 → `(108.55, 106.0)` 0.35/0.15; F.Cu stub extended. `shorting=0`, `unc=10` |

Replay: `python3 tools/_pass_ag_apply_keeps.py` on the Pass-AF board.

In-place `(at …)` / endpoint edits keep KiCad item order. That avoided the Pass-AG delete flake.

## REVERT (shorts)

| Attempt | Short |
|---------|--------|
| `ts_via_off_vbat` (delete TS via cluster) | SCL↔SDA, ILIM↔PMID, CD↔SCL (item-order flake) |
| `cd_erow_del` / `cd_off_erow` | TS↔VBAT via `(110.4, 105.65)` on B1–B2; CD↔3V3/SDA |
| `move_rscl_east` `(112.0, 107.8)` → `(112.5, 107.7)` | 3V3↔SCL (via `112.16, 107.6`); 3V3↔GND (`R_CD` / `C_LDO` pads) |

## Latent overlaps (still in copper)

These are DRC-quiet until sexpr order changes:

- TS via `(110.4, 105.65)` on VBAT F `y=105.6` / U2.B1 / U2.B2
- ILIM via `(111.45, 105.8)` size 0.5 on PMID B4/C4
- CD F.Cu `y=106.8` through U2 E3/E4/E5
- `R_SCL` pad 1 on SDA vertical `x=111.4`

## Remaining unc=10

Same islands as Pass-AF: GND U2 A5↔D5, mid 3V3, west 3V3_DISP ×2, SDA, SCL, PMIC_INT.

## Next

Fix ILIM via `(111.45, 105.8)` and TS via `(110.4, 105.65)` **in-place first**. Then rotate `R_SCL` with pad 1 at **+Y** (KiCad 0402 `90` is clockwise). Do not add copper until those two overlaps are gone.

gpt-6-sol (2026-09-24) proposed `R_SCL` @(112.70, 108.80) 90° assuming pad 1 at y−0.51; DRC showed pad 1 at y+0.51 on the 3V3 stub. Reverted.

## Archives

- `tools/_pass_ag_sexpr_lib.py`, `_pass_ag_gate.py`, `_pass_ag_try.py`, `_pass_ag_apply_keeps.py`, `_pass_ag_run.sh`
- `cursor.md` (in-place vs delete)
- `LIVE_LOG.txt`
