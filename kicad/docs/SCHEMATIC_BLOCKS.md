> **KiCad project note (2026-09-18):** для схемы в этой папке **NFC снят** (BLE-only pairing). См. корневые `../README.md` и `../DESIGN_NOTES.md`.

# Schematic Blocks — Pin / Interface Sketch

Sketch for **nRF52840 + NT3H2211 + 3× SPI E Ink + BQ25120A/BQ25155**. Pin numbers are a **starting assignment** — remap against your package (QIAA vs CKAA) and Nordic DK conflict table. Always reserve NFC1/NFC2 if using SoC NFCT; below we prioritize discrete NTAG and free those pins for GPIO if NFCT unused.

## 1. Power nets

| Net | Source | Consumers |
|-----|--------|-----------|
| `VBUS` | USB-C or wireless rectifier | PMIC VIN |
| `VBAT` | LiPo + PCM | PMIC BAT, optional gauge |
| `SYS` | PMIC PMID/SYS | Always-on 3V3 LDO input / MCU VDDH |
| `3V3_ALWAYS` | PMIC LDO or buck | MCU, NTAG VCC, RTC, pull-ups |
| `3V3_DISP` | Load switch from SYS | Main + strap E Ink VCI only when refreshing |
| `GND` | Star near PMIC | All |

Ship mode: PMIC `#SHIPMODE` / register via I2C from MCU (careful not to brick without button wake).

## 2. MCU — nRF52840 (logical map)

### SPI0 — shared E Ink bus

| Signal | Suggested nRF pin | Notes |
|--------|-------------------|-------|
| `EPD_SCK` | P0.03 | SPI SCK |
| `EPD_MOSI` | P0.04 | SPI MOSI (EPD usually MOSI-only) |
| `EPD_MISO` | NC or P0.05 | Unused on many panels |
| `EPD_CS_MAIN` | P0.06 | Main panel CS |
| `EPD_CS_L` | P0.07 | Left strap CS |
| `EPD_CS_R` | P0.08 | Right strap CS |
| `EPD_DC` | P0.26 | Data/command (shared) |
| `EPD_RST` | P0.27 | Shared reset |
| `EPD_BUSY_MAIN` | P0.28 | Input |
| `EPD_BUSY_L` | P0.29 | Input |
| `EPD_BUSY_R` | P0.30 | Input |
| `DISP_EN` | P0.31 | Gate `3V3_DISP` load switch |

### I2C0 — NFC tag (+ optional RTC / gauge / haptic)

| Signal | Suggested pin | Notes |
|--------|---------------|-------|
| `SDA` | P0.26 conflict → use **P0.11** | 4k7 pull-up to 3V3_ALWAYS |
| `SCL` | **P0.12** | Same |
| `NFC_FD` | P0.13 | NTAG field-detect → wake / interrupt |
| `RTC_INT` | P0.14 | Optional RV-3028 INT |
| `PMIC_INT` | P0.15 | Charger interrupt |

Adjust if `P0.26` already used for `EPD_DC` — table above already separates DC vs I2C.

### Buttons / crown / haptic

| Signal | Pin | Notes |
|--------|-----|-------|
| `BTN1` | P0.11 → if free, else P1.01 | Active low, wake |
| `BTN2` | P1.02 | |
| `BTN3` / encoder A | P1.03 | |
| Encoder B | P1.04 | |
| `HAPT_EN` / I2C DRV2605 | I2C0 addr 0x5A | Optional |

### Debug / misc

| Signal | Pin |
|--------|-----|
| SWDCLK / SWDIO | Dedicated |
| RESET | Dedicated |
| QSPI CS/SCK/DIO0–3 | P0.17–P0.23 region per Nordic QSPI examples | Optional NOR |

### If using SoC NFCT instead of / in addition to NTAG

| Signal | Pin | Constraint |
|--------|-----|------------|
| NFC1 | **P0.09** | Dedicated antenna; cannot use as GPIO when NFCT enabled |
| NFC2 | **P0.10** | Same |

## 3. NTAG I²C Plus (NT3H2211)

| Pin | Connect |
|-----|---------|
| VCC | `3V3_ALWAYS` |
| GND | GND |
| SDA / SCL | I2C0 |
| FD | MCU `NFC_FD` (configure pull per datasheet) |
| LA / LB | Antenna + tuning C + TVS to GND |
| Pad | Follow NXP HVQFN footprint |

I2C 7-bit address: typically **0x55** (confirm; depends on packaging/addr pin — check DS).

Modes used in FW:

1. EEPROM NDEF for BLE OOB record.
2. Pass-through SRAM 64 B for rare NFC-only chunks.
3. FD edge → GPIOTE wake from System OFF.

## 4. E Ink panels (logical FPC)

Typical 4-wire SPI panel signals (names vary by vendor):

| Panel pin | Net |
|-----------|-----|
| VCC / VCI | `3V3_DISP` |
| GND | GND |
| SDA / DIN | `EPD_MOSI` |
| SCL / SCLK | `EPD_SCK` |
| CS | per-panel CS |
| D/C | `EPD_DC` |
| RES | `EPD_RST` |
| BUSY | per-panel BUSY |

**Do not invent voltages:** some panels need additional VGH/VGL generated onboard — raw Good Display panels usually include integrated power; verify chosen SKU schematic. Never share `3V3_DISP` with MCU if panel injects noise — bead + bulk cap at each FPC.

## 5. PMIC (BQ25120A / BQ25155) sketch

| PMIC pin | Connect |
|----------|---------|
| IN | `VBUS` |
| BAT | `VBAT` |
| PMID / SYS | `SYS` |
| LSCTRL / LDO | `3V3_ALWAYS` (set 3.0–3.3 V) |
| SDA/SCL | I2C0 (addr per DS, often 0x6A class — **verify**) |
| TS | Battery NTC |
| /CD, /MR, INT | Buttons / MCU as TI ref |

Charge current register: start **50–100 mA** until thermal OK.

## 6. ASCII system diagram

```
                 ┌──────── phone ────────┐
                 │  NFC App  +  BLE App  │
                 └───────┬───────┬───────┘
                    13.56│       │2.4 GHz
                         │       │
              ┌──────────▼──┐    │
              │ NFC coil    │    │
              │ + TVS       │    │
              └──────┬──────┘    │
                     │ LA/LB     │
              ┌──────▼──────┐    │
              │ NT3H2211    │    │
              │ EEPROM/SRAM │    │
              └──────┬──────┘    │
                 I2C │ FD        │
         ┌───────────▼───────────▼───────────┐
         │            nRF52840               │
         │  BLE · SPI · I2C · RTC · GPIO     │
         └─┬─────┬──────┬──────┬──────┬──────┘
           │     │      │      │      │
        SWD│  BTN│   QSPI│   SPI0  DISP_EN
           │     │      │      │      │
           │     │   flash│     │   load-sw
           │     │      │      │      ▼
           │     │      │      │   3V3_DISP
           │     │      │      ├──────────────┐
           │     │      │      ▼              ▼
           │     │      │  ┌────────┐   ┌─────────┐
           │     │      │  │Main EPD│   │Strap L/R│
           │     │      │  │1.54″   │   │flex EPD │
           │     │      │  └────────┘   └─────────┘
           │     │      │
    ┌──────▼─────▼──────▼──┐
    │ BQ251xx  ←── VBUS    │
    │     ↓                │
    │   LiPo+PCM           │
    └──────────────────────┘
```

## 7. Firmware interface checklist

- [ ] Init PMIC: charge limit, SYS voltage, ship exit on button
- [ ] Gate `DISP_EN` only around refresh; wait BUSY
- [ ] Partial update minute hand/digits; full update anti-ghost schedule
- [ ] FD IRQ → read NDEF → start BLE advertising / connect
- [ ] GATT: theme header + zlib/RLE tiles → flash → render
- [ ] BLE disconnect → System OFF; RTC wake 60 s
- [ ] NFC-only fallback: reject payloads &gt; EEPROM size; show “use BLE” icon on main EPD

## 8. Uncertainty flags (do not treat as datasheet)

- Exact I2C addresses and NTAG pad names: confirm NT3H2211 DS.
- Exact EPD FPC pin order: confirm GDEY0154D67 / Waveshare raw panel pinout PDF for the purchased lot.
- BQ25120A vs BQ25155 pinout differs — pick one and use that TI schematic, not a blend.
