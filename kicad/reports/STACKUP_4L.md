# STACKUP_4L — стек 4 медных слоя (Ø40 e-ink watch)

**Дата:** 2026-09-18 ~12:52 IDT (Asia/Jerusalem)  
**Файл:** `e-ink-watch.kicad_pcb`  
**Толщина платы (допущение):** 1.6 mm FR-4  

---

## 1. Назначение слоёв

| # | Слой | Тип | Назначение |
|---|------|-----|------------|
| 1 | **F.Cu** | signal | Компоненты, fanout, силовые stub (VBUS/VBAT/VSYS/PMID), локальные escapes |
| 2 | **In1.Cu** | power | **Сплошная GND-плоскость** (круг Ø≈38.8) |
| 3 | **In2.Cu** | power | **Заливка 3V3** (плоскость питания MCU / pull-ups) |
| 4 | **B.Cu** | signal | Pogo pads (TP*), вторичные сигналы (SPI star / I2C / BTN), лёгкая GND-заливка |

---

## 2. Физика / fab notes

| Параметр | Значение | Комментарий |
|----------|----------|-------------|
| Cu weight | 1 oz (допущение) | Как в `CALC_POWER_TRACES.md` |
| Via | Ø0.60 / drill 0.30 | Through F↔B (шьёт In1/In2) |
| PowerFat | 0.50 mm | VBUS, VBAT |
| Power | 0.45 mm | VSYS, 3V3_DISP stubs |
| Signal | 0.18 mm | SWD / SPI / I2C / BTN |
| BGA neck | 0.20 mm | U2 YFP 0.4 mm pitch |

**IR drop:** при In2-плоскости 3V3 и In1-return пути MCU→периферия короче, чем на 2L spine; бюджет <50 mV @ 50 mA сохраняется с запасом.

---

## 3. IP67 / pogo

- Seal keepout (Dwgs.User): ≈ x=90.5…101.5, y=108.5…117 (матрица 2×3 @ 3.0 mm + margin).
- **Новые via в seal land запрещены**; via-in-pad на TP* удалялись.
- VBUS/GND зарядки идут **в обход SW_DBG** (DIP только SWD*).

---

## 4. 4L vs 6L (честно для JLCPCB / fab)

Многие PCB-houses (в т.ч. JLCPCB) **предпочитают чётные стеки 4/6/8**.  
Чистый **5L нестандартен**; **4L — нормальный quote**.

Если fab настаивает на 6L при том же электрическом замысле:

| 4L | → 6L (опционально) |
|----|---------------------|
| F.Cu | F.Cu |
| In1 GND | In1 GND |
| — | In2 GND или signal reference |
| In2 3V3 | In3 3V3 / power |
| — | In4 split VBAT/VBUS или GND |
| B.Cu | B.Cu |

Для текущего REV достаточно **4L**.

---

## 5. Вердикт

**4L включён и задокументирован.** Плоскости In1=GND / In2=3V3 заполнены.  
Не fab-ready DRC≈0 — см. `DRC_PASSIVES.md`.
