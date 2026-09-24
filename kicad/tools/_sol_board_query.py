#!/usr/bin/env python3
"""Read-only U2-pocket copper query and clearance probe. No API keys."""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _u2_pocket_render import nets_of, parse_footprints, parse_segments, parse_vias, rot_pt

BOARD = Path(__file__).resolve().parents[1] / "e-ink-watch.kicad_pcb"
RISK_MM = 0.05


def load() -> str:
    return BOARD.read_text()


def clamp(value: float, lo: float, hi: float) -> float:
    return lo if value < lo else hi if value > hi else value


def point_segment_distance(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    dx, dy = x2 - x1, y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-18:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / length_sq
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def segments_cross(
    a1x: float,
    a1y: float,
    a2x: float,
    a2y: float,
    b1x: float,
    b1y: float,
    b2x: float,
    b2y: float,
) -> bool:
    def orient(px, py, qx, qy, rx, ry):
        return (qy - py) * (rx - qx) - (qx - px) * (ry - qy)

    o1 = orient(a1x, a1y, a2x, a2y, b1x, b1y)
    o2 = orient(a1x, a1y, a2x, a2y, b2x, b2y)
    o3 = orient(b1x, b1y, b2x, b2y, a1x, a1y)
    o4 = orient(b1x, b1y, b2x, b2y, a2x, a2y)
    return o1 * o2 < 0 and o3 * o4 < 0


def segment_segment_distance(
    a1x: float,
    a1y: float,
    a2x: float,
    a2y: float,
    b1x: float,
    b1y: float,
    b2x: float,
    b2y: float,
) -> float:
    if segments_cross(a1x, a1y, a2x, a2y, b1x, b1y, b2x, b2y):
        return 0.0
    return min(
        point_segment_distance(a1x, a1y, b1x, b1y, b2x, b2y),
        point_segment_distance(a2x, a2y, b1x, b1y, b2x, b2y),
        point_segment_distance(b1x, b1y, a1x, a1y, a2x, a2y),
        point_segment_distance(b2x, b2y, a1x, a1y, a2x, a2y),
    )


def pad_world(fp: dict, pad: tuple) -> tuple[float, float, float, float, str, str]:
    name, net, local_x, local_y, size_x, size_y, layers = pad
    world_x, world_y = rot_pt(local_x, local_y, fp["rot"])
    if abs(fp["rot"] % 180 - 90) < 1:
        size_x, size_y = size_y, size_x
    return (
        fp["x"] + world_x,
        fp["y"] + world_y,
        size_x,
        size_y,
        net,
        name,
    )


def circle_rect_distance(
    cx: float, cy: float, radius: float, rx: float, ry: float, width: float, height: float
) -> float:
    nearest_x = clamp(cx, rx - width / 2, rx + width / 2)
    nearest_y = clamp(cy, ry - height / 2, ry + height / 2)
    return math.hypot(cx - nearest_x, cy - nearest_y) - radius


def in_window(x: float, y: float, x0: float, y0: float, x1: float, y1: float, pad: float = 0.4) -> bool:
    return x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad


def inspect_window(
    x0: float, y0: float, x1: float, y1: float, layer: str | None = None
) -> str:
    if x1 - x0 > 20 or y1 - y0 > 20:
        return "ERROR window too large; max 20 mm on each axis"
    text = load()
    netmap = nets_of(text)
    segs = parse_segments(text, netmap)
    vias = parse_vias(text, netmap)
    footprints = parse_footprints(text)
    lines = [
        f"BOARD {BOARD.name} window ({x0:.3f},{y0:.3f})-({x1:.3f},{y1:.3f}) layer={layer or 'F.Cu+B.Cu'}"
    ]
    if layer in (None, "F.Cu", "B.Cu"):
        wanted = {layer} if layer else {"F.Cu", "B.Cu"}
        lines.append("SEGMENTS")
        count = 0
        for sx1, sy1, sx2, sy2, width, seg_layer, net in segs:
            if seg_layer not in wanted:
                continue
            if not (
                in_window(sx1, sy1, x0, y0, x1, y1)
                or in_window(sx2, sy2, x0, y0, x1, y1)
            ):
                continue
            lines.append(
                f"  {net:12} {seg_layer:4} ({sx1:.3f},{sy1:.3f})-({sx2:.3f},{sy2:.3f}) w={width:.3f}"
            )
            count += 1
            if count >= 220:
                lines.append("  … truncated")
                break
        lines.append(f"  count={count}")
    lines.append("VIAS (through F.Cu-B.Cu)")
    via_count = 0
    for vx, vy, size, drill, net in vias:
        if not in_window(vx, vy, x0, y0, x1, y1, pad=0.1):
            continue
        lines.append(f"  {net:12} ({vx:.3f},{vy:.3f}) size={size:.3f} drill={drill:.3f}")
        via_count += 1
    lines.append(f"  count={via_count}")
    lines.append("PADS")
    pad_count = 0
    for fp in footprints:
        if not in_window(fp["x"], fp["y"], x0, y0, x1, y1, pad=3.0):
            continue
        shown = []
        for pad in fp["pads"]:
            px, py, size_x, size_y, net, name = pad_world(fp, pad)[:6]
            layers = pad[6]
            if not in_window(px, py, x0, y0, x1, y1, pad=0.2):
                continue
            copper = []
            if "F.Cu" in layers:
                copper.append("F")
            if "B.Cu" in layers:
                copper.append("B")
            shown.append(
                f"{name}:{net}@({px:.3f},{py:.3f}) {size_x:.2f}x{size_y:.2f}/{''.join(copper)}"
            )
        if shown:
            lines.append(
                f"  {fp['ref']} ({fp['x']:.3f},{fp['y']:.3f},rot={fp['rot']:.0f}) "
                + "; ".join(shown[:30])
            )
            pad_count += len(shown)
            if pad_count >= 250:
                lines.append("  … truncated")
                break
    lines.append(f"  pad_hits={pad_count}")
    return "\n".join(lines)


def _hits_for_via(vx: float, vy: float, size: float, net: str) -> list[tuple[float, str]]:
    text = load()
    netmap = nets_of(text)
    radius = size / 2
    hits: list[tuple[float, str]] = []
    for ox, oy, other_size, _drill, other_net in parse_vias(text, netmap):
        if other_net == net:
            continue
        if abs(ox - vx) > 3 or abs(oy - vy) > 3:
            continue
        edge = math.hypot(ox - vx, oy - vy) - radius - other_size / 2
        hits.append((edge, f"via {other_net} ({ox:.3f},{oy:.3f}) size={other_size:.3f}"))
    for fp in parse_footprints(text):
        if abs(fp["x"] - vx) > 6 or abs(fp["y"] - vy) > 6:
            continue
        for pad in fp["pads"]:
            px, py, size_x, size_y, other_net, name = pad_world(fp, pad)
            if other_net == net:
                continue
            if abs(size_x - size_y) < 0.02:
                edge = math.hypot(vx - px, vy - py) - radius - size_x / 2
            else:
                edge = circle_rect_distance(vx, vy, radius, px, py, size_x, size_y)
            hits.append((edge, f"pad {fp['ref']}.{name} {other_net} ({px:.3f},{py:.3f})"))
    for x1, y1, x2, y2, width, seg_layer, other_net in parse_segments(text, netmap):
        if other_net == net:
            continue
        if min(x1, x2) > vx + 3 or max(x1, x2) < vx - 3:
            continue
        if min(y1, y2) > vy + 3 or max(y1, y2) < vy - 3:
            continue
        edge = point_segment_distance(vx, vy, x1, y1, x2, y2) - radius - width / 2
        hits.append(
            (
                edge,
                f"track {other_net} {seg_layer} ({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f}) w={width:.3f}",
            )
        )
    hits.sort(key=lambda item: item[0])
    return hits


def _hits_for_segment(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    width: float,
    layer: str,
    net: str,
) -> list[tuple[float, str]]:
    text = load()
    netmap = nets_of(text)
    half = width / 2
    hits: list[tuple[float, str]] = []
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    for vx, vy, size, _drill, other_net in parse_vias(text, netmap):
        if other_net == net:
            continue
        if abs(vx - mid_x) > 6 or abs(vy - mid_y) > 6:
            continue
        edge = point_segment_distance(vx, vy, x1, y1, x2, y2) - half - size / 2
        hits.append((edge, f"via {other_net} ({vx:.3f},{vy:.3f}) size={size:.3f}"))
    for fp in parse_footprints(text):
        if abs(fp["x"] - mid_x) > 8 or abs(fp["y"] - mid_y) > 8:
            continue
        for pad in fp["pads"]:
            px, py, size_x, size_y, other_net, name = pad_world(fp, pad)
            layers = pad[6]
            if other_net == net:
                continue
            if layer not in layers:
                continue
            pad_radius = max(size_x, size_y) / 2
            edge = point_segment_distance(px, py, x1, y1, x2, y2) - half - pad_radius
            hits.append((edge, f"pad {fp['ref']}.{name} {other_net} ({px:.3f},{py:.3f})"))
    for ox1, oy1, ox2, oy2, other_w, other_layer, other_net in parse_segments(text, netmap):
        if other_net == net or other_layer != layer:
            continue
        if min(ox1, ox2) > max(x1, x2) + 3 or max(ox1, ox2) < min(x1, x2) - 3:
            continue
        edge = (
            segment_segment_distance(x1, y1, x2, y2, ox1, oy1, ox2, oy2)
            - half
            - other_w / 2
        )
        hits.append(
            (
                edge,
                f"track {other_net} {other_layer} ({ox1:.3f},{oy1:.3f})-({ox2:.3f},{oy2:.3f}) w={other_w:.3f}",
            )
        )
    hits.sort(key=lambda item: item[0])
    return hits


def format_hits(label: str, hits: list[tuple[float, str]], limit: int = 12) -> str:
    if not hits:
        return f"{label}\n  no nearby other-net copper"
    overlap = [item for item in hits if item[0] < 0]
    risk = [item for item in hits if 0 <= item[0] < RISK_MM]
    lines = [label, f"  overlap={len(overlap)} risk_lt_{RISK_MM}mm={len(risk)}"]
    for edge, desc in hits[:limit]:
        tag = "OVERLAP" if edge < 0 else ("RISK" if edge < RISK_MM else "ok")
        lines.append(f"  {tag} edge={edge:+.3f} {desc}")
    return "\n".join(lines)


def probe_via(x: float, y: float, size: float, net: str) -> str:
    return format_hits(f"PROBE via {net} ({x:.3f},{y:.3f}) size={size:.3f}", _hits_for_via(x, y, size, net))


def probe_segment(
    x1: float, y1: float, x2: float, y2: float, width: float, layer: str, net: str
) -> str:
    if layer not in ("F.Cu", "B.Cu"):
        return "ERROR layer must be F.Cu or B.Cu (In1/In2 are planes — do not route signals there)"
    label = (
        f"PROBE segment {net} {layer} ({x1:.3f},{y1:.3f})-({x2:.3f},{y2:.3f}) w={width:.3f}"
    )
    return format_hits(label, _hits_for_segment(x1, y1, x2, y2, width, layer, net))


def main() -> None:
    if len(sys.argv) < 5:
        print("usage: _sol_board_query.py x0 y0 x1 y1 [layer]")
        sys.exit(2)
    layer = sys.argv[5] if len(sys.argv) > 5 else None
    print(inspect_window(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), layer))


if __name__ == "__main__":
    main()
