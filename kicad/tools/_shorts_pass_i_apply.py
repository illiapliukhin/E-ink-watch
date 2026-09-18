#!/usr/bin/env python3
"""Pass I: safer non-latent clusters — PMIC_INT/VBAT, LSCTRL/3V3, SCL/3V3, IPRETERM/GND.
Never delete GND copper. Revert if power pairs non-zero or latent GND↔VSYS flips."""
import subprocess, sys, json, re, shutil
from pathlib import Path
from collections import Counter

ROOT = Path("/workspace/e-ink-watch-kicad")
PCB = ROOT / "e-ink-watch.kicad_pcb"
FIX = sys.argv[1]
BASE_SHORT = int(sys.argv[2]) if len(sys.argv) > 2 else 30

FIXES = {}

# --- I1: PMIC_INT — dedupe via on D2; jog VBAT west of via (keep via on pad) ---
FIXES["pmic_int_vbat"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# dedupe PMIC_INT vias at 110.6,106.4 — keep one
vias=[]
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-110.600)<0.05 and abs(y-106.400)<0.05:
        vias.append(t)
for v in vias[1:]:
    board.Remove(v); n+=1
# delete VBAT segments that skim the via
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    # vertical (110.2,105.6)-(110.2,106.4)
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        hit=True
    # horizontal (110.2,106.4)-(106.2,106.4) w=0.35
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.30:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n, "vias_kept", 1 if vias else 0)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
# B1 @110.2,105.6 → west 109.50 → south 106.4 → west to 106.2
# clears PMIC_INT via@110.6,106.4 (dx=1.1 > 0.3+0.175)
# also stitch B1-B2
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.35),  # B1-B2 stitch
    (110.200,105.600, 109.500,105.600, 0.35),
    (109.500,105.600, 109.500,106.400, 0.35),
    (109.500,106.400, 106.200,106.400, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# restore missing B.Cu link PMIC_INT via@110.6 → west corridor @94.2,106.4
# check for collisions: only add if gap exists
nc2=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode(); B=pcbnew.B_Cu
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(94.200),mm(106.400)))
t.SetEnd(pcbnew.VECTOR2I(mm(110.600),mm(106.400)))
t.SetWidth(mm(0.18)); t.SetLayer(B); t.SetNetCode(nc2); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- I1b: PMIC_INT VBAT jog ONLY (no B.Cu restore — safer if B hits something) ---
FIXES["pmic_int_vbat_only"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
vias=[]
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-110.600)<0.05 and abs(y-106.400)<0.05:
        vias.append(t)
for v in vias[1:]:
    board.Remove(v); n+=1
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        hit=True
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.30:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("del", n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.35),
    (110.200,105.600, 109.500,105.600, 0.35),
    (109.500,105.600, 109.500,106.400, 0.35),
    (109.500,106.400, 106.200,106.400, 0.35),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- I2: LSCTRL — east-approach pad1 (clear 3V3 pad2 + via); fix bogus 3V3 ---
FIXES["lsctrl_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        hit=False
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0: hit=True
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5: hit=True
        if hit: board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        # bogus pad1(LSCTRL)→via
        pts=sorted([(round(sx,2),round(sy,2)),(round(ex,2),round(ey,2))])
        if pts==[(114.3,108.41),(114.6,108.76)] or pts==[(114.30,108.41),(114.60,108.76)]:
            board.Remove(t); n+=1
        elif (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
             (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# U2 E3 → east to 113.40 → north past pad to 109.30 → east 115.20 → south to pad1 y → west to pad1
# stays clear of 3V3 via@114.30,108.41 and pad2@114.60,107.74
for x1,y1,x2,y2 in [
    (111.000,106.800, 113.400,106.800),
    (113.400,106.800, 113.400,109.300),
    (113.400,109.300, 115.200,109.300),
    (115.200,109.300, 115.200,108.760),
    (115.200,108.760, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# 3V3 pad2 → via (proper)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- I2b: LSCTRL simpler west-jog only (no north-of-pad) + fix 3V3; move via south ---
FIXES["lsctrl_via_south"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA":
        if t.GetNetname()=="3V3":
            x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
            if abs(x-114.300)<0.05 and abs(y-108.410)<0.05:
                t.SetPosition(pcbnew.VECTOR2I(mm(114.300),mm(107.950))); n+=1
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        hit=False
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0: hit=True
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5: hit=True
        if hit: board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# west jog x=113.50 clears moved via@114.30,107.95 (dx=0.80)
for x1,y1,x2,y2 in [
    (111.000,106.800, 113.500,106.800),
    (113.500,106.800, 113.500,108.760),
    (113.500,108.760, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,107.950),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
''')

# --- I3: SCL — move 3V3 via onto R_SCL pad2 (same net); clear U2 SCL ---
FIXES["scl_via_onpad"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-112.010)<0.05 and abs(y-106.900)<0.05:
        # move onto R_SCL pad2 @112.010,107.600
        t.SetPosition(pcbnew.VECTOR2I(mm(112.010),mm(107.600))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- I3b: R_SCL east +0.55 to clear R_SDA pad2; update tracks/via ---
FIXES["rscl_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.55
n=0
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SCL": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y))); n+=1
# move track ends and via that sat on old pads
old_p1=(110.990,107.600); new_p1=(110.990+dx,107.600)
old_p2=(112.010,107.600); new_p2=(112.010+dx,107.600)
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        # via on/near old pad2 (either 106.9 or 107.6 after prior fix)
        if t.GetNetname()=="3V3" and abs(x-112.010)<0.05 and abs(y-107.600)<0.15:
            t.SetPosition(pcbnew.VECTOR2I(mm(new_p2[0]),mm(y if abs(y-106.9)>0.05 else new_p2[1])))
            if abs(y-106.900)<0.05:
                t.SetPosition(pcbnew.VECTOR2I(mm(new_p2[0]),mm(new_p2[1])))
            else:
                t.SetPosition(pcbnew.VECTOR2I(mm(new_p2[0]),mm(new_p2[1])))
            n+=1
        continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
    # also 3V3 vertical (112.010,108.250)-(112.010,107.600)
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        ch=False
        if abs(sx-112.010)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
        if abs(ex-112.010)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
''', reb_code=None)

# --- I4: R_IPRETERM east +0.75 (clear R_ILIM GND pad + latent GND via) — do NOT touch GND via ---
FIXES["ripre_east"] = dict(del_code=r'''
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.75
n=0
# SAFETY: assert latent GND via still present before/after untouched
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        latent_ok=True
assert latent_ok, "latent GND via missing BEFORE"
for fp in board.GetFootprints():
    if fp.GetReference()!="R_IPRETERM": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y))); n+=1
old_p1=(111.490,103.500); new_p1=(111.490+dx,103.500)
old_p2=(112.510,103.500); new_p2=(112.510+dx,103.500)
# rebuild IPRETERM copper: delete old vertical/horizontal near old pad
for t in list(board.GetTracks()):
    if t.GetNetname()!="IPRETERM" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    hit=False
    if abs(sx-111.490)<0.05 or abs(ex-111.490)<0.05: hit=True
    if abs(sy-106.400)<0.05 and abs(ey-106.400)<0.05 and min(sx,ex)<=110.3 and max(sx,ex)>=111.4: hit=True
    if hit: board.Remove(t); n+=1
# add new route: U2 D1 @110.2,106.4 → east briefly → north jog? stay at y=106.4 to new x then south
# Avoid PMIC_INT via@110.6: go south from D1 first then east at lower y? 
# Safer: D1 → east only to 110.35 (still on pad) → south to 106.55 → east to new_p1 x → south to pad
# Actually D1 pad is small; simple: (110.2,106.4)-(new_p1x,106.4)-(new_p1x,103.5)
# That crosses PMIC_INT via — BAD. Jog south of via row:
# (110.2,106.4)-(110.2,106.55) no that's north into CD.
# Via at 106.4; go WEST then south? D1 is westmost.
# Path: (110.200,106.400) → (109.700,106.400) → (109.700,103.500) → (new_p1x,103.500)
# Clears via@110.6 and resistor row approach from west/south... wait 103.5 is the resistor row Y.
# Horizontal at y=103.5 from 109.7 to new_p1x runs along resistor pads — may hit R_ISET/R_ILIM.
# Better: vertical drop east of U2 away from via:
# (110.200,106.400)-(110.200,106.700) — into D-row/E-row? D1 is 106.4, E1 is 106.8 empty.
# Actually: from D1 go to (110.200,107.000) then east to new_x then south to 103.5 — long.
# Simplest clear of via: east at y=106.15 (between C-row 106.0 and D-row 106.4)
# (110.200,106.400)-(110.200,106.150)-(new_p1x,106.150)-(new_p1x,103.500)
nc=board.GetNetInfo().GetNetItem("IPRETERM").GetNetCode(); F=pcbnew.F_Cu
nx=new_p1[0]
for x1,y1,x2,y2 in [
    (110.200,106.400, 110.200,106.150),
    (110.200,106.150, nx,106.150),
    (nx,106.150, nx,103.500),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# GND stub to pad2 if any existed — leave; pad2 is GND and may touch zone
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="GND": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
        latent_ok=True
assert latent_ok, "latent GND via moved/deleted!"
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n, "new_p1", nx)
''', reb_code=None)

# --- I1c: PMIC_INT via nudge east-north off VBAT; dedupe; short F stub ---
FIXES["pmic_int_via_ne"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
vias=[]
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-110.600)<0.05 and abs(y-106.400)<0.05:
        vias.append(t)
if not vias:
    print(0); raise SystemExit
# keep one, move NE: clear VBAT at x=110.2 (need dx>=0.475+margin from track)
# VBAT track right edge ~110.375; via left = nx-0.3 >= 110.375+0.15 => nx>=110.825
vias[0].SetPosition(pcbnew.VECTOR2I(mm(110.900),mm(106.550))); n+=1
for v in vias[1:]:
    board.Remove(v); n+=1
# F stub pad D2 → via
nc=board.GetNetInfo().GetNetItem("PMIC_INT").GetNetCode()
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(110.600),mm(106.400)))
t.SetEnd(pcbnew.VECTOR2I(mm(110.900),mm(106.550)))
t.SetWidth(mm(0.15)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

# --- I1d: only dedupe PMIC_INT via (no move) ---
FIXES["pmic_int_dedupe"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
vias=[]
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="PMIC_INT": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-110.600)<0.05 and abs(y-106.400)<0.05:
        vias.append(t)
for v in vias[1:]:
    board.Remove(v); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n, "kept", len(vias)-n)
""", reb_code=None)

# --- I1e: thin/truncate VBAT horizontal end only (stop at x=109.9, not through via) ---
FIXES["vbat_truncate"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# Replace fat horizontal (110.2,106.4)-(106.2,106.4) w=0.35 with shorter end at 109.85
# and remove vertical that reaches y=106.4 at x=110.2 — replace with shorter to y=105.85
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        board.Remove(t); n+=1
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.30:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
# From B1 go west immediately at pad Y, then south further west
# B1-B2 stitch + escape west at y=105.6 to x=109.7, south to 106.4, west
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.30),
    (110.200,105.600, 109.700,105.600, 0.30),
    (109.700,105.600, 109.700,106.400, 0.30),
    (109.700,106.400, 106.200,106.400, 0.30),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["vbat_safe"] = dict(del_code=r"""
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
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.30:
        hit=True
    if hit: board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
# corridor x=109.80 clears C_BAT right~109.36 and PMIC_INT via left~110.30
for x1,y1,x2,y2,w in [
    (110.200,105.600, 110.600,105.600, 0.25),
    (110.200,105.600, 109.800,105.600, 0.25),
    (109.800,105.600, 109.800,106.400, 0.25),
    (109.800,106.400, 106.200,106.400, 0.25),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["lsctrl_north_enter"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        hit=False
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0: hit=True
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5: hit=True
        if hit: board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# west of pad column, enter pad1 from north y=108.95 (pad top~109.08)
# clears via@114.30,108.41 (dy=0.54 > 0.3+0.09)
for x1,y1,x2,y2 in [
    (111.000,106.800, 113.500,106.800),
    (113.500,106.800, 113.500,108.950),
    (113.500,108.950, 114.600,108.950),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# 3V3 pad2 to via — only if not already connected east
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["lsctrl_east_sw3"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        # only remove vertical through R_LSCTRL pads (keep U2 horizontal)
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
            board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# From end of horizontal @114.6,106.8 go east of SW3 pad1 then north above pad then west+stub
for x1,y1,x2,y2 in [
    (114.600,106.800, 116.550,106.800),
    (116.550,106.800, 116.550,109.150),
    (116.550,109.150, 114.600,109.150),
    (114.600,109.150, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


# Fix bogus GND track on R_CD pad1 (CD) — reconnect via to pad2 GND
FIXES["rcd_gnd_fix"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="GND" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # (112.8,108.41)-(113.3,108.41) on CD pad1
    if abs(sy-108.41)<0.05 and abs(ey-108.41)<0.05 and min(sx,ex)<=112.85 and max(sx,ex)>=113.25:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("GND").GetNetCode(); F=pcbnew.F_Cu
# pad2 GND @112.8,107.39 → east → north to via@113.3,108.41
for x1,y1,x2,y2 in [
    (112.800,107.390, 113.300,107.390),
    (113.300,107.390, 113.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["bogus_3v3_only"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
       (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["lsctrl_vert_only"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="LSCTRL" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode(); F=pcbnew.F_Cu
for x1,y1,x2,y2 in [
    (114.600,106.800, 116.550,106.800),
    (116.550,106.800, 116.550,109.150),
    (116.550,109.150, 114.600,109.150),
    (114.600,109.150, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["ripre_east"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.80
# assert latent via present
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()=="PCB_VIA" and t.GetNetname()=="GND":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
            latent_ok=True
assert latent_ok
for fp in board.GetFootprints():
    if fp.GetReference()!="R_IPRETERM": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
old_p1=(111.490,103.500); new_p1=(111.490+dx,103.500)
old_p2=(112.510,103.500); new_p2=(112.510+dx,103.500)
# shift IPRETERM track ends that were on old pads / vertical at old x
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname()!="IPRETERM": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        # pad ends
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
        # vertical column at old pad1 x
        if abs(px-111.490)<0.05:
            if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(px+dx),mm(py)))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(px+dx),mm(py)))
            n+=1
latent_ok=False
for t in board.GetTracks():
    if t.GetClass()=="PCB_VIA" and t.GetNetname()=="GND":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-111.31)<0.02 and abs(y-102.9)<0.02:
            latent_ok=True
assert latent_ok, "latent via disturbed"
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved", n, "new_p1", new_p1)
""", reb_code=None)

FIXES["ripre_east40"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.40
for fp in board.GetFootprints():
    if fp.GetReference()!="R_IPRETERM": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
old_p1=(111.490,103.500); new_p1=(111.490+dx,103.500)
old_p2=(112.510,103.500); new_p2=(112.510+dx,103.500)
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname()!="IPRETERM": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
        if abs(px-111.490)<0.05:
            if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(px+dx),mm(py)))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(px+dx),mm(py)))
            n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved", n)
""", reb_code=None)


FIXES["rilim_west"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=-0.70
for fp in board.GetFootprints():
    if fp.GetReference()!="R_ILIM": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
# old pads: pad1 ILIM 110.290, pad2 GND 111.310
old=[(110.290,103.500),(111.310,103.500)]
new=[(110.290+dx,103.500),(111.310+dx,103.500)]
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in zip(old,new):
            if abs(px-ox)<0.08 and abs(py-oy)<0.08:
                # only touch ILIM/GND nets near these pads
                if t.GetNetname() in ("ILIM","GND","ISET"):
                    if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                    else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                    n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved", n)
""", reb_code=None)


FIXES["rls_west_jog"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=-0.50
for fp in board.GetFootprints():
    if fp.GetReference()!="R_LSCTRL": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
# old pads 114.600,{108.760,107.740}
n=0
# delete LSCTRL vertical + extend horizontal; delete bogus 3V3; shift 3V3 east stub
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
            board.Remove(t); n+=1
        # shorten/remove horizontal that ended at 114.6 — will rebuild from 111
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0:
            board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
        # east stub from old pad2
        if abs(sy-107.740)<0.05 and abs(ey-107.740)<0.05 and min(sx,ex)<=114.65 and max(sx,ex)>=115.15:
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
# new pad positions after -0.50
p1x,p1y=114.100,108.760
p2x,p2y=114.100,107.740
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# approach from east of pads at x=114.70 (clears pad2 right~114.37 and via@114.30)
for x1,y1,x2,y2 in [
    (111.000,106.800, 114.700,106.800),
    (114.700,106.800, 114.700,108.760),
    (114.700,108.760, p1x,p1y),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
# pad2 to via@114.30,108.41 — via is east of new pad2
for x1,y1,x2,y2 in [
    (p2x,p2y, 114.300,p2y),
    (114.300,p2y, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
# restore east stub from pad2 if useful
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(p2x),mm(p2y))); t.SetEnd(pcbnew.VECTOR2I(mm(114.700),mm(p2y)))
t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["epd_dc_mosi"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# nudge EPD_DC F.Cu channel y=85.40 → 85.60; thin zero-len stub
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_DC" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # zero-len fat stub at 99,85.4
    if abs(sx-99.0)<0.05 and abs(sy-85.4)<0.05 and abs(ex-99.0)<0.05 and abs(ey-85.4)<0.05:
        board.Remove(t); n+=1; continue
    # horizontals at y=85.40
    if abs(sy-85.40)<0.05 and abs(ey-85.40)<0.05 and min(sx,ex)>=98.5 and max(sx,ex)<=103:
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.60)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.60))); n+=1
    # verticals that ended at 85.40 in this region
    if abs(sx-ex)<0.01 and abs(sx-100.25)<0.05:
        if abs(sy-85.40)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.60))); n+=1
        if abs(ey-85.40)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.60))); n+=1
    if abs(sx-ex)<0.01 and abs(sx-102.0)<0.05:
        if abs(sy-85.40)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.60))); n+=1
        if abs(ey-85.40)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.60))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["vbat_thin"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# only thin the two VBAT segments near PMIC_INT via — no path change
for t in list(board.GetTracks()):
    if t.GetNetname()!="VBAT" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-110.2)<0.05 and abs(ex-110.2)<0.05 and min(sy,ey)<=105.65 and max(sy,ey)>=106.35:
        t.SetWidth(mm(0.20)); n+=1
    if abs(sy-106.4)<0.05 and abs(ey-106.4)<0.05 and min(sx,ex)<=106.3 and max(sx,ex)>=110.1 and tomm(t.GetWidth())>0.30:
        # truncate east end to 109.95 and thin — small geometry change
        if sx>ex:
            t.SetStart(pcbnew.VECTOR2I(mm(109.95),mm(sy)))
        else:
            t.SetEnd(pcbnew.VECTOR2I(mm(109.95),mm(ey)))
        t.SetWidth(mm(0.20)); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
# bridge from vertical bottom to truncated horizontal: (110.2,106.4) gone;
# vertical still ends at 106.4 — connect with dogleg west at lower risk
# Actually vertical still at 110.2 to 106.4 — thin only may be enough.
# Add link (110.2,106.4)-(109.95,106.4) thin if gap
nc=board.GetNetInfo().GetNetItem("VBAT").GetNetCode(); F=pcbnew.F_Cu
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(110.200),mm(106.400)))
t.SetEnd(pcbnew.VECTOR2I(mm(109.950),mm(106.400)))
t.SetWidth(mm(0.20)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["mosi_south"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# move EPD_MOSI channel y=85.25 → 85.05 (further from DC@85.40)
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_MOSI" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # zero-len stub
    if abs(sx-98.0)<0.05 and abs(sy-85.25)<0.05 and abs(ex-sx)<0.01 and abs(ey-sy)<0.01:
        board.Remove(t); n+=1; continue
    if abs(sy-85.25)<0.05 and abs(ey-85.25)<0.05 and min(sx,ex)>=97.5 and max(sx,ex)<=102:
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.05)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.05))); n+=1
    # verticals touching 85.25
    if abs(sx-ex)<0.01 and (abs(sx-101.6)<0.05 or abs(sx-98.0)<0.05 or abs(sx-98.75)<0.05):
        ch=False
        if abs(sy-85.25)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.05))); ch=True
        if abs(ey-85.25)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.05))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["dc_stub_only"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
n=0
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_DC" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-99.0)<0.05 and abs(sy-85.4)<0.05 and abs(ex-99.0)<0.05 and abs(ey-85.4)<0.05:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["sw3_ls_combo"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
# move SW3 +0.60 further east for LSCTRL corridor
dx=0.60
fp=None
for f in board.GetFootprints():
    if f.GetReference()=="SW3": fp=f; break
oldx,oldy=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
fp.SetPosition(pcbnew.VECTOR2I(mm(oldx+dx),mm(oldy)))
# move BTN3 copper locked to pad1
n=0
pad1x=oldx-1.7  # pad1 offset from center for this FP: center 117.4, pad1 115.7 → -1.7
# actually pad1 was 115.70 at center 117.40
old_pad1=115.70; new_pad1=115.70+dx
for t in list(board.GetTracks()):
    if t.GetNetname()!="BTN3": continue
    if t.GetClass()=="PCB_VIA":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if abs(x-old_pad1)<0.05:
            t.SetPosition(pcbnew.VECTOR2I(mm(new_pad1),mm(y))); n+=1
        continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    ch=False
    if abs(sx-old_pad1)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
    if abs(ex-old_pad1)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
    if ch: n+=1
# LSCTRL vertical replace + bogus 3V3 delete
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
            board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("n", n, "sw3", oldx, "->", oldx+dx)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
F=pcbnew.F_Cu
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
# corridor x=115.15 between R_LSCTRL right~114.87 and new SW3 pad1 left~115.85
for x1,y1,x2,y2 in [
    (114.600,106.800, 115.150,106.800),
    (115.150,106.800, 115.150,108.760),
    (115.150,108.760, 114.600,108.760),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.16)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["lsctrl_bcu"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# remove F.Cu LSCTRL (both segments) and bogus 3V3
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0:
            board.Remove(t); n+=1
        elif abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
            board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
F,B=pcbnew.F_Cu,pcbnew.B_Cu
# stub from U2 E3 to via just east of U2 away from R_CD
# via @111.55,107.15 — north-east of E3, south of R_SCL
v1=(111.550,107.150)
# via near R_LSCTRL pad1 from east @115.00,108.760
v2=(115.000,108.760)
for (x,y) in (v1,v2):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(0.45)); v.SetDrill(mm(0.20))
    v.SetNetCode(nc); board.Add(v)
# F stub U2→v1
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(111.000),mm(106.800)))
t.SetEnd(pcbnew.VECTOR2I(mm(v1[0]),mm(v1[1])))
t.SetWidth(mm(0.15)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# F stub v2→pad1
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(v2[0]),mm(v2[1])))
t.SetEnd(pcbnew.VECTOR2I(mm(114.600),mm(108.760)))
t.SetWidth(mm(0.15)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
# B.Cu path v1 → south-east clear of dense area → v2
# (111.55,107.15)-(111.55,109.50)-(115.00,109.50)-(115.00,108.76)
for x1,y1,x2,y2 in [
    (v1[0],v1[1], v1[0],109.500),
    (v1[0],109.500, v2[0],109.500),
    (v2[0],109.500, v2[0],v2[1]),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.15)); t.SetLayer(B); t.SetNetCode(nc); board.Add(t)
# 3V3 pad2→via
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["rcd_south"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dy=-0.55  # south: pad1 108.41→107.86 clears GND stub/via at y=108.41
for fp in board.GetFootprints():
    if fp.GetReference()!="R_CD": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y+dy)))
old_p1=(112.800,108.410); new_p1=(112.800,108.410+dy)
old_p2=(112.800,107.390); new_p2=(112.800,107.390+dy)
n=0
# update CD tracks only (NOT GND)
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname()!="CD": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        if abs(px-old_p1[0])<0.08 and abs(py-old_p1[1])<0.08:
            if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1])))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1])))
            n+=1
        if abs(px-old_p2[0])<0.08 and abs(py-old_p2[1])<0.08:
            if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(new_p2[0]),mm(new_p2[1])))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(new_p2[0]),mm(new_p2[1])))
            n+=1
    # also shift vertical CD column endpoints at x=112.8 y near old
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-112.8)<0.05 and abs(ex-112.8)<0.05:
        # if one end was at U2 y=106.8 keep it; if at pad1 update already done
        pass
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("moved", n, "new_p1", new_p1)
""", reb_code=None)

FIXES["ls_bcu_rcd"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# 1) R_CD south first
dy=-0.55
for fp in board.GetFootprints():
    if fp.GetReference()!="R_CD": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y+dy)))
old_p1=(112.800,108.410); new_p1=(112.800,108.410+dy)
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetNetname()!="CD": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        if abs(px-old_p1[0])<0.08 and abs(py-old_p1[1])<0.08:
            if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1])))
            else: t.SetEnd(pcbnew.VECTOR2I(mm(new_p1[0]),mm(new_p1[1])))
            n+=1
# 2) remove F LSCTRL + bogus 3V3
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="LSCTRL" and t.GetLayer()==pcbnew.F_Cu:
        if abs(sx-ex)<1e-4 and abs(sy-ey)<1e-4: continue
        if abs(sy-106.800)<0.08 and abs(ey-106.800)<0.08 and min(sx,ex)<=111.2 and max(sx,ex)>=114.0:
            board.Remove(t); n+=1
        elif abs(sx-114.600)<0.08 and abs(ex-114.600)<0.08 and min(sy,ey)<=106.9 and max(sy,ey)>=108.5:
            board.Remove(t); n+=1
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu:
        if (abs(sx-114.6)<0.08 and abs(sy-108.76)<0.08 and abs(ex-114.3)<0.08 and abs(ey-108.41)<0.08) or \
           (abs(ex-114.6)<0.08 and abs(ey-108.76)<0.08 and abs(sx-114.3)<0.08 and abs(sy-108.41)<0.08):
            board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
nc=board.GetNetInfo().GetNetItem("LSCTRL").GetNetCode()
F,B=pcbnew.F_Cu,pcbnew.B_Cu
v1=(111.550,107.150); v2=(115.000,108.760)
for (x,y) in (v1,v2):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(0.45)); v.SetDrill(mm(0.20))
    v.SetNetCode(nc); board.Add(v)
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(111.000),mm(106.800)))
t.SetEnd(pcbnew.VECTOR2I(mm(v1[0]),mm(v1[1])))
t.SetWidth(mm(0.15)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
t=pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(mm(v2[0]),mm(v2[1])))
t.SetEnd(pcbnew.VECTOR2I(mm(114.600),mm(108.760)))
t.SetWidth(mm(0.15)); t.SetLayer(F); t.SetNetCode(nc); board.Add(t)
for x1,y1,x2,y2 in [
    (v1[0],v1[1], v1[0],109.500),
    (v1[0],109.500, v2[0],109.500),
    (v2[0],109.500, v2[0],v2[1]),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.15)); t.SetLayer(B); t.SetNetCode(nc); board.Add(t)
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
for x1,y1,x2,y2 in [
    (114.600,107.740, 114.300,107.740),
    (114.300,107.740, 114.300,108.410),
]:
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(0.18)); t.SetLayer(F); t.SetNetCode(nc3); board.Add(t)
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print("reb")
""")


FIXES["fix_3v3_via_btn"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
nc3=board.GetNetInfo().GetNetItem("3V3").GetNetCode()
# restore via @114.3,108.41 to 3V3 if it became LSCTRL
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-114.300)<0.05 and abs(y-108.410)<0.05:
        print("via net was", t.GetNetname())
        t.SetNetCode(nc3); n+=1
# truncate/remove 3V3 east stub that skims SW3: (114.6,107.74)-(115.2,107.74)
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-107.740)<0.05 and abs(ey-107.740)<0.05 and min(sx,ex)<=114.65 and max(sx,ex)>=115.15:
        board.Remove(t); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["via3v3_south"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
for t in list(board.GetTracks()):
    if t.GetClass()!="PCB_VIA": continue
    if t.GetNetname()!="3V3": continue
    x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
    if abs(x-114.300)<0.05 and abs(y-108.410)<0.05:
        # move south toward pad2, clear pad1: new y=107.95
        t.SetPosition(pcbnew.VECTOR2I(mm(114.300),mm(107.950))); n+=1
# update 3V3 track that ended at old via y
for t in list(board.GetTracks()):
    if t.GetNetname()!="3V3" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-114.3)<0.05 and abs(sy-108.41)<0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(114.300),mm(107.950))); n+=1
    if abs(ex-114.3)<0.05 and abs(ey-108.41)<0.05:
        t.SetEnd(pcbnew.VECTOR2I(mm(114.300),mm(107.950))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["rscl_east55"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=0.55
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SCL": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
old_p1=(110.990,107.600); new_p1=(110.990+dx,107.600)
old_p2=(112.010,107.600); new_p2=(112.010+dx,107.600)
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA":
        x,y=tomm(t.GetPosition().x),tomm(t.GetPosition().y)
        if t.GetNetname()=="3V3" and abs(x-112.010)<0.05 and abs(y-107.600)<0.05:
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
    # 3V3 spine at x=112.010
    if t.GetNetname()=="3V3" and t.GetLayer()==pcbnew.F_Cu and t.GetClass()!="PCB_VIA":
        sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
        ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
        ch=False
        if abs(sx-112.010)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy))); ch=True
        if abs(ex-112.010)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["epd_cs_rst"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# EPD_RST track near (100.75,85.9) — nudge south or jog
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_RST" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    # horizontal-ish near y=85.9 x~100.75
    if abs(sy-85.90)<0.15 and abs(ey-85.90)<0.15 and min(sx,ex)<=100.8 and max(sx,ex)>=99:
        # move to y=85.70
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(85.70)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(85.70))); n+=1
    elif min(sx,ex)<=101 and max(sx,ex)>=100 and min(sy,ey)<=86.5 and max(sy,ey)>=85.5:
        # print candidates
        print(f"cand ({sx:.3f},{sy:.3f})-({ex:.3f},{ey:.3f})")
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["rsda_west"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dx=-0.45
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SDA": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x+dx),mm(y)))
# current pad2 110.460,107.400 → 110.010; pad1 109.440→108.990
old_p1=(109.440,107.400); new_p1=(109.440+dx,107.400)
old_p2=(110.460,107.400); new_p2=(110.460+dx,107.400)
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08 and t.GetNetname() in ("SDA","3V3"):
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["epd_cs_rst2"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# list and fix EPD_RST / CS_MAIN near 100.8,86
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if t.GetNetname()=="EPD_CS_MAIN":
        # track @100.8,86.35 len 1.35 — nudge north
        if abs(sy-86.35)<0.1 and abs(ey-86.35)<0.1 and 99<min(sx,ex)<102:
            t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(86.55)))
            t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(86.55))); n+=1
            print("cs",sx,sy,ex,ey)
        elif 99.5<=min(sx,ex) and max(sx,ex)<=102 and 85.5<=min(sy,ey) and max(sy,ey)<=87:
            print("cs cand", sx,sy,ex,ey)
    if t.GetNetname()=="EPD_RST":
        if 99.5<=min(sx,ex) and max(sx,ex)<=102.5 and 85.2<=min(sy,ey) and max(sy,ey)<=87:
            print("rst cand", sx,sy,ex,ey, "w", tomm(t.GetWidth()))
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["rsda_south"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
dy=+0.35  # further south away from R_SCL
for fp in board.GetFootprints():
    if fp.GetReference()!="R_SDA": continue
    x,y=tomm(fp.GetPosition().x),tomm(fp.GetPosition().y)
    print("R_SDA was", x,y)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y+dy)))
old_p1=(109.440,107.400); new_p1=(109.440,107.400+dy)
old_p2=(110.460,107.400); new_p2=(110.460,107.400+dy)
n=0
for t in list(board.GetTracks()):
    if t.GetClass()=="PCB_VIA": continue
    for end_name in ("Start","End"):
        pt=t.GetStart() if end_name=="Start" else t.GetEnd()
        px,py=tomm(pt.x),tomm(pt.y)
        for (ox,oy),(nx,ny) in [(old_p1,new_p1),(old_p2,new_p2)]:
            if abs(px-ox)<0.08 and abs(py-oy)<0.08 and t.GetNetname() in ("SDA","3V3"):
                if end_name=="Start": t.SetStart(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                else: t.SetEnd(pcbnew.VECTOR2I(mm(nx),mm(ny)))
                n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["epd_cs_x"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# move EPD_CS_MAIN vertical x=100.80 → 101.05 (clear RST@100.75)
for t in list(board.GetTracks()):
    if t.GetNetname()!="EPD_CS_MAIN" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sx-100.80)<0.05 and abs(ex-100.80)<0.05:
        t.SetStart(pcbnew.VECTOR2I(mm(101.05),mm(sy)))
        t.SetEnd(pcbnew.VECTOR2I(mm(101.05),mm(ey))); n+=1
    # horizontal (100.80,85)-(99.75,85)
    if abs(sy-85.00)<0.05 and abs(ey-85.00)<0.05 and min(sx,ex)<=99.8 and max(sx,ex)>=100.7:
        if abs(sx-100.80)<0.05: t.SetStart(pcbnew.VECTOR2I(mm(101.05),mm(sy))); n+=1
        if abs(ex-100.80)<0.05: t.SetEnd(pcbnew.VECTOR2I(mm(101.05),mm(ey))); n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)

FIXES["ts_jog_south"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# TS horizontal at y=107.55 → 107.30 (clear R_SDA 3V3@107.75); stay clear of R_TS VBUS@107.00
for t in list(board.GetTracks()):
    if t.GetNetname()!="TS" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-107.55)<0.08 and abs(ey-107.55)<0.08 and min(sx,ex)<=108 and max(sx,ex)>=110:
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(107.30)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(107.30))); n+=1
    # verticals that meet y=107.55
    if abs(sx-ex)<0.01:
        ch=False
        if abs(sy-107.55)<0.08: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(107.30))); ch=True
        if abs(ey-107.55)<0.08: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(107.30))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


FIXES["nreset_pogo_jog"] = dict(del_code=r"""
import pcbnew
board=pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def tomm(v): return v/1e6
def mm(v): return int(round(float(v)*1e6))
n=0
# horizontal y=107.10 → 106.80 to clear GND via@94.16,107.25
for t in list(board.GetTracks()):
    if t.GetNetname()!="nRESET_POGO" or t.GetClass()=="PCB_VIA": continue
    if t.GetLayer()!=pcbnew.F_Cu: continue
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if abs(sy-107.10)<0.08 and abs(ey-107.10)<0.08:
        t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(106.80)))
        t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(106.80))); n+=1
    # vertical at x=98.3 that meets 107.10
    if abs(sx-98.30)<0.05 and abs(ex-98.30)<0.05:
        ch=False
        if abs(sy-107.10)<0.08: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(106.80))); ch=True
        if abs(ey-107.10)<0.08: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(106.80))); ch=True
        # also the segment (98.3,106.5)-(98.3,111) — adjust 106.5 end if needed
        if abs(sy-106.50)<0.08: t.SetStart(pcbnew.VECTOR2I(mm(sx),mm(106.80))); ch=True
        if abs(ey-106.50)<0.08: t.SetEnd(pcbnew.VECTOR2I(mm(ex),mm(106.80))); ch=True
        if ch: n+=1
pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(n)
""", reb_code=None)


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
    # latent specifically: GND↔VSYS shorting present
    latent = pairs.get(("GND","VSYS"),0)>0
    # also check via still exists
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
    print("del:", r.stdout.strip(), (r.stderr[-500:] if r.returncode else ""))
    if r.returncode!=0:
        shutil.copy2(snap, PCB); print("FAIL del"); sys.exit(2)
    if fix["reb_code"]:
        r=subprocess.run([sys.executable,"-c",fix["reb_code"]], cwd=str(ROOT), capture_output=True, text=True)
        print("reb:", r.stdout.strip(), "rc", r.returncode)
        if r.returncode!=0:
            shutil.copy2(snap, PCB); print("FAIL reb"); sys.exit(2)
    drc_n, short, power, pairs, latent, via_present = drc()
    power_ok = all(v==0 for v in power.values())
    keep = power_ok and short <= BASE_SHORT and not latent and via_present
    top=[f"{a}|{b}:{c}" for (a,b),c in pairs.most_common(12)]
    print(json.dumps({"fix":FIX,"drc":drc_n,"shorting":short,"base":BASE_SHORT,"power_ok":power_ok,"latent_gnd_vsys":latent,"via_present":via_present,"keep":keep,"top":top,"power":power}, indent=0))
    if not keep:
        shutil.copy2(snap, PCB)
        print("REVERTED")
        sys.exit(2)
    print("KEEP")

if __name__=="__main__":
    main()
