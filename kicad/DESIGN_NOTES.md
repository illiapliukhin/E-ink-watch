# DESIGN_NOTES — открытые вопросы и решения (RU)

## Принято в этой ревизии схемы

### 1. NFC убран полностью

- Нет NTAG (NT3H2211), нет катушки 13.56 МГц, нет листа `nfc.kicad_sch`.
- Телефон ↔ часы: **только BLE** (GATT bulk для тем/картинок).
- Встроенный NFCT nRF52840 **не используется** (пины NFC1/NFC2 можно оставить как GPIO при разводке).

### 2. Pairing UX (BLE)

1. Пользователь **удерживает BTN1 ~3 с**.
2. Прошивка включает **BLE advertising** на окно **~60 с**.
3. Приложение на телефоне подключается, пишет тему/конфиг по GATT.
4. По таймауту / disconnect → advertising off → System OFF / idle sleep.

Кнопки BTN2/BTN3 — UI (меню, refresh и т.п.); точная матрица — firmware TBD.

### 3. Почему раньше был NFC+BLE split (и почему отказались)

Исходный package (`docs/`) рекомендовал NTAG для OOB pairing + мелких chunk, BLE для bulk.  
Решение пользователя: упростить BOM/антенну/keepout — **BLE-only**. Минус: нет пассивного тапа при севшей батарее и нет NFC wake; плюс: меньше RF-коллизий, проще корпус.

---

## Открытые вопросы (механика / электрика)

| # | Вопрос | Блокирует |
|---|--------|-----------|
| 1 | Диаметр/форма корпуса (Ø40–44?), толщина | outline PCB, батарея |
| 2 | Ширина ремешка, радиус изгиба ≥30–33 мм | выбор strap EPD vs custom |
| 3 | Main face: квадрат 1.54″ vs round (COTS mono round почти нет) | FPC MAIN |
| 4 | Зарядка: USB-C / pogo / wireless / только сменная батарея | J6 / катушка Qi |
| 5 | Модуль nRF (MDBT50Q / XIAO) vs bare QIAA/WLCSP | footprint U2, антенна 2.4 ГГц |
| 6 | Точный pinout FPC купленных панелей (GDEY0154D67 / 2.13 Flexible) | J2–J4 нумерация |
| 7 | BQ25120A vs BQ25155 — финальный выбор (не смешивать pinout) | U1 |
| 8 | Нужен ли внешний RTC RV-3028 / QSPI NOR / haptic | опциональные блоки |

---

## Strap flex connectors

Рекомендация архитектуры: **жёсткая PCB в корпусе + 2× FPC к strap**.

- На схеме: `J3` = STRAP_L, `J4` = STRAP_R (ZIF 0.5 мм class, footprint TBD).
- Общая SPI + отдельные CS/BUSY; strain relief в корпусе у ушек 3/9 часов.
- Длина SPI flex желательно &lt;150–200 мм; series 22–100 Ω на SCK/MOSI; SCK 1–4 МГц на длинном flex.
- Не гнуть COG/жёсткую шейку панели; bend radius по datasheet flexible EPD.

---

## Питание (кратко)

```
VBUS (опц.) ──► BQ25120A ──► VBAT (LiPo+PCM)
                     ├── VSYS
                     ├── 3V3 (LDO, always-on: MCU, pull-ups)
                     └── 3V3_DISP (P-FET / TPS229xx, DISP_EN)
```

E Ink питается только на время refresh; между обновлениями `3V3_DISP` off.

---

## Placeholder-символы

| Библиотека | Символ | Примечание |
|------------|--------|------------|
| `EInkWatch` | `nRF52840` | Логический map, не полный package |
| `EInkWatch` | `BQ25120A` | Упрощённый pinout; сверить TI DS |
| — | NT3H2211 | **не включён** (NFC удалён) |

Пассивы/коннекторы/кнопки — встроенные упрощённые Device/Connector/Switch в `lib_symbols` листов (работают без глобальных KiCad libs, но лучше заменить на стандартные при доработке).

---

## Следующие шаги

1. Зафиксировать механику корпуса и выбрать модуль vs bare die.
2. Скачать актуальные footprint BQ25120A + nRF (или модуль) и ZIF.
3. ERC в KiCad, затем PCB outline 4-layer.
4. Firmware: long-press → advertising 60 s; GATT theme transfer; partial refresh минут.
