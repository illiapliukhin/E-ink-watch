# IP67 — влияние на PCB (E Ink Watch)

**Дата:** 2026-09-18 12:35 IDT  
**Цель корпуса:** IP67 design intent (не lab-certified)  
**SoT корпуса:** `/workspace/e-ink-watch-case/reports/IP67_SEALING.md`, `exports/SEAL_PARAMS.txt`  
**Pogo SoT:** `reports/POGO_PINOUT.md`

Этот файл — **список изменений / правил разводки**, которые нужны плате, чтобы sealed pogo и split-gasket работали. Саму `.kicad_pcb` здесь не правим (отдельный проход layout).

---

## 1. Обязательные правила под уплотнения

| # | Требование | Детали |
|---|------------|--------|
| P1 | **Keepout под pogo seal land** | На B.Cu вокруг матрицы TP1–TP6: зона ≈ envelope окна + **POGO_SEAL_MARGIN 1.8** mm. Без компонентов, шелкографии, открытой меди кроме 6 pads. |
| P2 | **No vias in seal land** | Запрет via / PTH / NPTH внутри seal envelope и под conductive pills. Via под pad = капилляр к внутренним слоям → обход elastomer. |
| P3 | **No via-in-pad на TP*** | Питание/сигналы подводить треком **вне** land, затем коротко к pad; или слепое/buried — не REV0. |
| P4 | **Mask opening только на pads** | B.Mask открыт на Ø pad (+tolerance); остальной seal land **под маской** (гладкая опора листа). |
| P5 | **ENIG / hard gold** на TP1–TP6 | Износ от pills/cradle; HASL нежелателен. |
| P6 | **Овальные pads (реком.)** | Вытянуть вдоль одной оси на ±0.15–0.2 мм под бюджет align ±0.2 case↔PCB. |
| P7 | **Gasket / boss keepout** | Кольцо под split cord проецируется на край PCB: не ставить высокие детали у края PCB (gasket R=20.7 на стенке корпуса); винтовые keepout на BC Ø35 уже нужны. |
| P8 | **SW_DBG internal only** | DIP на F.Cu; **без** требования отверстия в корпусе. Высота пакета — проверка vs battery tray / pogo channel. |
| P9 | **Edge clearance FPC 3/9** | Зоны выхода flex без via у края канала; паяные соединения ZIF не в «мокрой» зоне после plug. |
| P10 | **ESD у pogo** | TVS ближе к MCU/J_SWD, не обязательно в seal land; серии 22–100 Ω на SWD — вне land. |

---

## 2. Геометрия pogo (синхрон с корпусом)

| Параметр | Значение |
|----------|----------|
| Матрица | 2×3 @ **3.0** mm |
| Case origin | (−4.0, −12.5) |
| PCB | `(100+x, 100−y)` → TP1…TP6 как в `POGO_PINOUT.md` |
| Seal mode корпуса | **elastomer** (default), **глухие** wells, пол ≥0.55 mm |
| Seal sheet envelope (case) | **15.4 × 12.4 mm** (`POGO_MATRIX.txt`) |
| Сжатие cradle | 25–35% толщины sheet — PCB без бугров в land |
| Контакт | pills/inserts в wells → spring/flex на TP*; не открытые PTH сквозь back |
| Split gasket R | **20.7** (вне PCB OD; keepout высот у края платы) |

---

## 3. Изменения относительно текущего layout (чеклист)

Из `BOARD_VERIFY.md` уже есть блокеры — ниже только **IP67-добавки**:

1. [ ] Нарисовать `Keepout` / `Dwgs.User` контур **pogo seal land** (B.Cu side).  
2. [ ] DRC/rule: **no vias** в этом контуре (custom rule или ручная проверка).  
3. [ ] Убрать/перенести via под TP1 `VBUS` и dangling via у TP2 `GND` (уже flagged).  
4. [ ] Развести PTH `J_SWD` от TP4/5/6 (overlap ломает и электрику, и плоскую опору seal).  
5. [ ] Проверить silk: ничего под sheet.  
6. [ ] Документировать finish ENIG в fab notes.  
7. [ ] Опционально: тестовые купоны на панели под сжатие elastomer (не на часах).

---

## 4. Чего плата **не** делает

- Не сертифицирует IP67.  
- Не заменяет silicone cord / boots / FPC plugs.  
- SW_DBG OFF по умолчанию — security, не hydro barrier.

---

## 5. Вердикт для layout

Без **P1–P4** (keepout + no vias in seal land) sealed-pogo архитектура корпуса **недостижима** на уровне капилляров платы. Остальное — усиление надёжности контакта и сервиса.
