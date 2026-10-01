# PASS_AY — power re-layout cannot open an I2C lane (2026-10-01)

**Board:** `e-ink-watch.kicad_pcb` unchanged (Pass-AT KEEP)
**From / to:** `shorting=0`, `unc=6`. No copper moved.
**R_SCL:** `(112.00, 107.45)` rot 270, still on E5 and the 3V3 rail.
**SW_DBG:** `(90.50, 105.50)`, default OFF. No VBUS on the dock.

## Verdict

**No KEEP.** SDA can reach U1 only by taking the VBAT bar off the board. That bar is the fat link from x=100.00 to x=106.20. The route that appears once the bar is gone sits on the bar, so putting the copper back — on either side, at the same 0.35 mm width — closes the lane. SCL never gets a 0.15 mm opening that keeps the `R_SCL` seat. Nothing was written, so there was no DRC to gate.

## What has to move before SDA connects

Pads stay in the obstacle set. A 0.15 mm F track joins SDA to U1 pad 27 only when all of the following are absent:

| Copper | Geometry |
|---|---|
| VBAT | F `(100.00, 105.40)–(106.20, 105.40)` w=0.35 |
| 3V3 rail | F `(110.16, 108.25)–(112.16, 108.25)` w=0.25 |
| 3V3 spur | F `(110.46, 108.10)–(110.16, 108.25)` w=0.25 |
| 3V3 | F `(110.50, 108.25)–(110.16, 108.25)` w=0.12 |
| 3V3 | F `(110.50, 109.59)–(110.50, 108.25)` w=0.12 |
| 3V3 via | `(110.40, 108.25)` size 0.25 |

The east end of the rail can stay. `(111.55, 108.25)–(112.16, 108.25)` still covers `R_SCL` pad 2. The via `(112.16, 107.60)` can stay. The y=109.59 run can stay if it stops at x=109.90.

That via at `(110.40, 108.25)` already drops to B and runs to `(102.52, 108.55)`. Sliding the knot to x=109.90 keeps 3V3 connected and still leaves SDA connected **while the VBAT bar is missing**.

## The plane conflict

With the knot at x=109.90 and the bar removed, the SDA route is:

1. South through the old rail at x=110.25–110.50.
2. West along y=113.25 from x=108 to x=105.
3. North, then west to **x=103.25**.
4. Straight from `(103.25, 108.25)` to `(103.25, 103.00)`, which is the missing bar.
5. On to U1 pad 27.

VBAT has to join `(100.00, 105.40)` to `(106.20, 105.40)` at about 0.35 mm. Those ends are on opposite sides of the run at x=103.25. A reconnect crosses it:

| Bridge tried | SDA result |
|---|---|
| Bar left out | connected |
| North U around y=104.50–105.40 | 0.800 mm |
| South U up to y=109.10 | 0.800 mm, gap `(101.80, 108.27)–(102.60, 108.27)` |
| Rim at y=114.70 out to x=107.40 | overlaps VBUS_POGO y=114, BTN1, `SW1` pad 1, `R_TS`, and the 3V3 run at y=109.59 (gap 0) |

The minimum remainder after a short-free local bridge is **0.800 mm**.

SCL does not use this opening. With the same copper removed, SCL is still 0.934 mm from `(111.70, 107.35)` to `(111.10, 108.06)`, on the `R_SCL` seat.

## Pours

The crossing `(103.25, 105.40)` is 1.625 mm inside the B GND pour and 1.507 mm inside the In2 3V3 pour. A via there shorts GND and drills the 3V3 plane. The approach at `(104.25, 110.00)` is also inside both pours. A B or In2 lane would be a channel through both planes, not a hop.

## Nets closed

None.

## DRC

No copper edit, so no new DRC. Board matches Pass-AT: `shorting_items=0`, unconnected 6.

## Next

unc=6, shorting=0. Stop. The fat VBAT bar and the only SDA route occupy the same cut from y=103.00 to y=108.25 at x=103.25. No VBUS on the dock.
