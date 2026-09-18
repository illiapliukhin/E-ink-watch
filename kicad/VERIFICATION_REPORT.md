# Отчёт о верификации схемы — E Ink Watch (BLE-only)

**Дата:** 2026-09-18 (Asia/Jerusalem, UTC+3)  
**Проект:** `/workspace/e-ink-watch-kicad/`  
**Ревизия:** `0.2-concept-ble` (корневой title_block)  
**Инструменты:** KiCad 9.0.2 (`kicad-cli sch erc`), ngspice 44.2, Python 3

---

## 1. Что проверялось

| # | Проверка | Метод |
|---|----------|--------|
| 1 | Список `.kicad_sch` / `.kicad_pro` | `find` / `ls` |
| 2 | Баланс скобок S-expression | подсчёт `(`/`)` |
| 3 | Ссылки иерархических листов | парсинг `Sheetfile` + наличие имён pin ↔ hierarchical_label |
| 4 | Отсутствие NFC / NTAG / катушки | grep + отсутствие файлов |
| 5 | Примечание pairing: long-press BTN1 | grep по листам |
| 6 | ERC | `kicad-cli sch erc` → `reports/erc.txt` |
| 7 | Симуляция силового пути | ngspice `sim/power_path.cir` |
| 8 | Оценка времени работы от батареи | `sim/battery_life.py` |

---

## 2. Структурная валидация — результаты

### 2.1 Файлы схемы

| Файл | Роль | Баланс `()` |
|------|------|-------------|
| `e-ink-watch.kicad_pro` | проект | — |
| `e-ink-watch.kicad_sch` | корень | OK (1418/1418) |
| `power.kicad_sch` | питание BQ25120A | OK |
| `mcu_rf.kicad_sch` | nRF52840 BLE | OK |
| `displays.kicad_sch` | 3× E Ink FPC | OK |
| `connectors_ui.kicad_sch` | кнопки / SWD / VBUS | OK |
| `libraries/*.kicad_sym` | символы | OK |

**Итог:** PASS (все файлы существуют, S-expression сбалансированы).

### 2.2 Иерархия листов

Корневые `Sheetfile`:

- Power → `power.kicad_sch` (10 pin)
- MCU_RF → `mcu_rf.kicad_sch` (23 pin)
- Displays → `displays.kicad_sch` (12 pin)
- Connectors_UI → `connectors_ui.kicad_sch` (9 pin)

Имена pin на корне **совпадают** с `hierarchical_label` внутри дочерних листов (проверка скриптом).

Непрерывность ключевых цепей (по охвату листов):

| Нет | Листы | Статус |
|-----|-------|--------|
| `GND` | Power, MCU_RF, Displays, Connectors_UI | PASS |
| `3V3` | Power, MCU_RF, Connectors_UI | PASS |
| `3V3_DISP` | Power, Displays | PASS |
| `VSYS` | Power, MCU_RF | PASS |
| `DISP_EN` | Power, MCU_RF | PASS |
| `SDA`/`SCL` | Power, MCU_RF | PASS |
| `BTN1`–`BTN3` | MCU_RF, Connectors_UI | PASS |
| SPI EPD_* | MCU_RF, Displays | PASS |
| `VBUS` | Power, Connectors_UI | PASS |
| `VBAT` | только Power (ожидаемо) | PASS |

**Итог имён/ссылок:** PASS.  
**Предупреждение:** ERC (ниже) всё равно ругается на `hier_label_mismatch` и dangling labels — см. §3 (проблема разводки/инстансов генератора, не отсутствия имён).

### 2.3 NFC отсутствует

| Проверка | Результат |
|----------|-----------|
| Файл `nfc.kicad_sch` | **нет** |
| Символ `libraries/NT3H*` | **нет** |
| Компоненты NTAG / катушка 13.56 МГц в `.kicad_sch` | **нет** (только текстовые «no NFC» / «NFC unused») |
| Упоминания NFC в `docs/*` | устаревший концепт; в шапках docs есть пометка «NFC снят» |

**Итог:** PASS — железо BLE-only, NFC/NTAG/антенна в схеме **отсутствуют**.

### 2.4 BTN1 long-press pairing

Найдено в схеме:

- `mcu_rf.kicad_sch`: *«Pairing: long-press BTN1 ~3s -> BLE adv ~60s, then sleep.»*
- `connectors_ui.kicad_sch`: *«BTN1 long-press ~3s = BLE pairing window ~60s»* + `SW1` Value `BTN1_PAIR`
- `DESIGN_NOTES.md` §2 — полное UX-описание

**Итог:** PASS.

---

## 3. ERC (KiCad)

**Команда:**  
`kicad-cli sch erc --format report --severity-all -o reports/erc.txt e-ink-watch.kicad_sch`

**Статус запуска:** **успешно** (KiCad 9.0.2 установлен через `apt`).

**Сводка:** **167** сообщений — **77 errors**, **90 warnings**.

| Тип | Кол-во | Severity | Комментарий |
|-----|--------|----------|-------------|
| `endpoint_off_grid` | 84 | warning | провода/пины не на сетке соединения |
| `hier_label_mismatch` | 51 | error | KiCad не связывает sheet pin с label (см. ниже) |
| `label_dangling` | 24 | error | глобальные label на корне не касаются провода/пина |
| `unconnected_wire_endpoint` | 5 | warning | свободные концы |
| `pin_not_connected` | 2 | error | в т.ч. VBAT на корне |
| `multiple_net_names` | 1 | warning | конфликт имён на одном графе (`3V3_DISP`/`GND`) |

**Интерпретация:**

1. Имена hierarchical labels **есть** и совпадают с pin (структурный скрипт PASS), но ERC всё равно выдаёт `hier_label_mismatch`. Вероятные причины генератора:
   - некорректные/неполные `sheet_instances` / `path` у дочерних листов;
   - провода на корне **не попадают** в точки sheet pin (off-grid + dangling) → электрически ERC не видит связь.
2. Дочерние листы в отчёте ERC почти пустые (`Sheet /Power/` … без внутренних нарушений) — типично при сбое иерархической привязки.
3. Это **не** «зелёный» ERC для передачи в layout: перед PCB нужно открыть проект в GUI, выровнять сетку, перепривязать sheet pins и перезапустить ERC до 0 errors.

**Артефакт:** `/workspace/e-ink-watch-kicad/reports/erc.txt`

**Вердикт ERC:** FAIL (ошибки есть), но инструмент **запущен**, отчёт сохранён.

---

## 4. Симуляция / расчёт тока

Полный digital/RF SPICE nRF52840 **недоступен** — не эмулировался.

### 4.1 ngspice — только POWER path

Файлы: `sim/power_path.cir`, `sim/power_path.log`, `sim/power_path_trace.csv`, `sim/INTERPRETATION.txt`, `sim/SIMULATION.md`.

Модель: LiPo 3.8 V + ESR 80 мΩ + C 47 µF + Iq 15 µA + идеальный `DISP_EN` + нагрузка ~10 мА (1 с / 60 с).

| Параметр | Значение | Оценка |
|----------|----------|--------|
| Ток покоя | ~15 µA | PASS (совпадает с Iq) |
| Ток refresh (средн. в импульсе) | ~10–13 мА | PASS (цель ~10 мА) |
| Просадка VSYS | ~50 мВ | PASS / низкий риск |
| Inrush при замыкании SW | ~0.6 А (заряд C) | WARN — артефакт идеального ключа; у реального PMIC soft-start меньше |
| Iavg за 180 с (3 импульса) | ~181 µA | информативно |

**Вердикт sim:** PASS на уровне концепта (импульс E Ink не роняет шину).

### 4.2 Оценка жизни батареи (Python)

`sim/battery_life.py` → `sim/battery_life_out.txt`

Допущения: LiPo **120 мА·ч**, usable 85%; System ON idle 3 µA + PMIC Iq 8 µA; E Ink 10 мА + MCU 4 мА × 1 с; BLE pair/conn редкие.

| Сценарий refresh | Iavg (порядок) | Оценка жизни |
|------------------|----------------|--------------|
| каждые **60 с** | ~249 µA | **~17 дней** |
| каждые **15 мин** | ниже | **~месяцы** (см. вывод скрипта) |
| каждые **60 мин** | ещё ниже | существенно дольше |

Доминирует энергия refresh: при минутном обновлении трёх панелей батарея маленького корпуса быстро садится — для часов нужен partial refresh / реже обновлять strap.

**Вердикт hand-calc:** выполнен с числами; сценарий 60 с — жёсткий, требует продуктового решения по частоте обновления.

---

## 5. Сводный Pass / Fail / Warnings

| Пункт | Статус |
|-------|--------|
| Файлы схемы / баланс S-expr | **PASS** |
| Sheetfile существуют, pin↔label имена | **PASS** |
| Непрерывность Power/MCU/Displays/UI (по именам) | **PASS** |
| NFC / NTAG / антенна отсутствуют | **PASS** |
| BTN1 long-press pairing note | **PASS** |
| ERC запущен, отчёт сохранён | **PASS** (запуск) |
| ERC без ошибок | **FAIL** (77 errors) |
| ngspice power-path | **PASS** |
| Battery-life Python | **PASS** |
| Полноценный RF/digital SPICE SoC | **N/A** (не фейкали) |

---

## 6. Остаточные риски до разводки PCB

1. **ERC errors на корне** — off-grid, dangling labels, `hier_label_mismatch`: починить в KiCad GUI до netlist/PCB.
2. **Placeholder footprint** — nRF (логический map ≠ полный aQFN73), BQ25120A упрощён, ZIF/FPC TBD (`DESIGN_NOTES`).
3. **Выбор модуля vs bare die** — антенна 2.4 ГГц, keepout, толщина корпуса.
4. **Питание дисплеев** — реальный ток/буст панелей; soft-start `3V3_DISP`; измерить, не полагаться на 10 мА.
5. **Частота refresh** — при 1/мин жизнь ~недели на 120 мА·ч; нужна политика UI/firmware.
6. **Устаревшие `docs/*`** — ещё описывают NFC; актуальный источник истины — `DESIGN_NOTES.md` / корневой README.
7. **Механика** — Ø корпуса, strap bend, pinout купленных EPD — блокеры outline.
8. **Нет PCB / DRC** — только схема-концепт; layout не начинать до очистки ERC и фиксации footprint.

---

## 7. Артефакты

| Путь | Содержание |
|------|------------|
| `VERIFICATION_REPORT.md` | этот отчёт |
| `reports/erc.txt` | полный ERC |
| `sim/SIMULATION.md` | описание sim |
| `sim/power_path.cir` | netlist ngspice |
| `sim/power_path.log` | лог с meas |
| `sim/power_path_trace.csv` | трасса V/I |
| `sim/INTERPRETATION.txt` | краткий разбор sim |
| `sim/battery_life.py` | калькулятор |
| `sim/battery_life_out.txt` | численный вывод |

---

*Отчёт сгенерирован на BOX-агенте после rebuild схемы; NFC подтверждённо отсутствует; ERC и power-path sim выполнены.*
