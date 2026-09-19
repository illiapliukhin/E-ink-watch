"""Sexpr helpers for Pass-W — avoid pcbnew SaveBoard DRC order flake."""
from pathlib import Path
import re, uuid

BOARD = Path("e-ink-watch.kicad_pcb")

def load():
    return BOARD.read_text()

def save(t):
    BOARD.write_text(t)

def fpat(v):
    if isinstance(v, (int, float)) and abs(float(v) - round(float(v))) < 1e-9:
        return rf"{int(round(float(v)))}(?:\.0+)?"
    s = str(v)
    if re.match(r'^-?\d+\.\d+$', s):
        return re.escape(s) + r"0*"
    return re.escape(s)

def del_segments_at(t, x1, y1, x2, y2, layer=None):
    n = 0
    for (a, b, c, d) in [(x1, y1, x2, y2), (x2, y2, x1, y1)]:
        pat = (
            rf'\t\(segment\n'
            rf'\t\t\(start {fpat(a)} {fpat(b)}\)\n'
            rf'\t\t\(end {fpat(c)} {fpat(d)}\)\n'
            rf'\t\t\(width ([^\)]+)\)\n'
            rf'\t\t\(layer "([^"]+)"\)\n'
            rf'\t\t\(net (\d+)\)\n'
            rf'\t\t\(uuid "[^"]+"\)\n'
            rf'\t\)\n'
        )
        def repl(m):
            nonlocal n
            if layer and m.group(2) != layer:
                return m.group(0)
            n += 1
            return ''
        t = re.sub(pat, repl, t)
    return t, n

def add_segment(t, x1, y1, x2, y2, width, layer, net):
    seg = (
        f'\t(segment\n'
        f'\t\t(start {x1} {y1})\n'
        f'\t\t(end {x2} {y2})\n'
        f'\t\t(width {width})\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t)\n'
    )
    needle = '\t(via\n\t\t(at 111.35 103.85)'
    idx = t.find(needle)
    if idx < 0:
        raise SystemExit('PMID via anchor missing')
    return t[:idx] + seg + t[idx:]

def add_via(t, x, y, size, drill, net, layers='"F.Cu" "B.Cu"'):
    via = (
        f'\t(via\n'
        f'\t\t(at {x} {y})\n'
        f'\t\t(size {size})\n'
        f'\t\t(drill {drill})\n'
        f'\t\t(layers {layers})\n'
        f'\t\t(net {net})\n'
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t)\n'
    )
    needle = '\t(via\n\t\t(at 111.35 103.85)'
    idx = t.find(needle)
    if idx < 0:
        raise SystemExit('PMID via anchor missing')
    return t[:idx] + via + t[idx:]

def move_fp(t, ref, x, y):
    """Rewrite (at ...) for footprint with Reference property ref."""
    # Find property Reference line, then search backwards for (at
    prop = f'(property "Reference" "{ref}"'
    pidx = t.find(prop)
    if pidx < 0:
        raise SystemExit(f'Reference {ref} not found')
    # footprint blocks can be large; search back up to 8k
    window = t[max(0, pidx - 8000):pidx]
    matches = list(re.finditer(r'\(at ([^)]+)\)', window))
    if not matches:
        raise SystemExit(f'no (at) before {ref}')
    m = matches[-1]  # last (at) before property — usually the footprint at
    abs_start = max(0, pidx - 8000) + m.start(1)
    abs_end = max(0, pidx - 8000) + m.end(1)
    old = m.group(1).strip().split()
    rot = ' '.join(old[2:]) if len(old) > 2 else ''
    new = f'{x} {y}' + (f' {rot}' if rot else '')
    return t[:abs_start] + new + t[abs_end:]




def del_via(t, x, y, net=None):
    """Delete first via at (x,y); optional net filter. Returns (text, count)."""
    import re
    n = [0]
    pat = (
        rf'\t\(via\n'
        rf'\t\t\(at {fpat(x)} {fpat(y)}\)\n'
        rf'\t\t\(size [^\n]+\)\n'
        rf'\t\t\(drill [^\n]+\)\n'
        rf'\t\t\(layers [^\n]+\)\n'
        rf'\t\t\(net (\d+)\)\n'
        rf'\t\t\(uuid "[^"]+"\)\n'
        rf'\t\)\n'
    )
    def repl(m):
        if net is not None and int(m.group(1)) != int(net):
            return m.group(0)
        n[0] += 1
        return ''
    return re.sub(pat, repl, t, count=1), n[0]

def move_via(t, x, y, nx, ny, net=None):
    """Rewrite via at coords. Returns (text, count)."""
    import re
    n = [0]
    pat = (
        rf'(\t\(via\n\t\t\(at ){fpat(x)} {fpat(y)}(\n'
        rf'\t\t\(size [^\n]+\)\n'
        rf'\t\t\(drill [^\n]+\)\n'
        rf'\t\t\(layers [^\n]+\)\n'
        rf'\t\t\(net )(\d+)(\n'
        rf'\t\t\(uuid "[^"]+"\)\n'
        rf'\t\))'
    )
    def repl(m):
        if net is not None and int(m.group(3)) != int(net):
            return m.group(0)
        n[0] += 1
        return f'{m.group(1)}{nx} {ny}{m.group(2)}{m.group(3)}{m.group(4)}'
    return re.sub(pat, repl, t, count=1), n[0]

def netnum(t, name):
    m = re.search(rf'\(net (\d+) "{re.escape(name)}"\)', t)
    if not m:
        raise SystemExit(f'net {name} missing')
    return int(m.group(1))
