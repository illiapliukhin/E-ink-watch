# gpt-6-sol CD round + independent KEEP (2026-09-24)

Sol used workspace tools until HTTP 429 `free_limit_reached` (~01:57 UTC, quota reset 02:00 UTC). API key is not in the repo. Coordinates below that Sol probed during the cut-off round are **not** KEEP. Applied geometry is independent and DRC-gated.

## Sol probes before 429 (do not apply)

- CD via-in-pad on E2 `(110.60, 106.80)` / `(110.66, 106.80)` size 0.20 — DSBGA VIP. Independent: IPRETERM B RISK `+0.049`.
- CD B.Cu at `y=106.80` to `x=112.4` then south — Independent: vertical `x=112.4` OVERLAP `−0.120` vs 3V3 via `0.6@(112.16, 107.60)`.

Sol's chosen *family* from STEP1 was still correct: CD F.Cu → B.Cu → existing CD via `(113.30, 108.41)`, exit E2 only, never E1.

## Independent probe (overlap=0)

```text
add_via(net=CD, at=(110.6, 106.95), size=0.25, drill=0.15)
add_segment(net=CD, layer=F.Cu, start=(110.6, 106.8), end=(110.6, 106.95), width=0.15)
add_segment(net=CD, layer=B.Cu, start=(110.6, 106.95), end=(112.65, 106.95), width=0.12)
add_segment(net=CD, layer=B.Cu, start=(112.65, 106.95), end=(112.65, 108.41), width=0.12)
add_segment(net=CD, layer=B.Cu, start=(112.65, 108.41), end=(113.3, 108.41), width=0.12)
```

Tightest other-net edges: SDA F `+0.102`, IPRETERM B `+0.120`, 3V3_DISP B `+0.115`, 3V3 via `+0.130`. `x=112.70` is tighter vs 3V3_DISP (`+0.065`); keep `112.65`. Via `y=107.05` is a cleaner dogbone but SDA RISK.

## Applied KEEP `sol_cd_e2_via`

DRC: **`shorting_items=0`**, `unc=14→13`, power/pocket gates held.

## Applied KEEP `sol_ilim_c2_dogbone`

Orthogonal F.Cu C2 onto the existing ILIM via. Do not drop ILIM on `x=110.6` at `y=105.80` (VBAT RISK `+0.020`).

```text
add_segment(net=ILIM, layer=F.Cu, start=(110.6, 106.0), end=(110.75, 106.0), width=0.08)
add_segment(net=ILIM, layer=F.Cu, start=(110.75, 106.0), end=(110.75, 105.8), width=0.08)
```

Probe overlap=0 (VBAT `+0.070`, PMID `+0.080` on the via vertical). DRC: **`shorting_items=0`**, `unc=13→12`, power/pocket gates held. East 0402 column was not moved.

## Remaining U2 islands

TS C3 stub vs TS B via `(107.80, 105.65)`. SCL E5 vs `R_SCL` pad1 `(108.80, 110.31)` and U1. Through vias on the new CD B.Cu at `y=106.95` `x=110.60–112.65` short CD.
