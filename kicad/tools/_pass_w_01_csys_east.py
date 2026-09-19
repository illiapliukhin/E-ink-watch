#!/usr/bin/env python3
"""Pass-W1..3 ATOMIC: C_SYS east, 3V3_DISP truncate+C_LDO B, C_VINLS park @(112.5,104.5).

Single save. Also pull VSYS spine off C5 to avoid 3V3_DISP↔VSYS promotion.
"""
import pcbnew
board = pcbnew.LoadBoard("e-ink-watch.kicad_pcb")
def mm(v): return int(round(float(v)*1e6))
def tomm(u): return u/1e6
def near(a,b,eps=0.12): return abs(a-b)<eps
F,B=pcbnew.F_Cu,pcbnew.B_Cu
ni=board.GetNetInfo()
def nc(name): return ni.GetNetItem(name).GetNetCode()
def add(layer,x1,y1,x2,y2,w,net):
    t=pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
    t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNetCode(nc(net)); board.Add(t)
def via(x,y,net,drill=0.25,width=0.45):
    v=pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetDrill(mm(drill))
    try: v.SetWidth(mm(width), F); v.SetWidth(mm(width), B)
    except Exception:
        try: v.SetFrontWidth(mm(width)); v.SetBackWidth(mm(width))
        except Exception: pass
    v.SetNetCode(nc(net)); board.Add(v)

rm=[]
# --- remove C_VINLS old GND stubs ---
for t in list(board.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T or t.GetLayerName()!="F.Cu": continue
    n=t.GetNetname()
    sx,sy=tomm(t.GetStart().x),tomm(t.GetStart().y)
    ex,ey=tomm(t.GetEnd().x),tomm(t.GetEnd().y)
    if n=="GND" and near(sx,112.800) and near(ex,112.800) and max(sy,ey)<=105.45 and min(sy,ey)>=105.25:
        rm.append(t)
    # 3V3_DISP F through C_VINLS / to old C_LDO column
    if n=="3V3_DISP" and t.GetLayerName()=="F.Cu":
        if near(sy,106.000) and near(ey,106.000) and min(sx,ex)<=111.85 and max(sx,ex)>=112.3:
            rm.append(t)
        if near(sx,113.500) and near(ex,113.500) and min(sy,ey)<=106.4 and max(sy,ey)>=106.0:
            rm.append(t)
    # VSYS long spine to C5
    if n=="VSYS" and t.GetLayerName()=="F.Cu":
        if near(sy,106.100) and near(ey,106.100) and max(sx,ex)>=117.0 and min(sx,ex)<=111.85:
            rm.append(t)
        if near(sy,106.100) and near(ey,106.100) and near(min(sx,ex),111.800) and max(sx,ex)<=112.1:
            rm.append(t)
for t in rm: board.Remove(t)

# --- C_SYS east ---
csys=[f for f in board.GetFootprints() if f.GetReference()=="C_SYS"][0]
csys.SetPosition(pcbnew.VECTOR2I(mm(113.000), mm(104.000)))
sp={p.GetNumber():(tomm(p.GetPosition().x),tomm(p.GetPosition().y),p.GetNetname()) for p in csys.Pads()}
print("C_SYS→(113.000,104.000)", sp)
vsys_p=[v for v in sp.values() if v[2]=="VSYS"][0]
gnd_sys=[v for v in sp.values() if v[2]=="GND"][0]
add(F, vsys_p[0], vsys_p[1], 113.000, 106.100, 0.28, "VSYS")
add(F, gnd_sys[0], gnd_sys[1], 112.200, gnd_sys[1], 0.25, "GND")

# --- VSYS spine ends at 113.0 (joins C_SYS riser); not through C5 ---
add(F, 117.412, 106.100, 113.000, 106.100, 0.30, "VSYS")
# keep existing (112.05,106.1)-(112.05,105.6)-(111.8,105.6) if present — link from 113.0
add(F, 113.000, 106.100, 112.050, 106.100, 0.25, "VSYS")

# --- C_LDO B reconnect @y=107.30 clear of LSCTRL via@111.55 ---
cldo=[f for f in board.GetFootprints() if f.GetReference()=="C_LDO"][0]
disp=[(tomm(p.GetPosition().x),tomm(p.GetPosition().y)) for p in cldo.Pads() if p.GetNetname()=="3V3_DISP"][0]
print("C_LDO 3V3_DISP pad", disp)
via(111.800, 106.000, "3V3_DISP", 0.25, 0.45)
# B go east first to x=112.8 (past LSCTRL@111.55), THEN north to 107.30, east to C_LDO
add(B, 111.800, 106.000, 112.800, 106.000, 0.18, "3V3_DISP")
add(B, 112.800, 106.000, 112.800, 107.300, 0.18, "3V3_DISP")
add(B, 112.800, 107.300, disp[0], 107.300, 0.18, "3V3_DISP")
add(B, disp[0], 107.300, disp[0], disp[1], 0.18, "3V3_DISP")
via(disp[0], disp[1], "3V3_DISP", 0.25, 0.45)

# --- C_VINLS park ---
cv=[f for f in board.GetFootprints() if f.GetReference()=="C_VINLS"][0]
print(f"C_VINLS ({tomm(cv.GetPosition().x):.3f},{tomm(cv.GetPosition().y):.3f})→(112.500,104.500)")
cv.SetPosition(pcbnew.VECTOR2I(mm(112.500), mm(104.500)))
cp={p.GetNumber():(tomm(p.GetPosition().x),tomm(p.GetPosition().y),p.GetNetname()) for p in cv.Pads()}
print("  pads", cp)
pmid=[v for v in cp.values() if v[2]=="PMID"][0]
gnd=[v for v in cp.values() if v[2]=="GND"][0]

# PMID: south on x=112.9 (east of body) to 103.85, west to island — avoid pad2
add(F, pmid[0], pmid[1], 112.900, pmid[1], 0.20, "PMID")
add(F, 112.900, pmid[1], 112.900, 103.850, 0.20, "PMID")
add(F, 112.900, 103.850, 111.350, 103.850, 0.20, "PMID")

# GND: west then south to C_SYS GND (now @113.0,103.52) — path south of SW via
add(F, gnd[0], gnd[1], 111.400, gnd[1], 0.18, "GND")
add(F, 111.400, gnd[1], 111.400, 103.520, 0.18, "GND")
add(F, 111.400, 103.520, gnd_sys[0], 103.520, 0.18, "GND")

pcbnew.SaveBoard("e-ink-watch.kicad_pcb", board)
print(f"W1-3 atomic rem={len(rm)}")
