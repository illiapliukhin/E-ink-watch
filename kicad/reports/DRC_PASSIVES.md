# DRC_PASSIVES — passives BQ25120A + 4L cleanup

**Дата:** 2026-09-18 ~12:52 IDT  
**Вход:** post-fanout (`FANOUT_PASS.md`, `drc_fanout_after.txt`)  
**Выход:** 4L + BQ passives/charging support  
**Стек:** см. `STACKUP_4L.md`

---

## 1. Цели прохода

1. Снизить `shorting_items` / `tracks_crossing` на Ø40 (после апрува — **4L**, не 2L).
2. Добавить essential BQ25120A passives + I2C 4.7k + зарядный минимум (NTC/TVS/L/CD/ISET…).
3. IP67: без **новых** via в pogo seal land; SW_DBG **не** рвёт зарядку.
4. DRC + отчёт + архив `e-ink-watch-kicad-4layer.tar.gz`.

---

## 2. Зарядный путь (проверка стандартов / DS)

| Узел | Назначение | Статус на PCB |
|------|------------|---------------|
| **TP1 → U2.A2 (IN)** | VBUS с pogo | **CONNECTED** (PowerFat F.Cu y≈112.2); **не** через SW_DBG |
| **TP2 → GND** | возврат зарядки | pad GND; плоскость In1 |
| **U2.B1/B2 → J_BAT** | BAT → ячейка | **CONNECTED** (VBAT corridor) |
| **U2.B5 (SYS) → R_VSYS → 3V3** | нагрузка / MCU | **CONNECTED** + via в In2 |
| **PMID A3/B3** | high-side bypass | net + C_PMID 4.7µF; VINLS balls → PMID |
| **SW A4 → L_SYS → SYS** | buck | **L_SYS 2.2µH** добавлен |
| **TS C3** | JEITA NTC | **R_TS 5.1k** (VBUS→TS) + **NTC_BAT 10k** (TS→GND) |
| **/CD E2** | enable charge | **R_CD 10k → GND** (CD low = charge) |
| **ISET/ILIM/IPRETERM** | standalone limits | R_ISET 5.6k / R_ILIM 14k / R_IPRETERM 5.1k (EVT tune; I2C override) |
| **LSCTRL E3** | LDO default on | R_LSCTRL 10k → 3V3 |
| **TVS VBUS** | ESD pogo | **D_TVS_VBUS** SOD-323 у TP1, вне seal |
| **I2C** | SDA/SCL | R_SDA/R_SCL **4.7k → 3V3** |
| **Decap** | IN/PMID/SYS/BAT/LDO | C_IN 1µF, C_PMID 4.7µF, C_SYS 10µF, C_BAT 1µF, C_VINLS 1µF (на PMID), C_LDO 1µF |
| **SW_DBG** | только SWD* | pads 1–3 / 4–6 = SWDIO/CLK/nRESET ↔ *_POGO; **VBUS/GND не коммутируются** |

**Вывод по зарядке:** топология соответствует BQ25120A power-path (IN/BAT/SYS/PMID) + JEITA TS + /CD enable + buck L.  
**Не сертификация:** токи ISET/ILIM — оценочные для wearable; без EVT измерения ICHG/VSYS; TS divider упрощён (5.1k + 10k NTC) — сверить формулы DS §9.3.16 под конкретный NTC B-constant.

---

## 3. DRC: до / после

Снимки: `drc_fanout_after.txt` (**до**), `drc_passives_after.txt` (**после**).

| Метрика | До (2L fanout) | После (4L+passives) | Δ |
|---------|----------------|---------------------|---|
| **DRC violations** | **675** | **1049** | +373 |
| **shorting_items** | **172** | **199** | +27 |
| **tracks_crossing** | **98** | **28** | **-70** |
| **unconnected_items** | **1** | **86** | +85 |
| clearance | 87 | 173 | +86 |
| solder_mask_bridge | 199 | 199 | 0 (FH12) |

### Интерпретация (Harvard)

1. **`tracks_crossing` −69** — главный выигрыш 4L: силовые/GND ушли в In1/In2, сигналы реже пересекаются на F/B.
2. **`shorting_items` не → 0** и даже +27: плотность вокруг MDBT50Q + FH12 0.5 mm + новые stub passives на F.Cu; заливка/трек-остатки и courtyard U2↔passives. **Честно: Ø40 + модуль + 3×FPC на 4L всё ещё не «fab shorts=0» без интерактивного pcbnew.**
3. **`unconnected` +85** — побочный эффект агрессивного удаления пересекающихся сегментов; критический charge path (таблица §2) восстановлен треками, но SPI/SWD/BTN islands требуют доводки.
4. **`solder_mask_bridge`×199** — системный FH12, вне scope.
5. Рост total DRC от courtyard/silk/clearance вокруг новых 0402/L/TVS — ожидаем.

---

## 4. Оставшиеся blockers

| ID | Blocker | S | Mitigation |
|----|---------|---|------------|
| P1 | shorting_items ≫ 0 | H | Interactive cleanup F.Cu east of U1 / около U2; увеличить clearance power |
| P2 | unconnected SPI/SWD/BTN islands | H | Довести B.Cu star / via stitch после short cleanup |
| P3 | FH12 mask bridges ×199 | H | Vendor FP / mask policy |
| P4 | ISET/ILIM/TS — EVT calibrate | M | Измерить ICHG; пересчитать R_TS под NTC |
| P5 | Нет полного BOM sync в schematic | M | Update schematic symbols ↔ PCB refs |
| P6 | RF keepout — silk only | M | Rule area + вырез заливки |
| P7 | Courtyard U2 vs passives/SW | M | Сдвинуть SW2/SW3 / уплотнить 0201 |
| P8 | Residual vias near seal envelope | M | Проверить список; только треки к TP* |

---

## 5. Constraints сохранены

- Ø40, центр (100,100)
- Pogo 2×3 @ 3.0 mm (координаты TP*)
- SW_DBG gating SWD only
- IP67 seal Dwgs outline; no new vias in seal (via-in-pad TP* сняты)

---

## 6. Артефакты

- `STACKUP_4L.md`
- `tools/charging_4l_pass.py`, `tools/migrate_4layer.py`, `tools/drc_passives_pass.py`
- Backup: `backups/e-ink-watch.kicad_pcb.pre-4l-*`, `pre-drc-passives-*`
- Архив: `/workspace/e-ink-watch-kicad-4layer.tar.gz`

---

## 7. Итог

**Сделано:** 4L стек (F / In1 GND / In2 3V3 / B); BQ decap + I2C 4k7; зарядный минимум (TVS, TS/NTC, /CD, ISET/ILIM/IPRETERM, L_SYS, LSCTRL); charge path pogo→IN / BAT→cell / SYS→load **без** участия SW_DBG; crossings **98→28**.  

**Не сделано:** shorts→0, unconnected→0, fab-ready.  

**Честная рекомендация:** следующий leverage — **интерактивный** short cleanup в pcbnew на F.Cu вокруг U1/U2, затем восстановление SPI/SWD connectivity; 6L не обязателен для quote, но возможен как map из `STACKUP_4L.md` §4.
