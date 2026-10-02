# Pass-BI — Q1 source onto the module 3V3 rail

From Pass-BH (shorting 0, unc 17). U2 stays BQ25619RTWR at `(111.00, 91.00)` rotation 0. This pass does not merge.

## What closed

Q1 pin 2 and `R_LSCTRL` were already one `3V3` island. They were not on the module rail. `EPD_BUSY_L` via `(90.20, 90.80)` sat between `nRESET` at y=90.15 and the open side of the board, and the copper gap was 0.335 mm. A 0.15 mm track needs 0.45 mm.

The via slid in place to `(90.20, 90.96)`. The F.Cu vertical that left it now starts there. The existing B.Cu run from `(105.90, 90.80)` was retargeted onto the new via center. No segment was deleted, and no new via was added. `nRESET` stayed put.

`3V3` then leaves Q1 pin 2 at `(89.45, 93.80)`, runs north to y=90.49, east under the moved via to x=91.50, and south-east around the `3V3_DISP` diagonal onto `(93.80, 96.30)`. That point is on the module rail `(93.80, 96.01)–(93.80, 98.00)`. Checker gaps on the new segments are 0.170 mm or more. A farther slide, to y=91.15, measured 0.059 mm against the B.Cu `3V3_DISP` track and was not kept.

The module `3V3` track still ends at `(98.55, 86.35)`. U1 pad 15 is not on it. `SW_DBG` stays `(90.50, 105.50)`. No VBUS on the dock. U2 was not rotated. The PMID via `(111.35, 103.85)` was not moved. `PSEL` still owns the slot at x=107.81.

## DRC (KiCad 9.0.9, `--severity-error`)

| | Violations | unc | shorting | hole actual 0.000 vs a zone |
| --- | --- | --- | --- | --- |
| Before (Pass-BH) | 857 | 17 | 0 | 98 |
| After | 857 | 16 | 0 | 98 |

The header total is not the gate. `shorting_items` is 0. The 98 hole-to-zone zeros are the same count as Pass-BH. The moved via replaces its own previous hole and zone zeros at `(90.20, 90.80)`; it does not add one. The B.Cu `EPD_BUSY_L` track's zone overlap is the same track, now 15.7008 mm instead of 15.7000 mm.

Three clearance lines changed partners the way Pass-BH already saw. None of them is copper this pass added:

- U1 pad 41 against the existing `nRESET` track `(96.25, 90.15)`, actual 0.100 mm. Pass-BH reported the same track against pad 39.
- The existing `EPD_BUSY_R` track `(105.50, 89.75)` against the `3V3` via `(106.00, 91.35)`, actual 0.110 mm.
- An existing `EPD_MOSI` track against the `EPD_DC` via `(99.00, 85.55)`, actual 0.140 mm.

## Still open (unc 16)

- `VBUS`, `PMID`, `SW`: the north stubs still do not reach the south islands. `L_SYS` and the board edge block SW. No legal F.Cu path at 0.15 mm.
- `REGN`: U2 pin 22, `R_ISET` pin 1, `R_TS`, and `R_VSYS` are still separate. The 0.55 mm channel `VSYS` uses is still one track wide. A second track at y=86.05 beside that run is 0.150 mm from `VSYS`, and the way south from there crosses BTST and the PMID stub.
- `SCL` / `SDA`: `PSEL` still has the only slot at x=107.81. Nothing in this pass took it.
- `VBAT` pin 10, `PMIC_INT`, the old `TS` stub, and the south B.Cu `VSYS` island are unchanged.

`shorting_items` stays 0.
