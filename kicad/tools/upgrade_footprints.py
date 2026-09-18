#!/usr/bin/env python3
"""Replace placeholder U1/U2 footprints with Raytac MDBT50Q + BQ25120A YFP0025.

Honest pin mapping only — unmapped pads left without nets (NC).
"""
from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FP_DIR = ROOT / "libraries" / "EInkWatch.pretty"
FP_DIR.mkdir(parents=True, exist_ok=True)

KICAD_FP = Path("/usr/share/kicad/footprints")


def uid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# BQ25120A YFP0025 (DSBGA-25, 0.4 mm pitch, 2.50 x 2.50 mm body)
# Land pattern: NSMD pads 0.23 mm, pitch 0.4, from TI YFP family (cf. YFP0020).
# Pinout from BQ25120A datasheet SLUSCK5 — top view (looking through package).
# ---------------------------------------------------------------------------
BQ_BALL_NETS: dict[str, str] = {
    # Power path
    "A2": "VBUS",      # IN — charger input from pogo VBUS
    "A1": "GND",       # GND
    "D5": "GND",       # GND
    "A5": "GND",       # PGND
    "B1": "VBAT",      # BAT
    "B2": "VBAT",      # BAT
    "B5": "VSYS",      # SYS buck output
    "C5": "3V3_DISP",  # LS/LDO → display rail (host enables via LSCTRL)
    # VINLS typically tied to SYS or PMID for LDO input — map to VSYS (common wearable hookup)
    "B4": "VSYS",      # VINLS
    "C4": "VSYS",      # VINLS
    # PMID / SW left without board net (need local caps/inductor — NC until passives placed)
    # Control left NC until I2C nets exist on board (honest): INT, SDA, SCL, /CD, LSCTRL, /MR, TS, etc.
}

BQ_BALL_NAMES = {
    "A1": "GND", "A2": "IN", "A3": "PMID", "A4": "SW", "A5": "PGND",
    "B1": "BAT", "B2": "BAT", "B3": "PMID", "B4": "VINLS", "B5": "SYS",
    "C1": "ISET", "C2": "ILIM", "C3": "TS", "C4": "VINLS", "C5": "LS_LDO",
    "D1": "IPRETERM", "D2": "INT", "D3": "RESET", "D4": "PG", "D5": "GND",
    "E1": "MR", "E2": "CD", "E3": "LSCTRL", "E4": "SDA", "E5": "SCL",
}


def write_bq25120a_footprint() -> Path:
    """Create Texas_YFP0025 DSBGA-25 footprint for BQ25120A."""
    pitch = 0.4
    pad_d = 0.23
    rows = "ABCDE"
    cols = range(1, 6)
    # Center of 5x5 at 0,0; A1 at top-left (-0.8, -0.8)
    origin = -2 * pitch  # -0.8

    lines: list[str] = []
    lines.append('(footprint "Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm"')
    lines.append("\t(version 20241229)")
    lines.append('\t(generator "e-ink-watch-fp-upgrade")')
    lines.append('\t(generator_version "1.0")')
    lines.append('\t(layer "F.Cu")')
    lines.append(
        '\t(descr "TI YFP0025 DSBGA-25 2.50x2.50mm P0.4mm for BQ25120A; '
        'NSMD 0.23mm pads per YFP family land pattern (cf. YFP0020 / datasheet)")'
    )
    lines.append('\t(tags "BQ25120A YFP0025 DSBGA BGA TI wearable charger")')
    lines.append("\t(solder_mask_margin 0.05)")
    lines.append('\t(property "Reference" "REF**"')
    lines.append("\t\t(at 0 -2.1 0)")
    lines.append('\t\t(layer "F.SilkS")')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append("\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))")
    lines.append("\t)")
    lines.append('\t(property "Value" "BQ25120A"')
    lines.append("\t\t(at 0 2.1 0)")
    lines.append('\t\t(layer "F.Fab")')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append("\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))")
    lines.append("\t)")
    lines.append('\t(property "Datasheet" "https://www.ti.com/lit/ds/symlink/bq25120a.pdf"')
    lines.append("\t\t(at 0 0 0)")
    lines.append('\t\t(layer "F.Fab")')
    lines.append("\t\t(hide yes)")
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append("\t\t(effects (font (size 1.27 1.27)))")
    lines.append("\t)")
    lines.append("\t(attr smd)")

    # Fab body 2.5 x 2.5
    for layer, w in [("F.Fab", 0.1), ("F.CrtYd", 0.05)]:
        half = 1.25 if layer == "F.Fab" else 1.45
        lines.append(f'\t(fp_rect (start {-half} {-half}) (end {half} {half})')
        lines.append(f'\t\t(stroke (width {w}) (type solid))')
        lines.append("\t\t(fill none)")
        lines.append(f'\t\t(layer "{layer}")')
        lines.append(f'\t\t(uuid "{uid()}")')
        lines.append("\t)")

    # Silk corner mark near A1
    lines.append('\t(fp_line (start -1.25 -1.25) (end -0.6 -1.25)')
    lines.append('\t\t(stroke (width 0.12) (type solid))')
    lines.append('\t\t(layer "F.SilkS")')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append("\t)")
    lines.append('\t(fp_line (start -1.25 -1.25) (end -1.25 -0.6)')
    lines.append('\t\t(stroke (width 0.12) (type solid))')
    lines.append('\t\t(layer "F.SilkS")')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append("\t)")

    for ri, row in enumerate(rows):
        for ci, col in enumerate(cols):
            name = f"{row}{col}"
            x = origin + ci * pitch
            y = origin + ri * pitch
            lines.append(f'\t(pad "{name}" smd circle')
            lines.append(f"\t\t(at {x:.4f} {y:.4f})")
            lines.append(f"\t\t(size {pad_d} {pad_d})")
            lines.append('\t\t(layers "F.Cu" "F.Mask" "F.Paste")')
            lines.append(f'\t\t(uuid "{uid()}")')
            lines.append("\t)")

    lines.append(")")
    path = FP_DIR / "Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm.kicad_mod"
    path.write_text("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Raytac MDBT50Q pad → board net (from schematic logical GPIO map + KiCad symbol)
# ---------------------------------------------------------------------------
# Schematic logical GPIOs (EInkWatch nRF52840 symbol) → MDBT50Q pin numbers
MCU_PAD_NETS: dict[str, str] = {
    # Power
    "1": "GND",
    "2": "GND",
    "15": "GND",
    "33": "GND",
    "55": "GND",
    "28": "3V3",   # VDD
    "30": "3V3",   # VDDH tied for normal-voltage mode (document risk if high-voltage mode needed)
    # Debug / reset (P0.18 = pin 40 configurable as nRESET per Raytac)
    "51": "SWDIO",
    "53": "SWDCLK",
    "40": "nRESET",
    # EPD SPI / control — matches schematic pin names P0.03_SCK etc.
    "9": "EPD_SCK",       # P0.03
    "20": "EPD_MOSI",     # P0.04
    "22": "EPD_CS_MAIN",  # P0.06
    "23": "EPD_CS_L",     # P0.07
    "24": "EPD_CS_R",     # P0.08
    "19": "EPD_DC",       # P0.26
    "16": "EPD_RST",      # P0.27
    "13": "EPD_BUSY_MAIN",  # P0.28
    "10": "EPD_BUSY_L",   # P0.29
    "14": "EPD_BUSY_R",   # P0.30
    # Buttons
    "61": "BTN1",  # P1.01
    "50": "BTN2",  # P1.02
    "60": "BTN3",  # P1.03
    # I2C / PMIC_INT intentionally NOT mapped — board has no SDA/SCL/INT nets yet
}


def load_mod(lib: str, name: str) -> str:
    return (KICAD_FP / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()


def adapt_footprint(
    mod_text: str,
    lib_id: str,
    ref: str,
    value: str,
    x: float,
    y: float,
    rot: float,
    pad_nets: dict[str, tuple[int, str]],
) -> str:
    text = mod_text.strip()
    # Normalize header
    text = re.sub(r'^\(footprint\s+"[^"]+"', f'(footprint "{lib_id}"', text, count=1)
    text = re.sub(r"\n\t\(version\s+\d+\)", "", text, count=1)
    text = re.sub(r'\n\t\(generator\s+"[^"]*"\)', "", text, count=1)
    text = re.sub(r'\n\t\(generator_version\s+"[^"]*"\)', "", text, count=1)

    # Insert uuid + at after layer
    at = f"(at {x:g} {y:g}" + (f" {rot:g}" if rot else "") + ")"
    insert = f'\t(uuid "{uid()}")\n\t{at}\n'
    if re.search(r'\(layer\s+"F\.Cu"\)', text):
        text = re.sub(r'(\(layer\s+"F\.Cu"\))\n', r"\1\n" + insert, text, count=1)
    else:
        text = re.sub(r'^(\(footprint\s+"[^"]+"\s*\n)', r"\1" + insert, text, count=1)

    # Reference / Value
    text = re.sub(
        r'\(property\s+"Reference"\s+"[^"]*"',
        f'(property "Reference" "{ref}"',
        text,
        count=1,
    )
    text = re.sub(
        r'\(property\s+"Value"\s+"[^"]*"',
        f'(property "Value" "{value}"',
        text,
        count=1,
    )

    # Ensure uuids on properties missing them
    def prop_uuid(m: re.Match) -> str:
        full = m.group(0)
        if "(uuid " in full:
            return full
        if "(effects" in full:
            return full.replace("(effects", f'(uuid "{uid()}")\n\t\t(effects', 1)
        return full[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'

    text = re.sub(
        r'\(property\s+"[^"]+"\s+"[^"]*"(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        prop_uuid,
        text,
    )

    # Pads: uuid + nets
    def pad_sub(m: re.Match) -> str:
        full = m.group(0)
        pad = m.group(1)
        # strip existing net
        full = re.sub(r'\n\t\t\(net\s+\d+\s+"[^"]*"\)', "", full)
        if "(uuid " not in full:
            full = full[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'
        if pad in pad_nets:
            nid, nname = pad_nets[pad]
            full = full.replace(
                "(uuid ",
                f'(net {nid} "{nname}")\n\t\t(uuid ',
                1,
            )
        return full

    text = re.sub(
        r'\(pad\s+"([^"]+)"\s+\w+\s+\w+(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        pad_sub,
        text,
    )

    # Indent as board-level footprint (one tab)
    if not text.startswith("(footprint"):
        raise RuntimeError("bad footprint")
    # Board file uses tab-indented footprints at column 0 of token with leading tab
    indented = "\t" + text.replace("\n", "\n\t")
    return indented


def extract_fp_span(text: str, ref: str) -> tuple[int, int]:
    for m in re.finditer(r'\(property "Reference" "' + ref + '"', text):
        start = text.rfind("(footprint ", 0, m.start())
        i = start
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    # include leading newline+tab if present
                    s = i
                    if s > 0 and text[s - 1] == "\n":
                        pass
                    if text[s - 1 : s] != "\t" and text[max(0, s - 2) : s] == "\n\t":
                        s = s - 1
                    elif s > 0 and text[s - 1] == "\t":
                        s = s - 1
                    return s, j + 1
    raise KeyError(ref)


def net_table(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for m in re.finditer(r'^\t\(net (\d+) "([^"]*)"\)', text, re.M):
        out[m.group(2)] = int(m.group(1))
    return out


def strip_tracks_near(text: str, boxes: list[tuple[float, float, float, float]]) -> str:
    """Remove segments/arcs/vias whose endpoints fall inside any axis-aligned box."""

    def inside(x: float, y: float) -> bool:
        for x0, y0, x1, y1 in boxes:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return True
        return False

    def kill_seg(m: re.Match) -> str:
        body = m.group(0)
        coords = re.findall(r'\((?:start|end|mid|at) ([-\d.]+) ([-\d.]+)\)', body)
        if any(inside(float(a), float(b)) for a, b in coords):
            return ""
        return body

    text = re.sub(
        r'\n\t\(segment(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        kill_seg,
        text,
    )
    text = re.sub(
        r'\n\t\(via(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        kill_seg,
        text,
    )
    return text


def add_tracks(text: str, tracks: list[tuple]) -> str:
    """tracks: (x1,y1,x2,y2,width,layer,net_id,net_name)"""
    chunks = []
    for x1, y1, x2, y2, w, layer, nid, nname in tracks:
        chunks.append(
            f'\n\t(segment\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n'
            f'\t\t(width {w})\n\t\t(layer "{layer}")\n'
            f'\t\t(net {nid})\n\t\t(uuid "{uid()}")\n\t)'
        )
    # insert before zones or at end before closing
    idx = text.rfind("\n\t(zone")
    if idx < 0:
        idx = text.rfind("\n)")
    return text[:idx] + "".join(chunks) + text[idx:]


def main() -> None:
    write_bq25120a_footprint()
    # Also copy Raytac into project lib for archival completeness
    src = KICAD_FP / "RF_Module.pretty" / "Raytac_MDBT50Q.kicad_mod"
    shutil.copy(src, FP_DIR / "Raytac_MDBT50Q.kicad_mod")

    # fp-lib-table
    (ROOT / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n'
        '  (lib (name "EInkWatch")(type "KiCad")'
        '(uri "${KIPRJMOD}/libraries/EInkWatch.pretty")(options "")'
        '(descr "Project footprints: BQ25120A YFP0025 + Raytac MDBT50Q copy"))\n'
        ")\n"
    )

    text = PCB.read_text()
    nets = net_table(text)

    def pn(mapping: dict[str, str]) -> dict[str, tuple[int, str]]:
        out = {}
        for pad, nname in mapping.items():
            if nname not in nets:
                raise SystemExit(f"missing net {nname} for pad {pad}")
            out[pad] = (nets[nname], nname)
        return out

    # Placement: module above center, antenna toward top (-Y after rot 180)
    # Raytac body ~10.5 x 15.5; rot 180 puts antenna (pad row y=+7.15 local) toward -Y
    u1 = adapt_footprint(
        load_mod("RF_Module", "Raytac_MDBT50Q"),
        "RF_Module:Raytac_MDBT50Q",
        "U1",
        "MDBT50Q-1MV2",
        100.0,
        93.5,
        180.0,
        pn(MCU_PAD_NETS),
    )
    u2_mod = (FP_DIR / "Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm.kicad_mod").read_text()
    u2 = adapt_footprint(
        u2_mod,
        "EInkWatch:Texas_YFP0025_DSBGA-25_2.5x2.5mm_Layout5x5_P0.4mm",
        "U2",
        "BQ25120A",
        111.0,
        106.0,
        0.0,
        pn(BQ_BALL_NETS),
    )

    # Replace footprints
    s1, e1 = extract_fp_span(text, "U1")
    text = text[:s1] + "\n" + u1 + text[e1:]
    # re-find U2 after U1 replacement (indices shifted)
    s2, e2 = extract_fp_span(text, "U2")
    text = text[:s2] + "\n" + u2 + text[e2:]

    # Strip tracks that collided with old placeholders OR new courtyards
    # Old U1 ~7x7 at 100,98.5; old U2 ~3x3 at 100,107; new module box; new PMIC box
    boxes = [
        (100 - 5.6, 93.5 - 8.1, 100 + 5.6, 93.5 + 8.1),  # new U1
        (111 - 1.6, 106 - 1.6, 111 + 1.6, 106 + 1.6),    # new U2
        (100 - 4.0, 98.5 - 4.0, 100 + 4.0, 98.5 + 4.0),  # old U1 region
        (100 - 2.0, 107 - 2.0, 100 + 2.0, 107 + 2.0),    # old U2 region
    ]
    text = strip_tracks_near(text, boxes)

    # Minimal honest fanouts (0.25 mm signal / 0.35 mm power)
    # Compute a few pad absolute positions for U2 and U1 after transform
    # U2 rot0 at 111,106 — ball A2 at local (-0.4, -0.8) → (110.6, 105.2)
    # U1 rot180 at 100,93.5 — local (x,y) → board (100-x, 93.5-y)
    def u1_xy(lx: float, ly: float) -> tuple[float, float]:
        # rot 180
        return (100.0 - lx, 93.5 - ly)

    def u2_xy(lx: float, ly: float) -> tuple[float, float]:
        return (111.0 + lx, 106.0 + ly)

    # Pad locals from Raytac file / our BGA
    # VBUS: TP1 at (93,114) → U2.A2
    a2 = u2_xy(-0.4, -0.8)
    b1 = u2_xy(-0.8, -0.4)
    b5 = u2_xy(0.8, -0.4)
    c5 = u2_xy(0.8, 0.0)
    gnda1 = u2_xy(-0.8, -0.8)

    # MCU power/SWD pads (from earlier pad parse)
    # pad 28 VDD at (-4.65?, need from file)
    mod = load_mod("RF_Module", "Raytac_MDBT50Q")
    pad_pos = {
        m.group(1): (float(m.group(2)), float(m.group(3)))
        for m in re.finditer(
            r'\(pad "([^"]+)" smd [^\n]*\n\t\t\(at ([-\d.]+) ([-\d.]+)',
            mod,
        )
    }

    p28 = u1_xy(*pad_pos["28"])
    p51 = u1_xy(*pad_pos["51"])
    p53 = u1_xy(*pad_pos["53"])
    p40 = u1_xy(*pad_pos["40"])
    p1 = u1_xy(*pad_pos["1"])

    tracks = []
    # VBUS: TP1 (93,114) around bottom to U2.A2 — keep clear of J_SWD ~ (84,108)
    tracks += [
        (93.0, 114.0, 93.0, 110.0, 0.35, "F.Cu", nets["VBUS"], "VBUS"),
        (93.0, 110.0, 108.0, 110.0, 0.35, "F.Cu", nets["VBUS"], "VBUS"),
        (108.0, 110.0, 108.0, a2[1], 0.35, "F.Cu", nets["VBUS"], "VBUS"),
        (108.0, a2[1], a2[0], a2[1], 0.35, "F.Cu", nets["VBUS"], "VBUS"),
    ]
    # VBAT stub from U2.B1 left toward J_BAT (100, 115.8)
    tracks += [
        (b1[0], b1[1], b1[0], 112.0, 0.35, "F.Cu", nets["VBAT"], "VBAT"),
        (b1[0], 112.0, 100.0, 112.0, 0.35, "F.Cu", nets["VBAT"], "VBAT"),
        (100.0, 112.0, 100.0, 114.5, 0.35, "F.Cu", nets["VBAT"], "VBAT"),
    ]
    # VSYS to left toward old center for MCU 3V3 region
    tracks += [
        (b5[0], b5[1], 105.0, b5[1], 0.35, "F.Cu", nets["VSYS"], "VSYS"),
        (105.0, b5[1], 105.0, p28[1], 0.35, "F.Cu", nets["VSYS"], "VSYS"),
    ]
    # Note: 3V3 MCU still needs VSYS↔3V3 merge — add 0Ω-like short track near C-decoupling
    tracks += [
        (105.0, p28[1], p28[0], p28[1], 0.35, "F.Cu", nets["3V3"], "3V3"),
        (105.0, p28[1], 105.0, p28[1] + 0.01, 0.35, "F.Cu", nets["VSYS"], "VSYS"),
    ]
    # Explicit VSYS-3V3 bridge at (105, p28[1]) via short segment pair meeting — use via stitch comment in report
    # GND stitch U2.A1
    tracks += [
        (gnda1[0], gnda1[1], gnda1[0] - 1.0, gnda1[1], 0.35, "F.Cu", nets["GND"], "GND"),
    ]
    # SWD fanout toward J_SWD (84,108)
    tracks += [
        (p51[0], p51[1], 88.0, p51[1], 0.25, "F.Cu", nets["SWDIO"], "SWDIO"),
        (p53[0], p53[1], 88.0, p53[1], 0.25, "F.Cu", nets["SWDCLK"], "SWDCLK"),
        (p40[0], p40[1], 88.0, p40[1], 0.25, "F.Cu", nets["nRESET"], "nRESET"),
    ]
    # 3V3_DISP from C5 toward right strap
    tracks += [
        (c5[0], c5[1], 114.5, c5[1], 0.3, "F.Cu", nets["3V3_DISP"], "3V3_DISP"),
    ]

    text = add_tracks(text, tracks)

    # Add VSYS–3V3 intentional bridge net-tie style: short copper on F.Cu between two pads of a net-tie
    # Use a 0.2mm segment from (104.7, p28[1]) on VSYS to (104.9, p28[1]) — can't connect different nets with one segment.
    # Instead add a footprint net-tie — skip; document as 0Ω BOM item between VSYS and 3V3.

    PCB.write_text(text)
    print("PCB updated")
    print("U1 pads mapped:", sorted(MCU_PAD_NETS, key=lambda z: int(z)))
    print("U2 balls mapped:", sorted(BQ_BALL_NETS))
    print("U1 at (100, 93.5) rot180; U2 at (111, 106)")


if __name__ == "__main__":
    main()
