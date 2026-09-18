#!/usr/bin/env python3
"""Pass-L atomic U2 pocket rebuild — phased save/reload to avoid pcbnew SWIG corruption."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
BASE = int(sys.argv[1]) if len(sys.argv)>1 else 21
TAG = sys.argv[2] if len(sys.argv)>2 else "pocket"

PHASES = []

PHASES.append(("via_fps", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        t.SetPosition(pcbnew.VECTOR2I(mm(112.20),mm(102.20))); n+=1
for ref,nx,ny in [("C_PMID",111.30,103.70),("R_IPRETERM",113.20,103.10)]:
    for fp in board.GetFootprints():
        if fp.GetReference()==ref:
            fp.SetPosition(pcbnew.VECTOR2I(mm(nx),mm(ny)))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("via",n,"fps_ok")
'''))

PHASES.append(("vbus_del", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBUS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-102.9)<0.05 and abs(ey-102.9)<0.05 and min(sx,ex)<=108.2 and max(sx,ex)>=110.5: hit=True
    if abs(sx-110.6)<0.05 and abs(ex-110.6)<0.05 and min(sy,ey)<=105.15 and max(sy,ey)>=102.95: hit=True
    if abs(sy-104.5)<0.05 and abs(ey-104.5)<0.05 and min(sx,ex)<=105.8 and max(sx,ex)>=108.0 and tomm(t.GetWidth())>=0.30: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vbus_del",n)
'''))

PHASES.append(("vbus_reb", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBUS").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (105.700,104.500, 105.700,103.700, 0.35),
    (105.700,103.700, 108.120,103.700, 0.35),
    (108.120,103.700, 108.120,102.900, 0.35),
    (108.120,102.900, 109.850,102.900, 0.35),
    (109.850,102.900, 109.850,105.200, 0.35),
    (109.850,105.200, 110.600,105.200, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vbus_reb")
'''))

PHASES.append(("fanout_del", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    net=t.GetNetname()
    if net not in ("PMID","IPRETERM","ILIM","ISET"): continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if (107<=sx<=115 and 102.5<=sy<=107.5) or (107<=ex<=115 and 102.5<=ey<=107.5):
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("fanout_del",n)
'''))

PHASES.append(("fanout_reb", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
def add(net, segs):
    nc=board.GetNetInfo().GetNetItem(net).GetNetCode()
    for x1,y1,x2,y2,w in segs:
        t=pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
add("PMID", [
    (111.000,105.200, 111.000,105.600, 0.20),
    (111.000,105.600, 111.400,105.600, 0.20),
    (111.400,105.600, 111.400,106.000, 0.20),
    (111.400,106.000, 111.400,106.220, 0.18),
    (111.400,106.220, 112.800,106.220, 0.18),
    (112.800,106.220, 112.800,106.280, 0.20),
    (111.000,105.200, 111.000,103.700, 0.25),
    (111.000,103.700, 110.820,103.700, 0.25),
])
add("IPRETERM", [
    (110.200,106.400, 110.200,106.550, 0.18),
    (110.200,106.550, 112.690,106.550, 0.18),
    (112.690,106.550, 112.690,103.100, 0.18),
])
add("ILIM", [
    (110.600,106.000, 110.290,106.000, 0.18),
    (110.290,106.000, 110.290,103.500, 0.18),
])
add("ISET", [
    (110.200,106.000, 110.310,106.000, 0.18),
    (110.310,106.000, 110.310,103.500, 0.18),
])
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("fanout_reb")
'''))

PHASES.append(("vsys_stub_del", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05 and min(sx,ex)<=111.45 and max(sx,ex)>=111.75: hit=True
    if abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=105.95: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vsys_stub_del",n)
'''))

PHASES.append(("sw_fix", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="SW" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-104.5)<0.05 and abs(ey-104.5)<0.05 and max(sx,ex)>=115.0:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
nc=board.GetNetInfo().GetNetItem("SW").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (111.400,104.500, 111.400,105.050, 0.30),
    (111.400,105.050, 113.600,105.050, 0.30),
    (113.600,105.050, 113.600,104.500, 0.30),
    (113.600,104.500, 115.287,104.500, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("sw",n)
'''))

PHASES.append(("disp_fix", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3_DISP": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-115.55)<0.05 and abs(y-102.75)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-115.55)<0.05 and abs(ex-115.55)<0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(115.55),mm(106.00)))
        t.SetEnd(pcbnew.VECTOR2I(mm(115.55),mm(101.80))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3_DISP" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-106.32)<0.05 and abs(ey-106.32)<0.05 and min(sx,ex)<=112.85 and max(sx,ex)>=112.95: hit=True
    if abs(sx-113.0)<0.05 and abs(ex-113.0)<0.05 and min(sy,ey)<=106.05 and max(sy,ey)>=106.25: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
nc=board.GetNetInfo().GetNetItem("3V3_DISP").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (113.000,106.000, 113.500,106.000, 0.30),
    (113.500,106.000, 113.500,106.320, 0.30),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("disp",n)
'''))

PHASES.append(("vsys_corr", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VSYS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)>=117.0: hit=True
    if abs(sy-102.95)<0.05 and abs(ey-102.95)<0.05 and max(sx,ex)<=112.0 and min(sx,ex)>=111.4: hit=True
    if abs(sx-117.412)<0.02 and abs(ex-117.412)<0.02 and min(sy,ey)<=103.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
nc=board.GetNetInfo().GetNetItem("VSYS").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (117.412,104.500, 117.412,103.400, 0.35),
    (117.412,103.400, 115.000,103.400, 0.35),
    (115.000,103.400, 115.000,102.400, 0.35),
    (115.000,102.400, 111.450,102.400, 0.35),
    (111.450,102.400, 111.450,102.950, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("vsys_corr",n)
'''))

PHASES.append(("pmic", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-109.5)<0.05 and abs(y-106.4)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.10),mm(106.70))); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=109.6 and max(sx,ex)>=110.5:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.600,106.400, 110.600,106.700, 0.15),
    (110.600,106.700, 109.100,106.700, 0.15),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("pmic",n)
'''))

PHASES.append(("gnd_trim", r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="GND" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-112.8)<0.05 and abs(ex-112.8)<0.05 and min(sy,ey)>=105.30 and max(sy,ey)<=105.45:
        board.Remove(t); n+=1
    elif abs(sx-112.8)<0.05 and abs(sy-105.4)<0.05 and abs(ex-sx)<0.01 and abs(ey-sy)<0.01:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("gnd_trim",n)
'''))


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
        if fp.GetReference() in ("C_PMID","R_IPRETERM","U2","R_ILIM","R_ISET","C_VINLS","C_SYS"):
            fps[fp.GetReference()]=(round(tomm(fp.GetPosition().x),3), round(tomm(fp.GetPosition().y),3))
    layers=board.GetCopperLayerCount()
    return drc_n, short, power, pairs, latent, via_old, via_new, fps, layers

def main():
    snap=ROOT/f"backups/_try_passl_{TAG}.kicad_pcb"
    shutil.copy2(PCB, snap)
    for name, code in PHASES:
        r=subprocess.run([sys.executable,"-c",code], cwd=str(ROOT), capture_output=True, text=True)
        print(f"[{name}]", r.stdout.strip())
        if r.returncode!=0:
            print("FAIL", r.stderr[-600:])
            shutil.copy2(snap, PCB); sys.exit(2)
    ok, fo, fe = zone_refill()
    print("fill:", fo, fe[:300] if fe else "")
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
