# POWER_SHORTS_FIX — критические КЗ питания

**Дата:** 2026-09-18 13:10 IDT (Asia/Jerusalem, UTC+3)  
**Плата:** `e-ink-watch.kicad_pcb` (4L)  
**Бэкап:** `backups/e-ink-watch.kicad_pcb.pre-power-shorts-130714`  
**DRC до:** 1107 (shorting_items=199) → **после:** 983 (shorting_items=185)

> **VBUS НЕ подавать**, пока не закрыты оставшиеся pad-pad КЗ на 3V3/FH12/L_SYS (см. STUCK).  
> Цель сессии: **GND↔VBUS = 0**, **GND↔VBAT = 0** — **достигнута**.

---

## Before / After (приоритетные пары)

| Пара | До | После | Статус |
|------|----|-------|--------|
| **GND ↔ VBUS** | **11** | **0** | **PASS** |
| **GND ↔ VBAT** | **8** | **0** | **PASS** |
| **GND ↔ VBUS_POGO** | **2** | **0** | **PASS** |
| TS ↔ VBAT | 2 | **0** | **PASS** |
| VBAT ↔ VBUS | 0 | **0** | **PASS** |
| 3V3_DISP ↔ VBAT | 2 | **0** | **PASS** |
| 3V3 ↔ VBAT | 1 | **0** | **PASS** |
| 3V3 ↔ 3V3_DISP | 9 | **0** | **PASS** |
| 3V3_DISP ↔ GND | 6 | **3** | STUCK (FH12 pad↔pad) |
| 3V3 ↔ GND | 2 | **2** | STUCK (Ø40 placement) |
| GND ↔ SW | 1 | **2** | STUCK (C_SYS/C_VINLS↔L_SYS) |

---

## Что сделано (только медь; топология заряда сохранена)

### Класс 1 — GND ↔ VBUS (C_IN)
- Удалены горизонтали VBUS `(108.12,104.5)→(110.6,104.5)` — шли **через** GND-пад C_IN.
- Удалены южные стабы VBUS в сторону C_BAT и fake-via GND `@108.5,104.0` у VBUS-пада.
- Новый коридор: C_IN.pad1 → `(108.12,103.7)` → `(110.6,103.7)` → U2.A2 (восточнее R_VSYS).
- R_TS→VBUS: `(107.69,107)→(105.5,107)→(105.5,103.7)` join в тот же коридор (западнее VBAT @x=106.2).

### Класс 2 — GND ↔ VBAT (C_BAT / NTC)
- Удалены VBAT через тело C_BAT и лонг `@y=107.9` через NTC.GND.
- Удалён лонг `@y=105.6` через C_BAT.
- Новый коридор севернее конденсаторов: U2.B1 → y=106.4 → x=106.2 → J_BAT column.
- NTC.GND: восток→юг + via `@109.6,107.2` (вне seal keepout).

### Класс 3 — GND ↔ VBUS_POGO (D_TVS)
- Удалены треки VBUS_POGO через оба пада SOD-323.
- Обход: pad1 → `(88.15,111.6)` → `(93,111.6)` → join TP1/FB1 (без новых via в seal).

### Класс 4–5 — домены / TS
- Зачищены пересечения 3V3↔3V3_DISP (в т.ч. stacked B.Cu @x=84.45).
- TS: Manhattan `@y=107.3` вместо диагонали через VBAT; **TS↔VBAT = 0**.

---

## Preserve checklist

| Инвариант | Статус |
|-----------|--------|
| TP1 → FB1/TVS → U2.IN → BAT → J_BAT | **OK** (pad nets проверены) |
| SW_DBG только SWDIO/SWDCLK/nRESET(*) | **OK** |
| 4L stack | **OK** |
| Pogo matrix | **OK** |
| IP67 seal keepout (нет новых via в land) | **OK** |

---

## STUCK — честно про Ø40 / density

Оставшиеся КЗ — **pad↔pad** (не трек через чужой пад):

1. **3V3_DISP ↔ GND ×3** — соседние пины FH12-10S (0.5 mm pitch):  
   J_STRAP_L pad1/2, pad9/10; J_STRAP_R pad1/2.  
   Нужен другой FP / custom pad shrink / clearance exemption — **не** лечится delete трека.

2. **3V3 ↔ GND ×2** — слишком близкая посадка:  
   C_LDO.1(GND) ↔ R_LSCTRL.2(3V3); U1.GND ↔ R2.1(3V3).  
   Нужен сдвиг footprint ≥0.15–0.3 mm.

3. **GND ↔ SW ×2** — C_SYS / C_VINLS GND-пады рядом с L_SYS.pad1(SW).  
   Нужен сдвиг L_SYS или конденсаторов.

Пока эти pad-pad живы, **плата не fab-ready** для «зелёного» DRC, но **критическое КЗ зарядки на землю снято**.

---

## Рекомендация по питанию

| Вопрос | Ответ |
|--------|-------|
| Подавать VBUS на pogo? | **НЕТ**, пока не разведены pad-pad 3V3/FH12/SW (или не принят риск/waiver) |
| GND↔VBUS / GND↔VBAT copper short? | **Нет (×0)** |
| Charge path topology? | **OK** |

Архив: `/workspace/e-ink-watch-kicad-power-shorts.tar.gz`  
DRC: `reports/drc_power_shorts_final.txt`

---

## Pad-pad nudge follow-up (2026-09-18 13:22 IDT)

**Backup:** `backups/e-ink-watch.kicad_pcb.pre-padpad-nudge-131921`  
**DRC:** 983 → **947** (shorting 185 → **179**)  
**Tool:** `tools/power_padpad_nudge.py` + cleanup passes

| Пара | До | После | Метод |
|------|----|-------|-------|
| 3V3_DISP ↔ GND | 3 | **0** | FH12 signal pads size swap → 1.3×0.3 (0.3 along pitch); 3V3_DISP bus @ x=85 south of J_SWD |
| 3V3 ↔ GND | 2 | **0** | R_LSCTRL → (114.60,108.25); R2 → (105.65,95.50) |
| GND ↔ SW | 2 | **0** | L_SYS → (116.35,104.50); C_SYS/C_VINLS → x=112.80; SW corridor y=105.2 |
| GND ↔ VBUS / VBAT / VBUS_POGO | 0 | **0** | preserved (VBUS corridor y=102.9 clear of R_ISET) |
| 3V3 ↔ 3V3_DISP | 0 | **0** | preserved |

### Preserve
- 4L stack: OK
- SW_DBG SWD-only: OK
- Charge path TP1→FB1/TVS→U2→BAT→J_BAT: OK
- Pogo seal: no new vias in land

### VBUS?
**НЕТ** — глобальные shorting_items ещё 179 (не power-priority). Критические power-пары сессии = 0.

