# FIX_P0 — кнопки, батарея, IP67 sealing

**Дата:** 2026-09-18 12:36 IDT  
**Объект:** `/workspace/e-ink-watch-case/`  
**Генератор:** `src/watch_case.py`

## Что было сломано (из INTEGRITY_REVIEW)

1. **Кнопки:** `BTN_Z≈5.0` vs top `SPLIT_Z=5.6`; в bottom relief был `pass` → тоннели нерабочие.  
2. **Батарея:** tray `BAT_Z+BAT_FOAM=3.4` > `BATTERY_CAVITY_H=3.2` → overflow под полку PCB.  
3. **IP:** открытые сквозные pogo рвали контур (цель теперь **IP67**).

## Параметры: было → стало

| Параметр | Было | Стало | Зачем |
|----------|------|-------|-------|
| `BATTERY_CAVITY_H` | 3.2 | **3.6** (+0.4) | tray 3.4 + зазор 0.2; ASSUMED LiPo ~3.0 + foam 0.4 |
| `Z_PCB_BOTTOM` | 4.6 | **5.0** | следует из cavity |
| `Z_PCB_TOP` | 5.4 | **5.8** | |
| `SPLIT_Z` | 5.6 | **6.0** | |
| `BTN_Z` | `Z_PCB_TOP−0.4`≈5.0 | **`SPLIT_Z`=6.0** | тоннель через обе половины |
| Bottom button cut | `pass` | `_radial_button_tunnels` | рабочие актуаторы |
| `FPC_H` | 0.4 | **0.5** | лёгкий запас ZIF+flex |
| Pogo holes | сквозные Ø2.0 | **blind wells** + elastomer pocket | IP67 intent |
| Split gasket | нет | канавка R20.7 / 0.95×0.65, cord Ø1.0 | mid-seal |
| Button boots | нет | land Ø4 на OD (top+bottom) | мембрана |
| Glass bond | только pocket | + trench land | клей/PORON |
| Boss / rear | through cbore | **blind** pilot | нет дырки в back |

## Не трогали (locked)

- Ø**43** OD, PCB pocket Ø**40.3**, pogo **2×3 @ 3.0**, origin (−4,−12.5)
- Ушки **20 mm**, **нет** внешнего отверстия под SW_DBG
- `OVERALL_H=11.0`

## Новые Z (снизу вверх)

```
Z=11.0  верх безеля
Z≈6.0–11  top (стекло, aperture, bond land)
Z=6.0   SPLIT + BTN_Z + gasket groove
Z=5.8   верх PCB
Z=5.0   низ PCB / полка
Z=1.4   пол полости (батарея 3.6 mm высотой полости)
Z=0     back + sealed pogo wells (пол ≥0.55)
```

## Регенерация

```bash
cd /workspace/e-ink-watch-case && python3 src/watch_case.py
# или ./regenerate.sh
```

Экспорт: `exports/*.stl|step`, превью: `renders/`, архив: `/workspace/e-ink-watch-case-p0.tar.gz`.

Подробности IP: `reports/IP67_SEALING.md`.
