# CALC_POWER_TRACES — расчёт силовых трасс (REV0.2 fix+pro)

**Дата:** 2026-09-18 ~12:30 IDT  
**Стек:** 2L, Cu **1 oz ≈ 35 µm** (допущение fab)  
**Метод:** IPC-2221 external + IR drop; skill `pcb-physics-and-math`

---

## 1. Assumptions (явно)

| Параметр | Значение | Обоснование / риск |
|----------|----------|--------------------|
| Cu thickness | 1 oz (35 µm) | Типичный JLCPCB 2L; **не подтверждено** в fab notes |
| ρ_Cu (margin) | 2.0×10⁻⁸ Ω·m | +температура/старение vs 1.72e-8 |
| ΔT допустимый | 10 °C | Wearable, мало меди-радиатора |
| I_peak VBUS | **300 mA** | Класс BQ25120A charge; placeholder U2 |
| I_peak VBAT | **200 mA** | Разряд: refresh E Ink + MCU; без параллельной зарядки |
| I_peak VSYS | **200 mA** | После PMIC, до регуляторов |
| I_peak 3V3 | **50 mA** | nRF+BLE TX (~15–25 mA) + логика; **без** панели |
| I_peak 3V3_DISP | **120 mA** | Пик refresh маленькой E Ink (оценка 80–150 mA) |
| L_worst 3V3 | **35 mm** | Оценка самой длинной ветви MCU↔периферия/J_SWD |
| Цель IR drop 3V3 | **< 50 mV** @ peak | Бюджет для brown-out / ADC |

**Ограничения:** токи — **оценки**, не измерены на железе; U2/U1 — placeholder QFN, реальный BQ/nRF pinout может сместить пики.

---

## 2. IPC-2221 (external) — ширина vs ток

Формула: \( I \approx 0.048\,(\Delta T)^{0.44}\,A^{0.725} \), \(A\) в mil², \(t\approx 1.37\) mil.

| Нет | I_peak | w_IPC @10°C | w ×2 margin | Комментарий |
|-----|--------|-------------|-------------|-------------|
| VBUS | 0.30 A | ≈0.057 mm | ≈0.12 mm | IPC << fab comfort |
| VBAT | 0.20 A | ≈0.033 mm | ≈0.07 mm | то же |
| VSYS | 0.20 A | ≈0.033 mm | ≈0.07 mm | то же |
| 3V3_DISP | 0.12 A | ≈0.016 mm | ≈0.03 mm | то же |
| 3V3 | 0.05 A | ≈0.005 mm | ≈0.01 mm | то же |

**Вывод:** при этих токах **термика IPC не лимитирует**; лимит — IR drop, механическая надёжность, DRC/fab min, и требование проекта **≥0.45 mm** для power.

---

## 3. IR drop (DC)

\( R = \rho L / (w\,t) \), \( \Delta V = I R \).

| w | R @ L=35 mm | ΔV @ 50 mA | ΔV @ 150 mA |
|---|-------------|------------|-------------|
| 0.25 mm | 80 mΩ | 4.0 mV | 12 mV |
| 0.40 mm | 50 mΩ | 2.5 mV | 7.5 mV |
| **0.45 mm** | **44 mΩ** | **2.2 mV** | **6.7 mV** |
| 0.50 mm | 40 mΩ | 2.0 mV | 6.0 mV |

Все варианты **PASS** по бюджету <50 mV при заявленных токах. Выбрано **0.45 / 0.50 mm** по политике net-class + запас на более длинные/тонкие участки и via.

---

## 4. Via current (порядок величины)

Допущение: drill Ø0.3 mm, plating ~25 µm, h=1.6 mm  
\( R_\mathrm{via} \approx \rho h / (\pi d t_\mathrm{plate}) \approx 1.4\,\mathrm{mΩ} \) → @0.3 A ≈ 0.4 mV.

| Нет | Мин. vias (правило) | Факт на плате (после fix) | Статус |
|-----|---------------------|---------------------------|--------|
| VBUS | ≥2 | ≥3 (TP1 + 2 along path) | OK |
| VBAT | ≥2 | ≥2 | OK |
| 3V3 | ≥2 | несколько + zone | OK |
| 3V3_DISP | ≥2 | via farm F↔B | OK |
| GND | плоскость B.Cu | много stitch vias | OK |

---

## 5. Chosen geometry → net classes

| Class | Nets | Track | Clearance | Via |
|-------|------|-------|-----------|-----|
| PowerFat | VBAT, VBUS | **0.50 mm** | 0.15 mm | 0.6 / 0.3 |
| Power | 3V3, 3V3_DISP, VSYS, GND | **0.45 mm** | 0.15 mm | 0.6 / 0.3 |
| Signal | EPD_*, SWD*, nRESET*, BTN* | **0.18 mm** | 0.15 mm | 0.6 / 0.3 |

Записано в `e-ink-watch.kicad_pro` (`netclass_patterns`).

---

## 6. Verdict

**PASS WITH RISKS** для расчёта ширины при заявленных I_peak и 1 oz.  
**Не** верифицирует: реальный charger IC, измеренный refresh current, fab copper weight, PDN impedance выше десятков МГц.
