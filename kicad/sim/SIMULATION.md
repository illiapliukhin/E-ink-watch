# Simulation notes — E Ink Watch (BLE-only)

## What was NOT simulated
- Full digital / RF SPICE of **nRF52840** — no public transistor-level model suitable for this; **not faked**.
- Accurate BQ25120A behavioral model (TI may provide SIMPLIS/PSPICE under NDA; not used here).
- BLE antenna / 2.4 GHz matching.

## What was run

### 1. ngspice power-path (`power_path.cir`)
Ideal chain: **LiPo 3.8 V → ESR → VSYS (47 µF) → ideal DISP_EN switch → E Ink load (~10 mA)**.

| Artifact | Path |
|----------|------|
| Netlist | `sim/power_path.cir` |
| Log | `sim/power_path.log` |
| Trace (downsampled) | `sim/power_path_trace.csv` |
| Interpretation | `sim/INTERPRETATION.txt` |

Key results: idle ~15 µA; refresh ~10–13 mA; VSYS sag ~50 mV; capacitive inrush peak at switch close (ideal SW — real PMIC soft-start lower).

### 2. Battery-life Python (`battery_life.py`)
Duty-cycle average using Nordic PS order-of-magnitude + E Ink estimate. Output: `battery_life_out.txt`.

### 3. Static net continuity (pre-sim)
Hierarchical sheet pin names match child hierarchical labels; Power / MCU / Displays / UI nets span expected sheets (see verification report).

## How to re-run
```bash
sudo apt-get install -y ngspice   # if needed
cd sim && ngspice -b power_path.cir | tee power_path.log
python3 battery_life.py
```
