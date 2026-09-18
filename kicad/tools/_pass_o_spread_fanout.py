#!/usr/bin/env python3
"""Pass-O: SPREAD PMIC pocket then BATCH HV/45° fanout (pcbnew Python).

NOT freerouter / hand micro-surgery. Revert if power pairs>0 or shorting worsens.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pcbnew

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
SNAP = ROOT / "backups/_passo_snap.kicad_pcb"
BASE = ROOT / "backups/_passo_base.kicad_pcb"
ARCHDIR = ROOT / "e-ink-watch-backups"

POWER = [
    ("GND", "VBUS"), ("GND", "VBAT"), ("GND", "VBUS_POGO"),
    ("3V3", "GND"), ("3V3_DISP", "GND"), ("GND", "SW"),
    ("3V3", "3V3_DISP"), ("GND", "VSYS"),
]

SPREAD = {
    "C_VINLS": (112.80, 105.80, 90.0),
    "C_PMID": (113.65, 106.45, -90.0),  # pad1 PMID at -Y toward A3
    "R_ILIM": (115.90, 106.50, 0.0),
    "C_LDO": (114.60, 107.95, 90.0),
    "R_IPRETERM": (115.50, 102.50, 0.0),
    "R_ISET": (108.90, 103.50, 0.0),
}
MP_TARGET = (114.70, 104.65)
MP_SIZE = (1.000, 1.400)


def mm(v: float) -> int:
    return int(round(float(v) * 1e6))


def tomm(u: int) -> float:
    return u / 1e6


def fill() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            'import pcbnew;b=pcbnew.LoadBoard("e-ink-watch.kicad_pcb");'
            "pcbnew.ZONE_FILLER(b).Fill(b.Zones());"
            'pcbnew.SaveBoard("e-ink-watch.kicad_pcb",b)',
        ],
        cwd=str(ROOT),
        capture_output=True,
        check=True,
    )


def run_drc(out_name: str):
    fill()
    out = ROOT / "reports" / out_name
    subprocess.check_call(
        ["kicad-cli", "pcb", "drc", "--format", "report", "--output", str(out), str(PCB)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    text = out.read_text()
    short = text.count("[shorting_items]")
    drc_n = int(re.search(r"Found (\d+)", text).group(1))
    pairs: Counter = Counter()
    for block in re.split(r"\[shorting_items\]:", text)[1:]:
        m = re.search(r"nets ([^\s]+) and ([^\s\)]+)", block.split("\n[")[0])
        if m:
            pairs[tuple(sorted(m.groups()))] += 1
    power = {f"{a}|{b}": pairs.get(tuple(sorted([a, b])), 0) for a, b in POWER}
    return drc_n, short, power, pairs


def add_track(board, layer, x1, y1, x2, y2, w, net):
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(layer)
    t.SetNetCode(board.GetNetInfo().GetNetItem(net).GetNetCode())
    board.Add(t)


def add_via(board, x, y, net, drill=0.25, width=0.50):
    if 90.5 <= x <= 101.5 and 108.5 <= y <= 117.0:
        raise RuntimeError(f"refusing via in pogo seal ({x},{y})")
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetDrill(mm(drill))
    try:
        v.SetWidth(mm(width))
    except Exception:
        pass
    v.SetNetCode(board.GetNetInfo().GetNetItem(net).GetNetCode())
    board.Add(v)


def path(board, layer, pts, w, net):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        add_track(board, layer, x1, y1, x2, y2, w, net)


def get_pads(board, refs):
    out = {}
    for fp in board.GetFootprints():
        if fp.GetReference() in refs:
            for p in fp.Pads():
                out[f"{fp.GetReference()}.{p.GetNumber()}"] = (
                    tomm(p.GetPosition().x),
                    tomm(p.GetPosition().y),
                )
    return out


def apply_spread(board):
    notes = []
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r in SPREAD:
            x, y, rot = SPREAD[r]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)
            notes.append(f"{r}->({x:.2f},{y:.2f})/{rot}")
        if r == "J_STRAP_R":
            for pad in fp.Pads():
                if pad.GetNumber() != "MP":
                    continue
                px, py = tomm(pad.GetPosition().x), tomm(pad.GetPosition().y)
                if abs(py - 104.65) < 0.1 and abs(px - 114.0) < 0.4:
                    pad.SetPosition(pcbnew.VECTOR2I(mm(MP_TARGET[0]), mm(MP_TARGET[1])))
                    pad.SetSize(pcbnew.VECTOR2I(mm(MP_SIZE[0]), mm(MP_SIZE[1])))
                    notes.append(f"MP->{MP_TARGET}{MP_SIZE}")
    return notes


def wipe_fanout(board):
    remove = []
    for t in list(board.GetTracks()):
        net = t.GetNetname()
        if net in ("ILIM", "IPRETERM", "ISET"):
            remove.append(t)
            continue
        if net == "PMID":
            if t.Type() == pcbnew.PCB_VIA_T:
                x, y = tomm(t.GetPosition().x), tomm(t.GetPosition().y)
                if 110.85 <= x <= 111.50 and abs(y - 104.35) < 0.12:
                    continue
                if 111.2 <= x <= 116.8 and 102.0 <= y <= 108.8:
                    remove.append(t)
                continue
            sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
            ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
            layer = t.GetLayerName()
            stitch = (
                (abs(sx - 111.0) < 0.06 and abs(ex - 111.0) < 0.06 and min(sy, ey) >= 105.15 and max(sy, ey) <= 105.65)
                or (abs(sy - 105.6) < 0.06 and abs(ey - 105.6) < 0.06 and min(sx, ex) >= 110.95 and max(sx, ex) <= 111.45)
                or (abs(sx - 111.4) < 0.06 and abs(ex - 111.4) < 0.06 and min(sy, ey) >= 105.55 and max(sy, ey) <= 106.05)
                or (abs(sx - 111.0) < 0.06 and abs(ex - 111.0) < 0.06 and min(sy, ey) >= 104.30 and max(sy, ey) <= 105.25)
            )
            if stitch and layer == "F.Cu":
                continue
            if layer in ("F.Cu", "B.Cu"):
                if min(sx, ex) >= 111.25 and max(sx, ex) <= 116.8 and min(sy, ey) >= 102.4 and max(sy, ey) <= 108.5:
                    remove.append(t)
                elif abs(sy - 103.85) < 0.12 and abs(ey - 103.85) < 0.12:
                    remove.append(t)
            continue
        if net == "3V3_DISP" and t.Type() != pcbnew.PCB_VIA_T and t.GetLayerName() == "F.Cu":
            sx, sy = tomm(t.GetStart().x), tomm(t.GetStart().y)
            ex, ey = tomm(t.GetEnd().x), tomm(t.GetEnd().y)
            if abs(sx - 113.5) < 0.06 and abs(ex - 113.5) < 0.06 and 105.9 <= min(sy, ey) and max(sy, ey) <= 106.45:
                remove.append(t)
            elif abs(sy - 106.0) < 0.06 and abs(ey - 106.0) < 0.06 and abs(max(sx, ex) - 113.5) < 0.06 and min(sx, ex) >= 111.7:
                remove.append(t)
            elif abs(sx - 113.0) < 0.06 and abs(ex - 113.0) < 0.06 and 105.9 <= min(sy, ey) and max(sy, ey) <= 106.45:
                remove.append(t)
    for t in remove:
        board.Remove(t)
    return len(remove)


def rebuild_fanout(board):
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    p = get_pads(board, {"U2", "C_PMID", "R_ILIM", "R_IPRETERM", "R_ISET", "C_VINLS", "C_LDO"})
    notes = []

    cpmid = p["C_PMID.1"]
    cvin = p["C_VINLS.1"]
    a3 = p["U2.A3"]

    add_track(board, F, a3[0], a3[1], a3[0], 104.35, 0.40, "PMID")
    add_via(board, 111.00, 104.35, "PMID", 0.30, 0.55)
    vx, vy = cpmid[0], 105.70
    add_via(board, vx, vy, "PMID", 0.30, 0.55)
    path(board, B, [(111.00, 104.35), (vx, 104.35), (vx, vy)], 0.40, "PMID")
    add_track(board, F, vx, vy, cpmid[0], cpmid[1], 0.40, "PMID")
    add_via(board, cvin[0], cvin[1], "PMID", 0.30, 0.55)
    path(board, B, [(cvin[0], cvin[1]), (cvin[0], vy), (vx, vy)], 0.40, "PMID")
    notes.append("PMID highway+C_VINLS")

    c2 = p["U2.C2"]
    rilim = p["R_ILIM.1"]
    add_via(board, 110.75, 106.00, "ILIM", 0.25, 0.50)
    add_track(board, F, c2[0], c2[1], 110.75, 106.00, 0.15, "ILIM")
    vri = (rilim[0] - 0.40, rilim[1])
    add_via(board, vri[0], vri[1], "ILIM", 0.25, 0.50)
    path(
        board,
        B,
        [(110.75, 106.00), (110.30, 106.00), (110.30, 107.25), (vri[0], 107.25), (vri[0], vri[1])],
        0.15,
        "ILIM",
    )
    add_track(board, F, vri[0], vri[1], rilim[0], rilim[1], 0.15, "ILIM")
    notes.append("ILIM SE dogbone")

    d1 = p["U2.D1"]
    ript = p["R_IPRETERM.1"]
    add_via(board, 109.70, 106.40, "IPRETERM", 0.25, 0.50)
    add_track(board, F, d1[0], d1[1], 109.70, 106.40, 0.15, "IPRETERM")
    add_via(board, ript[0], ript[1], "IPRETERM", 0.25, 0.50)
    path(board, B, [(109.70, 106.40), (109.70, ript[1]), (ript[0], ript[1])], 0.18, "IPRETERM")
    notes.append("IPRETERM B spine")

    c1 = p["U2.C1"]
    riset = p["R_ISET.2"]
    add_via(board, 109.85, 106.00, "ISET", 0.25, 0.50)
    add_track(board, F, c1[0], c1[1], 109.85, 106.00, 0.15, "ISET")
    add_via(board, riset[0], riset[1], "ISET", 0.25, 0.50)
    path(
        board,
        B,
        [(109.85, 106.00), (108.60, 106.00), (108.60, riset[1]), (riset[0], riset[1])],
        0.15,
        "ISET",
    )
    notes.append("ISET B@108.60")

    c5 = p["U2.C5"]
    cldo = p["C_LDO.2"]
    path(board, F, [(c5[0], c5[1]), (cldo[0], 106.00), (cldo[0], cldo[1])], 0.25, "3V3_DISP")
    notes.append("C_LDO F rail")
    return notes


def fp_info(board):
    fps = {}
    a3 = cpmid = None
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r in list(SPREAD) + ["U2"]:
            pos = fp.GetPosition()
            fps[r] = (
                round(tomm(pos.x), 3),
                round(tomm(pos.y), 3),
                round(fp.GetOrientationDegrees(), 1),
            )
        if r == "U2":
            for pad in fp.Pads():
                if pad.GetNumber() == "A3":
                    a3 = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
        if r == "C_PMID":
            for pad in fp.Pads():
                if pad.GetNumber() == "1":
                    cpmid = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
    dist = None
    if a3 and cpmid:
        dist = ((cpmid[0] - a3[0]) ** 2 + (cpmid[1] - a3[1]) ** 2) ** 0.5
    return fps, dist


def main():
    ARCHDIR.mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)

    pre = ROOT / "backups" / f"pre_passo_spread_{datetime.now():%Y%m%d_%H%M%S}.kicad_pcb"
    shutil.copy2(PCB, pre)
    shutil.copy2(PCB, BASE)
    print("backup", pre)

    drc0, short0, power0, pairs0 = run_drc("_drc_passo_base.txt")
    print("BASE", short0, drc0, power0)
    print("top0", pairs0.most_common(12))
    if not all(v == 0 for v in power0.values()):
        print("ABORT: baseline power pairs != 0")
        sys.exit(2)
    if short0 != 12:
        print(f"WARN: baseline short={short0} expected 12 — continuing")

    shutil.copy2(PCB, SNAP)
    board = pcbnew.LoadBoard(str(PCB))
    assert board.GetCopperLayerCount() == 4

    spread_notes = apply_spread(board)
    print("SPREAD", spread_notes)
    nwipe = wipe_fanout(board)
    print("WIPE", nwipe)
    fan_notes = rebuild_fanout(board)
    print("FAN", fan_notes)
    pcbnew.SaveBoard(str(PCB), board)

    pads = get_pads(pcbnew.LoadBoard(str(PCB)), {"C_PMID", "U2"})
    print("C_PMID.1", pads.get("C_PMID.1"), "A3", pads.get("U2.A3"))

    drc1, short1, power1, pairs1 = run_drc("_drc_passo_spread.txt")
    fps, dist = fp_info(pcbnew.LoadBoard(str(PCB)))
    print("AFTER", short1, drc1, power1)
    print("top", pairs1.most_common(14))
    print("fps", fps, "dA3", None if dist is None else round(dist, 3))

    power_ok = all(v == 0 for v in power1.values())
    kept = power_ok and short1 <= short0

    result = {
        "method": "pcbnew_python_spread_then_batch_HV45_fanout",
        "freerouter": False,
        "before_short": short0,
        "after_short": short1 if kept else short0,
        "attempt_short": short1,
        "drc_before": drc0,
        "drc_after": drc1 if kept else drc0,
        "power_before": power0,
        "power_after": power1 if kept else power0,
        "top_before": [f"{a}|{b}:{c}" for (a, b), c in pairs0.most_common(14)],
        "top_after": [f"{a}|{b}:{c}" for (a, b), c in pairs1.most_common(14)],
        "spread": spread_notes,
        "fanout": fan_notes,
        "wipe": nwipe,
        "fps": {k: list(v) for k, v in fps.items()},
        "C_PMID_dist_A3_mm": None if dist is None else round(dist, 3),
        "kept": kept,
        "VBUS_x": 110.6,
        "layers": 4,
    }

    if not kept:
        print("REVERT to baseline (power or shorting guard)")
        shutil.copy2(BASE, PCB)
        result["reverted"] = True
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch = ARCHDIR / f"passo_spread_{ts}_s{short1}.kicad_pcb"
        shutil.copy2(PCB, arch)
        shutil.copy2(PCB, ARCHDIR / f"passo_spread_20260918_s{short1}.kicad_pcb")
        result["archive"] = str(arch)
        print("KEEP", arch)

    (ROOT / "reports" / "_shorts_passo_spread.json").write_text(json.dumps(result, indent=2))
    (ROOT / "reports" / "CALC_PASSO_SPREAD.txt").write_text(
        f"""# Pass-O SPREAD + batch fanout
Method: pcbnew Python (tools/_pass_o_spread_fanout.py) — NOT freerouter, NOT hand micro-surgery
I_peak 0.5A | Power>=0.40 | Signal 0.15 | HV paths | VBUS @x=110.6 w=0.40
MP ease: J_STRAP_R (114.0,104.65)1.2x2.0 -> (114.70,104.65)1.0x1.4 (match L inner)
Spread: C_PMID (113.65,106.45)r-90 dA3={result.get('C_PMID_dist_A3_mm')}
        R_ILIM (115.90,106.50) C_LDO (114.60,107.95)
        R_IPRETERM (115.50,102.50) R_ISET (108.90,103.50) C_VINLS kept
shorting {short0} -> attempt {short1} kept={kept} final={result['after_short']}
power pairs remain 0: {power_ok if kept else 'reverted'}
"""
    )
    print(json.dumps({k: result[k] for k in ("method", "before_short", "attempt_short", "after_short", "kept", "C_PMID_dist_A3_mm")}, indent=2))


if __name__ == "__main__":
    main()
