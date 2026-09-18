# POGO_SYNC — синхронизация PCB ↔ корпус (2×3 @ 3.0)

**Дата:** 2026-09-18 12:14 IDT  
**Case SoT:** `e-ink-watch-case/exports/POGO_MATRIX.txt`  
**PCB:** `e-ink-watch.kicad_pcb`

## Что сделано

1. Старый ряд **1×5 @ 2.54** (центр y=112.2) убран.
2. Поставлен массив **2×3, шаг 3.0 мм** на **B.Cu**, Ø1.5 мм, mask open, **без silk на pads**.
3. Координаты: `PCB=(100+case_x, 100−case_y)` — Y проверен по J_BAT (0,−15.8)→(100,115.8) и J_SWD (−11,−11.5)→(89,111.5).
4. Финальные pads (PCB mm):  
   - (93.00, 114.00) VCHG/`VBUS`  
   - (96.00, 114.00) GND  
   - (99.00, 114.00) SWDIO/`SWDIO_POGO`  
   - (93.00, 111.00) SWDCLK/`SWDCLK_POGO`  
   - (96.00, 111.00) nRESET/`nRESET_POGO`  
   - (99.00, 111.00) OPT/`OPT` (NC)
5. Добавлен **SW_DBG** @ (90.50, 105.50) F.Cu — DIP×3, по умолчанию OFF; рвёт только SWDIO/SWDCLK/nRESET к pogo. J_SWD остаётся на MCU. Зарядка (VBUS/GND) не коммутируется.
6. Короткие stub’ы: MCU↔J_SWD сохранены/добиты; pogo SWD идёт через SW_DBG.
7. Align корпуса: **±0.2 мм**.

## Не сделано / осторожно

- DRC **не** заявлять clean.
- Zone refill / полный DRC — вручную в KiCad.
- BOM PN для DIP — class footprint, не финальный.
