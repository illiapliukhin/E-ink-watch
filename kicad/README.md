# E Ink Watch — проект KiCad 8/9 (концепт, BLE-only)

Иерархическая схема носимых часов с монохромным E Ink (циферблат + 2 экрана в ремешке).
**NFC отсутствует:** обмен с телефоном и передача тем — только по **BLE** через nRF52840.

> Это **концепт-схема**, не production-ready. Все footprint помечены `TBD`.

## Как открыть в KiCad 8 / 9

1. Установите [KiCad 8](https://www.kicad.org/) или 9.
2. **File → Open Project…** и выберите:
   `/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pro`
   (на Windows после CopyFromBox — путь к скопированной папке).
3. Откроется корневой лист `e-ink-watch.kicad_sch` с иерархическими блоками.
4. Двойной клик по прямоугольнику листа — вход в дочерний sheet.
5. Локальная библиотека символов: `libraries/EInkWatch.kicad_sym` (подключена через `sym-lib-table`).

Генератор (для пересборки): `python3 tools/gen.py`.

## Карта листов

| Файл | Содержание |
|------|------------|
| `e-ink-watch.kicad_sch` | Корень: связи между блоками |
| `power.kicad_sch` | LiPo, BQ25120A, VBAT/VSYS, 3V3, коммутируемый 3V3_DISP |
| `mcu_rf.kicad_sch` | nRF52840 (BLE), кварцы 32 МГц / 32.768 кГц, SPI/I2C/GPIO |
| `displays.kicad_sch` | 3× FPC (MAIN, STRAP_L, STRAP_R), общая SPI, отдельные CS/BUSY |
| `connectors_ui.kicad_sch` | 3 кнопки (BTN1 = pairing), SWD, опц. USB VBUS |

**Нет** `nfc.kicad_sch`, NTAG, катушки LA/LB — по решению дизайна.

## Что разведено (логически)

- **Питание:** разъём LiPo+PCM → BQ25120A → VSYS / 3V3 (always) / 3V3_DISP через P-FET и `DISP_EN`
- **MCU:** nRF52840 (логический pin map, не полный aQFN73) + SWD + SPI0 на 3 E Ink + I2C к PMIC
- **Дисплеи:** общая шина `EPD_SCK`/`EPD_MOSI`/`EPD_DC`/`EPD_RST`, отдельные `CS`×3 и `BUSY`×3
- **UI:** BTN1 / BTN2 / BTN3; **долгий press BTN1 ~3 с** → BLE advertising ~60 с → sleep
- **Кварцы:** HF 32 МГц, LF 32.768 кГц

## Footprints TBD (не готово к производству)

| Ref | Назначение | Footprint |
|-----|------------|-----------|
| U1 | BQ25120A | `TBD:BQ25120A_DSBGA` |
| U2 | nRF52840 / модуль | `TBD:nRF52840_QIAA_or_MDBT50Q` |
| J1 | LiPo | `TBD:JST_PH_2pin` |
| J2–J4 | FPC E Ink | `TBD:ZIF_0.5mm_10pin` |
| J5 | SWD | `TBD:TagConnect_or_1x04` |
| J6 | USB VBUS | `TBD:USB_C_or_pogo` |
| SW1–3 | кнопки | `TBD:tactile_side` |
| Y1/Y2 | кварцы | `TBD:HF_XTAL` / `TBD:ABS07` |
| Q1 | load switch | `TBD:SOT23` |
| пассивы | R/C/FB | `TBD:0402` / `0603` |

Символ nRF52840 — **логический wearable map**, не полный pinout корпуса. Перед разводкой сверить с QIAA/CKAA / datasheet модуля.

## Документы

Копии исходного engineering package: каталог `docs/` (README, ARCHITECTURE, BOM, SCHEMATIC_BLOCKS, PCB_GUIDELINES).  
Учтите: исходные docs ещё упоминают NFC — для железа этого KiCad-проекта NFC **снят**; актуальные решения — в `DESIGN_NOTES.md`.


## PCB REV0.1 (placement + route)

На `e-ink-watch.kicad_pcb` выполнены **fine placement** внутри Ø40 мм (U1 сверху-центр, U2 под ним, развязка C1–C4/R1–R2 рядом, FPC MAIN/L/R на 12/9/3 ч, J_BAT на 6 ч, SW1–3 по нижней-правой дуге, J_SWD слева-снизу) и **черновая разводка** питания (VBAT/VSYS/3V3/3V3_DISP/GND, зона GND на B.Cu и 3V3 на F.Cu) плюс SPI к трём FPC (`EPD_SCK`/`MOSI`/`DC`/`RST`/`CS_*`/`BUSY_*`, 0.18 мм сигнал / 0.4–0.5 мм питание). Генератор: `tools/gen_pcb.py`; допущения pin-map — `tools/ROUTE_NOTES.md`; превью — `docs/pcb_routed.svg`.
## Статус

Концепт, сентябрь 2026. Rev `0.2-concept-ble` + PCB **REV0.1** (placed+routed).
