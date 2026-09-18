# STANDARDS_CHECK — PCB E Ink Watch (REV0.2 route + pogo)

**Дата:** 2026-09-18 (Asia/Jerusalem, UTC+3)  
**Источники норм:** `docs/PCB_GUIDELINES.md`, `DESIGN_NOTES.md`, `tools/ROUTE_NOTES.md`, DRC KiCad 9.0.2  
**Честность:** footprint **PLACEHOLDER** (QFN-48 ≠ nRF QIAA; QFN-16 ≠ BQ25120A). FPC pinout — **ASSUMPTION**.

---

## 1. Clearance track/via/pad vs Edge.Cuts

| Критерий | Цель | Факт | Статус |
|----------|------|------|--------|
| Зазор Cu → Edge.Cuts | ≥0.25–0.3 мм (proto); в `.kicad_pro` min_copper_edge_clearance **0.5** мм | keepout генератора ~0.9 мм от Ø40; min track-end→edge ≈ **>3** мм на основных трассах; FPC/J_BAT ближе по courtyard | **OK** по краю круга; courtyard FPC vs край — риск механики (см. ROUTE_NOTES) |
| Silk vs edge | warning | 1× silk_edge_clearance в DRC | WARN |

---

## 2. Min track width

| Класс | Цель | Факт | Статус |
|-------|------|------|--------|
| Сигнал | ≥0.15 мм | **0.18** мм | **OK** |
| Питание | ≥0.3–0.4 мм | **0.40 / 0.50** мм | **OK** |

---

## 3. Via (2-layer proto)

| Параметр | Цель | Факт | Статус |
|----------|------|------|--------|
| Size/drill | напр. 0.3/0.6 | **0.6 / 0.3** мм | **OK** (min_via_diameter проекта 0.5) |
| REV0.1 наследие | 0.45/0.25 → drill_out_of_range / via_diameter | исправлено в генераторе | fixed |

---

## 4. Antenna keepout (BLE)

| Пункт | Статус |
|-------|--------|
| Чип-антенна / модуль на placeholder QFN **отсутствует** | N/A физически |
| NFC снят (BLE-only) | OK по DESIGN_NOTES |
| Заметка: при замене на MDBT50Q / QIAA+chip ant — keepout без copper stub, батарея не под антенной | **TODO** (не разведено) |

---

## 5. Decoupling proximity

| Компонент | Расстояние (центр) | Оценка |
|-----------|-------------------|--------|
| C1/C2 (100n) → U1 | ~5.1 мм | приемлемо для концепта; цель &lt;2–3 мм на реальном QIAA |
| C3/C4 (10u) → U2 | ~3.3 мм | OK для proto |
| Кристаллы Y1/Y2 + load caps | **нет на PCB** | блок схемы есть; на плате **не размещены** |

---

## 6. Crystal load caps

**Отсутствуют** на `e-ink-watch.kicad_pcb`. Не утверждать размещение/ёмкости до footprint кварцев.

---

## 7. FPC connector pinout — ASSUMPTIONS

Карта 10-pin (все три ZIF) из `ROUTE_NOTES.md`:

`1=3V3_DISP, 2=GND, 3=MOSI, 4=SCK, 5=CS, 6=DC, 7=RST, 8=BUSY, 9=GND, 10=3V3_DISP, MP=GND`

⚠️ **Не verified** против lot GDEY0154D67 / Waveshare 2.13 Flexible. Перед заказом FPC/PCB — сверить datasheet панели.

---

## 8. Footprints = PLACEHOLDERS (не production)

| Ref | Stand-in | Реал |
|-----|----------|------|
| U1 | QFN-48-1EP 7×7 | nRF52840 **QIAA/CKAA** или модуль MDBT50Q / XIAO |
| U2 | QFN-16-1EP 3×3 | **BQ25120A** DSBGA (не смешивать с BQ25155) |
| J_* FPC | Hirose FH12-10S | ZIF под купленную панель |
| TP1–5 | custom Ø1.5 B.Cu | OK как контакт; ENIG в спецификации FAB |

Явно: **не** QIAA/BQ production-ready.

---

## 9. Pogo (REV0.2)

См. `reports/POGO_PINOUT.md`. 5 pads B.Cu @ 2.54 мм; J_SWD сохранён. ESD/series — **заметка**, в BOM платы пока нет.

---

## 10. DRC summary (severity-all)

| | before (REV0.1) | after (REV0.2+pogo) |
|--|-----------------|---------------------|
| Violations | **509** | **506** |
| Unconnected | **34** | **7** |
| shorting_items | 116 | 109 |
| tracks_crossing | 22 | 74 |
| solder_mask_bridge | 205 | 199 |
| drill_out_of_range / via_diameter | 16+16 | **0** |

Большинство оставшихся short/clearance — **0.5 mm pitch** QFN/FPC pad-pad и плотная Manhattan-разводка на Ø40; не маскировать как «чисто».

---

## 11. Pogo cradle + SW_DBG (2026-09-18 12:14 IDT)

- Case SoT: **2×3 @ 3.0 mm**, align **±0.2 mm** (`POGO_MATRIX.txt`).
- PCB pads TP1–TP6: см. `POGO_PINOUT.md` / `POGO_SYNC.md`.
- **SW_DBG** (DIP×3, F.Cu (90.5, 105.5)): series disconnect SWDIO/SWDCLK/nRESET к pogo; VCHG/GND всегда; завод = OFF.
- J_SWD factory header **до** переключателя (всегда на MCU).
- DRC после правки: **не verified clean**.
