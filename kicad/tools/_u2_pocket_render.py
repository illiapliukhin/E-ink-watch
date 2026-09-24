#!/usr/bin/env python3
"""Render annotated U2-pocket maps (mm) for gpt-6-sol review. No API keys."""
from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BOARD = Path("e-ink-watch.kicad_pcb")
OUT = Path("reports/sol_views")
TMP = Path("/tmp/sol_imgs")

# Pocket window (board mm). West edge 105.6 so moved R_SCL (106.5,110.1) and VBUS x=105.7 stay in frame.
X0, Y0, X1, Y1 = 105.6, 103.2, 117.6, 112.4
PX_PER_MM = 90

NET_COLORS = {
    "GND": (90, 90, 90),
    "3V3": (220, 40, 40),
    "3V3_DISP": (255, 120, 40),
    "VBAT": (40, 160, 80),
    "VBUS": (20, 90, 200),
    "VSYS": (0, 140, 140),
    "PMID": (180, 0, 180),
    "SW": (160, 80, 0),
    "TS": (0, 180, 220),
    "ILIM": (255, 200, 0),
    "ISET": (120, 200, 40),
    "CD": (255, 80, 160),
    "SCL": (80, 80, 255),
    "SDA": (40, 180, 80),
    "LSCTRL": (200, 140, 0),
    "PMIC_INT": (140, 80, 200),
    "IPRETERM": (100, 140, 180),
}

LATENTS = [
    "KEEP: TS via (107.8,105.65) 0.25; ILIM via (110.75,105.80) 0.20",
    "KEEP: R_SCL spread (106.5,110.1,90) pad1 SCL (106.5,110.61) pad2 3V3 (106.5,109.59)",
    "KEEP: CD E2 via (110.6,106.95); ILIM C2 F L w=0.08; GND D5 via (112.4,106.55)+F L to (112.8,107.24)",
    "Sol STEP5 SCL/TS no KEEP. Remaining: A5 GND, west GND, west 3V3, SDA, SCL, TS, PMIC_INT",
]


def load() -> str:
    return BOARD.read_text()


def nets_of(text: str) -> dict[str, str]:
    return dict(re.findall(r'\(net (\d+) "([^"]+)"\)', text))


def rot_pt(px: float, py: float, rot_deg: float) -> tuple[float, float]:
    rad = math.radians(rot_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    # KiCad footprint rotation is clockwise
    return px * cos_a + py * sin_a, -px * sin_a + py * cos_a


class Mapper:
    def __init__(self, x0, y0, x1, y1, ppm):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.ppm = ppm
        self.w = int(round((x1 - x0) * ppm))
        self.h = int(round((y1 - y0) * ppm))

    def xy(self, x, y) -> tuple[int, int]:
        return int(round((x - self.x0) * self.ppm)), int(round((y - self.y0) * self.ppm))

    def wpx(self, mm) -> int:
        return max(1, int(round(mm * self.ppm)))


def parse_segments(text, netmap):
    out = []
    pattern = re.compile(
        r'\t\(segment\n\t\t\(start ([^)]+)\)\n\t\t\(end ([^)]+)\)\n'
        r'\t\t\(width ([^)]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net (\d+)\)'
    )
    for match in pattern.finditer(text):
        x1, y1 = map(float, match.group(1).split())
        x2, y2 = map(float, match.group(2).split())
        out.append((x1, y1, x2, y2, float(match.group(3)), match.group(4), netmap.get(match.group(5), "?")))
    return out


def parse_vias(text, netmap):
    out = []
    pattern = re.compile(
        r'\t\(via\n\t\t\(at ([^)]+)\)\n\t\t\(size ([^)]+)\)\n\t\t\(drill ([^)]+)\)\n'
        r'\t\t\(layers ([^\n]+)\)\n\t\t\(net (\d+)\)'
    )
    for match in pattern.finditer(text):
        x, y = map(float, match.group(1).split())
        out.append((x, y, float(match.group(2)), float(match.group(3)), netmap.get(match.group(5), "?")))
    return out


def parse_footprints(text):
    """Return list of {ref, x, y, rot, pads:[(name,net,lx,ly,sx,sy)]}."""
    fps = []
    for fp_m in re.finditer(r"\t\(footprint ", text):
        start = fp_m.start()
        depth = 0
        i = start
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        body = text[start:i]
        at_m = re.search(r"\t\t\(at ([^)]+)\)", body)
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', body)
        if not at_m or not ref_m:
            continue
        parts = at_m.group(1).split()
        x, y = float(parts[0]), float(parts[1])
        rot = float(parts[2]) if len(parts) > 2 else 0.0
        pads = []
        for pad_m in re.finditer(
            r'\(pad "([^"]+)" (?:smd|thru_hole) [^\n]*\n'
            r'\t\t\t\(at ([^)]+)\)\n'
            r'\t\t\t\(size ([^)]+)\)\n'
            r'\t\t\t\(layers ([^\n]+)\)',
            body,
        ):
            pxy = pad_m.group(2).split()
            lx, ly = float(pxy[0]), float(pxy[1])
            sx, sy = map(float, pad_m.group(3).split()[:2])
            tail = body[pad_m.end() : pad_m.end() + 360]
            next_pad = tail.find("(pad ")
            net_m = re.search(r'\(net \d+ "([^"]+)"\)', tail)
            if net_m and (next_pad < 0 or net_m.start() < next_pad):
                net_name = net_m.group(1)
            else:
                net_name = "NC"
            pads.append(
                (pad_m.group(1), net_name, lx, ly, sx, sy, pad_m.group(4))
            )
        fps.append({"ref": ref_m.group(1), "x": x, "y": y, "rot": rot, "pads": pads})
    return fps


def font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_track(draw, mapper, x1, y1, x2, y2, width, color, fill_outline=None):
    p1, p2 = mapper.xy(x1, y1), mapper.xy(x2, y2)
    w = mapper.wpx(width)
    draw.line([p1, p2], fill=color, width=max(2, w))
    r = max(1, w // 2)
    draw.ellipse((p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r), fill=color)
    draw.ellipse((p2[0] - r, p2[1] - r, p2[0] + r, p2[1] + r), fill=color)
    if fill_outline:
        draw.line([p1, p2], fill=fill_outline, width=max(1, w // 4))


def render_layer(text, layer, title, callouts):
    netmap = nets_of(text)
    segs = parse_segments(text, netmap)
    vias = parse_vias(text, netmap)
    fps = parse_footprints(text)
    mapper = Mapper(X0, Y0, X1, Y1, PX_PER_MM)
    img = Image.new("RGB", (mapper.w, mapper.h + 210), (12, 14, 18))
    draw = ImageDraw.Draw(img)
    # board area
    draw.rectangle((0, 0, mapper.w, mapper.h), fill=(18, 22, 28))

    # grid 0.4 mm (BGA pitch)
    grid = (32, 38, 48)
    x = math.ceil(X0 * 5) / 5
    while x <= X1:
        px, _ = mapper.xy(x, Y0)
        draw.line([(px, 0), (px, mapper.h)], fill=grid, width=1)
        x += 0.4
    y = math.ceil(Y0 * 5) / 5
    while y <= Y1:
        _, py = mapper.xy(X0, y)
        draw.line([(0, py), (mapper.w, py)], fill=grid, width=1)
        y += 0.4

    layer_segs = [s for s in segs if s[5] == layer]
    other_layer = "B.Cu" if layer == "F.Cu" else "F.Cu"
    ghost = [s for s in segs if s[5] == other_layer]
    for x1, y1, x2, y2, width, _ly, net in ghost:
        col = tuple(max(0, c // 5) for c in NET_COLORS.get(net, (80, 80, 80)))
        draw_track(draw, mapper, x1, y1, x2, y2, width, col)

    for x1, y1, x2, y2, width, _ly, net in layer_segs:
        draw_track(draw, mapper, x1, y1, x2, y2, width, NET_COLORS.get(net, (180, 180, 180)))

    for x, y, size, _drill, net in vias:
        cx, cy = mapper.xy(x, y)
        r = mapper.wpx(size / 2)
        col = NET_COLORS.get(net, (200, 200, 200))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=2)
        ir = max(1, mapper.wpx(0.05))
        draw.ellipse((cx - ir, cy - ir, cx + ir, cy + ir), fill=col)

    fnt_s = font(11)
    fnt = font(13)
    fnt_b = font(16)
    for fp in fps:
        if not (X0 - 2 <= fp["x"] <= X1 + 2 and Y0 - 2 <= fp["y"] <= Y1 + 2):
            continue
        for name, net, lx, ly, sx, sy, layers in fp["pads"]:
            wx, wy = rot_pt(lx, ly, fp["rot"])
            px, py = mapper.xy(fp["x"] + wx, fp["y"] + wy)
            # KiCad rot 90 clockwise also rotates pad size axes
            pad_sx, pad_sy = sx, sy
            if abs(fp["rot"] % 180 - 90) < 1:
                pad_sx, pad_sy = sy, sx
            hx, hy = mapper.wpx(pad_sx / 2), mapper.wpx(pad_sy / 2)
            col = NET_COLORS.get(net, (200, 200, 200))
            on_layer = layer in layers
            if not on_layer:
                ghost = tuple(max(0, c // 5) for c in col)
                draw.ellipse(
                    (px - hx, py - hy, px + hx, py + hy),
                    outline=ghost,
                    width=1,
                )
                continue
            draw.ellipse((px - hx, py - hy, px + hx, py + hy), fill=col, outline=(250, 250, 250))
            if fp["ref"] == "U2":
                draw.text((px + 4, py - 12), name, fill=(255, 255, 255), font=fnt_s)
        ox, oy = mapper.xy(fp["x"], fp["y"])
        draw.text((ox + 6, oy - 18), fp["ref"], fill=(240, 240, 160), font=fnt)

    # latent / KEEP boxes
    boxes = [
        ((110.55, 105.62, 110.95, 105.98), "ILIM via KEEP"),
        ((106.15, 109.35, 106.85, 110.85), "R_SCL KEEP"),
        ((107.5, 105.4, 108.1, 105.9), "TS via KEEP"),
        ((110.45, 106.80, 110.75, 107.10), "CD via KEEP"),
        ((112.20, 106.35, 112.95, 107.35), "GND D5 KEEP"),
    ]
    if layer == "F.Cu":
        for (bx0, by0, bx1, by1), _label in boxes:
            p0, p1 = mapper.xy(bx0, by0), mapper.xy(bx1, by1)
            draw.rectangle([p0, p1], outline=(255, 60, 60), width=2)

    # KEEP marker
    kx, ky = mapper.xy(107.8, 105.65)
    draw.ellipse((kx - 10, ky - 10, kx + 10, ky + 10), outline=(40, 255, 120), width=3)

    draw.text((8, 6), title, fill=(255, 255, 255), font=fnt_b)
    # legend
    lx, ly = 8, mapper.h + 8
    draw.text((lx, ly), "Nets: ", fill=(220, 220, 220), font=fnt)
    lx += 50
    for net, col in list(NET_COLORS.items())[:12]:
        draw.rectangle((lx, ly + 4, lx + 12, ly + 16), fill=col)
        draw.text((lx + 14, ly), net, fill=(210, 210, 210), font=fnt_s)
        lx += 78
        if lx > mapper.w - 80:
            lx = 8
            ly += 16
    ly += 22
    for line in callouts:
        draw.text((8, ly), "• " + line, fill=(255, 200, 160), font=fnt_s)
        ly += 16
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    text = load()
    fcu = render_layer(
        text,
        "F.Cu",
        "U2 pocket F.Cu — after GND D5 tie (shorting=0, unc=10)",
        LATENTS,
    )
    bcu = render_layer(
        text,
        "B.Cu",
        "U2 pocket B.Cu — same window, F.Cu ghosted dark",
        [
            "KEEP CD B.Cu L: (110.6,106.95)->(112.65,106.95)->(112.65,108.41)->(113.3,108.41)",
            "TS B.Cu L: (108.51,107)->(107.8,107)->(107.8,105.65)->(110.4,105.65)",
            "ILIM B.Cu y=105.80 from 111.45 to 110.30 then south/east to R_ILIM",
            "Do not B.Cu CD at x=112.4 — clips 3V3 via 0.6@(112.16,107.60)",
        ],
    )
    fcu_path = OUT / "u2_pocket_fcu_annotated.png"
    bcu_path = OUT / "u2_pocket_bcu_annotated.png"
    fcu.save(fcu_path, optimize=True)
    bcu.save(bcu_path, optimize=True)
    print("wrote", fcu_path, fcu_path.stat().st_size)
    print("wrote", bcu_path, bcu_path.stat().st_size)
    # KiCad SVG viewBox is page-sized and a mm crop is unreliable; skip here.


if __name__ == "__main__":
    main()
