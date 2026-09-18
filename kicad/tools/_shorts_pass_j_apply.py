#!/usr/bin/env python3
"""Pass J: safer leftovers — PMIC_INT↔VBAT, ISET↔ILIM, SCL↔3V3, signal skims.
Never delete GND copper. Revert if power pairs non-zero or latent GND↔VSYS flips."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 23

FIXES = {}

FIXES["vbat_west_jog"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        hit=True
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.28:
        hit=True
    if hit:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.30),
    (110.200,105.600, 109.400,105.600, 0.30),
    (109.400,105.600, 109.400,106.400, 0.30),
    (109.400,106.400, 106.200,106.400, 0.30),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["vbat_y1056"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        hit=True
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.28:
        hit=True
    if hit:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.30),
    (110.200,105.600, 108.120,105.600, 0.30),
    (108.120,105.600, 108.120,105.800, 0.30),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# Thin VBAT vertical only: shrink width 0.35→0.18 so it clears via without jog
FIXES["vbat_thin_vert"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # vertical skim
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        t.SetWidth(mm(0.15)); n+=1
    # truncate horizontal so it stops west of via keepout (center-0.625≈109.975)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.28:
        # replace with thinner ending at 109.90
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
# horizontal from 109.90 west (clear of via); vertical stays thin at 110.2
# also micro-jog vertical west to 110.05 for extra clearance
# Actually vertical at 110.2 w=0.15: half=0.075; need dist>=0.3+0.15+0.075=0.525; 110.6-110.2=0.4 < 0.525 STILL SHORT
# So must move vertical west to <= 110.6-0.525=110.075 for w=0.15, or thinner
# w=0.10 → need 0.3+0.15+0.05=0.50; 0.4 still short
# MUST move: x <= 110.075 for w=0.15. Use x=109.95
for t in list(board.GetTracks()):
    pass
for x1,y1,x2,y2,w in [
    (110.200,105.600, 109.950,105.600, 0.20),
    (109.950,105.600, 109.950,106.400, 0.15),
    (109.950,106.400, 106.200,106.400, 0.20),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["riset_west"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=-0.40
n=0
old_p1=(109.290,103.500); new_p1=(109.290+dx,103.500)
old_p2=(110.310,103.500); new_p2=(110.310+dx,103.500)
for fp in board.GetFootprints():
    if fp.GetReference()!="R_ISET": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y))); n+=1
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="ISET" and t.GetLayer()==pcbnew.F_Cu:
        ch=False
        if abs(sx-110.310)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
        if abs(ex-110.310)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

FIXES["rsda_west35"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=-0.35
n=0
old_p1=(109.440,107.550); new_p1=(109.440+dx,107.550)
old_p2=(110.460,107.550); new_p2=(110.460+dx,107.550)
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SDA": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y))); n+=1
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

FIXES["rscl_east40"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.40
n=0
old_p1=(110.990,107.600); new_p1=(110.990+dx,107.600)
old_p2=(112.010,107.600); new_p2=(112.010+dx,107.600)
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SCL": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y))); n+=1
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if t.GetNetname()=="3V3" and abs(x-112.010)<0.05 and abs(y-107.600)<0.1:
            t.SetPosition(pcbnew.VECTOR2I(mm(new_p2[0]),mm(new_p2[1]))); n+=1
        continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        ch=False
        if abs(sx-112.010)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
        if abs(ex-112.010)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
        if ch: n+=1
    if t.GetNetname()=="SCL" and t.GetLayer()==pcbnew.F_Cu:
        # track to pad1 from U2 E5
        ch=False
        if abs(sx-110.990)<0.08 and abs(sy-107.600)<0.08:
            t.SetStart(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1]))); ch=True
        if abs(ex-110.990)<0.08 and abs(ey-107.600)<0.08:
            t.SetEnd(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1]))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# Move PMIC_INT via OFF pad slightly NE into free space (if any) — risky
# Better: delete via and use F.Cu only escape east then via elsewhere
FIXES["pmic_int_via_ne"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# move via from 110.6,106.4 to 110.6,106.85 (toward E2 CD — careful) 
# or to 109.80,106.40 west of D1 — may hit VBAT
# Try 110.60,107.20 south of R_SCL / near LSCTRL — crowded
# Safest free: west of U2 at 109.50,106.40 — between C_BAT and U2
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-110.600)<0.05 and abs(y-106.400)<0.05:
        t.SetPosition(pcbnew.VECTOR2I(mm(109.500),mm(106.400))); n+=1
# add F stub D2 → new via
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode(); F=pcbnew.F_Cu
tr=pcbnew.PCB_TRACK(board)
tr.SetStart(pcbnew.VECTOR2I(mm(110.600),mm(106.400)))
tr.SetEnd(pcbnew.VECTOR2I(mm(109.500),mm(106.400)))
tr.SetWidth(mm(0.15)); tr.SetLayer(F); tr.SetNetCode(nc); board.Add(tr)
# B.Cu: old via was at 110.6 — may need B track update from 110.6 to 109.5
for t in list(board.GetTracks()):
    if t.GetNetname()!="PMIC_INT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.B_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-110.600)<0.05 and abs(sy-106.400)<0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(109.500),mm(106.400))); n+=1
    if abs(ex-110.600)<0.05 and abs(ey-106.400)<0.05:
        t.SetEnd(pcbnew.VECTOR2I(mm(109.500),mm(106.400))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

FIXES["vsys_pmid_dedupe"] = dict(del_code=r'''
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
    if abs(sy-105.6)<0.05 and abs(ey-105.6)<0.05:
        if min(sx,ex) < 111.55 and max(sx,ex) <= 111.85:
            hit=True
    if abs(sx-111.4)<0.05 and abs(ex-111.4)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=105.95:
        hit=True
    if hit:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VSYS").GetNetCode(); F=pcbnew.F_Cu
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(111.450),mm(105.600)))
t.SetEnd(pcbnew.VECTOR2I(mm(111.800),mm(105.600)))
t.SetWidth(mm(0.25)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

FIXES["rvsys_north"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dy=-0.40
n=0
pads=[]
for fp in board.GetFootprints():
    if fp.GetReference()!="R_VSYS": continue
    for p in fp.Pads():
        pads.append((tomm(p.GetPosition().x), tomm(p.GetPosition().y), p.GetNumber(), p.GetNetname()))
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    print("was",x,y,pads)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y+dy))); n+=1
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for ox,oy,_,_ in pads:
            if abs(px-ox)<0.15 and abs(py-oy)<0.15:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(px),mm(py+dy)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(px),mm(py+dy)))
                n+=1
                break
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

FIXES["sw_south"] = dict(del_code=r'''
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
    # any segment near y=104.5 with x toward C_SYS
    if abs(sy-104.5)<0.2 or abs(ey-104.5)<0.2:
        if max(sx,ex) >= 112.0 or (min(sx,ex)>=111.2 and abs(sx-ex)<0.05):
            # shift endpoints at ~104.5 to 104.10
            ch=False
            if abs(sy-104.5)<0.2: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(104.10))); ch=True
            if abs(ey-104.5)<0.2: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(104.10))); ch=True
            if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

FIXES["ipre_dogbone"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        latent_ok=True
assert latent_ok, "latent missing BEFORE"
for t in list(board.GetTracks()):
    if t.GetNetname()!="IPRETERM" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=110.3 and max(sx,ex)>=111.4:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(v): return v/1e6
nc=board.GetNetInfo().GetNetItem("IPRETERM").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.200,106.400, 109.700,106.400, 0.18),
    (109.700,106.400, 109.700,106.950, 0.18),
    (109.700,106.950, 111.490,106.950, 0.18),
    (111.490,106.950, 111.490,106.400, 0.18),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        latent_ok=True
assert latent_ok, "latent disturbed"
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
    latent = pairs.get(("GND","VSYS"),0)>0
    import pcbnew
    board=pcbnew.LoadBoard(str(PCB))
    def tomm(v): return v/1e6
    via_present=False
    for t in board.GetTracks():
        if t.GetClass()!="PCB_VIA": continue
        if t.GetNetname()!="GND": continue
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
            via_present=True
    return drc_n, short, power, pairs, latent, via_present

def main():
    if FIX not in FIXES:
        print("unknown", FIX, "known", list(FIXES)); sys.exit(1)
    fix=FIXES[FIX]
    snap=ROOT/f"backups/_try_{FIX}.kicad_pcb"
    shutil.copy2(PCB, snap)
    r=subprocess.run([sys.executable,"-c",fix["del_code"]], cwd=str(ROOT), capture_output=True, text=True)
    print("del:", r.stdout.strip(), (r.stderr[-400:] if r.returncode else ""))
    if r.returncode!=0:
        shutil.copy2(snap, PCB); print("FAIL del"); sys.exit(2)
    if fix["reb_code"]:
        r=subprocess.run([sys.executable,"-c",fix["reb_code"]], cwd=str(ROOT), capture_output=True, text=True)
        print("reb:", r.stdout.strip(), "rc", r.returncode, (r.stderr[-300:] if r.returncode else ""))
        if r.returncode!=0:
            shutil.copy2(snap, PCB); print("FAIL reb"); sys.exit(2)
    drc_n, short, power, pairs, latent, via_present = drc()
    power_ok = all(v==0 for v in power.values())
    keep = power_ok and short < BASE_SHORT and not latent and via_present
    # also keep if equal short but we cleared target pairs? No — require strict improvement
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(12)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":power_ok,"latent_gnd_vsys":latent,"via_present":via_present,"keep":keep,"top":top,"power":power}, indent=0))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
