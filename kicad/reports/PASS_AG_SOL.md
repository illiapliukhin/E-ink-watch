# PASS_AG — gpt-6-sol U2 variants (2026-09-24)

Sol (`gpt-6-sol` via Experiential Labs) proposed three floorplans plus a shared
safe start. Coordinates mm. U2 stays at `(111, 106)`. API key is not stored.

## Sol's shared start

1. Slide existing TS via `(110.40, 105.65) → (108.00, 105.65)`, `0.35/0.15`, stay on TS B.Cu.
2. Park ILIM via `(111.45, 105.80) → (109.65, 106.30)`, `0.30/0.15`, then later microvia in C2/C3 (`0.20/0.10`).
3. Only then replace CD/SDA/SCL E-row copper. `shorting_items=0` after every KEEP.

Sol warned that C2/C3 `0.20/0.10` filled microvias need fab confirmation. This board uses through vias `F.Cu`–`B.Cu`.

## Geometry review (do not apply Sol's TS park as written)

| Proposal | Result |
|----------|--------|
| TS via `(108.00, 105.65)` `0.35` | **Overlap** VBAT F `x=108.12` w=0.35, VBAT F `y=105.60` w=0.28, ISET B `x=108.20` w=0.15 |
| TS via `(107.80, 105.65)` `0.35` | Overlap VBAT F vertical `x=108.12` w=0.35 (edge −0.030) |
| TS via `(107.80, 105.65)` `0.25` | **Clear** of pads/tracks/vias. Already the west elbow of TS B.Cu `(107.8, 105.65)-(110.4, 105.65)` |
| ILIM park `(109.65, 106.30)` `0.30` | **Clear** of pads/tracks (IPRETERM vias edge +0.012 / +0.072, not a short) |
| ILIM in-place shrink at `(111.45, 105.80)` | Still inside PMID F `x=111.40` w=0.40 |
| C2/C3 `0.20/0.10` microvia | Not this stackup; skip |

Whole TS B.Cu run at `y=105.65` from `x≈108.12` to `110.40` sits under VBAT F. A through via cannot stay on that run except at the west elbow, and only if size ≤ `0.25`.

KiCad 0402 `rot=90` still maps pad 1 to **+Y**. Sol's new variants use that correctly (`R_SCL` pad 1 at `y+0.51`).

## Variant A — «Восточный разнос» (Sol's preferred floorplan)

- `R_SCL` `(115.60, 109.50, 90)` pad1 SCL `(115.60, 110.01)`
- `R_SDA` `(114.30, 110.80, 0)`
- `R_CD` / `C_LDO` / `R_LSCTRL` stay
- Escapes: CD via `(110.60, 107.20)`, SDA via `(111.40, 107.65)`, SCL via `(111.80, 107.22)`, all `0.30/0.15`
- CD west on In1.Cu `y=109.60` to existing CD via `(113.30, 108.41)`
- SDA on In2.Cu to `R_SDA`; SCL on B.Cu to `R_SCL` pad 1
- TS B.Cu south of C3 then west to R_TS via `(108.51, 107.00)`

**Risk:** In1 is the GND plane and In2 is the 3V3 plane on this board. Do not haul CD/SDA on those layers. LSCTRL via `(110.80, 107.80)` sits in the TS B.Cu path Sol drew.

## Variant B — «Южный ряд резисторов»

Same escapes; cluster further south: `R_SCL` `(115.50, 110.30, 90)`, `R_SDA` `(113.70, 111.60, 0)`, `R_LSCTRL` `(116.70, 108.25, 90)`. Needs a rebuild of the LSCTRL net.

## Variant C — «Минимум перемещений 0402»

Only `R_SCL` `(114.80, 109.80, 90)` pad1 `(114.80, 110.31)`. SDA stays on existing `R_SDA`. Tight vs the 3V3 island at `y=108.25`.

## First KEEP actually tried

Not Sol's `(108.00, 105.65)`. **`ts_via_corner`**: existing TS via → `(107.8, 105.65)` `0.25/0.15`. In-place, no delete, no new copper. DRC: `shorting=0`, `unc=11`.

F stubs at `x=110.4` still overlap VBAT/C2. `ts_f_retract` and `ilim_via_slide` both REVERT (CD/SCL/SDA latents). Next ILIM+CD+`R_SCL` in one save.
