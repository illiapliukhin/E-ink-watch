# ROUTE_NOTES — PCB REV0.1 (разводка placeholder)

Кратко: размещение + питание + SPI без GUI (`tools/gen_pcb.py`). Footprint — stand-in (QFN-48≠QIAA, QFN-16≠BQ25120A).

## Размещение (центр 100,100; Ø40 мм; keepout ~0.9 мм)

| Ref | Роль | Позиция |
|-----|------|---------|
| U1 | nRF (QFN-48) | центр, чуть выше |
| U2 | PMIC (QFN-16) | под U1 |
| C1–C4, R1–R2 | развязка / pull-up | рядом с U1/U2 |
| J_DISP_MAIN | FPC main | 12 ч |
| J_STRAP_L / R | FPC ремешок | 9 / 3 ч |
| J_BAT | LiPo 1×02 | 6 ч |
| SW1–3 | кнопки | нижняя-правая дуга |
| J_SWD | SWD 1×05 | нижний-левый |

## Карта пинов (допущения)

**FPC 10 pin (все три разъёма):**  
1=`3V3_DISP`, 2=`GND`, 3=`EPD_MOSI`, 4=`EPD_SCK`, 5=`CS` (MAIN/L/R), 6=`EPD_DC`, 7=`EPD_RST`, 8=`BUSY` (MAIN/L/R), 9=`GND`, 10=`3V3_DISP`, MP=`GND`.  
Сверка с lot GDEY/Waveshare обязательна.

**U1 QFN-48 (логический map, не QIAA):**  
верх 40–45 → SCK/MOSI/DC/RST/CS_MAIN/BUSY_MAIN; лево 3–4 → CS_L/BUSY_L; право 28–29 → CS_R/BUSY_R; низ 15–18 → 3V3/GND; 10–12 → SWD; 22–24 → BTN; EP49=`GND`.

**U2 QFN-16:** 1/2/15/16=`VBAT`, 5/6/13/14/17=`GND`, 7/8=`VSYS`, 9/10=`3V3`, 11/12=`3V3_DISP`.

**J_BAT:** 1=`VBAT`, 2=`GND`. **J_SWD:** 1=`3V3`, 2=`SWDIO`, 3=`SWDCLK`, 4=`nRESET`, 5=`GND`.

## Трассы / зоны

- Сигнал 0.18 мм; питание 0.4–0.5 мм.
- SPI shared + CS/BUSY → три FPC; strap частично через B.Cu + via.
- Зоны: **GND на B.Cu** (круг ~Ø38.2), **3V3 на F.Cu** (внутренний ~Ø24).
- Star GND: vias с площадок в B.Cu pour.

## Риски DRC

- Пересечения Manhattan / близкие via у QFN — ожидаемы на REV0.1.
- Courtyard FPC vs край Ø40: запас ~3–4 мм по центру, тело FH12 может жать Edge.Cuts.
- Нет filled_polygon (заливка при открытии в pcbnew).
- Нет net-tie / thermal relief тонкой настройки; NFC нет.


## REV0.2 addendum — Pogo cradle

- 5× Ø1.5 mm pads on **B.Cu**, pitch 2.54 mm, y≈112.2: TP1 VBUS, TP2 GND, TP3 SWDIO, TP4 SWDCLK, TP5 nRESET.
- Primary field flash+charge; `J_SWD` remains factory backup (paralleled).
- Details: `reports/POGO_PINOUT.md`. Via size now 0.6/0.3; zones filled via pcbnew.
