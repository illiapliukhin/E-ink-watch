#!/usr/bin/env python3
"""Pass F2 incremental surgical fixes."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2])

FIXES = {}

FIXES["main_mosi_y"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_MOSI" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    if max(sx,ex)>110: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sx-101.60)<0.1 and abs(ex-101.60)<0.1 and ymin<=85.0 and ymax>=86.2: hit=True
    if abs(sy-84.90)<0.08 and abs(ey-84.90)<0.08 and xmin<=101.5 and xmax>=98.0: hit=True
    if abs(sx-98.75)<0.1 and abs(ex-98.75)<0.1 and ymax<=85.3 and ymin>=83.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_MOSI").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(101.60,86.35,101.60,84.55),(101.60,84.55,98.00,84.55),(98.00,84.55,98.00,84.90),(98.00,84.90,98.75,84.90),(98.75,84.90,98.75,83.15)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["nreset_pogo_y"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="nRESET_POGO" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-106.50)<0.08 and abs(ey-106.50)<0.08 and min(sx,ex)<=93.5 and max(sx,ex)>=98.0: hit=True
    if abs(sx-98.30)<0.1 and abs(ex-98.30)<0.1: hit=True
    if abs(sy-111.00)<0.08 and abs(ey-111.00)<0.08 and min(sx,ex)<=96.1 and max(sx,ex)>=98.2: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("nRESET_POGO").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(93.45,106.50,93.45,107.20),(93.45,107.20,98.30,107.20),(98.30,107.20,98.30,111.00),(98.30,111.00,96.00,111.00)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["swdclk_pogo_x"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="SWDCLK_POGO" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-105.50)<0.08 and abs(ey-105.50)<0.08 and min(sx,ex)<=93.5 and max(sx,ex)>=94.9: hit=True
    if abs(sx-95.00)<0.1 and abs(ex-95.00)<0.1: hit=True
    if abs(sy-111.00)<0.08 and abs(ey-111.00)<0.08 and min(sx,ex)<=93.1 and max(sx,ex)>=94.9: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("SWDCLK_POGO").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(93.45,105.50,95.80,105.50),(95.80,105.50,95.80,111.00),(95.80,111.00,93.00,111.00)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["l_rst_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_RST" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    if max(sx,ex)>=95: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sy-96.90)<0.12 and abs(ey-96.90)<0.12 and xmin<=84.0 and xmax>=87.0: hit=True
    if abs(sx-87.35)<0.1 and abs(ex-87.35)<0.1 and ymin<=97.0 and ymax>=99.5: hit=True
    if abs(sx-83.50)<0.1 and abs(ex-83.50)<0.1 and ymin<=97.0 and ymax>=99.5: hit=True
    if abs(sy-99.75)<0.08 and abs(ey-99.75)<0.08 and abs(xmin-83.15)<0.15 and abs(xmax-83.50)<0.2: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_RST").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(87.35,99.80,88.60,99.80),(88.60,99.80,88.60,95.50),(88.60,95.50,83.50,95.50),(83.50,95.50,83.50,99.75),(83.50,99.75,83.15,99.75)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["r_dc_x"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_DC" or t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    if max(sx,ex)<110: continue
    xmin,xmax=min(sx,ex),max(sx,ex); ymin,ymax=min(sy,ey),max(sy,ey)
    hit=False
    if abs(sx-112.90)<0.1 and abs(ex-112.90)<0.1 and ymin<=99.2 and ymax>=100.5: hit=True
    if abs(sy-99.10)<0.1 and abs(ey-99.10)<0.1 and xmin<=112.95 and xmax>=113.6: hit=True
    if abs(sy-100.75)<0.1 and abs(ey-100.75)<0.1 and xmin<=112.9 and xmax>=116.8: hit=True
    if abs(sx-113.65)<0.1 and abs(ex-113.65)<0.1 and ymin<=98.8 and ymax>=99.2: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("EPD_DC").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [(113.65,98.80,113.65,99.30),(113.65,99.30,113.50,99.30),(113.50,99.30,113.50,100.75),(113.50,100.75,116.85,100.75)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["btn3_y1105"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="BTN3" or t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
    hit=False
    if abs(sy-109.15)<0.12 and abs(ey-109.15)<0.12: hit=True
    if abs(sx-98.80)<0.1 and abs(ex-98.80)<0.1 and max(sy,ey)>=109.0: hit=True
    if abs(sx-114.80)<0.1 and abs(ex-114.80)<0.1 and min(sy,ey)<=109.2 and max(sy,ey)>=108.0: hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("BTN3").GetNetCode(); B=pcbnew.B_Cu
for x1,y1,x2,y2 in [(98.80,93.95,98.80,110.50),(98.80,110.50,114.80,110.50),(114.80,110.50,114.80,108.00)]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(B); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

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
    POWER=[("GND","VBUS"),("GND","VBAT"),("GND","VBUS_POGO"),("3V3","GND"),("3V3_DISP","GND"),("GND","SW"),("3V3","3V3_DISP"),("GND","VSYS")]
    power={f"{a}|{b}": pairs.get(tuple(sorted([a,b])),0) for a,b in POWER}
    return drc_n, short, power, pairs

def main():
    fix=FIXES[FIX]
    snap=ROOT/f"backups/_try_{FIX}.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",fix["del_code"]], cwd=str(ROOT), capture_output=True, text=True)
    print("del:", r.stdout.strip())
    if r.returncode!=0:
        shutil.copy2(snap, PCB); print("FAIL del", r.stderr[-200:]); sys.exit(2)
    if fix["reb_code"]:
        r=subprocess.run([sys.executable,"-c",fix["reb_code"]], cwd=str(ROOT), capture_output=True, text=True)
        print("reb:", r.stdout.strip(), "rc", r.returncode)
        if r.returncode!=0:
            shutil.copy2(snap, PCB); print("FAIL reb"); sys.exit(2)
    drc_n, short, power, pairs = drc()
    keep = all(v==0 for v in power.values()) and short < BASE_SHORT
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(8)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":all(v==0 for v in power.values()),"power":power,"keep":keep,"top":top}))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
