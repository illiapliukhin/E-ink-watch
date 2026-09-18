# Отчёт: замена placeholder footprint MCU/PMIC → реальные библиотеки

**Дата:** 2026-09-18 (Asia/Jerusalem, IDT)  
**Плата:** `e-ink-watch.kicad_pcb` (Ø40 мм)  
**Цель REV1:** orderable proto с предсертифицированным BLE-модулем + wearable PMIC.

---

## 1. Принятое решение (и почему)

| Ref | Было (placeholder) | Стало | Почему |
|-----|--------------------|-------|--------|
| **U1** | `QFN-48-1EP_7x7mm` «nRF52840» | **Raytac MDBT50Q** (`RF_Module:Raytac_MDBT50Q`), value `MDBT50Q-1MV2` | В KiCad есть Nordic aQFN-73, но для **первого заказного прототипа** модуль реалистичнее: встроенная антенна/matching, уже RF-сертификация (FCC/CE/… у Raytac), нет разводки 2.4 ГГц + XTAL на Ø40 мм. |
| **U2** | `QFN-16-1EP_3x3mm` «PMIC» | **BQ25120A**, footprint **YFP0025 DSBGA-25** (проектный `EInkWatch:Texas_YFP0025_…_P0.4mm`) | В стандартных lib нет готового YFP0025 под BQ25120A (есть YFP0020). Создан land pattern по семейству YFP: pitch **0.4 mm**, pad Ø **0.23 mm** NSMD, тело **2.5×2.5 mm**, сетка 5×5 — по даташиту TI BQ25120A (DSBGA-25 / YFP). |

**Альтернатива, отвергнутая для REV1:** голый `Nordic_AQFN-73-1EP_7x7mm_P0.5mm` — выше риск RF/сборки, дольше до первого BLE bring-up. QIAA остаётся вариантом REV2, если понадобится минимальная высота/BOM cost.

---

## 2. Размещение (constraints сохранены)

| Элемент | Позиция | Примечание |
|---------|---------|------------|
| Outline | Ø40 мм, центр (100,100) | без изменения |
| U1 MDBT50Q | (100, 93.5), rot **180°** | антенная сторона к «верху» платы (−Y), подальше от pogo |
| U2 BQ25120A | (111, 106) | справа внизу, вне корпуса модуля |
| Pogo 2×3 @ 3.0 mm | TP1–TP6 | без изменения |
| J_SWD | слева внизу | clear of pogo — без изменения |
| SW_DBG gating | на месте | топология SWDIO/SWDCLK/nRESET → pogo через ключ — без изменения |

---

## 3. Карта выводов и уверенность

### 3.1 U1 — Raytac MDBT50Q-1MV2 (nRF52840)

Логические GPIO из схемы → номера площадок модуля (KiCad symbol `MDBT50Q-1MV2` / Raytac DS):

| Pad | Функция модуля | Net на PCB | Уверенность |
|-----|----------------|------------|-------------|
| 1,2,15,33,55 | GND | GND | **высокая** |
| 28 | VDD | 3V3 | **высокая** |
| 30 | VDDH | 3V3 | **средняя** — normal-voltage mode (VDDH=VDD). High-voltage mode не разведён |
| 51 | SWDIO | SWDIO | **высокая** |
| 53 | SWDCLK | SWDCLK | **высокая** |
| 40 | P0.18 (nRESET conf.) | nRESET | **средняя** — на модуле nRESET = конфиг. P0.18; проверить fuse/UICR |
| 9 | P0.03 | EPD_SCK | **высокая** (по логической схеме) |
| 20 | P0.04 | EPD_MOSI | **высокая** |
| 22 | P0.06 | EPD_CS_MAIN | **высокая** |
| 23 | P0.07 | EPD_CS_L | **высокая** |
| 24 | P0.08 | EPD_CS_R | **высокая** |
| 19 | P0.26 | EPD_DC | **высокая** |
| 16 | P0.27 | EPD_RST | **высокая** |
| 13 | P0.28 | EPD_BUSY_MAIN | **высокая** |
| 10 | P0.29 | EPD_BUSY_L | **высокая** |
| 14 | P0.30 | EPD_BUSY_R | **высокая** |
| 61 | P1.01 | BTN1 | **высокая** |
| 50 | P1.02 | BTN2 | **высокая** |
| 60 | P1.03 | BTN3 | **высокая** |
| прочие | — | **без net (NC)** | намеренно — нет выдуманных swap |

**Не разведены (нет net на плате):** I2C SDA/SCL к PMIC, INT PMIC, DISP_EN/LSCTRL, USB, NFC (не используется).

### 3.2 U2 — BQ25120A (YFP0025)

| Ball | Имя TI | Net | Уверенность |
|------|--------|-----|-------------|
| A2 | IN | VBUS | **высокая** — заряд от pogo TP1 |
| A1, D5 | GND | GND | **высокая** |
| A5 | PGND | GND | **высокая** |
| B1, B2 | BAT | VBAT | **высокая** |
| B5 | SYS | VSYS | **высокая** |
| C5 | LS/LDO | 3V3_DISP | **средняя** — LS/LDO → дисплейная рейка; нужна прошивка/LSCTRL |
| B4, C4 | VINLS | VSYS | **средняя** — типовая wearable связка VINLS←SYS |
| A3, B3 | PMID | NC | ждут локальные конденсаторы |
| A4 | SW | NC | ждёт индуктор buck |
| D2 INT, E4 SDA, E5 SCL, E2 /CD, E3 LSCTRL, E1 /MR, C3 TS, … | NC | нет сигнальных net на PCB |

**VBUS:** pad A2 (IN) подключен трассой от зоны TP1 (pogo VBUS) — честный charger input.

**VSYS ↔ 3V3:** на плате это **разные net**. MCU питается от `3V3`, buck PMIC даёт `VSYS`. Для REV1 нужен **0 Ω / short** или прошивка SYS=3.3 V + merge net — см. blockers.

---

## 4. Схема

- `mcu_rf.kicad_sch`: **U1** = `MDBT50Q-1MV2`, footprint `RF_Module:Raytac_MDBT50Q`
- `power.kicad_sch`: **U2** = `BQ25120A`, footprint `EInkWatch:Texas_YFP0025_…`
- Референсы схемы выровнены с PCB (раньше на схеме U1 был PMIC — исправлено).
- Пины на символах по-прежнему **логические** (не полный aQFN/YFP pinout). Полная перенумерация символов → отдельный ERC/pass; до тех пор update-from-schematic по pin numbers **не делать вслепую**.

---

## 5. DRC: до / после

| Метрика | До | После | Δ |
|---------|----|-------|---|
| DRC violations | **537** | **567** | +30 |
| Unconnected items | **11** | **55** | +44 |
| `tracks_crossing` | 69 | 31 | **−38** |
| `shorting_items` | 124 | 107 | **−17** |
| `clearance` | 62 | 106 | +44 |
| `solder_mask_bridge` | 200 | 199 | −1 |

Интерпретация:
- Замена крупных placeholder QFN + вырезание пересекающихся треков в зоне U1/U2 **уменьшила short/cross**.
- Рост `unconnected` / `clearance` ожидаем: модуль больше, старые трассы к placeholder сняты, добавлен только минимальный fanout (VBUS/VBAT/VSYS/3V3/GND/SWD/3V3_DISP).
- Полный re-route сигнальной матрицы EPD/кнопок после смены геометрии — **следующий шаг**, не scope этой замены footprint.

Файлы: `reports/drc_before_fp_upgrade.txt`, `reports/drc_after_fp_upgrade.txt`.

---

## 6. Оставшиеся blockers (REV1)

1. **Доразвести** EPD SPI/CS/BUSY/DC/RST и BTN1–3 от новых pad U1 (сейчас net на pad есть, трассы частично оборваны).
2. **0 Ω между VSYS и 3V3** (или merge net + SYS=3.3 V по I2C) — иначе MCU без питания от PMIC.
3. **Passives BQ25120A:** IN/PMID/BAT/SYS/LS caps, SW inductor, TS divider, /CD strap, I2C pull-ups, INT → MCU.
4. **LSCTRL / DISP_EN** — нет net; 3V3_DISP может остаться выключенным.
5. **Courtyard overlap** модуля с соседними шелком/компонентами — проверить визуально в pcbnew.
6. **Символы:** логические pin numbers ≠ package pads → риск при «Update PCB from schematic».
7. **RF keepout** под антенной MDBT50Q (верх платы) — залить GND с вырезом по Raytac layout guide.
8. Остаточные short/clearance вне зоны upgrade — чинить отдельно (см. PRO_ROUTE / FIX_BLOCKERS).

---

## 7. Артефакты

- Footprint lib: `libraries/EInkWatch.pretty/`
  - `Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm.kicad_mod`
  - `Raytac_MDBT50Q.kicad_mod` (копия системной)
- `fp-lib-table` → `EInkWatch`
- Backup: `backups/e-ink-watch.kicad_pcb.pre-fp-upgrade-*`
- Скрипт: `tools/upgrade_footprints.py` (+ одноразовый clean runner в истории shell)

---

## 8. Итог для заказа

**Выбранные части:** Raytac **MDBT50Q-1MV2** (U1) + TI **BQ25120A** YFP (U2).  
**DRC delta:** shorts/crossings улучшились; unconnected выросли до завершения fanout.  
**Архив:** `/workspace/e-ink-watch-kicad-footprints.tar.gz`
