# FIX_BLOCKERS — устранение критических блокеров (порядок обязателен)

**Дата:** 2026-09-18 ~12:35 IDT  
**Плата:** `e-ink-watch.kicad_pcb`  
**Вердикт:** **PASS WITH RISKS** по целевым блокерам геометрического порядка; **FAIL** как production-ready (DRC shorts остаются).

---

## Assumptions

1. KiCad `(at … 90)` для `PinHeader_1x05` даёт pads вдоль **+X** (подтверждено pcbnew).
2. U2 — placeholder QFN-16; **pad 4** назначен как **VBUS/VIN** (нет реального BQ25120A pin).
3. Pogo TP1–TP6 координаты **не менялись** (2×3 @ 3.0 mm).
4. Топология SW_DBG: MCU nets ↔ DIP ↔ `*_POGO`; VBUS/GND не на DIP.

---

## 1. J_SWD vs pogo — СДЕЛАНО

| | Было | Стало |
|---|------|-------|
| Позиция | (89.0, 111.5) r90 | **(84.0, 108.0) r90** |
| Pads | x=89…99.16 @ y=111.5 (OVERLAP TP4/5/6) | x=84.00 / 86.54 / 89.08 / 91.62 / 94.16 @ y=108.0 |
| Gap PTH↔pogo Ø1.5 | отрицательный (КЗ MCU↔POGO) | **≥0.25 mm** (расчёт centers−1.6) — **PASS** |
| GND↔OPT через PTH | да | **нет** (DRC GND–OPT = 0) |

Сохранены nets factory: `3V3 / SWDIO / SWDCLK / nRESET / GND`.  
Перетрассированы stub’ы к MCU bus (y≈100.25–101.25) и связи SW_DBG.  
`*_POGO` уведены вправо (x≥96.5), чтобы не пересекать новый header.

**Альтернатива отвергнута:** vertical rot0 @ x=86.5 — courtyard внутрь SW_DBG / теснее к J_STRAP_L.

---

## 2. Power shorts — ЧАСТИЧНО

Приоритет: геометрические пересечения 3V3↔GND, 3V3_DISP↔GND, VBAT↔GND, VBAT↔VSYS.

Сделано:
- Удалён F.Cu GND spine `(100,98.5)–(100,107)` (КЗ с VBAT/VSYS).
- VBAT смещён на коридор **x=96.2** (не через pad-ряд VSYS).
- VBUS на коридоре **x=99.2** (разведён с VBAT).
- Сдвинуты vias, конфликтовавшие 3V3↔GND.
- 3V3_DISP длинный F.Cu x=95.2 заменён на **B.Cu lane x=92** + via.

**Остаётся:** много `3V3_DISP↔GND` на **смежных pads FH12** (pitch 0.5 mm) — это footprint/fanout, не «склеивание сеток». Также остаточные пересечения вокруг U1 QFN placeholder.

---

## 3. VBUS → PMIC — СДЕЛАНО (с допущением)

Маршрут **0.50 mm**:  
`TP1 (93,114) → (93,112.2) → (99.2,112.2) → (99.2,107.75) → U2.4 (98.5625,107.75)`.

**Допущение:** U2 pad **4** = VIN/VBUS (ранее NC). Зафиксировано в этом отчёте и в PRO_ROUTE. Реальный BQ25120A потребует смены footprint и переразводки.

Via count VBUS: **3** (≥2 по CALC).

---

## 4. nRESET off-board — СДЕЛАНО

Удалены stub’ы до x≈81.38 (r≈21.9).  
`copper_edge_clearance`: **2 → 0**.  
Макс. r точек nRESET ≪ 19.75 mm.

---

## 5. DRC before → after

| Метрика | BOARD_VERIFY | После fix |
|---------|--------------|-----------|
| Violations (footer) | **543** | **536** |
| Unconnected | **9** | **11** |
| shorting_items | 110 | 124 |
| tracks_crossing | 77 | 69 |
| clearance | 81 | 61 |
| copper_edge_clearance | 2 | **0** |
| GND↔OPT / J_SWD↔pogo | да | **нет** |
| VBUS↔GND/VBAT (новые) | — | устранены во 2-м проходе |

Число shorting_items **не** обрушилось: доминируют FFC 0.5 mm + хаотичная SPI/placeholder разводка. Целевые блокеры порядка 1–4 по геометрии закрыты.

Артефакт: `reports/DRC_after_fix.txt`.

---

## Risk register (блокеры)

| ID | Риск | Sev | Likely | Статус |
|----|------|-----|--------|--------|
| R1 | U2 pad4 ≠ реальный VIN BQ | High | High | Accept lab; сменить FP |
| R2 | Остаточные power shorts у FFC/QFN | High | High | Block production |
| R3 | Courtyard J_SWD vs SW_DBG | Med | Med | Accept prototype |
| R4 | Нет полного PDN / измеренных I_peak | Med | High | См. CALC_POWER_TRACES |
| R5 | Zone fill без ручной чистки islands | Low | Med | Watch |

---

## Итог

**Блокеры порядка:** J_SWD clear / nRESET on-board / VBUS до U2.4 / edge copper — **сделаны**.  
**Production:** **FAIL** до чистки shorts и реальных footprint’ов.
