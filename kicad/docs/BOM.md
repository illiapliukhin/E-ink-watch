> **KiCad project note (2026-09-18):** для схемы в этой папке **NFC снят** (BLE-only pairing). См. корневые `../README.md` и `../DESIGN_NOTES.md`.

# BOM — E Ink Watch PCB (concept)

Quantities for **one prototype**. Prices approximate (distributor, 2025–2026, low qty) — verify before purchase. Prefer real families; where pin-compatible variants exist, alternatives are listed.

## 1. Core compute & RF

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 1 | **nRF52840-QIAA** (aQFN73) or **-CKAA** (WLCSP) | MCU: BLE 5.x, NFC-A tag peripheral, SPI/I2C | Primary pick for wearables. WLCSP thinner; QFN easier hand-proto. SoftDevice S140 / Zephyr. |
| — | Alt: **nRF5340** | Dual-core, more flash | Overkill for v1; higher cost |
| — | Alt: **STM32U5** + separate BLE (e.g. nRF / STM32WB sibling) | Strong LP MCU | Needs extra radio IC → denser PCB |
| — | Alt: **ESP32-C3** | Cheap BLE | Higher sleep current; no NFC; OK for tethered demo only |
| 1 | 32.768 kHz crystal (e.g. **ABS07** class, 6–9 pF load) | LFCLK / RTC | Match Nordic load caps |
| 1 | HF crystal 32 MHz (as Nordic ref) | HFCLK | Follow Nordic DK schematic values |
| 1 | Chip antenna or PCB trace for 2.4 GHz | BLE | Keepout; or use module **MDBT50Q** / **XIAO nRF52840** for first bring-up |

## 2. NFC

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 1 | **NT3H2211W0FHK** (NTAG I²C Plus **2K**) | Dual NFC Type 2 + I²C EEPROM, FD pin, 64 B SRAM pass-through | Preferred for phone writes + MCU link |
| — | Alt: **NT3H2111** (1K) | Same family, less EEPROM | OK if only pairing tokens |
| — | Alt: **ST25DV04K / 16K / 64K** | ISO15693 Type 5, mailbox FTM | Better mailbox size; Type 5 phone support varies vs Type 2 |
| — | Avoid for watch: **PN532** | Reader IC | Too large / power-hungry |
| 1 | PCB coil + tuning caps | 13.56 MHz antenna | Design per NXP AN11276; measure & tune on assembled watch |
| 2 | ESD TVS (e.g. **PESD1NFC** class / dual rail-clamp) | ESD on LA/LB | Place near antenna feed |

**Note:** nRF52840 has built-in NFCT (Type 2). Using **both** NFCT and NTAG needs either two coils (awkward) or one path. **Recommendation:** discrete NTAG for dual-interface + FD wake; use nRF NFCT only if you drop NTAG and accept SoftDevice NFC constraints.

## 3. Displays

### Main face

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 1 | **GDEY0154D67** (Good Display) or Waveshare **1.54″ e-Paper** (HINK-E0154A05 class) | Main mono E Ink 200×200 SPI | AA ~27.6×27.6 mm; SSD1680/1681 family — confirm exact IC on lot |
| — | Alt smaller: **GDEM0122T61** 1.22″ 176×192 | Tighter case | Same SPI class |
| — | Round color (if accepted): **GDEH0169E01** 1.69″ Spectra 6 400×400 | Round COTS | Not mono; slower/full refresh power higher |
| — | Reflective mono round-ish: Sharp **LS013B7DH03** Memory LCD 128×128 | Ultra-low continuous power | Not bistable E Ink; different look |

### Strap ×2

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 2 | Waveshare **2.13inch e-Paper D** flexible raw panel 212×104 | Strap graphics prototype | ~0.3 mm thick; bend display area only; **width may exceed narrow straps** |
| — | Alt production: **Ynvisible** custom ECD strips | Narrow arbitrary shape | Segmented / limited gray; I²C/driver kits available |
| — | Alt: custom flexible EPD MOQ | Full bitmap narrow | Quote E Ink / DKE / Good Display |

Shared: 24-pin / 8-pin FPC depending on raw vs module — **use raw panels + on-PCB level translation if needed**; modules with Pi headers are for bench only.

## 4. Power

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 1 | Thin LiPo pouch **80–200 mAh** (e.g. ~3.0×20×22 mm @80 mAh; ~4–5 mm thick @200 mAh families) | Energy store | Exact size TBD by case; **must include PCM** (DW01+FS8205 class or vendor protected cell) |
| 1 | **BQ25120A** | Wearable charger + buck/LDO + ship mode | Up to ~300 mA charge; TI wearable ref designs |
| — | Alt: **BQ25155** | 500 mA, ADC, 10 nA ship | Better crude fuel gauge via ADC |
| 1 | Optional **BQ27421-G1** | Fuel gauge | If accurate % needed with BQ25120A |
| 1 | Load switch (e.g. **TPS229xx** / P-FET) | Gate 3V3_DISP | Cut E Ink rail between refreshes |
| 1 | Optional USB-C receptacle + **TPD** ESD / CC resistors | Wired charge | Or omit for wireless-only |
| 1 | Optional wireless RX coil + IC (e.g. proprietary 5–10 W-class overkill — use **low-power wearable RX** like ST WLC / TI BQ510xx class carefully) | Wireless charge | Coil under back; metal case kills it — polymer back required |

## 5. RTC, UI, misc

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 0–1 | **RV-3028-C7** (Micro Crystal) | External RTC ~45 nA | Optional; nRF LFCLK enough if daily BLE time sync |
| — | Alt: **PCF8563** / **DS3231** | Common RTCs | DS3231 larger / higher Iq — less ideal |
| 2–3 | Tactile switches (side) | UI | Waterproof membrane preferred in case design |
| 0–1 | Rotary encoder / crown sensor | Analog crown | Mechanical complexity |
| 0–1 | **DRV2605L** + LRA | Haptic | Optional |
| 0–1 | **W25Q64 / W25Q128** QSPI NOR | Theme storage | If internal 1 MB flash insufficient |
| 1 | SWD header footprint / test pads | Debug | Pogo in production |
| — | Decoupling, ferrite BLE, series 100 Ω SPI as needed | Passives | Follow Nordic + E Ink vendor refs |

## 6. Connectors / flex

| Qty | Part / family | Role | Notes |
|-----|---------------|------|-------|
| 2–3 | 0.5 mm pitch ZIF FPC connectors (e.g. Hirose **FH12** / Molex equivalents) | Main + 2 strap FPCs | Locking; strain relief in case |
| 2 | Custom FPC tails (PI flex) | Case → strap | Length TBD; stiffener at ZIF |

## 7. What is intentionally NOT invented

- Exact refresh current mA·s for each panel lot — use vendor datasheet of the purchased SKU.
- Exact NFC coil turns / inductance — must be simulated/measured for the final back geometry.
- Battery mm — blocked on case thickness from user.

## 8. Bring-up shortcut (optional modules)

For software before custom PCB:

1. **Seeed XIAO nRF52840** or Nordic **nRF52840 DK**
2. Waveshare 1.54″ + 2× 2.13″-D flexible on breadboard SPI
3. NXP **OM5569** NTAG I²C Plus explorer / breakout

Then migrate pin map from [SCHEMATIC_BLOCKS.md](SCHEMATIC_BLOCKS.md).
