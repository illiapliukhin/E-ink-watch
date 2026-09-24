#!/usr/bin/env python3
"""Render a KiCad 9 .kicad_pcb top view to PNG (no KiCad runtime required)."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import sexpdata
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle, Polygon as MplPolygon


def sym(value) -> str:
    if isinstance(value, sexpdata.Symbol):
        return value.value()
    return str(value)


def find_nodes(tree, name: str) -> list:
    found: list = []
    for item in tree:
        if isinstance(item, list) and item and sym(item[0]) == name:
            found.append(item)
        if isinstance(item, list):
            found.extend(find_nodes(item, name))
    return found


def node_field(node: list, key: str, default=None):
    for item in node[1:]:
        if isinstance(item, list) and item and sym(item[0]) == key:
            if len(item) >= 3:
                return item
            if len(item) == 2:
                return item[1]
    return default


def parse_xy(pair) -> tuple[float, float] | None:
    if not isinstance(pair, list) or len(pair) < 3:
        return None
    if sym(pair[0]) in {"at", "start", "end", "center", "xy"}:
        return float(pair[1]), float(pair[2])
    return None


def parse_point_node(node: list, key: str) -> tuple[float, float] | None:
    value = node_field(node, key)
    if isinstance(value, list):
        return parse_xy(value)
    return None


def build_net_map(tree: list) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in tree:
        if isinstance(item, list) and item and sym(item[0]) == "net" and len(item) >= 3:
            name = item[2]
            mapping[str(item[1])] = name if isinstance(name, str) else sym(name)
    return mapping


def transform_local(local_x: float, local_y: float, origin: tuple[float, float], angle_deg: float) -> tuple[float, float]:
    radians = math.radians(angle_deg)
    rotated_x = local_x * math.cos(radians) - local_y * math.sin(radians)
    rotated_y = local_x * math.sin(radians) + local_y * math.cos(radians)
    return origin[0] + rotated_x, origin[1] + rotated_y


def net_color(net_name: str | None) -> str:
    if not net_name:
        return "#c8964c"
    upper = net_name.upper()
    if upper == "GND":
        return "#3d5a80"
    if "3V3" in upper or upper == "VSYS" or upper == "VBAT" or "VBUS" in upper:
        return "#e07a5f"
    if "EPD" in upper or "SPI" in upper or upper in {"SDA", "SCL"}:
        return "#81b29a"
    return "#c8964c"


def collect_geometry(pcb_path: Path):
    text = pcb_path.read_text(encoding="utf-8", errors="replace")
    tree = sexpdata.loads(text)
    if not tree or sym(tree[0]) != "kicad_pcb":
        raise SystemExit("Invalid kicad_pcb")

    net_map = build_net_map(tree)

    segments: list[tuple] = []
    vias: list[tuple] = []
    pads: list[tuple] = []
    silk_lines: list[tuple] = []
    edge_lines: list[tuple] = []
    edge_circles: list[tuple] = []
    zones: list[tuple] = []

    for segment in find_nodes(tree, "segment"):
        layer = sym(node_field(segment, "layer"))
        if layer not in {"F.Cu", "Edge.Cuts"}:
            continue
        xy0 = parse_point_node(segment, "start")
        xy1 = parse_point_node(segment, "end")
        width = float(node_field(segment, "width", 0.15))
        net_id = node_field(segment, "net")
        net_name = net_map.get(str(net_id)) if net_id is not None else None
        if xy0 and xy1:
            if layer == "Edge.Cuts":
                edge_lines.append((xy0, xy1, width))
            elif layer == "F.Cu":
                segments.append((xy0, xy1, width, net_color(net_name)))

    for via in find_nodes(tree, "via"):
        at = node_field(via, "at")
        size = float(node_field(via, "size", 0.6))
        if isinstance(at, list):
            center = parse_xy(at) or (float(at[1]), float(at[2]))
            vias.append((center, size * 0.5))

    for zone in find_nodes(tree, "zone"):
        layer = sym(node_field(zone, "layer"))
        if layer != "F.Cu":
            continue
        net_name = node_field(zone, "net_name")
        if isinstance(net_name, sexpdata.Symbol):
            net_name = net_name.value()
        if not net_name:
            net_id = node_field(zone, "net")
            net_name = net_map.get(str(net_id))
        for poly in find_nodes(zone, "polygon"):
            for xy in find_nodes(poly, "xy"):
                pass
            points: list[tuple[float, float]] = []
            for xy in find_nodes(poly, "xy"):
                parsed = parse_xy(xy)
                if parsed:
                    points.append(parsed)
            if len(points) >= 3:
                zones.append((points, net_color(str(net_name) if net_name else None)))

    for footprint in find_nodes(tree, "footprint"):
        ref = ""
        for prop in find_nodes(footprint, "property"):
            if len(prop) >= 3 and prop[1] == "Reference":
                ref = str(prop[2])
        at_fp = node_field(footprint, "at")
        fp_angle = 0.0
        fp_xy = (0.0, 0.0)
        if isinstance(at_fp, list):
            fp_xy = parse_xy(at_fp) or (float(at_fp[1]), float(at_fp[2]))
            if len(at_fp) >= 4:
                fp_angle = float(at_fp[3])

        for pad in find_nodes(footprint, "pad"):
            at = node_field(pad, "at")
            size = node_field(pad, "size")
            shape = sym(node_field(pad, "shape", "rect"))
            if not isinstance(at, list) or not isinstance(size, list):
                continue
            local_xy = parse_xy(at) or (float(at[1]), float(at[2]))
            pad_xy = transform_local(local_xy[0], local_xy[1], fp_xy, fp_angle)
            pad_w = float(size[1])
            pad_h = float(size[2]) if len(size) > 2 else pad_w
            net_id = node_field(pad, "net")
            net_name = net_map.get(str(net_id)) if net_id is not None else None
            pads.append((pad_xy, pad_w, pad_h, shape, net_color(net_name), ref))

        for gr in find_nodes(footprint, "fp_line"):
            layer = sym(node_field(gr, "layer", ""))
            if layer != "F.SilkS":
                continue
            start = parse_point_node(gr, "start")
            end = parse_point_node(gr, "end")
            if start and end:
                silk_lines.append(
                    (
                        transform_local(start[0], start[1], fp_xy, fp_angle),
                        transform_local(end[0], end[1], fp_xy, fp_angle),
                        0.12,
                    )
                )

    for gr in find_nodes(tree, "gr_line"):
        layer = sym(node_field(gr, "layer"))
        if layer != "Edge.Cuts":
            continue
        start = parse_point_node(gr, "start")
        end = parse_point_node(gr, "end")
        if start and end:
            edge_lines.append((start, end, 0.15))

    for gr in find_nodes(tree, "gr_circle"):
        layer = sym(node_field(gr, "layer"))
        if layer != "Edge.Cuts":
            continue
        center = parse_point_node(gr, "center")
        end = parse_point_node(gr, "end")
        if center and end:
            radius = ((end[0] - center[0]) ** 2 + (end[1] - center[1]) ** 2) ** 0.5
            edge_circles.append((center, radius))

    return segments, vias, pads, silk_lines, edge_lines, edge_circles, zones


def render(pcb_path: Path, output_path: Path, dpi: int = 200) -> None:
    segments, vias, pads, silk_lines, edge_lines, edge_circles, zones = collect_geometry(pcb_path)

    fig, ax = plt.subplots(figsize=(8, 8), dpi=dpi)
    ax.set_facecolor("#0b3d2e")
    fig.patch.set_facecolor("#1a1a1a")

    for points, color in zones:
        ax.add_patch(
            MplPolygon(
                points,
                closed=True,
                facecolor=color,
                edgecolor="none",
                alpha=0.35,
                zorder=1,
            )
        )

    if segments:
        lc = LineCollection(
            [[a, b] for a, b, _, _ in segments],
            linewidths=[max(w * 6, 0.4) for _, _, w, _ in segments],
            colors=[c for _, _, _, c in segments],
            capstyle="round",
            zorder=3,
        )
        ax.add_collection(lc)

    for (center, radius) in vias:
        ax.add_patch(Circle(center, radius, facecolor="#b8c0cc", edgecolor="#666", linewidth=0.2, zorder=4))

    for center, width, height, shape, color, _ref in pads:
        if shape == "circle":
            ax.add_patch(
                Circle(center, min(width, height) * 0.5, facecolor="#d4af37", edgecolor="#333", linewidth=0.15, zorder=5)
            )
        else:
            half_w, half_h = width * 0.5, height * 0.5
            rect = [
                (center[0] - half_w, center[1] - half_h),
                (center[0] + half_w, center[1] - half_h),
                (center[0] + half_w, center[1] + half_h),
                (center[0] - half_w, center[1] + half_h),
            ]
            ax.add_patch(MplPolygon(rect, closed=True, facecolor="#d4af37", edgecolor="#333", linewidth=0.15, zorder=5))

    if silk_lines:
        slc = LineCollection(
            [[a, b] for a, b, _ in silk_lines],
            linewidths=[0.35] * len(silk_lines),
            colors=["#f5f5f5"] * len(silk_lines),
            zorder=6,
        )
        ax.add_collection(slc)

    if edge_lines:
        elc = LineCollection(
            [[a, b] for a, b, _ in edge_lines],
            linewidths=[1.2] * len(edge_lines),
            colors=["#f0e68c"] * len(edge_lines),
            zorder=7,
        )
        ax.add_collection(elc)

    for center, radius in edge_circles:
        ax.add_patch(
            Circle(
                center,
                radius,
                fill=False,
                edgecolor="#f0e68c",
                linewidth=1.4,
                zorder=8,
            )
        )

    all_x: list[float] = []
    all_y: list[float] = []
    for a, b, *_ in segments + [(p[0], p[1], 0, "") for p in pads]:
        all_x.extend([a[0], b[0] if isinstance(b, tuple) else a[0]])
        all_y.extend([a[1], b[1] if isinstance(b, tuple) else a[1]])
    for points, _ in zones:
        all_x.extend(p[0] for p in points)
        all_y.extend(p[1] for p in points)

    if all_x and all_y:
        margin = 3
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(max(all_y) + margin, min(all_y) - margin)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("e-ink-watch.kicad_pcb — F.Cu (текущее состояние)", color="white", fontsize=11, pad=12)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pcb", type=Path, nargs="?", default=Path("e-ink-watch.kicad_pcb"))
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=220)
    args = parser.parse_args()
    render(args.pcb.resolve(), args.output.resolve(), dpi=args.dpi)


if __name__ == "__main__":
    main()
