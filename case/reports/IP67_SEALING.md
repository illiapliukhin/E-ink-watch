# IP67 — герметизация корпуса E Ink часов (design intent)

**Дата:** 2026-09-18 12:36 IDT (Asia/Jerusalem, UTC+3)  
**Цель:** **IP67** (IEC 60529): пыленепроницаемость + погружение **1 м / 30 мин**.  
**Статус:** `IP_CERTIFIED=False` — **только design intent**. Заявлять IP67 на продукте **нельзя** до лабораторного теста на собранном образце.

Связанные файлы: `src/watch_case.py` (`IP_TARGET`, `POGO_SEAL_MODE`, `SEAL_*`), `MECHANICAL.md`, `exports/SEAL_PARAMS.txt`, `/workspace/e-ink-watch-kicad/reports/IP67_PCB_IMPACTS.md`.

---

## 1. Честный вердикт

| | |
|--|--|
| Цель | IP67 |
| CAD | Параметризова контур уплотнений |
| Сертификация | **Нет** — нужен lab test (пыль + immersion) |
| Rev0 FDM | Геометрия готова к печати; материал прокладки/адгезива — BOM |

Открытые сквозные pogo **убраны**. Электрика cradle → мембрана/пилюли → слепые колодцы pads → внутренний flex.

---

## 2. Контур уплотнения (снаружи → внутрь)

```
[ стекло ] ─── клеевой/gasket land вокруг aperture
[ безель top ]
     │  винты M1.4 + опц. O-ring под головкой
[ SPLIT_Z ] ─── кольцевая канавка Ø1.0 silicone cord (R=20.7)
[ bottom ]
[ зад ] ─── elastomer sheet над слепыми pogo wells
[ бок ] ─── button boots (эластомер) на SW1–3
[ 3/9 ] ─── FPC: герметичный гrommet + potting (сборка, не пластик)
```

**SW_DBG:** внешнего отверстия в корпусе **нет** (политика PCB) — доступ только после разборки.

---

## 3. Плоскость разъёма (split gasket)

| Параметр | Значение |
|----------|----------|
| Канавка | кольцо в `case_bottom` на `SPLIT_Z` |
| `SEAL_GROOVE_R` | **20.70 mm** (на тонкой полке стены: ~19.95…21.5) |
| `SEAL_GROOVE_W` × `D` | **0.95 × 0.65 mm** |
| Шнур | silicone cord **Ø1.0** (`SEAL_CORD_D`) |
| Сжатие | ~25–35% при затяжке винтов |

Top имеет ответную плоскую посадку. Канавка непрерывная (полный круг).

### Винты и линия gasket

- `SCREW_R=17.5` **внутри** периферийного gasket (ограничение Ø43).
- Для IP: **глухие** термо-вставки в бобышках (пилот **не** пробивает заднюю стенку); снаружи снизу сквозного cbore **нет**.
- Винты сверху + **O-ring / bonded washer** под головкой (или анаэробный герметик резьбы).
- Истинный «clamp снаружи gasket» потребовал бы больший OD / фланец — зафиксировано как лимит форм-фактора.

---

## 4. Pogo — sealed wells (не open through-holes)

**Режим по умолчанию:** `POGO_SEAL_MODE=elastomer`.

| Элемент | Геометрия |
|---------|-----------|
| Матрица | 2×3 @ **3.0 mm**, origin (−4.0, −12.5) — без изменений |
| Окно cradle | recess ≤ `BOTTOM_WALL−0.55` |
| Карман мембраны | `POGO_SEAL_POCKET_D≈0.55` + margin |
| Pad wells | Ø2.8 blind, пол ≥ **0.55 mm** |
| Сквозные Ø2.0 | **удалены** |

**Электрический путь:**  
cradle pogo → conductive elastomer (пилюли/лист) → recessed pads (приклеены/залиты) → внутренний канал/flex → PCB B.Cu.

**Альтернатива** `POGO_SEAL_MODE=gland`: посадочное место под O-ring на каждый пин; наконечник тоже **blind** до пола (сборка уплотняет пин в корпусе).

Ключ-паз −X сохранён (анти-180°).

---

## 5. Кнопки — elastomer boots

- Тоннели SW1–3 на `BTN_Z=SPLIT_Z=6.0` через **обе** половины (P0).
- На OD: land `BTN_BOOT_LAND_D=4.0` под фланец boot + посадочная выемка.
- BOM: силиконовый/TPE boot (overmold или отдельная деталь) + печатный `button_cap` внутри или как жёсткий толкатель за мембраной.
- Ход 0.3–0.5 mm до купола B3U-class.

Без boot тоннель — дыра в IP-контуре.

---

## 6. Стекло — bond / gasket land

- Карман `GLASS_POCKET≈30□`, aperture `28□`.
- Кольцо между ними + мелкая канавка (`GLASS_BOND_LAND_W=1.5`) под **PSA / liquid adhesive / PORON**.
- `GLASS_GASKET_T=0.5` — ном. толщина прокладки под стеклом.
- ASSUMED размер стекла (GDEY0154D67 class) — до обмера OEM риск переделки безеля.

---

## 7. FPC 3/9 часов

Каналы `10 × 0.5 mm` пробивают стенку — **обязательно** на сборке:

1. Силиконовый grommet / overmold на flex, **или**
2. Potting (силикон/уретан) в канале после укладки, **или**
3. Отдельный герметичный connector (дороже).

В CAD канал остаётся; IP держится процессом сборки (см. BOM вне пластика).

---

## 8. BOM уплотнений (не пластик)

| Поз. | Деталь | Примечание |
|------|--------|------------|
| 1 | Silicone cord Ø1.0 | split groove |
| 2 | Elastomer sheet + conductive pills | pogo window |
| 3 | ×3 button boots | OD land |
| 4 | Glass PSA / PORON | bond land |
| 5 | ×4 O-ring под головку M1.4 | опционально |
| 6 | FPC grommet / potting | 3 и 9 ч |
| 7 | Heat-set M1.4 inserts | глухие бобышки |

---

## 9. План валидации (до заявления IP67)

1. Печать PETG/ABS, сборка с полным BOM уплотнений.  
2. Smoke / bubble check на split + pogo + buttons.  
3. Immersion 1 m / 30 min (или аккредитованная лаборатория).  
4. Dust chamber (IP6X) — отдельно.  
5. Только после PASS: обновлять `IP_CERTIFIED=True` и маркетинг.

---

## 10. Параметры SoT (excerpt)

```
IP_TARGET=IP67
IP_CERTIFIED=False
POGO_SEAL_MODE=elastomer
SEAL_GROOVE_R=20.7  SEAL_GROOVE_W=0.95  SEAL_GROOVE_D=0.65  SEAL_CORD_D=1.0
BTN_Z=6.0  SPLIT_Z=6.0  BATTERY_CAVITY_H=3.6
CASE_OD=43  PCB_POCKET=40.3  POGO 2×3 @ 3.0  LUG=20
```

---

## 11. Failure modes

| ID | Режим | Следствие | Митигация |
|----|-------|-----------|-----------|
| F1 | Сквозные pogo / нет elastomer+insert | Вода в полость | Blind wells + seal sheet (CAD) |
| F2 | Недожим / пережат cord | Течь по split / трещина | Канавка 0.95×0.65 под Ø1.0; момент M1.4 |
| F3 | Стык cord не склеен | Точечная течь | Closed-loop + клей стыка (~130 mm) |
| F4 | FPC 3/9 без grommet/potting | Bypass периметра | Silicone plug на сборке |
| F5 | Void в glass bond | Течь с лица | Controlled land 1.5 + инспекция |
| F6 | Boot порван / смещён | Вода к SW | Land Ø4 + запасной boot |
| F7 | FDM пористость | Медленная инфильтрация | Пропитка / литьё для cert units |
| F8 | Cradle перекашивает sheet | Зазор у pills | Key −X + штифты; align ±0.2 |
| F9 | Via в seal land на PCB | Капилляр под маской | `IP67_PCB_IMPACTS.md` P1–P4 |
| F10 | Маркетинг «IP67» без lab | Юр./репутационный риск | `IP_CERTIFIED=False` до PASS |

---

## 12. PCB

Правила разводки / keepout: `/workspace/e-ink-watch-kicad/reports/IP67_PCB_IMPACTS.md`.

Экспорт параметров: `exports/SEAL_PARAMS.txt`, `exports/POGO_MATRIX.txt`.
