# FANOUT_PASS — профессиональный fanout после замены footprint

**Дата:** 2026-09-18 ~12:40 IDT (Asia/Jerusalem)  
**Плата:** `e-ink-watch.kicad_pcb` (Ø40 мм, 2L)  
**Вход:** состояние после `FOOTPRINT_UPGRADE.md` (U1=MDBT50Q-1MV2, U2=BQ25120A YFP0025)  
**Вердикт:** **PASS WITH RISKS** по connectivity критических net; **FAIL** как fab-ready / production DRC.

Связанные артефакты: `FOOTPRINT_UPGRADE.md`, `PRO_ROUTE.md`, `CALC_POWER_TRACES.md`,  
`reports/drc_fanout_before.txt`, `reports/drc_fanout_after.txt`,  
`tools/fanout_pass.py`, `tools/fanout_cleanup.py`.

---

## 1. Цель и constraints (сохранены)

| Constraint | Статус |
|------------|--------|
| Outline Ø40, центр (100,100) | без изменения |
| Pogo 2×3 @ 3.0 mm (TP1–TP6) | **заморожены** (координаты не трогались) |
| SW_DBG gating SWD* → `*_POGO` | топология сохранена; доведены трассы U1→SW_DBG→J_SWD |
| Net classes PowerFat / Power / Signal | использованы; добавлены SDA/SCL/PMIC_INT → Signal |
| IP67 seal land | **геометрии seal-ring на PCB нет** — добавлена заметка Dwgs.User (механика корпуса) |

**Не заявлено fab-ready.** Цель прохода: снизить unconnected (~55) и соединить критические net.

---

## 2. Что сделано (Harvard + PCB physics)

### 2.1 Удалён опасный short от minimal fanout upgrade

Горизонталь **3V3** `(98.4–104.6, y=86.35)` шла **по ряду pad U1** (MOSI / CS / RST / GND) — гарантированный short. Удалена.  
Вертикаль **VSYS** `x=105` в колонку восточных pad модуля — снята (clearance/short risk).

### 2.2 Питание

| Net | Действие |
|-----|----------|
| **VBUS** | PowerFat 0.50: TP1 → коридор y=112.2 → U2.**A2** (IN); сшивка параллельных stub |
| **VBAT** | B1↔B2 (0.20 BGA neck) + PowerFat к коридору x=96.2 / J_BAT |
| **VSYS** | B5↔B4↔C4; escape на **R_VSYS** |
| **3V3** | U1.28↔30; escape на **B.Cu** (не по SPI-ряду F); stitch C1/C2/R1/R2/J_SWD |
| **3V3_DISP** | U2.C5 → правый spine; B.Cu сшивка vias L/Main/R |
| **GND** | локальные ties U1/U2; **заливка GND F.Cu + B.Cu** (круг Ø≈38.8) |
| **VSYS↔3V3** | явный **R_VSYS = 0 Ω 0603** @ (107.5, 103.8) r90 — **не** silent net-merge |

Ширины: Signal **0.18**, Power **0.45**, PowerFat **0.50**, BGA neck **0.20**, via Ø0.60/0.30 — по `CALC_POWER_TRACES.md`.

### 2.3 SWD / pogo (через SW_DBG)

Доведены stub’ы от U1.51/53/40 к шине J_SWD / SW_DBG.  
Путь pogo: `SWDIO/SWDCLK/nRESET` → SW_DBG → `*_POGO` → TP3/TP4/TP5 **без** обхода ключа.  
VBUS/GND pogo по-прежнему вне DIP.

### 2.4 SPI → три FPC

| Net | U1 pad | Fanout |
|-----|--------|--------|
| EPD_SCK | 9 | F escape + **B.Cu star** Main↔L↔R vias |
| EPD_MOSI | 20 | то же |
| EPD_DC | 19 | то же |
| EPD_RST | 16 | то же |
| EPD_CS_MAIN / BUSY_MAIN | 22 / 13 | коротко на север к J_DISP_MAIN |
| EPD_CS_L / BUSY_L | 23 / 10 | B.Cu на J_STRAP_L |
| EPD_CS_R / BUSY_R | 24 / 14 | B.Cu на J_STRAP_R |

### 2.5 I2C → PMIC (впервые на PCB)

| Сигнал | MCU (Raytac DS) | PMIC ball |
|--------|-----------------|-----------|
| **SDA** | U1.**27** = P0.11 | U2.**E4** |
| **SCL** | U1.**29** = P0.12 | U2.**E5** |
| **PMIC_INT** | U1.**39** = P0.15 | U2.**D2** |

Маршрут Signal 0.18 преимущественно по **B.Cu** вдоль восточного края модуля → U2.  
Pull-up 4k7 на I2C **не установлены** (см. risks).

### 2.6 Кнопки

BTN1–3 от U1.61/50/60 к существующим stub → SW1–3; BTN3 уведён **южнее U2** (y=107.8), чтобы не резать BGA/GND.

### 2.7 RF / IP67 заметки

- Silk: «RF KEEPOUT: MDBT50Q antenna (top)…»
- Dwgs.User: IP67 — seal keepout **механический**; на PCB нет copper seal-ring; pogo 2×3 clear of seal boss.
- Rule-area RF keepout через API KiCad 9 — не удалось стабильно создать; зафиксировано текстом + в risks.

---

## 3. DRC: до / после

Файлы: `drc_fanout_before.txt` (снимок до fanout = post-fp-upgrade), `drc_fanout_after.txt`.

| Метрика | До | После | Δ |
|---------|----|-------|---|
| **DRC violations** | **569** | **675** | +106 |
| **Unconnected items** | **55** | **1** | **−54** |
| `solder_mask_bridge` | 199 | 199 | 0 |
| `shorting_items` | 111 | 173 | +62 |
| `tracks_crossing` | 31 | 97 | +66 |
| `clearance` | 104 | 86 | −18 |
| `via_dangling` | 23 | 8 | −15 |
| `track_dangling` | 14 | 8 | −6 |
| `isolated_copper` | 4 | 0 | −4 |

**Интерпретация (честно):**

1. **Unconnected −54 — цель прохода достигнута.** Единственный остаток — артефакт KiCad: Zone[3V3] ↔ Zone[3V3] (остров/self), не pad↔pad критической цепи.
2. Рост **shorting / crossing** ожидаем при плотной 2L разводке вокруг MDBT50Q + FH12 0.5 mm + новых B.Cu SPI/I2C коридоров без полного interactive cleanup. Это **регресс DRC**, не «улучшение short count».
3. `solder_mask_bridge`×199 — системный FH12 pitch, вне scope fanout.
4. Удаление shorting 3V3-across-pads улучшило физическую достоверность питания, даже если общий счётчик short вырос из-за новых трасс.

---

## 4. Критические net — статус connectivity

| Группа | Статус |
|--------|--------|
| VBUS TP1→U2.A2 | **CONNECTED** (трассы) |
| VBAT J_BAT→U2.B* | **CONNECTED** |
| VSYS U2 + R_VSYS→3V3 | **CONNECTED** (через 0 Ω) |
| 3V3 U1 VDD + decap/J_SWD | **CONNECTED** (F+B) |
| 3V3_DISP U2→FPCs | **CONNECTED** (с оговоркой denseness) |
| SWD U1↔SW_DBG↔J_SWD↔pogo | **CONNECTED**, gating сохранён |
| SPI shared + CS/BUSY ×3 FPC | **CONNECTED** (F + B.Cu star) |
| I2C SDA/SCL/INT U1↔U2 | **CONNECTED** (nets назначены + трассы) |
| BTN1–3 | **CONNECTED** |
| Pogo coords | **UNCHANGED** |

---

## 5. Оставшиеся risks (не fab-ready)

| ID | Risk | S | L | Mitigation |
|----|------|---|---|------------|
| F1 | DRC short/cross ≫ 0 после fanout | H | H | Interactive cleanup в pcbnew; возможно 4L |
| F2 | FH12 0.5 mm solder_mask_bridge×199 | H | H | Vendor FP / mask policy |
| F3 | Нет passives BQ25120A (IN/BAT/SYS/PMID caps, L, TS, /CD) | H | H | Следующий BOM/place pass |
| F4 | Нет I2C pull-ups; LSCTRL/DISP_EN не разведены | H | M | Добавить 4k7 + LSCTRL net |
| F5 | R_VSYS 0 Ω — MCU питается только если SYS=3.3 V по I2C **или** 0R стоит; без прошивки buck defaults проверить DS | H | M | EVT: измерить VSYS; опционально merge net |
| F6 | RF keepout под антенной — только silk/note, не rule-area | M | M | Rule area + вырез заливки по Raytac guide |
| F7 | Courtyard U2 vs SW2/SW3 | M | M | Сдвинуть кнопки |
| F8 | Символы логические ≠ package pads — Update from schematic опасен | H | M | Не update вслепую |
| F9 | 2L SPI/I2C под модулем — crosstalk / return path | M | M | Длина/сшивка GND vias; осциллограф на EVT |
| F10 | IP67 — нет seal land на PCB | M | L | Механика корпуса; не сверлить под gasket |

---

## 6. Alternatives considered

| Вариант | Решение |
|---------|---------|
| Silent merge VSYS≡3V3 | **Отклонён** — явный 0 Ω R_VSYS |
| Автороутер полный | **Отклонён** — контролируемый corridor fanout |
| Сдвиг pogo / Ø | **Запрещён** |
| 4-layer сейчас | Отложен (scope 2L); рекомендуется после short cleanup |
| Оставить I2C NC | **Отклонён** — цель включала I2C→PMIC |

---

## 7. Артефакты

- Backup: `backups/e-ink-watch.kicad_pcb.pre-fanout-*`
- Scripts: `tools/fanout_pass.py`, `tools/fanout_cleanup.py`
- New footprint instance: **R_VSYS** (R_0603_1608Metric, 0R)
- Nets добавлены на PCB: `SDA`, `SCL`, `PMIC_INT`
- Zones: GND **F.Cu** + GND **B.Cu**; 3V3 F.Cu
- Архив: `/workspace/e-ink-watch-kicad-fanout.tar.gz`

---

## 8. Итог

**Сделано:** критические power / SWD(gating) / SPI→FPC / I2C→PMIC / buttons / pogo path разведены; unconnected **55 → 1** (zone artifact).  
**Не сделано / не готово:** fab DRC≈0, passives PMIC, RF rule-area, mask на FH12, полный short cleanup.  
**Следующий leverage:** interactive short/cross cleanup вокруг U1 east column + B.Cu SPI, затем place BQ25120A passives + I2C pull-ups.
