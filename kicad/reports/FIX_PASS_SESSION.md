# FIX_PASS_SESSION — Pass-P + Pass-Q + Pass-R (2026-09-18 IDT)

## Verdict
**Improved (targeted pairs) / count flat.**  
`shorting_items` **12 → 12**. Power-priority shorts **stayed 0**.  
Cleared **EPD_BUSY_MAIN↔EPD_MOSI** and **SWDCLK↔nRESET**.  
**Not production-ready** — shorts remain; do **not** apply VBUS on the dock.

## Commands run
```bash
# Baseline
kicad-cli pcb drc --format report --output reports/drc_baseline_20260918_2013.txt e-ink-watch.kicad_pcb
kicad-cli sch erc --format report --output reports/erc_baseline_20260918_2013.txt e-ink-watch.kicad_sch

# Backups
cp e-ink-watch.kicad_pcb e-ink-watch-backups/pre_passo_20260918_201346_s12.kicad_pcb

# Attempted (all reverted except EPD + nRESET B-hop):
python3 tools/_pass_o_phases/02_jstrap_mp.py          # REVERT — GND↔SW
python3 tools/_pass_o_phases/01_cldo.py                # REVERT — power shorts
python3 tools/_pass_p_signal_trim.py                   # REVERT — GND↔SW from SW via move
python3 tools/_pass_p_epd_only.py                      # KEEP
python3 tools/_pass_p_nreset_bhop.py                   # KEEP
# via shrink / SWDCLK_POGO+EPD_BUSY_R extras           # REVERT

# Final (no zone refill)
kicad-cli pcb drc --format report --output reports/drc_after_passp_20260918_2018.txt e-ink-watch.kicad_pcb
```

## Before / after

| Metric | Baseline (`drc_baseline_20260918_2013`) | After Pass-P (`drc_after_passp_20260918_2018`) |
|--------|------------------------------------------|------------------------------------------------|
| shorting_items | **12** | **12** |
| DRC violations (header) | **600** | **594** |
| unconnected | **85** | **85** |
| clearance | **137** | **140** |
| copper_edge_clearance | **2** | **2** |
| power-priority total | **0** | **0** |
| ERC (sch) | **167** violations | (not re-run after PCB-only) |

### Power-priority pairs (must stay 0)
| Pair | Before | After |
|------|--------|-------|
| GND\|VBUS | 0 | 0 |
| GND\|VBAT | 0 | 0 |
| GND\|VBUS_POGO | 0 | 0 |
| 3V3\|GND | 0 | 0 |
| 3V3_DISP\|GND | 0 | 0 |
| GND\|SW | 0 | 0 |
| 3V3\|3V3_DISP | 0 | 0 |
| GND\|VSYS | 0 | 0 |

### Short pair composition
**Cleared vs baseline:** EPD_BUSY_MAIN↔EPD_MOSI, SWDCLK↔nRESET, GND↔ILIM (latter may be DRC flake).  
**New/exposed vs baseline:** 3V3_DISP↔PMID, GND↔SWDCLK_POGO, EPD_BUSY_R↔\<no net\> (U1.12).

**Remaining top (after):**
1. 3V3_DISP↔VSYS ×2 (J_STRAP_R pad10 / VSYS track @~117.4)
2. IPRETERM↔VBAT (U2 D1/B column @110.2,106.4)
3. PMID↔SW (vias @111.40,104.90 vs 111.35,104.35)
4. PMIC_INT↔TS
5. EPD_BUSY_R↔U1.12 \<no net\>
6. GND↔IPRETERM (via @109.55,104.5 vs B track)
7. ILIM↔TS
8. 3V3_DISP↔PMID (C_VINLS pad)
9. IPRETERM↔VSYS
10. 3V3_DISP↔ILIM
11. GND↔SWDCLK_POGO (track x=95.0 vs J_SWD pad5)

## Kept topology
- EPD_BUSY_MAIN corridor at **x=100.90** (was 101.55; MOSI at 101.60)
- nRESET **B.Cu** hop: vias **(87.55,106.90)** ↔ **(91.62,106.90)** — F.Cu cannot cross 1.7 mm J_SWD pads

## Reverted / blocked
| Attempt | Result |
|---------|--------|
| J_STRAP_R MP ease (114→114.7, 1.2×2→1.0×1.4) | short 15, GND↔SW×3 |
| C_LDO →(113.8,107.7) | short 31, 3V3_DISP↔GND×3, 3V3↔GND |
| SW via →(111.90,104.90) | GND↔SW×2, PMID↔SW worse |
| Via annular shrink | SetWidth corruption (SW w≈0), short↑ |
| SWDCLK_POGO x=95.6 + EPD_BUSY_R jog | short 19, 3V3_DISP↔GND |
| Zone refill after micro-edits | previously exposed PMID↔VBUS / power flake |

## Preserves (verified)
- 4-layer: In1.Cu=GND zone, In2.Cu=3V3 zone, B.Cu GND zone
- seal keepout vias = **0**
- pogo TP1–TP6 coords/nets unchanged
- SW_DBG: SWDIO/SWDCLK/nRESET (+POGO); no VBUS on DIP
- No wholesale GND pour deletion

## Risks
- Footprints still placeholders — geometry shorts remain
- Zone refill is **non-stable** near PMIC pocket; gate with no-refill DRC first
- nRESET vias near SW_DBG / J_SWD — watch hole_to_hole / courtyard
- Charge path incomplete (ISET copper may still be dropped); **do not energize VBUS on dock**

## Next recommended step
1. Isolate **VSYS** trim east of J_STRAP_R pad10 (avoid MP resize that caused GND↔SW).
2. **PMID↔SW**: try B.Cu SW escape south of PMID vias, or tiny SW via south move with snap+power gate (east move failed).
3. Jog **EPD_BUSY_R** around U1.12 *without* intersecting EPD_BUSY_MAIN (prior jog collided).
4. **SWDCLK_POGO** vertical to x≥95.5 in isolation (prior combo edit had collateral).
5. Defer U2 rotate / C_LDO / MP ease until PMIC corridors measured with keepout visualization.

## Absolute paths
- Board: `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch.kicad_pcb`
- Baseline DRC: `/workspace/eink-watch/E-ink-watch-main/kicad/reports/drc_baseline_20260918_2013.txt`
- After DRC: `/workspace/eink-watch/E-ink-watch-main/kicad/reports/drc_after_passp_20260918_2018.txt`
- ERC: `/workspace/eink-watch/E-ink-watch-main/kicad/reports/erc_baseline_20260918_2013.txt`
- Session note: `/workspace/eink-watch/E-ink-watch-main/kicad/reports/FIX_PASS_SESSION.md`
- Archive: `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/passp_signal_20260918_s12kept_epd_nreset.kicad_pcb`
- Pre-pass backup: `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/pre_passo_20260918_201346_s12.kicad_pcb`


---

## Pass-Q (2026-09-18 ~20:19–20:25 IDT)

### Verdict
**Improved.** `shorting_items` **12 → 10** (−2). Power-priority **stayed 0**.  
Cleared **3V3_DISP↔VSYS×2**, **IPRETERM↔VSYS**, **EPD_BUSY_R↔U1.12 (no net)**; SWDCLK_POGO geometry east of J_SWD GND.  
**Not production-ready** — shorts remain (esp. PMID↔VBUS×4); do **not** apply VBUS on the dock.

### Commands
```bash
kicad-cli pcb drc --format report --output reports/drc_before_passq_20260918_2019.txt e-ink-watch.kicad_pcb
python3 tools/_pass_q_01_vsys_trim.py      # KEEP (Q1f)
python3 tools/_pass_q_03_epd_busy_r.py     # KEEP (Q3c)
python3 tools/_pass_q_04_swdclk_pogo.py    # KEEP
kicad-cli pcb drc --format report --output reports/drc_after_passq_20260918_2025.txt e-ink-watch.kicad_pcb
# no zone refill
```

### Before / after (Pass-Q)

| Metric | Before (`drc_before_passq_20260918_2019`) | After (`drc_after_passq_20260918_2025`) |
|--------|-------------------------------------------|----------------------------------------|
| shorting_items | **12** | **10** |
| DRC violations | **594** | **588** |
| unconnected | **85** | **85** |
| clearance | **140** | **138** |
| copper_edge_clearance | **2** | **2** |
| power-priority total | **0** | **0** |

### Kept
| Change | Effect |
|--------|--------|
| VSYS: delete F (117.412,104.5→102.95) + horiz@102.95; reconnect L_SYS→north y=106.10→111.80→B5 | Cleared 3V3_DISP↔VSYS×2, IPRETERM↔VSYS |
| EPD_BUSY_R: (104.65,89.75)→y=89.20→x=107.60→(109.8,99.25) | Cleared U1.12 no-net short; no EPD_BUSY_MAIN hit |
| SWDCLK_POGO vertical x=95.00→95.60 | Clear of J_SWD pad5 GND |

### Reverted
| Attempt | Result |
|---------|--------|
| VSYS F HY=103.30 / 102.20 | GND↔VSYS power |
| VSYS B hops y=104.5 / 105.8 / 102.4 | short↑ / 3V3_DISP↔GND / GND↔VSYS |
| VSYS NY=106.55 | rebroke 3V3_DISP↔VSYS |
| SW via south (111.4,103.7) | short 19 |
| SW via SE (112.2,103.7) | GND↔SW×3 power |
| EPD_BUSY_R east @105.5 / via-dodge | 3V3 or GND↔EPD_BUSY_R |

### Remaining top shorts
1. PMID↔VBUS ×4  
2. PMIC_INT↔TS  
3. PMID↔VSYS  
4. GND↔IPRETERM  
5. PMID↔SW  
6. GND↔TS  
7. ILIM↔VSYS (collateral skim vs VSYS@y=106.10 / ILIM via@113.44,105.7)

### Scripts
- `tools/_pass_q_01_vsys_trim.py`
- `tools/_pass_q_03_epd_busy_r.py`
- `tools/_pass_q_04_swdclk_pogo.py`
- (also present, reverted attempts: `_pass_q_02_sw_via_south.py`)

### Archives
- `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/passq_topo_20260918_202511_s10.kicad_pcb`
- `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/pre_passq_20260918_2019_s12.kicad_pcb`


---

## Pass-R (2026-09-18 ~20:26–20:31 IDT)

### Verdict
**Improved (strong).** `shorting_items` **10 → 3** (−7). Power-priority **stayed 0**.  
**PMID↔VBUS 4→0**, **PMID↔VSYS 1→0**, **PMID↔SW 1→0**.  
**Not production-ready** — 3 shorts remain; C_PMID stitch to U2 may be incomplete (unconnected 85→87); do **not** apply VBUS on the dock.

### Commands
```bash
kicad-cli pcb drc --format report --output reports/drc_before_passr_20260918_2026.txt ...
python3 tools/_pass_r_01_pmid_vbus.py   # KEEP (R1h minimal)
python3 tools/_pass_r_02_pmid_sw.py     # KEEP (R2b)
python3 tools/_pass_r_03_signal_trims.py # KEEP
# R4 VSYS raise REVERTED
kicad-cli pcb drc --format report --output reports/drc_after_passr_20260918_2031.txt ...
```

### Before / after (Pass-R)

| Metric | Before | After |
|--------|--------|-------|
| shorting_items | **10** | **3** |
| DRC violations | **587** | **578** |
| unconnected | **85** | **87** |
| clearance | **137** | **135** |
| copper_edge_clearance | **2** | **2** |
| power-priority | **0** | **0** |
| PMID↔VBUS | **4** | **0** |
| PMID↔VSYS | **1** | **0** |
| PMID↔SW | **1** | **0** |

### Kept
| Change | Effect |
|--------|--------|
| Remove PMID via@(111.0,104.35) + F@x=111 below A3; A3–B3 w=0.22 | Cleared PMID↔VBUS×4 (centers 0.4 mm vs VBUS@110.6 w=0.40) |
| C_PMID south-only from via@(111.35→103.85) | Cap fanout without SW/VSYS mash |
| Delete leftover VSYS (111.8,102.95)–(111.8,105.6) | Remove Pass-Q remnant |
| PMID via →(111.35,103.85) | Cleared PMID↔SW vs SW via@(111.40,104.90) |
| Delete ILIM stub→MP; TS @y=107.40 west | Cleared GND↔ILIM, PMIC_INT↔TS, GND↔TS |

### Reverted
Heavy east/B.Cu PMID fanouts (GND↔PMID / PMID↔VSYS↑); VSYS NY=106.28 (short↑).

### Remaining top shorts
1. IPRETERM↔VBAT (U2 D1 column)  
2. GND↔IPRETERM (via@109.55 vs B track)  
3. ILIM↔VSYS (via@113.44,105.7 vs VSYS@y=106.10)

### Archives / scripts
- `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/passr_topo_20260918_203150_s3.kicad_pcb`
- `tools/_pass_r_01_pmid_vbus.py`, `_pass_r_02_pmid_sw.py`, `_pass_r_03_signal_trims.py`


---

## Pass-S (2026-09-18 ~20:32–20:40 IDT)

### Verdict
**Improved (strong).** `shorting_items` **4 → 0**. Power-priority **stayed 0**. PMID↔VBUS **stayed 0**.  
Cleared all three named remainders from Pass-R (**IPRETERM↔VBAT**, **GND↔IPRETERM**, **ILIM↔VSYS**) plus incidental **3V3↔TS**.  
**C_PMID↔U2 stitch deferred** — safe corridor blocked (see below); unconnected **87→87**.  
**Not production-ready** — unconnected 87, clearance/dangling debt, C_PMID island, VBAT west spine incomplete after S1g; do **not** apply VBUS on the dock.

### Commands
```bash
kicad-cli pcb drc --format report --output reports/drc_before_passs_20260918_2032.txt ...
python3 tools/_pass_s_01_ipreterm_vbat.py   # KEEP (S1g)
python3 tools/_pass_s_02_gnd_ipreterm.py     # KEEP (S2 + S2c)
python3 tools/_pass_s_03_ilim_vsys.py        # KEEP
python3 tools/_pass_s_04_pmid_vsys_ts.py     # KEEP
python3 tools/_pass_s_05_cvinls_cpmid.py     # KEEP (S5a trim only)
# S6/S6b/S6c/S6d TS jogs REVERTED
# S7 C_PMID stitch REVERTED
kicad-cli pcb drc --format report --output reports/drc_after_passs_20260918_2040.txt ...
```

### Before / after (Pass-S)

| Metric | Before | After |
|--------|--------|-------|
| shorting_items | **4** | **0** |
| DRC violations | **580** | **597** |
| unconnected | **87** | **87** |
| power-priority | **0** | **0** |
| IPRETERM↔VBAT | **1** | **0** |
| GND↔IPRETERM | **1** | **0** |
| ILIM↔VSYS | **1** | **0** |
| 3V3↔TS | **1** | **0** |
| PMID↔VBUS | **0** | **0** |

### Kept
| Change | Effect |
|--------|--------|
| S1g: delete VBAT climb into D1 (110.2,105.6→106.4) + horiz @y=106.4; keep B1–B2 | Cleared IPRETERM↔VBAT (no west reconnect — F/B west hit GND/ILIM) |
| S2: IPRETERM B vertical x=109.70→110.05; via@(110.05,106.40) | Cleared GND↔IPRETERM vs GND via@109.55 |
| S2c: trim PMIC_INT F west stub; B link to via | Cleared collateral IPRETERM↔PMIC_INT |
| S3: ILIM via (113.44,105.70)→(113.44,105.35) | Cleared ILIM↔VSYS vs VSYS@y=106.10 |
| S4: VSYS B5 jog east via x=112.05; PMIC_INT via 109.1→109.45 | Hold power / avoid PMID↔VSYS flake |
| S5a: trim 3V3_DISP stub @(113.0,106.0–106.32) off C_VINLS.1 PMID | Cleared 3V3_DISP↔PMID; 3V3↔TS cleared in chain |

### Reverted / deferred
| Attempt | Why |
|---------|-----|
| VBAT F/B west reconnect to C_BAT | GND↔VBAT / ILIM / VBUS / PMID mash |
| S2b IPRETERM via@(109.85,106.25) | GND↔IPRETERM back |
| S5 full C_PMID B.Cu east of SW | shorting →12 (PMID↔SW/GND/ILIM) |
| S6/S6b TS @y=107.85 / 108.15 | GND↔TS / NTC_BAT / short↑ |
| S6c/S6d TS B-hop | LSCTRL↔SCL or short↑6 |
| **S7** F west C_PMID→A3 @x=111.05 w=0.20 | shorting 0→6; corridor blocked |

### C_PMID connectivity note
- Island: via@(111.35,103.85) + F south to C_PMID.1@(111.72,103.40) — **not** stitched to U2 A3/B3/B4/C4.
- UNC still lists island ↔ U2 A3 track @(111.00,105.20).
- **Blocked why:** F west squeeze VBUS@x=110.6 vs SW via@(111.40,104.90); F east crosses VSYS bar @y=104.48; B east squeezes SW B@y=104.90 vs ILIM B@y=105.35 (gap < min clearance for safe track).
- Do **not** blind zone-refill to “fix” this.

### Remaining issues (non-shorting)
- unconnected 87 (incl. C_PMID island, C_VINLS↔U2 PMID, TS stub gap, ISET, ILIM/R_ILIM, IPRETERM/R_IPRETERM, VBUS_POGO TP1, …)
- VBAT west spine incomplete (S1g deleted climb; no safe reconnect yet)
- clearance / dangling / silk debt (~597 violations)
- Placeholder footprints

### Archives / scripts
- `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/passs_topo_20260918_2040_s0.kicad_pcb`
- `/workspace/eink-watch/E-ink-watch-main/kicad/e-ink-watch-backups/pre_passs_20260918_2032_s3.kicad_pcb`
- `tools/_pass_s_01_ipreterm_vbat.py` … `_pass_s_05_cvinls_cpmid.py` (kept)
- `tools/_pass_s_06_ts_3v3.py`, `_pass_s_07_cpmid_stitch.py` (reverted / do-not-run)


---

## Pass-T (2026-09-18 ~20:41–20:45 IDT)

### Verdict
**Partial / corridor prep only.** `shorting_items` **0 → 0** (hard gate held). Power-priority **0**. PMID↔VBUS **0**.  
**C_PMID still NOT stitched** to U2 A3/B3/B4/C4 — stitch attempts after opening west corridor still raised shorting (collateral 3V3_DISP/VSYS/PMID / SCL↔TS). Stopped per “do not thrash”.  
Unconnected **87 → 87**. SW via relocated; dangling VSYS bar removed. **Not production-ready.**

### Commands
```bash
kicad-cli pcb drc --format report --output reports/drc_before_passt_20260918_2041.txt ...
python3 tools/_pass_t_02_vsys_bar_trim.py   # KEEP (T2a)
python3 tools/_pass_t_01_sw_via_east.py     # KEEP (T1c)
python3 tools/_pass_t_03_ts_jog.py          # KEEP
# T4 C_PMID stitch REVERTED; T5 3V3_DISP trim REVERTED; T2 full C_SYS dogbone REVERTED
kicad-cli pcb drc --format report --output reports/drc_after_passt_20260918_2045.txt ...
```

### Before / after (Pass-T)

| Metric | Before | After |
|--------|--------|-------|
| shorting_items | **0** | **0** |
| DRC violations | **597** | **597** |
| unconnected | **87** | **87** |
| power-priority | **0** | **0** |
| PMID↔VBUS | **0** | **0** |
| C_PMID↔U2 | **no** | **no** |

### Corridor map (measured; min_clearance=0.15, hole_clearance=0.25)

| Obstacle | Coords | Notes |
|----------|--------|-------|
| VBUS spine | F x=**110.600** w=0.40 | Do not move west |
| SW via (pre-T) | **(111.400, 104.900)** diam≈0.55 | Blocked F west: no x with gap_VBUS≥0.15 AND gap_SWvia≥0.15 |
| SW via (kept) | **(111.550, 104.550)** | Opens F@x=111.05 w=0.15 (gap_SW≈0.275 centerline) |
| VSYS bar (deleted) | F y=**104.480** x=111.8–112.8 w=0.45 | Was dangling vs B5; blocked SW SE landing |
| SW B | y=**104.900** w=0.30 x=111.4–115 | |
| ILIM B | y=**105.350** w=0.15 x=110.3–113.44 | Copper gap SW_B→ILIM_B = **0.225** mm ≪ track+2×0.15 |
| C_VINLS.1 PMID | **(112.800, 106.280)** bbox top y=106.00 | Touches/overlaps 3V3_DISP @y=106.0 |
| C_PMID island | via **(111.350, 103.850)** → pad1 (111.720, 103.400) | UNC ↔ A3 track @(111.000, 105.200) |

### Kept
| Change | Effect |
|--------|--------|
| T2a: delete VSYS F bar @y=104.48 | Free SW SE; unc unchanged (was dangling) |
| T1c: SW via →(111.55,104.55); F/B reconnect | Open west F PMID corridor; power stayed 0 |
| T3: TS west y=107.40→107.25 | Clear 3V3↔TS SaveBoard flake after T1c |

### Reverted
| Attempt | Why |
|---------|-----|
| T1 @111.60,104.90 | GND↔SW×3 vs U2.A5 |
| T1b @111.65,104.70 (with bar) | SW↔VSYS |
| T2 full C_SYS B dogbone reconnect | GND↔VSYS + 3V3_DISP↔VSYS short↑ |
| **T4** C_PMID F stitch @x=111.05 | shorting 0→6 (3V3_DISP↔VSYS/PMID, SCL↔TS); PMID↔VBUS/SW stayed 0 |
| T4b stitch + zone UnFill | shorting 5; island UNC cleared but shorts remain |
| T5 trim 3V3_DISP + B→C_LDO | shorting 0→5 (CD↔PMIC_INT, OPT↔BTN2, …) |

### C_PMID blockers (why stitch stopped)
1. **Pre-T west F:** impossible — VBUS@110.6 vs SW via@111.40,104.90 (hole_clearance 0.25).
2. **B east between SW·ILIM:** copper gap **0.225 mm**; need ≥0.40 for w=0.10+2×0.15 — **impossible**.
3. **Post-T1c west F:** corridor geometrically opens, but adding island→A3 copper still yields shorting↑ from pre-existing **3V3_DISP @y=106.0 vs C_VINLS.1 / VSYS @y=106.10** clearance debt (promoted to shorting_items once PMID copper continuous) plus SCL↔TS from T3 spine.
4. Next pass should **first** separate 3V3_DISP from C_VINLS/VSYS (without short↑), then retry T4; or relocate C_PMID further south/east outside the U2 pocket.

### Archives / scripts
- `e-ink-watch-backups/passt_topo_20260918_2045_s0.kicad_pcb`
- `e-ink-watch-backups/pre_passt_20260918_2041_s0.kicad_pcb`
- KEEP: `tools/_pass_t_02_vsys_bar_trim.py`, `_pass_t_01_sw_via_east.py`, `_pass_t_03_ts_jog.py`
- REVERTED stubs: `_pass_t_04_cpmid_stitch.py`, `_pass_t_05_trim_3v3disp.py`


---

## Pass-U (2026-09-18 ~20:46–20:52 IDT)

### Verdict
**Blocked — no net keep.** `shorting_items` **0 → 0** (hard gate held by reverting every edit).  
**3V3_DISP not isolated** from C_VINLS/VSYS. **C_PMID stitch not attempted** (isolation prerequisite failed).  
**C_PMID placement move** also raised shorts → reverted. Board identical to Pass-T end state.  
Unconnected **87 → 87**. **Not production-ready.**

### Commands
```bash
kicad-cli pcb drc --format report --output reports/drc_before_passu_20260918_2046.txt ...
# U1a–g isolate attempts — ALL REVERTED
# U2a C_PMID Δy=-1.5 — REVERTED
# U3 stitch — NOT RUN
kicad-cli pcb drc --format report --output reports/drc_after_passu_*.txt ...
```

### Before / after (Pass-U)

| Metric | Before | After |
|--------|--------|-------|
| shorting_items | **0** | **0** |
| DRC violations | **597** | **597** |
| unconnected | **87** | **87** |
| power-priority | **0** | **0** |
| PMID↔VBUS | **0** | **0** |
| 3V3_DISP isolated | **no** | **no** |
| C_PMID↔U2 | **no** | **no** |

### Reverted attempts
| Attempt | Result |
|---------|--------|
| U1a via@(112.05,106) + VSYS truncate | 3V3_DISP↔VSYS (via under jog); CD↔PMIC_INT; OPT↔BTN2 |
| U1b VSYS west-of-113 @y=105.60 | GND↔VSYS vs C_VINLS.2 |
| U1c VSYS south @y=104.70 x=113.4 | GND↔VSYS vs J_STRAP_R MP@(114,104.65) |
| U1d minimal VSYS end@112.5 + via@112.15 | 3V3_DISP↔VSYS |
| U1e via-on-C5 + B@y=106.55 | shorting 7 (CD↔PMIC_INT, PMID↔VSYS, SCL↔TS, OPT↔BTN2); 3V3_DISP↔VSYS/PMID cleared but gate fails |
| U1f delete-only F into C_VINLS | shorting 7 collateral (no new copper!) |
| U1g delete + zone UnFill | shorting 7; unc 87→120 (zones were stitching GND/3V3) |
| U2a C_PMID Δy=−1.5 + fanout | shorting 14 (GND↔PMID, EPD_BUSY_R↔PMID, …) |
| U3 stitch | **not run** |

### Why isolation is blocked (coords)
- **3V3_DISP** F @(111.800,106.000)→east overlaps **C_VINLS.1 PMID** bbox top y=106.00 @x=112.80
- **VSYS** F spine @y=**106.100** through x=111.8–117.4 grazes U2.C5 (actual clr **0.010 mm**)
- **C_VINLS.2 GND** @(112.800,105.320) blocks VSYS reroute @y=105.60
- **J_STRAP_R MP GND** @(114.000,104.650) size 1.2×2.0 blocks VSYS SE vertical near x=113.4
- **Only F.Cu + B.Cu** have tracks (board reports 4 copper layers but In1/In2 not used for signals)
- Delete-only / UnFill still surfaces collateral shorting_items — do not treat as “safe trim”

### Recommendations (do not auto-apply without DRC gate)
1. **Placement (preferred):** move **C_VINLS** ≈**+0.50 mm north** (or rotate) so pad1 clears 3V3_DISP @y=106.0 by ≥0.15; **or** move **C_PMID** further from U2 pocket with a planned escape (Δy=−1.5 alone hit EPD/GND).
2. **Placement:** nudge **VSYS** spine to y=**106.35–106.50** only after confirming clearance to U2.D5 GND@(111.8,106.4) and C_LDO — or fan B5 solely via y=105.60 east of x=113.5 then north outside MP.
3. **Layer:** enable/use **In1.Cu** for PMID dogbone island→A3 if stackup allows (currently no In tracks).
4. After (1), retry F west stitch island→A3 @x≈111.05 (SW via already @(111.55,104.55) from Pass-T).

### Archives / scripts
- `e-ink-watch-backups/passu_topo_*_s0.kicad_pcb` (= Pass-T state)
- `e-ink-watch-backups/pre_passu_20260918_2046_s0.kicad_pcb`
- Stubs only: `tools/_pass_u_01_isolate_3v3disp.py`, `_pass_u_02_cpmid_move.py`, `_pass_u_03_cpmid_stitch.py`


---

## Pass-V (2026-09-18 ~20:51–21:00 IDT)

### Verdict
**Blocked — no net keep.** `shorting_items` **0 → 0** (all edits reverted).  
User authorized footprint moves + standing RF/power/SPI/RTC rules.  
**C_VINLS not successfully relocated**; **C_PMID stitch not run**. Board = Pass-T end state.  
Unconnected **87 → 87**. **Not production-ready.**

### Coord note
On this board **+Y = south** (TP pogo ~y=114; J_DISP_MAIN ~y=85).  
“+0.5 mm north” ⇒ **Δy = −0.5**. Tried; **worsens** 3V3_DISP overlap because C_VINLS **pad1 PMID is the south pad** @y=106.28 (north edge on the 3V3_DISP rail @y=106.0).

### Before / after

| Metric | Before | After |
|--------|--------|-------|
| shorting_items | **0** | **0** |
| unconnected | **87** | **87** |
| power-priority | **0** | **0** |
| PMID↔VBUS | **0** | **0** |
| 3V3_DISP isolated | **no** | **no** |
| C_PMID↔U2 | **no** | **no** |

### Attempts (all reverted)
| Attempt | Result |
|---------|--------|
| Δy=−0.5 north (literal) | pad1→105.78 into 3V3_DISP; GND↔VSYS vs C_SYS |
| Δy=+0.5 south | 3V3_DISP↔PMID **cleared**; hit R_CD / GND dogbone↔3V3_DISP |
| South+east / rotate / C_LDO moves | shorting↑; hit C_LDO, R_LSCTRL, SW3, R_ILIM |
| C_VINLS @(112.5,104.7) by U2 (decoupling-friendly) | 3V3_DISP↔PMID **0**; GND↔VSYS vs C_SYS.1; PMID/GND fanout mash |
| C_SYS east + VSYS reroutes | MP/ILIM/SW collateral; power GND↔VSYS |
| Best intermediate V1o | power_ok, shorting 8 (PMID↔SW/VSYS, …) — still not 0; not kept |

### Standing rules respected
- Work stayed **east of U1** ~(100,93.5) — no copper under antenna / RF zone.
- Kept trying to park **C_VINLS/C_PMID near U2** (decoupling); far moves abandoned partly for that reason.
- No SPI/RTC/crystal edits.

### Recommendations (next pass)
1. **Manual KiCad session**: place C_VINLS on a **grid** with DRC live; candidate ~(112.5, 104.5) after **moving C_SYS** to ~(113.5, 103.5) and **shortening 3V3_DISP** so it ends west of x=112.3 (reconnect C_LDO on B @y≥107.2 clear of LSCTRL via@111.55).
2. Then **one** C_PMID island→A3 F stitch @x≈111.05 (SW via already @111.55,104.55).
3. Or enable **In1.Cu** PMID dogbone under the pocket (4L unused for signals today).
4. Do **not** literal-north C_VINLS without rotating so PMID pad is not the south pad on the rail.

### Archives / scripts
- `e-ink-watch-backups/passv_topo_*_s0.kicad_pcb` (= Pass-T)
- `e-ink-watch-backups/pre_passv_20260918_2051_s0.kicad_pcb`
- Stubs: `tools/_pass_v_01_cvinls_north.py`, `_pass_v_01b_fix_routes.py`, `_pass_v_02_cpmid_stitch.py`

---

## Pass-W (2026-09-18 ~21:20 IDT) — STOP / REVERT

### Goal
Pass-W sequence: C_SYS east → truncate 3V3_DISP → park C_VINLS ~(112.5,104.5) → one C_PMID island→A3 stitch (F @x≈111.05; else In1 once). Expanded auth: rearrange anything around U2.

### Baseline (Pass-T)
- Board md5 `496f90b1f20338721aabd526f5807709`
- DRC: **shorting=0**, unc=87, power-priority=0, PMID↔VBUS=0
- `reports/drc_before_passw_20260918_2102.txt`

### Tooling discovery (critical)
1. **pcbnew `SaveBoard` after `Add()` of new copper** can flip latent clearance into `shorting_items` (CD↔PMIC_INT, EPD_*, OPT↔BTN2, 3V3_DISP↔PMID) even for far-away stubs — **item order dependent**. Sexpr insert next to PMID via @(111.35,103.85) often keeps shorting=0; insert among GND segments can report shorting≥6 on identical geometry.
2. **`ZONE_FILLER` / `FillZones` must never run** — promotes 3V3_DISP↔VSYS etc.
3. **Via `SetWidth(nm)` without layer** serializes `(size 0.000002)` — use sexpr vias `(size 0.45) (drill 0.3)`.
4. **Track-only pcbnew remove+add** (Pass-T style) can keep shorting=0; **footprint `SetPosition` via pcbnew** wakes latent 3V3_DISP↔PMID into shorting even when geometry unchanged elsewhere.
5. Baseline **already has geometric overlap** 3V3_DISP @y=106.0 vs C_VINLS.1 PMID @y=106.28 — reported as clearance, not shorting, until board is “touched”.

### Attempts (all reverted; none kept)
| Step | Action | Result |
|------|--------|--------|
| W1 VSYS y=105.6 F bar | Hits C_VINLS GND + ILIM + MP | power fail |
| W2–2d place caps | South park clears 3V3_DISP↔PMID; fanouts/MP/R_* mash | shorting 8–14 |
| W2c J_STRAP_R +1.2 mm east | MP clears ILIM but SW↔GND / EPD↔MP | worse |
| W3–4 C_SYS by L_SYS + VSYS@106.5 | 3V3_DISP↔PMID=0; PMID→A4 SW mistake; VSYS↔R_ILIM | shorting 7–12 |
| W5 rebuild + F stitch @111.05 | unc 87→85; power_ok; stitch copper present | shorting 7 (PMID fanout through GND pad, VSYS B↔SW/ILIM) |
| W6–8 VSYS B / TS B-hop / CD B | Collateral TS/SCL/CD/LSCTRL; duplicate vias | shorting 11–14 |
| W10 atomic sexpr | 3V3_DISP↔PMID=0, ↔VSYS=0, unc=84, stitch in | shorting 10 |
| W11 fix | power_ok; PMID↔SW cleared; GND↔PMID from east fanout; VSYS B↔SW@115 | shorting 13 |
| In1 dogbone (early) | PMID↔SW under via column | fail |
| In1 west then F to A3 | PMID↔SW on F fanout | fail |
| Min move-only C_VINLS | Hits C_SYS; wakes CD/TS/ILIM | shorting 3–8 |

### What worked geometrically (but not DRC-gate)
- **C_VINLS @(112.50, 104.50)** (pad1 PMID south @104.98): **3V3_DISP↔PMID = 0**
- **Delete VSYS F bar @y=106.1** (L_SYS↔B5): clears 3V3_DISP↔VSYS when replaced carefully
- **C_SYS by L_SYS ~(117.5–118.2, 103.5–103.8)** frees U2 east pocket
- **Island→A3 F stitch** segments @(111.35,103.85)→(111.05,103.85)→(111.05,105.20)→(111.00,105.20) land without PMID↔VBUS

### Blockers for shorting=0 after placement
1. **J_STRAP_R MP GND @(114.0,104.65) 1.2×2.0** — blocks VSYS F and ILIM via; moving strap breaks EPD/SW
2. **SW via @(111.55,104.55)** — PMID fanout from C_VINLS south-park must go **east of ~112.9** then south (west path kisses SW)
3. **ILIM B @y≈105.35** — fights VSYS vias/B hops under U2–L_SYS
4. **CD @y=106.8 vs PMIC_INT @y=106.7 @x=110.6** — real overlap; waking DRC demands fix whenever board is edited
5. **TS @y=107.25–107.30 vs R_SCL / R_SDA** — same
6. **OPT(TP6)↔BTN2 on B** — appears when B.Cu VSYS added (order/zone interaction)

### C_PMID connected?
**No** on reverted board. Stitch was present on W10/W11 working trees but never kept (shorting≠0).

### Deliverables
- Scripts: `tools/_pass_w_sexpr_lib.py`, `_pass_w_01_vsys_y1056.py`, `_pass_w_02*.py`, `_pass_w_03_pocket.py`, `_pass_w_04_fix_shorts.py`, `_pass_w_05_rebuild.py`, `_pass_w_06_fix.py`, `_pass_w_07_fix.py`, `_pass_w_08_cleanup.py`, `_pass_w_10_atomic.py`, `_pass_w_11_fix.py`, `_pass_w_min*.py`
- DRC: `reports/drc_before_passw_20260918_2102.txt`, `reports/_drc_passw_*.txt`, `reports/drc_after_passw_*_reverted.txt`
- Archive: `e-ink-watch-backups/passw_reverted_*_s0.kicad_pcb` (= Pass-T)

### Verdict
**Pass-W incomplete — REVERTED.** Hard gate (shorting=0 after kept step) could not be held while parking C_VINLS and stitching C_PMID. Recommend interactive KiCad session: (1) fix CD/PMIC_INT + TS/SCL clearances first so DRC wake-ups don’t flood, (2) ease or move J_STRAP_R MP, (3) C_SYS to L_SYS, C_VINLS @(112.5,104.5) with **east** PMID escape, (4) VSYS on B clear of SW via @x=115, (5) then F stitch @x=111.05.

### Coord reminder
+Y = south. C_VINLS pad1 PMID is **south** pad — do not “north” it onto 3V3_DISP @y=106.0.

## Pass-X — 2026-09-18 (SUCCESS)

### Goal
Re-apply Pass-W pocket geometry; **fix shorts in place** (no full-revert of good placement). Success = shorting 0 + C_VINLS clear of 3V3_DISP; ideally C_PMID stitched.

### Before → After
| Metric | Pass-T | Pass-X |
|--------|--------|--------|
| shorting | 0 | **0** |
| unconnected | 87 | **84** |
| power-priority pairs | 0 | **0** |
| PMID↔VBUS | 0 | **0** |
| 3V3_DISP↔PMID | (blocked by C_VINLS@112.8,105.8) | **0** |
| C_PMID↔U2 | no | **yes** (F @x≈111.05) |

### Positions kept
| Part | Position | Notes |
|------|----------|-------|
| C_VINLS | (112.50, 104.50) | pad1 PMID south @104.98 |
| C_SYS | (117.80, 103.60) | by L_SYS |
| C_PMID | (112.20, 103.40) | stitched |
| C_LDO | (113.50, 106.80) | home |
| R_SDA | (109.95, 108.10) | south of GND column |

### What was fixed vs reverted (per-step)
- **Kept:** VSYS B-hop past MP; ILIM via east; PMID west fanout; GND ghost delete; TS stub shorten; CD fanout strip; LSCTRL north micro-via; BTN2 local jog; F stitch @111.05
- **Locally reverted:** R_SCL/R_SDA south cascades; BTN2 at x=96.4 (hit GND/VBAT/TP5); GND B-hop vias at R_SDA; LSCTRL south/west fanouts that hit CD/SCL; failed stitch attempts before shorting=0
- **Not full-reverted** once C_VINLS/C_SYS parked — followed user policy

### C_PMID connected?
**Yes.** Island via @(111.35,103.85) ↔ U2 A3 via F column @x=111.05. shorting stayed 0; unc 85→84.

### Deliverables
- `tools/_pass_x_sexpr_lib.py`, `_pass_x_46_pocket.py`, `_pass_x_28`…`_pass_x_55*`, `_pass_x_final_summary.py`
- `reports/_drc_passx_*.txt`, `reports/drc_after_passx.txt`
- `backups/_passx_final_shorting0_stitched.kicad_pcb`, `_passx_shorting0_pocket.kicad_pcb`, `_passx_session_base.kicad_pcb`

### Verdict
**SUCCESS.** shorting=0 with improved pocket and C_PMID stitched. Live board = Pass-X final.

## Pass-Y — 2026-09-18 (unc cut)

### Goal
Reduce unconnected_items from Pass-X **84** while keeping shorting=0, power-priority=0, C_PMID stitch.

### Triage (before)
| Category | Count | Notes |
|----------|------:|-------|
| power | 49 | Many GND/3V3/3V3_DISP island pairs (zone-starved) + real missing ties |
| spi_disp | 16 | EPD_* track/via islands |
| swd | 9 | SWDIO/SWDCLK/nRESET / pogo |
| btn_tp | 3 | BTN via missing |
| other | 7 | TS, CD, dangling |

### Before → After
| Metric | Before | After |
|--------|--------|-------|
| shorting | 0 | **0** |
| unconnected | 84 | **63 (−21)** |
| PMID annular @111.35,103.85 | fail 0.075 | **pass** (size 0.5) |
| C_PMID stitch | yes | **yes** |

### Kept copper (safe gates)
C_VINLS/C_SYS/R_CD–C_LDO GND; IPRETERM via-under-pad; 3V3_DISP via@(113,106); R_ILIM GND via;
R_ISET GND; BTN1/2/3 layer joins; 3V3 U1-area via link; VBAT west via; SW3 GND; U1 GND stitches; LSCTRL/TS clearance tweak.

### Reverted / blocked
- Blind FillZones → shorting (EPD_RST↔BUSY, ILIM↔TS, LSCTRL↔SDA)
- VSYS↔R_VSYS B routes (PMID/GND/3V3 via collisions)
- ISET/CD/TS/VBAT through U2 pocket (too dense)
- Aggressive SDA reroutes (BTN3/GND collisions)
- Some J_STRAP / J_DISP GND bars (hit adjacent pads)

### Remaining unc (~63) top categories
1. **power_island** — same-net pads/vias not joined without zone pour (U2 A5↔D5, J_STRAP 3V3_DISP p1↔p10, etc.)
2. **spi_disp** — EPD_* multi-island (~16)
3. **swd** — SWDIO/CLK/nRESET + pogo (~9)
4. **pmic_signal** — ISET, TS, CD still open by design of Pass-X strip / density

### Verdict
**Partial success.** Meaningful unc drop 84→63 with hard gates held. Further cuts need interactive zone fill with local clearance fixes, or dedicated Pass-Z for SPI/SWD islands.

## Pass-Z — 2026-09-18 (unc cut)

### Goal
Cut remaining SPI (~16), SWD (~9), power_island (~30) unconnected with explicit copper (no blind FillZones). Keep shorting=0, power-priority=0, PMID↔VBUS=0, C_PMID stitch.

### Before → After
| Metric | Pass-Y | Pass-Z |
|--------|--------|--------|
| shorting | 0 | **0** |
| unconnected | 63 | **35 (−28)** |
| power-priority | 0 | **0** |
| PMID↔VBUS | 0 | **0** |
| C_PMID stitch | yes | **yes** |
| md5 | baf1d288f22feb15aec3dca864defd23 | **01cc759d19eb5eefaa6bca21ef716c8d** |

### Kept copper (highlights)
- **SWD complete:** pogo vias + SWDIO/SWDCLK/nRESET U1↔header/pogo (SW_DBG topology kept)
- **SPI:** EPD_SCK (U1 VIP+B east + L↔R B bridge @y=94.5 + F west), EPD_MOSI B-hops, EPD_CS_L/R/MAIN, EPD_BUSY_R, EPD_DC east, EPD_RST B @y=89
- **Power:** selective GND/3V3/3V3_DISP explicit stitches; removed landmine 3V3_DISP F @x=116.85
- **pmic:** TS short hop only (CD/ISET/TS2 blocked — LSCTRL↔SDA / pocket)

### Reverted / blocked
| Item | Why |
|------|-----|
| Blind FillZones | Not attempted (Pass-Y woke shorts) |
| 3V3_DISP F vertical x=116.85 | Crosses GND@y=102.25 + SPI fanouts; intermittent shorting |
| EPD_DC local F | Wakes latent RST↔BUSY_MAIN (centers ~0.15 mm) |
| EPD_BUSY_L | B congested (SWDCLK/BTN/CS_L) |
| ISET/CD/VBAT/VSYS | U2 pocket; CD wakes LSCTRL↔SDA |
| RST left island | SDA/SCL vias on B @y≈89 |

### Remaining (~35)
1. **power_island ~28** — same-net islands needing pours or long corridors (GND/3V3/3V3_DISP/VBAT/VSYS/SDA/SCL/PMIC_INT)
2. **spi_disp ~4** — EPD_DC local+left, EPD_RST left, EPD_BUSY_L
3. **pmic_signal ~3** — TS (2nd island), CD, ISET

### Deliverables
- `tools/_pass_z_sexpr_lib.py`, `tools/_pass_z_gate.py`
- `reports/drc_before_passz_20260918_2202.txt`, `reports/drc_after_passz.txt` (+ json), `reports/_drc_passz_*.txt`
- `backups/_passz_final_unc35_shorting0_01cc759d19eb.kicad_pcb`, `_passz_final.kicad_pcb`, `_passz_last_ok.kicad_pcb`, `_passz_session_base.kicad_pcb`

### Verdict
**Partial success.** Large unc cut 63→35 with all hard gates held. Next: fix RST↔BUSY_MAIN clearance (~0.15 mm @x=100.75/100.9), then DC local; interactive zone fill with immediate DRC revert; U2 pocket signals only with LSCTRL↔SDA watch.

## Pass-AA — 2026-09-18 (unc cut)

### Goal
Continue from Pass-Z (unc≈35): explicit power stitches, clear EPD after fixing RST↔BUSY_MAIN, pmic only if safe from LSCTRL↔SDA.

### Before → After
| Metric | Pass-Z | Pass-AA |
|--------|--------|---------|
| shorting | 0 | **0** |
| unconnected | 35 | **21 (−14)** |
| power-priority / PMID↔VBUS | 0 | **0** |
| C_PMID stitch | yes | **yes** |
| md5 | 01cc759d… | **b53606a120e3503145c957b169a3286b** |

### Key unlock
**AA1:** Reworked EPD_BUSY_MAIN to pad-8 column @x=101.25 (was @x=100.9), clearing ~0.15 mm RST↔BUSY_MAIN latent that blocked DC local.

### Kept highlights
DC local + DC left; BUSY_L; 3V3_DISP top/east/long B stitches; GND J_DISP + left B; 3V3 west B; CD (F, fragile); removed TS-column GND landmine.

### Remaining (21)
| Cat | ~n | Items |
|-----|---:|-------|
| power_island | 18 | GND U2 pocket, 3V3/3V3_DISP longs, VBAT, VSYS, SDA, SCL, PMIC_INT |
| spi_disp | 1 | EPD_RST left (87.35↔104) |
| pmic_signal | 2 | TS 2nd island, ISET |

### Irreducible / blocked
- **EPD_RST left:** no F/B corridor past SDA/SCL/GND/BUSY_L/MOSI
- **ISET/TS:** U2 pocket (ILIM/IPRETERM/PMID); adjacent pads
- **VBAT/VSYS:** same pocket; VSYS B hits PMID stitch via
- **CD:** connected on F but tracks_crossing LSCTRL/SCL/SDA; C_LDO clearance tight — do not edit nearby without CD rebuild
- **In1/In2:** power planes only — not for signal stitches

### Deliverables
- `tools/_pass_aa_sexpr_lib.py`, `tools/_pass_aa_gate.py`
- `reports/drc_before_passaa_20260918_2227.txt`, `reports/drc_after_passaa.txt` (+json)
- `backups/_passaa_final_unc21_shorting0_b53606a120e3.kicad_pcb`

### Verdict
**Partial success.** unc 35→21 with gates held. Next: interactive KiCad for RST left + U2 pocket (CD/LSCTRL/ISET) and controlled zone fill with immediate DRC revert.

## Pass-AB (footprint moves) — 2026-09-18 ~23:30 IDT

| | Before (AA) | After (AB) |
|--|--|--|
| unc | 21 | **19** |
| shorting | 0 | **0** |
| md5 | b53606a120e3503145c957b169a3286b | bd3de38dbce0f369764f841b889ad75f |

### Moved footprints
| Ref | From | To |
|--|--|--|
| C_BAT | (108.6, 105.8) | **(107.5, 108.8)** |
| C_SYS | (117.8, 103.6, 90) | **(118.2, 103.6, 90)** |
| R_CD | (112.8, 107.75, 90) | **(113.5, 107.75, 90)** |

### Moved vias
| Net | From | To |
|--|--|--|
| ILIM | (110.75, 106) | **(111.3, 105.6)** |
| LSCTRL | (110.35, 107.2) | **(110.8, 107.8)** |

### Cleared nets
- EPD_RST left (SPI leftover from AA)
- VBAT U2 corridor
- 3V3↔R_VSYS pad2 (north stub)
- LSCTRL fanout after via move

### Remaining (19) — likely hard without bigger U2 pocket tear-up
1–7 GND (U2 A5↔D5 + J_STRAP/SW3)
8–10 3V3 (local near CD; R_VSYS south island; MCU west)
11–13 3V3_DISP
14 VSYS (R_VSYS↔U2 B5; corridor blocked by VBAT/PMID/GND)
15–16 SDA/SCL (long haul; mid-vias removed for RST)
17 PMIC_INT
18 TS (C3 center; ILIM/IPRETERM/PMID ring)
19 ISET (R_ISET↔C1 through GND/VBUS mesh)

### Gates
shorting=0, power-priority=0, PMID↔VBUS=0, C_PMID stitch kept, no blind FillZones.

## Pass-AC (coordinated U2 pocket) — 2026-09-18 ~24:05 IDT

| | Before (AB) | After (AC) |
|--|--|--|
| unc | 19 | **20** (+1) |
| shorting | 0 | **0** |
| md5 | bd3de38dbce0… | 019e9718136d… |

Moves: R_ISET→(109.2,102.5); R_TS→(108,107); R_VSYS→(105,104.5,90); C_SYS→(118.5,104,90); R_SDA→(111.5,109); R_SCL→(111.65,107.4); ILIM via→(110.9,105.9).

Verdict: geometry opened; unc +1; ISET one VBUS-clearance away. C_PMID stitch kept.

## Pass-AD — stitch on AC placement (2026-09-19 IDT)

| | |
|--|--|
| From | Pass-AC unc=20 shorting=0 `019e9718136d178f5fa0d65d31c5e4db` |
| To | unc=**16** shorting=0 `16216c1cb799038166a91b2ff437b630` |
| Delta | **−4 unc** (goal was &lt;19) |
| Gates | shorting=0, power=0, PMID↔VBUS=0, C_PMID kept |

### Stitched
1. **ISET** → U2.C1 (R_ISET rot90 @101.5 + B-hop)
2. **VSYS** → U2.B5 island (R_VSYS @103.8 + B north-wrap to x=116)
3. **TS** → U2.C3 (ILIM via nudge + B under VBAT row)
4. **R_SCL 3V3** after SCL nudge to (112.0,107.8)

### Remaining (16)
GND×8, 3V3×2, 3V3_DISP×3, SDA, SCL, PMIC_INT

### Paths (key)
- ISET: pad2(109.2,100.99) → B(108.2,*) → via(109.5,106) → F → C1
- VSYS: pad(105,104.625) → B(106.8,100.3)→(116,100.3)→(116,105.6)
- TS: pad(108.51,107) → B(107.8,105.65)→via(110.4,105.65) → F → C3

### Honest verdict
Pass goal met. CD rebuild and under-BGA GND / long hauls still irreducible without larger rearrange or zone strategy.

## Pass-AE — post-AD islands (2026-09-19 IDT)

| | |
|--|--|
| From | Pass-AD unc=16 `16216c1cb799038166a91b2ff437b630` |
| To | unc=**12** shorting=0 `aca702a4a25cdde40051f848a2abd47a` |
| Delta | **-4 unc** (goal <16 met; <=10 not reached) |
| Gates | shorting=0, power=0, PMID↔VBUS=0, C_PMID + ISET/VSYS/TS kept |

### Stitched
1. C_SYS GND (B east-wrap)
2. 3V3_DISP east island to C5
3. J_STRAP_L GND
4. 3V3 north (U1 area)
5. Clearances: BTN1/OPT, TP6 move, CD west of R_CD

### Remaining (12)
GND A5-D5 + strap-R + SW3; mid 3V3; west 3V3_DISP x2; SDA/SCL hauls; PMIC_INT

### Honest verdict
Good progress on same-net power. I2C hauls and under-BGA GND need dedicated pass.
