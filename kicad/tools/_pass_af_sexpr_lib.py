"""Sexpr helpers for Pass-AF — insert copper next to PMID via to avoid SaveBoard flake."""
from pathlib import Path
import re
import uuid

BOARD = Path("e-ink-watch.kicad_pcb")
PMID_ANCHOR = "\t(via\n\t\t(at 111.35 103.85)"


def load():
    return BOARD.read_text()


def save(text):
    BOARD.write_text(text)


def fpat(value):
    if isinstance(value, (int, float)) and abs(float(value) - round(float(value))) < 1e-9:
        return rf"{int(round(float(value)))}(?:\.0+)?"
    text = str(value)
    if re.match(r"^-?\d+\.\d+$", text):
        return re.escape(text) + r"0*"
    return re.escape(text)


def del_segments_at(text, x1, y1, x2, y2, layer=None):
    removed = 0
    for start_x, start_y, end_x, end_y in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        pattern = (
            rf"\t\(segment\n"
            rf"\t\t\(start {fpat(start_x)} {fpat(start_y)}\)\n"
            rf"\t\t\(end {fpat(end_x)} {fpat(end_y)}\)\n"
            rf"\t\t\(width ([^\)]+)\)\n"
            rf"\t\t\(layer \"([^\"]+)\"\)\n"
            rf"\t\t\(net (\d+)\)\n"
            rf"\t\t\(uuid \"[^\"]+\"\)\n"
            rf"\t\)\n"
        )

        def replacer(match):
            nonlocal removed
            if layer and match.group(2) != layer:
                return match.group(0)
            removed += 1
            return ""

        text = re.sub(pattern, replacer, text)
    return text, removed


def add_segment(text, x1, y1, x2, y2, width, layer, net):
    segment = (
        f"\t(segment\n"
        f"\t\t(start {x1} {y1})\n"
        f"\t\t(end {x2} {y2})\n"
        f"\t\t(width {width})\n"
        f"\t\t(layer \"{layer}\")\n"
        f"\t\t(net {net})\n"
        f"\t\t(uuid \"{uuid.uuid4()}\")\n"
        f"\t)\n"
    )
    index = text.find(PMID_ANCHOR)
    if index < 0:
        raise SystemExit("PMID via anchor missing")
    return text[:index] + segment + text[index:]


def add_via(text, x, y, size, drill, net, layers='"F.Cu" "B.Cu"'):
    via = (
        f"\t(via\n"
        f"\t\t(at {x} {y})\n"
        f"\t\t(size {size})\n"
        f"\t\t(drill {drill})\n"
        f"\t\t(layers {layers})\n"
        f"\t\t(net {net})\n"
        f"\t\t(uuid \"{uuid.uuid4()}\")\n"
        f"\t)\n"
    )
    index = text.find(PMID_ANCHOR)
    if index < 0:
        raise SystemExit("PMID via anchor missing")
    return text[:index] + via + text[index:]


def del_via(text, x, y, net=None):
    removed = [0]
    pattern = (
        rf"\t\(via\n"
        rf"\t\t\(at {fpat(x)} {fpat(y)}\)\n"
        rf"\t\t\(size [^\n]+\)\n"
        rf"\t\t\(drill [^\n]+\)\n"
        rf"\t\t\(layers [^\n]+\)\n"
        rf"\t\t\(net (\d+)\)\n"
        rf"\t\t\(uuid \"[^\"]+\"\)\n"
        rf"\t\)\n"
    )

    def replacer(match):
        if net is not None and int(match.group(1)) != int(net):
            return match.group(0)
        removed[0] += 1
        return ""

    return re.sub(pattern, replacer, text, count=1), removed[0]


def netnum(text, name):
    match = re.search(rf'\(net (\d+) "{re.escape(name)}"\)', text)
    if not match:
        raise SystemExit(f"net {name} missing")
    return int(match.group(1))
