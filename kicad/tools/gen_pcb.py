#!/usr/bin/env python3
"""Generate KiCad 9 e-ink-watch.kicad_pcb: Ø40mm, fine placement, nets, tracks, zones."""
from __future__ import annotations

import math
import re
import uuid
from pathlib import Path

ROOT = Path("/workspace/e-ink-watch-kicad")
FP_ROOT = Path("/usr/share/kicad/footprints")
OUT = ROOT / "e-ink-watch.kicad_pcb"

CX, CY = 100.0, 100.0
DIAM = 40.0
KEEPOUT = 0.9  # mm from Edge.Cuts


def uid() -> str:
    return str(uuid.uuid4())


def load_mod(lib: str, name: str) -> str:
    path = FP_ROOT / f"{lib}.pretty" / f"{name}.kicad_mod"
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def adapt_footprint(
    mod_text: str,
    lib: str,
    name: str,
    ref: str,
    value: str,
    x: float,
    y: float,
    rot: float = 0.0,
) -> str:
    text = mod_text.strip()
    text = re.sub(
        r'^\(footprint\s+"[^"]+"',
        f'(footprint "{lib}:{name}"',
        text,
        count=1,
    )
    text = re.sub(r"\n\t\(version\s+\d+\)", "", text, count=1)
    text = re.sub(r'\n\t\(generator\s+"[^"]*"\)', "", text, count=1)
    text = re.sub(r'\n\t\(generator_version\s+"[^"]*"\)', "", text, count=1)

    at_line = f"\t(at {x:.4f} {y:.4f}" + (f" {rot:g}" if rot else "") + ")"
    insert = f'\t(uuid "{uid()}")\n{at_line}\n\t(path "/")\n'
    if re.search(r'\(layer\s+"F\.Cu"\)', text):
        text = re.sub(
            r'(\(layer\s+"F\.Cu"\))\n',
            r"\1\n" + insert,
            text,
            count=1,
        )
    else:
        text = re.sub(
            r'^(\(footprint\s+"[^"]+"\s*\n)',
            r"\1" + insert,
            text,
            count=1,
        )

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

    def prop_sub(m: re.Match) -> str:
        full = m.group(0)
        if "(uuid " in full:
            return full
        if "(effects" in full:
            return full.replace("(effects", f'(uuid "{uid()}")\n\t\t(effects', 1)
        return full[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'

    text = re.sub(
        r'\(property\s+"[^"]+"\s+"[^"]*"(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        prop_sub,
        text,
    )

    def pad_sub(m: re.Match) -> str:
        full = m.group(0)
        if "(uuid " in full:
            return full
        return full[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'

    text = re.sub(
        r'\(pad\s+"[^"]+"\s+\w+\s+\w+(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        pad_sub,
        text,
    )

    def fptext_sub(m: re.Match) -> str:
        full = m.group(0)
        if "(uuid " in full:
            return full
        if "(effects" in full:
            return full.replace("(effects", f'(uuid "{uid()}")\n\t\t(effects', 1)
        return full

    text = re.sub(
        r'\(fp_text\s+\w+\s+"[^"]*"(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        fptext_sub,
        text,
    )
    return text


def assign_pad_nets(fp_text: str, pad_net: dict[str, tuple[int, str]]) -> str:
    """Insert (net id "name") into pads. pad_net keys are pad numbers as str."""

    def pad_sub(m: re.Match) -> str:
        full = m.group(0)
        pad_name = m.group(1)
        if pad_name not in pad_net:
            return full
        if re.search(r"\(net\s+\d+", full):
            return full
        nid, nname = pad_net[pad_name]
        net_line = f'\t\t(net {nid} "{nname}")\n'
        # insert before uuid
        if "(uuid " in full:
            return full.replace("(uuid ", net_line + "\t\t(uuid ", 1)
        return full[:-1] + "\n" + net_line + "\t)"

    return re.sub(
        r'\(pad\s+"([^"]+)"\s+\w+\s+\w+(?:\s|\n)(?:(?!\n\t\()[\s\S])*?\n\t\)',
        pad_sub,
        fp_text,
    )


# Fine placement: absolute = center + offset; keep ~0.9mm from Ø40 edge
# Connector FPCs ~6mm deep body; pin headers ~2.5mm; switches ~3mm courtyard
PLACEMENTS = [
    # U1 nRF near center slightly upper
    (
        "Package_DFN_QFN",
        "QFN-48-1EP_7x7mm_P0.5mm_EP3.5x3.5mm",
        "U1",
        "nRF52840",
        0.0,
        -1.5,
        0,
    ),
    # U2 PMIC below U1
    (
        "Package_DFN_QFN",
        "QFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm",
        "U2",
        "PMIC",
        0.0,
        7.0,
        0,
    ),
    # J_DISP_MAIN 12 o'clock
    (
        "Connector_FFC-FPC",
        "Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal",
        "J_DISP_MAIN",
        "DISP_MAIN",
        0.0,
        -15.0,
        0,
    ),
    # J_STRAP_L 9 o'clock
    (
        "Connector_FFC-FPC",
        "Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal",
        "J_STRAP_L",
        "STRAP_L",
        -15.0,
        0.5,
        90,
    ),
    # J_STRAP_R 3 o'clock
    (
        "Connector_FFC-FPC",
        "Hirose_FH12-10S-0.5SH_1x10-1MP_P0.50mm_Horizontal",
        "J_STRAP_R",
        "STRAP_R",
        15.0,
        0.5,
        270,
    ),
    # J_BAT 6 o'clock
    (
        "Connector_PinHeader_2.54mm",
        "PinHeader_1x02_P2.54mm_Vertical",
        "J_BAT",
        "BAT",
        0.0,
        15.8,
        0,
    ),
    # SW1–SW3 lower-right arc
    ("Button_Switch_SMD", "SW_SPST_B3U-1000P", "SW1", "BTN1", 9.2, 12.0, 0),
    ("Button_Switch_SMD", "SW_SPST_B3U-1000P", "SW2", "BTN2", 12.0, 9.0, 0),
    ("Button_Switch_SMD", "SW_SPST_B3U-1000P", "SW3", "BTN3", 13.5, 5.5, 0),
    # J_SWD lower-left
    (
        "Connector_PinHeader_2.54mm",
        "PinHeader_1x05_P2.54mm_Vertical",
        "J_SWD",
        "SWD",
        -11.0,
        11.5,
        90,
    ),
    # Decoupling tight to U1/U2
    ("Capacitor_SMD", "C_0402_1005Metric", "C1", "100n", -4.6, 2.2, 0),
    ("Capacitor_SMD", "C_0402_1005Metric", "C2", "100n", 4.6, 2.2, 0),
    ("Capacitor_SMD", "C_0402_1005Metric", "C3", "10u", -3.0, 8.8, 0),
    ("Capacitor_SMD", "C_0402_1005Metric", "C4", "10u", 3.0, 8.8, 0),
    ("Resistor_SMD", "R_0402_1005Metric", "R1", "10k", -5.2, -4.5, 90),
    ("Resistor_SMD", "R_0402_1005Metric", "R2", "10k", 5.2, -4.5, 90),
]

# Net table (id, name) — matches schematic hierarchical labels where possible
NETS: list[tuple[int, str]] = [
    (0, ""),
    (1, "GND"),
    (2, "3V3"),
    (3, "3V3_DISP"),
    (4, "VBAT"),
    (5, "VSYS"),
    (22, "VBUS"),
    (6, "EPD_SCK"),
    (7, "EPD_MOSI"),
    (8, "EPD_DC"),
    (9, "EPD_RST"),
    (10, "EPD_CS_MAIN"),
    (11, "EPD_CS_L"),
    (12, "EPD_CS_R"),
    (13, "EPD_BUSY_MAIN"),
    (14, "EPD_BUSY_L"),
    (15, "EPD_BUSY_R"),
    (16, "SWDIO"),
    (17, "SWDCLK"),
    (18, "nRESET"),
    (19, "BTN1"),
    (20, "BTN2"),
    (21, "BTN3"),
]
NET_ID = {n: i for i, n in NETS}


def N(name: str) -> tuple[int, str]:
    return (NET_ID[name], name)


# Placeholder pin maps (see tools/ROUTE_NOTES.md)
# FPC 10-pin: VCI GND MOSI SCK CS DC RST BUSY GND VCI
FPC_COMMON = {
    "1": N("3V3_DISP"),
    "2": N("GND"),
    "3": N("EPD_MOSI"),
    "4": N("EPD_SCK"),
    "6": N("EPD_DC"),
    "7": N("EPD_RST"),
    "9": N("GND"),
    "10": N("3V3_DISP"),
    "MP": N("GND"),
}

PAD_NETS: dict[str, dict[str, tuple[int, str]]] = {
    "U1": {
        # left side → strap L
        "3": N("EPD_CS_L"),
        "4": N("EPD_BUSY_L"),
        "5": N("GND"),
        "6": N("3V3"),
        # SWD cluster lower-left of package
        "10": N("SWDIO"),
        "11": N("SWDCLK"),
        "12": N("nRESET"),
        # bottom → PMIC / power
        "15": N("3V3"),
        "16": N("GND"),
        "17": N("3V3"),
        "18": N("GND"),
        # buttons lower-right
        "22": N("BTN1"),
        "23": N("BTN2"),
        "24": N("BTN3"),
        # right → strap R
        "28": N("EPD_CS_R"),
        "29": N("EPD_BUSY_R"),
        "30": N("GND"),
        "31": N("3V3"),
        # top → main display SPI
        "40": N("EPD_SCK"),
        "41": N("EPD_MOSI"),
        "42": N("EPD_DC"),
        "43": N("EPD_RST"),
        "44": N("EPD_CS_MAIN"),
        "45": N("EPD_BUSY_MAIN"),
        "46": N("GND"),
        "47": N("3V3"),
        "49": N("GND"),  # EP
    },
    "U2": {
        "1": N("VBAT"),
        "2": N("VBAT"),
        "3": N("GND"),
        "5": N("GND"),
        "6": N("GND"),
        "7": N("VSYS"),
        "8": N("VSYS"),
        "9": N("3V3"),
        "10": N("3V3"),
        "11": N("3V3_DISP"),
        "12": N("3V3_DISP"),
        "13": N("GND"),
        "14": N("GND"),
        "15": N("VBAT"),
        "16": N("VBAT"),
        "17": N("GND"),  # EP
    },
    "J_DISP_MAIN": {
        **FPC_COMMON,
        "5": N("EPD_CS_MAIN"),
        "8": N("EPD_BUSY_MAIN"),
    },
    "J_STRAP_L": {
        **FPC_COMMON,
        "5": N("EPD_CS_L"),
        "8": N("EPD_BUSY_L"),
    },
    "J_STRAP_R": {
        **FPC_COMMON,
        "5": N("EPD_CS_R"),
        "8": N("EPD_BUSY_R"),
    },
    "J_BAT": {"1": N("VBAT"), "2": N("GND")},
    "J_SWD": {
        "1": N("3V3"),
        "2": N("SWDIO"),
        "3": N("SWDCLK"),
        "4": N("nRESET"),
        "5": N("GND"),
    },
    "C1": {"1": N("3V3"), "2": N("GND")},
    "C2": {"1": N("3V3"), "2": N("GND")},
    "C3": {"1": N("3V3"), "2": N("GND")},
    "C4": {"1": N("3V3"), "2": N("GND")},
    "R1": {"1": N("3V3"), "2": N("nRESET")},
    "R2": {"1": N("3V3"), "2": N("EPD_CS_MAIN")},
    "SW1": {"1": N("BTN1"), "2": N("GND")},
    "SW2": {"1": N("BTN2"), "2": N("GND")},
    "SW3": {"1": N("BTN3"), "2": N("GND")},
    "TP1": {"1": N("VBUS")},
    "TP2": {"1": N("GND")},
    "TP3": {"1": N("SWDIO")},
    "TP4": {"1": N("SWDCLK")},
    "TP5": {"1": N("nRESET")},
}

# Local pad offsets from footprint libs (rot=0)
PAD_LOCAL: dict[str, dict[str, tuple[float, float]]] = {
    "U1": {
        **{str(i): (-3.45, -2.75 + (i - 1) * 0.5) for i in range(1, 13)},
        **{str(i): (-2.75 + (i - 13) * 0.5, 3.45) for i in range(13, 25)},
        **{str(i): (3.45, 2.75 - (i - 25) * 0.5) for i in range(25, 37)},
        **{str(i): (2.75 - (i - 37) * 0.5, -3.45) for i in range(37, 49)},
        "49": (0.0, 0.0),
    },
    "U2": {
        "1": (-1.4375, -0.75),
        "2": (-1.4375, -0.25),
        "3": (-1.4375, 0.25),
        "4": (-1.4375, 0.75),
        "5": (-0.75, 1.4375),
        "6": (-0.25, 1.4375),
        "7": (0.25, 1.4375),
        "8": (0.75, 1.4375),
        "9": (1.4375, 0.75),
        "10": (1.4375, 0.25),
        "11": (1.4375, -0.25),
        "12": (1.4375, -0.75),
        "13": (0.75, -1.4375),
        "14": (0.25, -1.4375),
        "15": (-0.25, -1.4375),
        "16": (-0.75, -1.4375),
        "17": (0.0, 0.0),
    },
    "J_DISP_MAIN": {
        **{str(i): (-2.25 + (i - 1) * 0.5, -1.85) for i in range(1, 11)},
        "MP": (-4.15, 1.4),
    },
    "J_STRAP_L": {
        **{str(i): (-2.25 + (i - 1) * 0.5, -1.85) for i in range(1, 11)},
        "MP": (-4.15, 1.4),
    },
    "J_STRAP_R": {
        **{str(i): (-2.25 + (i - 1) * 0.5, -1.85) for i in range(1, 11)},
        "MP": (-4.15, 1.4),
    },
    "J_BAT": {"1": (0.0, 0.0), "2": (0.0, 2.54)},
    "J_SWD": {
        "1": (0.0, 0.0),
        "2": (0.0, 2.54),
        "3": (0.0, 5.08),
        "4": (0.0, 7.62),
        "5": (0.0, 10.16),
    },
    "C1": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},  # approx 0402
    "C2": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},
    "C3": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},
    "C4": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},
    "R1": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},
    "R2": {"1": (-0.5, 0.0), "2": (0.5, 0.0)},
    "SW1": {"1": (-1.7, 0.0), "2": (1.7, 0.0)},
    "SW2": {"1": (-1.7, 0.0), "2": (1.7, 0.0)},
    "SW3": {"1": (-1.7, 0.0), "2": (1.7, 0.0)},
    "TP1": {"1": (0.0, 0.0)},
    "TP2": {"1": (0.0, 0.0)},
    "TP3": {"1": (0.0, 0.0)},
    "TP4": {"1": (0.0, 0.0)},
    "TP5": {"1": (0.0, 0.0)},
}



def pogo_pad_footprint(ref, value, x, y, net_id, net_name, dia=1.5):
    """SMD circular pogo contact on B.Cu (case-back). ENIG recommended."""
    t = "\t"
    r = dia / 2.0
    silk_r = r + 0.2
    crtyd = r + 0.35
    s = []

    def L(n, sline):
        s.append(t * n + sline)

    L(1, f'(footprint "TestPoint:Pogo_Pad_D{dia}mm"')
    L(1, '(layer "B.Cu")')
    L(1, f'(uuid "{uid()}")')
    L(1, f'(at {x:.4f} {y:.4f})')
    L(1, '(path "/")')
    L(1, f'(descr "Pogo contact pad dia {dia}mm on B.Cu — cradle charge/flash")')
    L(1, '(tags "pogo testpoint B.Cu")')
    L(1, f'(property "Reference" "{ref}"')
    L(2, f'(at 0 {-silk_r - 0.6:.3f} 0)')
    L(2, '(layer "B.SilkS")')
    L(2, f'(uuid "{uid()}")')
    L(2, '(effects')
    L(3, '(font')
    L(4, '(size 0.6 0.6)')
    L(4, '(thickness 0.1)')
    L(3, ')')
    L(3, '(justify mirror)')
    L(2, ')')
    L(1, ')')
    L(1, f'(property "Value" "{value}"')
    L(2, f'(at 0 {silk_r + 0.6:.3f} 0)')
    L(2, '(layer "B.Fab")')
    L(2, f'(uuid "{uid()}")')
    L(2, '(effects')
    L(3, '(font')
    L(4, '(size 0.5 0.5)')
    L(4, '(thickness 0.08)')
    L(3, ')')
    L(3, '(justify mirror)')
    L(2, ')')
    L(1, ')')
    L(1, '(attr smd)')
    L(1, '(fp_circle')
    L(2, '(center 0 0)')
    L(2, f'(end {silk_r:.3f} 0)')
    L(2, '(stroke')
    L(3, '(width 0.1)')
    L(3, '(type solid)')
    L(2, ')')
    L(2, '(fill no)')
    L(2, '(layer "B.SilkS")')
    L(2, f'(uuid "{uid()}")')
    L(1, ')')
    L(1, '(fp_circle')
    L(2, '(center 0 0)')
    L(2, f'(end {crtyd:.3f} 0)')
    L(2, '(stroke')
    L(3, '(width 0.05)')
    L(3, '(type solid)')
    L(2, ')')
    L(2, '(fill no)')
    L(2, '(layer "B.CrtYd")')
    L(2, f'(uuid "{uid()}")')
    L(1, ')')
    L(1, '(pad "1" smd circle')
    L(2, '(at 0 0)')
    L(2, f'(size {dia:g} {dia:g})')
    L(2, '(layers "B.Cu" "B.Mask")')
    L(2, f'(net {net_id} "{net_name}")')
    L(2, f'(uuid "{uid()}")')
    L(1, ')')
    L(1, ')')
    return "\n".join(s) + "\n"


POGO_Y = 12.2
POGO_PITCH = 2.54
POGO_DEFS = [
    ("TP1", "VCHG", "VBUS", -2),
    ("TP2", "GND", "GND", -1),
    ("TP3", "SWDIO", "SWDIO", 0),
    ("TP4", "SWDCLK", "SWDCLK", 1),
    ("TP5", "nRESET", "nRESET", 2),
]


def world_xy(ref: str, pad: str, placements_map: dict) -> tuple[float, float]:
    x, y, rot = placements_map[ref]
    lx, ly = PAD_LOCAL[ref][pad]
    rad = math.radians(rot)
    c, s = math.cos(rad), math.sin(rad)
    # KiCad: positive rotation is clockwise in PCB? Actually CCW in older; in KiCad PCB
    # rotation is clockwise for footprints when angle increases... empirically:
    # at angle θ: x' = x*cos - y*sin, y' = x*sin + y*cos for CCW.
    # KiCad uses CCW for sch, but footprint at: rotation is clockwise.
    # Standard KiCad board: (at x y ang) rotates footprint clockwise by ang.
    # Local point after CW rot: x' = lx*cos(a) + ly*sin(a), y' = -lx*sin(a) + ly*cos(a)
    a = math.radians(rot)
    wx = x + lx * math.cos(a) + ly * math.sin(a)
    wy = y - lx * math.sin(a) + ly * math.cos(a)
    return wx, wy


HEADER_TEMPLATE = '''(kicad_pcb
	(version 20241229)
	(generator "pcbnew")
	(generator_version "9.0")
	(general
		(thickness 1.6)
		(legacy_teardrops no)
	)
	(paper "A4")
	(title_block
		(title "E-INK WATCH BLE")
		(date "2026-09-18")
		(rev "0.1")
		(company "")
		(comment 1 "Ø40mm circular watch PCB — placed+routed REV0.1")
	)
	(layers
		(0 "F.Cu" signal)
		(2 "B.Cu" signal)
		(9 "F.Adhes" user "F.Adhesive")
		(11 "B.Adhes" user "B.Adhesive")
		(13 "F.Paste" user)
		(15 "B.Paste" user)
		(5 "F.SilkS" user "F.Silkscreen")
		(7 "B.SilkS" user "B.Silkscreen")
		(1 "F.Mask" user)
		(3 "B.Mask" user)
		(17 "Dwgs.User" user "User.Drawings")
		(19 "Cmts.User" user "User.Comments")
		(21 "Eco1.User" user "User.Eco1")
		(23 "Eco2.User" user "User.Eco2")
		(25 "Edge.Cuts" user)
		(27 "Margin" user)
		(31 "F.CrtYd" user "F.Courtyard")
		(29 "B.CrtYd" user "B.Courtyard")
		(35 "F.Fab" user)
		(33 "B.Fab" user)
		(39 "User.1" user)
		(41 "User.2" user)
		(43 "User.3" user)
		(45 "User.4" user)
	)
	(setup
		(pad_to_mask_clearance 0)
		(allow_soldermask_bridges_in_footprints no)
		(tenting front back)
		(pcbplotparams
			(layerselection 0x00000000_00000000_55555555_5755f5ff)
			(plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)
			(disableapertmacros no)
			(usegerberextensions no)
			(usegerberattributes yes)
			(usegerberadvancedattributes yes)
			(creategerberjobfile yes)
			(dashed_line_dash_ratio 12.000000)
			(dashed_line_gap_ratio 3.000000)
			(svgprecision 4)
			(plotframeref no)
			(mode 1)
			(useauxorigin no)
			(hpglpennumber 1)
			(hpglpenspeed 20)
			(hpglpendiameter 15.000000)
			(pdf_front_fp_property_popups yes)
			(pdf_back_fp_property_popups yes)
			(pdf_metadata yes)
			(pdf_single_document no)
			(dxfpolygonmode yes)
			(dxfimperialunits yes)
			(dxfusepcbnewfont yes)
			(psnegative no)
			(psa4output no)
			(plot_black_and_white yes)
			(sketchpadsonfab no)
			(plotpadnumbers no)
			(hidednponfab no)
			(sketchdnponfab yes)
			(crossoutdnponfab yes)
			(subtractmaskfromsilk no)
			(outputformat 1)
			(mirror no)
			(drillshape 1)
			(scaleselection 1)
			(outputdirectory "")
		)
	)
'''


def gr_circle() -> str:
    r = DIAM / 2.0
    return f'''	(gr_circle
		(center {CX:g} {CY:g})
		(end {CX + r:g} {CY:g})
		(stroke
			(width 0.05)
			(type default)
		)
		(fill no)
		(layer "Edge.Cuts")
		(uuid "{uid()}")
	)
'''


def gr_text(txt: str, x: float, y: float, size: float = 1.5) -> str:
    return f'''	(gr_text "{txt}"
		(at {x:g} {y:g} 0)
		(layer "F.SilkS")
		(uuid "{uid()}")
		(effects
			(font
				(size {size:g} {size:g})
				(thickness 0.2)
			)
		)
	)
'''


def segment(x1, y1, x2, y2, width, layer, net_id) -> str:
    return f'''	(segment
		(start {x1:.4f} {y1:.4f})
		(end {x2:.4f} {y2:.4f})
		(width {width:g})
		(layer "{layer}")
		(net {net_id})
		(uuid "{uid()}")
	)
'''


def via(x, y, net_id, size=0.6, drill=0.3) -> str:
    return f'''	(via
		(at {x:.4f} {y:.4f})
		(size {size:g})
		(drill {drill:g})
		(layers "F.Cu" "B.Cu")
		(net {net_id})
		(uuid "{uid()}")
	)
'''


def manhattan(
    x1, y1, x2, y2, width, layer, net_id, bend="hv"
) -> list[str]:
    """Two-segment Manhattan route."""
    out = []
    if abs(x1 - x2) < 0.01 and abs(y1 - y2) < 0.01:
        return out
    if abs(x1 - x2) < 0.01 or abs(y1 - y2) < 0.01:
        out.append(segment(x1, y1, x2, y2, width, layer, net_id))
        return out
    if bend == "hv":
        mx, my = x2, y1
    else:
        mx, my = x1, y2
    out.append(segment(x1, y1, mx, my, width, layer, net_id))
    out.append(segment(mx, my, x2, y2, width, layer, net_id))
    return out


def circle_pts(cx, cy, r, n=64) -> str:
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append(f"(xy {cx + r * math.cos(a):.4f} {cy + r * math.sin(a):.4f})")
    # wrap lines ~4 pts
    lines = []
    for i in range(0, n, 4):
        lines.append("\t\t\t\t" + " ".join(pts[i : i + 4]))
    return "\n".join(lines)


def zone(net_id: int, net_name: str, layer: str, r: float = 19.1) -> str:
    return f'''	(zone
		(net {net_id})
		(net_name "{net_name}")
		(layer "{layer}")
		(uuid "{uid()}")
		(hatch edge 0.508)
		(connect_pads yes
			(clearance 0.2)
		)
		(min_thickness 0.15)
		(filled_areas_thickness no)
		(fill yes
			(thermal_gap 0.3)
			(thermal_bridge_width 0.3)
			(smoothing fillet)
			(radius 0.5)
		)
		(polygon
			(pts
{circle_pts(CX, CY, r)}
			)
		)
	)
'''


def balance_parens(s: str) -> bool:
    depth = 0
    in_str = False
    esc = False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def build_routes(pmap: dict) -> list[str]:
    """REV0.2 routing — unique escape lanes; via farms ≥1.0 mm; no via on 0.5 mm pads."""
    parts: list[str] = []
    W_SIG, W_PWR, W_PWR_WIDE = 0.18, 0.4, 0.5
    VIA_S, VIA_D = 0.6, 0.3

    def pad(ref, p):
        return world_xy(ref, p, pmap)

    def add_seg(x1, y1, x2, y2, w, layer, net):
        if abs(x1 - x2) < 0.001 and abs(y1 - y2) < 0.001:
            return
        parts.append(segment(x1, y1, x2, y2, w, layer, NET_ID[net]))

    def add_via(x, y, net):
        parts.append(via(x, y, NET_ID[net], size=VIA_S, drill=VIA_D))

    def path(pts, w, layer, net):
        for (a, b) in zip(pts, pts[1:]):
            add_seg(a[0], a[1], b[0], b[1], w, layer, net)

    def stub_via(x, y, net, dx=0.0, dy=0.0, w=W_PWR):
        vx, vy = x + dx, y + dy
        add_seg(x, y, vx, vy, w, "F.Cu", net)
        add_via(vx, vy, net)
        return vx, vy

    # ----- POWER -----
    bx, by = pad("J_BAT", "1")
    u21 = pad("U2", "1")
    path([(bx, by), (bx, u21[1]), u21], W_PWR_WIDE, "F.Cu", "VBAT")
    for a, b in [("1", "2"), ("1", "16"), ("16", "15")]:
        p1, p2 = pad("U2", a), pad("U2", b)
        add_seg(p1[0], p1[1], p2[0], p2[1], W_PWR, "F.Cu", "VBAT")

    add_seg(*pad("U2", "7"), *pad("U2", "8"), W_PWR, "F.Cu", "VSYS")

    u29, u210 = pad("U2", "9"), pad("U2", "10")
    u115, u117 = pad("U1", "15"), pad("U1", "17")
    add_seg(*u29, *u210, W_PWR, "F.Cu", "3V3")
    path([u29, (u29[0], u115[1]), u115], W_PWR, "F.Cu", "3V3")
    add_seg(*u115, *u117, W_PWR, "F.Cu", "3V3")
    for uref, upad, cref in [("U1","15","C1"),("U1","17","C2"),("U2","9","C3"),("U2","10","C4")]:
        a, b = pad(uref, upad), pad(cref, "1")
        path([a, (b[0], a[1]), b], W_PWR, "F.Cu", "3V3")

    u16, u131 = pad("U1", "6"), pad("U1", "31")
    vx_l, vy_l = stub_via(*u16, "3V3", dx=-1.5, dy=-0.8, w=W_PWR)
    vx_r, vy_r = stub_via(*u131, "3V3", dx=+1.5, dy=-0.8, w=W_PWR)
    vx_f, vy_f = stub_via(*u117, "3V3", dx=+1.8, dy=+1.4, w=W_PWR)
    path([(vx_f, vy_f), (vx_r, vy_f), (vx_r, vy_r)], W_PWR, "B.Cu", "3V3")
    path([(vx_l, vy_l), (vx_r, vy_r)], W_PWR, "B.Cu", "3V3")
    swd1 = pad("J_SWD", "1")
    path([(vx_l, vy_l), (vx_l, swd1[1]), swd1], W_PWR, "F.Cu", "3V3")

    u147 = pad("U1", "47")
    path([u147, (pad("R1", "1")[0], u147[1]), pad("R1", "1")], W_SIG, "F.Cu", "3V3")
    path([u147, (u147[0], 94.8), (pad("R2", "1")[0], 94.8), pad("R2", "1")], W_SIG, "F.Cu", "3V3")

    u211, u212 = pad("U2", "11"), pad("U2", "12")
    add_seg(*u211, *u212, W_PWR, "F.Cu", "3V3_DISP")
    main1, main10 = pad("J_DISP_MAIN", "1"), pad("J_DISP_MAIN", "10")
    path([u211, (95.2, u211[1]), (95.2, 87.0), (main1[0], 87.0), main1], W_PWR, "F.Cu", "3V3_DISP")
    path([main1, (main1[0], 82.40), (main10[0], 82.40), main10], W_PWR, "F.Cu", "3V3_DISP")

    for side, jref, bus_y, u_via in [
        ("L", "J_STRAP_L", 108.5, (96.0, 105.2)),
        ("R", "J_STRAP_R", 89.5, (104.0, 105.2)),
    ]:
        j1, j10 = pad(jref, "1"), pad(jref, "10")
        add_seg(u212[0], u212[1], u_via[0], u_via[1], W_PWR, "F.Cu", "3V3_DISP")
        add_via(*u_via, "3V3_DISP")
        x_land = j1[0] + (1.3 if side == "L" else -1.3)
        path([u_via, (u_via[0], bus_y), (x_land, bus_y)], W_PWR, "B.Cu", "3V3_DISP")
        add_via(x_land, bus_y, "3V3_DISP")
        path([(x_land, bus_y), (x_land, j1[1]), j1], W_PWR, "F.Cu", "3V3_DISP")
        path([j1, (x_land, j1[1]), (x_land, j10[1]), j10], W_PWR, "F.Cu", "3V3_DISP")

    # ----- GND -----
    for ref, p in [("U1", "49"), ("U2", "17")]:
        add_via(*pad(ref, p), "GND")
    add_via(*pad("J_BAT", "2"), "GND")
    add_via(*pad("J_SWD", "5"), "GND")
    for ref, p, dx, dy in [
        ("C1", "2", 0.4, 1.0), ("C2", "2", -0.4, 1.0),
        ("C3", "2", 0.4, 1.0), ("C4", "2", -0.4, 1.0),
        ("SW1", "2", 0.0, 1.0), ("SW2", "2", 0.0, 1.0), ("SW3", "2", 0.0, 1.0),
        ("J_DISP_MAIN", "2", 0.0, 1.1),
        ("J_STRAP_L", "2", 1.1, 0.0), ("J_STRAP_R", "2", -1.1, 0.0),
    ]:
        stub_via(*pad(ref, p), "GND", dx=dx, dy=dy, w=W_PWR)
    for ref, p, dx, dy in [
        ("U1", "5", -1.7, 0.0), ("U1", "16", -1.2, 1.7), ("U1", "18", 1.2, 1.7),
        ("U1", "30", 1.7, 0.0), ("U1", "46", 0.0, -1.7),
        ("U2", "3", -1.5, 0.0), ("U2", "5", -1.0, 1.5), ("U2", "6", 1.0, 1.5),
        ("U2", "13", 1.0, -1.5), ("U2", "14", -1.0, -1.5),
    ]:
        stub_via(*pad(ref, p), "GND", dx=dx, dy=dy, w=W_PWR)
    path([pad("U1", "49"), pad("U2", "17")], W_PWR_WIDE, "F.Cu", "GND")

    for jref in ("J_DISP_MAIN", "J_STRAP_L", "J_STRAP_R"):
        p2, p9 = pad(jref, "2"), pad(jref, "9")
        if jref == "J_DISP_MAIN":
            path([p2, (p2[0], 84.1), (p9[0], 84.1), p9], W_PWR, "F.Cu", "GND")
            mp = pad(jref, "MP")
            path([p2, (mp[0], p2[1]), mp], W_PWR, "F.Cu", "GND")
        else:
            x_g = p2[0] + (-1.2 if jref == "J_STRAP_L" else 1.2)
            path([p2, (x_g, p2[1]), (x_g, p9[1]), p9], W_PWR, "F.Cu", "GND")
            if "MP" in PAD_LOCAL[jref]:
                mp = pad(jref, "MP")
                path([p2, (mp[0], p2[1]), mp], W_PWR, "F.Cu", "GND")

    # ----- SPI MAIN: unique escape_y per net, then farm via, B to land -----
    main_spi = [
        # net, u1, fpc, farm_x, escape_y
        ("EPD_SCK", "40", "4", 97.0, 94.40),
        ("EPD_MOSI", "41", "3", 98.0, 93.80),
        ("EPD_DC", "42", "6", 99.0, 93.20),
        ("EPD_RST", "43", "7", 100.0, 92.60),
        ("EPD_CS_MAIN", "44", "5", 101.0, 92.00),
        ("EPD_BUSY_MAIN", "45", "8", 102.0, 91.40),
    ]
    land_y = 85.2
    for net, u1p, fp, fx, ey in main_spi:
        a, b = pad("U1", u1p), pad("J_DISP_MAIN", fp)
        path([a, (a[0], ey), (fx, ey)], W_SIG, "F.Cu", net)
        add_via(fx, ey, net)  # via at unique (fx, ey) — both unique ⇒ ≥0.6 diag
        path([(fx, ey), (fx, land_y)], W_SIG, "B.Cu", net)
        add_via(fx, land_y, net)
        # land: unique fx column → jog to pad at land_y then vertical
        path([(fx, land_y), (b[0], land_y), b], W_SIG, "F.Cu", net)

    path(
        [pad("R2", "2"), (pad("R2", "2")[0], 94.9), (101.0, 94.9), (101.0, 92.00)],
        W_SIG, "F.Cu", "EPD_CS_MAIN",
    )

    # ----- SPI straps: branch from MAIN vias on B; unique land_dx -----
    strap_spi = [
        ("EPD_SCK", "4", 97.0, 94.40, 96.8, 1.2),
        ("EPD_MOSI", "3", 98.0, 93.80, 97.8, 2.2),
        ("EPD_DC", "6", 99.0, 93.20, 98.8, 3.2),
        ("EPD_RST", "7", 100.0, 92.60, 99.8, 4.2),
    ]
    for net, fp, fx, ey, bus_y, land_dx in strap_spi:
        # B from main via up/down to bus_y (may be north or south of ey)
        path([(fx, ey), (fx, bus_y)], W_SIG, "B.Cu", net)
        for jref, sign in (("J_STRAP_L", +1), ("J_STRAP_R", -1)):
            b = pad(jref, fp)
            x_land = b[0] + sign * land_dx
            path([(fx, bus_y), (x_land, bus_y)], W_SIG, "B.Cu", net)
            add_via(x_land, bus_y, net)
            path([(x_land, bus_y), (b[0], bus_y), b], W_SIG, "F.Cu", net)

    # CS/BUSY
    for u1p, fp, net, mid_x in [
        ("3", "5", "EPD_CS_L", 91.2), ("4", "8", "EPD_BUSY_L", 90.2),
        ("28", "5", "EPD_CS_R", 108.8), ("29", "8", "EPD_BUSY_R", 109.8),
    ]:
        jref = "J_STRAP_L" if "_L" in net else "J_STRAP_R"
        a, b = pad("U1", u1p), pad(jref, fp)
        path([a, (mid_x, a[1]), (mid_x, b[1]), b], W_SIG, "F.Cu", net)

    # SWD / BTN
    for u1p, jp, net, mid_x in [
        ("10", "2", "SWDIO", 92.2), ("11", "3", "SWDCLK", 91.2), ("12", "4", "nRESET", 90.2),
    ]:
        a, b = pad("U1", u1p), pad("J_SWD", jp)
        path([a, (mid_x, a[1]), (mid_x, b[1]), b], W_SIG, "F.Cu", net)
    path([pad("R1", "2"), (pad("R1", "2")[0], pad("U1", "12")[1]), pad("U1", "12")], W_SIG, "F.Cu", "nRESET")
    for u1p, sw, net, mid_x in [
        ("22", "SW1", "BTN1", 106.8), ("23", "SW2", "BTN2", 107.6), ("24", "SW3", "BTN3", 108.4),
    ]:
        a, b = pad("U1", u1p), pad(sw, "1")
        path([a, (a[0], 103.6), (mid_x, 103.6), (mid_x, b[1]), b], W_SIG, "F.Cu", net)


    # ----- POGO cradle (B.Cu pads TP1-TP5): primary field flash + charge -----
    tp = {ref: pad(ref, "1") for ref in ("TP1", "TP2", "TP3", "TP4", "TP5")}
    add_via(tp["TP2"][0], tp["TP2"][1], "GND")
    for ref, net, jpad in [
        ("TP3", "SWDIO", "2"),
        ("TP4", "SWDCLK", "3"),
        ("TP5", "nRESET", "4"),
    ]:
        px, py = tp[ref]
        add_via(px, py, net)
        jx, jy = pad("J_SWD", jpad)
        mid_y = min(py, jy) - 0.8
        path([(px, py), (px, mid_y), (jx, mid_y), (jx, jy)], W_SIG, "F.Cu", net)
    # VBUS/VCHG: via ON B.Cu pogo pad (stitch), then F stub toward U2
    # PMIC VBUS pin TBD on real BQ footprint — stub is attach point only
    px, py = tp["TP1"]
    add_via(px, py, "VBUS")
    path(
        [(px, py), (px, py - 1.5), (px, pad("U2", "1")[1]), (pad("U2", "1")[0] - 2.8, pad("U2", "1")[1])],
        W_PWR,
        "F.Cu",
        "VBUS",
    )

    return parts


def main() -> None:
    # placement map for routing
    pmap: dict[str, tuple[float, float, float]] = {}
    for lib, name, ref, value, dx, dy, rot in PLACEMENTS:
        pmap[ref] = (CX + dx, CY + dy, rot)
        d = math.hypot(dx, dy)
        margin = DIAM / 2 - KEEPOUT - d
        print(f"place {ref:12} @ ({CX+dx:.2f},{CY+dy:.2f}) r={d:.2f} edge_margin≈{margin:.2f}")

    parts: list[str] = [HEADER_TEMPLATE]
    for nid, nname in NETS:
        parts.append(f'\t(net {nid} "{nname}")\n')

    parts.append(gr_circle())
    parts.append(gr_text("E-INK WATCH BLE", CX, CY - 12.0, 1.1))
    parts.append(gr_text("Ø40mm REV0.2", CX, CY + 13.8, 0.9))

    placed = []
    for lib, name, ref, value, dx, dy, rot in PLACEMENTS:
        mod = load_mod(lib, name)
        fp = adapt_footprint(mod, lib, name, ref, value, CX + dx, CY + dy, rot)
        if ref in PAD_NETS:
            fp = assign_pad_nets(fp, PAD_NETS[ref])
        parts.append(fp)
        if not fp.endswith("\n"):
            parts.append("\n")
        placed.append(ref)

    # Pogo pad array on B.Cu (primary field flash + charge cradle)
    for ref, val, nname, idx in POGO_DEFS:
        px = CX + idx * POGO_PITCH
        py = CY + POGO_Y
        pmap[ref] = (px, py, 0.0)
        parts.append(pogo_pad_footprint(ref, val, px, py, NET_ID[nname], nname, dia=1.5))
        placed.append(ref)
        print(f"place {ref:12} @ ({px:.2f},{py:.2f}) pogo B.Cu {val}/{nname}")
    parts.append(gr_text("POGO CHARGE+SWD", CX, CY + 14.6, 0.7))

    # Zones first (under tracks visually doesn't matter in sexpr)
    parts.append(zone(NET_ID["GND"], "GND", "B.Cu", r=19.1))
    parts.append(zone(NET_ID["3V3"], "3V3", "F.Cu", r=12.0))  # inner pour around MCU/PMIC

    # Tracks + vias
    routes = build_routes(pmap)
    parts.extend(routes)
    print(f"segments+vias blocks: {len(routes)}")

    parts.append("\t(embedded_fonts no)\n)\n")
    pcb = "".join(parts)

    if not balance_parens(pcb):
        raise SystemExit("ERROR: unbalanced parentheses in generated PCB")

    lock = ROOT / "~e-ink-watch.kicad_pcb.lck"
    if lock.exists():
        try:
            lock.unlink()
        except OSError:
            pass

    OUT.write_text(pcb, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"\nWrote {OUT} ({size} bytes)")
    print("Refs:", ", ".join(placed))
    text = OUT.read_text(encoding="utf-8")
    assert "Edge.Cuts" in text
    assert "(footprint " in text
    assert "(segment" in text
    assert "(zone" in text
    assert '(net 6 "EPD_SCK")' in text
    print("OK: Edge.Cuts + footprints + nets + tracks + zones")


if __name__ == "__main__":
    main()
