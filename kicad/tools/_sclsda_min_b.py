#!/usr/bin/env python3
"""Minimal pass B: 3V3 jog, F.Cu I2C, FH12 rebuild, R_SDA nudge. Avoid power corridor."""
from pathlib import Path
import pcbnew

PCB=Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
F_CU=pcbnew.F_Cu
W_SIG,W_PWR=0.18,0.25
# Power corridor keepout for NEW vias/tracks (except explicit 3V3 jog at y~108)
def in_power_corridor(x,y):
    return 110.0<=x<=118.0 and 100.0<=y<=106.0

def mm(v): return int(round(float(v)*1e6))
def tomm(v): return float(v)/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
def is_zero(t):
    return abs(tomm(t.GetStart().x)-tomm(t.GetEnd().x))<1e-4 and abs(tomm(t.GetStart().y)-tomm(t.GetEnd().y))<1e-4
def netcode(board,name):
    return board.GetNetInfo().GetNetItem(name).GetNetCode()

def add_track(board,x1,y1,x2,y2,w,layer,net):
    if near(x1,x2,1e-9) and near(y1,y2,1e-9): return
    # block new copper in power corridor except 3V3
    if net!="3V3":
        for x,y in ((x1,y1),(x2,y2),((x1+x2)/2,(y1+y2)/2)):
            if in_power_corridor(x,y):
                print(f"BLOCK track {net} through power corridor ({x:.2f},{y:.2f})")
                return
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(netcode(board,net))
    board.Add(t)

def add_via(board,x,y,d,net):
    if in_power_corridor(x,y):
        print(f"BLOCK via {net} in power corridor ({x},{y})"); return False
    if 90.5<=x<=101.5 and 108.5<=y<=117.0:
        print(f"BLOCK seal via ({x},{y})"); return False
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x),mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x),mm(y)))
    t.SetWidth(mm(d)); t.SetLayer(F_CU); t.SetNetCode(netcode(board,net))
    board.Add(t); return True

def pad_xy(fp,num):
    for p in fp.Pads():
        if p.GetNumber()==str(num):
            return tomm(p.GetX()),tomm(p.GetY())
    raise KeyError(num)

def shift_ends(board, old_pts, dx, dy, allow_nets, eps=0.10):
    n=0
    for t in board.GetTracks():
        if is_zero(t): continue
        if t.GetNetname() not in allow_nets: continue
        sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
        ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
        for ox,oy in old_pts:
            if near(sx,ox,eps) and near(sy,oy,eps):
                t.SetStart(pcbnew.VECTOR2I(mm(sx+dx),mm(sy+dy))); n+=1
            if near(ex,ox,eps) and near(ey,oy,eps):
                t.SetEnd(pcbnew.VECTOR2I(mm(ex+dx),mm(ey+dy))); n+=1
    return n

board=pcbnew.LoadBoard(str(PCB))
assert board.GetCopperLayerCount()==4

# R_SDA south (away from NTC 107.8 / R_TS 107.0)
fp=board.FindFootprintByReference("R_SDA")
old=(tomm(fp.GetX()),tomm(fp.GetY()))
old_pads=[pad_xy(fp,"1"),pad_xy(fp,"2")]
dx,dy=0.15,-0.55  # -> 109.65, 107.05
fp.SetPosition(pcbnew.VECTOR2I(mm(old[0]+dx),mm(old[1]+dy)))
n=shift_ends(board, old_pads, dx, dy, allow_nets={"SDA","3V3"})
print(f"R_SDA {old} -> ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {n}")

# East MP shrink
jd=board.FindFootprintByReference("J_DISP_MAIN")
for p in jd.Pads():
    if p.GetNumber()!="MP": continue
    px,py=tomm(p.GetX()),tomm(p.GetY())
    if px<100: continue
    p.SetSize(pcbnew.VECTOR2I(mm(1.0),mm(1.4)))
    p.SetPosition(pcbnew.VECTOR2I(mm(105.10),mm(86.80)))
    print(f"east MP ({px:.2f},{py:.2f})->(105.10,86.80)")

sda1,sda2=pad_xy(fp,"1"),pad_xy(fp,"2")
rc=board.FindFootprintByReference("R_SCL")
scl1,scl2=pad_xy(rc,"1"),pad_xy(rc,"2")

# 3V3 jog north of pullups (y~108.2) — outside power corridor y<=106
y_jog=max(sda2[1],scl2[1])+0.65
add_track(board,sda2[0],sda2[1],sda2[0],y_jog,W_PWR,F_CU,"3V3")
add_track(board,sda2[0],y_jog,scl2[0],y_jog,W_PWR,F_CU,"3V3")
add_track(board,scl2[0],y_jog,scl2[0],scl2[1],W_PWR,F_CU,"3V3")
print(f"3V3 jog y={y_jog:.2f}")

# F.Cu to U2 — these are at y=106.8 which is borderline corridor (y<=106).
# U2 pads at y=106.8 — allow by using y=106.85 which is >106 ... corridor is y<=106, so 106.8 OK
add_track(board,sda1[0],sda1[1],111.400,106.800,W_SIG,F_CU,"SDA")
add_track(board,111.800,106.800,scl1[0],scl1[1],W_SIG,F_CU,"SCL")
print("F.Cu SDA/SCL to U2")

# FH12 channels
add_via(board,97.000,84.050,0.45,"EPD_SCK")
add_track(board,105.500,84.050,97.000,84.050,W_SIG,F_CU,"EPD_SCK")
add_track(board,97.000,84.050,99.250,84.050,W_SIG,F_CU,"EPD_SCK")
add_track(board,99.250,84.050,99.250,83.150,W_SIG,F_CU,"EPD_SCK")
print("EPD_SCK y=84.05")

add_track(board,104.000,86.350,102.600,86.350,W_SIG,F_CU,"EPD_RST")
add_track(board,102.600,86.350,102.600,85.550,W_SIG,F_CU,"EPD_RST")
add_track(board,102.600,85.550,100.750,85.550,W_SIG,F_CU,"EPD_RST")
add_track(board,100.750,85.550,100.750,83.150,W_SIG,F_CU,"EPD_RST")
print("EPD_RST west-jog")

add_track(board,105.400,90.150,105.400,86.550,W_SIG,F_CU,"EPD_BUSY_MAIN")
add_track(board,105.400,86.550,101.250,86.550,W_SIG,F_CU,"EPD_BUSY_MAIN")
add_track(board,101.250,86.550,101.250,83.150,W_SIG,F_CU,"EPD_BUSY_MAIN")
print("EPD_BUSY_MAIN y=86.55")

pcbnew.SaveBoard(str(PCB), board)
print("min B saved; 4L=", board.GetCopperLayerCount())
