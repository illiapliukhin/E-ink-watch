# PRO_ROUTE — профессиональный проход разводки

**Дата:** 2026-09-18 ~12:35 IDT  
**Вердикт:** **PASS WITH RISKS** (дисциплина net-class + physics + частичная чистка питания); **FAIL** production DRC.

Связанные артефакты: `FIX_BLOCKERS.md`, `CALC_POWER_TRACES.md`, `DRC_after_fix.txt`.

---

## Goal & constraints

- Ø40 mm Edge.Cuts, 2L, pogo 2×3 @ 3.0 mm **заморожены**.
- SW_DBG gates только SWD*; charge (VBUS/GND) всегда.
- Fab-ориентир: clearance ≥0.15 mm, signal 0.18 mm, power ≥0.45 mm.

---

## Что сделано в pro-pass

1. **Net classes** в `e-ink-watch.kicad_pro`: Default / Signal (0.18) / Power (0.45) / PowerFat (0.50); patterns на VBAT/VBUS/3V3/…
2. **Ширины из расчёта** (`CALC_POWER_TRACES.md`): IPC не лимит → выбраны 0.45/0.50 по IR+политике.
3. **GND:** убран F.Cu «спагетти» spine через центр; опора на **B.Cu zone** + stitch vias; zones **re-filled** (`ZONE_FILLER`).
4. **Питание:** раздельные коридоры VBAT (x≈96.2) и VBUS (x≈99.2); 3V3_DISP частично на B.Cu.
5. **Decoupling:** C1–C4 / R1–R2 **не сдвигались** (остаются у U1/U2).
6. **SPI / три FPC:** полной переразводки fanout **не** выполнено — dense 0.5 mm FH12 + placeholder U1 дают системные pad↔pad/clearance; косметический «clean topology» без смены FP был бы самообманом.

---

## DRC before → after (сводка)

| | Verify | After |
|--|--------|-------|
| Violations | 543 | 536 |
| Unconnected | 9 | 11 |
| copper_edge | 2 | 0 |
| tracks_crossing | 77 | 69 |
| clearance | 81 | 61 |
| shorting_items | 110 | 124 |

Интерпретация: целевые геометрические блокеры сняты; общий short count держит **FFC pitch + старая SPI сетка**. Честно: pro-pass **не** довёл DRC до нуля.

---

## Alternatives considered

| Вариант | Решение |
|---------|---------|
| 4-layer для GND | Отклонён сейчас (scope 2L); рекомендуем позже |
| Сдвиг pogo | Запрещён требованиями |
| Удаление J_SWD | Отклонён (factory path нужен) |
| Слияние shorted nets | **Запрещено** правилами фикса |

---

## Risk register

| ID | Описание | S | L | Mitigation |
|----|----------|---|---|------------|
| P1 | Placeholder U1/U2 pin map | H | H | Реальные FP + re-route |
| P2 | FH12 0.5 mm solder_mask_bridge×200 | H | H | Vendor FP / mask sliver policy |
| P3 | SPI stubs / crossings | M | H | Перетрассировка после MCU FP |
| P4 | VSYS без via (только pad bridge) | L | M | Добавить stitch при необходимости |
| P5 | I_peak не измерены | M | H | Ток. проба на EVT |
| P6 | Security SW_DBG — courtyard рядом с J_SWD | M | M | Механика/крышка |

---

## Readiness

**FAIL** для заказа партии / sale.  
**PASS WITH RISKS** для lab bring-up **после** ручной проверки отсутствия питания↔GND на критичных парах в 3D/FA и замены U2 на реальный charger.

**Следующий наивысший leverage fix:** заменить U1/U2 на реальные footprint’ы и переразвести SPI fanout от нуля; иначе DRC short count не станет честным нулём.
