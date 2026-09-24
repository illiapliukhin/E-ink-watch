# PASS_AF — UUID fix + SW2/strap-R GND (2026-09-20)

**Board:** `e-ink-watch.kicad_pcb`  
**From:** Pass-AE (`shorting=0`, `unc=12`, DRC **1101** on KiCad 9.0.9)  
**To:** Pass-AF (`shorting=0`, `unc=10`, DRC **1107**)  
**Tool:** `kicad-cli 9.0.9 pcb drc` (PPA `kicad-9.0-releases`)

## Verdict

**Improved.** Hard gates held. Closed SW2 GND and `J_STRAP_R` GND. Fixed duplicate UUIDs on SW1/SW2/SW3 so DRC refs match real pads. Not production-ready.

## KEEP (DRC-gated, rebuildable)

| Step | Result |
|------|--------|
| Uniquify 44 duplicate UUIDs on SW1/SW2/SW3 | `dup_groups=0`; SW3 ratsnest was a UUID alias of **SW2** |
| `sw3_gnd_bwrap` B.Cu 117.2,108 → 113.7,110 | `shorting=0` (extra GND stitch) |
| `sw2_gnd_f` F.Cu 116.2,111 → via 113.7,110 | **unc 12→11** |
| `strap_r_gnd_east` F 116.85,98.75→118.4 then B to via 114.65,97.8 | **unc 11→10** |

Replay: `python3 tools/_pass_af_apply_keeps.py` on `backups/_passaf_session_base.kicad_pcb`.

## REVERT (shorts)

| Attempt | Short |
|---------|--------|
| `strap_r_gnd_f` diagonal | GND↔3V3_DISP (FH12 pad 1) |
| `strap_r_gnd_bwrap` south-east | GND↔EPD_MOSI (FH12 pad 3) |
| `disp_west_to_via96` F y=103.2 | GND via @96.3,103.2 |
| `disp_west_outer` B x=81.8 | GND B @x=82.0 |

## Remaining unc=10

- **GND U2 A5↔D5** and nearby F stubs (under DSBGA / CD @ y=106.8)
- **mid 3V3** 107.1,102.97 ↔ 110.16,108.25 (ILIM/PMID pocket)
- **west 3V3_DISP** vs via 96,105.2 and B 92,87 (SWD/3V3 forest + west GND)
- **SDA / SCL** U2 → U1 (BTN/pogo forest)
- **PMIC_INT** B @94.2,106.4 ↔ F stub @110.6,106.4 (IPRETERM)

## Archives

- `backups/_passaf_session_base.kicad_pcb`
- `backups/_passaf_final_unc10_shorting0.kicad_pcb`
- `reports/drc_before_passaf.txt` / `reports/drc_after_passaf.txt`
- `tools/_pass_af_sexpr_lib.py`, `_pass_af_gate.py`, `_pass_af_try.py`, `_pass_af_apply_keeps.py`
