# BOARD_VERIFY — проверка платы E Ink Watch (REV0.2 / pogo 2×3)

**Дата:** 2026-09-18 12:18 IDT (Asia/Jerusalem, UTC+3)  
**Плата:** `/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb` (mtime 12:14 IDT)  
**Критерий выбора:** pogo **2×3 @ 3.0 mm** + **SW_DBG** DIP  
**Инструмент DRC:** `kicad-cli 9.0.2 pcb drc` → `reports/VERIFY_drc.txt`

---

## Вердикт: **FAIL**

Плата **не готова к производству**. Координаты pogo и логика SW_DBG в документации/назначении сеток выглядят согласованными, но на меди есть критические КЗ (в т.ч. питание), коллизия PTH `J_SWD` с pogo-площадками (обход PROG EN), треки за краем платы и незавершённый путь зарядки `VBUS`.

---

## Что в порядке (OK)

1. **Выбрана актуальная плата:** `e-ink-watch.kicad_pcb` содержит TP1–TP6 (`Pogo_Pad_D1.5mm`, B.Cu, 2×3@3.0) и `SW_DBG` (Copal CVS-03 class DIP×3).
2. **Координаты pogo = матрица корпуса** (преобразование `PCB = (100+case_x, 100−case_y)`):

   | Ref | PCB (факт) | Ожидание | Нет | Статус |
   |-----|------------|----------|-----|--------|
   | TP1 | (93.00, 114.00) | (93, 114) VCHG | `VBUS` | OK (имя VBUS ≡ VCHG в доках) |
   | TP2 | (96.00, 114.00) | (96, 114) GND | `GND` | OK |
   | TP3 | (99.00, 114.00) | (99, 114) SWDIO | `SWDIO_POGO` | OK |
   | TP4 | (93.00, 111.00) | (93, 111) SWDCLK | `SWDCLK_POGO` | OK |
   | TP5 | (96.00, 111.00) | (96, 111) nRESET | `nRESET_POGO` | OK |
   | TP6 | (99.00, 111.00) | (99, 111) OPT | `OPT` | OK |

3. **SW_DBG существует** @ (90.50, 105.50), footprint `SW_DIP_SPSTx03_Slide_Copal_CVS-03xB_W5.9mm_P1mm`.
4. **Назначение сеток на DIP (серия, как задумано):**
   - pad1 `SWDIO` ↔ pad6 `SWDIO_POGO`
   - pad2 `SWDCLK` ↔ pad5 `SWDCLK_POGO`
   - pad3 `nRESET` ↔ pad4 `nRESET_POGO`
   - `VBUS`/`GND` **не** на переключателе (зарядка не рвётся на уровне схемы сеток).
5. **J_SWD** на MCU-сетках напрямую: `3V3 / SWDIO / SWDCLK / nRESET / GND` (factory path).
6. **Edge.Cuts:** окружность Ø40 мм, центр (100, 100), end (120, 100), layer `Edge.Cuts` — **есть**.
7. **Origins всех 23 footprint’ов** внутри r≤20 мм от центра (грубая проверка).
8. Документы `POGO_PINOUT.md` / `SW_DBG_PROG_GATE.md` / `POGO_SYNC.md` **согласованы** с координатами и топологией «SWD через DIP, VBUS/GND всегда».

---

## Критические проблемы (блокер производства)

### 1. DRC: массовые КЗ и пересечения треков
| Метрика | Значение |
|---------|----------|
| DRC violations | **543** |
| Unconnected items | **9** |
| `shorting_items` | **110** (error) |
| `tracks_crossing` | **77** (error) |
| `clearance` | **81** (error) |
| `solder_mask_bridge` | **200** (error) |
| `hole_clearance` | **11** |
| `courtyards_overlap` | **5** |
| `copper_edge_clearance` | **2** |

Уникальных пар короткозамкнутых сеток: **~50**. Среди них с питанием (примеры частоты):
- `3V3` ↔ `GND` — **12**
- `3V3_DISP` ↔ `GND` — **13**
- `VBAT` ↔ `GND` — **2**
- `VBAT` ↔ `VSYS` — **1**
- `3V3` ↔ `3V3_DISP` — **1**
- плюс множество сигнал↔GND/3V3 вокруг FFC и MCU

**Вывод:** раскладка меди в текущем виде электрически небезопасна; заливать/заказывать нельзя.

### 2. Коллизия PTH `J_SWD` с pogo TP4/TP5/TP6 (обход SW_DBG)
`J_SWD` @ (89, 111.5) rot=90° (KiCad Y-down): pads идут по +X с шагом 2.54:

| Pad | Нет | PCB |
|-----|-----|-----|
| 1 | 3V3 | (89.00, 111.50) |
| 2 | SWDIO | (91.54, 111.50) |
| 3 | SWDCLK | (94.08, 111.50) |
| 4 | nRESET | (96.62, 111.50) |
| 5 | GND | (99.16, 111.50) |

Перекрытие с pogo Ø1.5 (B.Cu) и PTH Ø~1.7 (`*.Cu`):
- **TP4** `SWDCLK_POGO` (93,111) ↔ J_SWD.3 `SWDCLK` — gap **−0.41 mm** (OVERLAP)
- **TP4** также близко/перекрывает J_SWD.2 `SWDIO` — gap **−0.06 mm**
- **TP5** `nRESET_POGO` (96,111) ↔ J_SWD.4 `nRESET` — gap **−0.80 mm** (OVERLAP)
- **TP6** `OPT` (99,111) ↔ J_SWD.5 `GND` — gap **−1.08 mm** (OVERLAP)

PTH пробивает все слои → **MCU SWDCLK/nRESET закорочены на pogo-сторону**, `OPT` на `GND`.  
**SW_DBG как security-gate фактически скомпрометирован** геометрией, даже при корректных net-именах на DIP.

### 3. Треки за / на краю платы
- Трек `nRESET` до **(81.38, 111.50)** — **вне** Ø40 (r≈21.89, +1.89 мм за край).
- Трек `SWDCLK` до **(83.92, 111.50)** — у края (нарушение edge clearance 0.5 мм).
- DRC: `copper_edge_clearance` ×2, `track_dangling` на nRESET.

Похоже на «зеркальные» stub’ы не в ту сторону относительно фактических pads `J_SWD`.

### 4. Зарядка: `VBUS` не доведён до PMIC
- TP1 = `VBUS`, есть трек F.Cu и via @ (93,114).
- На **U2** нет pad’а `VBUS` (placeholder QFN-16: VBAT/VSYS/3V3/3V3_DISP/GND).
- Конец трека ~ (95.76, 106.25) **не** стыкуется с зарядным входом.
- Via `GND` @ TP2 помечен `via_dangling`.

Без доводки VBUS→charger **cradle charge не работает**, несмотря на совпадение координат pads.

### 5. Обрывы (9 unconnected)
В т.ч.:
- GND к mounting pads FFC (`J_STRAP_L/R`, `J_DISP_MAIN`)
- Разрывы островков GND около U1
- `SWDCLK` / `nRESET` треки ↔ pads `J_SWD` (следствие неверной доводки stub’ов)

### 6. Нет copper zones
В PCB **нет** `zone` (полигонов) — питание/GND только треками; отсюда фрагментация GND и часть unconnected.

---

## Средние проблемы

| # | Проблема | Комментарий |
|---|----------|-------------|
| M1 | `solder_mask_bridge` ×200 | Часть может быть следствием КЗ/плотной разводки QFN/0402; всё равно требует разбора |
| M2 | `silk_over_copper` ×16, `silk_overlap` ×13 | Косметика/читаемость, не блокер сама по себе |
| M3 | `lib_footprint_mismatch` / `issues` ×6+6 | Расхождение с библиотекой (в т.ч. кастом pogo / DIP class) |
| M4 | `courtyards_overlap` ×5 | Механический риск при сборке |
| M5 | `hole_to_hole` / `holes_co_located` | PTH/via скученность у J_SWD/pogo |
| M6 | Много NC pad на U1 (QFN-48 placeholder) | Ожидаемо для stub-MCU, но не production pinout |
| M7 | OPT без треков | NC — ок по доке; но КЗ с GND через PTH J_SWD — уже критично |
| M8 | Именование VCHG vs VBUS | В доках согласовано; на схеме только `VBUS` |

---

## Inventory footprints (23)

| Ref | Footprint | Позиция | Основные nets |
|-----|-----------|---------|---------------|
| U1 | `Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP3.5x3.5mm` | (100, 98.5) | SWD*, EPD_*, BTN*, 3V3, GND |
| U2 | `Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm` | (100, 107) | VBAT, VSYS, 3V3, 3V3_DISP, GND |
| J_BAT | `PinHeader_1x02_P2.54mm_Vertical` | (100, 115.8) | VBAT, GND |
| J_SWD | `PinHeader_1x05_P2.54mm_Vertical` | (89, 111.5) r90 | 3V3, SWDIO, SWDCLK, nRESET, GND |
| J_DISP_MAIN | `Hirose_FH12-10S-0.5SH_...` | (100, 85) | EPD_*, 3V3_DISP, GND |
| J_STRAP_L | то же | (85, 100.5) r90 | EPD_*_L, … |
| J_STRAP_R | то же | (115, 100.5) r−90 | EPD_*_R, … |
| SW_DBG | `SW_DIP_SPSTx03_...CVS-03xB...` | (90.5, 105.5) | SWD* ↔ *_POGO |
| SW1–SW3 | `SW_SPST_B3U-1000P` | ~109–113, 105–112 | BTN1–3, GND |
| TP1–TP6 | `TestPoint:Pogo_Pad_D1.5mm` | см. таблицу | VBUS/GND/*_POGO/OPT |
| R1 | `R_0402` | (94.8, 95.5) | 3V3, nRESET |
| R2 | `R_0402` | (105.2, 95.5) | 3V3, EPD_CS_MAIN |
| C1–C4 | `C_0402` | около U1/U2 | 3V3, GND |

---

## Sanity: питание и off-board

| Проверка | Результат |
|----------|-----------|
| КЗ с участием питания | **Да**, многократно (3V3/GND, 3V3_DISP/GND, VBAT/GND, …) |
| Треки за Edge.Cuts | **Да** — stub `nRESET` @ x=81.38; `SWDCLK` у границы |
| Компоненты origins внутри Ø40 | Да (origins) |
| Реальный copper/PTH у края | J_SWD pad-ряд ок по origins, но **ошибочные треки** уходят наружу; pogo/J_SWD overlap внутри |

---

## Согласованность документации

| Документ | Vs PCB |
|----------|--------|
| `POGO_PINOUT.md` | Координаты и nets TP/SW_DBG — **совпадают** |
| `SW_DBG_PROG_GATE.md` | Топология «рвём только SWD*» — **совпадает по nets** |
| `POGO_SYNC.md` | Заявленные координаты и transform — **совпадают** |
| Честность доков | Доки уже предупреждают: DRC не clean, U2/VBUS placeholder, DIP class PN — **подтверждено аудитом** |
| Слепое пятно доков | **Не зафиксирована** коллизия J_SWD PTH ↔ pogo TP4/5/6 |

---

## Ограничения placeholder (честно)

1. **U1** — generic QFN-48, не финальный nRF/пинмап SWD/EPD.
2. **U2** — generic QFN-16 «PMIC», **нет** вывода `VBUS`/зарядного входа как у реального BQ25120A и т.п.
3. **SW_DBG** — class footprint Copal CVS-03, не утверждённый BOM PN.
4. **Pogo** — кастомный `Pogo_Pad_D1.5mm`; покрытие ENIG/hard gold — рекомендация, не в DRC.
5. **Нет zone refill** / полигонов — разводка «проволочная».
6. Часть DRC (`solder_mask_bridge`, часть clearance у 0.5 mm FFC) может **раздуваться** от текущего хаоса треков; после чистки цифры упадут, но **110 shorting — не артефакт одного правила**.
7. ERC/схема в этом прогоне не пересобирались заново (фокус — PCB).

---

## Рекомендуемые следующие фиксы (по приоритету)

1. **P0 — развести `J_SWD` и pogo:** сдвинуть header (например, −X/−Y внутрь или повернуть так, чтобы PTH не пересекали TP4/TP5/TP6), либо вынести factory SWD на край без пересечения с cradle matrix. Перепроверить gap ≥0.2–0.3 мм ко всем слоям.
2. **P0 — удалить/перетрассировать off-board stub’ы** `nRESET`/`SWDCLK` (x≈81–84) и корректно привязать треки к реальным pads J_SWD.
3. **P0 — устранить все `shorting_items` / `tracks_crossing`**, особенно пары питания (3V3↔GND, 3V3_DISP↔GND, VBAT↔GND).
4. **P0 — ввести зоны GND/3V3** (и при необходимости 3V3_DISP), refill, закрыть 9 unconnected.
5. **P0 — довести VBUS:** pad/нет на реальном charger IC или явный путь TP1→феррит/TVS→VIN; убрать dangling via.
6. **P1 — clearance 0.2 mm**, hole/courtyard; пересчитать FFC fanout.
7. **P1 — silk** cleanup; зафиксировать BOM PN для DIP и pogo finish.
8. **P2 —** повторить `kicad-cli pcb drc` до **0 error** (warnings — по политике); обновить `POGO_PINOUT` разделом «keepout J_SWD vs pogo».
9. **P2 —** механическая проверка: pads B.Cu vs отверстия корпуса ±0.2 мм (уже в case SoT).

---

## Артефакты

- DRC: `reports/VERIFY_drc.txt`
- Этот отчёт: `reports/BOARD_VERIFY.md`
- Архив: `/workspace/e-ink-watch-kicad-verify.tar.gz`

**Итог одной строкой:** геометрический sync pogo/case и сетка SW_DBG — OK на уровне refs/nets; **электромеханика платы — FAIL** (КЗ, PTH↔pogo, off-board tracks, VBUS dead-end).
