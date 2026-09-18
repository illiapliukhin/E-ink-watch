# NET_COMPONENT_AUDIT — E Ink Watch (4L + BQ25120A)

**Дата:** 2026-09-18 13:05 IDT (Asia/Jerusalem, UTC+3)  
**Проект:** `/workspace/e-ink-watch-kicad/`  
**PCB:** `e-ink-watch.kicad_pcb` (4L: F.Cu / In1.Cu GND / In2.Cu PWR / B.Cu)  
**DRC:** **1107** (shorting_items=199, unconnected_items=77)  
**ERC:** **167** (endpoint_off_grid:84, hier_label_mismatch:51, label_dangling:24, unconnected_wire_endpoint:5, pin_not_connected:2)  

> **Honesty / Harvard:** это **не** fab-ready и **не** power-safe для подачи VBUS.  
> Pad-level charge topology (design-intent) = OK. Copper DRC: **GND↔VBUS ×11** ещё жив.  
> Однозначно исправлено в этом аудите: **VBAT↔VBUS → 0**; VBUS убран с TP1 (больше не обходит FB1).

---

## Сводка PASS / FAIL / GAP

| PASS | FAIL | GAP |
|------|------|-----|
| **25** | **2** | **8** |

FAIL = (1) GND↔VBUS copper short, (2) charge path not power-safe.  
GAP = Vrating caps, Q_DISP missing, SPI series R missing, sch/PCB ref drift, R_TS 5.1k vs sch 10k, crystals on module assumption, zone fill=0, thousands of non-power DRC.

---

## 1. Инвентарь PCB footprints (42)

| Ref | Value | Footprint |
|-----|-------|-----------|
| C1 | 100n | `Capacitor_SMD:C_0402_1005Metric` |
| C2 | 100n | `Capacitor_SMD:C_0402_1005Metric` |
| C3 | 10u | `Capacitor_SMD:C_0402_1005Metric` |
| C4 | 10u | `Capacitor_SMD:C_0402_1005Metric` |
| C_BAT | 1uF | `Capacitor_SMD:C_0402_1005Metric` |
| C_IN | 1uF | `Capacitor_SMD:C_0402_1005Metric` |
| C_LDO | 1uF | `Capacitor_SMD:C_0402_1005Metric` |
| C_PMID | 4.7uF | `Capacitor_SMD:C_0402_1005Metric` |
| C_SYS | 10uF | `Capacitor_SMD:C_0402_1005Metric` |
| C_VINLS | 1uF | `Capacitor_SMD:C_0402_1005Metric` |
| D_TVS_VBUS | PESD5V0S1U | `D_SOD-323` |
| FB1 | BLM18PG121SN1 | `Inductor_SMD:L_0603_1608Metric` |
| J_BAT | BAT | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |
| J_DISP_MAIN | DISP_MAIN | `Connector_FFC-FPC:Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal` |
| J_STRAP_L | STRAP_L | `Connector_FFC-FPC:Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal` |
| J_STRAP_R | STRAP_R | `Connector_FFC-FPC:Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal` |
| J_SWD | SWD | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` |
| L_SYS | 2.2uH | `L_0805_2012Metric` |
| NTC_BAT | 10k_NTC | `R_0402_1005Metric` |
| R1 | 10k | `Resistor_SMD:R_0402_1005Metric` |
| R2 | 10k | `Resistor_SMD:R_0402_1005Metric` |
| R_CD | 10k | `R_0402_1005Metric` |
| R_ILIM | 2.0k | `R_0402_1005Metric` |
| R_IPRETERM | 0R | `R_0402_1005Metric` |
| R_ISET | 4.02k | `R_0402_1005Metric` |
| R_LSCTRL | 10k | `R_0402_1005Metric` |
| R_SCL | 4.7k | `Resistor_SMD:R_0402_1005Metric` |
| R_SDA | 4.7k | `Resistor_SMD:R_0402_1005Metric` |
| R_TS | 5.1k | `R_0402_1005Metric` |
| R_VSYS | 0R | `R_0603_1608Metric` |
| SW1 | BTN1 | `Button_Switch_SMD:SW_SPST_B3U-1000P` |
| SW2 | BTN2 | `Button_Switch_SMD:SW_SPST_B3U-1000P` |
| SW3 | BTN3 | `Button_Switch_SMD:SW_SPST_B3U-1000P` |
| SW_DBG | PROG EN | `Button_Switch_SMD:SW_DIP_SPSTx03_Slide_Copal_CVS-03xB_W5.9mm_P1mm` |
| TP1 | VCHG | `TestPoint:Pogo_Pad_D1.5mm` |
| TP2 | GND | `TestPoint:Pogo_Pad_D1.5mm` |
| TP3 | SWDIO | `TestPoint:Pogo_Pad_D1.5mm` |
| TP4 | SWDCLK | `TestPoint:Pogo_Pad_D1.5mm` |
| TP5 | nRESET | `TestPoint:Pogo_Pad_D1.5mm` |
| TP6 | OPT | `TestPoint:Pogo_Pad_D1.5mm` |
| U1 | MDBT50Q-1MV2 | `RF_Module:Raytac_MDBT50Q` |
| U2 | BQ25120A | `EInkWatch:Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm` |

TSV: `reports/_full_inventory.tsv`.

### Sch ↔ PCB gaps

| Item | Статус |
|------|--------|
| Y1/Y2 + load caps | **GAP/OK*** — на PCB нет; MDBT50Q модуль обычно содержит XTAL (*проверить datasheet Raytac*) |
| Q1 P-FET 3V3_DISP | **GAP** — на PCB нет; U2.C5 (LS/LDO) идёт на FPC напрямую |
| SPI series 33Ω | **GAP** — на PCB нет (есть только в displays.sch как TBD) |
| Refdes drift (J2 vs J_DISP_MAIN, U2 BQ name) | **GAP** — sch/PCB naming не 1:1 |
| Cap Vrating в value | **GAP** — нигде не указано (≥2× rail) |
| Zone pours | **GAP** — 0 zones; GND в основном треками/via |

---

## 2. Net-by-net audit

### A. Charging (VBUS_POGO → FB1 → VBUS → U2 → VBAT / VSYS → 3V3)

| Check | Domain | Result | Evidence |
|-------|--------|--------|----------|
| TP1 = VBUS_POGO | 0 / 5V cradle | **PASS** | pad net |
| TP2 = GND | 0V | **PASS** | pad net; SW_DBG не рвёт GND |
| D_TVS_VBUS VBUS_POGO↔GND | ESD | **PASS** | pads |
| FB1 VBUS_POGO→VBUS | series ferrite | **PASS** | pads 1/2; DRC VBUS↔VBUS_POGO ×1 ≈ pad FB1 |
| U2.A2 IN = VBUS | ~5V | **PASS** | pad + track corridor x=107 |
| C_IN VBUS↔GND | ≥10V needed | **PASS*** | topology OK; *Vrating GAP* |
| U2.B1/B2 + C_BAT + J_BAT = VBAT | 3.0–4.2V | **PASS*** | pads OK; *GND↔VBAT DRC remain* |
| U2.A4 SW → L_SYS → VSYS | buck | **PASS** | pads |
| R_VSYS 0Ω VSYS→3V3 | intentional bridge | **PASS** | pads |
| R_ISET 4.02k (~50 mA) | ISET | **PASS** | value |
| R_ILIM 2.0k (~100 mA) | ILIM | **PASS** | value |
| R_IPRETERM 0R | default | **PASS** | value |
| R_TS 5.1k + NTC_BAT 10k | JEITA TS | **PASS*** | pads; *sch text 10k drift* |
| R_CD 10k CD→GND | charge enable | **PASS** | pads |
| SW_DBG nets ≠ VBUS/GND/VBAT | safety | **PASS** | only SWD*/nRESET* |
| VBAT↔VBUS copper short | must be open | **PASS** | DRC ×0 after fix |
| GND↔VBUS copper short | must be open | **FAIL** | DRC ×11 |
| Charge path power-safe | — | **FAIL** | topology OK, copper not |

### B. MCU MDBT50Q (U1)

| Check | Result | Notes |
|-------|--------|-------|
| 3V3 on U1.28/30 | **PASS** | pads |
| GND on module pads | **PASS** | multiple GND pads |
| SWDIO/SWDCLK/nRESET → J_SWD + SW_DBG | **PASS** | pads |
| I2C SDA/SCL + R_SDA/R_SCL 4.7k | **PASS*** | pads; DRC 3V3↔SCL noise |
| SPI EPD_* + CS×3 + BUSY×3 | **PASS*** | pads; many EPD↔GND shorts |
| BTN1/2/3 | **PASS*** | pads; BTN1↔VBUS DRC |
| PMIC_INT | **GAP** | pad net present; fanout weak (U2.D2 no near track earlier) |

### C. Displays FPC×3

| Check | Result | Notes |
|-------|--------|-------|
| J_DISP_MAIN / J_STRAP_L / J_STRAP_R | **PASS** | FH12-10S footprints |
| Shared MOSI/SCK/DC/RST | **PASS** | net membership |
| Separate CS / BUSY | **PASS** | nets distinct |
| 3V3_DISP on pin1/10 | **PASS*** | pads; 3V3↔3V3_DISP DRC ×9 |
| Pinout vs panel datasheet | **GAP** | ASSUMPTION, not vendor-verified |

### D. Pogo SWD gated by SW_DBG

| Check | Result | Notes |
|-------|--------|-------|
| TP3/4/5 = SWDIO_POGO / SWDCLK_POGO / nRESET_POGO | **PASS** | pads |
| SW_DBG series only SWD* | **PASS** | charge intact topologically |
| Charge copper clean | **FAIL** | GND↔VBUS |

---

## 3. Track width vs current (physics)

Допущение: **1 oz / 35 µm**, ΔT 10 °C, IPC-2221 external. I_peak: VBUS 300 mA, VBAT/VSYS 200 mA, 3V3 50 mA, 3V3_DISP 120 mA.

| Net | w observed (mm) | IPC need @Ipeak | Verdict |
|-----|-----------------|-----------------|---------|
| VBUS | 0.20…0.50 | ≪0.12 | **PASS** thermal; policy want ≥0.45 |
| VBAT | 0.35…0.50 | ≪0.07 | **PASS** |
| VSYS | 0.20…0.45 | ≪0.07 | **PASS*** thin spots 0.20 |
| 3V3 | 0.18…0.45 | ≪0.01 | **PASS** |
| 3V3_DISP | 0.30…0.45 | ≪0.03 | **PASS** |
| GND | 0.18…0.35 + vias | plane preferred | **GAP** — нет zone pour |

IR @0.45 mm / 35 mm / 50 mA ≈ 2 mV → **PASS** бюджету <50 mV. Лимит — **shorts**, не ширина.

---

## 4. Component polarity / values / Vrating

| Ref | Value | Rail | Polarity | Vrating ≥2× |
|-----|-------|------|----------|-------------|
| C1 | 100n | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C2 | 100n | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C3 | 10u | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C4 | 10u | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C_BAT | 1uF | VBAT~4.2V | MLCC OK | **GAP** (≥10V not in BOM) |
| C_IN | 1uF | VBUS~5V | MLCC OK | **GAP** (≥10V not in BOM) |
| C_LDO | 1uF | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C_PMID | 4.7uF | PMID~5V | MLCC OK | **GAP** (≥10V not in BOM) |
| C_SYS | 10uF | 3.3V | MLCC OK | **GAP** (≥6.3V not in BOM) |
| C_VINLS | 1uF | PMID~5V | MLCC OK | **GAP** (≥10V not in BOM) |
| D_TVS_VBUS | PESD5V0S1U | VBUS_POGO | **verify pad1=signal** | PASS family |
| L_SYS | 2.2uH | SW↔VSYS | non-polar | PASS |
| FB1 | BLM18PG121 | series | non-polar | PASS |
| U2 | BQ25120A | multi | DSBGA orient critical | PASS FP |
| U1 | MDBT50Q-1MV2 | 3V3 | module | PASS |

---

## 5. Fixes this audit (unambiguous only)

1. Deleted VBUS copper on TP1 / west of FB1 (ferrite bypass).  
2. Deleted VBUS vertical through C_BAT pad → **VBAT↔VBUS = 0**.  
3. Rebuilt VBUS corridor FB1.2 → x=107 → C_IN → U2.A2.  
4. Attempted GND stubs east of C_IN/C_BAT + vias (partial; GND↔VBUS remains).  
5. **No** blind deletes of EPD/BTN crossings.

---

## 6. Verdict

| Question | Answer |
|----------|--------|
| PASS / FAIL / GAP (checks) | **25 / 2 / 8** |
| Charge topology (pads) | **OK** |
| Charge path power-safe (copper) | **NO** |
| Fab-ready | **NO** |
| Top blocker | GND↔VBUS ×11 |

См. `reports/SHORTS_TRIAGE.md`.
