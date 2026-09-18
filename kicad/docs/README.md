> **KiCad project note (2026-09-18):** для схемы в этой папке **NFC снят** (BLE-only pairing). См. корневые `../README.md` и `../DESIGN_NOTES.md`.

# E Ink Watch PCB — концепт инженерного пакета

Концепт носимых часов с **монохромным E Ink** на циферблате и **двумя узкими монохромными экранами в ремешке**, NFC для обмена с телефоном и полноценным блоком питания/заряда.

Документы в этой папке — стартовый engineering package для прототипа (не готовый gerber/PCB layout).

## Состав документов

| Файл | Содержание |
|------|------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Блок-схема, дерево питания, топология дисплеев, путь данных NFC |
| [BOM.md](BOM.md) | Рекомендуемые партномера, роли, альтернативы |
| [PCB_GUIDELINES.md](PCB_GUIDELINES.md) | Стекап, flex для ремешка, NFC-антенна, батарея, корпус |
| [SCHEMATIC_BLOCKS.md](SCHEMATIC_BLOCKS.md) | Эскиз назначения пинов/шин (SPI, I2C, питание) |

## Рекомендуемая архитектура (кратко)

```
Телефон ──NFC tap──► NTAG I²C Plus (метаданные / pairing) ──I2C──► nRF52840
                └──BLE bulk──► nRF52840 ──SPI──► 3× E Ink (main + 2 strap)
                                      └──PMIC──► LiPo thin pouch
```

| Блок | Выбор | Почему |
|------|--------|--------|
| MCU | **Nordic nRF52840** (QFN / WLCSP) | Лучший sleep (~1.5 µA), BLE 5.x, встроенный NFC-A tag, зрелый wearable-стек (Zephyr / SoftDevice) |
| NFC bulk | **NT3H2211** (NTAG I²C Plus 2K) + BLE | NFC-only слишком мал/медленен для тем; NFC = pairing + мелкие chunks, BLE = картинки |
| Main display | **GDEY0154D67** / Waveshare 1.54″ 200×200 B/W | Проверенный SPI mono E Ink ~1.5″; round mono COTS редки |
| Strap ×2 | **Waveshare 2.13″ Flexible** 212×104 | Гибкий EPD, есть academic proof (Watch+Strap); узкий strap — custom housing / Ynvisible ECD |
| Power | **BQ25120A** или **BQ25155** + thin LiPo 80–200 mAh | Wearable PMIC с charge + LDO/buck; защита LiPo обязательна |
| RTC | Кварц 32.768 кГц на nRF + опц. **RV-3028-C7** | Внешний RTC — для недель deep sleep с точным временем |

## Ключевые решения

1. **Жёсткая PCB в корпусе + flex-хвосты к экранам ремешка** (не all-in-one): драйверы, MCU, батарея, NFC-катушка остаются в case; на strap — только панели + короткий FPC.
2. **NFC ≠ канал для полноценных тем.** Честно: Type 2 EEPROM ~1–2 KB user, pass-through по 64 B; полный bitmap 200×200 ≈ 5 KB уже неудобен. Рекомендация: NFC пишет BLE OOB / session token → bulk по BLE; NFC-only только иконки/метаданные/чанки.
3. **Ultra-low power:** E Ink держит картинку без питания; partial refresh для минут; full refresh редко; MCU System OFF / System ON idle; RTC wake раз в минуту (или по кнопке).
4. **Safety:** PCM/защита на LiPo, ESD на NFC-антенне (TVS), keepout металла у катушки.

## Что нужно от вас (механика)

Без этих размеров нельзя финализировать outline PCB и антенну:

1. Диаметр / форма корпуса (например 40 / 42 / 44 mm) и целевая толщина.
2. Ширина ремешка и допустимый радиус изгиба (типично ≥ 30–33 mm для flexible EPD).
3. Форма main display: **квадрат 1.54″** (доступно сейчас) vs **круг** (COTS mono круглый почти нет — custom / цветной 1.69″ Spectra 6 / Memory LCD).
4. Зарядка: **USB-C** (pogo / скрытый разъём) vs **беспроводная катушка** (Qi-like / proprietary) vs только replaceable батарея.
5. Нужен ли **BLE всегда** или «только NFC» (второе сильно ограничивает темы).

## Статус

Концепт / research package, сентябрь 2026. Партномера — реальные семейства с рынка 2025–2026; точные токи refresh и pinout FPC сверять по актуальным datasheet выбранного vendor lot.

## Update 2026-09-18 — no NFC

User decision: **NFC removed**. Pairing and image/theme transfer are **BLE-only** (nRF52840). Long-press button (~3 s) opens a BLE advertising window (~60 s), then radio sleeps. Bulk bitmaps never go over NFC.
