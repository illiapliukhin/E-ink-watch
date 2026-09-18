#!/usr/bin/env python3
"""Pass-O SAFE topology driver: C_LDO shift, J_STRAP_R MP ease, dogbones, ISET, C_VINLS."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
SNAP = ROOT / "backups/_passo_snap.kicad_pcb"
BASE = ROOT / "backups/_passo_base.kicad_pcb"
PHASES = ROOT / "tools" / "_pass_o_phases"

POWER = [
    ("GND", "VBUS"), ("GND", "VBAT"), ("GND", "VBUS_POGO"),
    ("3V3", "GND"), ("3V3_DISP", "GND"), ("GND", "SW"),
    ("3V3", "3V3_DISP"), ("GND", "VSYS"),
]

def tomm(u): return u / 1e6

def fill():
    subprocess.run([sys.executable, "-c",
        'import pcbnew;b=pcbnew.LoadBoard("e-ink-watch.kicad_pcb");'
        'pcbnew.ZONE_FILLER(b).Fill(b.Zones());'
        'pcbnew.SaveBoard("e-ink-watch.kicad_pcb",b)'],
        cwd=str(ROOT), capture_output=True, check=True)

def drc(out_name="_drc_passo_inc.txt"):
    fill()
    out = ROOT / "reports" / out_name
    subprocess.check_call(["kicad-cli", "pcb", "drc", "--format", "report", "--output", str(out), str(PCB)],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text = out.read_text()
    short = text.count("[shorting_items]")
    drc_n = int(re.search(r"Found (\d+)", text).group(1))
    pairs = Counter()
    for b in re.split(r"\[shorting_items\]:", text)[1:]:
        m = re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
        if m: pairs[tuple(sorted(m.groups()))] += 1
    power = {f"{a}|{b}": pairs.get(tuple(sorted([a, b])), 0) for a, b in POWER}
    return drc_n, short, power, pairs

def fp_info():
    import pcbnew
    board = pcbnew.LoadBoard(str(PCB))
    fps = {}; a3 = cpmid = cldo = None; mp = None
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r in ("R_ISET", "R_ILIM", "C_PMID", "R_IPRETERM", "C_VINLS", "U2", "C_SYS", "C_LDO"):
            p = fp.GetPosition(); fps[r] = (round(tomm(p.x), 3), round(tomm(p.y), 3))
        if r == "U2":
            for pad in fp.Pads():
                if pad.GetNumber() == "A3":
                    a3 = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
        if r == "C_PMID":
            for pad in fp.Pads():
                if pad.GetNumber() == "1":
                    cpmid = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
        if r == "C_LDO":
            for pad in fp.Pads():
                if pad.GetNumber() == "2":
                    cldo = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
        if r == "J_STRAP_R":
            for pad in fp.Pads():
                if pad.GetNumber() == "MP" and abs(tomm(pad.GetPosition().y)-104.65)<0.15:
                    s = pad.GetSize()
                    mp = (round(tomm(pad.GetPosition().x),3), round(tomm(pad.GetPosition().y),3),
                          round(tomm(s.x),3), round(tomm(s.y),3))
    dist = ((cpmid[0]-a3[0])**2+(cpmid[1]-a3[1])**2)**0.5 if a3 and cpmid else None
    return fps, dist, cldo, mp

def copper_nets():
    import pcbnew
    board = pcbnew.LoadBoard(str(PCB))
    out = {}
    for net in ("ILIM", "PMID", "IPRETERM", "ISET"):
        out[net] = sum(1 for t in board.GetTracks() if t.GetNetname() == net)
    return out

def try_phase(name, script_path, max_short):
    shutil.copy2(PCB, SNAP)
    r = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT), capture_output=True, text=True)
    print(f"--- {name} --- {(r.stdout or '').strip()[:300]}")
    if r.returncode != 0:
        print("FAIL", r.returncode, (r.stderr or "")[-400:])
        shutil.copy2(SNAP, PCB); return False, None, None
    drc_n, short, power, pairs = drc(f"_drc_passo_{name}.txt")
    power_ok = all(v == 0 for v in power.values())
    print(f"  short={short} power_ok={power_ok} top={pairs.most_common(10)}")
    if not (power_ok and short <= max_short):
        shutil.copy2(SNAP, PCB); print("  REVERT"); return False, short, pairs
    print("  KEEP"); return True, short, pairs

def main():
    # Resume from live disk (Pass-N s12); do not restore if already advanced
    if not BASE.exists():
        shutil.copy2(PCB, BASE)
    drc_n0, short0, power0, pairs0 = drc("_drc_passo_base2.txt")
    fps0, dist0, cldo0, mp0 = fp_info()
    cu0 = copper_nets()
    print("BASE", short0, "drc", drc_n0, "distA3", round(dist0,3) if dist0 else None, "C_LDO", fps0.get("C_LDO"), "MP", mp0)
    print("top0", pairs0.most_common(12))
    print("copper0", cu0)
    assert all(v == 0 for v in power0.values()), f"power already broken: {power0}"
    assert short0 <= 12, f"unexpected short baseline {short0}"
    kept, blocked = [], []
    cur = short0

    # Allow +2 temporary during placement if power stays 0; prefer not to rise for keep
    ok, short, _ = try_phase("01_cldo", PHASES / "01_cldo.py", cur + 2)
    if ok:
        kept.append(f"C_LDO north clear short {cur}->{short}"); cur = short
    else:
        blocked.append("C_LDO shift")

    ok, short, _ = try_phase("02_jstrap_mp", PHASES / "02_jstrap_mp.py", cur + 2)
    if ok:
        kept.append(f"J_STRAP_R MP ease short {cur}->{short}"); cur = short
    else:
        blocked.append("J_STRAP_R MP ease (mechanical or DRC)")

    ok, short, _ = try_phase("03_dogbones", PHASES / "03_dogbones.py", cur + 3)
    if ok:
        kept.append(f"ILIM/PMID/IPRETERM dogbones short {cur}->{short}"); cur = short
    else:
        blocked.append("dogbones fanout")

    ok, short, _ = try_phase("04_iset", PHASES / "04_iset.py", cur)
    if ok:
        kept.append(f"ISET B west short {cur}->{short}"); cur = short
    else:
        blocked.append("ISET B.Cu west of 109.2")

    ok, short, _ = try_phase("05_cvinls", PHASES / "05_cvinls.py", cur)
    if ok:
        kept.append(f"C_VINLS PMID stitch short {cur}->{short}"); cur = short
    else:
        blocked.append("C_VINLS→PMID stitch")

    drc_n, short, power, pairs = drc("_drc_passo_final.txt")
    fps, dist, cldo, mp = fp_info()
    cu = copper_nets()
    import pcbnew
    board = pcbnew.LoadBoard(str(PCB))
    # VBUS x check
    vbus_x = []
    for t in board.GetTracks():
        if t.GetNetname()=="VBUS" and t.Type()!=pcbnew.PCB_VIA_T and t.GetLayerName()=="F.Cu":
            sx,ex = tomm(t.GetStart().x), tomm(t.GetEnd().x)
            if abs(sx-ex)<0.05 and 104.0 < tomm(t.GetStart().y) < 106.0:
                vbus_x.append(round(sx,2))
    result = {
        "before": short0, "after": short, "drc_before": drc_n0, "drc_after": drc_n,
        "power": power, "fps": fps, "C_PMID_dist_A3_mm": round(dist,3) if dist else None,
        "C_LDO_pad2": cldo, "J_STRAP_R_MP": mp,
        "copper": cu, "copper0": cu0,
        "top": [f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(14)],
        "top0": [f"{a}|{b}:{c}" for (a,b),c in pairs0.most_common(14)],
        "kept": kept, "blocked": blocked, "I_peak_A": 0.5,
        "widths_mm": {"VBUS": 0.40, "PMID": "0.40", "VSYS": 0.45, "ILIM": 0.15, "Signal": 0.15},
        "layers": board.GetCopperLayerCount(), "VBUS_spine_x": vbus_x,
        "U2_rot": 0, "seal_vias_note": "unchanged",
    }
    if short > short0 or not all(v==0 for v in power.values()):
        print("WORSE than base — restore")
        shutil.copy2(BASE, PCB)
        result["after"] = short0
        result["restored_base"] = True
        result["attempt_short"] = short
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch = ROOT / "e-ink-watch-backups" / f"passo_topo_{ts}_s{short}.kicad_pcb"
        shutil.copy2(PCB, arch)
        shutil.copy2(PCB, ROOT / "e-ink-watch-backups" / f"passo_topo_20260918_s{short}.kicad_pcb")
        shutil.copy2(PCB, ROOT / "backups" / f"passo_topo_{ts}_s{short}.kicad_pcb")
        result["archive"] = str(arch)
        print("ARCHIVE", arch)
    (ROOT/"reports"/"_shorts_passo_topo.json").write_text(json.dumps(result, indent=2))
    print("FINAL", json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
