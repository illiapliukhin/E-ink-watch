#!/usr/bin/env python3
"""Hand / duty-cycle battery life estimate for BLE-only E Ink watch.
Uses Nordic nRF52840 Product Spec order-of-magnitude currents + E Ink refresh estimate.
Not a substitute for measured power; no full RF SPICE.
"""
from __future__ import annotations

# Battery
CAP_mAh = 120.0          # typical small LiPo for Ø40–44 watch (assumption)
USABLE = 0.85            # avoid deep discharge / aging
VNOM = 3.7

# Nordic PS-ish (nRF52840, 3V, typical) — approximate
I_SYSTEM_OFF_uA = 1.5    # System OFF, wake on GPIO/RTC
I_SYSTEM_ON_IDLE_uA = 1.5  # with RTC (actually ~1.5–3 depending config); use 3.0 conservative
I_SYSTEM_ON_IDLE_uA = 3.0
I_CPU_RUN_mA = 3.0       # CPU active rough
I_RADIO_RX_mA = 6.0      # RX
I_RADIO_TX_0DBM_mA = 5.0 # TX 0 dBm order
I_PMIC_IQ_uA = 8.0       # BQ25120A quiescent ballpark when battery-powered

# Duty assumptions (user can edit)
REFRESH_PERIOD_s = 60.0      # partial/minute clock update
REFRESH_DURATION_s = 1.0
I_EINK_REFRESH_mA = 10.0     # panel+boost during refresh (estimate)
I_MCU_DURING_REFRESH_mA = 4.0

# BLE: rare pairing window + occasional notify
PAIR_PER_DAY = 1.0
PAIR_ADV_s = 60.0
I_ADV_mA = 2.0               # advertising average (depends interval)
BLE_CONN_PER_DAY = 2.0       # theme sync / notify
BLE_CONN_s = 30.0
I_CONN_mA = 4.0

# RTC wake for clock: already in System ON idle with RTC

def avg_uA() -> dict:
    sec_day = 86400.0
    # Base sleep: System ON idle + PMIC
    base = I_SYSTEM_ON_IDLE_uA + I_PMIC_IQ_uA

    # E Ink refreshes
    n_ref = sec_day / REFRESH_PERIOD_s
    t_ref = n_ref * REFRESH_DURATION_s
    e_ref_uAh = n_ref * REFRESH_DURATION_s / 3600.0 * (I_EINK_REFRESH_mA + I_MCU_DURING_REFRESH_mA) * 1000.0
    # convert: mA * hours * 1000 = uAh ... wait: mA * h = mAh; *1000 = uAh
    e_ref_uAh = (t_ref / 3600.0) * (I_EINK_REFRESH_mA + I_MCU_DURING_REFRESH_mA) * 1000.0

    # BLE pairing adv
    e_pair_uAh = PAIR_PER_DAY * (PAIR_ADV_s / 3600.0) * I_ADV_mA * 1000.0
    e_conn_uAh = BLE_CONN_PER_DAY * (BLE_CONN_s / 3600.0) * I_CONN_mA * 1000.0

    # Base continuous
    e_base_uAh = base * 24.0  # uA * h = uAh

    # While refreshing / BLE, base still roughly applies (conservative double-count small)
    total_uAh = e_base_uAh + e_ref_uAh + e_pair_uAh + e_conn_uAh
    i_avg_uA = total_uAh / 24.0

    usable_mAh = CAP_mAh * USABLE
    days = (usable_mAh * 1000.0) / total_uAh if total_uAh > 0 else float('inf')

    return {
        "I_base_uA": base,
        "E_base_uAh_day": e_base_uAh,
        "E_eink_uAh_day": e_ref_uAh,
        "E_ble_pair_uAh_day": e_pair_uAh,
        "E_ble_conn_uAh_day": e_conn_uAh,
        "E_total_uAh_day": total_uAh,
        "I_avg_uA": i_avg_uA,
        "battery_mAh": CAP_mAh,
        "usable_mAh": usable_mAh,
        "life_days": days,
        "n_refresh_per_day": n_ref,
    }

def main():
    r = avg_uA()
    lines = [
        "E Ink Watch — battery life hand calculation",
        "==========================================",
        f"Battery: {r['battery_mAh']:.0f} mAh LiPo, usable {USABLE*100:.0f}% => {r['usable_mAh']:.1f} mAh",
        f"Base (System ON idle {I_SYSTEM_ON_IDLE_uA} uA + PMIC Iq {I_PMIC_IQ_uA} uA) = {r['I_base_uA']:.1f} uA",
        f"E Ink: {I_EINK_REFRESH_mA} mA + MCU {I_MCU_DURING_REFRESH_mA} mA for {REFRESH_DURATION_s}s every {REFRESH_PERIOD_s}s",
        f"  => {r['n_refresh_per_day']:.0f} refreshes/day, energy {r['E_eink_uAh_day']:.1f} uAh/day",
        f"BLE pair: {PAIR_PER_DAY}/day × {PAIR_ADV_s}s @ {I_ADV_mA} mA => {r['E_ble_pair_uAh_day']:.1f} uAh/day",
        f"BLE conn: {BLE_CONN_PER_DAY}/day × {BLE_CONN_s}s @ {I_CONN_mA} mA => {r['E_ble_conn_uAh_day']:.1f} uAh/day",
        f"Base energy: {r['E_base_uAh_day']:.1f} uAh/day",
        f"TOTAL: {r['E_total_uAh_day']:.1f} uAh/day  (Iavg ≈ {r['I_avg_uA']:.1f} uA)",
        f"Estimated life: {r['life_days']:.1f} days (~{r['life_days']/30:.1f} months)",
        "",
        "Sources / caveats:",
        "- nRF52840 currents: Nordic Product Specification order-of-magnitude (3 V).",
        "- E Ink 10 mA @ 1 s: concept estimate; measure real panel + onboard boost.",
        "- No NFC (design decision). Full SPICE of SoC/RF not available.",
        "- Dominated by refresh rate: slower updates extend life almost linearly for E Ink term.",
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    open("battery_life_out.txt", "w").write(text)

if __name__ == "__main__":
    main()
