# cursor.md — agent lessons (E Ink watch / KiCad)

Do not skip these on the next PCB pass.

## Verification

- After every copper edit run `kicad-cli pcb drc` and keep `shorting_items=0` plus power-priority pairs at 0. Revert the board if the gate fails.
- Rebuild KEEP edits from `backups/_passaf_session_base.kicad_pcb` with `tools/_pass_af_apply_keeps.py` before treating a pass as done.
- A clearance probe that only measures endpoints will miss crossing tracks. Include segment–segment intersection and **pads**, not only tracks/vias.

## KiCad pitfalls found

- Copied footprints (SW1/SW2/SW3) reused pad UUIDs. KiCad then reports the wrong ref for unconnected pads. Uniquify duplicate `(uuid …)` before trusting DRC ratsnests.
- Hirose FH12 0.5 mm: middle pins (GND on pad 2) must exit along **+X / cable**, not toward pad 1/3 on the 0.5 mm pitch. A diagonal from pad 2 shorts `3V3_DISP` or `EPD_MOSI`.
- Inserting long B.Cu on the west rim (x≈81.8) shorts existing GND at x≈82.0. West `3V3_DISP` cannot cross the SWD/3V3 forest on F.Cu.
- `pcbnew SaveBoard` after adding copper can promote distant clearance to `shorting_items`. Prefer sexpr insert next to the PMID via `(111.35, 103.85)`.

## Hard gates (do not relax)

- `shorting_items = 0`
- Power pairs: GND↔VBUS/VBAT/VBUS_POGO/SW/VSYS, 3V3↔GND, 3V3_DISP↔GND, 3V3↔3V3_DISP
- Pocket: PMID↔VBUS, 3V3_DISP↔PMID, PMID↔SW
- Do not apply VBUS on the dock while any power short is possible
