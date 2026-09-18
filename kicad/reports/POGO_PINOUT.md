# POGO_PINOUT — контакты зарядки и прошивки (REV0.2)

**Дата:** 2026-09-18 12:14 IDT (Asia/Jerusalem, UTC+3)  
**Плата:** `e-ink-watch.kicad_pcb`  
**Назначение:** один pogo-cradle = **зарядка + SWD flash** (основной field-путь).  
**Источник истины корпуса:** `e-ink-watch-case/exports/POGO_MATRIX.txt`  
**Резерв на фабрике:** разъём `J_SWD` (1×05) — **всегда** на MCU SWD (до `SW_DBG`).

---

## Массив площадок (2×3 @ 3.0 mm)

| Параметр | Значение |
|----------|----------|
| Слой | **B.Cu** (+ B.Mask opening; **без silk** на pads) |
| Кол-во | **6** (2 ряда × 3) |
| Форма | круг Ø**1.5** мм Cu |
| Шаг | **3.0** мм |
| Origin (case) | (−4.0, −12.5); ряды y=−14 и y=−11 |
| Допуск выравнивания корпуса | **±0.2** мм |
| PCB center | (100, 100) мм |
| Преобразование | `PCB = (100 + case_x, 100 − case_y)` — **Y инвертирован** (проверено по J_BAT / J_SWD) |
| Покрытие | **ENIG / hard gold** (рекомендация) |
| Refs | TP1…TP6 |

### Координаты pads (PCB mm)

Вид **со стороны B.Cu** (сзади платы). Ряд «к 6 часам» = больший Y:

```
        x=93.00     x=96.00     x=99.00
y=114.0 TP1 VCHG    TP2 GND     TP3 SWDIO     ← case y=−14
y=111.0 TP4 SWDCLK  TP5 nRESET  TP6 OPT       ← case y=−11
```

| Ref | Сигнал | Case (mm) | PCB (mm) | Нет |
|-----|--------|-----------|----------|-----|
| TP1 | **VCHG / VBUS** | (−7, −14) | **(93.00, 114.00)** | `VBUS` |
| TP2 | **GND** | (−4, −14) | **(96.00, 114.00)** | `GND` |
| TP3 | **SWDIO** | (−1, −14) | **(99.00, 114.00)** | `SWDIO_POGO` |
| TP4 | **SWDCLK** | (−7, −11) | **(93.00, 111.00)** | `SWDCLK_POGO` |
| TP5 | **nRESET** | (−4, −11) | **(96.00, 111.00)** | `nRESET_POGO` |
| TP6 | **OPT** | (−1, −11) | **(99.00, 111.00)** | `OPT` (NC / label) |

---

## SW_DBG — скрытый PROG EN (security)

| Параметр | Значение |
|----------|----------|
| Ref | **SW_DBG** |
| Silk | `PROG EN` / `ON` |
| Тип | SMT DIP SPST×3 (footprint Copal CVS-03xB class, P1.0 mm) |
| Позиция PCB | **(90.50, 105.50)** F.Cu — внутри корпуса, **без отверстия** в крышке |
| Заводское состояние | **OFF** (pogo SWD разомкнут) |
| Field recovery | открыть корпус → ON → программатор через cradle |

### Топология

```
MCU SWD  ←→  J_SWD (factory)     … всегда
MCU SWD  ←→  SW_DBG  ←→  pogo TP3/TP4/TP5   … только при ON
VBUS/GND ←→  pogo TP1/TP2                  … всегда (зарядка)
OPT      … NC / reserved
```

Коммутируется **только**: SWDIO, SWDCLK, nRESET (series).  
**Не** рвёт VCHG и GND.

Nets за переключателем: `SWDIO_POGO`, `SWDCLK_POGO`, `nRESET_POGO`.

---

## Распиновка cradle (логика)

| # | Ref | Сигнал | Доступ при SW_DBG OFF |
|---|-----|--------|----------------------|
| 1 | TP1 | VCHG/VBUS | да (зарядка) |
| 2 | TP2 | GND | да |
| 3 | TP3 | SWDIO | **нет** (открыто) |
| 4 | TP4 | SWDCLK | **нет** |
| 5 | TP5 | nRESET | **нет** (anti reset-attack) |
| 6 | TP6 | OPT | NC |

---

## Электрические примечания

1. **ESD:** TVS на SWD-линиях — предпочтительно на стороне MCU (до/у J_SWD); на pogo-стороне — по месту.  
2. **Series:** 22–100 Ω на SWDIO/SWDCLK — TBD.  
3. **VBUS:** феррит + TVS; ток лимитирует PMIC.  
4. **Механика:** отверстия в back ≥ Ø1.8–2.2 мм, центр на pads, align **±0.2** мм к case matrix.  
5. Key notch корпуса: −X сторона окна.

---

## Допущения

- Pin map nRF/SWD — placeholder QFN-48.  
- VBUS на U2 не привязан к datasheet BQ25120A.  
- DRC **не** утверждается clean после правки.  
- Part number DIP — class Copal CVS-03; заменить на выбранный PN при BOM.
