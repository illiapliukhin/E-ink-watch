#!/usr/bin/env python3
"""Pass B: nudge FPs + rebuild SCL/SDA corridors + FH12 channels."""
from pathlib import Path
import pcbnew

PCB = Path("/workspace/e-ink-watch-kicad/e-ink-watch.kicad_pcb")
POGO = dict(xmin=90.5, xmax=101.5, ymin=108.5, ymax=117.0)
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
W_SIG, W_PWR = 0.18, 0.25

def mm(v): return int(round(float(v)*1e6))
def tomm(v): return float(v)/1e6
def near(a,b,eps=0.08): return abs(a-b)<eps
def is_zero(t,eps=1e-4):
    return abs(tomm(t.GetStart().x)-tomm(t.GetEnd().x))<eps and abs(tomm(t.GetStart().y)-tomm(t.GetEnd().y))<eps

def netcode(board, name):
    return board.GetNetInfo().GetNetItem(name).GetNetCode()

def add_track(board, x1,y1,x2,y2,w,layer,net):
    if near(x1,x2,1e-9) and near(y1,y2,1e-9): return
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(netcode(board,net))
    board.Add(t)

def add_via(board, x,y,d,net):
    if POGO["xmin"]<=x<=POGO["xmax"] and POGO["ymin"]<=y<=POGO["ymax"]:
        print(f"SKIP seal via ({x},{y})"); return False
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x),mm(y)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x),mm(y)))
    t.SetWidth(mm(d)); t.SetLayer(F_CU); t.SetNetCode(netcode(board,net))
    board.Add(t); return True

def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber()==str(num):
            return tomm(p.GetX()), tomm(p.GetY())
    raise KeyError(num)

def shift_ends(board, old_pts, dx, dy, eps=0.12):
    n=0
    for t in board.GetTracks():
        if is_zero(t): continue
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

# --- nudge R_SDA ---
fp=board.FindFootprintByReference("R_SDA")
old=(tomm(fp.GetX()), tomm(fp.GetY()))
old_pads=[pad_xy(fp,"1"), pad_xy(fp,"2")]
dx,dy=0.20,-0.55
fp.SetPosition(pcbnew.VECTOR2I(mm(old[0]+dx), mm(old[1]+dy)))
n=shift_ends(board, old_pads, dx, dy)
print(f"R_SDA {old} -> ({old[0]+dx:.2f},{old[1]+dy:.2f}); ends {n}")

# --- shrink east MP ---
jd=board.FindFootprintByReference("J_DISP_MAIN")
for p in jd.Pads():
    if p.GetNumber()!="MP": continue
    px,py=tomm(p.GetX()), tomm(p.GetY())
    if px<100: continue
    p.SetSize(pcbnew.VECTOR2I(mm(1.0), mm(1.4)))
    p.SetPosition(pcbnew.VECTOR2I(mm(105.10), mm(86.80)))
    print(f"east MP ({px:.2f},{py:.2f})->(105.10,86.80) 1.0x1.4")

# refresh pad coords after nudge
sda1,sda2=pad_xy(fp,"1"), pad_xy(fp,"2")
rc=board.FindFootprintByReference("R_SCL")
scl1,scl2=pad_xy(rc,"1"), pad_xy(rc,"2")

# 3V3 jog north of R_SCL.1
y_jog=max(sda2[1], scl2[1])+0.70
add_track(board, sda2[0],sda2[1], sda2[0],y_jog, W_PWR, F_CU, "3V3")
add_track(board, sda2[0],y_jog, scl2[0],y_jog, W_PWR, F_CU, "3V3")
add_track(board, scl2[0],y_jog, scl2[0],scl2[1], W_PWR, F_CU, "3V3")
print(f"3V3 jog y={y_jog:.2f}")

# F.Cu pullup links
add_track(board, sda1[0],sda1[1], 111.400,106.800, W_SIG, F_CU, "SDA")
add_track(board, 111.800,106.800, scl1[0],scl1[1], W_SIG, F_CU, "SCL")

# SDA B.Cu west corridor (avoid BTN1 @98/98.8)
if add_via(board, sda1[0], 106.90, 0.45, "SDA"):
    add_track(board, 98.800,88.800, 96.400,88.800, W_SIG, B_CU, "SDA")
    add_track(board, 96.400,88.800, 96.400,106.900, W_SIG, B_CU, "SDA")
    add_track(board, 96.400,106.900, sda1[0],106.900, W_SIG, B_CU, "SDA")
    add_track(board, sda1[0],106.900, sda1[0],sda1[1], W_SIG, F_CU, "SDA")
    print(f"SDA B.Cu via @({sda1[0]:.2f},106.90)")

# SCL B.Cu
vx,vy=scl1[0], scl1[1]+0.55
if add_via(board, vx, vy, 0.45, "SCL"):
    add_track(board, 98.000,89.200, 95.600,89.200, W_SIG, B_CU, "SCL")
    add_track(board, 95.600,89.200, 95.600,vy, W_SIG, B_CU, "SCL")
    add_track(board, 95.600,vy, vx,vy, W_SIG, B_CU, "SCL")
    add_track(board, vx,vy, scl1[0],scl1[1], W_SIG, F_CU, "SCL")
    print(f"SCL B.Cu via @({vx:.2f},{vy:.2f})")

# EPD_SCK
add_via(board, 97.000,84.050, 0.45, "EPD_SCK")
add_track(board, 105.500,84.050, 97.000,84.050, W_SIG, F_CU, "EPD_SCK")
add_track(board, 97.000,84.050, 99.250,84.050, W_SIG, F_CU, "EPD_SCK")
add_track(board, 99.250,84.050, 99.250,83.150, W_SIG, F_CU, "EPD_SCK")
print("EPD_SCK y=84.05")

# EPD_RST west jog
add_track(board, 104.000,86.350, 102.600,86.350, W_SIG, F_CU, "EPD_RST")
add_track(board, 102.600,86.350, 102.600,85.550, W_SIG, F_CU, "EPD_RST")
add_track(board, 102.600,85.550, 100.750,85.550, W_SIG, F_CU, "EPD_RST")
add_track(board, 100.750,85.550, 100.750,83.150, W_SIG, F_CU, "EPD_RST")
print("EPD_RST west-jog")

# EPD_BUSY_MAIN
add_track(board, 105.400,90.150, 105.400,86.550, W_SIG, F_CU, "EPD_BUSY_MAIN")
add_track(board, 105.400,86.550, 101.250,86.550, W_SIG, F_CU, "EPD_BUSY_MAIN")
add_track(board, 101.250,86.550, 101.250,83.150, W_SIG, F_CU, "EPD_BUSY_MAIN")
print("EPD_BUSY_MAIN y=86.55")

pcbnew.SaveBoard(str(PCB), board)
print("pass B saved; 4L=", board.GetCopperLayerCount())
