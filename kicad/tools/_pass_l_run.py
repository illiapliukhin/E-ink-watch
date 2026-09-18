#!/usr/bin/env python3
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
PHASES = sorted((ROOT/"tools/_pass_l_phases").glob("*.py"))
BASE = int(sys.argv[1]) if len(sys.argv)>1 else 21
TAG = sys.argv[2] if len(sys.argv)>2 else "v1"

def zone_refill():
    r=subprocess.run([sys.executable,"-c",'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("filled")
'''], cwd=str(ROOT), capture_output=True, text=True)
    return r.returncode==0, r.stdout.strip(), (r.stderr or "")[-400:]

def drc():
    out = ROOT/"reports/_drc_inc.txt"
    subprocess.check_call(["kicad-cli","pcb","drc","--format","report","--output",str(out),str(PCB)],
                          cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text=out.read_text()
    drc_n=int(re.search(r"Found (\d+)", text).group(1))
    short=text.count("[shorting_items]")
    pairs=Counter()
    for b in re.split(r"\[shorting_items\]:", text)[1:]:
        m=re.search(r"nets ([^\s]+) and ([^\s\)]+)", b.split("\n[")[0])
        if m: pairs[tuple(sorted(m.groups()))]+=1
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),
           ("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f"{a}|{b}": pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    latent = pairs.get(("GND","VSYS"),0)>0
    import pcbnew
    board=pcbnew.LoadBoard(str(PCB))
    def tomm(v): return v/1e6
    via_old=via_new=False
    fps={}
    for t in board.GetTracks():
        if t.GetClass()!="PCB_VIA" or t.GetNetname()!="GND": continue
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.31)<0.02 and abs(y-102.9)<0.02: via_old=True
        if abs(x-112.20)<0.05 and abs(y-102.20)<0.05: via_new=True
    for fp in board.GetFootprints():
        if fp.GetReference() in ("C_PMID","R_IPRETERM","U2","R_ILIM","R_ISET"):
            fps[fp.GetReference()]=(round(tomm(fp.GetPosition().x),3), round(tomm(fp.GetPosition().y),3))
    return drc_n, short, power, pairs, latent, via_old, via_new, fps, board.GetCopperLayerCount()

def main():
    snap=ROOT/f"backups/_try_passl_{TAG}.kicad_pcb"
    shutil.copy2(PCB, snap)
    for ph in PHASES:
        r=subprocess.run([sys.executable,str(ph)], cwd=str(ROOT), capture_output=True, text=True)
        print(f"[{ph.name}]", r.stdout.strip())
        if r.returncode!=0:
            print("FAIL", r.stderr[-500:])
            shutil.copy2(snap, PCB); sys.exit(2)
    ok, fo, fe = zone_refill()
    print("fill:", fo, fe[:200] if fe else "")
    drc_n, short, power, pairs, latent, via_old, via_new, fps, layers = drc()
    power_ok = all(v==0 for v in power.values())
    keep = power_ok and (short < BASE) and (not latent) and (layers==4)
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(15)]
    result={"tag":TAG,"drc":drc_n,"shorting":short,"base":BASE,"power_ok":power_ok,
            "latent":latent,"via_old":via_old,"via_new":via_new,"fps":fps,"layers":layers,
            "keep":keep,"top":top,"power":power}
    print(json.dumps(result, indent=2))
    (ROOT/"reports"/f"drc_shorts_passl_{TAG}.txt").write_text((ROOT/"reports/_drc_inc.txt").read_text())
    (ROOT/"reports"/f"_shorts_passl_{TAG}_counts.json").write_text(json.dumps(result, indent=2))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
