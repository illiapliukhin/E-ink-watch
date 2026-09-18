> **KiCad project note (2026-09-18):** для схемы в этой папке **NFC снят** (BLE-only pairing). См. корневые `../README.md` и `../DESIGN_NOTES.md`.

# PCB Guidelines — E Ink Watch

## 1. Recommended stackups

### Main board (rigid, inside case)

**4-layer** preferred for BLE + NFC coexistence:

| Layer | Use |
|-------|-----|
| L1 | Signals + BLE antenna clearance / NFC coil (or coil on L1/L2) |
| L2 | Solid GND |
| L3 | Power pours (VBAT, SYS, 3V3) |
| L4 | Signals + GND pour |

**2-layer** acceptable for early prototype modules, but expect worse RF and harder NFC tuning.

Thickness: 0.6–0.8 mm FR-4 for thin watches; 1.0 mm easier mechanically. ENIG finish for FPC pads and battery contacts.

### Strap display interconnect

- **Polyimide flex FPC**, 1- or 2-layer, 0.12–0.2 mm.
- Coverlay; stiffener (FR-4 or PI) only under ZIF insertion zone.
- Bend region: copper teardrops, no vias in bend, trace axis perpendicular to bend fold where possible.
- Min bend radius: follow panel maker — flexible EPD demos often cite **~30–33 mm**; do not bend the driver COG / stiff FPC neck of the panel.

## 2. Board partitioning

```
┌─────────────────────────────────────────┐
│  CASE OUTLINE (TBD: Ø40–44 mm typical)  │
│  ┌──────────┐  ┌────────────────────┐   │
│  │ Main EPD │  │  BLE chip antenna  │   │
│  │  FPC     │  │  keepout           │   │
│  └──────────┘  └────────────────────┘   │
│  ┌─────────────────────────────────┐    │
│  │ nRF52840 + PMIC + flash         │    │
│  └─────────────────────────────────┘    │
│  ┌──────────────┐  ┌───────────────┐    │
│  │ LiPo pouch   │  │ NFC coil zone │    │
│  │ + PCM        │  │ (polymer back)│    │
│  └──────────────┘  └───────────────┘    │
│  ZIF-L ◄FPC strap          FPC strap► ZIF-R │
└─────────────────────────────────────────┘
```

**Do not** place NFC coil under battery metal tab sandwiches without ferrite; prefer coil on back polymer window.

## 3. NFC antenna keepout

- Frequency **13.56 MHz**; follow NXP AN11276 / ST AN2972 for dual-interface tags.
- Keep **≥5 mm** free of continuous copper pours inside coil; hatch GND if needed for return with care.
- No large metal (steel case back, battery can overlapping 100%) over coil — use plastic/glass/ceramic back or ferrite sheet between battery and coil (ferrite changes tuning — re-measure).
- Place TVS + series damping near chip LA/LB; short symmetric traces to coil.
- Tuning: design slightly high resonant freq; add parallel C after assembly measurement with case + battery present.
- ESD: user wrist + phone tap — assume IEC contact discharge; clamp to GND with NFC-rated TVS.

**BLE antenna** (2.4 GHz): opposite side of board from NFC if possible; Nordic layout guidelines; no battery under BLE antenna.

## 4. Battery placement & safety

| Rule | Detail |
|------|--------|
| Protected cell | Buy LiPo **with PCM** or add DW01A + dual MOSFET protection on PCB |
| Soft pouch support | Foam / adhesive; no sharp PCB edges into pouch |
| Charge current | Limit for small cells (often 0.5C → 40–100 mA for 80–200 mAh) in PMIC registers |
| Thermistor | Route NTC from cell to PMIC TS pin if available |
| Ship mode | Use BQ251xx ship mode for shelf life |
| Isolation | Battery disconnect test point for factory |
| Swelling | Leave mechanical gap; never fully encapsulate without vent path in case design |

**USB-C:** if present, put ESD on CC/D+/D−/VBUS; isolate from sweat (gasket). Prefer **pogo or magnetic** hidden port for waterproofing.

**Wireless:** RX coil on back; align with charger; metal bezel loops can detune both NFC and wireless — simulate.

## 5. Display / flex constraints

- Main EPD FPC usually exits one side — reserve corridor to ZIF; 180° fold common under display.
- Strap FPCs exit at 3 o’clock / 9 o’clock lugs; strain relief clamp in case so yanking strap does not peel ZIF.
- SPI length to strap: keep **&lt;150–200 mm** if possible; series 22–100 Ω on SCK/MOSI; common GND return in flex; consider lower SCK (1–4 MHz) for long flex.
- Separate `CS`, `BUSY` per panel; shared `RST` OK with care at boot.
- Never route display HV boost inductors (if external) near NFC/BLE — most small EPDs integrate boost on panel TCON.

## 6. Watch case constraints (needs user numbers)

| Parameter | Why it matters | Typical starting guess |
|-----------|----------------|------------------------|
| Case OD / shape | PCB outline, antenna diameter | 40–44 mm round |
| Max thickness | Battery + PCB + EPD stack | 10–12 mm fashion; &lt;9 mm sport |
| Lug width / strap width | Flex width & EPD choice | 20 / 22 mm common |
| Back material | NFC + wireless | Polymer preferred |
| Water rating | Seal, button membranes | IP67 target → no open USB |

**Blockers until specified:** final PCB diameter, battery SKU, NFC coil OD, flex length.

## 7. EMC / wearables hygiene

- Enable nRF internal DC/DC; place inductors per ref design.
- Ferrite bead on VBUS.
- Keep haptic motor return local if used.
- Sweat: conformal coat selective (not over RF antenna / NFC coil / battery contacts).

## 8. Test points & factory

- SWDIO / SWDCLK / RESET / GND pads.
- VBAT, SYS, 3V3.
- NFC: leave U.FL or temporary wire pads for VNA during bring-up (depopulate later).
- Current sense footprint in VBAT for sleep validation.
