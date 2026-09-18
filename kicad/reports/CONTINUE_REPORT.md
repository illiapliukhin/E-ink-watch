# CONTINUE_REPORT — продолжение разводки E Ink Watch PCB

**Дата:** 2026-09-18 (Asia/Jerusalem, UTC+3)  
**Проект:** `/workspace/e-ink-watch-kicad/`  
**Ревизия платы:** REV0.2 (route cleanup + zone fill + **pogo charge/SWD**)  
**Инструменты:** `tools/gen_pcb.py`, `pcbnew` ZONE_FILLER (без GUI), `kicad-cli pcb drc/export`

---

## 1. Что было не так (REV0.1)

- **34 unconnected** (KiCad): зоны GND не залиты → dangling via; часть pad (FPC pin9/10/MP, VBAT cluster U2, 3V3 кольцо) без связи.
- Трек **3V3 на B.Cu между F-падами без via**.
- Via **0.45/0.25** → `via_diameter` / `drill_out_of_range`.
- Наивный Manhattan → много `shorting_items` / crossings на Ø40.
- Нет пути **field flash/charge** кроме header SWD.

---

## 2. Что сделано

1. Переписан `build_routes` в `tools/gen_pcb.py`: lane/via-farm, via **0.6/0.3**, без via на 0.5 mm-pitch pad.
2. Добиты связи по documented pad-map: FPC GND pin9/MP, 3V3_DISP pin10, VBAT U2, 3V3 side pads через via.
3. **Zone fill** GND (B.Cu) + 3V3 (F.Cu) через pcbnew API.
4. **Pogo 5× Ø1.5 mm на B.Cu** (TP1–TP5): VBUS, GND, SWDIO, SWDCLK, nRESET @ 2.54 mm; параллель с J_SWD; stub VBUS к зоне U2 (пин PMIC TBD).
5. Документы: `POGO_PINOUT.md`, `STANDARDS_CHECK.md`, этот отчёт; SVG `docs/pcb_rev02.svg`.
6. DRC: `reports/drc_before.txt` → `reports/drc_after.txt`.

---

## 3. Unrouted / unconnected

| | Before | After |
|--|--------|-------|
| Unconnected (DRC) | **34** | **7** |

Оставшиеся 7 — в основном **GND**: MP strap/main (геометрия MP после поворота footprint), «острова» stubs vs pour/via. Не сигнал SPI/SWD/VBUS (VBUS pogo стыкован via-on-pad).

Каждый remaining — **не** «забытый net без pad map», а мелкие GND ties / island; полное зелье требует ручной подчистки или правильного MP local после rot.

---

## 4. DRC counts

| | Before | After |
|--|--------|-------|
| Total violations | **509** | **506** |
| unconnected_items | 34 | 7 |
| shorting_items | 116 | 109 |
| tracks_crossing | 22 | 74 |
| solder_mask_bridge | 205 | 199 |
| via_diameter + drill_out_of_range | 32 | **0** |

Итог: **unconnected сильно улучшен**; общее число violations почти то же из‑за intrinsic fine-pitch + более плотного SPI via farm (больше crossings формально). Это **не** green DRC.

---

## 5. Заблокировано до реальных footprint / datasheet

- nRF **QIAA** или модуль + BLE antenna keepout  
- **BQ25120A** реальный pinout (VBUS/I2C/TS) — сейчас stub VBUS  
- ZIF pinout панелей GDEY / flexible strap — **ASSUMPTION**  
- Кварцы + load caps, USB-C/pogo ESD TVS + series на SWD  
- Корпус Ø/отверстия под pogo, батарея SKU  
- 4-layer stackup (guidelines) — сейчас **2-layer** proto  

---

## 6. Артефакты

| Файл | Назначение |
|------|------------|
| `reports/drc_before.txt` | DRC до правок |
| `reports/drc_after.txt` | DRC после REV0.2+pogo |
| `reports/STANDARDS_CHECK.md` | чеклист норм (RU) |
| `reports/POGO_PINOUT.md` | распиновка cradle (RU) |
| `docs/pcb_rev02.svg` | превью Cu/Silk/Edge |
| `/workspace/e-ink-watch-kicad-rev02.tar.gz` | архив проекта |

---

## 7. Топ оставшихся рисков

1. Placeholder QFN ≠ production nRF/BQ — **не заказывать** без смены footprint.  
2. FPC pinout не сверен с панелью.  
3. Плотная разводка на Ø40: shorts/crossings на 0.5 mm pitch.  
4. VBUS не на реальном пине PMIC.  
5. Нет ESD/series на pogo SWD; нет antenna keepout.  
6. GND MP straps частично unconnected.
