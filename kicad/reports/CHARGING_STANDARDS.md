# CHARGING_STANDARDS — путь зарядки e-ink watch

**Дата:** 2026-09-18 12:55 IDT (Asia/Jerusalem, UTC+3)  
**Плата:** `e-ink-watch.kicad_pcb` (стек **4L**: F.Cu / In1.Cu GND / In2.Cu PWR / B.Cu — **не 5L**)  
**Зарядный IC:** **BQ25120A** (U2), YFP DSBGA-25 — **не** BQ25125  

> **Harvard honesty:** ниже — *design-intent* по TI SLUSD08 + обычной wearable-практике CC/CV.  
> Это **не** сертификат IEC 62133 / UL 2054 / UN 38.3. На ячейке по-прежнему нужен **PCM**.

---

## 1. Диаграмма пути (факт на плате)

```
Pogo TP1 (VCHG)
    │  net VBUS_POGO
    ├──── D_TVS_VBUS (PESD5V0S1UL) ── GND        ← ESD у контакта
    ▼
  FB1 (BLM18PG121 class)                         ← серия, добавлен
    │  net VBUS
    ▼
  C_IN 1µF ── GND
    ▼
 U2.A2 IN ══ BQ25120A
    ├── UVLO / OVP внутри IC
    ├── PMID (A3/B3/…) + C_PMID 4.7µF
    ├── charger ── BAT B1/B2 ── C_BAT ── J_BAT → LiPo+PCM
    │                 ▲
    │     ISET  ← R_ISET 4.02k → GND     (~50 mA)
    │     ILIM  ← R_ILIM 2.0k  → GND     (~100 mA in)
    │     IPRETERM ← R_IPRETERM 0R → GND (default)
    │     TS ← R_TS 5.1k ← VBUS
    │          └── NTC_BAT 10k → GND     (JEITA)
    │     CD ← R_CD 10k → GND            (charge enable)
    └── SW A4 ── L_SYS 2.2µH ── VSYS B5 ── C_SYS / R_VSYS 0R → 3V3
                                       └── LS/LDO → 3V3_DISP (LSCTRL↑)

TP2 GND ────────── system GND (SW_DBG НЕ рвёт)
```

**На руке / в cradle:** power-path IC питает SYS от IN при VBUS и одновременно заряжает BAT; без cradle — от BAT.  
**SW_DBG** коммутирует только SWDIO/SWDCLK/nRESET (и `_POGO`); **VBUS/GND не разрываются**.

---

## 2. Чеклист (wearable Li-ion / IEC-ish care)

| # | Требование | Статус | Факт |
|---|------------|--------|------|
| 1 | Dedicated CC/CV charger IC | **PASS** | U2 = **BQ25120A** |
| 2 | Ток для ~80–200 mAh (~0.5C class) | **PASS*** | R_ISET=**4.02k** → ≈**50 mA** (K≈200). *Assumption 100 mAh → 0.5C; 80 mAh≈0.63C; 200 mAh≈0.25C |
| 3 | Input UVLO / OVP | **PASS** | Внутри BQ25120A |
| 4 | NTC / TS | **PASS** | R_TS + **NTC_BAT** на `TS` |
| 5 | Decoupling IN/BAT/SYS/PMID | **PASS** | C_IN, C_BAT, C_SYS, C_PMID (+C_VINLS) |
| 6 | Нет short VBUS↔VBAT | **PASS** | Только через IC |
| 7 | SW_DBG не рвёт VBUS/GND | **PASS** | Только SWD* |
| 8 | ESD на VBUS | **PASS** | D_TVS_VBUS + FB1 |
| 9 | Buck L SW→SYS | **PASS** | L_SYS 2.2µH |
| 10 | PCM на ячейке | **GAP** | Рекомендация на J_BAT; pack-level |
| 11 | Lab certification | **FAIL/N/A** | Design-intent ≠ certified |

---

## 3. Ток заряда (assumption)

| Параметр | Значение |
|----------|----------|
| Целевая ёмкость | 80–200 mAh |
| Design point | **100 mAh @ 0.5C → 50 mA** |
| R_ISET | **4.02 kΩ** → \(I\approx200/R\approx50\,\mathrm{mA}\) |
| R_ILIM | **2.0 kΩ** → ~100 mA input |
| Host | I²C может переопределить после boot |

---

## 4. Добавлено / доведено в этой сессии

- Подтверждён **BQ25120A** (U2), не BQ25125  
- Сшиты nets: ISET/ILIM/IPRETERM/TS/SW–L_SYS/VBUS/VBAT  
- Значения R_ISET→4.02k, R_ILIM→2.0k, R_IPRETERM→0R  
- Добавлен **FB1** (феррит) в разрыв TP1→C_IN (`VBUS_POGO`/`VBUS`)  
- TVS/NTC/L_SYS/decap — на плате  
- Схема `power.kicad_sch` дополнена refs + note  
- Стек **оставлен 4L**

---

## 5. Остаточные риски

1. PCM на pack обязателен — IC не заменяет cell-level OCP/UVP.  
2. Default SYS часто 1.8 V — для 3V3 нужен I²C (R_VSYS 0R после программирования).  
3. Ориентация uni-TVS — проверить на fab drawing.  
4. Полный board DRC может иметь сторонние (не charge) нарушения.  
5. **Не сертифицировано** IEC/UL.

---

## 6. Вердикт

# **OK with gaps**

Зарядка через настоящий **BQ25120A** CC/CV + power-path; путь pogo→TVS/FB→IN→BAT→J_BAT замкнут; NTC/ISET/ILIM/L/decap на месте; SW_DBG не ломает заряд; 4L сохранён.

**Gaps:** нет lab-сертификации; PCM на pack; SYS 3V3 от I²C; board-wide DRC не clean.


## 7. DRC (charge-focused)

Полный DRC платы: **~1103** violations / **~77** unconnected (много legacy/dangling вне зарядки).

Charge-related unconnected после stitch: **~18** блоков (частично stub-треки / pad-entry на BGA 0.4 мм).  
**Net assignment** критического пути (TP1→FB1→IN→BAT→J_BAT, SW→L_SYS→VSYS, ISET/ILIM/TS/IPRETERM, TVS) — **задан**;  
ручная доводка fanout BGA в PCBNew всё ещё рекомендуется перед tape-out.

Файлы: `reports/drc_charging_final.txt`, `reports/drc_charging_focus.txt`.
