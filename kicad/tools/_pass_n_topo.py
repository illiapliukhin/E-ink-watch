#!/usr/bin/env python3
"""Pass-N SAFE topology driver."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
SNAP = ROOT / "backups/_passn_snap.kicad_pcb"
BASE = ROOT / "backups/_passn_base.kicad_pcb"
PHASES = ROOT / "tools" / "_pass_n_phases"

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

def drc(out_name="_drc_passn_inc.txt"):
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
    fps = {}; a3 = cpmid = None
    for fp in board.GetFootprints():
        r = fp.GetReference()
        if r in ("R_ISET", "R_ILIM", "C_PMID", "R_IPRETERM", "C_VINLS", "U2", "C_SYS"):
            p = fp.GetPosition(); fps[r] = (round(tomm(p.x), 3), round(tomm(p.y), 3))
        if r == "U2":
            for pad in fp.Pads():
                if pad.GetNumber() == "A3":
                    a3 = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
        if r == "C_PMID":
            for pad in fp.Pads():
                if pad.GetNumber() == "1":
                    cpmid = (tomm(pad.GetPosition().x), tomm(pad.GetPosition().y))
    dist = ((cpmid[0]-a3[0])**2+(cpmid[1]-a3[1])**2)**0.5 if a3 and cpmid else None
    return fps, dist

def try_phase(name, script_path, max_short):
    shutil.copy2(PCB, SNAP)
    r = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT), capture_output=True, text=True)
    print(f"--- {name} --- {(r.stdout or '').strip()[:240]}")
    if r.returncode != 0:
        print("FAIL", r.returncode, (r.stderr or "")[-300:])
        shutil.copy2(SNAP, PCB); return False, None, None
    drc_n, short, power, pairs = drc()
    power_ok = all(v == 0 for v in power.values())
    print(f"  short={short} power_ok={power_ok} top={pairs.most_common(10)}")
    if not (power_ok and short <= max_short):
        shutil.copy2(SNAP, PCB); print("  REVERT"); return False, short, pairs
    print("  KEEP"); return True, short, pairs

def main():
    shutil.copy2(BASE, PCB)
    drc_n0, short0, power0, pairs0 = drc("_drc_passn_base.txt")
    fps0, dist0 = fp_info()
    print("BASE", short0, "drc", drc_n0, "distA3", round(dist0,3) if dist0 else None)
    print("top0", pairs0.most_common(12))
    assert all(v == 0 for v in power0.values())
    kept, blocked = [], []

    ok, short, _ = try_phase("p1_atomic", PHASES / "01_place_reb.py", short0 + 2)
    if not ok:
        blocked.append("p1 atomic")
        print("ABORT — keep base")
        result = {"before": short0, "after": short0, "failed": "p1", "blocked": blocked,
                  "top0": [f"{a}|{b}:{c}" for (a,b),c in pairs0.most_common(12)]}
        (ROOT/"reports"/"_shorts_passn_topo.json").write_text(json.dumps(result, indent=2))
        return
    kept.append("R_ILIM@(112.50,104.55) C_PMID@(114.00,105.45) R_IPRETERM@(114.20,102.80) + rebuild")

    _, cur, power, pairs = drc()
    print("POST short", cur, "top", pairs.most_common(10))

    ok, short, _ = try_phase("p4_iset", PHASES / "04_iset.py", cur)
    if ok: kept.append("ISET B @x=108.80"); cur = short
    else: blocked.append("ISET")

    ok, short, _ = try_phase("p5_cvinls", PHASES / "05_cvinls.py", cur)
    if ok: kept.append("C_VINLS stitch"); cur = short
    else: blocked.append("C_VINLS")

    # fix TS script segfault: rewrite inline
    _, _, _, pairs = drc()
    if pairs.get(("ILIM","TS"),0) > 0:
        ok, short, _ = try_phase("p6_ts", PHASES / "06_ts.py", cur)
        if ok: kept.append("TS ortho"); cur = short
        else: blocked.append("ILIM-TS")
    else:
        kept.append("ILIM-TS clear")

    _, _, _, pairs = drc()
    if pairs.get(("3V3_DISP","VSYS"),0) > 0:
        ok, short, _ = try_phase("p7_disp", PHASES / "07_disp.py", cur)
        if ok: kept.append("trim 3V3_DISP"); cur = short
        else: blocked.append("3V3_DISP-VSYS")
    else:
        kept.append("3V3_DISP-VSYS clear")

    drc_n, short, power, pairs = drc("_drc_passn_final.txt")
    fps, dist = fp_info()
    import pcbnew
    board = pcbnew.LoadBoard(str(PCB))
    result = {
        "before": short0, "after": short, "drc_before": drc_n0, "drc_after": drc_n,
        "power": power, "fps": fps, "C_PMID_dist_A3_mm": round(dist,3) if dist else None,
        "top": [f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(14)],
        "kept": kept, "blocked": blocked, "I_peak_A": 0.5,
        "widths_mm": {"VBUS": 0.40, "PMID": "0.40", "VSYS": 0.45, "ILIM": 0.15},
        "layers": board.GetCopperLayerCount(), "VBUS_x": 110.6,
        "south_dy_mm": {"R_ILIM": 1.05, "C_PMID": 1.60},
    }
    if short > short0 or not all(v==0 for v in power.values()):
        print("WORSE than base — restore s14")
        shutil.copy2(BASE, PCB)
        result["after"] = short0
        result["restored_base"] = True
        result["attempt_short"] = short
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch = ROOT / "e-ink-watch-backups" / f"passn_topo_{ts}_s{short}.kicad_pcb"
        shutil.copy2(PCB, arch)
        shutil.copy2(PCB, ROOT / "e-ink-watch-backups" / f"passn_topo_20260918_s{short}.kicad_pcb")
        result["archive"] = str(arch)
        print("ARCHIVE", arch)
    (ROOT/"reports"/"_shorts_passn_topo.json").write_text(json.dumps(result, indent=2))
    print("FINAL", json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
