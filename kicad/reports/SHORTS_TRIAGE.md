# SHORTS_TRIAGE — power-first

**Дата:** 2026-09-18 13:05 IDT (Asia/Jerusalem, UTC+3)  
**Источник:** `reports/drc_net_audit_final.txt`  
**DRC:** 1107; **shorting_items:** 199; **unique pairs:** 78

> INTENT_BRIDGE = ожидаемо через компонент (FB1, L_SYS, R_VSYS, R_TS, NTC). Не резать вслепую.

## Top 10 power shorts

| # | Net A | Net B | × | Class | Why |
|---|-------|-------|---|-------|-----|
| 1 | GND | VBUS | 11 | SHORT | КЗ зарядки на землю — hot pogo / дым |
| 2 | GND | VBAT | 8 | SHORT | КЗ батареи — PCM trip / риск без PCM |
| 3 | 3V3_DISP | GND | 6 | SHORT | КЗ rail дисплея |
| 4 | 3V3 | GND | 2 | SHORT | КЗ MCU rail |
| 5 | 3V3_DISP | VBAT | 2 | SHORT | смешение доменов |
| 6 | GND | VBUS_POGO | 2 | SHORT | КЗ входа cradle |
| 7 | TS | VBAT | 2 | SHORT | ломает JEITA / charge |
| 8 | 3V3 | VBAT | 1 | SHORT | смешение 3V3/BAT |
| 9 | GND | SW | 1 | SHORT | шунт buck SW node |
| 10 | 3V3 | 3V3_DISP | 9 | SHORT | LDO bypass / домены слиплись |

## Полный ranked list (power-involved)

| Net A | Net B | × | Class |
|-------|-------|---|-------|
| GND | VBUS | 11 | PWR↔PWR |
| GND | VBAT | 8 | PWR↔PWR |
| 3V3_DISP | GND | 6 | PWR↔PWR |
| 3V3 | GND | 2 | PWR↔PWR |
| 3V3_DISP | VBAT | 2 | PWR↔PWR |
| GND | VBUS_POGO | 2 | PWR↔PWR |
| TS | VBAT | 2 | PWR↔PWR |
| 3V3 | VBAT | 1 | PWR↔PWR |
| GND | SW | 1 | PWR↔PWR |
| 3V3 | 3V3_DISP | 9 | PWR↔PWR |
| 3V3_DISP | PMID | 4 | PWR↔PWR |
| 3V3_DISP | VSYS | 4 | PWR↔PWR |
| 3V3_DISP | VINLS | 1 | PWR↔PWR |
| GND | TS | 3 | INTENT_BRIDGE |
| VBUS | VBUS_POGO | 1 | INTENT_BRIDGE |
| SW | VSYS | 1 | INTENT_BRIDGE |
| BTN1 | VBUS | 4 | PWR↔SIG |
| BTN3 | GND | 3 | PWR↔SIG |
| EPD_SCK | GND | 3 | PWR↔SIG |
| GND | PMIC_INT | 3 | PWR↔SIG |
| EPD_BUSY_L | GND | 2 | PWR↔SIG |
| EPD_MOSI | GND | 2 | PWR↔SIG |
| EPD_RST | GND | 2 | PWR↔SIG |
| GND | ISET | 2 | PWR↔SIG |
| GND | SWDIO | 2 | PWR↔SIG |
| GND | nRESET_POGO | 2 | PWR↔SIG |
| BTN3 | VBAT | 1 | PWR↔SIG |
| CD | VBUS | 1 | PWR↔SIG |
| EPD_BUSY_MAIN | GND | 1 | PWR↔SIG |
| EPD_CS_R | GND | 1 | PWR↔SIG |
| GND | ILIM | 1 | PWR↔SIG |
| GND | IPRETERM | 1 | PWR↔SIG |
| GND | LSCTRL | 1 | PWR↔SIG |
| SWDCLK_POGO | VBAT | 1 | PWR↔SIG |
| 3V3 | SCL | 7 | PWR↔SIG |
| 3V3 | CD | 2 | PWR↔SIG |
| 3V3 | EPD_BUSY_MAIN | 2 | PWR↔SIG |
| 3V3 | SWDCLK_POGO | 2 | PWR↔SIG |
| ILIM | PMID | 2 | PWR↔SIG |
| 3V3 | BTN3 | 1 | PWR↔SIG |
| 3V3 | LSCTRL | 1 | PWR↔SIG |
| 3V3_DISP | IPRETERM | 1 | PWR↔SIG |
| 3V3_DISP | SWDCLK_POGO | 1 | PWR↔SIG |
| 3V3_DISP | nRESET | 1 | PWR↔SIG |
| PMIC_INT | TS | 1 | PWR↔SIG |

## Исправлено в этом аудите

| Пара | Было → стало |
|------|--------------|
| VBAT ↔ VBUS | ≥1 → **0** |
| VBUS на TP1 (обход FB1) | был → **удалён** |
| VBUS ↔ VBUS_POGO | много → **×1** (вероятно pads FB1) |

## Не чинили (неоднозначно)

- GND↔VBUS у C_IN (fat track / pad clearance)  
- GND↔VBAT cluster  
- 3V3↔3V3_DISP, EPD*↔GND, BTN1↔VBUS — плотная F.Cu  
- 0 copper zones → многие shorts = пересечения треков

## Порядок ремонта

1. Power: GND↔VBUS, GND↔VBAT, PMID↔VBUS, GND↔SW  
2. Domains: 3V3↔VBAT, 3V3_DISP↔VBAT, 3V3↔3V3_DISP  
3. Sensors: TS↔VBAT, GND↔TS  
4. Debug: BTN*/SWD*↔power  
5. EPD signal↔GND  
6. Silk/mask/courtyard

## Charge path OK?

**НЕТ для подачи питания.** Pad topology OK; copper **GND↔VBUS ×11**.

**Не fab-ready.**
